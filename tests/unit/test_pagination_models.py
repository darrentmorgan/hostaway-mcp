"""Unit tests for pagination models.

Tests PaginatedResponse, PageMetadata, and pagination validation.
"""

import pytest
from pydantic import ValidationError

from src.models.pagination import (
    CursorMetadata,
    PageMetadata,
    PaginatedResponse,
    PaginationParams,
)


class TestPageMetadata:
    """Test suite for PageMetadata model."""

    def test_create_page_metadata(self):
        """Test creating page metadata."""
        metadata = PageMetadata(totalCount=100, pageSize=50, hasMore=True)

        assert metadata.totalCount == 100
        assert metadata.pageSize == 50
        assert metadata.hasMore is True

    def test_page_metadata_last_page(self):
        """Test page metadata for last page."""
        metadata = PageMetadata(totalCount=100, pageSize=50, hasMore=False)

        assert metadata.hasMore is False

    def test_page_metadata_negative_total(self):
        """Test validation error for negative totalCount."""
        with pytest.raises(ValidationError):
            PageMetadata(totalCount=-10, pageSize=50, hasMore=False)


class TestPaginatedResponse:
    """Test suite for PaginatedResponse model."""

    def test_create_paginated_response(self):
        """Test creating paginated response."""
        response = PaginatedResponse[dict](
            items=[{"id": 1}, {"id": 2}, {"id": 3}],
            nextCursor="cursor-123",
            meta=PageMetadata(totalCount=100, pageSize=3, hasMore=True),
        )

        assert len(response.items) == 3
        assert response.nextCursor == "cursor-123"
        assert response.meta.hasMore is True

    def test_paginated_response_last_page(self):
        """Test paginated response for last page."""
        response = PaginatedResponse[dict](
            items=[{"id": 1}, {"id": 2}],
            nextCursor=None,
            meta=PageMetadata(totalCount=2, pageSize=2, hasMore=False),
        )

        assert response.nextCursor is None
        assert response.meta.hasMore is False

    def test_paginated_response_empty(self):
        """Test paginated response with no items."""
        response = PaginatedResponse[dict](
            items=[], nextCursor=None, meta=PageMetadata(totalCount=0, pageSize=0, hasMore=False)
        )

        assert len(response.items) == 0
        assert response.nextCursor is None

    def test_cursor_consistency_valid(self):
        """Test that valid cursor/hasMore combinations work."""
        # hasMore=True with cursor
        response1 = PaginatedResponse[dict](
            items=[{"id": 1}],
            nextCursor="cursor-123",
            meta=PageMetadata(totalCount=100, pageSize=1, hasMore=True),
        )
        assert response1.nextCursor == "cursor-123"

        # hasMore=False without cursor
        response2 = PaginatedResponse[dict](
            items=[{"id": 1}],
            nextCursor=None,
            meta=PageMetadata(totalCount=1, pageSize=1, hasMore=False),
        )
        assert response2.nextCursor is None

    def test_typed_paginated_response(self):
        """Test PaginatedResponse with specific type."""
        from pydantic import BaseModel

        class Item(BaseModel):
            id: str
            name: str

        items = [Item(id="1", name="Item 1"), Item(id="2", name="Item 2")]

        response = PaginatedResponse[Item](
            items=items,
            nextCursor="cursor-abc",
            meta=PageMetadata(totalCount=10, pageSize=2, hasMore=True),
        )

        assert all(isinstance(item, Item) for item in response.items)
        assert response.items[0].name == "Item 1"


class TestPaginationParams:
    """Test suite for PaginationParams model."""

    def test_create_pagination_params_defaults(self):
        """Test creating pagination params with defaults."""
        params = PaginationParams()

        assert params.cursor is None
        assert params.limit == 50

    def test_pagination_params_with_cursor(self):
        """Test pagination params with cursor."""
        params = PaginationParams(cursor="cursor-123", limit=100)

        assert params.cursor == "cursor-123"
        assert params.limit == 100

    def test_pagination_params_limit_bounds(self):
        """Test limit validation."""
        # Minimum limit
        params = PaginationParams(limit=1)
        assert params.limit == 1

        # Maximum limit
        params = PaginationParams(limit=200)
        assert params.limit == 200

        # Below minimum
        with pytest.raises(ValidationError):
            PaginationParams(limit=0)

        # Above maximum
        with pytest.raises(ValidationError):
            PaginationParams(limit=201)


class TestCursorMetadata:
    """Test suite for CursorMetadata model."""

    def test_create_cursor_metadata(self):
        """Test creating cursor metadata."""
        metadata = CursorMetadata(
            cursor_id="cursor-123",
            offset=50,
            timestamp=1234567890.0,
            order_by="created_desc",
            filters={"status": "confirmed"},
            ttl_seconds=600,
        )

        assert metadata.cursor_id == "cursor-123"
        assert metadata.offset == 50
        assert metadata.timestamp == 1234567890.0
        assert metadata.order_by == "created_desc"
        assert metadata.filters == {"status": "confirmed"}
        assert metadata.ttl_seconds == 600

    def test_cursor_metadata_defaults(self):
        """Test cursor metadata with default values."""
        metadata = CursorMetadata(cursor_id="cursor-456", offset=0, timestamp=1234567890.0)

        assert metadata.order_by is None
        assert metadata.filters is None
        assert metadata.ttl_seconds == 600

    def test_cursor_metadata_negative_offset(self):
        """Test validation error for negative offset."""
        with pytest.raises(ValidationError):
            CursorMetadata(cursor_id="cursor-789", offset=-10, timestamp=1234567890.0)
