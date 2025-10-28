"""Unit tests for token budget models.

Tests token budget tracking, estimation, and configuration models.
"""

import pytest
from pydantic import ValidationError

from src.models.token_budget import (
    BudgetMetadata,
    EndpointBudgetOverride,
    TokenBudget,
    TokenBudgetConfig,
    TokenEstimationResult,
)


class TestTokenBudget:
    """Test suite for TokenBudget model."""

    def test_create_token_budget_defaults(self):
        """Test creating token budget with default values."""
        budget = TokenBudget(estimated_tokens=3000)

        assert budget.threshold == 4000
        assert budget.hard_cap == 12000
        assert budget.estimated_tokens == 3000

    def test_token_budget_custom_values(self):
        """Test creating token budget with custom values."""
        budget = TokenBudget(threshold=5000, hard_cap=15000, estimated_tokens=4500)

        assert budget.threshold == 5000
        assert budget.hard_cap == 15000
        assert budget.estimated_tokens == 4500

    def test_budget_used_under_threshold(self):
        """Test budget_used calculation when under threshold."""
        budget = TokenBudget(threshold=4000, hard_cap=12000, estimated_tokens=2000)

        assert budget.budget_used == 0.5  # 2000 / 4000

    def test_budget_used_over_threshold(self):
        """Test budget_used calculation when over threshold."""
        budget = TokenBudget(threshold=4000, hard_cap=12000, estimated_tokens=6000)

        assert budget.budget_used == 1.5  # 6000 / 4000

    def test_summary_mode_false(self):
        """Test summary_mode is False when under threshold."""
        budget = TokenBudget(threshold=4000, hard_cap=12000, estimated_tokens=3000)

        assert budget.summary_mode is False

    def test_summary_mode_true(self):
        """Test summary_mode is True when over threshold."""
        budget = TokenBudget(threshold=4000, hard_cap=12000, estimated_tokens=5000)

        assert budget.summary_mode is True

    def test_summary_mode_exact_threshold(self):
        """Test summary_mode at exact threshold."""
        budget = TokenBudget(threshold=4000, hard_cap=12000, estimated_tokens=4000)

        assert budget.summary_mode is False  # Not > threshold

    def test_exceeds_hard_cap_false(self):
        """Test exceeds_hard_cap is False when under hard cap."""
        budget = TokenBudget(threshold=4000, hard_cap=12000, estimated_tokens=10000)

        assert budget.exceeds_hard_cap is False

    def test_exceeds_hard_cap_true(self):
        """Test exceeds_hard_cap is True when over hard cap."""
        budget = TokenBudget(threshold=4000, hard_cap=12000, estimated_tokens=15000)

        assert budget.exceeds_hard_cap is True

    def test_hard_cap_validation_error(self):
        """Test validation error when hard_cap < threshold."""
        with pytest.raises(ValueError, match="hard_cap must be >= threshold"):
            TokenBudget(threshold=10000, hard_cap=5000, estimated_tokens=1000)

    def test_negative_threshold_error(self):
        """Test validation error for negative threshold."""
        with pytest.raises(ValidationError):
            TokenBudget(threshold=-1000, hard_cap=12000, estimated_tokens=1000)

    def test_negative_estimated_tokens_error(self):
        """Test validation error for negative estimated tokens."""
        with pytest.raises(ValidationError):
            TokenBudget(threshold=4000, hard_cap=12000, estimated_tokens=-500)


class TestBudgetMetadata:
    """Test suite for BudgetMetadata model."""

    def test_create_budget_metadata(self):
        """Test creating budget metadata."""
        metadata = BudgetMetadata(
            threshold_used=4000,
            estimated_tokens=6000,
            budget_ratio=1.5,
            action_taken="summarized",
            reason="Response exceeded token threshold",
        )

        assert metadata.threshold_used == 4000
        assert metadata.estimated_tokens == 6000
        assert metadata.budget_ratio == 1.5
        assert metadata.action_taken == "summarized"
        assert metadata.reason == "Response exceeded token threshold"

    def test_budget_metadata_allowed_action(self):
        """Test budget metadata for allowed action."""
        metadata = BudgetMetadata(
            threshold_used=4000,
            estimated_tokens=2000,
            budget_ratio=0.5,
            action_taken="allowed",
            reason="Response within budget",
        )

        assert metadata.action_taken == "allowed"
        assert metadata.budget_ratio == 0.5

    def test_budget_metadata_paginated_action(self):
        """Test budget metadata for paginated action."""
        metadata = BudgetMetadata(
            threshold_used=4000,
            estimated_tokens=8000,
            budget_ratio=2.0,
            action_taken="paginated",
            reason="List response split into pages",
        )

        assert metadata.action_taken == "paginated"


