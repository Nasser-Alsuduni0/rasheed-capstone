from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from rasheed.domain.entities import Application


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    gpa: float = Field(ge=0, le=4)
    monthly_household_income_sar: float = Field(ge=0, le=1_000_000)
    household_size: int = Field(ge=1, le=20)
    transcript_present: bool
    income_proof_present: bool

    def to_domain(self) -> Application:
        return Application(**self.model_dump())


class DecisionData(BaseModel):
    decision: Literal["accept", "review", "reject"]
    eligibility_score: float = Field(ge=0, le=1)
    model_version: str
    policy_version: str
    reason_codes: list[str]
    explanation: str
    next_steps: list[str]
    missing_documents: list[str]


class ErrorData(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    data: None = None
    error: ErrorData
    trace_id: str


class PredictionResponse(BaseModel):
    data: DecisionData
    error: None = None
    trace_id: str


class HealthData(BaseModel):
    status: str


class HealthResponse(BaseModel):
    data: HealthData
    error: None = None
    trace_id: str


class StatisticsResponse(BaseModel):
    data: dict[str, int]
    error: None = None
    trace_id: str
