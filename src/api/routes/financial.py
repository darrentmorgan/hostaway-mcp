"""Financial routes for MCP tools.

Provides endpoints to retrieve financial reports and analytics.
These endpoints are automatically exposed as MCP tools via FastAPI-MCP.
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from nanoid import generate
from pydantic import BaseModel, Field

from src.mcp.auth import get_authenticated_client
from src.services.hostaway_client import HostawayClient

router = APIRouter()


class FinancialReportResponse(BaseModel):
    """Response model for financial report."""

    report: dict = Field(..., description="Financial report data")


@router.get(
    "/financialReports",
    response_model=dict,
    summary="Get financial report",
    description="Retrieve financial report with revenue and expense breakdown for a date range",
    tags=["Financial"],
)
async def get_financial_report(
    start_date: str = Query(
        ...,
        description="Report start date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    end_date: str = Query(
        ...,
        description="Report end date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
    listing_id: int | None = Query(
        None,
        description="Optional: Get report for specific property (default: all properties)",
        gt=0,
    ),
    client: HostawayClient = Depends(get_authenticated_client),
) -> dict:
    """
    Get financial report for a date range.

    This tool retrieves financial analytics including:
    - Revenue breakdown by booking channel (direct, Airbnb, VRBO, etc.)
    - Expense breakdown by category (cleaning, maintenance, utilities, etc.)
    - Net income and profit margin
    - Occupancy rate and average daily rate
    - Total bookings and nights booked

    Can be filtered to a specific property or aggregated across all properties.

    Args:
        start_date: Report start date in YYYY-MM-DD format
        end_date: Report end date in YYYY-MM-DD format
        listing_id: Optional property ID for property-specific report
        client: Authenticated Hostaway client (injected)

    Returns:
        Financial report with revenue, expenses, and profitability metrics

    Raises:
        HTTPException: If invalid date range or API request fails
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

        # Get report based on whether listing_id is provided
        if listing_id:
            report = await client.get_property_financials(
                property_id=listing_id,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            report = await client.get_financial_report(
                start_date=start_date,
                end_date=end_date,
            )

        if not report:
            raise HTTPException(
                status_code=404,
                detail="No financial data found for the specified period",
            )

        return report
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        # Handle Hostaway API errors with compact error hygiene
        correlation_id = generate(size=10)

        # Log full error server-side
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            "Hostaway API error for financial reports",
            extra={
                "correlation_id": correlation_id,
                "status_code": e.response.status_code,
                "start_date": start_date,
                "end_date": end_date,
                "listing_id": listing_id,
                "response_text": e.response.text[:500],  # First 500 chars only
            },
        )

        # Return compact JSON error (no HTML)
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Financial reports endpoint not available",
                    "message": "The Hostaway API financial reports endpoint may not be enabled for your account",
                    "correlation_id": correlation_id,
                },
            )
        if e.response.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Permission denied",
                    "message": "Your Hostaway account does not have permission to access financial reports",
                    "correlation_id": correlation_id,
                },
            )
        raise HTTPException(
            status_code=502,
            detail={
                "error": "Hostaway API error",
                "message": f"Failed to fetch financial reports (HTTP {e.response.status_code})",
                "correlation_id": correlation_id,
            },
        )
    except Exception as e:
        # Catch-all for unexpected errors
        correlation_id = generate(size=10)

        import logging

        logger = logging.getLogger(__name__)
        logger.exception(
            "Unexpected error in financial reports",
            extra={
                "correlation_id": correlation_id,
                "start_date": start_date,
                "end_date": end_date,
                "listing_id": listing_id,
            },
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred while fetching financial reports",
                "correlation_id": correlation_id,
            },
        )
