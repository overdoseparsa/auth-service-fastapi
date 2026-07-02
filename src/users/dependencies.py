from configparser import NoOptionError

from fastapi import Depends

from auth.dependencies import get_current_user_id
from core.security.utils.hashing import hash_password
from core.security.utils.token_utils import generate_token, hash_token
from infrastructure.sqlalchemy.AsyncSession import AsyncSessionLocal
from models.user import User

from .controllers import UserRegistrationController
from .exceptions import UserNotExists
from .repository import ProfileRepository, UserRepository
from .selectors import UserSelector
from .service import ProfileService, UserService


def get_user_repo():
    return UserRepository()


def get_profile_repo():
    return ProfileRepository()


def get_user_service(user_repo=Depends(get_user_repo)):
    return UserService(
        user_repo=user_repo,
        token_generator=generate_token,
        hasher_password=hash_password,
        hasher_token=hash_token,
    )


def get_profile_service(profile_repo=Depends(get_profile_repo)):
    return ProfileService(
        profile_repo=profile_repo,
    )


def get_registration_service(
    user_service: UserService = Depends(get_user_service),
    profile_service: ProfileService = Depends(get_profile_service),
):
    return UserRegistrationController(
        user_service=user_service,
        profile_service=profile_service,
        session_factory=AsyncSessionLocal,
    )


def get_user_selector(
    user_repo=Depends(get_user_repo),
    profile_repo=Depends(get_profile_repo),
):
    return UserSelector(
        user_repo=user_repo,
        profile_repo=profile_repo,
        session_factory=AsyncSessionLocal,
    )


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    user_selector: UserSelector = Depends(get_user_selector),
) -> User:
    user = await user_selector.get_user(user_id)
    if not user:
        raise UserNotExists("User not found")
    return user
