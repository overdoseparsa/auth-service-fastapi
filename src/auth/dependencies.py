from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.security.jwt.dependencies import get_jwt_controller
from infrastructure.redis.client import RedisManager
from infrastructure.sqlalchemy.AsyncSession import AsyncSessionLocal

from .controller import AuthController
from .expections import ForbiddenException
from .repository import AuthRepository


def get_auth_repository():
    return AuthRepository()


def get_auth_controller():
    return AuthController(
        repository=get_auth_repository(),
        jwt_controller=get_jwt_controller(),
        session_factory=AsyncSessionLocal,
        redis_manger=RedisManager(),
    )


http_bearer = HTTPBearer()


async def get_current_user_id(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(http_bearer)
):
    if credentials.scheme != "Bearer":
        raise ForbiddenException("Invalid Header")
    access_token = request.cookies.get("Access-Token")
    if not access_token:
        raise ForbiddenException("Access-Token is not provided")

    jwt_controller = get_jwt_controller()

    user_id = await jwt_controller.get_user_id(access_token)
    if not user_id:
        raise ForbiddenException("Invalid Access Token")

    return int(user_id)