class TestTokenEstimationResult:
    """Test suite for TokenEstimationResult model."""

    def test_create_estimation_result(self):
        """Test creating token estimation result."""
        result = TokenEstimationResult(
            text_length=10000,
            estimated_tokens=2500,
            estimation_method="character-based",
            overhead_tokens=200,
        )

        assert result.text_length == 10000
        assert result.estimated_tokens == 2500
        assert result.estimation_method == "character-based"
        assert result.overhead_tokens == 200

    def test_total_tokens_calculation(self):
        """Test total_tokens includes overhead."""
        result = TokenEstimationResult(text_length=8000, estimated_tokens=2000, overhead_tokens=300)

        assert result.total_tokens == 2300  # 2000 + 300

    def test_estimation_result_defaults(self):
        """Test estimation result with default values."""
        result = TokenEstimationResult(text_length=5000, estimated_tokens=1250)

        assert result.estimation_method == "character-based"
        assert result.overhead_tokens == 200
        assert result.total_tokens == 1450

    def test_estimation_result_zero_overhead(self):
        """Test estimation with zero overhead."""
        result = TokenEstimationResult(text_length=4000, estimated_tokens=1000, overhead_tokens=0)

        assert result.total_tokens == 1000


class TestTokenBudgetConfig:
    """Test suite for TokenBudgetConfig model."""

    def test_create_config_defaults(self):
        """Test creating config with default values."""
        config = TokenBudgetConfig()

        assert config.output_token_threshold == 4000
        assert config.hard_output_token_cap == 12000
        assert config.default_page_size == 50
        assert config.max_page_size == 200
        assert config.enable_summarization is True
        assert config.enable_pagination is True

    def test_create_config_custom_values(self):
        """Test creating config with custom values."""
        config = TokenBudgetConfig(
            output_token_threshold=5000,
            hard_output_token_cap=15000,
            default_page_size=100,
            max_page_size=500,
            enable_summarization=False,
            enable_pagination=True,
        )

        assert config.output_token_threshold == 5000
        assert config.hard_output_token_cap == 15000
        assert config.default_page_size == 100
        assert config.max_page_size == 500
        assert config.enable_summarization is False

    def test_config_hard_cap_validation_error(self):
        """Test validation error when hard_cap < threshold."""
        with pytest.raises(
            ValueError, match="hard_output_token_cap must be >= output_token_threshold"
        ):
            TokenBudgetConfig(output_token_threshold=10000, hard_output_token_cap=5000)

    def test_config_max_page_size_validation_error(self):
        """Test validation error when max_page_size < default_page_size."""
        with pytest.raises(ValueError, match="max_page_size must be >= default_page_size"):
            TokenBudgetConfig(default_page_size=100, max_page_size=50)

    def test_config_page_size_bounds(self):
        """Test page size boundary validation."""
        # default_page_size must be >= 1 and <= 200
        with pytest.raises(ValidationError):
            TokenBudgetConfig(default_page_size=0)

        with pytest.raises(ValidationError):
            TokenBudgetConfig(default_page_size=201)

    def test_config_summarization_disabled(self):
        """Test config with summarization disabled."""
        config = TokenBudgetConfig(enable_summarization=False)

        assert config.enable_summarization is False
        assert config.enable_pagination is True  # Unaffected

    def test_config_pagination_disabled(self):
        """Test config with pagination disabled."""
        config = TokenBudgetConfig(enable_pagination=False)

        assert config.enable_pagination is False
        assert config.enable_summarization is True  # Unaffected


class TestEndpointBudgetOverride:
    """Test suite for EndpointBudgetOverride model."""

    def test_create_override_all_fields(self):
        """Test creating override with all fields."""
        override = EndpointBudgetOverride(
            endpoint_pattern="/api/v1/listings",
            threshold=8000,
            hard_cap=20000,
            page_size=25,
            summarization_enabled=False,
            pagination_enabled=True,
        )

        assert override.endpoint_pattern == "/api/v1/listings"
        assert override.threshold == 8000
        assert override.hard_cap == 20000
        assert override.page_size == 25
        assert override.summarization_enabled is False
        assert override.pagination_enabled is True

    def test_create_override_partial_fields(self):
        """Test creating override with only some fields."""
        override = EndpointBudgetOverride(endpoint_pattern="/api/v1/bookings", threshold=6000)

        assert override.endpoint_pattern == "/api/v1/bookings"
        assert override.threshold == 6000
        assert override.hard_cap is None
        assert override.page_size is None
        assert override.summarization_enabled is None
        assert override.pagination_enabled is None

    def test_override_threshold_only(self):
        """Test override with only threshold."""
        override = EndpointBudgetOverride(endpoint_pattern="/api/v1/financial", threshold=10000)

        assert override.threshold == 10000
        assert override.hard_cap is None

    def test_override_page_size_bounds(self):
        """Test page size validation in override."""
        # page_size must be >= 1 and <= 200
        with pytest.raises(ValidationError):
            EndpointBudgetOverride(endpoint_pattern="/test", page_size=0)

        with pytest.raises(ValidationError):
            EndpointBudgetOverride(endpoint_pattern="/test", page_size=201)

    def test_override_negative_threshold(self):
        """Test validation error for negative threshold."""
        with pytest.raises(ValidationError):
            EndpointBudgetOverride(endpoint_pattern="/test", threshold=-1000)

    def test_override_wildcard_pattern(self):
        """Test override with wildcard pattern."""
        override = EndpointBudgetOverride(endpoint_pattern="/api/v1/*", threshold=5000)

        assert override.endpoint_pattern == "/api/v1/*"

    def test_override_boolean_flags(self):
        """Test override with boolean flags."""
        override = EndpointBudgetOverride(
            endpoint_pattern="/api/test", summarization_enabled=True, pagination_enabled=False
        )

        assert override.summarization_enabled is True
        assert override.pagination_enabled is False
