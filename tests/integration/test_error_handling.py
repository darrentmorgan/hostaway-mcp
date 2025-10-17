"""Integration tests for batch operations and error handling."""

import pytest

from src.mcp.auth import TokenManager
from src.mcp.config import HostawayConfig
from src.services.hostaway_client import HostawayClient
from src.services.rate_limiter import RateLimiter


@pytest.fixture
async def hostaway_client():
    """Create HostawayClient for testing.

    Uses test configuration and creates a real client instance
    for integration testing with batch operations.
    """
    config = HostawayConfig()  # type: ignore[call-arg]
    token_manager = TokenManager(config=config)
    rate_limiter = RateLimiter()
    client = HostawayClient(
        config=config,
        token_manager=token_manager,
        rate_limiter=rate_limiter,
    )
    yield client
    await client.aclose()


@pytest.mark.asyncio
async def test_batch_operations_all_success(hostaway_client):
    """Test batch operations where all succeed."""

    async def mock_success_op(value: int):
        """Mock operation that always succeeds."""
        return {"status": "success", "id": value}

    operations = [lambda v=i: mock_success_op(v) for i in range(3)]
    result = await hostaway_client.execute_batch(operations)

    assert result.total_count == 3
    assert result.success_count == 3
    assert result.failure_count == 0
    assert result.has_successes is True
    assert result.has_failures is False
    assert len(result.successful) == 3
    assert result.partial_success is False


@pytest.mark.asyncio
async def test_batch_operations_mixed_results(hostaway_client):
    """Test batch operations with mixed success/failure."""

    async def success_op():
        """Operation that succeeds."""
        return {"status": "success"}

    async def failure_op():
        """Operation that fails."""
        raise ValueError("Test failure")

    operations = [success_op, failure_op, success_op]
    operation_ids = ["op_1", "op_2", "op_3"]

    result = await hostaway_client.execute_batch(operations, operation_ids)

    assert result.total_count == 3
    assert result.success_count == 2
    assert result.failure_count == 1
    assert result.partial_success is True

    # Check failed operation details
    assert len(result.failed) == 1
    assert result.failed[0].operation_id == "op_2"
    assert "Test failure" in result.failed[0].error  # type: ignore[operator]

    # Check successful operations
    assert len(result.successful) == 2
    assert result.successful[0].operation_id == "op_1"
    assert result.successful[1].operation_id == "op_3"


@pytest.mark.asyncio
async def test_batch_operations_all_failed(hostaway_client):
    """Test batch operations where all fail."""

    async def failure_op(error_msg: str):
        """Operation that fails with specific message."""
        raise RuntimeError(error_msg)

    operations = [
        lambda: failure_op("Error 1"),
        lambda: failure_op("Error 2"),
    ]

    result = await hostaway_client.execute_batch(operations)

    assert result.total_count == 2
    assert result.success_count == 0
    assert result.failure_count == 2
    assert result.has_failures is True
    assert result.has_successes is False
    assert len(result.failed) == 2
    assert result.partial_success is False


@pytest.mark.asyncio
async def test_batch_operations_preserves_order(hostaway_client):
    """Test that batch operations preserve execution order."""

    results_order = []

    async def tracked_op(value: int):
        """Operation that tracks execution order."""
        results_order.append(value)
        return {"value": value}

    operations = [
        lambda: tracked_op(1),
        lambda: tracked_op(2),
        lambda: tracked_op(3),
    ]

    result = await hostaway_client.execute_batch(operations)

    # Verify operations executed in order
    assert results_order == [1, 2, 3]
    assert result.success_count == 3

    # Verify results are in order
    assert result.successful[0].data["value"] == 1  # type: ignore[index]
    assert result.successful[1].data["value"] == 2  # type: ignore[index]
    assert result.successful[2].data["value"] == 3  # type: ignore[index]


@pytest.mark.asyncio
async def test_batch_operations_with_different_error_types(hostaway_client):
    """Test batch operations with different exception types."""

    async def value_error_op():
        raise ValueError("Value error")

    async def type_error_op():
        raise TypeError("Type error")

    async def success_op():
        return {"status": "ok"}

    operations = [value_error_op, type_error_op, success_op]

    result = await hostaway_client.execute_batch(operations)

    assert result.total_count == 3
    assert result.success_count == 1
    assert result.failure_count == 2

    # Check error types are captured
    assert "ValueError" in str(result.failed[0].error) or "Value error" in str(
        result.failed[0].error
    )
    assert "TypeError" in str(result.failed[1].error) or "Type error" in str(result.failed[1].error)


@pytest.mark.asyncio
async def test_batch_operations_empty_list(hostaway_client):
    """Test batch operations with empty operations list."""

    operations = []  # type: ignore[var-annotated]
    result = await hostaway_client.execute_batch(operations)

    assert result.total_count == 0
    assert result.success_count == 0
    assert result.failure_count == 0
    assert result.has_successes is False
    assert result.has_failures is False


@pytest.mark.asyncio
async def test_batch_operations_custom_operation_ids(hostaway_client):
    """Test batch operations with custom operation IDs."""

    async def simple_op():
        return {"result": "done"}

    operations = [simple_op, simple_op, simple_op]
    operation_ids = ["custom_1", "custom_2", "custom_3"]

    result = await hostaway_client.execute_batch(operations, operation_ids)

    assert result.success_count == 3
    assert result.successful[0].operation_id == "custom_1"
    assert result.successful[1].operation_id == "custom_2"
    assert result.successful[2].operation_id == "custom_3"


@pytest.mark.asyncio
async def test_batch_operations_auto_generated_ids(hostaway_client):
    """Test batch operations with auto-generated operation IDs."""

    async def simple_op():
        return {"result": "done"}

    operations = [simple_op, simple_op]

    result = await hostaway_client.execute_batch(operations)

    # Should auto-generate IDs like "op_0", "op_1"
    assert result.successful[0].operation_id == "op_0"
    assert result.successful[1].operation_id == "op_1"


@pytest.mark.asyncio
async def test_batch_operations_logs_failures(hostaway_client, caplog):
    """Test that batch operations log failures appropriately."""

    async def failing_op():
        raise RuntimeError("Intentional test failure")

    operations = [failing_op]
    operation_ids = ["test_op"]

    with caplog.at_level("WARNING"):
        result = await hostaway_client.execute_batch(operations, operation_ids)

    assert result.failure_count == 1

    # Check that failure was logged
    assert any("Batch operation test_op failed" in record.message for record in caplog.records)
