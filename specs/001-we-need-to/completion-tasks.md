# Completion Tasks: Partial Failure Handling (FR-013)

**Feature**: Hostaway MCP Server - Phase 2.5 Completion
**Created**: 2025-10-17
**Status**: Ready for Implementation
**Priority**: Optional (Post-MVP Enhancement)

## Overview

These tasks complete the Partial Failure Handling requirement (FR-013) that allows the system to gracefully handle scenarios where some operations succeed while others fail in batch requests.

**Value**: Improves resilience when processing multiple properties/bookings - system returns successful data while reporting failures rather than failing completely.

---

## Tasks (5 Total)

### T029a [P] [FOUND] Create PartialFailureResponse Model

**File**: `/Users/darrenmorgan/AI_Projects/hostaway-mcp/src/models/errors.py`

**Objective**: Define Pydantic model for tracking successful and failed operations in batch responses

**Implementation**:
```python
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Any

T = TypeVar('T')

class OperationResult(BaseModel, Generic[T]):
    """Result of a single operation in a batch."""
    success: bool = Field(..., description="Whether operation succeeded")
    data: T | None = Field(None, description="Operation result data if successful")
    error: str | None = Field(None, description="Error message if failed")
    operation_id: str | None = Field(None, description="Identifier for this operation")

class PartialFailureResponse(BaseModel, Generic[T]):
    """Response containing both successful and failed operations."""
    successful: list[OperationResult[T]] = Field(
        default_factory=list,
        description="Operations that completed successfully"
    )
    failed: list[OperationResult[T]] = Field(
        default_factory=list,
        description="Operations that failed"
    )
    total_count: int = Field(..., description="Total operations attempted")
    success_count: int = Field(..., description="Number of successful operations")
    failure_count: int = Field(..., description="Number of failed operations")

    @property
    def has_failures(self) -> bool:
        """Check if any operations failed."""
        return self.failure_count > 0

    @property
    def has_successes(self) -> bool:
        """Check if any operations succeeded."""
        return self.success_count > 0

    @property
    def partial_success(self) -> bool:
        """Check if response has both successes and failures."""
        return self.has_successes and self.has_failures
```

**Acceptance Criteria**:
- Model validates successful and failed operation lists
- Properties correctly compute counts and states
- Generic type parameter works with different data types

**Estimated Time**: 30 minutes

---

### T029b [P] [FOUND] Add Error Recovery Middleware

**File**: `/Users/darrenmorgan/AI_Projects/hostaway-mcp/src/api/main.py`

**Objective**: Create FastAPI middleware that catches exceptions and enables graceful degradation

**Implementation**:
```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.mcp.logging import get_logger

logger = get_logger(__name__)

class ErrorRecoveryMiddleware(BaseHTTPMiddleware):
    """Middleware for graceful error recovery and partial success handling."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the error with context
            logger.error(
                "Unhandled error in request",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )

            # Return 500 with error details (sanitized)
            return Response(
                content=json.dumps({
                    "detail": "Internal server error - operation may have partially completed",
                    "error_type": type(e).__name__,
                }),
                status_code=500,
                media_type="application/json"
            )

# Add to FastAPI app in main.py
app.add_middleware(ErrorRecoveryMiddleware)
```

**Acceptance Criteria**:
- Middleware catches unhandled exceptions
- Errors logged with full context
- Response indicates partial completion possibility
- No sensitive data leaked in error messages

**Estimated Time**: 45 minutes

---

### T029c [FOUND] Implement Batch Operation Handler

**File**: `/Users/darrenmorgan/AI_Projects/hostaway-mcp/src/services/hostaway_client.py`

**Objective**: Add method to HostawayClient for executing batch operations with individual error handling

**Dependencies**: T029a (requires PartialFailureResponse model)

**Implementation**:
```python
async def execute_batch(
    self,
    operations: list[Callable[[], Awaitable[T]]],
    operation_ids: list[str] | None = None,
) -> PartialFailureResponse[T]:
    """Execute multiple operations and return partial success results.

    Args:
        operations: List of async callables to execute
        operation_ids: Optional IDs for tracking each operation

    Returns:
        PartialFailureResponse with successful and failed operations
    """
    from src.models.errors import OperationResult, PartialFailureResponse

    if operation_ids is None:
        operation_ids = [f"op_{i}" for i in range(len(operations))]

    successful: list[OperationResult[T]] = []
    failed: list[OperationResult[T]] = []

    # Execute all operations, capturing individual results
    for op_id, operation in zip(operation_ids, operations):
        try:
            result = await operation()
            successful.append(
                OperationResult[T](
                    success=True,
                    data=result,
                    operation_id=op_id,
                )
            )
        except Exception as e:
            logger.warning(
                f"Batch operation {op_id} failed",
                extra={"operation_id": op_id, "error": str(e)}
            )
            failed.append(
                OperationResult[T](
                    success=False,
                    error=str(e),
                    operation_id=op_id,
                )
            )

    return PartialFailureResponse[T](
        successful=successful,
        failed=failed,
        total_count=len(operations),
        success_count=len(successful),
        failure_count=len(failed),
    )
```

**Acceptance Criteria**:
- Executes all operations even if some fail
- Returns both successful and failed results
- Logs individual operation failures
- Generic type parameter preserves type safety

**Estimated Time**: 1 hour

---

### T029d [P] [FOUND] Unit Test for Partial Failure Response Model

**File**: `/Users/darrenmorgan/AI_Projects/hostaway-mcp/tests/unit/test_errors.py`

**Objective**: Test PartialFailureResponse model validation and properties

