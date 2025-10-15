"""Unit tests for token_estimator module.

Tests character-based token estimation with 20% safety margin,
budget checking, and page size calculations.
"""

import pytest

from src.utils.token_estimator import (
    calculate_safe_page_size,
    check_token_budget,
    estimate_reduction_needed,
    estimate_tokens,
    estimate_tokens_from_dict,
    estimate_tokens_from_list,
)


class TestEstimateTokens:
    """Test basic token estimation functionality."""

    def test_estimate_tokens_empty_string(self) -> None:
        """Test estimation for empty string."""
        result = estimate_tokens("")
        assert result == 0

    def test_estimate_tokens_short_text(self) -> None:
        """Test estimation for short text."""
        # "Hello world" = 11 chars
        # Base: 11/4 = 2.75 → 2
        # Safety: 2 * 0.20 = 0.4
        # Total: 2 + 0.4 = 2.4 → 2
        result = estimate_tokens("Hello world")
        assert result >= 2
        assert result <= 5  # Reasonable upper bound

    def test_estimate_tokens_exact_4_char_boundary(self) -> None:
        """Test estimation at exact 4-character boundary."""
        # 4 chars exactly
        result = estimate_tokens("test")
        # Base: 4/4 = 1
        # Safety: 1 * 0.20 = 0.2
        # Total: 1.2 → 1
        assert result >= 1
        assert result <= 2

    def test_estimate_tokens_1000_chars(self) -> None:
        """Test estimation for 1000 characters."""
        text = "A" * 1000
        result = estimate_tokens(text)
        # Base: 1000/4 = 250
        # Safety: 250 * 0.20 = 50
        # Total: 300
        assert result == 300

    def test_estimate_tokens_includes_safety_margin(self) -> None:
        """Test that estimates include 20% safety margin."""
        # 100 chars
        text = "x" * 100
        result = estimate_tokens(text)

        # Without safety: 100/4 = 25
        # With 20% safety: 25 + 5 = 30
        assert result == 30

    def test_estimate_tokens_special_characters(self) -> None:
        """Test estimation with special characters."""
        text = "Hello 世界! @#$%^&*()"
        result = estimate_tokens(text)
        # Should count all characters including special ones
        assert result > 0

    def test_estimate_tokens_multiline(self) -> None:
        """Test estimation for multiline text."""
        text = """Line 1
Line 2
Line 3"""
        result = estimate_tokens(text)
        assert result > 0


class TestEstimateTokensFromDict:
    """Test token estimation from dictionary objects."""

    def test_estimate_tokens_from_dict_empty(self) -> None:
        """Test estimation for empty dict."""
        result = estimate_tokens_from_dict({})
        # Empty dict → "{}" = 2 chars
        assert result >= 0
        assert result <= 2

    def test_estimate_tokens_from_dict_simple(self) -> None:
        """Test estimation for simple dict."""
        obj = {"id": "BK12345", "status": "confirmed"}
        result = estimate_tokens_from_dict(obj)
        # JSON: {"id":"BK12345","status":"confirmed"} ≈ 38 chars
        # Estimate: 38/4 = 9.5 + 20% = 11.4 → 11
        assert result >= 10
        assert result <= 15

    def test_estimate_tokens_from_dict_nested(self) -> None:
        """Test estimation for nested dict."""
        obj = {
            "id": "BK12345",
            "guest": {"name": "John Doe", "email": "john@example.com"},
        }
        result = estimate_tokens_from_dict(obj)
        assert result > 0

    def test_estimate_tokens_from_dict_with_arrays(self) -> None:
        """Test estimation for dict with arrays."""
        obj = {
            "id": "BK12345",
            "amenities": ["WiFi", "Kitchen", "Parking"],
        }
        result = estimate_tokens_from_dict(obj)
        assert result > 0


class TestEstimateTokensFromList:
    """Test token estimation from list of objects."""

    def test_estimate_tokens_from_list_empty(self) -> None:
        """Test estimation for empty list."""
        result = estimate_tokens_from_list([])
        # Empty list → "[]" = 2 chars
        assert result >= 0
        assert result <= 2

    def test_estimate_tokens_from_list_single_item(self) -> None:
        """Test estimation for single-item list."""
        items = [{"id": "1", "name": "Item 1"}]
        result = estimate_tokens_from_list(items)
        assert result > 0

    def test_estimate_tokens_from_list_multiple_items(self) -> None:
        """Test estimation for multiple items."""
        items = [
            {"id": "1", "name": "Item 1"},
            {"id": "2", "name": "Item 2"},
            {"id": "3", "name": "Item 3"},
        ]
        result = estimate_tokens_from_list(items)
        # JSON array should be larger than single item
        assert result > 20

    def test_estimate_tokens_from_list_scales_linearly(self) -> None:
        """Test that estimation scales roughly linearly with item count."""
        items_10 = [{"id": str(i)} for i in range(10)]
        items_20 = [{"id": str(i)} for i in range(20)]

        result_10 = estimate_tokens_from_list(items_10)
        result_20 = estimate_tokens_from_list(items_20)

        # 20 items should be roughly 2x the tokens of 10 items
        assert 1.5 <= result_20 / result_10 <= 2.5


