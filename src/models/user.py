from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from infrastructure.sqlalchemy.base import CustomBase as Base

from .enums import UserRoleEnum


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("token_hash", name="uq_users_token_hash"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )  # must be set autoincrement if in tranasction boundery you have role back dont inscres id  and be consistans

    name: Mapped[str] = mapped_column(String(30), nullable=False)
    family: Mapped[str] = mapped_column(String(30), nullable=False)

    email: Mapped[str] = mapped_column(String(254), nullable=False, index=True)

    username: Mapped[str] = mapped_column(String(30), nullable=False)

    role: Mapped[UserRoleEnum] = mapped_column(
        Enum(UserRoleEnum), default=UserRoleEnum.USER, nullable=False
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    """for Fa later account"""
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verifyed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    profile: Mapped["Profile"] = relationship(
        "Profile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"

    @validates("username")
    def validate_username(self, key, value):

        value = value.lower().strip()

        if len(value) < 3:
            raise ValueError("username too short")

        if len(value) > 30:
            raise ValueError("username too long")

        return value

    @validates("name", "family")
    def validate_names(self, key, value):
        if len(value) < 2:
            raise ValueError(f"{key} is too short")
        if len(value) > 30:
            raise ValueError(f"{key} is too long")
        return value


class Profile(Base):  # add profile field
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    bio: Mapped[str] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<{self.__class__.__name__}>({self.user})"
