"""Unit tests for summarized response models.

Tests SummarizedListing and SummarizedBooking Pydantic models for:
- Valid model creation
- Field validation (bedrooms >= 0, totalPrice >= 0)
- ISO 8601 date validation for SummarizedBooking
- camelCase/snake_case field alias support
"""

import pytest
from pydantic import ValidationError

from src.models.summarized import SummarizedBooking, SummarizedListing


class TestSummarizedListing:
    """Test cases for SummarizedListing model."""

    def test_valid_listing_creation(self):
        """Test creating a valid summarized listing."""
        listing = SummarizedListing(
            id=12345,
            name="Luxury Villa in Seminyak",
            city="Seminyak",
            country="Indonesia",
            bedrooms=3,
            status="Available",
        )

        assert listing.id == 12345
        assert listing.name == "Luxury Villa in Seminyak"
        assert listing.city == "Seminyak"
        assert listing.country == "Indonesia"
        assert listing.bedrooms == 3
        assert listing.status == "Available"

    def test_listing_with_null_optional_fields(self):
        """Test listing creation with null city and country."""
        listing = SummarizedListing(
            id=1,
            name="Test Property",
            city=None,
            country=None,
            bedrooms=2,
            status="Inactive",
        )

        assert listing.city is None
        assert listing.country is None
        assert listing.bedrooms == 2

    def test_listing_missing_optional_fields(self):
        """Test listing creation without optional fields."""
        listing = SummarizedListing(id=1, name="Test", bedrooms=1, status="Available")

        assert listing.city is None
        assert listing.country is None

    def test_listing_invalid_bedrooms_negative(self):
        """Test that negative bedrooms raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizedListing(
                id=1,
                name="Test",
                bedrooms=-1,
                status="Available",  # Invalid
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("bedrooms",) for e in errors)

    def test_listing_zero_bedrooms_valid(self):
        """Test that zero bedrooms is allowed (e.g., studio)."""
        listing = SummarizedListing(id=1, name="Studio", bedrooms=0, status="Available")

        assert listing.bedrooms == 0

    def test_listing_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizedListing(id=1, name="Test")  # Missing bedrooms and status

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("bedrooms",) for e in errors)
        assert any(e["loc"] == ("status",) for e in errors)

    def test_listing_json_serialization(self):
        """Test listing can be serialized to JSON."""
        listing = SummarizedListing(
            id=1, name="Test", city="City", country="Country", bedrooms=2, status="Available"
        )

        json_data = listing.model_dump()

        assert json_data["id"] == 1
        assert json_data["name"] == "Test"
        assert json_data["city"] == "City"
        assert json_data["country"] == "Country"
        assert json_data["bedrooms"] == 2
        assert json_data["status"] == "Available"


class TestSummarizedBooking:
    """Test cases for SummarizedBooking model."""

    def test_valid_booking_creation_camelcase(self):
        """Test creating a valid booking with camelCase fields."""
        booking = SummarizedBooking(
            id=67890,
            guestName="John Doe",
            checkIn="2025-11-15",
            checkOut="2025-11-22",
            listingId=12345,
            status="confirmed",
            totalPrice=2500.00,
        )

        assert booking.id == 67890
        assert booking.guestName == "John Doe"
        assert booking.checkIn == "2025-11-15"
        assert booking.checkOut == "2025-11-22"
        assert booking.listingId == 12345
        assert booking.status == "confirmed"
        assert booking.totalPrice == 2500.00

    def test_valid_booking_creation_snake_case(self):
        """Test creating a valid booking with snake_case fields (alias support)."""
        booking = SummarizedBooking(
            id=67890,
            guest_name="Jane Smith",
            check_in="2025-12-01",
            check_out="2025-12-10",
            listing_id=12346,
            status="pending",
            total_price=3500.50,
        )

        assert booking.id == 67890
        assert booking.guestName == "Jane Smith"  # Normalized to camelCase
        assert booking.checkIn == "2025-12-01"
        assert booking.checkOut == "2025-12-10"
        assert booking.listingId == 12346
        assert booking.status == "pending"
        assert booking.totalPrice == 3500.50

    def test_booking_invalid_date_format_wrong_separator(self):
        """Test that invalid ISO 8601 date format raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizedBooking(
                id=1,
                guestName="Test",
                checkIn="2025/11/15",  # Wrong separator
                checkOut="2025-11-22",
                listingId=1,
                status="confirmed",
                totalPrice=100.0,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("checkIn",) for e in errors)
        assert "Invalid ISO 8601 date format" in str(exc_info.value)

    def test_booking_valid_date_format_without_leading_zeros(self):
        """Test that date without leading zeros is accepted by datetime.strptime."""
        # Python's datetime.strptime accepts dates without leading zeros
        booking = SummarizedBooking(
            id=1,
            guestName="Test",
            checkIn="2025-1-5",  # Valid - Python accepts this
            checkOut="2025-11-22",
            listingId=1,
            status="confirmed",
            totalPrice=100.0,
        )

        assert booking.checkIn == "2025-1-5"  # Preserved as-is

    def test_booking_invalid_date_format_with_time(self):
        """Test that date with time component raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizedBooking(
                id=1,
                guestName="Test",
                checkIn="2025-11-15T14:30:00",  # Includes time
                checkOut="2025-11-22",
                listingId=1,
                status="confirmed",
                totalPrice=100.0,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("checkIn",) for e in errors)

    def test_booking_invalid_total_price_negative(self):
        """Test that negative totalPrice raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizedBooking(
                id=1,
                guestName="Test",
                checkIn="2025-11-15",
                checkOut="2025-11-22",
                listingId=1,
                status="confirmed",
                totalPrice=-100.0,  # Invalid
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("totalPrice",) for e in errors)

    def test_booking_zero_total_price_valid(self):
        """Test that zero totalPrice is allowed (e.g., free stays, comped)."""
        booking = SummarizedBooking(
            id=1,
            guestName="Test",
            checkIn="2025-11-15",
            checkOut="2025-11-22",
            listingId=1,
            status="confirmed",
            totalPrice=0.0,
        )

        assert booking.totalPrice == 0.0

    def test_booking_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            SummarizedBooking(
                id=1, guestName="Test"
            )  # Missing dates, listingId, status, totalPrice

        errors = exc_info.value.errors()
        assert len(errors) == 5  # checkIn, checkOut, listingId, status, totalPrice

    def test_booking_json_serialization(self):
        """Test booking can be serialized to JSON."""
        booking = SummarizedBooking(
            id=1,
            guestName="Test Guest",
            checkIn="2025-11-15",
            checkOut="2025-11-22",
            listingId=123,
            status="confirmed",
            totalPrice=1500.0,
        )

        json_data = booking.model_dump()

        assert json_data["id"] == 1
        assert json_data["guestName"] == "Test Guest"
        assert json_data["checkIn"] == "2025-11-15"
        assert json_data["checkOut"] == "2025-11-22"
        assert json_data["listingId"] == 123
        assert json_data["status"] == "confirmed"
        assert json_data["totalPrice"] == 1500.0

    def test_booking_valid_edge_date_formats(self):
        """Test valid edge date cases (leap year, month boundaries)."""
        # Leap year date
        booking1 = SummarizedBooking(
            id=1,
            guestName="Test",
            checkIn="2024-02-29",  # Leap year
            checkOut="2024-03-01",
            listingId=1,
            status="confirmed",
            totalPrice=100.0,
        )
        assert booking1.checkIn == "2024-02-29"

        # Month boundary
        booking2 = SummarizedBooking(
            id=2,
            guestName="Test",
            checkIn="2025-01-31",
            checkOut="2025-02-01",
            listingId=1,
            status="confirmed",
            totalPrice=100.0,
        )
        assert booking2.checkIn == "2025-01-31"
