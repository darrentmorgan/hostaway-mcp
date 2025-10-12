# Data Model: Hostaway MCP Server

**Feature Branch**: `001-we-need-to`
**Created**: 2025-10-12
**Status**: Complete

## Overview

This document defines all Pydantic data models for the Hostaway MCP Server. Models are organized by domain (Authentication, Listings, Bookings, Guests, Financial) and include field definitions, validation rules, relationships, and example values.

**Key Design Principles**:
- All models use Pydantic v2 with strict type validation
- Field constraints enforce API requirements (min/max values, regex patterns)
- DateTime fields use timezone-aware datetime objects
- Enums enforce valid values for status fields
- Optional fields have clear defaults or None
- Example values demonstrate real-world usage

---

## 1. Authentication Models

### 1.1 HostawayConfig

Configuration model for OAuth credentials and API settings.

```python
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

class HostawayConfig(BaseSettings):
    """Hostaway API configuration loaded from environment variables.

    Required environment variables:
    - HOSTAWAY_ACCOUNT_ID: OAuth client ID
    - HOSTAWAY_SECRET_KEY: OAuth client secret
    - HOSTAWAY_API_BASE_URL: Base API URL (default: https://api.hostaway.com/v1)
    """

    account_id: str = Field(
        ...,
        description="Hostaway account ID (OAuth client ID)",
        min_length=1,
        alias="HOSTAWAY_ACCOUNT_ID"
    )

    secret_key: SecretStr = Field(
        ...,
        description="Hostaway secret key (OAuth client secret)",
        alias="HOSTAWAY_SECRET_KEY"
    )

    api_base_url: str = Field(
        default="https://api.hostaway.com/v1",
        description="Hostaway API base URL",
        alias="HOSTAWAY_API_BASE_URL"
    )

    rate_limit_ip: int = Field(
        default=15,
        description="IP-based rate limit (requests per 10 seconds)",
        ge=1,
        le=15,
        alias="RATE_LIMIT_IP"
    )

    rate_limit_account: int = Field(
        default=20,
        description="Account-based rate limit (requests per 10 seconds)",
        ge=1,
        le=20,
        alias="RATE_LIMIT_ACCOUNT"
    )

    max_concurrent_requests: int = Field(
        default=10,
        description="Maximum concurrent requests",
        ge=1,
        le=50,
        alias="MAX_CONCURRENT_REQUESTS"
    )

    token_refresh_threshold_days: int = Field(
        default=7,
        description="Days before expiration to refresh token",
        ge=1,
        le=30,
        alias="TOKEN_REFRESH_THRESHOLD_DAYS"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Example usage
config = HostawayConfig(
    HOSTAWAY_ACCOUNT_ID="12345",
    HOSTAWAY_SECRET_KEY="secret_abc123xyz"
)
```

### 1.2 AccessToken

OAuth access token with expiration tracking.

```python
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class AccessToken(BaseModel):
    """OAuth 2.0 access token for Hostaway API authentication.

    Tokens are valid for 24 months from issuance.
    """

    access_token: str = Field(
        ...,
        description="Bearer token for API authentication",
        min_length=20
    )

    token_type: str = Field(
        default="Bearer",
        description="Token type (always 'Bearer' for Hostaway)",
        pattern=r"^Bearer$"
    )

    expires_in: int = Field(
        ...,
        description="Token lifetime in seconds (typically 63072000 = 24 months)",
        ge=1
    )

    issued_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when token was issued (UTC)"
    )

    scope: str = Field(
        default="general",
        description="OAuth scope (Hostaway uses 'general')"
    )

    @property
    def expires_at(self) -> datetime:
        """Calculate token expiration timestamp."""
        return self.issued_at + timedelta(seconds=self.expires_in)

    @property
    def is_expired(self) -> bool:
        """Check if token is currently expired."""
        return datetime.utcnow() >= self.expires_at

    @property
    def days_until_expiration(self) -> int:
        """Calculate days remaining until token expires."""
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)

    def should_refresh(self, threshold_days: int = 7) -> bool:
        """Determine if token should be refreshed.

        Args:
            threshold_days: Refresh if expiring within this many days

        Returns:
            True if token should be refreshed
        """
        return self.days_until_expiration <= threshold_days

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 63072000,
                "issued_at": "2025-10-12T10:30:00Z",
                "scope": "general"
            }
        }

# Example usage
token = AccessToken(
    access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    expires_in=63072000  # 24 months
)
print(f"Token expires in {token.days_until_expiration} days")
print(f"Should refresh: {token.should_refresh(threshold_days=7)}")
```

