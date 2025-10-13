"""Financial models for revenue and expense tracking.

This module provides Pydantic models for financial reports, including
revenue breakdown, expense tracking, and profitability metrics.
"""

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class FinancialReportPeriod(str, Enum):
    """Financial reporting period types."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class RevenueBreakdown(BaseModel):
    """Revenue breakdown by booking source/channel."""

    total_revenue: Decimal = Field(
        ...,
        description="Total revenue for period",
        ge=0,
        decimal_places=2,
    )

    direct_bookings: Decimal = Field(
        default=Decimal("0.00"),
        description="Revenue from direct bookings",
        ge=0,
        decimal_places=2,
    )

    airbnb: Decimal = Field(
        default=Decimal("0.00"),
        description="Revenue from Airbnb",
        ge=0,
        decimal_places=2,
    )

    vrbo: Decimal = Field(
        default=Decimal("0.00"),
        description="Revenue from VRBO",
        ge=0,
        decimal_places=2,
    )

    booking_com: Decimal = Field(
        default=Decimal("0.00"),
        description="Revenue from Booking.com",
        ge=0,
        decimal_places=2,
    )

    other: Decimal = Field(
        default=Decimal("0.00"),
        description="Revenue from other sources",
        ge=0,
        decimal_places=2,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_revenue": "12500.00",
                "direct_bookings": "3000.00",
                "airbnb": "6000.00",
                "vrbo": "2500.00",
                "booking_com": "1000.00",
                "other": "0.00",
            }
        }
    }


class ExpenseBreakdown(BaseModel):
    """Expense breakdown by category."""

    total_expenses: Decimal = Field(
        ...,
        description="Total expenses for period",
        ge=0,
        decimal_places=2,
    )

    cleaning: Decimal = Field(
        default=Decimal("0.00"),
        description="Cleaning service expenses",
        ge=0,
        decimal_places=2,
    )

    maintenance: Decimal = Field(
        default=Decimal("0.00"),
        description="Maintenance and repairs",
        ge=0,
        decimal_places=2,
    )

    utilities: Decimal = Field(
        default=Decimal("0.00"),
        description="Utilities (water, electricity, internet)",
        ge=0,
        decimal_places=2,
    )

    platform_fees: Decimal = Field(
        default=Decimal("0.00"),
        description="Platform commission fees",
        ge=0,
        decimal_places=2,
    )

    supplies: Decimal = Field(
        default=Decimal("0.00"),
        description="Supplies and amenities",
        ge=0,
        decimal_places=2,
    )

    other: Decimal = Field(
        default=Decimal("0.00"),
        description="Other expenses",
        ge=0,
        decimal_places=2,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_expenses": "3250.00",
                "cleaning": "1200.00",
                "maintenance": "500.00",
                "utilities": "300.00",
                "platform_fees": "1000.00",
                "supplies": "200.00",
                "other": "50.00",
            }
        }
    }


class FinancialReport(BaseModel):
    """Financial report with revenue, expenses, and profitability metrics.

    Aggregates financial data for a specific period and optionally for a specific property.
    """

    period_start: date = Field(
        ...,
        description="Report period start date",
    )

    period_end: date = Field(
        ...,
        description="Report period end date",
    )

    period_type: FinancialReportPeriod = Field(
        ...,
        description="Type of reporting period",
    )

    listing_id: int | None = Field(
        None,
        description="Specific listing ID (null for all properties)",
        gt=0,
    )

    listing_name: str | None = Field(
        None,
        description="Listing name (if listing_id specified)",
        max_length=200,
    )

    revenue: RevenueBreakdown = Field(
        ...,
        description="Revenue breakdown",
    )

    expenses: ExpenseBreakdown = Field(
        ...,
        description="Expense breakdown",
    )

    net_income: Decimal = Field(
        ...,
        description="Net income (revenue - expenses)",
        decimal_places=2,
    )

    total_bookings: int = Field(
        ...,
        description="Number of bookings in period",
        ge=0,
    )

    total_nights_booked: int = Field(
        ...,
        description="Total nights booked in period",
        ge=0,
    )

    average_daily_rate: Decimal = Field(
        ...,
        description="Average nightly rate for period",
        ge=0,
        decimal_places=2,
    )

    occupancy_rate: Decimal = Field(
        ...,
        description="Occupancy rate as percentage (0-100)",
        ge=0,
        le=100,
        decimal_places=2,
    )

    currency: str = Field(
        default="USD",
        description="Currency code (ISO 4217)",
        pattern=r"^[A-Z]{3}$",
    )

    @property
    def profit_margin(self) -> Decimal:
        """Calculate profit margin as percentage."""
        if self.revenue.total_revenue == 0:
            return Decimal("0.00")
        return (self.net_income / self.revenue.total_revenue) * 100

    model_config = {
        "json_schema_extra": {
            "example": {
                "period_start": "2025-10-01",
                "period_end": "2025-10-31",
                "period_type": "monthly",
                "listing_id": 12345,
                "listing_name": "Cozy Downtown Apartment",
                "revenue": {
                    "total_revenue": "12500.00",
                    "direct_bookings": "3000.00",
                    "airbnb": "6000.00",
                    "vrbo": "2500.00",
                    "booking_com": "1000.00",
                },
                "expenses": {
                    "total_expenses": "3250.00",
                    "cleaning": "1200.00",
                    "platform_fees": "1000.00",
                },
                "net_income": "9250.00",
                "total_bookings": 15,
                "total_nights_booked": 75,
                "average_daily_rate": "166.67",
                "occupancy_rate": "80.65",
                "currency": "USD",
            }
        }
    }
