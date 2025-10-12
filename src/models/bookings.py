"""Booking models for Hostaway reservation management.

This module provides Pydantic models for bookings/reservations, including
payment information, search filters, and booking status enums.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class BookingStatus(str, Enum):
    """Valid booking/reservation statuses in Hostaway."""

    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    INQUIRY = "inquiry"
    DECLINED = "declined"
    EXPIRED = "expired"

    def is_active(self) -> bool:
        """Check if booking is currently active."""
        return self in (BookingStatus.CONFIRMED, BookingStatus.PENDING)

    def is_finalized(self) -> bool:
        """Check if booking status is final (no further changes)."""
        return self in (
            BookingStatus.CANCELLED,
            BookingStatus.COMPLETED,
            BookingStatus.DECLINED,
            BookingStatus.EXPIRED,
        )


class PaymentStatus(str, Enum):
    """Payment status for bookings."""

    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    PENDING = "pending"
    REFUNDED = "refunded"
    FAILED = "failed"

    def is_complete(self) -> bool:
        """Check if payment is fully complete."""
        return self == PaymentStatus.PAID


class PaymentInfo(BaseModel):
    """Payment information for a booking/reservation."""

    total_price: Decimal = Field(
        ...,
        description="Total booking price",
        ge=0,
        decimal_places=2,
    )

    currency: str = Field(
        default="USD",
        description="Currency code (ISO 4217)",
        pattern=r"^[A-Z]{3}$",
    )

    amount_paid: Decimal = Field(
        default=Decimal("0.00"),
        description="Amount already paid",
        ge=0,
        decimal_places=2,
    )

    amount_due: Decimal = Field(
        default=Decimal("0.00"),
        description="Remaining amount due",
        ge=0,
        decimal_places=2,
    )

    payment_status: PaymentStatus = Field(
        ...,
        description="Current payment status",
    )

    payment_method: Optional[str] = Field(
        None,
        description="Payment method (credit_card, bank_transfer, etc.)",
        max_length=50,
    )

    paid_at: Optional[datetime] = Field(
        None,
        description="Timestamp when payment was completed (UTC)",
    )

    @property
    def is_fully_paid(self) -> bool:
        """Check if booking is fully paid."""
        return self.amount_paid >= self.total_price

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_price": "525.00",
                "currency": "USD",
                "amount_paid": "525.00",
                "amount_due": "0.00",
                "payment_status": "paid",
                "payment_method": "credit_card",
                "paid_at": "2025-10-12T10:30:00Z",
            }
        }
    }


class Booking(BaseModel):
    """Complete booking/reservation with guest and payment information.

    Represents a guest reservation for a property listing.
    """

    id: int = Field(
        ...,
        description="Unique booking ID",
        gt=0,
    )

    listing_id: int = Field(
        ...,
        description="ID of the booked property",
        gt=0,
    )

    listing_name: Optional[str] = Field(
        None,
        description="Name of the booked property",
        max_length=200,
    )

    guest_id: int = Field(
        ...,
        description="ID of the guest making the reservation",
        gt=0,
    )

    guest_name: str = Field(
        ...,
        description="Full name of guest",
        min_length=1,
        max_length=200,
    )

    guest_email: EmailStr = Field(
        ...,
        description="Guest email address",
    )

    guest_phone: Optional[str] = Field(
        None,
        description="Guest phone number",
        max_length=50,
    )

    check_in: date = Field(
        ...,
        description="Check-in date",
    )

    check_out: date = Field(
        ...,
        description="Check-out date",
    )

    num_guests: int = Field(
        ...,
        description="Number of guests",
        ge=1,
        le=50,
    )

    num_adults: Optional[int] = Field(
        None,
        description="Number of adult guests",
        ge=0,
    )

    num_children: Optional[int] = Field(
        None,
        description="Number of child guests",
        ge=0,
    )

    num_nights: int = Field(
        ...,
        description="Number of nights for stay",
        ge=1,
    )

    status: BookingStatus = Field(
        ...,
        description="Current booking status",
    )

    payment: PaymentInfo = Field(
        ...,
        description="Payment information",
    )

    booking_source: str = Field(
        ...,
        description="Booking channel (direct, airbnb, vrbo, booking_com)",
        max_length=100,
    )

    confirmation_code: Optional[str] = Field(
        None,
        description="Booking confirmation code",
        max_length=50,
    )

    created_at: datetime = Field(
        ...,
        description="Booking creation timestamp (UTC)",
    )

    updated_at: Optional[datetime] = Field(
        None,
        description="Last update timestamp (UTC)",
    )

    special_requests: Optional[str] = Field(
        None,
        description="Guest special requests or notes",
        max_length=1000,
    )

    @property
    def is_upcoming(self) -> bool:
        """Check if check-in date is in the future."""
        return self.check_in > date.today()

    @property
    def is_current(self) -> bool:
        """Check if guest is currently checked in."""
        today = date.today()
        return self.check_in <= today <= self.check_out

    @property
    def is_past(self) -> bool:
        """Check if check-out date has passed."""
        return self.check_out < date.today()

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 67890,
                "listing_id": 12345,
                "listing_name": "Cozy Downtown Apartment",
                "guest_id": 54321,
                "guest_name": "John Smith",
                "guest_email": "john.smith@example.com",
                "guest_phone": "+1-555-123-4567",
                "check_in": "2025-11-10",
                "check_out": "2025-11-13",
                "num_guests": 2,
                "num_adults": 2,
                "num_children": 0,
                "num_nights": 3,
                "status": "confirmed",
                "payment": {
                    "total_price": "525.00",
                    "currency": "USD",
                    "amount_paid": "525.00",
                    "amount_due": "0.00",
                    "payment_status": "paid",
                    "payment_method": "credit_card",
                },
                "booking_source": "airbnb",
                "confirmation_code": "ABCD1234",
                "created_at": "2025-10-01T14:30:00Z",
                "updated_at": "2025-10-01T14:30:00Z",
                "special_requests": "Early check-in if possible",
            }
        }
    }


class BookingSearchFilters(BaseModel):
    """Filters for searching bookings/reservations.

    All filters are optional and combined with AND logic.
    """

    listing_id: Optional[int] = Field(
        None,
        description="Filter by specific property",
        gt=0,
    )

    check_in_from: Optional[date] = Field(
        None,
        description="Filter bookings with check-in on or after this date",
    )

    check_in_to: Optional[date] = Field(
        None,
        description="Filter bookings with check-in on or before this date",
    )

    check_out_from: Optional[date] = Field(
        None,
        description="Filter bookings with check-out on or after this date",
    )

    check_out_to: Optional[date] = Field(
        None,
        description="Filter bookings with check-out on or before this date",
    )

    status: Optional[List[BookingStatus]] = Field(
        None,
        description="Filter by booking status (multiple allowed)",
    )

    guest_email: Optional[EmailStr] = Field(
        None,
        description="Filter by guest email address",
    )

    booking_source: Optional[str] = Field(
        None,
        description="Filter by booking channel (airbnb, vrbo, etc.)",
        max_length=100,
    )

    min_guests: Optional[int] = Field(
        None,
        description="Filter bookings with at least this many guests",
        ge=1,
    )

    max_guests: Optional[int] = Field(
        None,
        description="Filter bookings with at most this many guests",
        ge=1,
    )

    limit: int = Field(
        default=100,
        description="Maximum results to return",
        ge=1,
        le=1000,
    )

    offset: int = Field(
        default=0,
        description="Number of results to skip (for pagination)",
        ge=0,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "listing_id": 12345,
                "check_in_from": "2025-11-01",
                "check_in_to": "2025-11-30",
                "status": ["confirmed", "pending"],
                "min_guests": 2,
                "limit": 50,
                "offset": 0,
            }
        }
    }
