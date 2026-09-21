from contextlib import ExitStack
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rasheed.adapters.rule_model import RuleModel
from rasheed.api.app import create_app
from rasheed.domain.entities import Decision
from rasheed.domain.policy import ScholarshipPolicy
from rasheed.service.screening import ScreeningService

ROOT = Path(__file__).resolve().parents[1]


class ConstantModel:
    version = "constant-test-1"

    def __init__(self, value=0.8):
        self.value = value

    def score(self, application):
        return self.value


class MemoryStatistics:
    def __init__(self):
        self.counts = {d.value: 0 for d in Decision}
        self.available = True
        self.closed = False

    def record(self, decision):
        self.counts[decision.value] += 1

    def snapshot(self):
        return dict(self.counts)

    def ready(self):
        return self.available

    def close(self):
        self.closed = True


@pytest.fixture
def store():
    return MemoryStatistics()


@pytest.fixture
def client_factory(store):
    with ExitStack() as stack:

        def make(score=0.8):
            service = ScreeningService(ConstantModel(score), ScholarshipPolicy(), store)
            client = stack.enter_context(
                TestClient(create_app(lambda: service), raise_server_exceptions=False)
            )
            return client

        yield make


@pytest.fixture(scope="session")
def real_model():
    return RuleModel.load(ROOT / "models/scholarship_rules.v1.json")


@pytest.fixture
def valid_payload():
    return {
        "gpa": 3.5,
        "monthly_household_income_sar": 4000.0,
        "household_size": 4,
        "transcript_present": True,
        "income_proof_present": True,
    }
