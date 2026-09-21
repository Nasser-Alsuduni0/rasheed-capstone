import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from rasheed.domain.entities import Application
from rasheed.domain.policy import ScholarshipPolicy

pytestmark = [pytest.mark.behavioural, pytest.mark.slow]
ROOT = Path(__file__).resolve().parents[2]
GOLDEN = json.loads((ROOT / "tests/golden/decisions.v1.json").read_text(encoding="utf-8"))


def test_artifact_matches_reviewed_golden_fingerprint():
    digest = hashlib.sha256((ROOT / "models/scholarship_rules.v1.json").read_bytes()).hexdigest()
    assert digest == GOLDEN["model_sha256"]


@pytest.mark.parametrize("case", GOLDEN["cases"], ids=lambda c: c["name"])
def test_full_golden_decision(real_model, case):
    application = Application(**case["input"])
    outcome = ScholarshipPolicy().decide(
        application, real_model.score(application), real_model.version
    )
    # Full decision, explanations, document names, action list and both versions.
    actual = json.loads(json.dumps(asdict(outcome)))
    assert actual == case["expected"]


@pytest.mark.parametrize("income,size", [(0, 1), (4000, 4), (1000000, 20)])
def test_increasing_gpa_never_reduces_score(real_model, income, size):
    scores = [
        real_model.score(Application(gpa, income, size, True, True))
        for gpa in [0, 1, 2, 2.5, 3, 3.5, 4]
    ]
    assert scores == sorted(scores)
    assert all(0 <= value <= 1 for value in scores)


@pytest.mark.parametrize("gpa", [0, 2, 3.5, 4])
def test_increasing_income_never_increases_score(real_model, gpa):
    scores = [
        real_model.score(Application(gpa, income, 4, True, True))
        for income in [0, 1000, 5000, 20000, 1000000]
    ]
    assert scores == sorted(scores, reverse=True)


def test_equivalent_per_person_income_is_invariant(real_model):
    first = Application(3, 4000, 4, True, True)
    second = Application(3, 8000, 8, True, True)
    assert real_model.score(first) == real_model.score(second)


@pytest.mark.parametrize("gpa,income", [(0, 1000000), (2.5, 8000), (4, 0)])
def test_missing_document_always_routes_to_review(real_model, gpa, income):
    application = Application(gpa, income, 4, False, True)
    outcome = ScholarshipPolicy().decide(
        application, real_model.score(application), real_model.version
    )
    assert outcome.decision == "review"
    assert outcome.reason_codes == ("MISSING_REQUIRED_DOCUMENTS",)
