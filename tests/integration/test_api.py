from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rasheed.api.app import create_app
from rasheed.service.interfaces import StoreUnavailable
from rasheed.service.screening import ScreeningService

pytestmark = pytest.mark.integration
CORPUS = sorted((Path(__file__).resolve().parents[2] / "payloads/malformed").glob("*.json"))


@pytest.mark.parametrize("score,decision", [(0.8, "accept"), (0.6, "review"), (0.2, "reject")])
def test_contract_and_aggregate_counts(client_factory, valid_payload, score, decision):
    client = client_factory(score)
    trace = "a" * 32
    response = client.post("/v1/predict", json=valid_payload, headers={"X-Trace-Id": trace})
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["trace_id"] == response.headers["X-Trace-Id"] == trace
    assert body["data"]["decision"] == decision
    assert body["data"]["eligibility_score"] == score
    assert body["data"]["model_version"] == "constant-test-1"
    assert body["data"]["explanation"] and body["data"]["next_steps"]
    counts = client.get("/v1/statistics").json()["data"]
    assert counts[decision] == 1 and sum(counts.values()) == 1


def test_health_is_independent_and_readiness_checks_support(client_factory, store):
    client = client_factory()
    assert client.get("/ready").status_code == 200
    store.available = False
    assert client.get("/health").status_code == 200
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "NOT_READY"


def test_unstarted_service_is_live_but_not_ready():
    def factory():
        raise AssertionError("Must not load without lifespan")

    client = TestClient(create_app(factory), raise_server_exceptions=False)
    try:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503
    finally:
        client.close()


@pytest.mark.parametrize("path", CORPUS, ids=lambda p: p.stem)
def test_every_malformed_file_is_4xx(client_factory, store, path):
    response = client_factory().post(
        "/v1/predict", content=path.read_bytes(), headers={"Content-Type": "application/json"}
    )
    assert 400 <= response.status_code < 500
    assert response.json()["data"] is None
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert sum(store.counts.values()) == 0


def test_corpus_is_not_accidentally_empty():
    assert len(CORPUS) >= 40


def test_declared_500_is_safe_and_traceable(client_factory, valid_payload, monkeypatch):
    client = client_factory()

    def fail(self, application):
        raise RuntimeError("SecretInternalException applicant-private-data")

    monkeypatch.setattr(ScreeningService, "predict", fail)
    response = client.post("/v1/predict", json=valid_payload)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert response.json()["trace_id"] == response.headers["X-Trace-Id"]
    assert "RuntimeError" not in response.text
    assert "SecretInternalException" not in response.text
    assert "applicant-private-data" not in response.text


def test_store_failure_returns_503(client_factory, valid_payload, monkeypatch, store):
    client = client_factory()

    def fail(decision):
        raise StoreUnavailable("private connection string")

    monkeypatch.setattr(store, "record", fail)
    response = client.post("/v1/predict", json=valid_payload)
    assert response.status_code == 503
    assert "private connection" not in response.text


def test_unknown_route_has_same_envelope(client_factory):
    response = client_factory().get("/absent")
    assert response.status_code == 404
    assert set(response.json()) == {"data", "error", "trace_id"}


def test_document_extension_lists_actionable_next_steps(client_factory, valid_payload):
    valid_payload.update(gpa=0.0, transcript_present=False)
    body = client_factory(0).post("/v1/predict", json=valid_payload).json()["data"]
    assert body["decision"] == "review"
    assert body["reason_codes"] == ["MISSING_REQUIRED_DOCUMENTS"]
    assert body["missing_documents"] == ["transcript"]
    assert body["next_steps"] == ["Submit transcript."]


def test_invalid_trace_header_is_replaced(client_factory):
    response = client_factory().get("/health", headers={"X-Trace-Id": "private-applicant-name"})
    assert len(response.headers["X-Trace-Id"]) == 32
    assert "private-applicant-name" not in response.text
