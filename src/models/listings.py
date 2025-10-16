"""Listing models for Hostaway property management.

This module provides Pydantic models for property listings, including
pricing information, availability, and both full and abbreviated listing details.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl


class PricingInfo(BaseModel):
    """Pricing information for a property listing."""

    base_price: Decimal = Field(
        ...,
        description="Base nightly rate",
        ge=0,
        decimal_places=2,
    )

    currency: str = Field(
        default="USD",
        description="Currency code (ISO 4217)",
        pattern=r"^[A-Z]{3}$",
    )

    weekend_price: Decimal | None = Field(
        None,
        description="Weekend nightly rate (if different)",
        ge=0,
        decimal_places=2,
    )

    cleaning_fee: Decimal = Field(
        default=Decimal("0.00"),
        description="One-time cleaning fee",
        ge=0,
        decimal_places=2,
    )

    security_deposit: Decimal = Field(
        default=Decimal("0.00"),
        description="Refundable security deposit",
        ge=0,
        decimal_places=2,
    )

    extra_guest_fee: Decimal | None = Field(
        None,
        description="Fee per additional guest beyond base capacity",
        ge=0,
        decimal_places=2,
    )

    min_stay_nights: int = Field(
        default=1,
        description="Minimum stay in nights",
        ge=1,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "base_price": "150.00",
                "currency": "USD",
                "weekend_price": "200.00",
                "cleaning_fee": "75.00",
                "security_deposit": "500.00",
                "extra_guest_fee": "25.00",
                "min_stay_nights": 2,
            }
        }
    }


class AvailabilityInfo(BaseModel):
    """Availability and calendar information for a property."""

    is_available: bool = Field(
        ...,
        description="Whether property is currently available for booking",
    )

    available_from: date | None = Field(
        None,
        description="Date when property becomes available",
    )

    blocked_dates: list[date] = Field(
        default_factory=list,
        description="Dates when property is unavailable",
    )

    booked_dates: list[date] = Field(
        default_factory=list,
        description="Dates with existing reservations",
    )

    calendar_notes: str | None = Field(
        None,
        description="Notes about availability or scheduling",
        max_length=500,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "is_available": True,
                "available_from": "2025-10-15",
                "blocked_dates": ["2025-12-24", "2025-12-25", "2025-12-31"],
                "booked_dates": ["2025-11-10", "2025-11-11", "2025-11-12"],
                "calendar_notes": "Holiday dates blocked for owner use",
            }
        }
    }


class Listing(BaseModel):
    """Complete property listing with all details.

    Represents a rental property in the Hostaway system.
    """

    id: int = Field(
        ...,
        description="Unique listing ID",
        gt=0,
    )

    name: str = Field(
        ...,
        description="Property name/title",
        min_length=1,
        max_length=200,
    )

    address: str = Field(
        ...,
        description="Full property address",
        min_length=1,
        max_length=500,
    )

    city: str = Field(
        ...,
        description="City name",
        min_length=1,
        max_length=100,
    )

    state: str | None = Field(
        None,
        description="State/province",
        max_length=100,
    )

    country: str = Field(
        ...,
        description="Country name or ISO code",
        min_length=2,
        max_length=100,
    )

    postal_code: str | None = Field(
        None,
        description="Postal/ZIP code",
        max_length=20,
    )

    latitude: Decimal | None = Field(
        None,
        description="GPS latitude",
        ge=-90,
        le=90,
        decimal_places=6,
    )

    longitude: Decimal | None = Field(
        None,
        description="GPS longitude",
        ge=-180,
        le=180,
        decimal_places=6,
    )

    description: str = Field(
        ...,
        description="Full property description",
        min_length=1,
        max_length=5000,
    )

    capacity: int = Field(
        ...,
        description="Maximum guest capacity",
        ge=1,
        le=50,
    )

    bedrooms: int = Field(
        ...,
        description="Number of bedrooms",
        ge=0,
        le=20,
    )

    bathrooms: Decimal = Field(
        ...,
        description="Number of bathrooms (0.5 for half bath)",
        ge=0,
        le=20,
        decimal_places=1,
    )

    beds: int = Field(
        default=0,
        description="Total number of beds",
        ge=0,
        le=50,
    )

    property_type: str = Field(
        ...,
        description="Type of property (apartment, house, villa, etc.)",
        max_length=100,
    )

    amenities: list[str] = Field(
        default_factory=list,
        description="List of amenities (WiFi, parking, pool, etc.)",
    )

    pricing: PricingInfo = Field(
        ...,
        description="Pricing information",
    )

    availability: AvailabilityInfo = Field(
        ...,
        description="Availability and calendar info",
    )

    cancellation_policy: str = Field(
        default="moderate",
        description="Cancellation policy type",
        max_length=100,
    )

    check_in_time: str | None = Field(
        None,
        description="Check-in time (e.g., '15:00')",
        pattern=r"^\d{2}:\d{2}$",
    )

    check_out_time: str | None = Field(
        None,
        description="Check-out time (e.g., '11:00')",
        pattern=r"^\d{2}:\d{2}$",
    )

    images: list[HttpUrl] = Field(
        default_factory=list,
        description="URLs to property images",
    )

    channel_ids: dict[str, str] = Field(
        default_factory=dict,
        description="External platform listing IDs (airbnb, vrbo, booking_com)",
    )

    is_active: bool = Field(
        default=True,
        description="Whether listing is active and bookable",
    )

    house_rules: str | None = Field(
        None,
        description="Property-specific rules for guests",
        max_length=2000,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 12345,
                "name": "Cozy Downtown Apartment",
                "address": "123 Main St, Apt 4B",
                "city": "San Francisco",
                "state": "California",
                "country": "USA",
                "postal_code": "94102",
                "latitude": "37.774929",
                "longitude": "-122.419416",
                "description": "Beautiful 2BR apartment in the heart of downtown...",
                "capacity": 4,
                "bedrooms": 2,
                "bathrooms": "1.5",
                "beds": 2,
                "property_type": "apartment",
                "amenities": ["WiFi", "Kitchen", "Parking", "Air Conditioning"],
                "pricing": {
                    "base_price": "150.00",
                    "currency": "USD",
                    "cleaning_fee": "75.00",
                },
                "availability": {"is_available": True},
                "cancellation_policy": "moderate",
                "check_in_time": "15:00",
                "check_out_time": "11:00",
                "images": [
                    "https://example.com/image1.jpg",
                    "https://example.com/image2.jpg",
                ],
                "channel_ids": {"airbnb": "abc123", "vrbo": "xyz789"},
                "is_active": True,
                "house_rules": "No smoking, no pets, quiet hours after 10pm",
            }
        }
    }


class ListingSummary(BaseModel):
    """Abbreviated listing information for list/search results.

    Used when returning multiple properties to reduce payload size.
    """

    id: int = Field(
        ...,
        description="Unique listing ID",
        gt=0,
    )

    name: str = Field(
        ...,
        description="Property name",
        min_length=1,
        max_length=200,
    )

    city: str = Field(
        ...,
        description="City name",
    )

    state: str | None = Field(
        None,
        description="State/province",
    )

    capacity: int = Field(
        ...,
        description="Maximum guest capacity",
        ge=1,
    )

    bedrooms: int = Field(
        ...,
        description="Number of bedrooms",
        ge=0,
    )

    bathrooms: Decimal = Field(
        ...,
        description="Number of bathrooms",
        ge=0,
        decimal_places=1,
    )

    base_price: Decimal = Field(
        ...,
        description="Base nightly rate",
        ge=0,
        decimal_places=2,
    )

    is_available: bool = Field(
        ...,
        description="Current availability status",
    )

    property_type: str = Field(
        ...,
        description="Type of property",
    )

    thumbnail_url: HttpUrl | None = Field(
        None,
        description="URL to primary property image",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 12345,
                "name": "Cozy Downtown Apartment",
                "city": "San Francisco",
                "state": "California",
                "capacity": 4,
                "bedrooms": 2,
                "bathrooms": "1.5",
                "base_price": "150.00",
                "is_available": True,
                "property_type": "apartment",
                "thumbnail_url": "https://example.com/image1.jpg",
            }
        }
    }
