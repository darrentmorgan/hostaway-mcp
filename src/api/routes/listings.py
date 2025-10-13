"""Listings routes for MCP tools.

Provides endpoints to retrieve property listings, details, and availability.
These endpoints are automatically exposed as MCP tools via FastAPI-MCP.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.mcp.auth import get_authenticated_client
from src.services.hostaway_client import HostawayClient

router = APIRouter()


class AvailabilityRecord(BaseModel):
    """Availability record for a specific date."""

    date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    status: str = Field(..., description="Availability status (available, blocked, booked)")
    price: float | None = Field(None, description="Price for this date")
    min_stay: int | None = Field(None, description="Minimum stay in nights")


class ListingsResponse(BaseModel):
    """Response model for listings list."""

    listings: list[dict] = Field(..., description="List of property listings")
    count: int = Field(..., description="Total number of listings")
    limit: int = Field(..., description="Page size limit")
    offset: int = Field(..., description="Pagination offset")


class AvailabilityResponse(BaseModel):
    """Response model for listing availability."""

    listing_id: int = Field(..., description="Listing ID")
    start_date: str = Field(..., description="Start date of availability range")
    end_date: str = Field(..., description="End date of availability range")
    availability: list[AvailabilityRecord] = Field(..., description="Availability records")


@router.get(
    "/listings",
    response_model=ListingsResponse,
    summary="Get all property listings",
    description="Retrieve all property listings with pagination support",
    tags=["Listings"],
)
async def get_listings(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    client: HostawayClient = Depends(get_authenticated_client),
) -> ListingsResponse:
    """
    Get all property listings with pagination.

    This tool retrieves a paginated list of all property listings from Hostaway.
    Useful for:
    - Browsing all available properties
    - Building property catalogs
    - Searching across properties

    Args:
        limit: Maximum number of listings to return (1-1000, default: 100)
        offset: Number of listings to skip for pagination (default: 0)
        client: Authenticated Hostaway client (injected)

    Returns:
        ListingsResponse with listings array and pagination metadata

    Raises:
        HTTPException: If API request fails
    """
    try:
        listings = await client.get_listings(limit=limit, offset=offset)

        return ListingsResponse(
            listings=listings,
            count=len(listings),
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/listings/{listing_id}",
    response_model=dict,
    summary="Get property listing details",
    description="Retrieve detailed information for a specific property listing",
    tags=["Listings"],
)
async def get_listing(
    listing_id: int,
    client: HostawayClient = Depends(get_authenticated_client),
) -> dict:
    """
    Get detailed information for a specific property listing.

    This tool retrieves complete details for a single property, including:
    - Property information (name, address, capacity, etc.)
    - Pricing details
    - Amenities
    - Availability status
    - Images and descriptions

    Args:
        listing_id: Unique identifier for the listing
        client: Authenticated Hostaway client (injected)

    Returns:
        Complete listing details

    Raises:
        HTTPException: If listing not found (404) or API request fails
    """
    try:
        listing = await client.get_listing(listing_id)

        if not listing:
            raise HTTPException(status_code=404, detail=f"Listing {listing_id} not found")

        return listing
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/listings/{listing_id}/calendar",
    response_model=AvailabilityResponse,
    summary="Get listing availability calendar",
    description="Retrieve availability calendar for a property listing",
    tags=["Listings"],
)
async def get_listing_availability(
    listing_id: int,
    start_date: str = Query(
        ..., description="Start date (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"
    ),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)", regex=r"^\d{4}-\d{2}-\d{2}$"),
    client: HostawayClient = Depends(get_authenticated_client),
) -> AvailabilityResponse:
    """
    Get availability calendar for a property listing.

    This tool retrieves the availability status for each date in the specified range.
    Shows which dates are:
    - Available for booking
    - Blocked/unavailable
    - Already booked

    Includes pricing and minimum stay information for each date.

    Args:
        listing_id: Unique identifier for the listing
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        client: Authenticated Hostaway client (injected)

    Returns:
        AvailabilityResponse with availability records for each date

    Raises:
        HTTPException: If listing not found (404) or API request fails
    """
    try:
        availability_data = await client.get_listing_availability(
            listing_id=listing_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Convert API response to AvailabilityRecord models
        availability_records = [
            AvailabilityRecord(
                date=record.get("date", ""),
                status=record.get("status", "unknown"),
                price=record.get("price"),
                min_stay=record.get("min_stay"),
            )
            for record in availability_data
        ]

        return AvailabilityResponse(
            listing_id=listing_id,
            start_date=start_date,
            end_date=end_date,
            availability=availability_records,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
