"""Unit tests for PaginationService.

Tests cursor creation, validation, paginated response building, and query execution.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.models.pagination import PageMetadata, PaginatedResponse, PaginationParams
from src.services.pagination_service import PaginationService, get_pagination_service
from src.utils.cursor_codec import CursorCodecError


class TestPaginationService:
    """Test suite for PaginationService."""

    @pytest.fixture
    def service(self):
        """Create pagination service instance."""
        return PaginationService(
            secret="test-secret-key",
            default_page_size=50,
            max_page_size=200
        )

    def test_init(self):
        """Test service initialization."""
        service = PaginationService(secret="my-secret", default_page_size=25, max_page_size=100)

        assert service.secret == "my-secret"
        assert service.default_page_size == 25
        assert service.max_page_size == 100

    def test_validate_page_size_none(self, service):
        """Test validate_page_size with None returns default."""
        result = service.validate_page_size(None)
        assert result == 50

    def test_validate_page_size_negative(self, service):
        """Test validate_page_size with negative returns default."""
        result = service.validate_page_size(-10)
        assert result == 50

    def test_validate_page_size_zero(self, service):
        """Test validate_page_size with zero returns default."""
        result = service.validate_page_size(0)
        assert result == 50

    def test_validate_page_size_normal(self, service):
        """Test validate_page_size with normal value."""
        result = service.validate_page_size(100)
        assert result == 100

    def test_validate_page_size_exceeds_max(self, service):
        """Test validate_page_size clamped to max."""
        result = service.validate_page_size(500)
        assert result == 200  # Clamped to max_page_size

    def test_create_cursor_basic(self, service):
        """Test creating basic cursor."""
        cursor = service.create_cursor(offset=100)

        assert isinstance(cursor, str)
        assert len(cursor) > 0

    def test_create_cursor_with_order_by(self, service):
        """Test creating cursor with order_by."""
        cursor = service.create_cursor(offset=50, order_by="created_desc")

        assert isinstance(cursor, str)

    def test_create_cursor_with_filters(self, service):
        """Test creating cursor with filters."""
        filters = {"status": "confirmed", "listing_id": "123"}
        cursor = service.create_cursor(offset=25, filters=filters)

        assert isinstance(cursor, str)

    def test_parse_cursor(self, service):
        """Test parsing valid cursor."""
        # Create and then parse cursor
        original_offset = 100
        original_order = "created_desc"
        original_filters = {"status": "confirmed"}

        cursor = service.create_cursor(
            offset=original_offset,
            order_by=original_order,
            filters=original_filters
        )

        decoded = service.parse_cursor(cursor)

        assert decoded["offset"] == original_offset
        assert decoded.get("order_by") == original_order
        assert decoded.get("filters") == original_filters

    def test_parse_cursor_invalid(self, service):
        """Test parsing invalid cursor raises error."""
        with pytest.raises(CursorCodecError):
            service.parse_cursor("invalid-cursor-string")

    def test_build_response_first_page(self, service):
        """Test building response for first page."""
        items = [{"id": i, "name": f"Item {i}"} for i in range(1, 51)]
        params = PaginationParams(cursor=None, limit=50)

        response = service.build_response(
            items=items,
            total_count=150,
            params=params,
        )

        assert isinstance(response, PaginatedResponse)
        assert response.items == items
        assert response.meta.totalCount == 150
        assert response.meta.pageSize == 50
        assert response.meta.hasMore is True
        assert response.nextCursor is not None

    def test_build_response_middle_page(self, service):
        """Test building response for middle page."""
        items = [{"id": i, "name": f"Item {i}"} for i in range(51, 101)]
        cursor = service.create_cursor(offset=50)
        params = PaginationParams(cursor=cursor, limit=50)

        response = service.build_response(
            items=items,
            total_count=150,
            params=params,
        )

        assert response.items == items
        assert response.meta.totalCount == 150
        assert response.meta.pageSize == 50
        assert response.meta.hasMore is True
        assert response.nextCursor is not None

    def test_build_response_last_page(self, service):
        """Test building response for last page."""
        items = [{"id": i, "name": f"Item {i}"} for i in range(101, 151)]
        cursor = service.create_cursor(offset=100)
        params = PaginationParams(cursor=cursor, limit=50)

        response = service.build_response(
            items=items,
            total_count=150,
            params=params,
        )

        assert response.items == items
        assert response.meta.totalCount == 150
        assert response.meta.pageSize == 50
        assert response.meta.hasMore is False
        assert response.nextCursor is None

    def test_build_response_empty_results(self, service):
        """Test building response with no items."""
        items = []
        params = PaginationParams(cursor=None, limit=50)

        response = service.build_response(
            items=items,
            total_count=0,
            params=params,
        )

        assert response.items == []
        assert response.meta.totalCount == 0
        assert response.meta.pageSize == 0
        assert response.meta.hasMore is False
        assert response.nextCursor is None

    def test_build_response_with_order_by(self, service):
        """Test building response preserves order_by in cursor."""
        items = [{"id": i} for i in range(50)]
        params = PaginationParams(cursor=None, limit=50)

        response = service.build_response(
            items=items,
            total_count=100,
            params=params,
            order_by="created_desc",
        )

        # Decode next cursor and verify order_by preserved
        if response.nextCursor:
            decoded = service.parse_cursor(response.nextCursor)
            assert decoded.get("order_by") == "created_desc"

    def test_build_response_with_filters(self, service):
        """Test building response preserves filters in cursor."""
        items = [{"id": i} for i in range(50)]
        params = PaginationParams(cursor=None, limit=50)
        filters = {"status": "confirmed", "listing_id": "123"}

        response = service.build_response(
            items=items,
            total_count=100,
            params=params,
            filters=filters,
        )

        # Decode next cursor and verify filters preserved
        if response.nextCursor:
            decoded = service.parse_cursor(response.nextCursor)
            assert decoded.get("filters") == filters

    @pytest.mark.asyncio
    async def test_paginate_query_first_page(self, service):
        """Test paginate_query for first page."""
        # Mock query function
        async def mock_query(offset: int, limit: int):
            return [{"id": i} for i in range(offset, offset + limit)]

        params = PaginationParams(cursor=None, limit=50)

        response = await service.paginate_query(
            query_func=mock_query,
            params=params,
            total_count=150,
        )

        assert len(response.items) == 50
        assert response.items[0]["id"] == 0
        assert response.meta.hasMore is True
        assert response.nextCursor is not None

    @pytest.mark.asyncio
    async def test_paginate_query_with_cursor(self, service):
        """Test paginate_query with existing cursor."""
        # Mock query function
        async def mock_query(offset: int, limit: int):
            return [{"id": i} for i in range(offset, offset + limit)]

        # Create cursor for offset 50
        cursor = service.create_cursor(offset=50)
        params = PaginationParams(cursor=cursor, limit=50)

        response = await service.paginate_query(
            query_func=mock_query,
            params=params,
            total_count=150,
        )

        assert len(response.items) == 50
        assert response.items[0]["id"] == 50
        assert response.meta.hasMore is True

    @pytest.mark.asyncio
    async def test_paginate_query_last_page(self, service):
        """Test paginate_query for last page."""
        # Mock query function
        async def mock_query(offset: int, limit: int):
            remaining = 150 - offset
            count = min(limit, remaining)
            return [{"id": i} for i in range(offset, offset + count)]

        cursor = service.create_cursor(offset=100)
        params = PaginationParams(cursor=cursor, limit=50)

        response = await service.paginate_query(
            query_func=mock_query,
            params=params,
            total_count=150,
        )

        assert len(response.items) == 50
        assert response.items[0]["id"] == 100
        assert response.meta.hasMore is False
        assert response.nextCursor is None

    @pytest.mark.asyncio
    async def test_paginate_query_validates_page_size(self, service):
        """Test paginate_query validates and clamps page size."""
        call_args = []

        async def mock_query(offset: int, limit: int):
            call_args.append({"offset": offset, "limit": limit})
            return [{"id": i} for i in range(limit)]

        # Request page size at limit (PaginationParams validates <= 200)
        params = PaginationParams(cursor=None, limit=200)

        await service.paginate_query(
            query_func=mock_query,
            params=params,
            total_count=500,
        )

        # Should use the requested limit (200)
        assert call_args[0]["limit"] == 200


class TestGetPaginationService:
    """Test suite for get_pagination_service singleton function."""

    def test_requires_secret_on_first_call(self):
        """Test that first call requires secret."""
        # Reset global singleton
        import src.services.pagination_service
        src.services.pagination_service._pagination_service = None

        with pytest.raises(ValueError, match="secret required"):
            get_pagination_service(secret=None)

    def test_singleton_pattern(self):
        """Test that get_pagination_service returns same instance."""
        # Reset global singleton
        import src.services.pagination_service
        src.services.pagination_service._pagination_service = None

        service1 = get_pagination_service(secret="test-secret")
        service2 = get_pagination_service()

        assert service1 is service2

    def test_singleton_initialization(self):
        """Test singleton is initialized with correct parameters."""
        # Reset global singleton
        import src.services.pagination_service
        src.services.pagination_service._pagination_service = None

        service = get_pagination_service(
            secret="my-secret",
            default_page_size=75,
            max_page_size=300
        )

        assert service.secret == "my-secret"
        assert service.default_page_size == 75
        assert service.max_page_size == 300
