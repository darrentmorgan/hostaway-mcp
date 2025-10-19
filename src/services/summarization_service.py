"""Summarization service for response compression.

Provides field projection and response summarization to reduce token usage.
Integrates with token estimator and field projector utilities.
"""

from typing import Any

from src.models.summarization import (
    DetailsFetchInfo,
    SummarizationResult,
    SummaryMetadata,
    SummaryResponse,
)
from src.utils.field_projector import (
    estimate_field_count,
    get_essential_fields,
    project_fields,
)
from src.utils.token_estimator import estimate_tokens_from_dict


class SummarizationService:
    """Service for response summarization.

    Implements field projection strategy to reduce response size
    while preserving essential information.
    """

    def summarize_object(
        self,
        obj: dict[str, Any],
        obj_type: str,
        endpoint: str,
        custom_fields: list[str] | None = None,
    ) -> SummaryResponse:
        """Summarize object using field projection.

        Args:
            obj: Original object to summarize
            obj_type: Object type (e.g., "booking", "listing")
            endpoint: API endpoint for full details
            custom_fields: Custom field list (uses defaults if None)

        Returns:
            SummaryResponse with projected fields and metadata
        """
        # Determine fields to project
        fields = custom_fields or get_essential_fields(obj_type)

        # Project fields
        summary = project_fields(obj, fields)

        # Count total fields
        total_fields = estimate_field_count(obj)

        # Build metadata
        meta = SummaryMetadata(
            kind="preview",
            totalFields=total_fields,
            projectedFields=fields,
            detailsAvailable=DetailsFetchInfo(
                endpoint=endpoint,
                parameters={"fields": "all"},
            ),
        )

        return SummaryResponse(
            summary=summary,
            meta=meta,
        )

    def should_summarize(
        self,
        obj: dict[str, Any],
        token_threshold: int = 4000,
    ) -> tuple[bool, int]:
        """Determine if object should be summarized.

        Args:
            obj: Object to evaluate
            token_threshold: Token threshold for summarization

        Returns:
            Tuple of (should_summarize, estimated_tokens)
        """
        estimated_tokens = estimate_tokens_from_dict(obj)
        should_summarize = estimated_tokens > token_threshold

        return should_summarize, estimated_tokens

    def calculate_reduction(
        self,
        original: dict[str, Any],
        summary: dict[str, Any],
    ) -> SummarizationResult:
        """Calculate summarization metrics.

        Args:
            original: Original object
            summary: Summarized object

        Returns:
            SummarizationResult with reduction metrics
        """
        # Count fields
        original_field_count = estimate_field_count(original)
        summarized_field_count = estimate_field_count(summary)

        # Calculate field reduction
        if original_field_count > 0:
            reduction_ratio = 1.0 - (summarized_field_count / original_field_count)
        else:
            reduction_ratio = 0.0

        # Estimate tokens
        original_tokens = estimate_tokens_from_dict(original)
        summarized_tokens = estimate_tokens_from_dict(summary)

        # Calculate token reduction
        token_reduction = 1.0 - summarized_tokens / original_tokens if original_tokens > 0 else 0.0

        return SummarizationResult(
            original_field_count=original_field_count,
            summarized_field_count=summarized_field_count,
            reduction_ratio=reduction_ratio,
            original_tokens=original_tokens,
            summarized_tokens=summarized_tokens,
            token_reduction=token_reduction,
        )

    def summarize_list(
        self,
        items: list[dict[str, Any]],
        obj_type: str,
        endpoint_template: str,
        id_field: str = "id",
        custom_fields: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Summarize list of objects.

        Args:
            items: List of objects to summarize
            obj_type: Object type
            endpoint_template: Endpoint template with {id} placeholder
            id_field: Field name containing object ID
            custom_fields: Custom fields to project

        Returns:
            List of summarized objects (as dicts, not SummaryResponse)

        Example:
            >>> items = [
            ...     {"id": "BK1", "status": "confirmed", "guestName": "John", "details": {...}},
            ...     {"id": "BK2", "status": "pending", "guestName": "Jane", "details": {...}},
            ... ]
            >>> summarized = service.summarize_list(
            ...     items=items,
            ...     obj_type="booking",
            ...     endpoint_template="/api/v1/bookings/{id}"
            ... )
            >>> # Returns list of projected dicts (not SummaryResponse objects)
        """
        # Determine fields to project
        fields = custom_fields or get_essential_fields(obj_type)

        # Project fields for each item
        summarized_items = []
        for item in items:
            summary = project_fields(item, fields)
            summarized_items.append(summary)

        return summarized_items


# Global singleton instance
_summarization_service: SummarizationService | None = None


def get_summarization_service() -> SummarizationService:
    """Get global summarization service instance.

    Returns:
        Singleton SummarizationService instance
    """
    global _summarization_service

    if _summarization_service is None:
        _summarization_service = SummarizationService()

    return _summarization_service
