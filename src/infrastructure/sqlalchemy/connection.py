from core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=True,
    pool_size=20,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    future=True,
)
