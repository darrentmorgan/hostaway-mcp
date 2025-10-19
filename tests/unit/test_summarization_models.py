"""Unit tests for summarization models.

Tests Pydantic models for response compression and chunking.
"""

import pytest
from pydantic import ValidationError

from src.models.summarization import (
    ChunkMetadata,
    ContentChunk,
    DetailsFetchInfo,
    SummarizationResult,
    SummarizationStrategy,
    SummaryMetadata,
    SummaryResponse,
)


class TestDetailsFetchInfo:
    """Test suite for DetailsFetchInfo model."""

    def test_create_details_fetch_info(self):
        """Test creating DetailsFetchInfo with required fields."""
        info = DetailsFetchInfo(endpoint="/api/v1/bookings/123", parameters={"fields": "all"})

        assert info.endpoint == "/api/v1/bookings/123"
        assert info.parameters == {"fields": "all"}

    def test_details_fetch_info_empty_parameters(self):
        """Test DetailsFetchInfo with empty parameters."""
        info = DetailsFetchInfo(endpoint="/api/v1/listings/456")

        assert info.endpoint == "/api/v1/listings/456"
        assert info.parameters == {}


class TestSummaryMetadata:
    """Test suite for SummaryMetadata model."""

    def test_create_summary_metadata_preview(self):
        """Test creating preview metadata."""
        metadata = SummaryMetadata(
            kind="preview",
            totalFields=20,
            projectedFields=["id", "status", "guestName"],
            detailsAvailable=DetailsFetchInfo(endpoint="/api/v1/bookings/123"),
        )

        assert metadata.kind == "preview"
        assert metadata.totalFields == 20
        assert metadata.projectedFields == ["id", "status", "guestName"]

    def test_create_summary_metadata_full(self):
        """Test creating full metadata."""
        metadata = SummaryMetadata(
            kind="full",
            totalFields=20,
            projectedFields=["id"] * 20,
            detailsAvailable=DetailsFetchInfo(endpoint="/api/v1/bookings/123"),
        )

        assert metadata.kind == "full"

    def test_summary_metadata_negative_total_fields(self):
        """Test validation error for negative totalFields."""
        with pytest.raises(ValidationError):
            SummaryMetadata(
                kind="preview",
                totalFields=-5,
                projectedFields=["id"],
                detailsAvailable=DetailsFetchInfo(endpoint="/test"),
            )


class TestSummaryResponse:
    """Test suite for SummaryResponse model."""

    def test_create_summary_response(self):
        """Test creating summary response."""
        response = SummaryResponse[dict](
            summary={"id": "BK12345", "status": "confirmed", "guestName": "John Doe"},
            meta=SummaryMetadata(
                kind="preview",
                totalFields=20,
                projectedFields=["id", "status", "guestName"],
                detailsAvailable=DetailsFetchInfo(
                    endpoint="/api/v1/bookings/BK12345", parameters={"fields": "all"}
                ),
            ),
        )

        assert response.summary["id"] == "BK12345"
        assert response.summary["status"] == "confirmed"
        assert response.meta.kind == "preview"
        assert response.meta.totalFields == 20

    def test_summary_response_empty_summary(self):
        """Test summary response with empty summary."""
        response = SummaryResponse[dict](
            summary={},
            meta=SummaryMetadata(
                kind="preview",
                totalFields=0,
                projectedFields=[],
                detailsAvailable=DetailsFetchInfo(endpoint="/api/test"),
            ),
        )

        assert response.summary == {}
        assert response.meta.projectedFields == []


class TestSummarizationStrategy:
    """Test suite for SummarizationStrategy model."""

    def test_create_strategy_defaults(self):
        """Test creating strategy with defaults."""
        strategy = SummarizationStrategy()

        assert strategy.strategy_type == "field_projection"
        assert strategy.essential_fields == []
        assert strategy.max_nested_depth == 2
        assert strategy.preserve_structure is True

    def test_create_strategy_field_projection(self):
        """Test creating field projection strategy."""
        strategy = SummarizationStrategy(
            strategy_type="field_projection",
            essential_fields=["id", "status", "name"],
            max_nested_depth=3,
            preserve_structure=True,
        )

        assert strategy.strategy_type == "field_projection"
        assert strategy.essential_fields == ["id", "status", "name"]
        assert strategy.max_nested_depth == 3

    def test_create_strategy_extractive(self):
        """Test creating extractive strategy."""
        strategy = SummarizationStrategy(
            strategy_type="extractive", essential_fields=["summary", "highlights"]
        )

        assert strategy.strategy_type == "extractive"

    def test_create_strategy_abstractive(self):
        """Test creating abstractive strategy."""
        strategy = SummarizationStrategy(
            strategy_type="abstractive", max_nested_depth=1, preserve_structure=False
        )

        assert strategy.strategy_type == "abstractive"
        assert strategy.preserve_structure is False

    def test_strategy_invalid_nested_depth(self):
        """Test validation error for invalid nested depth."""
        with pytest.raises(ValidationError):
            SummarizationStrategy(max_nested_depth=0)


