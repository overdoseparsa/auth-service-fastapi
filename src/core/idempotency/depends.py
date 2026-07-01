from infrastructure.redis.client import get_redis_db

from .service import IdempotencyService


def get_idempotency_service() -> IdempotencyService:
    return IdempotencyService(
        get_redis_db()
        )
