from datetime import datetime

from sqlalchemy import (
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from core.base.repository import BaseRepository
from core.exceptions import MustNotImplementError
from core.security.jwt.schams import RefreshTokenCreate
from models.tokens import RefreshTokenModel

from .base import RefreshTokenStore


class RefreshTokenStoreRepository(BaseRepository, RefreshTokenStore):
    model = RefreshTokenModel

    def __init__(self):
        super().__init__(self.model)

    async def create_refresh_token(
        self, session: AsyncSession, data: RefreshTokenCreate, auto_flush: bool = True
    ) -> RefreshTokenModel:
        return await super().create(session, auto_flush, **data.model_dump())

    async def get_by_jti(
        self, session: AsyncSession, jti: str
    ) -> RefreshTokenModel | None:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.jti == jti)
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None

        return row

    async def mark_used(
        self, session: AsyncSession, jti: str, used_at: datetime
    ) -> None:
        stmt = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.jti == jti)
            .values(used_at=used_at)
        )
        await session.execute(stmt)
        await session.flush()

    async def revoke(
        self, session: AsyncSession, jti: str, revoked_at: datetime
    ) -> None:
        stmt = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.jti == jti)
            .values(revoked_at=revoked_at)
        )
        await session.execute(stmt)
        await session.flush()

    async def revoke_family(
        self,
        session: AsyncSession,
        family_id: str,
        revoked_at: datetime,
        compromised: bool,
    ) -> None:
        stmt = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.family_id == family_id)
            .values(revoked_at=revoked_at, compromised=compromised)
        )
        await session.execute(stmt)
        await session.flush()

    async def get_by_family_id(
        self, session: AsyncSession, family_id: str
    ) -> list[RefreshTokenModel]:
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.family_id == family_id)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return rows

    async def revoke_refresh_token(
        self, session: AsyncSession, jti: str, revoked_at: datetime
    ) -> None:
        stmt = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.jti == jti)
            .values(revoked_at=revoked_at)
        )
        await session.execute(stmt)
        await session.flush()

    async def regenerate_refresh_token(
        self,
        session: AsyncSession,
        old_jti: str,
        data: RefreshTokenCreate,
        revoked_at_old: datetime,
    ) -> None:
        """
        Revokes the old refresh token and creates a new one.
        This is when a refresh token is rotated.
        and you create a new one with the same family_id.


        >>> await regenerate_refresh_token(session, old_jti, data, revoked_at_old)
        ... old_token_object = await self.get_by_jti(session, old_jti)
        ... old_token_object.rotated_from == data.jti  # True
        ... old_token_object.revoked_at == revoked_at_old  # True


        if You want to deactivate and create a new one hahaha
        """
        data.rotated_from = old_jti
        await self.revoke_refresh_token(session, old_jti, revoked_at_old)
        await self.create_refresh_token(session, data=data)

    async def activate_refresh_token(self, session: AsyncSession, jti: str) -> None:
        ...
        """
        it so important we dont have any active refresh tokens
        if that token was revoked
        never activate it again
        must create a new one

        for example:
            >>> await revoked_refresh_token = activate_refresh_token(session, jti)
            ... revoked_refresh_token.revoked_at is not None  # True
            ... revoked_refresh_token.used_at is None  # True
            ... print(revoked_refresh_token.rotated_from)
                jti - > abctoken

        You have update all fields and create complexly
        and inconssitance to update that log from action servers
        """

        raise MustNotImplementError("This function is must implemented")

    async def get_family_id(self, session: AsyncSession, jti: str) -> str:
        result = await session.execute(
            select(RefreshTokenModel.family_id).where(RefreshTokenModel.jti == jti)
        )
        return result.scalar_one_or_none()
