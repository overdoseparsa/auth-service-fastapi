import pytest_asyncio

from core.security.utils.hashing import hash_password
from core.security.utils.token_utils import generate_token, hash_token
from users.repository import ProfileRepository, UserRepository
from users.service import ProfileService, UserService


@pytest_asyncio.fixture(scope="module")
async def user_service():
    return UserService(
        user_repo=UserRepository(),
        token_generator=generate_token,
        hasher_password=hash_password,
        hasher_token=hash_token,
    )


@pytest_asyncio.fixture(scope="module")
async def profile_service():
    return ProfileService(profile_repo=user_service)
