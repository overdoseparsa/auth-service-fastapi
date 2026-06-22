from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from models.enums import UserRoleEnum


class UserBase(BaseModel):
    name: str
    family: str
    username: str
    email: EmailStr


class UserRegister(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    family: Optional[str] = None
    username: Optional[str] = None


class UserResponse(UserBase):
    id: int
    role: UserRoleEnum
    is_active: bool
    is_verifyed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ListUserResponse(BaseModel):
    users: Optional[List[UserResponse]]
    count: int = 0


class ProfileBase(BaseModel):
    bio: Optional[str] = None


class ProfileCreate(ProfileBase):
    user_id: int


class ProfileUpdate(BaseModel):
    bio: Optional[str] = None


class ProfileResponse(ProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class UserWithProfile(BaseModel):
    user: UserResponse
    profile: Optional[ProfileResponse] = None


class UserRegiserWithProfile(UserWithProfile):
    token: str


class QueryFilterUsers(BaseModel):
    role: Optional[UserRoleEnum] = Field(
        default=None,
        description="Filter users by role",
    )
    is_active: Optional[bool] = Field(
        default=True,
        description="Filter users by active status",
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Filter by exact creation datetime",
    )


class QueryFilterProfile(QueryFilterUsers):
    pass  # TODO add for join profile and user
