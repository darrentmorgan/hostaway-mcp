"""Unit tests for error models.

Tests OperationResult and PartialFailureResponse models for batch operations.
"""

import pytest

from src.models.errors import OperationResult, PartialFailureResponse


class TestOperationResult:
    """Test suite for OperationResult model."""

    def test_create_successful_operation(self):
        """Test creating successful operation result."""
        result = OperationResult[dict](
            success=True, data={"id": "123", "name": "Test"}, operation_id="op-1"
        )

        assert result.success is True
        assert result.data == {"id": "123", "name": "Test"}
        assert result.error is None
        assert result.operation_id == "op-1"

    def test_create_failed_operation(self):
        """Test creating failed operation result."""
        result = OperationResult[dict](
            success=False, error="Resource not found", operation_id="op-2"
        )

        assert result.success is False
        assert result.data is None
        assert result.error == "Resource not found"
        assert result.operation_id == "op-2"

    def test_operation_result_without_id(self):
        """Test operation result without operation_id."""
        result = OperationResult[dict](success=True, data={"value": 42})

        assert result.success is True
        assert result.operation_id is None

    def test_operation_result_typed(self):
        """Test operation result with specific type."""
        from pydantic import BaseModel

        class Item(BaseModel):
            id: str
            value: int

        item = Item(id="item-1", value=100)
        result = OperationResult[Item](success=True, data=item)

        assert result.success is True
        assert isinstance(result.data, Item)
        assert result.data.value == 100


class TestPartialFailureResponse:
    """Test suite for PartialFailureResponse model."""

    def test_create_all_successful(self):
        """Test partial failure response with all successes."""
        response = PartialFailureResponse[dict](
            successful=[
                OperationResult(success=True, data={"id": 1}),
                OperationResult(success=True, data={"id": 2}),
            ],
            failed=[],
            total_count=2,
            success_count=2,
            failure_count=0,
        )

        assert response.total_count == 2
        assert response.success_count == 2
        assert response.failure_count == 0
        assert response.has_successes is True
        assert response.has_failures is False
        assert response.partial_success is False

    def test_create_all_failed(self):
        """Test partial failure response with all failures."""
        response = PartialFailureResponse[dict](
            successful=[],
            failed=[
                OperationResult(success=False, error="Error 1"),
                OperationResult(success=False, error="Error 2"),
            ],
            total_count=2,
            success_count=0,
            failure_count=2,
        )

        assert response.total_count == 2
        assert response.success_count == 0
        assert response.failure_count == 2
        assert response.has_successes is False
        assert response.has_failures is True
        assert response.partial_success is False

    def test_create_mixed_results(self):
        """Test partial failure response with mixed results."""
        response = PartialFailureResponse[dict](
            successful=[
                OperationResult(success=True, data={"id": 1}),
                OperationResult(success=True, data={"id": 2}),
            ],
            failed=[
                OperationResult(success=False, error="Not found"),
            ],
            total_count=3,
            success_count=2,
            failure_count=1,
        )

        assert response.total_count == 3
        assert response.success_count == 2
        assert response.failure_count == 1
        assert response.has_successes is True
        assert response.has_failures is True
        assert response.partial_success is True

    def test_empty_response(self):
        """Test partial failure response with no operations."""
        response = PartialFailureResponse[dict](
            successful=[], failed=[], total_count=0, success_count=0, failure_count=0
        )

        assert response.total_count == 0
        assert response.has_successes is False
        assert response.has_failures is False
        assert response.partial_success is False

    def test_has_failures_property(self):
        """Test has_failures property."""
        response = PartialFailureResponse[dict](
            successful=[],
            failed=[OperationResult(success=False, error="Error")],
            total_count=1,
            success_count=0,
            failure_count=1,
        )

        assert response.has_failures is True

    def test_has_successes_property(self):
        """Test has_successes property."""
        response = PartialFailureResponse[dict](
            successful=[OperationResult(success=True, data={"id": 1})],
            failed=[],
            total_count=1,
            success_count=1,
            failure_count=0,
        )

        assert response.has_successes is True

    def test_partial_success_property(self):
        """Test partial_success property."""
        # All successful - not partial
        response1 = PartialFailureResponse[dict](
            successful=[OperationResult(success=True, data={"id": 1})],
            failed=[],
            total_count=1,
            success_count=1,
            failure_count=0,
        )
        assert response1.partial_success is False

        # All failed - not partial
        response2 = PartialFailureResponse[dict](
            successful=[],
            failed=[OperationResult(success=False, error="Error")],
            total_count=1,
            success_count=0,
            failure_count=1,
        )
        assert response2.partial_success is False

        # Mixed - is partial
        response3 = PartialFailureResponse[dict](
            successful=[OperationResult(success=True, data={"id": 1})],
            failed=[OperationResult(success=False, error="Error")],
            total_count=2,
            success_count=1,
            failure_count=1,
        )
        assert response3.partial_success is True

    def test_operation_ids_preserved(self):
        """Test that operation IDs are preserved in results."""
        response = PartialFailureResponse[dict](
            successful=[
                OperationResult(success=True, data={"value": 1}, operation_id="op-1"),
                OperationResult(success=True, data={"value": 2}, operation_id="op-2"),
            ],
            failed=[
                OperationResult(success=False, error="Error", operation_id="op-3"),
            ],
            total_count=3,
            success_count=2,
            failure_count=1,
        )

        assert response.successful[0].operation_id == "op-1"
        assert response.successful[1].operation_id == "op-2"
        assert response.failed[0].operation_id == "op-3"
