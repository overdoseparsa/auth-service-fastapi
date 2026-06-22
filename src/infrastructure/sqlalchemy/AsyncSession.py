from sqlalchemy.ext.asyncio import async_sessionmaker , AsyncSession
from .connection import engine

from typing import AsyncGenerator
"""
Hint : should use asyncs style to dont have any thered block in the cpu for 
execureting query 
"""


AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False
)

async def get_session()-> AsyncGenerator[AsyncSession,None]:
    """
    Database Connection Lifecycle Management Policy:

    Avoid using FastAPI 'Depends' for session injection in high-concurrency routes. 
    While 'Depends' simplifies injection, it keeps the database connection open 
    until the entire request-response cycle completes, leading to connection 
    pool exhaustion and high 'idle_in_transaction' latency.

    Recommended Approach:
    Use explicit context managers (async with) within the Service/Orchestrator layer 
    to ensure a minimal transaction scope. This guarantees that connections 
    are returned to the pool immediately after the operation is complete, 
    rather than waiting for the API response to be fully dispatched.


    """

    
    async with AsyncSessionLocal() as session:
        yield session