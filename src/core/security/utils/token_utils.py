import hashlib
import hmac
import secrets

from core.config import settings


def generate_token(length: int = 20) -> str:
    return secrets.token_urlsafe(length)


def hash_token(token: str, secret: str = settings.SECRET_KEY) -> str:
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