### 1.3 TokenRefreshRequest

Request model for OAuth token exchange.

```python
from pydantic import BaseModel, Field

class TokenRefreshRequest(BaseModel):
    """OAuth 2.0 token request using Client Credentials Grant.

    Sent as application/x-www-form-urlencoded to POST /v1/accessTokens
    """

    grant_type: str = Field(
        default="client_credentials",
        description="OAuth grant type (always 'client_credentials')",
        pattern=r"^client_credentials$"
    )

    client_id: str = Field(
        ...,
        description="Hostaway account ID",
        min_length=1
    )

    client_secret: str = Field(
        ...,
        description="Hostaway secret key",
        min_length=1
    )

    scope: str = Field(
        default="general",
        description="OAuth scope (Hostaway uses 'general')"
    )

    def to_form_data(self) -> dict[str, str]:
        """Convert to form-encoded data for HTTP request."""
        return {
            "grant_type": self.grant_type,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope
        }

    class Config:
        json_schema_extra = {
            "example": {
                "grant_type": "client_credentials",
                "client_id": "12345",
                "client_secret": "secret_abc123xyz",
                "scope": "general"
            }
        }
```

### 1.4 TokenRefreshResponse

Response model from OAuth token endpoint.

```python
from pydantic import BaseModel, Field

class TokenRefreshResponse(BaseModel):
    """OAuth token response from Hostaway API.

    Returned from POST /v1/accessTokens
    """

    access_token: str = Field(
        ...,
        description="JWT access token",
        min_length=20
    )

    token_type: str = Field(
        ...,
        description="Token type (always 'Bearer')"
    )

    expires_in: int = Field(
        ...,
        description="Token lifetime in seconds",
        ge=1
    )

    scope: str = Field(
        default="general",
        description="OAuth scope"
    )

    def to_access_token(self) -> AccessToken:
        """Convert to AccessToken model."""
        return AccessToken(
            access_token=self.access_token,
            token_type=self.token_type,
            expires_in=self.expires_in,
            scope=self.scope
        )

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 63072000,
                "scope": "general"
            }
        }
```

---

## 2. Listing Models

### 2.1 PricingInfo

Pricing details for a property listing.

```python
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional

class PricingInfo(BaseModel):
    """Pricing information for a property listing."""

    base_price: Decimal = Field(
        ...,
        description="Base nightly rate in USD",
        ge=0,
        decimal_places=2
    )

    currency: str = Field(
        default="USD",
        description="Currency code (ISO 4217)",
        pattern=r"^[A-Z]{3}$"
    )

    weekend_price: Optional[Decimal] = Field(
        None,
        description="Weekend nightly rate (if different)",
        ge=0,
        decimal_places=2
    )

    cleaning_fee: Decimal = Field(
        default=Decimal("0.00"),
        description="One-time cleaning fee",
        ge=0,
        decimal_places=2
    )

    security_deposit: Decimal = Field(
        default=Decimal("0.00"),
        description="Refundable security deposit",
        ge=0,
        decimal_places=2
    )

    extra_guest_fee: Optional[Decimal] = Field(
        None,
        description="Fee per additional guest beyond base capacity",
        ge=0,
        decimal_places=2
    )

    min_stay_nights: int = Field(
        default=1,
        description="Minimum stay in nights",
        ge=1
    )

    class Config:
        json_schema_extra = {
            "example": {
                "base_price": "150.00",
                "currency": "USD",
                "weekend_price": "200.00",
                "cleaning_fee": "75.00",
                "security_deposit": "500.00",
                "extra_guest_fee": "25.00",
                "min_stay_nights": 2
            }
        }
```

### 2.2 AvailabilityInfo

Availability and calendar information for a listing.

```python
from datetime import date
from pydantic import BaseModel, Field
from typing import List, Optional

class AvailabilityInfo(BaseModel):
    """Availability and calendar information for a property."""

    is_available: bool = Field(
        ...,
        description="Whether property is currently available for booking"
    )

    available_from: Optional[date] = Field(
        None,
        description="Date when property becomes available"
    )

    blocked_dates: List[date] = Field(
        default_factory=list,
        description="Dates when property is unavailable"
    )

    booked_dates: List[date] = Field(
        default_factory=list,
        description="Dates with existing reservations"
    )

    calendar_notes: Optional[str] = Field(
        None,
        description="Notes about availability or scheduling",
        max_length=500
    )

    class Config:
        json_schema_extra = {
            "example": {
                "is_available": True,
                "available_from": "2025-10-15",
                "blocked_dates": ["2025-12-24", "2025-12-25", "2025-12-31"],
                "booked_dates": ["2025-11-10", "2025-11-11", "2025-11-12"],
                "calendar_notes": "Holiday dates blocked for owner use"
            }
        }
```

