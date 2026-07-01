import pytest

from core.base.expections import NotFoundException
from core.security.utils.hashing import hash_password, verify_password
from core.security.utils.token_utils import generate_token, hash_token
from tests.fixtures.db import db_session as fake_session
from tests.fixtures.users.service import get_user_sample, user_service

"""
User Sample test
>>> UserRegister(
    username="testuser",
    email="test@example.com",
    password="password",
    name="Test",
    family="User"
    )


"""


@pytest.mark.asyncio
async def test_pre_create_user_returns_token_and_hashed_password(
    user_service, get_user_sample
):
    user_data = get_user_sample
    user_pyload, token = await user_service.pre_create_user_process(user_data)

    assert token is not None, "Token should not be None"
    assert user_pyload is not None, "User Pyload should not be None"
    assert user_pyload.get("username") == "testuser", "Username should be testuser"
    assert user_pyload.get("email") == "test@example.com", (
        "Email should be test@example.com"
    )

    assert user_pyload.get("password_hash") is not None, (
        "Password hash should not be None"
    )

    assert (
        await verify_password(user_data.password, user_pyload.get("password_hash"))
        is True
    ), "Password should be verified"

    assert user_pyload.get("name") == "Test", "Name should be Test"
    assert user_pyload.get("family") == "User", "Family should be User"


# for create user we need integration tests


@pytest.mark.asyncio
async def test_create_user_with_fake_session(
    user_service, get_user_sample, fake_session
):

    user_data = get_user_sample
    user_field, token = await user_service.pre_create_user_process(user_data)
    user = await user_service.db_create_user_process(fake_session, user_field)

    assert user is not None, "User should not be None"

    assert user.username == user_field.get("username"), "Username should match"
    assert user.email == user_field.get("email"), "Email should match"
    assert user.name == user_field.get("name"), "Name should match"
    assert user.family == user_field.get("family"), "Family should match"
    assert user.password_hash is not None, "Password hash should not be None"
