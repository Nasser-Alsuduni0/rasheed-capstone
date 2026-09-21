from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RASHEED_", extra="forbid", hide_input_in_errors=True
    )
    model_path: Path = Path("models/scholarship_rules.v1.json")
    redis_url: SecretStr = SecretStr("redis://localhost:6379/0")
    redis_timeout_seconds: float = Field(default=1.0, gt=0, le=5)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("redis_url")
    @classmethod
    def valid_redis_url(cls, value: SecretStr) -> SecretStr:
        from urllib.parse import urlparse

        try:
            parsed = urlparse(value.get_secret_value())
            if parsed.scheme not in ("redis", "rediss") or not parsed.hostname:
                raise ValueError
            if parsed.port is not None and not 1 <= parsed.port <= 65535:
                raise ValueError
        except ValueError:
            raise ValueError("redis_url must be a valid redis:// or rediss:// URL") from None
        return value