### 2.3 Listing

Complete property listing details.

```python
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict
from decimal import Decimal

class Listing(BaseModel):
    """Complete property listing with all details.

    Represents a rental property in the Hostaway system.
    """

    id: int = Field(
        ...,
        description="Unique listing ID",
        gt=0
    )

    name: str = Field(
        ...,
        description="Property name/title",
        min_length=1,
        max_length=200
    )

    address: str = Field(
        ...,
        description="Full property address",
        min_length=1,
        max_length=500
    )

    city: str = Field(
        ...,
        description="City name",
        min_length=1,
        max_length=100
    )

    state: Optional[str] = Field(
        None,
        description="State/province",
        max_length=100
    )

    country: str = Field(
        ...,
        description="Country name or ISO code",
        min_length=2,
        max_length=100
    )

    postal_code: Optional[str] = Field(
        None,
        description="Postal/ZIP code",
        max_length=20
    )

    latitude: Optional[Decimal] = Field(
        None,
        description="GPS latitude",
        ge=-90,
        le=90,
        decimal_places=6
    )

    longitude: Optional[Decimal] = Field(
        None,
        description="GPS longitude",
        ge=-180,
        le=180,
        decimal_places=6
    )

    description: str = Field(
        ...,
        description="Full property description",
        min_length=1,
        max_length=5000
    )

    capacity: int = Field(
        ...,
        description="Maximum guest capacity",
        ge=1,
        le=50
    )

    bedrooms: int = Field(
        ...,
        description="Number of bedrooms",
        ge=0,
        le=20
    )

    bathrooms: Decimal = Field(
        ...,
        description="Number of bathrooms (0.5 for half bath)",
        ge=0,
        le=20,
        decimal_places=1
    )

    beds: int = Field(
        default=0,
        description="Total number of beds",
        ge=0,
        le=50
    )

    property_type: str = Field(
        ...,
        description="Type of property (apartment, house, villa, etc.)",
        max_length=100
    )

    amenities: List[str] = Field(
        default_factory=list,
        description="List of amenities (WiFi, parking, pool, etc.)"
    )

    pricing: PricingInfo = Field(
        ...,
        description="Pricing information"
    )

    availability: AvailabilityInfo = Field(
        ...,
        description="Availability and calendar info"
    )

    cancellation_policy: str = Field(
        default="moderate",
        description="Cancellation policy type",
        max_length=100
    )

    check_in_time: Optional[str] = Field(
        None,
        description="Check-in time (e.g., '15:00')",
        pattern=r"^\d{2}:\d{2}$"
    )

    check_out_time: Optional[str] = Field(
        None,
        description="Check-out time (e.g., '11:00')",
        pattern=r"^\d{2}:\d{2}$"
    )

    images: List[HttpUrl] = Field(
        default_factory=list,
        description="URLs to property images"
    )

    channel_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="External platform listing IDs (airbnb, vrbo, booking_com)"
    )

    is_active: bool = Field(
        default=True,
        description="Whether listing is active and bookable"
    )

    house_rules: Optional[str] = Field(
        None,
        description="Property-specific rules for guests",
        max_length=2000
    )

    class Config:
        json_schema_extra = {
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
                    "cleaning_fee": "75.00"
                },
                "availability": {
                    "is_available": True
                },
                "cancellation_policy": "moderate",
                "check_in_time": "15:00",
                "check_out_time": "11:00",
                "images": [
                    "https://example.com/image1.jpg",
                    "https://example.com/image2.jpg"
                ],
                "channel_ids": {
                    "airbnb": "abc123",
                    "vrbo": "xyz789"
                },
                "is_active": True,
                "house_rules": "No smoking, no pets, quiet hours after 10pm"
            }
        }
```

### 2.4 ListingSummary

Abbreviated listing information for list views.

