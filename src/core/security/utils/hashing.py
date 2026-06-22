from fastapi.concurrency import run_in_threadpool
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)


def hash_password_sync(password: str) -> str:
    return pwd_context.hash(password)


def verify_password_sync(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


async def hash_password(password: str) -> str:
    return await run_in_threadpool(hash_password_sync, password)


async def verify_password(password: str, password_hash: str) -> bool:
    return await run_in_threadpool(verify_password_sync, password, password_hash)
