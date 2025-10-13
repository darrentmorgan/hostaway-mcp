"""Hostaway MCP Server data models.

This package contains Pydantic models for all Hostaway API entities and
multi-tenant organization management.
"""

from src.models.auth import AccessToken, TokenRefreshRequest, TokenRefreshResponse
from src.models.bookings import (
    Booking,
    BookingSearchFilters,
    BookingStatus,
    PaymentInfo,
    PaymentStatus,
)
from src.models.financial import (
    ExpenseBreakdown,
    FinancialReport,
    FinancialReportPeriod,
    RevenueBreakdown,
)
from src.models.listings import (
    AvailabilityInfo,
    Listing,
    ListingSummary,
    PricingInfo,
)
from src.models.organization import (
    APIKey,
    AuditLog,
    HostawayCredentials,
    Organization,
    OrganizationMember,
    OrganizationRole,
    Subscription,
    SubscriptionStatus,
    UsageMetrics,
)

__all__ = [
    # Authentication models
    "AccessToken",
    "TokenRefreshRequest",
    "TokenRefreshResponse",
    # Listing models
    "Listing",
    "ListingSummary",
    "PricingInfo",
    "AvailabilityInfo",
    # Booking models
    "Booking",
    "BookingSearchFilters",
    "BookingStatus",
    "PaymentInfo",
    "PaymentStatus",
    # Financial models
    "FinancialReport",
    "RevenueBreakdown",
    "ExpenseBreakdown",
    "FinancialReportPeriod",
    # Organization models
    "Organization",
    "OrganizationMember",
    "OrganizationRole",
    "APIKey",
    "HostawayCredentials",
    "Subscription",
    "SubscriptionStatus",
    "UsageMetrics",
    "AuditLog",
]
