import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings
from tests.mocks.db import Session_Mock


@pytest_asyncio.fixture
async def db_session():
    mock_session = await Session_Mock()
    yield mock_session
    del mock_session


@pytest_asyncio.fixture
async def async_session_factory():
    engine = create_async_engine(str(settings.DATABASE_URL_TEST))
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
    )
    yield async_session
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_session_factory):
    async with async_session_factory() as session:
        yield session
