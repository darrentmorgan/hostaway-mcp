"""Analytics routes for MCP tools.

Provides endpoints for financial analytics and reporting summaries.
These endpoints are automatically exposed as MCP tools via FastAPI-MCP.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.dependencies import OrganizationContext, get_organization_context
from src.mcp.auth import get_authenticated_client
from src.services.hostaway_client import HostawayClient

router = APIRouter()


# T055: Financial summary endpoint for AI-powered analytics
class ListingSummary(BaseModel):
    """Summary for a single listing."""

    listing_id: int = Field(..., description="Listing ID")
    listing_name: str = Field(..., description="Property name")
    total_revenue: float = Field(..., description="Total revenue for period")
    booking_count: int = Field(..., description="Number of bookings")
    nights_booked: int = Field(..., description="Total nights booked")
    average_nightly_rate: float = Field(..., description="Average rate per night")
    occupancy_rate: float = Field(..., description="Occupancy percentage (0-100)")


class FinancialSummaryResponse(BaseModel):
    """Response model for financial summary."""

    period_start: str = Field(..., description="Start date of analysis period")
    period_end: str = Field(..., description="End date of analysis period")
    total_revenue: float = Field(..., description="Total revenue across all listings")
    total_bookings: int = Field(..., description="Total number of bookings")
    total_nights: int = Field(..., description="Total nights booked")
    average_nightly_rate: float = Field(..., description="Average nightly rate across all listings")
    listings_summary: list[ListingSummary] = Field(..., description="Per-listing breakdown")
    organization_id: int = Field(..., description="Organization ID (for verification)")


@router.get(
    "/analytics/financial",
    response_model=FinancialSummaryResponse,
    summary="Get financial summary analytics",
    description="AI-powered financial analysis aggregating revenue, bookings, and rates per listing",
    tags=["Analytics"],
    operation_id="get_financial_summary",
)
async def get_financial_summary(
    start_date: str = Query(
        ...,
        description="Analysis start date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    end_date: str = Query(
        ...,
        description="Analysis end date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    client: HostawayClient = Depends(get_authenticated_client),
    context: OrganizationContext = Depends(get_organization_context),
) -> FinancialSummaryResponse:
    """
    Get financial summary with per-listing revenue breakdown.

    This AI-powered tool enables natural language queries like:
    "What's my total revenue this month?" or
    "Show me booking stats for Q3 2024"

    The tool aggregates:
    - Total revenue across all listings
    - Booking counts and nights booked
    - Average nightly rates
    - Per-listing performance breakdown
    - Occupancy rates

    Organization scoping (T058): Only includes listings from authenticated org.

    Args:
        start_date: Analysis period start (YYYY-MM-DD format)
        end_date: Analysis period end (YYYY-MM-DD format)
        client: Authenticated Hostaway client (injected)
        context: Organization context for multi-tenant scoping (injected)

    Returns:
        FinancialSummaryResponse with aggregated metrics and per-listing breakdown

    Raises:
        HTTPException: 400 for invalid date range, 404 if no data found, 500 for API failures

    Example Usage:
        "What's my total revenue from January to March 2024?"
        -> GET /api/analytics/financial?start_date=2024-01-01&end_date=2024-03-31

    Example Response:
        {
            "period_start": "2024-01-01",
            "period_end": "2024-03-31",
            "total_revenue": 45000.00,
            "total_bookings": 45,
            "total_nights": 180,
            "average_nightly_rate": 250.00,
            "listings_summary": [
                {
                    "listing_id": 123,
                    "listing_name": "Beach Condo",
                    "total_revenue": 25000.00,
                    "booking_count": 25,
                    "nights_booked": 100,
                    "average_nightly_rate": 250.00,
                    "occupancy_rate": 85.5
                },
                ...
            ],
            "organization_id": 456
        }
    """
    try:
        # Validate date range
        from datetime import datetime

        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()

            if end < start:
                raise HTTPException(
                    status_code=400,
                    detail="End date must be on or after start date",
                )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {e!s}",
            )

        # Organization scoping: Only fetch listings for authenticated organization
        # This ensures User A cannot see User B's financial data (T058)
        listings = await client.get_listings(limit=1000, offset=0)

        if not listings:
            raise HTTPException(
                status_code=404,
                detail="No listings found for organization",
            )

        # Aggregate financial data per listing
        listings_summary: list[ListingSummary] = []
        total_revenue = 0.0
        total_bookings = 0
        total_nights = 0

        for listing in listings:
            listing_id = listing.get("id")
            listing_name = listing.get("name", f"Listing {listing_id}")

            # Fetch bookings for this listing in date range
            try:
                bookings = await client.get_bookings_by_listing(
                    listing_id=listing_id,
                    start_date=start_date,
                    end_date=end_date,
                )

                # Calculate listing metrics
                listing_revenue = sum(b.get("totalPrice", 0) for b in bookings)
                listing_bookings = len(bookings)
                listing_nights = sum(b.get("nightsCount", 0) for b in bookings)
                avg_rate = listing_revenue / listing_nights if listing_nights > 0 else 0.0

                # Calculate occupancy rate (nights booked / total nights in period)
                period_days = (end - start).days + 1
                occupancy = (listing_nights / period_days) * 100 if period_days > 0 else 0.0

                listings_summary.append(
                    ListingSummary(
                        listing_id=listing_id,
                        listing_name=listing_name,
                        total_revenue=round(listing_revenue, 2),
                        booking_count=listing_bookings,
                        nights_booked=listing_nights,
                        average_nightly_rate=round(avg_rate, 2),
                        occupancy_rate=round(occupancy, 2),
                    )
                )

                # Aggregate totals
                total_revenue += listing_revenue
                total_bookings += listing_bookings
                total_nights += listing_nights

            except Exception as e:
                # Log warning but continue with other listings
                print(f"Warning: Failed to fetch bookings for listing {listing_id}: {e}")
                continue

        # Calculate overall average nightly rate
        overall_avg_rate = total_revenue / total_nights if total_nights > 0 else 0.0

        return FinancialSummaryResponse(
            period_start=start_date,
            period_end=end_date,
            total_revenue=round(total_revenue, 2),
            total_bookings=total_bookings,
            total_nights=total_nights,
            average_nightly_rate=round(overall_avg_rate, 2),
            listings_summary=listings_summary,
            organization_id=context.organization_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate financial summary: {e!s}",
        )
