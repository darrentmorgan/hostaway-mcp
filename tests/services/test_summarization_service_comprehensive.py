"""Comprehensive tests for summarization service.

Tests all methods including uncovered lines in summarize_object, should_summarize,
calculate_reduction, and summarize_list.
"""

import pytest

from src.services.summarization_service import (
    SummarizationService,
    get_summarization_service,
)


class TestSummarizationServiceComprehensive:
    """Comprehensive tests for SummarizationService."""

    @pytest.fixture
    def service(self):
        """Create summarization service instance."""
        return SummarizationService()

    def test_summarize_object_with_custom_fields(self, service):
        """Test summarize_object with custom fields list."""
        obj = {
            "id": "BK123",
            "status": "confirmed",
            "guestName": "John Doe",
            "guestEmail": "john@example.com",
            "listingId": 456,
            "checkIn": "2024-01-01",
            "checkOut": "2024-01-07",
            "totalAmount": 1500.00,
            "paymentStatus": "paid",
            "notes": "Early check-in requested",
            "source": "airbnb",
            "guestCount": 2,
        }

        # Use custom fields instead of defaults
        custom_fields = ["id", "status", "guestName", "totalAmount"]
        result = service.summarize_object(
            obj=obj,
            obj_type="booking",
            endpoint="/api/bookings/BK123",
            custom_fields=custom_fields,
        )

        # Verify summary contains only custom fields
        assert "id" in result.summary
        assert "status" in result.summary
        assert "guestName" in result.summary
        assert "totalAmount" in result.summary
        
        # Should not contain other fields
        assert "guestEmail" not in result.summary
        assert "checkIn" not in result.summary

        # Verify metadata
        assert result.meta.kind == "preview"
        assert result.meta.projectedFields == custom_fields
        assert result.meta.detailsAvailable.endpoint == "/api/bookings/BK123"

    def test_summarize_object_with_default_fields(self, service):
        """Test summarize_object uses default fields when custom_fields is None."""
        obj = {
            "id": "LIST789",
            "name": "Beach House",
            "address": "123 Ocean Drive",
            "city": "Miami",
            "bedrooms": 3,
            "bathrooms": 2,
            "maxGuests": 6,
            "pricePerNight": 200,
            "description": "Beautiful oceanfront property",
            "amenities": ["WiFi", "Pool", "Beach Access"],
            "photos": ["photo1.jpg", "photo2.jpg"],
        }

        result = service.summarize_object(
            obj=obj,
            obj_type="listing",
            endpoint="/api/listings/LIST789",
            custom_fields=None,  # Use defaults
        )

        # Verify it used default fields (from get_essential_fields)
        assert "id" in result.summary
        assert "name" in result.summary
        
        # Verify metadata
        assert result.meta.kind == "preview"
        assert result.meta.detailsAvailable.endpoint == "/api/listings/LIST789"
        assert result.meta.detailsAvailable.parameters == {"fields": "all"}

    def test_summarize_object_counts_total_fields(self, service):
        """Test summarize_object correctly counts total fields."""
        obj = {
            "id": 1,
            "name": "Test",
            "nested": {"field1": "value1", "field2": "value2"},
            "list": [1, 2, 3],
        }

        result = service.summarize_object(
            obj=obj,
            obj_type="test",
            endpoint="/api/test/1",
            custom_fields=["id", "name"],
        )

        # Verify totalFields reflects actual field count
        assert result.meta.totalFields > 0

    def test_should_summarize_exceeds_threshold(self, service):
        """Test should_summarize returns True when exceeding threshold."""
        # Create large object that exceeds default threshold
        large_obj = {
            "id": 1,
            "data": "x" * 20000,  # Large string to exceed token threshold
            "nested": {"key": "value" * 1000},
        }

        should_sum, tokens = service.should_summarize(large_obj, token_threshold=4000)

        assert should_sum is True
        assert tokens > 4000

    def test_should_summarize_below_threshold(self, service):
        """Test should_summarize returns False when below threshold."""
        small_obj = {
            "id": 1,
            "name": "Small Object",
        }

        should_sum, tokens = service.should_summarize(small_obj, token_threshold=4000)

        assert should_sum is False
        assert tokens < 4000

    def test_should_summarize_custom_threshold(self, service):
        """Test should_summarize with custom threshold."""
        obj = {
            "id": 1,
            "data": "x" * 100,
        }

        # Test with very low threshold
        should_sum, tokens = service.should_summarize(obj, token_threshold=10)

        assert should_sum is True
        assert tokens > 10

    def test_calculate_reduction_with_data(self, service):
        """Test calculate_reduction computes correct metrics."""
        original = {
            "id": 1,
            "name": "Test",
            "description": "Long description here",
            "nested": {"field1": "value1", "field2": "value2"},
            "tags": ["tag1", "tag2", "tag3"],
        }

        summary = {
            "id": 1,
            "name": "Test",
        }

        result = service.calculate_reduction(original, summary)

        # Verify field counts
        assert result.original_field_count > 0
        assert result.summarized_field_count > 0
        assert result.summarized_field_count < result.original_field_count

        # Verify reduction ratio
        assert 0.0 < result.reduction_ratio < 1.0

        # Verify token counts
        assert result.original_tokens > 0
        assert result.summarized_tokens > 0
        assert result.summarized_tokens < result.original_tokens

        # Verify token reduction
        assert 0.0 < result.token_reduction < 1.0

    def test_calculate_reduction_empty_objects(self, service):
        """Test calculate_reduction handles empty objects."""
        original = {}
        summary = {}

        result = service.calculate_reduction(original, summary)

        assert result.original_field_count == 0
        assert result.summarized_field_count == 0
        assert result.reduction_ratio == 0.0
        assert result.original_tokens == 0
        assert result.summarized_tokens == 0
        assert result.token_reduction == 0.0

    def test_calculate_reduction_no_reduction(self, service):
        """Test calculate_reduction when summary equals original."""
        obj = {"id": 1, "name": "Test"}

        result = service.calculate_reduction(obj, obj)

        # No reduction should occur
        assert result.reduction_ratio == 0.0
        assert result.token_reduction == 0.0

    def test_summarize_list_with_custom_fields(self, service):
        """Test summarize_list with custom fields."""
        items = [
            {"id": "BK1", "status": "confirmed", "guestName": "John", "details": "..."},
            {"id": "BK2", "status": "pending", "guestName": "Jane", "details": "..."},
            {"id": "BK3", "status": "confirmed", "guestName": "Bob", "details": "..."},
        ]

        custom_fields = ["id", "status", "guestName"]
        summarized = service.summarize_list(
            items=items,
            obj_type="booking",
            endpoint_template="/api/bookings/{id}",
            id_field="id",
            custom_fields=custom_fields,
        )

        # Verify all items were summarized
        assert len(summarized) == 3

        # Verify each item contains only projected fields
        for item in summarized:
            assert "id" in item
            assert "status" in item
            assert "guestName" in item
            assert "details" not in item

    def test_summarize_list_with_default_fields(self, service):
        """Test summarize_list uses default fields when custom_fields is None."""
        items = [
            {"id": 1, "name": "Listing 1", "address": "123 Main St", "extra": "data"},
            {"id": 2, "name": "Listing 2", "address": "456 Oak Ave", "extra": "more"},
        ]

        summarized = service.summarize_list(
            items=items,
            obj_type="listing",
            endpoint_template="/api/listings/{id}",
            custom_fields=None,  # Use defaults
        )

        assert len(summarized) == 2
        # Verify items are dicts (not SummaryResponse objects)
        assert isinstance(summarized[0], dict)

    def test_summarize_list_empty_list(self, service):
        """Test summarize_list handles empty list."""
        summarized = service.summarize_list(
            items=[],
            obj_type="booking",
            endpoint_template="/api/bookings/{id}",
        )

        assert summarized == []

    def test_summarize_list_custom_id_field(self, service):
        """Test summarize_list with custom id_field parameter."""
        items = [
            {"booking_id": "BK1", "status": "confirmed"},
            {"booking_id": "BK2", "status": "pending"},
        ]

        summarized = service.summarize_list(
            items=items,
            obj_type="booking",
            endpoint_template="/api/bookings/{booking_id}",
            id_field="booking_id",
            custom_fields=["booking_id", "status"],
        )

        assert len(summarized) == 2
        assert all("booking_id" in item for item in summarized)


class TestSummarizationServiceSingleton:
    """Test summarization service singleton."""

    def test_get_summarization_service_returns_singleton(self):
        """Test get_summarization_service returns same instance."""
        service1 = get_summarization_service()
        service2 = get_summarization_service()

        assert service1 is service2

    def test_singleton_is_summarization_service_instance(self):
        """Test singleton is correct type."""
        service = get_summarization_service()

        assert isinstance(service, SummarizationService)
