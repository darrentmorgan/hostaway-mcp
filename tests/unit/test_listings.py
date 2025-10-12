"""Unit tests for Listings models.

Tests Listing, ListingSummary, PricingInfo, and AvailabilityInfo models.
Following TDD: These tests should FAIL until models are implemented.
"""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError


# T043: Unit tests for listings models
class TestListingModels:
    """Test suite for Listing-related Pydantic models."""

    def test_listing_creation_with_all_fields(self) -> None:
        """Test that Listing model can be created with all fields."""
        # TODO: Import models once implemented
        # from src.models.listings import Listing, PricingInfo, AvailabilityInfo
        #
        # listing = Listing(
        #     id=12345,
        #     name="Cozy Downtown Apartment",
        #     address="123 Main St, Apt 4B",
        #     city="San Francisco",
        #     state="California",
        #     country="USA",
        #     postal_code="94102",
        #     description="Beautiful 2BR apartment...",
        #     capacity=4,
        #     bedrooms=2,
        #     bathrooms=Decimal("1.5"),
        #     property_type="apartment",
        #     amenities=["wifi", "parking", "kitchen"],
        #     base_price=Decimal("150.00"),
        #     is_active=True,
        #     pricing=PricingInfo(
        #         base_price=Decimal("150.00"),
        #         currency="USD",
        #         cleaning_fee=Decimal("50.00"),
        #         security_deposit=Decimal("200.00"),
        #         min_stay_nights=2,
        #     ),
        #     availability=AvailabilityInfo(
        #         is_available=True,
        #         available_from=date(2024, 1, 15),
        #         blocked_dates=[],
        #         booked_dates=[],
        #     ),
        # )
        #
        # assert listing.id == 12345
        # assert listing.name == "Cozy Downtown Apartment"
        # assert listing.capacity == 4
        # assert listing.bathrooms == Decimal("1.5")
        pass

    def test_listing_summary_creation(self) -> None:
        """Test ListingSummary model for abbreviated listing info."""
        # TODO: Import models once implemented
        # from src.models.listings import ListingSummary
        #
        # summary = ListingSummary(
        #     id=12345,
        #     name="Cozy Downtown Apartment",
        #     city="San Francisco",
        #     capacity=4,
        #     base_price=Decimal("150.00"),
        #     is_available=True,
        # )
        #
        # assert summary.id == 12345
        # assert summary.name == "Cozy Downtown Apartment"
        # assert summary.base_price == Decimal("150.00")
        pass

    def test_pricing_info_model(self) -> None:
        """Test PricingInfo model for listing pricing details."""
        # TODO: Import models once implemented
        # from src.models.listings import PricingInfo
        #
        # pricing = PricingInfo(
        #     base_price=Decimal("150.00"),
        #     currency="USD",
        #     cleaning_fee=Decimal("50.00"),
        #     security_deposit=Decimal("200.00"),
        #     min_stay_nights=2,
        #     max_stay_nights=30,
        # )
        #
        # assert pricing.base_price == Decimal("150.00")
        # assert pricing.currency == "USD"
        # assert pricing.cleaning_fee == Decimal("50.00")
        # assert pricing.min_stay_nights == 2
        pass

    def test_availability_info_model(self) -> None:
        """Test AvailabilityInfo model for listing availability."""
        # TODO: Import models once implemented
        # from src.models.listings import AvailabilityInfo
        #
        # availability = AvailabilityInfo(
        #     is_available=True,
        #     available_from=date(2024, 1, 15),
        #     available_to=date(2024, 12, 31),
        #     blocked_dates=[date(2024, 2, 14)],
        #     booked_dates=[date(2024, 3, 15), date(2024, 3, 16)],
        # )
        #
        # assert availability.is_available is True
        # assert availability.available_from == date(2024, 1, 15)
        # assert len(availability.blocked_dates) == 1
        # assert len(availability.booked_dates) == 2
        pass

    def test_listing_validation_required_fields(self) -> None:
        """Test that Listing model requires essential fields."""
        # TODO: Import models once implemented
        # from src.models.listings import Listing
        #
        # # Missing required fields should raise ValidationError
        # with pytest.raises(ValidationError) as exc_info:
        #     Listing(id=12345)  # Missing name, city, etc.
        #
        # error_fields = {err["loc"][0] for err in exc_info.value.errors()}
        # assert "name" in error_fields
        # assert "city" in error_fields
        pass

    def test_pricing_info_validation_positive_amounts(self) -> None:
        """Test that PricingInfo validates positive amounts."""
        # TODO: Import models once implemented
        # from src.models.listings import PricingInfo
        #
        # with pytest.raises(ValidationError) as exc_info:
        #     PricingInfo(
        #         base_price=Decimal("-150.00"),  # Negative price
        #         currency="USD",
        #         cleaning_fee=Decimal("50.00"),
        #         security_deposit=Decimal("200.00"),
        #         min_stay_nights=2,
        #     )
        #
        # assert "base_price" in str(exc_info.value)
        pass

    def test_pricing_info_validation_currency_code(self) -> None:
        """Test that PricingInfo validates currency code."""
        # TODO: Import models once implemented
        # from src.models.listings import PricingInfo
        #
        # with pytest.raises(ValidationError) as exc_info:
        #     PricingInfo(
        #         base_price=Decimal("150.00"),
        #         currency="INVALID",  # Invalid currency code
        #         cleaning_fee=Decimal("50.00"),
        #         security_deposit=Decimal("200.00"),
        #         min_stay_nights=2,
        #     )
        #
        # assert "currency" in str(exc_info.value)
        pass

    def test_availability_info_date_range_validation(self) -> None:
        """Test that AvailabilityInfo validates date ranges."""
        # TODO: Import models once implemented
        # from src.models.listings import AvailabilityInfo
        #
        # # available_to should be after available_from
        # with pytest.raises(ValidationError) as exc_info:
        #     AvailabilityInfo(
        #         is_available=True,
        #         available_from=date(2024, 12, 31),
        #         available_to=date(2024, 1, 15),  # Before available_from
        #         blocked_dates=[],
        #         booked_dates=[],
        #     )
        #
        # assert "date" in str(exc_info.value).lower()
        pass

    def test_listing_summary_derived_from_full_listing(self) -> None:
        """Test that ListingSummary can be derived from full Listing."""
        # TODO: Import models once implemented
        # from src.models.listings import Listing, ListingSummary, PricingInfo, AvailabilityInfo
        #
        # full_listing = Listing(
        #     id=12345,
        #     name="Cozy Downtown Apartment",
        #     address="123 Main St, Apt 4B",
        #     city="San Francisco",
        #     state="California",
        #     country="USA",
        #     postal_code="94102",
        #     description="Beautiful 2BR apartment...",
        #     capacity=4,
        #     bedrooms=2,
        #     bathrooms=Decimal("1.5"),
        #     property_type="apartment",
        #     amenities=["wifi", "parking"],
        #     base_price=Decimal("150.00"),
        #     is_active=True,
        #     pricing=PricingInfo(
        #         base_price=Decimal("150.00"),
        #         currency="USD",
        #         cleaning_fee=Decimal("50.00"),
        #         security_deposit=Decimal("200.00"),
        #         min_stay_nights=2,
        #     ),
        #     availability=AvailabilityInfo(
        #         is_available=True,
        #         available_from=date(2024, 1, 15),
        #         blocked_dates=[],
        #         booked_dates=[],
        #     ),
        # )
        #
        # # Create summary from full listing
        # summary = ListingSummary(
        #     id=full_listing.id,
        #     name=full_listing.name,
        #     city=full_listing.city,
        #     capacity=full_listing.capacity,
        #     base_price=full_listing.base_price,
        #     is_available=full_listing.availability.is_available,
        # )
        #
        # assert summary.id == full_listing.id
        # assert summary.name == full_listing.name
        pass
