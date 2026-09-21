from typing import cast

from redis import Redis
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from redis.retry import Retry

from rasheed.domain.entities import Decision
from rasheed.service.interfaces import StoreUnavailable


class RedisStatistics:
    """Only aggregate counters are stored. No applicant inputs or identifiers."""

    def __init__(self, url: str, timeout: float):
        # Bound dependency failure latency and never retry a possibly-applied increment.
        self.client = Redis.from_url(
            url,
            socket_timeout=timeout,
            socket_connect_timeout=timeout,
            retry=Retry(NoBackoff(), 0),
        )
        self.key = "rasheed:decision-counts:v1"

    def record(self, decision: Decision) -> None:
        try:
            self.client.hincrby(self.key, decision.value, 1)
        except RedisError:
            raise StoreUnavailable("Decision statistics unavailable") from None

    def snapshot(self) -> dict[str, int]:
        try:
            # A single HGETALL provides one snapshot even during concurrent requests.
            values = cast(dict[bytes, bytes], self.client.hgetall(self.key))
            return {d.value: int(values.get(d.value.encode(), b"0")) for d in Decision}
        except RedisError:
            raise StoreUnavailable("Decision statistics unavailable") from None

    def ready(self) -> bool:
        try:
            return bool(self.client.ping())
        except RedisError:
            return False

    def close(self) -> None:
        self.client.close()
