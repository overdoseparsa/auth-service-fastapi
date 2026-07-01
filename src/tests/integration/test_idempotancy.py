import asyncio
import pytest
import pytest_asyncio
from core.idempotency.service import IdempotencyException, IdempotencyService
from tests.fixtures.redis import redis_real


@pytest_asyncio.fixture
async def idempotency_service(redis_real):

    yield IdempotencyService(redis_real)


@pytest.mark.asyncio
async def test_successful_first_request(idempotency_service):

    test_idempotency_value = "unique_key_1"
    
    result = await idempotency_service(test_idempotency_value)
    
    assert result == test_idempotency_value
    
    redis_key = f"idempotency:{test_idempotency_value}"
    redis_val = await idempotency_service.redis.get(redis_key)
    
    assert redis_val in (b"processing", "processing")


@pytest.mark.asyncio
async def test_concurrent_requests_race_condition(idempotency_service):

    test_idempotency_value = "concurrent_key"
    results = await asyncio.gather(
        idempotency_service(test_idempotency_value),
        idempotency_service(test_idempotency_value),
        idempotency_service(test_idempotency_value),
        idempotency_service(test_idempotency_value),
        idempotency_service(test_idempotency_value),
        return_exceptions=True  
    )

    successful_results = [r for r in results if not isinstance(r, Exception)]
    exceptions = [r for r in results if isinstance(r, Exception)]

    assert len(successful_results) == 1
    assert successful_results[0] == test_idempotency_value

    assert len(exceptions) == 4
    for exc in exceptions:
        assert isinstance(exc, IdempotencyException)
        assert "Request already in progress" in str(exc)


@pytest.mark.asyncio
async def test_request_after_mark_completed(idempotency_service):

    test_idempotency_value = "completed_flow_key"

    await idempotency_service(test_idempotency_value)

    await idempotency_service.mark_completed(test_idempotency_value)

    redis_key = f"idempotency:{test_idempotency_value}"
    redis_val = await idempotency_service.redis.get(redis_key)
    assert redis_val in (b"completed", "completed")

    with pytest.raises(IdempotencyException) as exc_info:
        await idempotency_service(test_idempotency_value)
    
    assert "Duplicate request" in str(exc_info.value)
