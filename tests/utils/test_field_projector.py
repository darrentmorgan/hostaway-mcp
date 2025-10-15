"""Unit tests for field_projector module.

Tests field projection, essential field mapping, and field count estimation.
"""

import pytest

from src.utils.field_projector import (
    calculate_projection_ratio,
    estimate_field_count,
    get_essential_fields,
    project_fields,
)


class TestProjectFields:
    """Test field projection functionality."""

    def test_project_fields_simple(self) -> None:
        """Test projecting simple top-level fields."""
        obj = {
            "id": "BK12345",
            "status": "confirmed",
            "guestName": "John Doe",
            "guestEmail": "john@example.com",
        }

        result = project_fields(obj, ["id", "status"])

        assert result == {"id": "BK12345", "status": "confirmed"}
        assert "guestName" not in result
        assert "guestEmail" not in result

    def test_project_fields_empty_field_list(self) -> None:
        """Test projecting with empty field list."""
        obj = {"id": "BK12345", "status": "confirmed"}

        result = project_fields(obj, [])

        assert result == {}

    def test_project_fields_all_fields(self) -> None:
        """Test projecting all fields."""
        obj = {"id": "BK12345", "status": "confirmed"}

        result = project_fields(obj, ["id", "status"])

        assert result == obj

    def test_project_fields_nonexistent_field(self) -> None:
        """Test projecting nonexistent field (should be skipped)."""
        obj = {"id": "BK12345"}

        result = project_fields(obj, ["id", "nonexistent"])

        assert result == {"id": "BK12345"}
        assert "nonexistent" not in result

    def test_project_fields_nested_simple(self) -> None:
        """Test projecting nested field with dot notation."""
        obj = {
            "id": "BK12345",
            "guestAddress": {
                "city": "NYC",
                "state": "NY",
                "zip": "10001",
            },
        }

        result = project_fields(obj, ["id", "guestAddress.city"])

        assert result == {
            "id": "BK12345",
            "guestAddress": {"city": "NYC"},
        }
        assert "state" not in result.get("guestAddress", {})

    def test_project_fields_nested_multiple(self) -> None:
        """Test projecting multiple nested fields."""
        obj = {
            "id": "BK12345",
            "guestAddress": {
                "city": "NYC",
                "state": "NY",
                "zip": "10001",
            },
        }

        result = project_fields(obj, ["guestAddress.city", "guestAddress.state"])

        assert result == {
            "guestAddress": {
                "city": "NYC",
                "state": "NY",
            }
        }

    def test_project_fields_nested_deeply(self) -> None:
        """Test projecting deeply nested fields."""
        obj = {
            "booking": {
                "guest": {
                    "contact": {
                        "email": "john@example.com",
                    }
                }
            }
        }

        result = project_fields(obj, ["booking.guest.contact.email"])

        assert result == {
            "booking": {
                "guest": {
                    "contact": {
                        "email": "john@example.com",
                    }
                }
            }
        }

    def test_project_fields_nested_nonexistent(self) -> None:
        """Test projecting nonexistent nested field."""
        obj = {
            "id": "BK12345",
            "guestAddress": {"city": "NYC"},
        }

        result = project_fields(obj, ["guestAddress.nonexistent"])

        # Should not create nonexistent fields
        assert result == {}

    def test_project_fields_mixed_simple_and_nested(self) -> None:
        """Test projecting mix of simple and nested fields."""
        obj = {
            "id": "BK12345",
            "status": "confirmed",
            "guestAddress": {
                "city": "NYC",
                "state": "NY",
            },
        }

        result = project_fields(obj, ["id", "guestAddress.city"])

        assert result == {
            "id": "BK12345",
            "guestAddress": {"city": "NYC"},
        }

    def test_project_fields_booking_example(self) -> None:
        """Test realistic booking object projection."""
        booking = {
            "id": "BK12345",
            "status": "confirmed",
            "guestName": "John Doe",
            "guestEmail": "john@example.com",
            "guestPhone": "+1-555-0100",
            "guestAddress": {
                "street": "123 Main St",
                "city": "NYC",
                "state": "NY",
                "zip": "10001",
            },
            "checkInDate": "2025-11-01",
            "checkOutDate": "2025-11-05",
            "totalPrice": 1200.0,
            "priceBreakdown": {
                "nights": 4,
                "basePrice": 1000.0,
                "cleaningFee": 100.0,
                "taxesAndFees": 100.0,
            },
        }

        essential_fields = [
            "id",
            "status",
            "guestName",
            "checkInDate",
            "checkOutDate",
            "totalPrice",
        ]

        result = project_fields(booking, essential_fields)

        assert result == {
            "id": "BK12345",
            "status": "confirmed",
            "guestName": "John Doe",
            "checkInDate": "2025-11-01",
            "checkOutDate": "2025-11-05",
            "totalPrice": 1200.0,
        }
        assert len(result) == 6


