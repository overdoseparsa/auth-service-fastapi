from typing import Union
from urllib.parse import urlsplit, urlunsplit

from pydantic import (
    HttpUrl,
    PostgresDsn,
    RedisDsn,
    field_validator,
)
from pydantic_settings import (
    BaseSettings,
)


class Settings(BaseSettings):
    POST: int = 8000
    HOST: str = "localhost"

    ENVIRONMENT: str
    DATABASE_URL: PostgresDsn
    SECRET_KEY: str

    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 900
    REFRESH_TOKEN_EXPIRE_DAYS: int = 24 * 60 * 30
    AUDIENCE: str = "Auth_service"

    REDIS_URL: RedisDsn

    SQL_ECHO: bool = False

    HTTP_ONLY: bool = True
    HTTP_SECURE: bool = False
    SAME_SITE: str = "lax"
    ALLOWED_ORIGINS_LIST: list[Union[HttpUrl, str]] = ["https://localhost:8000"]

    ISSUER: str

    """
    validates and forces the use of asyncpg driver for PostgreSQL DSN
    if schema is not explicitly set to postgresql+asyncpg or postgres+asyncpg,
    it will be set to postgresql+asyncpg by default
    """

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_and_force_async_postgres_driver(cls, value: str) -> str:
        if not value:
            raise ValueError("DATABASE_URL is required")

        value = str(value)
        parsed = urlsplit(value)
        scheme = parsed.scheme

        if not scheme:
            raise ValueError(
                "DATABASE_URL must include a scheme, example: postgresql://user:pass@host:5432/db"
            )

        if scheme in {"postgresql+asyncpg", "postgres+asyncpg"}:
            return value

        base_scheme = scheme.split("+", 1)[0]

        if base_scheme not in {"postgresql", "postgres"}:
            raise ValueError("DATABASE_URL must be a PostgreSQL DSN")

        return urlunsplit(
            (
                "postgresql+asyncpg",
                parsed.netloc,
                parsed.path,
                parsed.query,
                parsed.fragment,
            )
        )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()  # type: ignore


def get_settings() -> Settings:
    return settings