```python
from pydantic import BaseModel, Field, HttpUrl
from decimal import Decimal
from typing import Optional

class ListingSummary(BaseModel):
    """Abbreviated listing information for list/search results.

    Used when returning multiple properties to reduce payload size.
    """

    id: int = Field(
        ...,
        description="Unique listing ID",
        gt=0
    )

    name: str = Field(
        ...,
        description="Property name",
        min_length=1,
        max_length=200
    )

    city: str = Field(
        ...,
        description="City name"
    )

    state: Optional[str] = Field(
        None,
        description="State/province"
    )

    capacity: int = Field(
        ...,
        description="Maximum guest capacity",
        ge=1
    )

    bedrooms: int = Field(
        ...,
        description="Number of bedrooms",
        ge=0
    )

    bathrooms: Decimal = Field(
        ...,
        description="Number of bathrooms",
        ge=0,
        decimal_places=1
    )

    base_price: Decimal = Field(
        ...,
        description="Base nightly rate",
        ge=0,
        decimal_places=2
    )

    is_available: bool = Field(
        ...,
        description="Current availability status"
    )

    property_type: str = Field(
        ...,
        description="Type of property"
    )

    thumbnail_url: Optional[HttpUrl] = Field(
        None,
        description="URL to primary property image"
    )

    class Config:
        json_schema_extra = {
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
                "thumbnail_url": "https://example.com/image1.jpg"
            }
        }
```

---

## 3. Booking Models

### 3.1 BookingStatus

Enumeration of valid booking statuses.

```python
from enum import Enum

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
        return self in (
            BookingStatus.CONFIRMED,
            BookingStatus.PENDING
        )

    def is_finalized(self) -> bool:
        """Check if booking status is final (no further changes)."""
        return self in (
            BookingStatus.CANCELLED,
            BookingStatus.COMPLETED,
            BookingStatus.DECLINED,
            BookingStatus.EXPIRED
        )
```

### 3.2 PaymentStatus

Enumeration of payment statuses.

```python
from enum import Enum

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
```

### 3.3 PaymentInfo

Payment details for a booking.

```python
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from datetime import datetime

class PaymentInfo(BaseModel):
    """Payment information for a booking/reservation."""

    total_price: Decimal = Field(
        ...,
        description="Total booking price",
        ge=0,
        decimal_places=2
    )

    currency: str = Field(
        default="USD",
        description="Currency code (ISO 4217)",
        pattern=r"^[A-Z]{3}$"
    )

    amount_paid: Decimal = Field(
        default=Decimal("0.00"),
        description="Amount already paid",
        ge=0,
        decimal_places=2
    )

    amount_due: Decimal = Field(
        default=Decimal("0.00"),
        description="Remaining amount due",
        ge=0,
        decimal_places=2
    )

    payment_status: PaymentStatus = Field(
        ...,
        description="Current payment status"
    )

    payment_method: Optional[str] = Field(
        None,
        description="Payment method (credit_card, bank_transfer, etc.)",
        max_length=50
    )

    paid_at: Optional[datetime] = Field(
        None,
        description="Timestamp when payment was completed (UTC)"
    )

    @property
    def is_fully_paid(self) -> bool:
        """Check if booking is fully paid."""
        return self.amount_paid >= self.total_price

    class Config:
        json_schema_extra = {
            "example": {
                "total_price": "525.00",
                "currency": "USD",
                "amount_paid": "525.00",
                "amount_due": "0.00",
                "payment_status": "paid",
                "payment_method": "credit_card",
                "paid_at": "2025-10-12T10:30:00Z"
            }
        }
```

### 3.4 Booking

Complete booking/reservation details.