class TestCheckTokenBudget:
    """Test token budget checking functionality."""

    def test_check_token_budget_under_threshold(self) -> None:
        """Test budget check when under threshold."""
        text = "Hello" * 100  # ~500 chars → ~150 tokens
        estimated, exceeds, ratio = check_token_budget(text, threshold=4000)

        assert estimated < 4000
        assert exceeds is False
        assert 0.0 < ratio < 1.0

    def test_check_token_budget_over_threshold(self) -> None:
        """Test budget check when over threshold."""
        text = "Hello" * 5000  # ~25k chars → ~7500 tokens
        estimated, exceeds, ratio = check_token_budget(text, threshold=4000)

        assert estimated > 4000
        assert exceeds is True
        assert ratio > 1.0

    def test_check_token_budget_exactly_at_threshold(self) -> None:
        """Test budget check at exact threshold."""
        # Create text that's approximately 4000 tokens
        # 4000 tokens * 4 chars/token / 1.2 (safety margin) ≈ 13333 chars
        text = "x" * 13333
        estimated, exceeds, ratio = check_token_budget(text, threshold=4000)

        # Should be very close to 4000 tokens
        assert 3900 <= estimated <= 4100
        # Ratio should be close to 1.0
        assert 0.95 <= ratio <= 1.05

    def test_check_token_budget_custom_threshold(self) -> None:
        """Test budget check with custom threshold."""
        text = "Hello" * 100
        estimated, exceeds, ratio = check_token_budget(text, threshold=100)

        assert estimated > 100
        assert exceeds is True

    def test_check_token_budget_zero_threshold(self) -> None:
        """Test budget check with zero threshold."""
        text = "Hello"
        estimated, exceeds, ratio = check_token_budget(text, threshold=0)

        assert exceeds is True
        assert ratio == 0.0  # Avoid division by zero


class TestEstimateReductionNeeded:
    """Test reduction calculation functionality."""

    def test_estimate_reduction_needed_over_threshold(self) -> None:
        """Test reduction calculation when over threshold."""
        tokens_to_reduce, ratio = estimate_reduction_needed(6000, target_threshold=4000)

        assert tokens_to_reduce == 2000
        assert ratio == pytest.approx(0.333, rel=0.01)  # 2000/6000 = 0.333

    def test_estimate_reduction_needed_under_threshold(self) -> None:
        """Test reduction calculation when under threshold."""
        tokens_to_reduce, ratio = estimate_reduction_needed(3000, target_threshold=4000)

        assert tokens_to_reduce == 0
        assert ratio == 0.0

    def test_estimate_reduction_needed_exactly_at_threshold(self) -> None:
        """Test reduction calculation at exact threshold."""
        tokens_to_reduce, ratio = estimate_reduction_needed(4000, target_threshold=4000)

        assert tokens_to_reduce == 0
        assert ratio == 0.0

    def test_estimate_reduction_needed_large_excess(self) -> None:
        """Test reduction calculation with large excess."""
        tokens_to_reduce, ratio = estimate_reduction_needed(12000, target_threshold=4000)

        assert tokens_to_reduce == 8000
        assert ratio == pytest.approx(0.666, rel=0.01)  # 8000/12000 = 0.666


class TestCalculateSafePageSize:
    """Test safe page size calculation."""

    def test_calculate_safe_page_size_small_items(self) -> None:
        """Test page size calculation for small items."""
        # Small items (50 tokens each)
        page_size = calculate_safe_page_size(
            avg_item_tokens=50,
            target_threshold=4000,
            overhead_tokens=200,
        )

        # (4000 - 200) / 50 = 76
        assert page_size == 76

    def test_calculate_safe_page_size_large_items(self) -> None:
        """Test page size calculation for large items."""
        # Large items (500 tokens each)
        page_size = calculate_safe_page_size(
            avg_item_tokens=500,
            target_threshold=4000,
            overhead_tokens=200,
        )

        # (4000 - 200) / 500 = 7.6 → 7
        assert page_size == 7

    def test_calculate_safe_page_size_very_large_items(self) -> None:
        """Test page size calculation for very large items."""
        # Very large items (5000 tokens each)
        page_size = calculate_safe_page_size(
            avg_item_tokens=5000,
            target_threshold=4000,
            overhead_tokens=200,
        )

        # Would be negative, but minimum is 1
        assert page_size == 1

    def test_calculate_safe_page_size_custom_overhead(self) -> None:
        """Test page size calculation with custom overhead."""
        page_size = calculate_safe_page_size(
            avg_item_tokens=100,
            target_threshold=4000,
            overhead_tokens=1000,  # High overhead
        )

        # (4000 - 1000) / 100 = 30
        assert page_size == 30

    def test_calculate_safe_page_size_minimum_one(self) -> None:
        """Test that page size is always at least 1."""
        page_size = calculate_safe_page_size(
            avg_item_tokens=10000,
            target_threshold=4000,
        )

        assert page_size >= 1


class TestTokenEstimatorPerformance:
    """Test token estimator performance requirements."""

    def test_estimate_tokens_performance_under_20ms(self) -> None:
        """Test that token estimation completes in under 20ms (spec requirement)."""
        import timeit

        # Create typical API response (~1000 chars)
        text = "x" * 1000

        def estimate_test() -> None:
            estimate_tokens(text)

        # Run 1000 iterations and measure average time
        execution_time = timeit.timeit(estimate_test, number=1000)
        avg_time_ms = (execution_time / 1000) * 1000

        # Should be well under 20ms per operation
        assert avg_time_ms < 20.0

    def test_estimate_from_dict_performance_under_20ms(self) -> None:
        """Test that dict estimation completes in under 20ms."""
        import timeit

        # Create typical object
        obj = {
            "id": "BK12345",
            "status": "confirmed",
            "guestName": "John Doe",
            "checkInDate": "2025-11-01",
            "checkOutDate": "2025-11-05",
            "totalPrice": 1200.0,
        }

        def estimate_test() -> None:
            estimate_tokens_from_dict(obj)

        # Run 1000 iterations and measure average time
        execution_time = timeit.timeit(estimate_test, number=1000)
        avg_time_ms = (execution_time / 1000) * 1000

        # Should be well under 20ms per operation
        assert avg_time_ms < 20.0
