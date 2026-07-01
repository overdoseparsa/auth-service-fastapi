# tests/unit/users/test_register_api.py
import pytest
from main import app
from infrastructure.redis.client import get_redis_db

@pytest.fixture
def mock_idempotency(monkeypatch):
    app.dependency_overrides[idempotency_guard] = lambda: "fake-test-key"
    yield
    app.dependency_overrides.pop(idempotency_guard, None)

async def test_register_endpoint_success(client, mock_idempotency):
    response = await client.post("/api/v1/register", json={"email": "pars@test.com", ...})
    assert response.status_code == 201
