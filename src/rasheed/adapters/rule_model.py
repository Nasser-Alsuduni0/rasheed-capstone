from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from rasheed.domain.entities import Application


class ModelArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False, frozen=True)
    version: str = Field(pattern=r"^rasheed-rules-\d+\.\d+\.\d+$")
    merit_weight: float = Field(ge=0, le=1)
    need_weight: float = Field(ge=0, le=1)
    income_per_person_ceiling_sar: float = Field(gt=0)

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> Self:
        if abs(self.merit_weight + self.need_weight - 1) > 1e-9:
            raise ValueError("model weights must sum to one")
        return self


class RuleModel:
    """Versioned rules model; score is not a learned probability."""

    def __init__(self, artifact: ModelArtifact):
        self.artifact = artifact

    @property
    def version(self) -> str:
        return self.artifact.version

    @classmethod
    def load(cls, path: Path) -> Self:
        return cls(ModelArtifact.model_validate_json(path.read_text(encoding="utf-8")))

    def score(self, application: Application) -> float:
        merit = application.gpa / 4.0
        need = 1 - min(
            application.income_per_person / self.artifact.income_per_person_ceiling_sar, 1.0
        )
        return self.artifact.merit_weight * merit + self.artifact.need_weight * need
