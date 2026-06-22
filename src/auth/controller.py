from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.security.jwt.controller import JWTController
from core.security.utils.hashing import hash_password
from infrastructure.redis.client import RedisManager

from .expections import PasswordError, TokenInvalidError, TokenRevokedError
from .repository import AuthRepository
from .schamas import (
    LoginSchema,
    RegisterAccessSchema,
    RegisterRefreshSchema,
    logoutSchamas,
)


class AuthController:
    def __init__(
        self,
        repository: AuthRepository,
        session_factory: async_sessionmaker[AsyncSession],
        jwt_controller: JWTController,
        redis_manger: RedisManager,
    ) -> None:

        self.repository = repository
        self.session_factory = session_factory
        self.jwt_controller = jwt_controller
        self.redis_manager = redis_manger

    async def login(self, data: LoginSchema, **context):

        async with (
            self.session_factory() as session
        ):  # Just connection Here for prevent idle_transaction and less session active
            async with session.begin():
                user = await self.repository.get_user_by_username(
                    session=session, username=data.username
                )

        if not user:
            raise PasswordError("User not found")

        if hash_password(data.password) != user.password_hash:
            raise PasswordError("Invalid password")

        assert context.get("context").get("request"), "must context for request"
        request = context["context"]["request"]

        user_agent = request.user_agent
        ip_address = request.ip_address.host

        token_pair = await self.jwt_controller.create_token_pair(
            user_id=user.id,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        return token_pair

    async def register_access(
        self,
        data: RegisterAccessSchema,
        **context,
    ):
        access_token = data.access_token

        payload = await self.jwt_controller.get_access_token(access_token)

        is_revoked = await self.redis_manager.get(f"revoked_access_token:{payload.jti}")

        if is_revoked:
            raise TokenInvalidError("access token is invalid")

        return payload

    async def register_refresh(
        self,
        data: RegisterRefreshSchema,
        **context,
    ):
        refresh_token = data.refresh_token

        payload, family_id = await self.jwt_controller.get_refresh_token(refresh_token)

        is_revoked = await self.redis_manager.get(
            f"revoked_refresh_token:{payload.jti}"
        )

        if is_revoked:
            raise TokenInvalidError("refresh token is invalid")

        return payload, family_id

    async def refresh(
        self,
        data: RegisterRefreshSchema,
    ):

        refresh_token = data.refresh_token

        refresh_token_payload, family_id = await self.jwt_controller.get_refresh_token(
            refresh_token
        )

        is_revoked = await self.redis_manager.get(
            f"revoked_refresh_token:{refresh_token_payload.jti}"
        )

        if is_revoked:
            raise TokenInvalidError("refresh token is invalid")

        async with (
            self.session_factory() as session
        ):  # Just connection Here for prevent idle_transaction and less session active
            async with session.begin():
                refresh_token_model = await self.jwt_controller.repository.get_by_jti(
                    session,
                    refresh_token_payload.jti,
                )
                if not refresh_token_model:
                    raise TokenInvalidError("tokan was invalidate in model class")
                await self.jwt_controller.repository.mark_used(
                    session,
                    refresh_token,
                    datetime.now(),
                )

            if refresh_token_model.revoked_at:
                raise TokenRevokedError("Refresh token was revoked")

        (
            create_access_token,
            access_token_pyload,
        ) = await self.jwt_controller.create_access_token(
            user_id=refresh_token_payload.sub,
        )

        return create_access_token, family_id

    async def logout(
        self,
        data: logoutSchamas,
        **context,
    ):
        # first check if the token is valid
        access_token = data.access_token
        try:
            access_token_payload = await self.jwt_controller.get_access_token(
                access_token
            )
        except Exception as e:
            raise TokenInvalidError(f"access token is invalid {e}")

        refresh_token = data.refresh_token
        try:
            (
                refresh_token_payload,
                family_id,
            ) = await self.jwt_controller.get_refresh_token(refresh_token)
        except Exception as e:
            raise TokenInvalidError(f"refresh token is invalid {e}")

        # check if the refresh token is valid or not revoked
        async with (
            self.session_factory() as session
        ):  # Just connection Here for prevent idle_transaction and less session active
            async with session.begin():
                # get refresh token
                refresh_token_model = await self.jwt_controller.repository.get_by_jti(
                    session,
                    refresh_token_payload.jti,
                )
                # mark as last
                if refresh_token_model is None:
                    raise TokenInvalidError("refresh token is invalid")

                await self.jwt_controller.repository.mark_used(
                    session,
                    refresh_token_model.jti,
                    datetime.now(),
                )

                if refresh_token_model.revoked_at:
                    raise TokenInvalidError("refresh token is invalid it revoked")

                await self.jwt_controller.repository.revoke(
                    session,
                    refresh_token_model.jti,
                    datetime.now(),
                )

        await self.redis_manager.set(
            f"revoked_refresh_token:{refresh_token_payload.jti}",
            "1",  # TODO need data
            ex=30,
        )

        """
        Hint that accces token is state less
        but in secure system we can store in redis
        to prevent replay attacks

        and have ttl  just 5 min ot that can be configured
        """

        await self.redis_manager.set(
            f"revoked_access_token:{access_token_payload.jti}",
            "1",  # TODO need data
            ex=5,
        )

        return True
