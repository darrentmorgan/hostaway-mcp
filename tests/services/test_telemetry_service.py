"""Comprehensive tests for telemetry service.

Tests telemetry recording, metrics aggregation, and monitoring functionality.
"""

import time
from datetime import datetime

import pytest

from src.services.telemetry_service import (
    TelemetryRecord,
    TelemetryService,
    get_telemetry_service,
)


class TestTelemetryRecord:
    """Test TelemetryRecord model."""

    def test_telemetry_record_creation(self):
        """Test creating a telemetry record."""
        record = TelemetryRecord(
            request_id="req-123",
            endpoint="/api/listings",
            timestamp=datetime.now(),
            estimated_tokens=1000,
            response_bytes=5000,
            item_count=10,
            latency_ms=150,
            pagination_used=True,
            summarization_used=False,
            chunking_used=False,
            optimization_metadata={"page": 1},
        )

        assert record.request_id == "req-123"
        assert record.endpoint == "/api/listings"
        assert record.estimated_tokens == 1000
        assert record.response_bytes == 5000
        assert record.item_count == 10
        assert record.latency_ms == 150
        assert record.pagination_used is True
        assert record.summarization_used is False
        assert record.chunking_used is False
        assert record.optimization_metadata == {"page": 1}

    def test_tokens_per_item_calculation(self):
        """Test tokens per item property calculation."""
        record = TelemetryRecord(
            request_id="req-123",
            endpoint="/api/listings",
            timestamp=datetime.now(),
            estimated_tokens=1000,
            response_bytes=5000,
            item_count=10,
            latency_ms=150,
            pagination_used=True,
            summarization_used=False,
            chunking_used=False,
        )

        assert record.tokens_per_item == 100.0  # 1000 / 10

    def test_tokens_per_item_zero_items(self):
        """Test tokens per item returns 0 when item count is 0."""
        record = TelemetryRecord(
            request_id="req-123",
            endpoint="/api/listings",
            timestamp=datetime.now(),
            estimated_tokens=1000,
            response_bytes=5000,
            item_count=0,
            latency_ms=150,
            pagination_used=True,
            summarization_used=False,
            chunking_used=False,
        )

        assert record.tokens_per_item == 0.0


