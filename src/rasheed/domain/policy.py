from dataclasses import dataclass
from math import isfinite

from rasheed.domain.entities import Application, Decision, Outcome


@dataclass(frozen=True)
class ScholarshipPolicy:
    minimum_gpa: float = 2.0
    review_threshold: float = 0.45
    accept_threshold: float = 0.70
    version: str = "scholarship-policy-1.0.0"

    def __post_init__(self) -> None:
        if not 0 <= self.minimum_gpa <= 4:
            raise ValueError("invalid minimum GPA")
        if not 0 <= self.review_threshold < self.accept_threshold <= 1:
            raise ValueError("thresholds must satisfy 0 <= review < accept <= 1")

    def decide(self, app: Application, score: float, model_version: str) -> Outcome:
        if not isfinite(score) or not 0 <= score <= 1:
            raise ValueError("model score must be finite and between 0 and 1")
        reasons: tuple[str, ...]
        if app.missing_documents:
            decision = Decision.REVIEW
            reasons = ("MISSING_REQUIRED_DOCUMENTS",)
            explanation = "Committee review is required because the application is incomplete."
            steps = tuple(f"Submit {name.replace('_', ' ')}." for name in app.missing_documents)
        elif app.gpa < self.minimum_gpa:
            decision = Decision.REJECT
            reasons = ("GPA_BELOW_MINIMUM",)
            explanation = "The GPA is below this demonstration scholarship's minimum."
            steps = ("Request a committee review if the GPA record is incorrect.",)
        elif score >= self.accept_threshold:
            decision = Decision.ACCEPT
            reasons = ("DOCUMENTS_COMPLETE", "SCORE_MEETS_ACCEPTANCE")
            explanation = "The complete application meets the demonstration eligibility policy."
            steps = ("Await the institution's verification and final award decision.",)
        elif score >= self.review_threshold:
            decision = Decision.REVIEW
            reasons = ("BORDERLINE_SCORE",)
            explanation = "The score falls within the committee review band."
            steps = ("A committee member must review the application.",)
        else:
            decision = Decision.REJECT
            reasons = ("SCORE_BELOW_REVIEW_BAND",)
            explanation = "The score is below this demonstration policy's review band."
            steps = ("Request a committee review if application information is incorrect.",)
        return Outcome(
            decision,
            round(score, 6),
            model_version,
            self.version,
            reasons,
            explanation,
            steps,
            app.missing_documents,
        )
