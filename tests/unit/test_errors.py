"""Unit tests for error and partial failure response models."""

from src.models.errors import OperationResult, PartialFailureResponse


def test_partial_failure_response_all_success():
    """Test response with all successful operations."""
    response = PartialFailureResponse[dict](
        successful=[
            OperationResult[dict](success=True, data={"id": 1}, operation_id="op_1"),
            OperationResult[dict](success=True, data={"id": 2}, operation_id="op_2"),
        ],
        failed=[],
        total_count=2,
        success_count=2,
        failure_count=0,
    )

    assert response.has_successes is True
    assert response.has_failures is False
    assert response.partial_success is False
    assert len(response.successful) == 2
    assert len(response.failed) == 0
    assert response.total_count == 2


def test_partial_failure_response_all_failed():
    """Test response with all failed operations."""
    response = PartialFailureResponse[dict](
        successful=[],
        failed=[
            OperationResult[dict](success=False, error="Not found", operation_id="op_1"),
            OperationResult[dict](success=False, error="Timeout", operation_id="op_2"),
        ],
        total_count=2,
        success_count=0,
        failure_count=2,
    )

    assert response.has_successes is False
    assert response.has_failures is True
    assert response.partial_success is False
    assert len(response.successful) == 0
    assert len(response.failed) == 2
    assert response.total_count == 2


def test_partial_failure_response_mixed():
    """Test response with both successful and failed operations."""
    response = PartialFailureResponse[dict](
        successful=[
            OperationResult[dict](success=True, data={"id": 1}, operation_id="op_1"),
        ],
        failed=[
            OperationResult[dict](success=False, error="Not found", operation_id="op_2"),
        ],
        total_count=2,
        success_count=1,
        failure_count=1,
    )

    assert response.has_successes is True
    assert response.has_failures is True
    assert response.partial_success is True
    assert response.success_count == 1
    assert response.failure_count == 1
    assert len(response.successful) == 1
    assert len(response.failed) == 1


def test_operation_result_validation_success():
    """Test OperationResult model validation for successful operation."""
    success_result = OperationResult[str](success=True, data="test data", operation_id="test_1")

    assert success_result.success is True
    assert success_result.data == "test data"
    assert success_result.error is None
    assert success_result.operation_id == "test_1"


def test_operation_result_validation_failure():
    """Test OperationResult model validation for failed operation."""
    failure_result = OperationResult[str](success=False, error="Test error", operation_id="test_2")

    assert failure_result.success is False
    assert failure_result.error == "Test error"
    assert failure_result.data is None
    assert failure_result.operation_id == "test_2"


def test_operation_result_generic_type_int():
    """Test OperationResult works with int generic type."""
    int_result = OperationResult[int](success=True, data=42, operation_id="int_test")

    assert int_result.data == 42
    assert isinstance(int_result.data, int)


def test_operation_result_generic_type_dict():
    """Test OperationResult works with dict generic type."""
    dict_result = OperationResult[dict](
        success=True, data={"key": "value", "count": 10}, operation_id="dict_test"
    )

    assert dict_result.data == {"key": "value", "count": 10}
    assert dict_result.data["key"] == "value"  # type: ignore[index]
    assert dict_result.data["count"] == 10  # type: ignore[index]


def test_partial_failure_response_empty():
    """Test response with no operations."""
    response = PartialFailureResponse[dict](
        successful=[],
        failed=[],
        total_count=0,
        success_count=0,
        failure_count=0,
    )

    assert response.has_successes is False
    assert response.has_failures is False
    assert response.partial_success is False
    assert len(response.successful) == 0
    assert len(response.failed) == 0


def test_partial_failure_response_default_factory():
    """Test that default_factory creates empty lists."""
    # Should be able to create response without specifying lists
    response = PartialFailureResponse[dict](total_count=0, success_count=0, failure_count=0)

    assert response.successful == []
    assert response.failed == []


def test_operation_result_without_operation_id():
    """Test OperationResult works without operation_id."""
    result = OperationResult[str](success=True, data="test")

    assert result.success is True
    assert result.data == "test"
    assert result.operation_id is None


def test_partial_failure_response_properties_consistency():
    """Test that count properties match list lengths."""
    successful_ops = [
        OperationResult[int](success=True, data=i, operation_id=f"op_{i}") for i in range(3)
    ]
    failed_ops = [
        OperationResult[int](success=False, error=f"Error {i}", operation_id=f"op_{i}")
        for i in range(2)
    ]

    response = PartialFailureResponse[int](
        successful=successful_ops,
        failed=failed_ops,
        total_count=5,
        success_count=3,
        failure_count=2,
    )

    assert len(response.successful) == response.success_count
    assert len(response.failed) == response.failure_count
    assert response.total_count == response.success_count + response.failure_count