**Implementation**:
```python
import pytest
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
    assert len(response.failed) == 2

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

def test_operation_result_validation():
    """Test OperationResult model validation."""
    # Valid success case
    success_result = OperationResult[str](
        success=True,
        data="test data",
        operation_id="test_1"
    )
    assert success_result.success is True
    assert success_result.data == "test data"

    # Valid failure case
    failure_result = OperationResult[str](
        success=False,
        error="Test error",
        operation_id="test_2"
    )
    assert failure_result.success is False
    assert failure_result.error == "Test error"
```

**Acceptance Criteria**:
- Tests all success, all failure, and mixed scenarios
- Validates properties (has_successes, has_failures, partial_success)
- Confirms generic type parameter works
- All tests pass

**Estimated Time**: 45 minutes

---

### T029e [P] [FOUND] Integration Test for Batch Operations

**File**: `/Users/darrenmorgan/AI_Projects/hostaway-mcp/tests/integration/test_error_handling.py`

**Objective**: Test batch operation handler with mixed success/failure scenarios

**Dependencies**: T029c (requires batch operation handler)

**Implementation**:
```python
import pytest
from src.services.hostaway_client import HostawayClient
from src.mcp.config import HostawayConfig
from src.mcp.auth import TokenManager
from src.services.rate_limiter import RateLimiter

@pytest.fixture
async def hostaway_client():
    """Create HostawayClient for testing."""
    config = HostawayConfig()
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

    async def mock_success_op():
        return {"status": "success", "id": 123}

    operations = [mock_success_op for _ in range(3)]
    result = await hostaway_client.execute_batch(operations)

    assert result.total_count == 3
    assert result.success_count == 3
    assert result.failure_count == 0
    assert result.has_successes is True
    assert result.has_failures is False
    assert len(result.successful) == 3

@pytest.mark.asyncio
async def test_batch_operations_mixed_results(hostaway_client):
    """Test batch operations with mixed success/failure."""

    async def success_op():
        return {"status": "success"}

    async def failure_op():
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
    assert "Test failure" in result.failed[0].error

@pytest.mark.asyncio
async def test_batch_operations_all_failed(hostaway_client):
    """Test batch operations where all fail."""

    async def failure_op():
        raise RuntimeError("Operation failed")

    operations = [failure_op for _ in range(2)]
    result = await hostaway_client.execute_batch(operations)

    assert result.total_count == 2
    assert result.success_count == 0
    assert result.failure_count == 2
    assert result.has_failures is True
    assert result.has_successes is False
    assert len(result.failed) == 2

@pytest.mark.asyncio
async def test_batch_operations_preserves_order(hostaway_client):
    """Test that batch operations preserve execution order."""

    results_order = []

    async def tracked_op(value: int):
        results_order.append(value)
        return {"value": value}

    operations = [
        lambda: tracked_op(1),
        lambda: tracked_op(2),
        lambda: tracked_op(3),
    ]

    result = await hostaway_client.execute_batch(operations)

    assert results_order == [1, 2, 3]
    assert result.success_count == 3
```

**Acceptance Criteria**:
- Tests all success scenario
- Tests mixed success/failure scenario
- Tests all failure scenario
- Verifies operation order preserved
- All tests pass with proper assertions

**Estimated Time**: 1 hour

---

## Execution Plan

### Sequential Approach (Recommended)

```bash
# Day 1: Models and Infrastructure (1.5 hours)
1. T029a - Create PartialFailureResponse model (30 min)
2. T029b - Add error recovery middleware (45 min)

# Day 2: Implementation and Testing (2.5 hours)
3. T029d - Unit test for model (45 min) - Run first to verify T029a
4. T029c - Implement batch operation handler (1 hour)
5. T029e - Integration test for batch ops (1 hour)

# Validation
6. Run full test suite to ensure no regressions
7. Test with real batch scenarios (multiple property lookups)
```

### Parallel Approach (With 2 Developers)

```bash
# Developer A: Models and Tests
- T029a - Create PartialFailureResponse model
- T029d - Unit test for partial failure response

# Developer B: Infrastructure and Integration
- T029b - Add error recovery middleware
- T029e - Integration test for batch operations (wait for T029c)

# Sequential (After models complete)
- T029c - Implement batch handler (requires T029a)
```

---

## Validation Criteria

After completing all tasks:

1. **Unit Tests Pass**: All tests in `test_errors.py` pass
2. **Integration Tests Pass**: All tests in `test_error_handling.py` pass
3. **No Regressions**: Full test suite still passes (72.8%+ coverage maintained)
4. **Real-World Test**:
   ```python
   # Test batch listing lookup
   listing_ids = [1, 2, 999999, 4]  # 999999 should fail
   operations = [
       lambda: client.get_listing_by_id(lid)
       for lid in listing_ids
   ]
   result = await client.execute_batch(operations, operation_ids=listing_ids)

   # Should have 3 successes, 1 failure
   assert result.success_count == 3
   assert result.failure_count == 1
   assert result.partial_success is True
   ```

---

## Integration Points

After these tasks complete:

1. **Update listings endpoint** (`src/api/routes/listings.py`):
   - Add batch listing lookup endpoint using `execute_batch()`

2. **Update bookings endpoint** (`src/api/routes/bookings.py`):
   - Add batch booking lookup endpoint using `execute_batch()`

3. **Update documentation** (`README.md`):
   - Document partial failure handling capability
   - Add examples of batch operations

---

## Estimated Total Time

- **Sequential**: 4 hours
- **Parallel (2 devs)**: 2.5 hours
- **Testing & Validation**: 1 hour
- **Total**: 5 hours (end-to-end)

---

**Status**: ✅ Ready for implementation
**Priority**: Optional post-MVP enhancement
**Value**: Improved resilience for batch operations
