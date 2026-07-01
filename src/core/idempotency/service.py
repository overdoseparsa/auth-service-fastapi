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

    async def __call__(self, idempotency_key: str) -> str | None:
        if not idempotency_key:
            return None

        redis_key = f"idempotency:{idempotency_key}"

        acquired = await self.redis.set(redis_key, "processing", ex=self.ttl, nx=True)

        if acquired:
            return idempotency_key

        status_value = await self.redis.get(redis_key)
        
        if status_value is None:
            return await self.__call__(idempotency_key)

        if status_value == b"processing" or status_value == "processing":
            raise IdempotencyException(
                "Request already in progress. Please wait.",
            )

        if status_value == b"completed" or status_value == "completed":
            raise IdempotencyException(
                "Duplicate request. Operation already completed.",
            )

        raise IdempotencyException("Conflict. Request collision detected.")

    async def mark_completed(self, idempotency_key: str) -> None:
        redis_key = f"idempotency:{idempotency_key}"


        status_value = await self.redis.get(redis_key)
        if status_value in (b"processing", "processing"):
            await self.redis.set(redis_key, "completed", ex=self.ttl)
