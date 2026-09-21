from typing import Protocol

from rasheed.domain.entities import Application, Decision


class ScoringModel(Protocol):
    @property
    def version(self) -> str: ...
    def score(self, application: Application) -> float: ...


class DecisionStatistics(Protocol):
    def record(self, decision: Decision) -> None: ...
    def snapshot(self) -> dict[str, int]: ...
    def ready(self) -> bool: ...
    def close(self) -> None: ...


class StoreUnavailable(Exception):
    """The supporting service cannot safely complete this operation."""
