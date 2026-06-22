from pydantic import BaseModel

from models.user import Base


class LoginSchema(BaseModel):
    username: str
    password: str


class RegisterAccessSchema(BaseModel):
    "here get that accesstoken to validate and retrieve"

    access_token: str


class RegisterRefreshSchema(BaseModel):
    "here get that accesstoken to validate and retrieve"

    refresh_token: str


class logoutSchamas(BaseModel):
    access_token: str
    refresh_token: str