```python
from pydantic import BaseModel, Field, EmailStr
from datetime import date, datetime
from typing import Optional
from decimal import Decimal

class Booking(BaseModel):
    """Complete booking/reservation with guest and payment information.

    Represents a guest reservation for a property listing.
    """

    id: int = Field(
        ...,
        description="Unique booking ID",
        gt=0
    )

    listing_id: int = Field(
        ...,
        description="ID of the booked property",
        gt=0
    )

    listing_name: Optional[str] = Field(
        None,
        description="Name of the booked property",
        max_length=200
    )

    guest_id: int = Field(
        ...,
        description="ID of the guest making the reservation",
        gt=0
    )

    guest_name: str = Field(
        ...,
        description="Full name of guest",
        min_length=1,
        max_length=200
    )

    guest_email: EmailStr = Field(
        ...,
        description="Guest email address"
    )

    guest_phone: Optional[str] = Field(
        None,
        description="Guest phone number",
        max_length=50
    )

    check_in: date = Field(
        ...,
        description="Check-in date"
    )

    check_out: date = Field(
        ...,
        description="Check-out date"
    )

    num_guests: int = Field(
        ...,
        description="Number of guests",
        ge=1,
        le=50,
        alias="guests"
    )

    num_adults: Optional[int] = Field(
        None,
        description="Number of adult guests",
        ge=0
    )

    num_children: Optional[int] = Field(
        None,
        description="Number of child guests",
        ge=0
    )

    num_nights: int = Field(
        ...,
        description="Number of nights for stay",
        ge=1
    )

    status: BookingStatus = Field(
        ...,
        description="Current booking status"
    )

    payment: PaymentInfo = Field(
        ...,
        description="Payment information"
    )

    booking_source: str = Field(
        ...,
        description="Booking channel (direct, airbnb, vrbo, booking_com)",
        max_length=100
    )

    confirmation_code: Optional[str] = Field(
        None,
        description="Booking confirmation code",
        max_length=50
    )

    created_at: datetime = Field(
        ...,
        description="Booking creation timestamp (UTC)"
    )

    updated_at: Optional[datetime] = Field(
        None,
        description="Last update timestamp (UTC)"
    )

    special_requests: Optional[str] = Field(
        None,
        description="Guest special requests or notes",
        max_length=1000
    )

    @property
    def is_upcoming(self) -> bool:
        """Check if check-in date is in the future."""
        from datetime import date as date_module
        return self.check_in > date_module.today()

    @property
    def is_current(self) -> bool:
        """Check if guest is currently checked in."""
        from datetime import date as date_module
        today = date_module.today()
        return self.check_in <= today <= self.check_out

    @property
    def is_past(self) -> bool:
        """Check if check-out date has passed."""
        from datetime import date as date_module
        return self.check_out < date_module.today()

    class Config:
        json_schema_extra = {
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
                "guests": 2,
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
                    "payment_method": "credit_card"
                },
                "booking_source": "airbnb",
                "confirmation_code": "ABCD1234",
                "created_at": "2025-10-01T14:30:00Z",
                "updated_at": "2025-10-01T14:30:00Z",
                "special_requests": "Early check-in if possible"
            }
        }
```

### 3.5 BookingSearchFilters

Search filters for booking queries.

```python
from pydantic import BaseModel, Field, EmailStr
from datetime import date
from typing import Optional, List

class BookingSearchFilters(BaseModel):
    """Filters for searching bookings/reservations.

    All filters are optional and combined with AND logic.
    """

    listing_id: Optional[int] = Field(
        None,
        description="Filter by specific property",
        gt=0
    )

    check_in_from: Optional[date] = Field(
        None,
        description="Filter bookings with check-in on or after this date"
    )

    check_in_to: Optional[date] = Field(
        None,
        description="Filter bookings with check-in on or before this date"
    )

    check_out_from: Optional[date] = Field(
        None,
        description="Filter bookings with check-out on or after this date"
    )

    check_out_to: Optional[date] = Field(
        None,
        description="Filter bookings with check-out on or before this date"
    )

    status: Optional[List[BookingStatus]] = Field(
        None,
        description="Filter by booking status (multiple allowed)"
    )

    guest_email: Optional[EmailStr] = Field(
        None,
        description="Filter by guest email address"
    )

    booking_source: Optional[str] = Field(
        None,
        description="Filter by booking channel (airbnb, vrbo, etc.)",
        max_length=100
    )

    min_guests: Optional[int] = Field(
        None,
        description="Filter bookings with at least this many guests",
        ge=1
    )

    max_guests: Optional[int] = Field(
        None,
        description="Filter bookings with at most this many guests",
        ge=1
    )

    limit: int = Field(
        default=100,
        description="Maximum results to return",
        ge=1,
        le=1000
    )

    offset: int = Field(
        default=0,
        description="Number of results to skip (for pagination)",
        ge=0
    )

    class Config:
        json_schema_extra = {
            "example": {
                "listing_id": 12345,
                "check_in_from": "2025-11-01",
                "check_in_to": "2025-11-30",
                "status": ["confirmed", "pending"],
                "min_guests": 2,
                "limit": 50,
                "offset": 0
            }
        }
```

---

## 4. Guest Models

### 4.1 MessageChannel

Enumeration of communication channels.

```python
from enum import Enum

class MessageChannel(str, Enum):
    """Communication channels for guest messaging."""

    EMAIL = "email"
    SMS = "sms"
    AIRBNB = "airbnb"
    BOOKING_COM = "booking_com"
    VRBO = "vrbo"
    DIRECT = "direct"

    def is_platform_messaging(self) -> bool:
        """Check if channel is platform-specific (vs direct)."""
        return self in (
            MessageChannel.AIRBNB,
            MessageChannel.BOOKING_COM,
            MessageChannel.VRBO
        )
```

