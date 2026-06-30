import pytest_asyncio

from core.security.utils.hashing import hash_password
from core.security.utils.token_utils import generate_token, hash_token
from users.repository import ProfileRepository, UserRepository
from users.schemas import UserRegister
from users.service import ProfileService, UserService


@pytest_asyncio.fixture(scope="module")
async def user_service() -> UserService:
    return UserService(
        user_repo=UserRepository(),
        token_generator=generate_token,
        hasher_password=hash_password,
        hasher_token=hash_token,
    )


@pytest_asyncio.fixture(scope="module")
async def profile_service() -> ProfileService:
    return ProfileService(profile_repo=ProfileRepository())


@pytest_asyncio.fixture
def get_user_sample():
    return UserRegister(
        username="testuser",
        email="test@example.com",
        password="password",
        name="Test",
        family="User",
    )
