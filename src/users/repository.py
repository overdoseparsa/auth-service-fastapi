from sqlalchemy import exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.base.expections import NotFoundException
from core.base.repository import BaseRepository
from models.user import Profile, User

from .schemas import ProfileResponse, UserResponse


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, session: AsyncSession, email):
        stmt = select(User).where(func.lower(User.email) == func.lower(email))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def check_token_exists(self, session: AsyncSession, token_hash):
        stmt = select(exists().where(User.token_hash == token_hash))
        result = await session.execute(stmt)
        return result.scalar()

    async def get_list_user_profile_stmt(
        self, *, created_lt, created_gt, limit, offset, profile_model=Profile, **filters
    ):
        """

        PostgreSQL Dependency Notice

        This repository leverages PostgreSQL-specific JSON functions:
            - json_agg()
            - json_build_object()

        Make sure your database is PostgreSQL before using these queries.
        Other databases are NOT supported.

        """

        # stmt = select(
        #     func.json_build_object(
        #         'users'
        #     ) ,

        #     self.model
        #     ).options(joinedload(self.model.profile))

        stmt = select(self.model, profile_model).outerjoin(
            profile_model, self.model.id == profile_model.user_id
        )

        if filters:
            stmt = self.add_domain_filters(stmt, self.model, filters)

        stmt = self.filter_by_timezone(stmt, created_lt, created_gt, self.model)

        stmt = self.filter_by_limit_offset(stmt, limit, offset)
        # print(stmt)
        return stmt

    async def _serialize_get_list_user_profile(self, results):

        # results =  await session.execute(stmt)

        # print('res' ,results.all())

        data = [
            {
                "users": UserResponse.model_validate(d["User"]).model_dump(),
                "profiles": ProfileResponse.model_validate(d["Profile"]).model_dump(),
            }
            for d in results.mappings().all()
        ]

        return data

    async def update(self, session: AsyncSession, user_id: int, update_data: dict):

        invalid_fields = set(update_data) - self._valid_columns

        if invalid_fields:
            raise NotFoundException(f"invalid fields for {self.model.__name__}")
        stmt = (
            update(User).where(User.id == user_id).values(**update_data).returning(User)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(
        self, session: AsyncSession, username: str
    ) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


class ProfileRepository(BaseRepository):
    def __init__(self):
        super().__init__(Profile)

    async def get_by_user_id(self, session, user_id):
        stmt = select(Profile).where(Profile.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
