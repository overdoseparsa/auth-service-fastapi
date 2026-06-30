import logging
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

logger = logging.getLogger(__name__)  # TOOD use aiologger


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
        logger.info("Creating user", extra={"email": data.email})

        user_dict = data.model_dump()
        try:
            token = self.token_generator()
        except Exception:
            raise TokenGenerationError()

        try:
            token_hash = self.hasher_token(token)
            password_hash = await self.hasher_password(user_dict.pop("password"))
        except Exception as e:
            print("e", e)
            raise

        fields = {
            **{"password_hash": password_hash, "token_hash": token_hash},
            **user_dict,
        }
        return fields, token


    async def db_create_user_process(self, session: AsyncSession, fields: dict):

        try:
            return await self.user_repo.create(session, **fields)

        except IntegrityError as exc:
            print("Error from debugging ,,, ", exc)
            # hint : This work just in postgres database driver
            if exc.orig.pgcode == "23505":  # unique_violation
                print(
                    "Error3 from debugging ,,, ",
                    type(exc),
                    "yupe3",
                    type(exc.orig),
                    "type3 ... ",
                    type(exec),
                )

                if isinstance(exc, UniqueViolationError):
                    constraint: str | None = get_constraint_name_postgres(exc)

                    if constraint == "uq_users_email":
                        raise EmailAlreadyExists(message="email is alredey exist's")

                    if constraint == "uq_users_username":
                        raise UsernameAlreadyExists("username already exists")

            if exc.orig.pgcode == "40001":  #  Serialization Failure
                raise ConcurrencyError("Serialization Failure")

            raise DatabaseOperationError(f"DatabaseError : Check System {exc}")

        except DBAPIError as e:
            logger.error(f"Database connection error: {e}")
            raise DatabaseOperationError(f"DatabaseError : Check System {e}")

    async def after_create_user_process(self, user: User) -> None:

        logger.info(
            "User created successfully", extra={"user_id": user.id, "email": user.email}
        )

        

    async def update_user(self, session: AsyncSession, user_id: int, data: UserUpdate):
        try:
            updated_user = await self.user_repo.update(
                session=session,
                user_id=user_id,
                update_data=data.model_dump(exclude_unset=True),
            )

            return updated_user
        except Exception as e:
            raise e

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
        logger.info("Creating profile", extra={"profile_id": profile.id})
