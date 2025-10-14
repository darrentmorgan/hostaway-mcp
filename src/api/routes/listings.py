"""Listings routes for MCP tools.

Provides endpoints to retrieve property listings, details, and availability.
These endpoints are automatically exposed as MCP tools via FastAPI-MCP.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.mcp.auth import get_authenticated_client
from src.services.hostaway_client import HostawayClient
from src.api.dependencies import get_organization_context, OrganizationContext

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


# T053: Create listing endpoint for AI-powered property creation
class CreateListingRequest(BaseModel):
    """Request model for creating a new listing."""

    name: str = Field(..., description="Property name/title", min_length=1, max_length=200)
    address: str = Field(..., description="Full property address")
    city: str = Field(..., description="City")
    state: str | None = Field(None, description="State/Province")
    country: str = Field(..., description="Country code (US, CA, GB, etc.)")
    zip_code: str | None = Field(None, description="Postal/ZIP code")
    bedrooms: int = Field(..., description="Number of bedrooms", ge=0)
    bathrooms: float = Field(..., description="Number of bathrooms", ge=0)
    max_guests: int = Field(..., description="Maximum guest capacity", ge=1)
    base_price: float = Field(..., description="Base nightly price in USD", gt=0)
    description: str | None = Field(None, description="Property description")
    amenities: list[str] = Field(default_factory=list, description="List of amenities")


class CreateListingResponse(BaseModel):
    """Response model for create listing."""

    listing_id: int = Field(..., description="Newly created listing ID")
    name: str = Field(..., description="Property name")
    status: str = Field(..., description="Creation status")
    message: str = Field(..., description="Success message")


@router.post(
    "/listings",
    response_model=CreateListingResponse,
    status_code=201,
    summary="Create new property listing",
    description="Create a new property listing in Hostaway via AI-powered natural language request",
    tags=["Listings"],
    operation_id="create_listing",
)
async def create_listing(
    listing_data: CreateListingRequest,
    client: HostawayClient = Depends(get_authenticated_client),
    context: OrganizationContext = Depends(get_organization_context),
) -> CreateListingResponse:
    """
    Create a new property listing in Hostaway.

    This AI-powered tool allows creating listings via natural language. Example:
    "Create a 2-bedroom listing in Miami, FL with 4 guests capacity at $150/night"

    The tool will:
    - Validate all required fields
    - Create the listing in the authenticated organization's Hostaway account
    - Return the new listing ID for further operations
    - Scope the listing to the organization (multi-tenant isolation)

    Args:
        listing_data: Property details including name, address, capacity, pricing
        client: Authenticated Hostaway client (injected)
        context: Organization context for multi-tenant scoping (injected)

    Returns:
        CreateListingResponse with new listing ID and confirmation

    Raises:
        HTTPException: 400 for validation errors, 500 for API failures

    Example Request:
        {
            "name": "Luxury Beachfront Condo",
            "address": "123 Ocean Drive",
            "city": "Miami",
            "state": "FL",
            "country": "US",
            "zip_code": "33139",
            "bedrooms": 2,
            "bathrooms": 2.0,
            "max_guests": 4,
            "base_price": 250.00,
            "description": "Beautiful oceanfront condo with stunning views",
            "amenities": ["WiFi", "Air Conditioning", "Pool", "Beach Access"]
        }
    """
    try:
        # Organization scoping: context.organization_id ensures this listing
        # belongs to the authenticated organization (T058 verification)

        # Prepare listing payload for Hostaway API
        listing_payload = {
            "name": listing_data.name,
            "address": listing_data.address,
            "city": listing_data.city,
            "state": listing_data.state or "",
            "country": listing_data.country,
            "zipCode": listing_data.zip_code or "",
            "bedrooms": listing_data.bedrooms,
            "bathrooms": listing_data.bathrooms,
            "maxGuests": listing_data.max_guests,
            "basePrice": listing_data.base_price,
            "description": listing_data.description or "",
            "amenities": listing_data.amenities,
            # Organization context used for isolation
            "organizationId": context.organization_id,
        }

        # Create listing via Hostaway API
        created_listing = await client.create_listing(listing_payload)

        if not created_listing or "id" not in created_listing:
            raise HTTPException(
                status_code=500,
                detail="Listing creation failed - no ID returned",
            )

        return CreateListingResponse(
            listing_id=created_listing["id"],
            name=listing_data.name,
            status="created",
            message=f"Successfully created listing '{listing_data.name}' with ID {created_listing['id']}",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create listing: {e!s}",
        )


# T054: Batch update listings endpoint for AI-powered bulk operations
class ListingUpdate(BaseModel):
    """Single listing update operation."""

    listing_id: int = Field(..., description="Listing ID to update", gt=0)
    base_price: float | None = Field(None, description="New base price", gt=0)
    max_guests: int | None = Field(None, description="New max guests", ge=1)
    description: str | None = Field(None, description="New description")
    amenities: list[str] | None = Field(None, description="New amenities list")


class BatchUpdateRequest(BaseModel):
    """Request model for batch listing updates."""

    updates: list[ListingUpdate] = Field(..., description="List of listing updates", min_length=1)


class UpdateResult(BaseModel):
    """Result for a single update operation."""

    listing_id: int = Field(..., description="Listing ID")
    success: bool = Field(..., description="Whether update succeeded")
    message: str = Field(..., description="Success or error message")


class BatchUpdateResponse(BaseModel):
    """Response model for batch updates (PartialFailureResponse pattern from v1.1)."""

    total: int = Field(..., description="Total updates requested")
    successful: int = Field(..., description="Number of successful updates")
    failed: int = Field(..., description="Number of failed updates")
    results: list[UpdateResult] = Field(..., description="Detailed results for each update")


@router.patch(
    "/listings/batch",
    response_model=BatchUpdateResponse,
    summary="Batch update property listings",
    description="Update multiple listings in a single request with partial failure support",
    tags=["Listings"],
    operation_id="batch_update_listings",
)
async def batch_update_listings(
    batch_request: BatchUpdateRequest,
    client: HostawayClient = Depends(get_authenticated_client),
    context: OrganizationContext = Depends(get_organization_context),
) -> BatchUpdateResponse:
    """
    Batch update multiple property listings.

    This AI-powered tool enables bulk operations via natural language. Example:
    "Increase all nightly rates by 10%" or "Update amenities for listings 123, 456, 789"

    Uses PartialFailureResponse pattern (v1.1):
    - Continues processing even if some updates fail
    - Returns detailed success/failure status for each listing
    - Includes remediation guidance in error messages

    Organization scoping (T058): Only updates listings belonging to authenticated org.

    Args:
        batch_request: List of listing updates (ID + fields to update)
        client: Authenticated Hostaway client (injected)
        context: Organization context for multi-tenant scoping (injected)

    Returns:
        BatchUpdateResponse with detailed results for each update

    Raises:
        HTTPException: 400 for validation errors, never fails entire batch

    Example Request:
        {
            "updates": [
                {"listing_id": 123, "base_price": 275.00},
                {"listing_id": 456, "max_guests": 6, "amenities": ["WiFi", "Pool"]},
                {"listing_id": 789, "description": "Updated description"}
            ]
        }
    """
    results: list[UpdateResult] = []
    successful_count = 0
    failed_count = 0

    for update in batch_request.updates:
        try:
            # Organization scoping: Verify listing belongs to org before updating
            listing = await client.get_listing(update.listing_id)

            if not listing:
                results.append(
                    UpdateResult(
                        listing_id=update.listing_id,
                        success=False,
                        message=f"Listing {update.listing_id} not found (may not belong to your organization)",
                    )
                )
                failed_count += 1
                continue

            # Build update payload (only include fields that are not None)
            update_payload = {}
            if update.base_price is not None:
                update_payload["basePrice"] = update.base_price
            if update.max_guests is not None:
                update_payload["maxGuests"] = update.max_guests
            if update.description is not None:
                update_payload["description"] = update.description
            if update.amenities is not None:
                update_payload["amenities"] = update.amenities

            # Apply update via Hostaway API
            await client.update_listing(update.listing_id, update_payload)

            results.append(
                UpdateResult(
                    listing_id=update.listing_id,
                    success=True,
                    message=f"Successfully updated listing {update.listing_id}",
                )
            )
            successful_count += 1

        except Exception as e:
            results.append(
                UpdateResult(
                    listing_id=update.listing_id,
                    success=False,
                    message=f"Failed to update listing {update.listing_id}: {e!s}",
                )
            )
            failed_count += 1

    return BatchUpdateResponse(
        total=len(batch_request.updates),
        successful=successful_count,
        failed=failed_count,
        results=results,
    )