### 4.2 MessageDeliveryStatus

Enumeration of message delivery statuses.

```python
from enum import Enum

class MessageDeliveryStatus(str, Enum):
    """Message delivery status."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"

    def is_successful(self) -> bool:
        """Check if message was successfully delivered."""
        return self in (
            MessageDeliveryStatus.SENT,
            MessageDeliveryStatus.DELIVERED,
            MessageDeliveryStatus.READ
        )
```

### 4.3 Message

Guest message/communication.

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Message(BaseModel):
    """Guest communication message.

    Represents a message sent to or received from a guest.
    """

    id: Optional[int] = Field(
        None,
        description="Message ID (null for unsent messages)",
        gt=0
    )

    booking_id: int = Field(
        ...,
        description="Associated booking ID",
        gt=0
    )

    guest_id: int = Field(
        ...,
        description="Recipient/sender guest ID",
        gt=0
    )

    channel: MessageChannel = Field(
        ...,
        description="Communication channel"
    )

    subject: Optional[str] = Field(
        None,
        description="Message subject (for email)",
        max_length=200
    )

    content: str = Field(
        ...,
        description="Message body/content",
        min_length=1,
        max_length=5000
    )

    sender: str = Field(
        default="host",
        description="Sender identifier (host or guest)"
    )

    delivery_status: MessageDeliveryStatus = Field(
        default=MessageDeliveryStatus.PENDING,
        description="Current delivery status"
    )

    sent_at: Optional[datetime] = Field(
        None,
        description="Timestamp when message was sent (UTC)"
    )

    delivered_at: Optional[datetime] = Field(
        None,
        description="Timestamp when message was delivered (UTC)"
    )

    read_at: Optional[datetime] = Field(
        None,
        description="Timestamp when message was read (UTC)"
    )

    error_message: Optional[str] = Field(
        None,
        description="Error details if delivery failed",
        max_length=500
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": 11111,
                "booking_id": 67890,
                "guest_id": 54321,
                "channel": "email",
                "subject": "Check-in Instructions",
                "content": "Welcome! Here are your check-in instructions...",
                "sender": "host",
                "delivery_status": "sent",
                "sent_at": "2025-11-09T10:00:00Z"
            }
        }
```

### 4.4 Guest

Guest profile and preferences.

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class Guest(BaseModel):
    """Guest profile with contact information and preferences.

    Represents a guest who has made or is making a booking.
    """

    id: int = Field(
        ...,
        description="Unique guest ID",
        gt=0
    )

    first_name: str = Field(
        ...,
        description="Guest first name",
        min_length=1,
        max_length=100
    )

    last_name: str = Field(
        ...,
        description="Guest last name",
        min_length=1,
        max_length=100
    )

    email: EmailStr = Field(
        ...,
        description="Primary email address"
    )

    phone: Optional[str] = Field(
        None,
        description="Phone number",
        max_length=50
    )

    language: str = Field(
        default="en",
        description="Preferred language (ISO 639-1 code)",
        pattern=r"^[a-z]{2}$"
    )

    country: Optional[str] = Field(
        None,
        description="Country of residence",
        max_length=100
    )

    city: Optional[str] = Field(
        None,
        description="City of residence",
        max_length=100
    )

    total_bookings: int = Field(
        default=0,
        description="Total number of bookings made",
        ge=0
    )

    preferred_channels: List[MessageChannel] = Field(
        default_factory=lambda: [MessageChannel.EMAIL],
        description="Preferred communication channels"
    )

    notes: Optional[str] = Field(
        None,
        description="Internal notes about guest",
        max_length=1000
    )

    created_at: datetime = Field(
        ...,
        description="Guest profile creation timestamp (UTC)"
    )

    last_booking_at: Optional[datetime] = Field(
        None,
        description="Timestamp of most recent booking (UTC)"
    )

    @property
    def full_name(self) -> str:
        """Get guest's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_repeat_guest(self) -> bool:
        """Check if guest has made multiple bookings."""
        return self.total_bookings > 1

    class Config:
        json_schema_extra = {
            "example": {
                "id": 54321,
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@example.com",
                "phone": "+1-555-123-4567",
                "language": "en",
                "country": "USA",
                "city": "New York",
                "total_bookings": 3,
                "preferred_channels": ["email", "sms"],
                "notes": "VIP guest - prefers early check-in",
                "created_at": "2024-01-15T10:00:00Z",
                "last_booking_at": "2025-10-01T14:30:00Z"
            }
        }
```

