import asyncio
from unittest.mock import AsyncMock


async def Session_Mock():

    async def execute(stmt, *args):
        print("Execute that querys", stmt, args)
        await asyncio.sleep(0.01)

    async def rollback():
        print("Rollback")
        await asyncio.sleep(0.01)

    async def commit():
        print("Commit")
        await asyncio.sleep(0.01)

    async def flush():
        print("Flush")
        await asyncio.sleep(0.01)

    async def close():
        print("Close")
        await asyncio.sleep(0.01)

    async def delete(obj):
        print("Delete", obj)
        await asyncio.sleep(0.01)

    async def add(obj):
        print("Add", obj)
        await asyncio.sleep(0.01)

    result = AsyncMock()
    result.scalar.return_value = None
    result.scalar_one_or_none.return_value = None

    session = AsyncMock()
    session.execute.side_effect = execute
    session.rollback.side_effect = rollback
    session.commit.side_effect = commit
    session.flush.side_effect = flush
    session.close.side_effect = close
    session.delete.side_effect = delete
    session.add.side_effect = add

    session.execute.return_value = result

    return session
