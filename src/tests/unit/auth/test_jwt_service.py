import pytest
from jose import ExpiredSignatureError, JWTError, jwt

from core.security.jwt.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    TypeTokenError,
)
from tests.fixtures.auth.service import (
    expired_fake_payload,
    fake_payload,
    token_service,
)


def test_token_service_base_calm(token_service, fake_payload):
    pyload = fake_payload

    encoded_pyload: str = token_service._encode(pyload)
    decoded_pyload: dict = token_service._decode(encoded_pyload, return_dict=True)

    assert decoded_pyload is not None, (
        "token Service Decode Not Returning decoded payload"
    )
    assert decoded_pyload["sub"] == pyload["sub"], "not same subject"
    assert decoded_pyload["type"] == pyload["type"], "not same token type"
    assert decoded_pyload["iat"] == pyload["iat"], "not same iat"
    assert decoded_pyload["exp"] == pyload["exp"], "not same exp"


def test_token_service_decode_invalid_token(token_service):
    invalid_token = "access_token : hello world"

    with pytest.raises(InvalidTokenError):
        token_service._decode(invalid_token, return_dict=True)


def test_token_service_decode_expired_token(token_service, expired_fake_payload):
    pyload = expired_fake_payload
    encoded_pyload: str = token_service._encode(pyload)

    with pytest.raises(TokenExpiredError):
        token_service._decode(encoded_pyload, return_dict=True)


def test_token_service_type_error(token_service, fake_payload):
    fake_payload["type"] = "hello_world"
    encoded_pyload: str = token_service._encode(fake_payload)

    with pytest.raises(TypeTokenError):
        token_service._decode(encoded_pyload, return_dict=True)
