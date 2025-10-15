"""Pagination models for MCP server context window protection.

Defines Pydantic models for paginated responses with cursor-based navigation.
Based on data-model.md entity definitions.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field, field_validator

# Generic type for paginated items
T = TypeVar("T")


class PageMetadata(BaseModel):
    """Pagination metadata for a response page.

    Attributes:
        totalCount: Total number of items available across all pages
        pageSize: Number of items in current page
        hasMore: Whether more pages are available
    """

    totalCount: int = Field(ge=0, description="Total items available")
    pageSize: int = Field(ge=0, description="Items in current page")
    hasMore: bool = Field(description="More pages available")

    @field_validator("pageSize")
    @classmethod
    def validate_page_size(cls, v: int, info) -> int:
        """Validate that pageSize <= totalCount."""
        # Note: info.data is available in Pydantic v2
        # We'll validate this in the PaginatedResponse model instead
        return v


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper.

    Wraps a list of items with pagination metadata and optional cursor
    for fetching the next page.

    Type Parameters:
        T: Type of items in the response

    Attributes:
        items: Current page of items
        nextCursor: Opaque cursor for next page (null on final page)
        meta: Pagination metadata

    Example:
        >>> from pydantic import BaseModel
        >>> class Listing(BaseModel):
        ...     id: str
        ...     name: str
        >>> response = PaginatedResponse[Listing](
        ...     items=[Listing(id="1", name="Beach House")],
        ...     nextCursor="eyJvZmZzZXQiOjUwfQ==",
        ...     meta=PageMetadata(totalCount=100, pageSize=1, hasMore=True)
        ... )
    """

    items: list[T] = Field(description="Current page items")
    nextCursor: str | None = Field(
        default=None,
        description="Cursor for next page (null on final page)",
    )
    meta: PageMetadata = Field(description="Pagination metadata")

    @field_validator("nextCursor")
    @classmethod
    def validate_cursor_consistency(cls, v: str | None, info) -> str | None:
        """Validate cursor presence matches hasMore flag.

        Rules:
        - If hasMore is True, nextCursor must be present
        - If hasMore is False, nextCursor must be null
        """
        if not info.data:
            return v

        meta = info.data.get("meta")
        if meta is None:
            return v

        has_more = meta.hasMore if isinstance(meta, PageMetadata) else meta.get("hasMore")

        if has_more and v is None:
            raise ValueError("nextCursor required when meta.hasMore is True")

        if not has_more and v is not None:
            raise ValueError("nextCursor must be null when meta.hasMore is False")

        return v

    @field_validator("items")
    @classmethod
    def validate_items_count(cls, v: list, info) -> list:
        """Validate items count matches pageSize."""
        if not info.data:
            return v

        meta = info.data.get("meta")
        if meta is None:
            return v

        page_size = meta.pageSize if isinstance(meta, PageMetadata) else meta.get("pageSize")

        if page_size is not None and len(v) != page_size:
            raise ValueError(
                f"items length ({len(v)}) must match meta.pageSize ({page_size})"
            )

        return v


class PaginationParams(BaseModel):
    """Query parameters for pagination requests.

    Attributes:
        cursor: Optional cursor from previous response
        limit: Maximum items per page (default: 50, max: 200)
    """

    cursor: str | None = Field(
        default=None,
        description="Cursor from previous response",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum items per page",
    )


class CursorMetadata(BaseModel):
    """Metadata about a pagination cursor.

    Attributes:
        cursor_id: Unique identifier for the cursor
        offset: Position in result set
        timestamp: Cursor creation time (Unix timestamp)
        order_by: Sort column and direction
        filters: Query filters at cursor creation
        ttl_seconds: Cursor TTL in seconds (default: 600)
    """

    cursor_id: str = Field(description="Unique cursor identifier")
    offset: int = Field(ge=0, description="Position in result set")
    timestamp: float = Field(description="Cursor creation time")
    order_by: str | None = Field(default=None, description="Sort order")
    filters: dict | None = Field(default=None, description="Query filters")
    ttl_seconds: int = Field(default=600, ge=1, description="Cursor TTL")