class TestTelemetryService:
    """Test TelemetryService functionality."""

    @pytest.fixture
    def service(self):
        """Create fresh telemetry service for each test."""
        return TelemetryService(max_records=100)

    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service.max_records == 100
        assert service.records == []
        assert service._start_time > 0

    def test_record_request_basic(self, service):
        """Test recording a single request."""
        service.record_request(
            request_id="req-1",
            endpoint="/api/listings",
            estimated_tokens=500,
            response_bytes=2000,
            item_count=5,
            latency_ms=100,
        )

        assert len(service.records) == 1
        record = service.records[0]
        assert record.request_id == "req-1"
        assert record.endpoint == "/api/listings"
        assert record.estimated_tokens == 500
        assert record.response_bytes == 2000
        assert record.item_count == 5
        assert record.latency_ms == 100
        assert record.pagination_used is False
        assert record.summarization_used is False

    def test_record_request_with_optimizations(self, service):
        """Test recording request with optimization flags."""
        service.record_request(
            request_id="req-2",
            endpoint="/api/bookings",
            estimated_tokens=1500,
            response_bytes=8000,
            item_count=15,
            latency_ms=250,
            pagination_used=True,
            summarization_used=True,
            chunking_used=False,
            optimization_metadata={"cursor": "abc123"},
        )

        record = service.records[0]
        assert record.pagination_used is True
        assert record.summarization_used is True
        assert record.chunking_used is False
        assert record.optimization_metadata == {"cursor": "abc123"}

    def test_max_records_trimming(self):
        """Test that old records are trimmed when exceeding max_records."""
        service = TelemetryService(max_records=10)

        # Add 15 records
        for i in range(15):
            service.record_request(
                request_id=f"req-{i}",
                endpoint="/api/test",
                estimated_tokens=100,
                response_bytes=500,
                item_count=1,
                latency_ms=50,
            )

        # Should only keep last 10
        assert len(service.records) == 10
        assert service.records[0].request_id == "req-5"
        assert service.records[-1].request_id == "req-14"

    def test_get_metrics_empty(self, service):
        """Test get_metrics returns correct structure when empty."""
        metrics = service.get_metrics()

        assert metrics["total_requests"] == 0
        assert metrics["pagination_adoption"] == 0.0
        assert metrics["summarization_adoption"] == 0.0
        assert metrics["avg_response_size"] == 0
        assert metrics["avg_latency_ms"] == 0
        assert metrics["oversized_events"] == 0
        assert "uptime_seconds" in metrics
        assert metrics["uptime_seconds"] >= 0

    def test_get_metrics_with_data(self, service):
        """Test get_metrics calculates correct aggregations."""
        # Add 10 requests: 5 with pagination, 3 with summarization, 2 oversized
        for i in range(10):
            service.record_request(
                request_id=f"req-{i}",
                endpoint="/api/test",
                estimated_tokens=5000 if i < 2 else 2000,  # First 2 are oversized
                response_bytes=1000,
                item_count=5,
                latency_ms=100,
                pagination_used=i < 5,  # First 5 use pagination
                summarization_used=i < 3,  # First 3 use summarization
            )

        metrics = service.get_metrics()

        assert metrics["total_requests"] == 10
        assert metrics["pagination_adoption"] == 0.5  # 5/10
        assert metrics["summarization_adoption"] == 0.3  # 3/10
        assert metrics["avg_response_size"] == 1000  # 10000 / 10
        assert metrics["avg_latency_ms"] == 100  # 1000 / 10
        assert metrics["oversized_events"] == 2  # 2 events > 4000 tokens

    def test_get_endpoint_metrics_empty(self, service):
        """Test get_endpoint_metrics returns correct structure when empty."""
        metrics = service.get_endpoint_metrics("/api/listings")

        assert metrics["endpoint"] == "/api/listings"
        assert metrics["total_requests"] == 0
        assert metrics["pagination_rate"] == 0.0
        assert metrics["summarization_rate"] == 0.0
        assert metrics["avg_tokens"] == 0
        assert metrics["avg_items"] == 0

    def test_get_endpoint_metrics_with_data(self, service):
        """Test get_endpoint_metrics calculates endpoint-specific metrics."""
        # Add requests for different endpoints
        for i in range(5):
            service.record_request(
                request_id=f"listings-{i}",
                endpoint="/api/listings",
                estimated_tokens=1000,
                response_bytes=5000,
                item_count=10,
                latency_ms=100,
                pagination_used=i < 3,  # 3/5 use pagination
                summarization_used=i < 2,  # 2/5 use summarization
            )

        for i in range(3):
            service.record_request(
                request_id=f"bookings-{i}",
                endpoint="/api/bookings",
                estimated_tokens=2000,
                response_bytes=8000,
                item_count=20,
                latency_ms=200,
                pagination_used=True,
                summarization_used=False,
            )

        # Test listings endpoint metrics
        listings_metrics = service.get_endpoint_metrics("/api/listings")
        assert listings_metrics["endpoint"] == "/api/listings"
        assert listings_metrics["total_requests"] == 5
        assert listings_metrics["pagination_rate"] == 0.6  # 3/5
        assert listings_metrics["summarization_rate"] == 0.4  # 2/5
        assert listings_metrics["avg_tokens"] == 1000  # 5000 / 5
        assert listings_metrics["avg_items"] == 10  # 50 / 5

        # Test bookings endpoint metrics
        bookings_metrics = service.get_endpoint_metrics("/api/bookings")
        assert bookings_metrics["total_requests"] == 3
        assert bookings_metrics["pagination_rate"] == 1.0  # 3/3
        assert bookings_metrics["summarization_rate"] == 0.0  # 0/3
        assert bookings_metrics["avg_tokens"] == 2000  # 6000 / 3
        assert bookings_metrics["avg_items"] == 20  # 60 / 3

    def test_get_recent_records(self, service):
        """Test get_recent_records returns correct number of recent records."""
        # Add 20 records
        for i in range(20):
            service.record_request(
                request_id=f"req-{i}",
                endpoint="/api/test",
                estimated_tokens=100,
                response_bytes=500,
                item_count=1,
                latency_ms=50,
            )

        # Get last 5 records
        recent = service.get_recent_records(limit=5)

        assert len(recent) == 5
        assert recent[0]["request_id"] == "req-15"
        assert recent[-1]["request_id"] == "req-19"
        # Verify they are dicts (model_dump was called)
        assert isinstance(recent[0], dict)
        assert "timestamp" in recent[0]

    def test_get_recent_records_less_than_limit(self, service):
        """Test get_recent_records when fewer records than limit."""
        # Add only 3 records
        for i in range(3):
            service.record_request(
                request_id=f"req-{i}",
                endpoint="/api/test",
                estimated_tokens=100,
                response_bytes=500,
                item_count=1,
                latency_ms=50,
            )

        # Request 10 but should only get 3
        recent = service.get_recent_records(limit=10)

        assert len(recent) == 3

    def test_clear_records(self, service):
        """Test clearing all telemetry records."""
        # Add some records
        for i in range(5):
            service.record_request(
                request_id=f"req-{i}",
                endpoint="/api/test",
                estimated_tokens=100,
                response_bytes=500,
                item_count=1,
                latency_ms=50,
            )

        assert len(service.records) == 5

        # Clear records
        service.clear_records()

        assert len(service.records) == 0

    def test_uptime_tracking(self, service):
        """Test that uptime is correctly tracked."""
        time.sleep(0.1)  # Sleep for 100ms

        metrics = service.get_metrics()

        assert metrics["uptime_seconds"] >= 0.1
        assert metrics["uptime_seconds"] < 1.0  # Should be less than 1 second


class TestTelemetryServiceSingleton:
    """Test telemetry service singleton behavior."""

    def test_get_telemetry_service_returns_singleton(self):
        """Test get_telemetry_service returns same instance."""
        service1 = get_telemetry_service()
        service2 = get_telemetry_service()

        assert service1 is service2

    def test_singleton_maintains_state(self):
        """Test singleton maintains state across calls."""
        service = get_telemetry_service()
        service.clear_records()  # Start fresh

        service.record_request(
            request_id="req-singleton",
            endpoint="/api/test",
            estimated_tokens=100,
            response_bytes=500,
            item_count=1,
            latency_ms=50,
        )

        # Get service again
        service2 = get_telemetry_service()

        assert len(service2.records) == 1
        assert service2.records[0].request_id == "req-singleton"
