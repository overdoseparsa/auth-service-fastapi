from datetime import timedelta

import pytest_asyncio

from core.security.jwt.service import TokenService
from core.security.jwt.utils import _utc_now


@pytest_asyncio.fixture
async def token_service():
    return TokenService(
        audience="test_audience",
    )


@pytest_asyncio.fixture
def fake_payload(token_service):
    fake_payload = token_service._base_claims(
        subject="user_id",
        token_type="access",
        now=_utc_now(),
        ttl=timedelta(days=1),
    )
    yield fake_payload
    del fake_payload


@pytest_asyncio.fixture
def expired_fake_payload(token_service):
    fake_payload = token_service._base_claims(
        subject="user_id",
        token_type="access",
        now=_utc_now() - timedelta(days=2),
        ttl=timedelta(days=1),
    )
    yield fake_payload
