"""Error and partial failure response models.

Provides models for handling partial success scenarios where some operations
succeed while others fail in batch requests.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class OperationResult(BaseModel, Generic[T]):
    """Result of a single operation in a batch.

    Tracks whether an operation succeeded or failed, along with either
    the result data or error message.
    """

    success: bool = Field(..., description="Whether operation succeeded")
    data: T | None = Field(None, description="Operation result data if successful")
    error: str | None = Field(None, description="Error message if failed")
    operation_id: str | None = Field(None, description="Identifier for this operation")


class PartialFailureResponse(BaseModel, Generic[T]):
    """Response containing both successful and failed operations.

    Used for batch operations where some items may succeed while others fail.
    Allows clients to process successful results while being aware of failures.

    Example:
        >>> response = PartialFailureResponse[dict](
        ...     successful=[OperationResult(success=True, data={"id": 1})],
        ...     failed=[OperationResult(success=False, error="Not found")],
        ...     total_count=2,
        ...     success_count=1,
        ...     failure_count=1,
        ... )
        >>> response.partial_success
        True
    """

    successful: list[OperationResult[T]] = Field(
        default_factory=list, description="Operations that completed successfully"
    )
    failed: list[OperationResult[T]] = Field(
        default_factory=list, description="Operations that failed"
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
