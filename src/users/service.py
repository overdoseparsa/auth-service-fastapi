from aiologger import Logger
from typing import (
    Awaitable,
    Callable,
    List,
    Optional,
    Tuple,
    Dict,
    Any
)

from asyncpg.exceptions import UniqueViolationError
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing_extensions import Coroutine

from core.base.repository import BaseRepository
from core.base.services import BaseAbstractService

from .exceptions import (
    ConcurrencyError,
    DatabaseOperationError,
    EmailAlreadyExists,
    HashingFailedError,
    TokenGenerationError,
    UsernameAlreadyExists,
    UserNotExists,
)
from .repository import Profile, User
from .schemas import (
    ProfileCreate,
    UserRegister,
    UserUpdate,
)

logger = Logger.with_default_handlers(name='users_logger')


def get_constraint_name_postgres(exc: UniqueViolationError) -> Optional[str]:
    return exc.orig.constraint_name


class UserService(BaseAbstractService):
    service_name = "USER_SERVICE"

    def __init__(
        self,
        user_repo: BaseRepository,
        token_generator: Callable,
        hasher_password: Callable[[str], Awaitable[str]],
        hasher_token: Callable[[str], str],
    ):
        self.user_repo = user_repo
        self.token_generator = token_generator
        self.hasher_password = hasher_password
        self.hasher_token = hasher_token


    async def pre_create_user_process(self, data: UserRegister) -> Tuple[Dict[str, Any], str]:
        await logger.info("Creating user", extra={"email": data.email})

        user_dict = data.model_dump()
        try:
            token = self.token_generator()
        except Exception:
            raise TokenGenerationError()

        try:
            token_hash = self.hasher_token(token)
            password_hash = await self.hasher_password(user_dict.pop("password"))
        except Exception as e:
            raise

        fields = {
            **{"password_hash": password_hash, "token_hash": token_hash},
            **user_dict,
        }
        return fields, token


    async def db_create_user_process(self, session: AsyncSession, fields: dict) -> User:
        try:
            return await self.user_repo.create(session, **fields)

        except IntegrityError as exc:
            orig_exc = exc.orig
            
            if not orig_exc:
                await logger.error("IntegrityError occurred without underlying driver exception")
                raise DatabaseOperationError("Database integrity violation occurred")

            pgcode = getattr(orig_exc, "pgcode", None)

            if pgcode == "40001":
                raise ConcurrencyError("Serialization Failure. Please retry transaction.")

            if pgcode == "23505":
                constraint_name = getattr(orig_exc, "constraint_name", None)
                
                if not constraint_name and hasattr(orig_exc, "message"):
                    constraint_name = str(orig_exc.message)

                await logger.warning(
                    "Unique constraint violation occurred",
                    extra={"constraint": constraint_name}
                )

                if constraint_name:
                    if "uq_users_email" in constraint_name:
                        raise EmailAlreadyExists("Email is already registered.")
                    if "uq_users_username" in constraint_name:
                        raise UsernameAlreadyExists("Username is already taken.")
                    if "uq_users_token_hash" in constraint_name:
                        raise DatabaseOperationError("Token collision detected.")

                raise DatabaseOperationError("Unique constraint violated on user creation.")

            await logger.error("Database integrity error occurred", exc_info=True)
            raise DatabaseOperationError(f"Database validation failed: {exc}")

        except DBAPIError as exc:
            await logger.critical("Database connection or API level failure", exc_info=True)
            raise DatabaseOperationError(f"Database connection error: {exc}")

    async def after_create_user_process(self, user: User) -> None:

        await logger.info(
            "User created successfully", extra={"user_id": user.id, "email": user.email}
        )

        

    # async def update_user(self, session: AsyncSession, user_id: int, data: UserUpdate):
    #     try:
    #         updated_user = await self.user_repo.update(
    #             session=session,
    #             user_id=user_id,
    #             update_data=data.model_dump(exclude_unset=True),
    #         )

    #         return updated_user
    #     except Exception as e:
    #         raise e
        

    async def update_user(self, session: AsyncSession, user_id: int, data: UserUpdate) -> User:
        user = await self.user_repo.get(session, user_id)
        if not user:
            raise UserNotExists("User not found")

        try:
            updated_user = await self.user_repo.update(
                session=session,
                user_id=user.id,
                update_data = data.model_dump(exclude_unset=True),
            )
            return updated_user

        except IntegrityError as exc:
            orig_exc = exc.orig
            if not orig_exc:
                raise DatabaseOperationError("Database integrity violation during update.")

            pgcode = getattr(orig_exc, "pgcode", None)

            if pgcode == "23505":
                constraint_name = getattr(orig_exc, "constraint_name", None)
                if not constraint_name and hasattr(orig_exc, "message"):
                    constraint_name = str(orig_exc.message)

                await logger.warning(
                    "Unique constraint violation during user update",
                    extra={"user_id": user_id, "constraint": constraint_name}
                )

                if constraint_name:
                    if "uq_users_email" in constraint_name:
                        raise EmailAlreadyExists("Email is already registered.")
                    if "uq_users_username" in constraint_name:
                        raise UsernameAlreadyExists("Username is already taken.")
                
                raise DatabaseOperationError("Unique constraint violated on user update.")

            if pgcode == "40001":
                raise ConcurrencyError("Serialization Failure. Please retry transaction.")

            raise DatabaseOperationError(f"Database error during update: {exc}")

        except DBAPIError as exc:
            await logger.critical(f"Database connection error during update for user {user_id}", exc_info=True)
            raise DatabaseOperationError(f"Database connection error: {exc}")


    # async def create_bulk_user(self, session: AsyncSession, users_data: UsersRegister):
    #     try:
    #         users_data = users_data

    #     except Exception as e:
    #         raise e


class ProfileService(BaseAbstractService):
    service_name = "PROFILE_SERVICE"

    def __init__(self, profile_repo: BaseRepository):
        self.profile_repo = profile_repo

    async def db_create_profile_process(self, session: AsyncSession, user: User):
        try:
            return await self.profile_repo.create(session, **{"user": user})

        except IntegrityError as exc:
            if "user" in str(exc).lower():
                raise UserNotExists(message="User not found")
            raise

    async def after_create_profile_process(self, profile: Profile):
        await logger.info("Creating profile", extra={"profile_id": profile.id})
