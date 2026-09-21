from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class Decision(StrEnum):
    ACCEPT = "accept"
    REVIEW = "review"
    REJECT = "reject"


@dataclass(frozen=True)
class Application:
    gpa: float
    monthly_household_income_sar: float
    household_size: int
    transcript_present: bool
    income_proof_present: bool

    def __post_init__(self) -> None:
        if not isfinite(self.gpa) or not 0 <= self.gpa <= 4:
            raise ValueError("gpa must be between 0 and 4")
        if (
            not isfinite(self.monthly_household_income_sar)
            or not 0 <= self.monthly_household_income_sar <= 1_000_000
        ):
            raise ValueError("income must be between 0 and 1000000")
        if type(self.household_size) is not int or not 1 <= self.household_size <= 20:
            raise ValueError("household_size must be an integer between 1 and 20")
        if type(self.transcript_present) is not bool or type(self.income_proof_present) is not bool:
            raise ValueError("document presence must be boolean")

    @property
    def missing_documents(self) -> tuple[str, ...]:
        return tuple(
            name
            for name, present in (
                ("transcript", self.transcript_present),
                ("income_proof", self.income_proof_present),
            )
            if not present
        )

    @property
    def income_per_person(self) -> float:
        return self.monthly_household_income_sar / self.household_size


@dataclass(frozen=True)
class Outcome:
    decision: Decision
    eligibility_score: float
    model_version: str
    policy_version: str
    reason_codes: tuple[str, ...]
    explanation: str
    next_steps: tuple[str, ...]
    missing_documents: tuple[str, ...]
