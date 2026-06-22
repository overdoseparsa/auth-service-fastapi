from core.security.jwt.dependencies import get_jwt_controller
from infrastructure.redis.client import RedisManager
from infrastructure.sqlalchemy.AsyncSession import AsyncSessionLocal

from .controller import AuthController
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