---

## 5. Financial Models

### 5.1 FinancialReportPeriod

Enumeration of reporting periods.

```python
from enum import Enum

class FinancialReportPeriod(str, Enum):
    """Financial reporting period types."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"
```

### 5.2 RevenueBreakdown

Revenue breakdown by source.

```python
from pydantic import BaseModel, Field
from decimal import Decimal

class RevenueBreakdown(BaseModel):
    """Revenue breakdown by booking source/channel."""

    total_revenue: Decimal = Field(
        ...,
        description="Total revenue for period",
        ge=0,
        decimal_places=2
    )

    direct_bookings: Decimal = Field(
        default=Decimal("0.00"),
        description="Revenue from direct bookings",
        ge=0,
        decimal_places=2
    )

    airbnb: Decimal = Field(
        default=Decimal("0.00"),
        description="Revenue from Airbnb",
        ge=0,
        decimal_places=2
    )

    vrbo: Decimal = Field(
        default=Decimal("0.00"),
        description="Revenue from VRBO",
        ge=0,
        decimal_places=2
    )

    booking_com: Decimal = Field(
        default=Decimal("0.00"),
        description="Revenue from Booking.com",
        ge=0,
        decimal_places=2
    )

    other: Decimal = Field(
        default=Decimal("0.00"),
        description="Revenue from other sources",
        ge=0,
        decimal_places=2
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_revenue": "12500.00",
                "direct_bookings": "3000.00",
                "airbnb": "6000.00",
                "vrbo": "2500.00",
                "booking_com": "1000.00",
                "other": "0.00"
            }
        }
```

### 5.3 ExpenseBreakdown

Expense breakdown by category.

```python
from pydantic import BaseModel, Field
from decimal import Decimal

class ExpenseBreakdown(BaseModel):
    """Expense breakdown by category."""

    total_expenses: Decimal = Field(
        ...,
        description="Total expenses for period",
        ge=0,
        decimal_places=2
    )

    cleaning: Decimal = Field(
        default=Decimal("0.00"),
        description="Cleaning service expenses",
        ge=0,
        decimal_places=2
    )

    maintenance: Decimal = Field(
        default=Decimal("0.00"),
        description="Maintenance and repairs",
        ge=0,
        decimal_places=2
    )

    utilities: Decimal = Field(
        default=Decimal("0.00"),
        description="Utilities (water, electricity, internet)",
        ge=0,
        decimal_places=2
    )

    platform_fees: Decimal = Field(
        default=Decimal("0.00"),
        description="Platform commission fees",
        ge=0,
        decimal_places=2
    )

    supplies: Decimal = Field(
        default=Decimal("0.00"),
        description="Supplies and amenities",
        ge=0,
        decimal_places=2
    )

    other: Decimal = Field(
        default=Decimal("0.00"),
        description="Other expenses",
        ge=0,
        decimal_places=2
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_expenses": "3250.00",
                "cleaning": "1200.00",
                "maintenance": "500.00",
                "utilities": "300.00",
                "platform_fees": "1000.00",
                "supplies": "200.00",
                "other": "50.00"
            }
        }
```

### 5.4 FinancialReport

Comprehensive financial report.

