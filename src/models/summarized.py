"""Summarized response models for API-level response optimization.

Defines compact Pydantic models for property listings and bookings with only
essential fields to reduce response sizes by 80-90% for AI assistant consumption.
Based on specs/009-add-api-level/data-model.md entity definitions.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SummarizedListing(BaseModel):
    """Summarized property listing with essential fields only.

    Reduces full listing response size by ~90% by including only core
    identification and availability information.

    Attributes:
        id: Unique property listing ID
        name: Property display name
        city: City location (optional)
        country: Country location (optional)
        bedrooms: Number of bedrooms (non-negative)
        status: Availability status derived from isActive boolean
    """

    id: int = Field(..., description="Unique property listing ID")
    name: str = Field(..., description="Property display name")
    city: str | None = Field(None, description="City location")
    country: str | None = Field(None, description="Country location")
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms")
    status: str = Field(..., description="Availability status (Available or Inactive)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 12345,
                "name": "Luxury Villa in Seminyak",
                "city": "Seminyak",
                "country": "Indonesia",
                "bedrooms": 3,
                "status": "Available",
            }
        }
    )


class SummarizedBooking(BaseModel):
    """Summarized booking with essential fields only.

    Reduces full booking response size by excluding nested objects (guest details,
    property info, payment history). Includes only core booking information.

    Attributes:
        id: Unique booking ID
        guestName: Guest full name
        checkIn: Check-in date (ISO 8601: YYYY-MM-DD)
        checkOut: Check-out date (ISO 8601: YYYY-MM-DD)
        listingId: Associated property listing ID
        status: Booking status (e.g., confirmed, cancelled)
        totalPrice: Total booking price (non-negative)
    """

    id: int = Field(..., description="Unique booking ID")
    guestName: str = Field(..., description="Guest full name", alias="guest_name")  # noqa: N815
    checkIn: str = Field(  # noqa: N815
        ..., description="Check-in date (ISO 8601: YYYY-MM-DD)", alias="check_in"
    )
    checkOut: str = Field(  # noqa: N815
        ..., description="Check-out date (ISO 8601: YYYY-MM-DD)", alias="check_out"
    )
    listingId: int = Field(  # noqa: N815
        ..., description="Associated property listing ID", alias="listing_id"
    )
    status: str = Field(..., description="Booking status (e.g., confirmed, cancelled)")
    totalPrice: float = Field(..., ge=0, description="Total booking price", alias="total_price")  # noqa: N815

    @field_validator("checkIn", "checkOut")
    @classmethod
    def validate_iso_date(cls, v: str) -> str:
        """Validate ISO 8601 date format (YYYY-MM-DD).

        Args:
            v: Date string to validate

        Returns:
            Validated date string

        Raises:
            ValueError: If date format is invalid
        """
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 date format (expected YYYY-MM-DD): {v}") from e

    model_config = ConfigDict(
        populate_by_name=True,  # Allow both camelCase and snake_case
        json_schema_extra={
            "example": {
                "id": 67890,
                "guestName": "John Doe",
                "checkIn": "2025-11-15",
                "checkOut": "2025-11-22",
                "listingId": 12345,
                "status": "confirmed",
                "totalPrice": 2500.00,
            }
        },
    )
