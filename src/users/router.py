from datetime import datetime
from typing import List, Optional, Union

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    Response,
)

from .controllers import (
    UserRegistrationController,
)
from .dependencies import get_registration_service, get_user_selector
from .schemas import (
    ListUserResponse,
    ProfileResponse,
    QueryFilterUsers,
    UserRegiserWithProfile,
    UserRegister,
    UserResponse,
    UserUpdate,
    UserWithProfile,
)
from .selectors import UserSelector

"""
Hint : Apis Error handeling in the main.py with

"""


router = APIRouter()


@router.post("/users", response_model=UserRegiserWithProfile)
async def register_user(
    user_register_data: UserRegister,
    registration_service: UserRegistrationController = Depends(
        get_registration_service
    ),
):
    user, token, profile = await registration_service.register(
        data=user_register_data,
    )

    return UserRegiserWithProfile(
        user=UserResponse.model_validate(user),
        profile=ProfileResponse.model_validate(profile),
        token=token,
    )


@router.get("/me", response_model=UserWithProfile)
async def get_user(
    user_selector: UserSelector = Depends(get_user_selector),
    # will be added auth get_current_user
    inc_profile: bool = Query(True, description="Include user's profile"),
):
    # currnet user 1
    cur_user = 1

    user, profile = await user_selector.get_user_with_profile(
        user_id=cur_user, with_profile=inc_profile
    )

    return UserWithProfile(
        user=UserResponse.model_validate(user),
        profile=(
            ProfileResponse.model_validate(profile) if inc_profile and profile else None
        ),
    )


@router.get("/users", response_model=ListUserResponse)
async def get_user(
    user_selector: UserSelector = Depends(get_user_selector),
    filters: QueryFilterUsers = Depends(),
    created_lt: Optional[datetime] = Query(
        None, description="Filter users created before this date"
    ),
    created_gt: Optional[datetime] = Query(
        None, description="Filter users created after this date"
    ),
    limit: int = Query(
        10, description="Maximum number of users to return", ge=1, le=10000000
    ),
    offset: int = Query(0, description="Number of users to skip", ge=0),
    # TODO add in the  pydantic schamas dublicate query params
):

    users, total = await user_selector.get_all_users(
        created_lt=created_lt,
        created_gt=created_gt,
        limit=limit,
        offset=offset,
        **filters.model_dump(
            exclude_none=True,
        ),
    )
    return ListUserResponse(users=users, count=total)


@router.get("/users-profile")
async def get_user_profile(
    user_selector: UserSelector = Depends(get_user_selector),
    filters: QueryFilterUsers = Depends(),
    created_lt: Optional[datetime] = Query(
        None, description="Filter users created before this date"
    ),
    created_gt: Optional[datetime] = Query(
        None, description="Filter users created after this date"
    ),
    limit: int = Query(
        10, description="Maximum number of users to return", ge=1, le=10000000
    ),
    offset: int = Query(0, description="Number of users to skip", ge=0),
):

    resualt = await user_selector.get_all_user_with_profile(
        created_lt=created_lt,
        created_gt=created_gt,
        limit=limit,
        offset=offset,
        **filters.model_dump(exclude_none=True),
    )

    return resualt


@router.put("/users", response_model=UserResponse)
async def update_profile(
    user_id: int,
    user_update_data: UserUpdate,
    registration_service: UserRegistrationController = Depends(
        get_registration_service
    ),
):
    user = await registration_service.update_user(
        user_id=user_id,
        data=user_update_data,
    )

    return user
