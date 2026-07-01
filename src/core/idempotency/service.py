from core.config import settings
from infrastructure.redis.client import RedisManager

from .exceptions import IdempotencyException


class IdempotencyService:
    def __init__(
        self,
        redis_client: RedisManager,
        ttl_seconds: int = settings.IDEMPOTENCY_TTL,
    ):
        self.redis = redis_client
        self.ttl = ttl_seconds

    async def __call__(self, idempotency_key: str):

        if not idempotency_key:
            return None

        redis_key = f"idempotency:{idempotency_key}"

        status_value = await self.redis.get(redis_key)
        print("status_values", status_value)
        if status_value == "processing":
            raise IdempotencyException(
                "Request already in progress. Please wait.",
            )

        if status_value == "completed":
            raise IdempotencyException(
                "Duplicate request. Operation already completed.",
            )

        acquired = await self.redis.set(redis_key, "processing", ex=self.ttl)

        if not acquired:
            raise IdempotencyException(
                "Conflict. Request processing started by another thread.",
            )

        return idempotency_key
