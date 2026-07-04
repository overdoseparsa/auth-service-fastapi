from typing import (
    Any,
)

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.security.refresh_tokens.repository import RefreshTokenStoreRepository
from core.security.utils.token_utils import hash_token

from .exceptions import TokenMissingClaimError
from .schams import RefreshTokenCreate, TokenPair
from .service import TokenService


class JWTController:
    def __init__(
        self,
        repository: RefreshTokenStoreRepository,
        service: TokenService,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self.repository: RefreshTokenStoreRepository = repository
        self.service: TokenService = service
        self.session_factory = session_factory

    @staticmethod
    def create_famliy_token(
        *args,
    ):
        family_token = ""
        for v in args:
            family_token += hash_token(v) + "."
        return family_token[:-1]

    async def create_token_pair(
        self,
        user_id: int,
        user_agent: str,
        ip_address: str,
        extra_claims: dict[str, Any] | None = None,
    ):

        refresh_token, refresh_token_recored = self.service.create_refresh_token(
            user_id=user_id, extra_claims=extra_claims
        )

        # must create refresh token

        async with self.session_factory() as session:
            async with session.begin():
                await self.repository.create_refresh_token(
                    session=session,
                    data=RefreshTokenCreate(
                        jti=refresh_token_recored.jti,
                        family_id=JWTController.create_famliy_token(
                            user_agent, ip_address
                        ),
                        user_id=user_id,
                        issued_at=self.service.convert_timestamp_datetime(
                            float(refresh_token_recored.iat)
                        ),
                        expires_at=self.service.convert_timestamp_datetime(
                            float(refresh_token_recored.exp)
                        ),
                        used_at=self.service.convert_timestamp_datetime(
                            float(refresh_token_recored.iat)
                        ),
                    ),
                )

        access_token, pyload = self.service.create_access_token(
            user_id=str(user_id), extra_claims=extra_claims
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def get_access_token(self, access_token: str, **context):
        decoded_access_token = self.service.decode_access_token(access_token)

        return decoded_access_token

    async def get_refresh_token(self, refresh_token: str, **context):
        decoded_refresh_token = self.service.decode_refresh_token(refresh_token)

        try:
            async with self.session_factory() as session:
                async with session.begin():
                    family_id = await self.repository.get_family_id(
                        session=session, jti=decoded_refresh_token.jti
                    )
                    if family_id is None:
                        raise TokenMissingClaimError("family_id not found")

        except Exception as e:
            raise TokenMissingClaimError(f"this jti is not valid {e}") from e

        return decoded_refresh_token, family_id

    async def create_access_token(
        self, user_id: str, extra_claims: dict = None, **context
    ):
        access_token, payload = self.service.create_access_token(
            user_id=str(user_id), extra_claims=extra_claims
        )

        return access_token, payload

    async def get_user_id(self, access_token: str, **context) -> str:
        decoded_access_token = self.service.decode_access_token(access_token)
        return decoded_access_token.sub
