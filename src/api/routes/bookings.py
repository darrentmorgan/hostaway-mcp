"""Bookings routes for MCP tools.

Provides endpoints to search and retrieve booking/reservation information.
These endpoints are automatically exposed as MCP tools via FastAPI-MCP.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.mcp.auth import get_authenticated_client
from src.services.hostaway_client import HostawayClient

router = APIRouter()


class BookingsResponse(BaseModel):
    """Response model for bookings search."""

    bookings: List[dict] = Field(..., description="List of bookings/reservations")
    count: int = Field(..., description="Total number of bookings returned")
    limit: int = Field(..., description="Page size limit")
    offset: int = Field(..., description="Pagination offset")


@router.get(
    "/reservations",
    response_model=BookingsResponse,
    summary="Search bookings/reservations",
    description="Search and filter bookings/reservations with various criteria",
    tags=["Bookings"],
)
async def search_bookings(
    listing_id: Optional[int] = Query(None, description="Filter by property ID"),
    check_in_from: Optional[str] = Query(
        None,
        description="Filter bookings with check-in on or after this date (YYYY-MM-DD)",
        regex=r"^\d{4}-\d{2}-\d{2}$",
    ),
    check_in_to: Optional[str] = Query(
        None,
        description="Filter bookings with check-in on or before this date (YYYY-MM-DD)",
        regex=r"^\d{4}-\d{2}-\d{2}$",
    ),
    check_out_from: Optional[str] = Query(
        None,
        description="Filter bookings with check-out on or after this date (YYYY-MM-DD)",
        regex=r"^\d{4}-\d{2}-\d{2}$",
    ),
    check_out_to: Optional[str] = Query(
        None,
        description="Filter bookings with check-out on or before this date (YYYY-MM-DD)",
        regex=r"^\d{4}-\d{2}-\d{2}$",
    ),
    status: Optional[str] = Query(
        None,
        description="Filter by booking status (comma-separated for multiple: confirmed,pending)",
    ),
    guest_email: Optional[str] = Query(None, description="Filter by guest email address"),
    booking_source: Optional[str] = Query(
        None, description="Filter by booking channel (airbnb, vrbo, etc.)"
    ),
    min_guests: Optional[int] = Query(
        None, ge=1, description="Filter bookings with at least this many guests"
    ),
    max_guests: Optional[int] = Query(
        None, ge=1, description="Filter bookings with at most this many guests"
    ),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    client: HostawayClient = Depends(get_authenticated_client),
) -> BookingsResponse:
    """
    Search and filter bookings/reservations.

    This tool searches through bookings with various filter criteria.
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
        limit: Maximum number of bookings to return (1-1000, default: 100)
        offset: Number of bookings to skip for pagination (default: 0)
        client: Authenticated Hostaway client (injected)

    Returns:
        BookingsResponse with bookings array and pagination metadata

    Raises:
        HTTPException: If API request fails
    """
    try:
        # Convert comma-separated status string to list
        status_list = status.split(",") if status else None

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
            limit=limit,
            offset=offset,
        )

        return BookingsResponse(
            bookings=bookings,
            count=len(bookings),
            limit=limit,
            offset=offset,
        )
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
