"""Pagination service for cursor-based navigation.

Provides cursor encoding, decoding, and paginated response building.
Integrates cursor_codec and cursor_storage for complete pagination workflow.
"""

from typing import Any, TypeVar

from src.models.pagination import PageMetadata, PaginatedResponse, PaginationParams
from src.services.cursor_storage import get_cursor_storage
from src.utils.cursor_codec import decode_cursor, encode_cursor

T = TypeVar("T")


class PaginationService:
    """Service for cursor-based pagination.

    Handles cursor creation, validation, and paginated response building.

    Attributes:
        secret: HMAC secret for cursor signing
        default_page_size: Default items per page
        max_page_size: Maximum allowed items per page
    """

    def __init__(
        self,
        secret: str,
        default_page_size: int = 50,
        max_page_size: int = 200,
    ) -> None:
        """Initialize pagination service.

        Args:
            secret: HMAC secret for cursor signing
            default_page_size: Default page size (default: 50)
            max_page_size: Maximum page size (default: 200)
        """
        self.secret = secret
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size
        self.cursor_storage = get_cursor_storage()

    def validate_page_size(self, requested: int | None) -> int:
        """Validate and normalize page size.

        Args:
            requested: Requested page size (None uses default)

        Returns:
            Validated page size (clamped to max_page_size)
        """
        if requested is None:
            return self.default_page_size

        if requested < 1:
            return self.default_page_size

        return min(requested, self.max_page_size)

    def create_cursor(
        self,
        offset: int,
        order_by: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> str:
        """Create pagination cursor.

        Args:
            offset: Current position in result set
            order_by: Sort order (e.g., "created_desc")
            filters: Query filters

        Returns:
            Encoded cursor string
        """
        return encode_cursor(
            offset=offset,
            secret=self.secret,
            order_by=order_by,
            filters=filters,
        )

    def parse_cursor(self, cursor: str) -> dict[str, Any]:
        """Parse and validate cursor.

        Args:
            cursor: Encoded cursor string

        Returns:
            Decoded cursor data

        Raises:
            CursorCodecError: If cursor is invalid or expired
        """
        return decode_cursor(cursor, secret=self.secret)

    def build_response(
        self,
        items: list[T],
        total_count: int,
        params: PaginationParams,
        order_by: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> PaginatedResponse[T]:
        """Build paginated response with metadata and next cursor.

        Args:
            items: Current page of items
            total_count: Total items across all pages
            params: Pagination parameters from request
            order_by: Sort order for cursor
            filters: Query filters for cursor

        Returns:
            PaginatedResponse with items, metadata, and optional next cursor
        """
        # Determine current offset
        if params.cursor:
            cursor_data = self.parse_cursor(params.cursor)
            current_offset = cursor_data["offset"]
        else:
            current_offset = 0

        # Calculate next offset
        next_offset = current_offset + len(items)
        has_more = next_offset < total_count

        # Create next cursor if more pages available
        next_cursor = None
        if has_more:
            next_cursor = self.create_cursor(
                offset=next_offset,
                order_by=order_by,
                filters=filters,
            )

        # Build metadata
        meta = PageMetadata(
            totalCount=total_count,
            pageSize=len(items),
            hasMore=has_more,
        )

        return PaginatedResponse[T](
            items=items,
            nextCursor=next_cursor,
            meta=meta,
        )

    async def paginate_query(
        self,
        query_func: Any,  # Callable that accepts offset and limit
        params: PaginationParams,
        total_count: int,
        order_by: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> PaginatedResponse[T]:
        """Execute paginated query and build response.

        Helper method that executes query function with pagination parameters
        and builds the response.

        Args:
            query_func: Async function that accepts (offset, limit) and returns items
            params: Pagination parameters
            total_count: Total items available
            order_by: Sort order
            filters: Query filters

        Returns:
            PaginatedResponse with results

        Example:
            >>> async def fetch_listings(offset: int, limit: int) -> list[Listing]:
            ...     # Fetch from database
            ...     return await db.query("SELECT * FROM listings LIMIT ? OFFSET ?", limit, offset)
            >>> params = PaginationParams(cursor=None, limit=50)
            >>> response = await service.paginate_query(
            ...     query_func=fetch_listings,
            ...     params=params,
            ...     total_count=500
            ... )
        """
        page_size = self.validate_page_size(params.limit)

        # Determine offset from cursor
        if params.cursor:
            cursor_data = self.parse_cursor(params.cursor)
            offset = cursor_data["offset"]
        else:
            offset = 0

        # Execute query
        items = await query_func(offset=offset, limit=page_size)

        # Build response
        return self.build_response(
            items=items,
            total_count=total_count,
            params=params,
            order_by=order_by,
            filters=filters,
        )


# Global singleton instance
_pagination_service: PaginationService | None = None


def get_pagination_service(
    secret: str | None = None,
    default_page_size: int = 50,
    max_page_size: int = 200,
) -> PaginationService:
    """Get global pagination service instance.

    Args:
        secret: HMAC secret (required for first call)
        default_page_size: Default page size
        max_page_size: Maximum page size

    Returns:
        Singleton PaginationService instance

    Raises:
        ValueError: If secret not provided on first call
    """
    global _pagination_service

    if _pagination_service is None:
        if secret is None:
            raise ValueError("secret required for first initialization")
        _pagination_service = PaginationService(
            secret=secret,
            default_page_size=default_page_size,
            max_page_size=max_page_size,
        )

    return _pagination_service
