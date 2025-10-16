"""Bookings routes for MCP tools.

Provides endpoints to search and retrieve booking/reservation information.
These endpoints are automatically exposed as MCP tools via FastAPI-MCP.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.mcp.auth import get_authenticated_client
from src.models.pagination import PageMetadata, PaginatedResponse
from src.services.hostaway_client import HostawayClient
from src.utils.cursor_codec import decode_cursor, encode_cursor

router = APIRouter()


class BookingsResponse(BaseModel):
    """Response model for bookings search."""

    bookings: list[dict] = Field(..., description="List of bookings/reservations")
    count: int = Field(..., description="Total number of bookings returned")
    limit: int = Field(..., description="Page size limit")
    offset: int = Field(..., description="Pagination offset")


@router.get(
    "/reservations",
    response_model=PaginatedResponse[dict],
    summary="Search bookings/reservations",
    description="Search and filter bookings/reservations with cursor-based pagination",
    tags=["Bookings"],
)
async def search_bookings(
    listing_id: int | None = Query(None, description="Filter by property ID"),
    check_in_from: str | None = Query(
        None,
        description="Filter bookings with check-in on or after this date (YYYY-MM-DD)",
        regex=r"^\d{4}-\d{2}-\d{2}$",
    ),
    check_in_to: str | None = Query(
        None,
        description="Filter bookings with check-in on or before this date (YYYY-MM-DD)",
        regex=r"^\d{4}-\d{2}-\d{2}$",
    ),
    check_out_from: str | None = Query(
        None,
        description="Filter bookings with check-out on or after this date (YYYY-MM-DD)",
        regex=r"^\d{4}-\d{2}-\d{2}$",
    ),
    check_out_to: str | None = Query(
        None,
        description="Filter bookings with check-out on or before this date (YYYY-MM-DD)",
        regex=r"^\d{4}-\d{2}-\d{2}$",
    ),
    status: str | None = Query(
        None,
        description="Filter by booking status (comma-separated for multiple: confirmed,pending)",
    ),
    guest_email: str | None = Query(None, description="Filter by guest email address"),
    booking_source: str | None = Query(
        None, description="Filter by booking channel (airbnb, vrbo, etc.)"
    ),
    min_guests: int | None = Query(
        None, ge=1, description="Filter bookings with at least this many guests"
    ),
    max_guests: int | None = Query(
        None, ge=1, description="Filter bookings with at most this many guests"
    ),
    limit: int = Query(default=100, ge=1, le=200, description="Maximum results per page"),
    cursor: str | None = Query(None, description="Pagination cursor from previous response"),
    client: HostawayClient = Depends(get_authenticated_client),
) -> PaginatedResponse[dict]:
    """
    Search and filter bookings/reservations with cursor-based pagination.

    This tool searches through bookings with various filter criteria.
    Supports cursor-based pagination for efficient navigation through large result sets.

    Useful for:
    - Finding bookings for a specific date range
    - Checking reservations for a property
    - Looking up bookings by guest email
    - Filtering by booking status or channel

    Args:
        listing_id: Filter by specific property ID
        check_in_from: Filter bookings with check-in on or after this date (YYYY-MM-DD)
        check_in_to: Filter bookings with check-in on or before this date (YYYY-MM-DD)
        check_out_from: Filter bookings with check-out on or after this date (YYYY-MM-DD)
        check_out_to: Filter bookings with check-out on or before this date (YYYY-MM-DD)
        status: Booking status filter (comma-separated: confirmed,pending,cancelled)
        guest_email: Filter by guest email address
        booking_source: Filter by booking channel (airbnb, vrbo, booking_com, direct)
        min_guests: Minimum number of guests
        max_guests: Maximum number of guests
        limit: Maximum number of bookings per page (1-200, default: 100)
        cursor: Optional cursor from previous response for fetching next page
        client: Authenticated Hostaway client (injected)

    Returns:
        PaginatedResponse with items, nextCursor, and metadata

    Raises:
        HTTPException: If API request fails or cursor is invalid

    Example:
        # First page
        GET /reservations?limit=100&status=confirmed
        # Response includes nextCursor

        # Next page
        GET /reservations?cursor=eyJvZmZzZXQiOjEwMCwidHMiOjE2OTc0NTI4MDAuMH0=
    """
    try:
        # Parse cursor if provided
        offset = 0
        if cursor:
            try:
                cursor_data = decode_cursor(cursor, secret="hostaway-cursor-secret")
                offset = cursor_data["offset"]
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid cursor: {e}",
                )

        # Clamp limit to max
        page_size = min(limit, 200)

        # Convert comma-separated status string to list
        status_list = status.split(",") if status else None

        # Search bookings via Hostaway API
        bookings = await client.search_bookings(
            listing_id=listing_id,
            check_in_from=check_in_from,
            check_in_to=check_in_to,
            check_out_from=check_out_from,
            check_out_to=check_out_to,
            status=status_list,
            guest_email=guest_email,
            booking_source=booking_source,
            min_guests=min_guests,
            max_guests=max_guests,
            limit=page_size,
            offset=offset,
        )

        # Estimate total and check for more pages
        total_count = offset + len(bookings) + (100 if len(bookings) == page_size else 0)
        has_more = len(bookings) == page_size

        # Create next cursor if more pages available
        next_cursor = None
        if has_more:
            next_cursor = encode_cursor(
                offset=offset + len(bookings),
                secret="hostaway-cursor-secret",
            )

        # Build paginated response
        return PaginatedResponse[dict](
            items=bookings,
            nextCursor=next_cursor,
            meta=PageMetadata(
                totalCount=total_count,
                pageSize=len(bookings),
                hasMore=has_more,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/reservations/{booking_id}",
    response_model=dict,
    summary="Get booking details",
    description="Retrieve detailed information for a specific booking/reservation",
    tags=["Bookings"],
)
async def get_booking(
    booking_id: int,
    client: HostawayClient = Depends(get_authenticated_client),
) -> dict:
    """
    Get detailed information for a specific booking/reservation.

    This tool retrieves complete details for a single booking, including:
    - Guest information (name, email, phone)
    - Property details
    - Check-in/check-out dates
    - Number of guests
    - Payment information
    - Booking status
    - Special requests

    Args:
        booking_id: Unique identifier for the booking
        client: Authenticated Hostaway client (injected)

    Returns:
        Complete booking details

    Raises:
        HTTPException: If booking not found (404) or API request fails
    """
    try:
        booking = await client.get_booking(booking_id)

        if not booking:
            raise HTTPException(status_code=404, detail=f"Booking {booking_id} not found")

        return booking
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/reservations/{booking_id}/guest",
    response_model=dict,
    summary="Get booking guest information",
    description="Retrieve guest details for a specific booking/reservation",
    tags=["Bookings"],
)
async def get_booking_guest(
    booking_id: int,
    client: HostawayClient = Depends(get_authenticated_client),
) -> dict:
    """
    Get guest information for a specific booking/reservation.

    This tool retrieves detailed guest information, including:
    - Guest name (first and last)
    - Contact details (email, phone)
    - Location (city, country)
    - Language preference
    - Booking history (total bookings with this account)

    Args:
        booking_id: Unique identifier for the booking
        client: Authenticated Hostaway client (injected)

    Returns:
        Guest details for the booking

    Raises:
        HTTPException: If booking not found (404) or API request fails
    """
    try:
        guest = await client.get_booking_guest(booking_id)

        if not guest:
            raise HTTPException(
                status_code=404, detail=f"Guest information not found for booking {booking_id}"
            )

        return guest
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
