import pytest

from rasheed.domain.entities import Application, Decision
from rasheed.domain.policy import ScholarshipPolicy

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "score,expected",
    [
        (0, "reject"),
        (0.449999, "reject"),
        (0.45, "review"),
        (0.699999, "review"),
        (0.70, "accept"),
        (1, "accept"),
    ],
)
def test_threshold_boundaries(score, expected):
    result = ScholarshipPolicy().decide(Application(3, 1000, 2, True, True), score, "test")
    assert result.decision == expected
    assert result.explanation and result.reason_codes and result.next_steps


@pytest.mark.parametrize("score", [0, 0.5, 1])
def test_missing_documents_override_even_low_gpa(score):
    result = ScholarshipPolicy().decide(Application(1, 1000, 2, False, False), score, "test")
    assert result.decision == Decision.REVIEW
    assert result.reason_codes == ("MISSING_REQUIRED_DOCUMENTS",)
    assert result.missing_documents == ("transcript", "income_proof")
    assert len(result.next_steps) == 2


def test_complete_low_gpa_has_explained_rejection():
    result = ScholarshipPolicy().decide(Application(1.99, 0, 1, True, True), 1, "test")
    assert result.decision == "reject"
    assert result.reason_codes == ("GPA_BELOW_MINIMUM",)


@pytest.mark.parametrize("score", [-0.1, 1.1, float("nan"), float("inf")])
def test_invalid_model_output_is_never_a_decision(score):
    with pytest.raises(ValueError):
        ScholarshipPolicy().decide(Application(3, 0, 1, True, True), score, "test")


@pytest.mark.parametrize(
    "kwargs", [{"minimum_gpa": 5}, {"review_threshold": 0.8}, {"accept_threshold": -1}]
)
def test_invalid_policy_fails_fast(kwargs):
    with pytest.raises(ValueError):
        ScholarshipPolicy(**kwargs)


@pytest.mark.parametrize(
    "args",
    [
        (-1, 0, 1, True, True),
        (5, 0, 1, True, True),
        (float("nan"), 0, 1, True, True),
        (3, -1, 1, True, True),
        (3, 0, 0, True, True),
        (3, 0, True, True, True),
        (3, 0, 1, 1, True),
    ],
)
def test_invalid_domain_inputs_are_rejected(args):
    with pytest.raises(ValueError):
        Application(*args)
