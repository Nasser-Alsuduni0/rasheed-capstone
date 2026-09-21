from dataclasses import dataclass

from rasheed.domain.entities import Application, Outcome
from rasheed.domain.policy import ScholarshipPolicy
from rasheed.service.interfaces import DecisionStatistics, ScoringModel


@dataclass
class ScreeningService:
    model: ScoringModel
    policy: ScholarshipPolicy
    statistics: DecisionStatistics

    def predict(self, application: Application) -> Outcome:
        outcome = self.policy.decide(application, self.model.score(application), self.model.version)
        self.statistics.record(outcome.decision)
        return outcome

    def ready(self) -> bool:
        return self.statistics.ready()

    def warm_up(self) -> None:
        sample = Application(3.0, 6000.0, 4, True, True)
        self.policy.decide(sample, self.model.score(sample), self.model.version)

    def close(self) -> None:
        self.statistics.close()
