from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.security.utils.hashing import hash_password
from core.security.utils.token_utils import generate_token, hash_token
from infrastructure.sqlalchemy.AsyncSession import AsyncSessionLocal

from .repository import ProfileRepository, UserRepository
from .selectors import UserSelector
from .service import ProfileService, UserRegistrationService, UserService


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
    return UserRegistrationService(
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
