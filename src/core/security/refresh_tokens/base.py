from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession


class RefreshTokenStore(ABC):
    @abstractmethod
    async def mark_used(
        self, session: AsyncSession, jti: str, used_at: datetime
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def revoke(
        self, session: AsyncSession, jti: str, revoked_at: datetime
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def revoke_family(
        self,
        session: AsyncSession,
        family_id: str,
        revoked_at: datetime,
        compromised: bool,
    ) -> None:
        raise NotImplementedError