class TestGetEssentialFields:
    """Test essential field retrieval for object types."""

    def test_get_essential_fields_booking(self) -> None:
        """Test essential fields for booking."""
        fields = get_essential_fields("booking")

        assert "id" in fields
        assert "status" in fields
        assert "guestName" in fields
        assert "checkInDate" in fields
        assert "checkOutDate" in fields
        assert "totalPrice" in fields
        assert len(fields) >= 6

    def test_get_essential_fields_listing(self) -> None:
        """Test essential fields for listing."""
        fields = get_essential_fields("listing")

        assert "id" in fields
        assert "name" in fields
        assert "status" in fields
        assert "address" in fields

    def test_get_essential_fields_financial_transaction(self) -> None:
        """Test essential fields for financial transaction."""
        fields = get_essential_fields("financial_transaction")

        assert "id" in fields
        assert "type" in fields
        assert "amount" in fields
        assert "currency" in fields
        assert "status" in fields

    def test_get_essential_fields_conversation(self) -> None:
        """Test essential fields for conversation."""
        fields = get_essential_fields("conversation")

        assert "id" in fields
        assert "bookingId" in fields
        assert "guestName" in fields

    def test_get_essential_fields_review(self) -> None:
        """Test essential fields for review."""
        fields = get_essential_fields("review")

        assert "id" in fields
        assert "bookingId" in fields
        assert "rating" in fields

    def test_get_essential_fields_unknown_type(self) -> None:
        """Test essential fields for unknown type (should return id only)."""
        fields = get_essential_fields("unknown_type")

        assert fields == ["id"]


class TestEstimateFieldCount:
    """Test field count estimation."""

    def test_estimate_field_count_empty(self) -> None:
        """Test field count for empty object."""
        count = estimate_field_count({})
        assert count == 0

    def test_estimate_field_count_simple(self) -> None:
        """Test field count for simple object."""
        obj = {
            "id": "BK12345",
            "status": "confirmed",
            "totalPrice": 1200.0,
        }

        count = estimate_field_count(obj)
        assert count == 3

    def test_estimate_field_count_nested(self) -> None:
        """Test field count for nested object."""
        obj = {
            "id": "BK12345",
            "guestAddress": {
                "city": "NYC",
                "state": "NY",
            },
        }

        # id, guestAddress, city, state = 4 fields
        count = estimate_field_count(obj)
        assert count == 4

    def test_estimate_field_count_deeply_nested(self) -> None:
        """Test field count for deeply nested object."""
        obj = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep",
                    }
                }
            }
        }

        # level1, level2, level3, value = 4 fields
        count = estimate_field_count(obj)
        assert count == 4

    def test_estimate_field_count_with_list(self) -> None:
        """Test field count for object with list."""
        obj = {
            "id": "BK12345",
            "amenities": [
                {"name": "WiFi", "available": True},
                {"name": "Kitchen", "available": True},
            ],
        }

        # id, amenities, name, available = 4 fields
        # (counts fields in first list item)
        count = estimate_field_count(obj)
        assert count == 4

    def test_estimate_field_count_realistic_booking(self) -> None:
        """Test field count for realistic booking object."""
        booking = {
            "id": "BK12345",
            "status": "confirmed",
            "guestName": "John Doe",
            "guestAddress": {
                "city": "NYC",
                "state": "NY",
            },
            "checkInDate": "2025-11-01",
            "checkOutDate": "2025-11-05",
            "totalPrice": 1200.0,
        }

        # id, status, guestName, guestAddress, city, state,
        # checkInDate, checkOutDate, totalPrice = 9 fields
        count = estimate_field_count(booking)
        assert count == 9


