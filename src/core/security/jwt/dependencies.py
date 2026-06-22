from core.config import settings
from core.security.refresh_tokens.repository import RefreshTokenStoreRepository
from infrastructure.sqlalchemy.AsyncSession import AsyncSessionLocal

from .controller import JWTController
from .service import TokenService


def get_refresh_token_repositoy():
    return RefreshTokenStoreRepository()


def get_token_service():
    return TokenService(secret_key=settings.SECRET_KEY, audience=settings.AUDIENCE)


def get_jwt_controller():
    return JWTController(
        service=get_token_service(),
        repository=get_refresh_token_repositoy(),
        session_factory=AsyncSessionLocal,
    )
