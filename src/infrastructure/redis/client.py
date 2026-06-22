from typing import Any
from uuid import UUID

from asyncpg.pgproto.pgproto import UUID as _UUID

from core.config import settings
from redis.asyncio import ConnectionPool
from redis.asyncio.client import Redis

redis_connection_pool = ConnectionPool.from_url(
    url=str(settings.REDIS_URL), max_connections=100
)


class RedisManager:
    def __init__(self):
        self.redis = Redis(connection_pool=redis_connection_pool)

    def serialize(self, data):
        if type(data) in [UUID, _UUID]:
            data = str(data)
        return data

    def deserialize(self, data) -> str:
        if type(data) is bytes:
            data = data.decode("utf-8")
        return data

    async def ttl(self, name) -> Any:
        name = self.serialize(name)
        result: int = await self.redis.ttl(name)
        return result

    async def get(self, name) -> Any:
        name = self.serialize(name)
        result: bytes | None | str = await self.redis.get(name)
        result = self.deserialize(result)
        return result

    async def set(self, name, value, ex: int) -> Any:
        name = self.serialize(name)
        value = self.serialize(value)
        result = await self.redis.set(name, value, ex)
        result = self.deserialize(result)
        return result

    async def delete(self, name) -> Any:
        name = self.serialize(name)
        result = await self.redis.delete(name)
        result = self.deserialize(result)
        return result


def get_redis_db() -> RedisManager:
    return RedisManager()