class TestCalculateProjectionRatio:
    """Test projection ratio calculation."""

    def test_calculate_projection_ratio_half(self) -> None:
        """Test projection ratio when half fields retained."""
        original = {
            "id": "BK12345",
            "field1": 1,
            "field2": 2,
            "field3": 3,
        }
        projected = {
            "id": "BK12345",
            "field1": 1,
        }

        ratio = calculate_projection_ratio(original, projected)

        # 2 out of 4 fields = 0.5
        assert ratio == pytest.approx(0.5, rel=0.01)

    def test_calculate_projection_ratio_all_fields(self) -> None:
        """Test projection ratio when all fields retained."""
        obj = {"id": "BK12345", "status": "confirmed"}

        ratio = calculate_projection_ratio(obj, obj)

        assert ratio == 1.0

    def test_calculate_projection_ratio_no_fields(self) -> None:
        """Test projection ratio when no fields retained."""
        original = {"id": "BK12345", "status": "confirmed"}
        projected = {}

        ratio = calculate_projection_ratio(original, projected)

        assert ratio == 0.0

    def test_calculate_projection_ratio_empty_original(self) -> None:
        """Test projection ratio with empty original (edge case)."""
        ratio = calculate_projection_ratio({}, {})

        # Avoid division by zero
        assert ratio == 1.0

    def test_calculate_projection_ratio_nested(self) -> None:
        """Test projection ratio with nested objects."""
        original = {
            "id": "BK12345",
            "status": "confirmed",
            "guestAddress": {
                "city": "NYC",
                "state": "NY",
                "zip": "10001",
            },
        }
        projected = {
            "id": "BK12345",
            "guestAddress": {
                "city": "NYC",
            },
        }

        ratio = calculate_projection_ratio(original, projected)

        # Original: id, status, guestAddress, city, state, zip = 6 fields
        # Projected: id, guestAddress, city = 3 fields
        # Ratio: 3/6 = 0.5
        assert ratio == pytest.approx(0.5, rel=0.01)

    def test_calculate_projection_ratio_realistic_summarization(self) -> None:
        """Test projection ratio for realistic summarization scenario."""
        original = {
            "id": "BK12345",
            "status": "confirmed",
            "guestName": "John Doe",
            "guestEmail": "john@example.com",
            "guestPhone": "+1-555-0100",
            "guestAddress": {
                "street": "123 Main St",
                "city": "NYC",
                "state": "NY",
                "zip": "10001",
            },
            "checkInDate": "2025-11-01",
            "checkOutDate": "2025-11-05",
            "totalPrice": 1200.0,
            "currency": "USD",
            "priceBreakdown": {
                "nights": 4,
                "basePrice": 1000.0,
                "cleaningFee": 100.0,
                "taxesAndFees": 100.0,
            },
        }

        projected = {
            "id": "BK12345",
            "status": "confirmed",
            "guestName": "John Doe",
            "checkInDate": "2025-11-01",
            "checkOutDate": "2025-11-05",
            "totalPrice": 1200.0,
        }

        ratio = calculate_projection_ratio(original, projected)

        # Should retain roughly 30-40% of fields (typical summarization)
        assert 0.25 <= ratio <= 0.5
