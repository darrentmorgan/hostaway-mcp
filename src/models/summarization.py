"""Summarization models for response compression.

Defines Pydantic models for condensed responses with drill-down instructions.
Based on data-model.md entity definitions.
"""

from typing import Any, Literal, TypeVar

from pydantic import BaseModel, Field

# Generic type for summarized objects
T = TypeVar("T")


class DetailsFetchInfo(BaseModel):
    """Instructions for fetching full object details.

    Attributes:
        endpoint: API endpoint for full details
        parameters: Query/path parameters to include
    """

    endpoint: str = Field(description="API endpoint for full details")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for request",
    )


class SummaryMetadata(BaseModel):
    """Metadata about a summarized response.

    Attributes:
        kind: Response type ("preview" for summary, "full" for complete)
        totalFields: Total fields in full object
        projectedFields: Fields included in summary
        detailsAvailable: How to fetch full details
    """

    kind: Literal["preview", "full"] = Field(description="Response type")
    totalFields: int = Field(ge=0, description="Total fields in full object")  # noqa: N815
    projectedFields: list[str] = Field(description="Fields in summary")  # noqa: N815
    detailsAvailable: DetailsFetchInfo = Field(description="Full details fetch info")  # noqa: N815


class SummaryResponse[T](BaseModel):
    """Condensed response with essential fields.

    Generic wrapper for summarized objects with metadata explaining
    how to retrieve full details.

    Type Parameters:
        T: Original object type being summarized

    Attributes:
        summary: Projected essential fields from original object
        meta: Summary metadata and drill-down instructions

    Example:
        >>> summary_response = SummaryResponse[dict](
        ...     summary={
        ...         "id": "BK12345",
        ...         "status": "confirmed",
        ...         "guestName": "John Doe",
        ...     },
        ...     meta=SummaryMetadata(
        ...         kind="preview",
        ...         totalFields=20,
        ...         projectedFields=["id", "status", "guestName"],
        ...         detailsAvailable=DetailsFetchInfo(
        ...             endpoint="/api/v1/bookings/BK12345",
        ...             parameters={"fields": "all"}
        ...         )
        ...     )
        ... )
    """

    summary: dict[str, Any] = Field(description="Essential fields")
    meta: SummaryMetadata = Field(description="Summary metadata")


class SummarizationStrategy(BaseModel):
    """Configuration for summarization behavior.

    Attributes:
        strategy_type: Type of summarization (field_projection, extractive, etc.)
        essential_fields: Fields to always include
        max_nested_depth: Maximum depth for nested objects
        preserve_structure: Whether to preserve object structure
    """

    strategy_type: Literal["field_projection", "extractive", "abstractive"] = Field(
        default="field_projection",
        description="Summarization strategy",
    )
    essential_fields: list[str] = Field(
        default_factory=list,
        description="Fields to always include",
    )
    max_nested_depth: int = Field(
        default=2,
        ge=1,
        description="Max nested depth",
    )
    preserve_structure: bool = Field(
        default=True,
        description="Preserve object structure",
    )


class SummarizationResult(BaseModel):
    """Result of summarizing an object.

    Captures metrics about the summarization for observability.

    Attributes:
        original_field_count: Fields in original object
        summarized_field_count: Fields in summary
        reduction_ratio: Percentage of fields removed (0.0-1.0)
        original_tokens: Estimated tokens in original
        summarized_tokens: Estimated tokens in summary
        token_reduction: Percentage of tokens saved
    """

    original_field_count: int = Field(ge=0)
    summarized_field_count: int = Field(ge=0)
    reduction_ratio: float = Field(ge=0.0, le=1.0)
    original_tokens: int = Field(ge=0)
    summarized_tokens: int = Field(ge=0)
    token_reduction: float = Field(ge=0.0, le=1.0)


class ContentChunk(BaseModel):
    """Semantic segment of large content.

    Used for progressive loading of large text content (e.g., logs, messages).

    Attributes:
        content: Chunk content (respects semantic boundaries)
        chunkIndex: Current chunk number (0-indexed)
        totalChunks: Total chunks in full content
        nextCursor: Cursor for next chunk (null on final chunk)
        metadata: Additional chunk information
    """

    content: str = Field(description="Chunk content")
    chunkIndex: int = Field(ge=0, description="Current chunk (0-indexed)")  # noqa: N815
    totalChunks: int = Field(ge=1, description="Total chunks")  # noqa: N815
    nextCursor: str | None = Field(  # noqa: N815
        default=None,
        description="Cursor for next chunk",
    )
    metadata: "ChunkMetadata" = Field(description="Chunk metadata")


class ChunkMetadata(BaseModel):
    """Metadata about a content chunk.

    Attributes:
        startLine: Starting line number in full content
        endLine: Ending line number (inclusive)
        totalLines: Total lines in full content
        bytesInChunk: Size of this chunk in bytes
    """

    startLine: int = Field(ge=0, description="Start line")  # noqa: N815
    endLine: int = Field(ge=0, description="End line (inclusive)")  # noqa: N815
    totalLines: int = Field(ge=0, description="Total lines")  # noqa: N815
    bytesInChunk: int = Field(ge=0, description="Chunk size in bytes")  # noqa: N815

    def model_post_init(self, __context) -> None:
        """Validate line number constraints."""
        if self.endLine < self.startLine:
            raise ValueError("endLine must be >= startLine")

        if self.totalLines < self.endLine + 1:
            raise ValueError("totalLines must be > endLine")