```python
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal
from typing import Optional

class FinancialReport(BaseModel):
    """Financial report with revenue, expenses, and profitability metrics.

    Aggregates financial data for a specific period and optionally for a specific property.
    """

    period_start: date = Field(
        ...,
        description="Report period start date"
    )

    period_end: date = Field(
        ...,
        description="Report period end date"
    )

    period_type: FinancialReportPeriod = Field(
        ...,
        description="Type of reporting period"
    )

    listing_id: Optional[int] = Field(
        None,
        description="Specific listing ID (null for all properties)",
        gt=0
    )

    listing_name: Optional[str] = Field(
        None,
        description="Listing name (if listing_id specified)",
        max_length=200
    )

    revenue: RevenueBreakdown = Field(
        ...,
        description="Revenue breakdown"
    )

    expenses: ExpenseBreakdown = Field(
        ...,
        description="Expense breakdown"
    )

    net_income: Decimal = Field(
        ...,
        description="Net income (revenue - expenses)",
        decimal_places=2
    )

    total_bookings: int = Field(
        ...,
        description="Number of bookings in period",
        ge=0
    )

    total_nights_booked: int = Field(
        ...,
        description="Total nights booked in period",
        ge=0
    )

    average_daily_rate: Decimal = Field(
        ...,
        description="Average nightly rate for period",
        ge=0,
        decimal_places=2
    )

    occupancy_rate: Decimal = Field(
        ...,
        description="Occupancy rate as percentage (0-100)",
        ge=0,
        le=100,
        decimal_places=2
    )

    currency: str = Field(
        default="USD",
        description="Currency code (ISO 4217)",
        pattern=r"^[A-Z]{3}$"
    )

    @property
    def profit_margin(self) -> Decimal:
        """Calculate profit margin as percentage."""
        if self.revenue.total_revenue == 0:
            return Decimal("0.00")
        return (self.net_income / self.revenue.total_revenue) * 100

    class Config:
        json_schema_extra = {
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
                    "booking_com": "1000.00"
                },
                "expenses": {
                    "total_expenses": "3250.00",
                    "cleaning": "1200.00",
                    "platform_fees": "1000.00"
                },
                "net_income": "9250.00",
                "total_bookings": 15,
                "total_nights_booked": 75,
                "average_daily_rate": "166.67",
                "occupancy_rate": "80.65",
                "currency": "USD"
            }
        }
```

---

## 6. Model Relationships

### Entity Relationship Diagram

```
┌──────────────────┐
│  HostawayConfig  │
│  (Singleton)     │
└──────────────────┘
         │
         │ configures
         ▼
┌──────────────────┐
│   AccessToken    │
│  (Singleton)     │
└──────────────────┘
         │
         │ authenticates
         ▼
┌──────────────────┐       ┌──────────────────┐
│     Listing      │◄──────┤ ListingSummary   │
│   (1:1 full)     │       │ (abbreviated)    │
└──────────────────┘       └──────────────────┘
         │
         │ has
         ▼
┌──────────────────┐
│  PricingInfo     │
│  AvailabilityInfo│
└──────────────────┘
         │
         │ referenced by
         ▼
┌──────────────────┐       ┌──────────────────┐
│     Booking      │──────►│   PaymentInfo    │
│                  │       │                  │
└──────────────────┘       └──────────────────┘
         │
         │ references
         ▼
┌──────────────────┐       ┌──────────────────┐
│      Guest       │◄──────┤     Message      │
│                  │       │                  │
└──────────────────┘       └──────────────────┘
         │
         │ generates
         ▼
┌──────────────────┐
│ FinancialReport  │
│                  │
└──────────────────┘
         │
         │ aggregates
         ▼
┌──────────────────┐
│ RevenueBreakdown │
│ ExpenseBreakdown │
└──────────────────┘
```

### Key Relationships

1. **HostawayConfig → AccessToken**: Configuration provides credentials for token generation
2. **Listing → Booking**: Bookings reference a specific listing (listing_id)
3. **Guest → Booking**: Bookings reference a specific guest (guest_id)
4. **Booking → Message**: Messages are associated with a booking and guest
5. **Booking → PaymentInfo**: Each booking has payment details
6. **Listing → FinancialReport**: Reports can be property-specific or aggregated
7. **Listing → PricingInfo/AvailabilityInfo**: Listings embed pricing and availability

---

## Summary

This data model document defines **19 core Pydantic models** organized into 5 domains:

| Domain | Models | Purpose |
|--------|--------|---------|
| **Authentication** | HostawayConfig, AccessToken, TokenRefreshRequest, TokenRefreshResponse | OAuth credential management |
| **Listings** | Listing, ListingSummary, PricingInfo, AvailabilityInfo | Property data and availability |
| **Bookings** | Booking, BookingSearchFilters, PaymentInfo, BookingStatus, PaymentStatus | Reservation management |
| **Guests** | Guest, Message, MessageChannel, MessageDeliveryStatus | Guest profiles and communication |
| **Financial** | FinancialReport, RevenueBreakdown, ExpenseBreakdown, FinancialReportPeriod | Revenue and expense tracking |

**Key Benefits**:
- Full type safety with mypy strict compliance
- Automatic validation of API data
- Clear documentation through field descriptions
- Example values for every model
- Helper methods for common operations
- Enum types for constrained values

**Next Steps**:
1. Implement models in `src/models/` directory
2. Use models in API client (`src/services/hostaway_client.py`)
3. Integrate models into MCP tools
4. Add comprehensive unit tests
5. Update API contracts to reference these models
