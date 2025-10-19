"""Telemetry service for context protection metrics.

Tracks pagination, summarization, and token budget metrics for observability.
Based on data-model.md TelemetryRecord entity.
"""

import time
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TelemetryRecord(BaseModel):
    """Per-request telemetry record.

    Attributes:
        request_id: Correlation ID for request tracing
        endpoint: API endpoint path
        timestamp: Request timestamp
        estimated_tokens: Estimated tokens in response
        response_bytes: Actual response size in bytes
        item_count: Number of items returned (for lists)
        latency_ms: Request processing time in milliseconds
        pagination_used: Whether pagination was applied
        summarization_used: Whether summarization was triggered
        chunking_used: Whether content chunking was applied
        optimization_metadata: Additional optimization details
    """

    request_id: str
    endpoint: str
    timestamp: datetime
    estimated_tokens: int
    response_bytes: int
    item_count: int
    latency_ms: int
    pagination_used: bool
    summarization_used: bool
    chunking_used: bool
    optimization_metadata: dict[str, Any] = {}

    @property
    def tokens_per_item(self) -> float:
        """Calculate average tokens per item.

        Returns:
            Tokens per item (0.0 if no items)
        """
        if self.item_count == 0:
            return 0.0
        return self.estimated_tokens / self.item_count


class TelemetryService:
    """Service for tracking context protection metrics.

    Maintains in-memory metrics and provides aggregation for observability.
    """

    def __init__(self, max_records: int = 10000) -> None:
        """Initialize telemetry service.

        Args:
            max_records: Maximum records to keep in memory
        """
        self.max_records = max_records
        self.records: list[TelemetryRecord] = []
        self._start_time = time.time()

    def record_request(
        self,
        request_id: str,
        endpoint: str,
        estimated_tokens: int,
        response_bytes: int,
        item_count: int,
        latency_ms: int,
        pagination_used: bool = False,
        summarization_used: bool = False,
        chunking_used: bool = False,
        optimization_metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record request metrics.

        Args:
            request_id: Correlation ID
            endpoint: API endpoint path
            estimated_tokens: Estimated response tokens
            response_bytes: Response size in bytes
            item_count: Number of items
            latency_ms: Latency in milliseconds
            pagination_used: Pagination applied
            summarization_used: Summarization applied
            chunking_used: Chunking applied
            optimization_metadata: Additional metadata
        """
        record = TelemetryRecord(
            request_id=request_id,
            endpoint=endpoint,
            timestamp=datetime.now(),
            estimated_tokens=estimated_tokens,
            response_bytes=response_bytes,
            item_count=item_count,
            latency_ms=latency_ms,
            pagination_used=pagination_used,
            summarization_used=summarization_used,
            chunking_used=chunking_used,
            optimization_metadata=optimization_metadata or {},
        )

        self.records.append(record)

        # Trim old records if exceeding max
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records :]

    def get_metrics(self) -> dict[str, Any]:
        """Get aggregated metrics.

        Returns:
            Dict with aggregated telemetry metrics
        """
        if not self.records:
            return {
                "total_requests": 0,
                "pagination_adoption": 0.0,
                "summarization_adoption": 0.0,
                "avg_response_size": 0,
                "avg_latency_ms": 0,
                "oversized_events": 0,
                "uptime_seconds": time.time() - self._start_time,
            }

        total_requests = len(self.records)
        pagination_count = sum(1 for r in self.records if r.pagination_used)
        summarization_count = sum(1 for r in self.records if r.summarization_used)

        total_bytes = sum(r.response_bytes for r in self.records)
        total_latency = sum(r.latency_ms for r in self.records)

        # Count oversized events (>4000 tokens before optimization)
        oversized_events = sum(1 for r in self.records if r.estimated_tokens > 4000)

        return {
            "total_requests": total_requests,
            "pagination_adoption": pagination_count / total_requests,
            "summarization_adoption": summarization_count / total_requests,
            "avg_response_size": total_bytes // total_requests,
            "avg_latency_ms": total_latency // total_requests,
            "oversized_events": oversized_events,
            "uptime_seconds": time.time() - self._start_time,
        }

    def get_endpoint_metrics(self, endpoint: str) -> dict[str, Any]:
        """Get metrics for specific endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            Dict with endpoint-specific metrics
        """
        endpoint_records = [r for r in self.records if r.endpoint == endpoint]

        if not endpoint_records:
            return {
                "endpoint": endpoint,
                "total_requests": 0,
                "pagination_rate": 0.0,
                "summarization_rate": 0.0,
                "avg_tokens": 0,
                "avg_items": 0,
            }

        total_requests = len(endpoint_records)
        pagination_count = sum(1 for r in endpoint_records if r.pagination_used)
        summarization_count = sum(1 for r in endpoint_records if r.summarization_used)

        total_tokens = sum(r.estimated_tokens for r in endpoint_records)
        total_items = sum(r.item_count for r in endpoint_records)

        return {
            "endpoint": endpoint,
            "total_requests": total_requests,
            "pagination_rate": pagination_count / total_requests,
            "summarization_rate": summarization_count / total_requests,
            "avg_tokens": total_tokens // total_requests,
            "avg_items": total_items // total_requests,
        }

    def get_recent_records(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent telemetry records.

        Args:
            limit: Maximum records to return

        Returns:
            List of recent records as dicts
        """
        recent = self.records[-limit:]
        return [r.model_dump() for r in recent]

    def clear_records(self) -> None:
        """Clear all telemetry records."""
        self.records.clear()


# Global singleton instance
_telemetry_service: TelemetryService | None = None


def get_telemetry_service() -> TelemetryService:
    """Get global telemetry service instance.

    Returns:
        Singleton TelemetryService instance
    """
    global _telemetry_service

    if _telemetry_service is None:
        _telemetry_service = TelemetryService()

    return _telemetry_service