class TestSummarizationResult:
    """Test suite for SummarizationResult model."""

    def test_create_summarization_result(self):
        """Test creating summarization result."""
        result = SummarizationResult(
            original_field_count=20,
            summarized_field_count=5,
            reduction_ratio=0.75,
            original_tokens=1000,
            summarized_tokens=250,
            token_reduction=0.75,
        )

        assert result.original_field_count == 20
        assert result.summarized_field_count == 5
        assert result.reduction_ratio == 0.75
        assert result.original_tokens == 1000
        assert result.summarized_tokens == 250
        assert result.token_reduction == 0.75

    def test_summarization_result_no_reduction(self):
        """Test summarization result with no reduction."""
        result = SummarizationResult(
            original_field_count=10,
            summarized_field_count=10,
            reduction_ratio=0.0,
            original_tokens=500,
            summarized_tokens=500,
            token_reduction=0.0,
        )

        assert result.reduction_ratio == 0.0
        assert result.token_reduction == 0.0

    def test_summarization_result_negative_counts(self):
        """Test validation error for negative counts."""
        with pytest.raises(ValidationError):
            SummarizationResult(
                original_field_count=-5,
                summarized_field_count=5,
                reduction_ratio=0.5,
                original_tokens=100,
                summarized_tokens=50,
                token_reduction=0.5,
            )

    def test_summarization_result_invalid_ratio(self):
        """Test validation error for invalid reduction ratio."""
        with pytest.raises(ValidationError):
            SummarizationResult(
                original_field_count=10,
                summarized_field_count=5,
                reduction_ratio=1.5,  # Invalid: > 1.0
                original_tokens=100,
                summarized_tokens=50,
                token_reduction=0.5,
            )


class TestChunkMetadata:
    """Test suite for ChunkMetadata model."""

    def test_create_chunk_metadata(self):
        """Test creating chunk metadata."""
        metadata = ChunkMetadata(startLine=0, endLine=99, totalLines=500, bytesInChunk=4096)

        assert metadata.startLine == 0
        assert metadata.endLine == 99
        assert metadata.totalLines == 500
        assert metadata.bytesInChunk == 4096

    def test_chunk_metadata_validation_end_before_start(self):
        """Test validation error when endLine < startLine."""
        with pytest.raises(ValidationError, match="endLine must be >= startLine"):
            ChunkMetadata(startLine=100, endLine=50, totalLines=500, bytesInChunk=1024)

    def test_chunk_metadata_validation_total_too_small(self):
        """Test validation error when totalLines <= endLine."""
        with pytest.raises(ValidationError, match="totalLines must be > endLine"):
            ChunkMetadata(
                startLine=0,
                endLine=100,
                totalLines=100,  # Should be > endLine
                bytesInChunk=1024,
            )

    def test_chunk_metadata_equal_start_end(self):
        """Test chunk metadata with equal start and end lines."""
        metadata = ChunkMetadata(startLine=50, endLine=50, totalLines=100, bytesInChunk=100)

        assert metadata.startLine == metadata.endLine


class TestContentChunk:
    """Test suite for ContentChunk model."""

    def test_create_content_chunk(self):
        """Test creating content chunk."""
        chunk = ContentChunk(
            content="This is chunk 1 content...",
            chunkIndex=0,
            totalChunks=5,
            nextCursor="cursor-for-chunk-2",
            metadata=ChunkMetadata(startLine=0, endLine=99, totalLines=500, bytesInChunk=2048),
        )

        assert chunk.content == "This is chunk 1 content..."
        assert chunk.chunkIndex == 0
        assert chunk.totalChunks == 5
        assert chunk.nextCursor == "cursor-for-chunk-2"
        assert chunk.metadata.startLine == 0

    def test_content_chunk_last_chunk(self):
        """Test content chunk for last chunk (no next cursor)."""
        chunk = ContentChunk(
            content="This is the last chunk",
            chunkIndex=4,
            totalChunks=5,
            nextCursor=None,
            metadata=ChunkMetadata(startLine=400, endLine=499, totalLines=500, bytesInChunk=1024),
        )

        assert chunk.chunkIndex == 4
        assert chunk.totalChunks == 5
        assert chunk.nextCursor is None

    def test_content_chunk_negative_index(self):
        """Test validation error for negative chunk index."""
        with pytest.raises(ValidationError):
            ContentChunk(
                content="test",
                chunkIndex=-1,
                totalChunks=5,
                metadata=ChunkMetadata(startLine=0, endLine=10, totalLines=100, bytesInChunk=100),
            )

    def test_content_chunk_zero_total(self):
        """Test validation error for zero total chunks."""
        with pytest.raises(ValidationError):
            ContentChunk(
                content="test",
                chunkIndex=0,
                totalChunks=0,
                metadata=ChunkMetadata(startLine=0, endLine=10, totalLines=100, bytesInChunk=100),
            )

    def test_content_chunk_empty_content(self):
        """Test content chunk with empty content."""
        chunk = ContentChunk(
            content="",
            chunkIndex=0,
            totalChunks=1,
            metadata=ChunkMetadata(startLine=0, endLine=0, totalLines=1, bytesInChunk=0),
        )

        assert chunk.content == ""
        assert chunk.metadata.bytesInChunk == 0
