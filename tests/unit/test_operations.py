import importlib
import io
import json
import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from redis.exceptions import ConnectionError

from rasheed.adapters.redis_statistics import RedisStatistics
from rasheed.adapters.rule_model import ModelArtifact, RuleModel
from rasheed.api.app import create_app
from rasheed.config import Settings
from rasheed.domain.entities import Decision
from rasheed.domain.policy import ScholarshipPolicy
from rasheed.logging_config import JsonFormatter
from rasheed.service.interfaces import StoreUnavailable
from rasheed.service.screening import ScreeningService

pytestmark = pytest.mark.unit


def test_model_artifact_rejects_invalid_weights():
    with pytest.raises(ValidationError):
        ModelArtifact(
            version="rasheed-rules-1.0.0",
            merit_weight=0.9,
            need_weight=0.9,
            income_per_person_ceiling_sar=5000.0,
        )


def test_missing_artifact_fails_clearly(tmp_path):
    with pytest.raises(FileNotFoundError):
        RuleModel.load(tmp_path / "missing.json")


@pytest.mark.parametrize(
    "field,value",
    [
        ("redis_timeout_seconds", 0),
        ("log_level", "invalid"),
        ("redis_url", "http://example.org"),
        ("redis_url", "redis://host:99999"),
        ("redis_url", "redis://"),
    ],
)
def test_settings_fail_fast_without_echoing_values(field, value):
    with pytest.raises(ValidationError):
        Settings(**{field: value})


def test_import_does_not_load_model_or_connect(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("Unexpected import-time I/O")

    monkeypatch.setattr(RuleModel, "load", fail)
    monkeypatch.setattr(RedisStatistics, "__init__", fail)
    import rasheed.bootstrap

    importlib.reload(rasheed.bootstrap)


def test_lifespan_closes_support_even_if_readiness_fails(store):
    from tests.conftest import ConstantModel

    store.available = False
    service = ScreeningService(ConstantModel(), ScholarshipPolicy(), store)
    with pytest.raises(RuntimeError, match="Supporting service"):
        with TestClient(create_app(lambda: service)):
            pass
    assert store.closed


def test_redis_adapter_records_only_aggregate_counts(monkeypatch):
    class FakeRedis:
        def hincrby(self, key, field, count):
            assert key == "rasheed:decision-counts:v1"
            assert field == "accept" and count == 1

        def hgetall(self, key):
            return {b"accept": b"3"}

        def ping(self):
            return True

        def close(self):
            self.closed = True

    fake = FakeRedis()

    def factory(url, **kwargs):
        assert kwargs["socket_timeout"] == kwargs["socket_connect_timeout"] == 1
        assert kwargs["retry"].get_retries() == 0
        return fake

    monkeypatch.setattr("rasheed.adapters.redis_statistics.Redis.from_url", factory)
    adapter = RedisStatistics("redis://localhost", 1)
    adapter.record(Decision.ACCEPT)
    assert adapter.snapshot() == {"accept": 3, "review": 0, "reject": 0}
    assert adapter.ready()
    adapter.close()
    assert fake.closed


def test_redis_failure_has_safe_error(monkeypatch):
    class BrokenRedis:
        def hincrby(self, *args):
            raise ConnectionError("sensitive")

        def hgetall(self, *args):
            raise ConnectionError("sensitive")

        def ping(self):
            raise ConnectionError("sensitive")

    monkeypatch.setattr(
        "rasheed.adapters.redis_statistics.Redis.from_url", lambda *a, **kw: BrokenRedis()
    )
    adapter = RedisStatistics("redis://localhost", 1)
    assert not adapter.ready()
    with pytest.raises(StoreUnavailable, match="statistics unavailable"):
        adapter.record(Decision.ACCEPT)
    with pytest.raises(StoreUnavailable, match="statistics unavailable"):
        adapter.snapshot()


def test_json_request_logs_exclude_applicant_data(client_factory, valid_payload):
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("rasheed")
    old_level = logger.level
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    try:
        client = client_factory()
        response = client.post("/v1/predict", json=valid_payload)
        events = [json.loads(line) for line in buffer.getvalue().splitlines()]
        request = next(event for event in events if event["event"] == "request_completed")
        assert request["trace_id"] == response.json()["trace_id"]
        assert request["status_code"] == 200
        assert request["duration_ms"] >= 0
        assert "gpa" not in buffer.getvalue()
        assert "monthly_household_income_sar" not in buffer.getvalue()
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)
