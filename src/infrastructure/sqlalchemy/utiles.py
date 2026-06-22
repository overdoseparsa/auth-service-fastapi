from .base import Base
from .connection import engine
from models import * 


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
