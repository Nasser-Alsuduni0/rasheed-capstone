from rasheed.adapters.redis_statistics import RedisStatistics
from rasheed.adapters.rule_model import RuleModel
from rasheed.api.app import create_app
from rasheed.config import Settings
from rasheed.domain.policy import ScholarshipPolicy
from rasheed.logging_config import configure_logging
from rasheed.service.screening import ScreeningService


def build_service() -> ScreeningService:
    # Settings, file I/O, logging and Redis connections belong exclusively to startup.
    settings = Settings()
    configure_logging(settings.log_level)
    model = RuleModel.load(settings.model_path)
    statistics = RedisStatistics(
        settings.redis_url.get_secret_value(), settings.redis_timeout_seconds
    )
    return ScreeningService(model, ScholarshipPolicy(), statistics)


app = create_app(build_service)
