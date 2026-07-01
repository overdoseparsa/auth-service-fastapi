import fakeredis
import pytest_asyncio

from core.config import settings
from infrastructure.redis.client import RedisManager
from tests.mocks.redis import RedisMock


@pytest_asyncio.fixture
def mock_redis():
    return RedisMock


@pytest_asyncio.fixture
async def redis_real():
    """
    Test Container Redis a Sepreate Cluster
    """
    redis_manager = RedisManager(settings.REDIS_URL_TEST)

    yield redis_manager

    await redis_manager.flush_all()


@pytest_asyncio.fixture
def redis_fake_client():
    return fakeredis.FakeAsyncRedis()
