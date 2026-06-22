from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from infrastructure.sqlalchemy.base import CustomBase as Base

from .user import User


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(100))

    token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    created_at: Mapped[datetime]
    last_used_at: Mapped[datetime | None]

    revoked: Mapped[bool] = mapped_column(default=False)

    user: Mapped["User"] = relationship(backref="api_tokens")


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    __table_args__ = (UniqueConstraint("jti", name="jti_refresh_tokens"),)

    jti: Mapped[str] = mapped_column(
        String(256), primary_key=True, unique=True, index=True
    )
    # user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )

    family_id: Mapped[str] = mapped_column(String(256), nullable=True, index=True)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    rotated_from: Mapped[str | None] = mapped_column(String(64), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    compromised: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
