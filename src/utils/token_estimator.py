"""Token estimation utility for Claude context window management.

Character-based estimation with 20% safety margin.
Based on research.md R001: 1 token ≈ 4 characters heuristic.
"""

import json
from typing import Any


def estimate_tokens(text: str) -> int:
    """Estimate Claude token count from text.

    Uses 4 characters per token heuristic with 20% safety margin.
    Target performance: <20ms for typical API responses.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count (includes 20% safety margin)

    Example:
        >>> estimate_tokens("Hello world")
        4  # 11 chars / 4 = 2.75 → 3 base + 20% = 3.6 → 4 tokens
        >>> estimate_tokens("A" * 1000)
        300  # 1000 / 4 = 250 base + 20% = 300 tokens
    """
    char_count = len(text)
    base_estimate = char_count / 4
    safety_margin = base_estimate * 0.20
    return int(base_estimate + safety_margin)


def estimate_tokens_from_dict(obj: dict[str, Any]) -> int:
    """Estimate tokens from a dictionary object.

    Serializes dict to JSON and estimates tokens from the string representation.

    Args:
        obj: Dictionary to estimate tokens for

    Returns:
        Estimated token count

    Example:
        >>> estimate_tokens_from_dict({"id": "BK12345", "status": "confirmed"})
        12  # JSON string ~40 chars / 4 = 10 + 20% = 12
    """
    json_str = json.dumps(obj, separators=(",", ":"))
    return estimate_tokens(json_str)


def estimate_tokens_from_list(items: list[dict[str, Any]]) -> int:
    """Estimate tokens from a list of objects.

    Args:
        items: List of dictionaries to estimate tokens for

    Returns:
        Estimated token count for entire list

    Example:
        >>> items = [{"id": "1"}, {"id": "2"}]
        >>> estimate_tokens_from_list(items)
        7  # JSON array ~20 chars / 4 = 5 + 20% = 6
    """
    json_str = json.dumps(items, separators=(",", ":"))
    return estimate_tokens(json_str)


def check_token_budget(
    text: str,
    threshold: int = 4000,
) -> tuple[int, bool, float]:
    """Check if text exceeds token budget threshold.

    Args:
        text: Text to check
        threshold: Token budget threshold (default: 4000)

    Returns:
        Tuple of (estimated_tokens, exceeds_threshold, budget_used_ratio)

    Example:
        >>> check_token_budget("Hello" * 1000, threshold=4000)
        (1800, False, 0.45)  # 1800 tokens, within budget, 45% used
        >>> check_token_budget("Hello" * 2000, threshold=4000)
        (3600, False, 0.90)  # 3600 tokens, within budget, 90% used
        >>> check_token_budget("Hello" * 3000, threshold=4000)
        (5400, True, 1.35)  # 5400 tokens, exceeds budget, 135% used
    """
    estimated = estimate_tokens(text)
    exceeds = estimated > threshold
    budget_ratio = estimated / threshold if threshold > 0 else 0.0

    return estimated, exceeds, budget_ratio


def estimate_reduction_needed(
    current_tokens: int,
    target_threshold: int = 4000,
) -> tuple[int, float]:
    """Calculate token reduction needed to meet threshold.

    Args:
        current_tokens: Current estimated token count
        target_threshold: Target token threshold

    Returns:
        Tuple of (tokens_to_reduce, reduction_ratio)

    Example:
        >>> estimate_reduction_needed(6000, 4000)
        (2000, 0.33)  # Need to reduce by 2000 tokens (33% reduction)
        >>> estimate_reduction_needed(3000, 4000)
        (0, 0.0)  # Already under threshold
    """
    if current_tokens <= target_threshold:
        return 0, 0.0

    tokens_to_reduce = current_tokens - target_threshold
    reduction_ratio = tokens_to_reduce / current_tokens

    return tokens_to_reduce, reduction_ratio


def calculate_safe_page_size(
    avg_item_tokens: int,
    target_threshold: int = 4000,
    overhead_tokens: int = 200,
) -> int:
    """Calculate safe page size given average item token count.

    Args:
        avg_item_tokens: Average tokens per item in list
        target_threshold: Target token threshold
        overhead_tokens: Overhead tokens for metadata/envelope (default: 200)

    Returns:
        Recommended page size (minimum 1)

    Example:
        >>> calculate_safe_page_size(avg_item_tokens=50, target_threshold=4000)
        76  # (4000 - 200) / 50 = 76 items per page
        >>> calculate_safe_page_size(avg_item_tokens=500, target_threshold=4000)
        7  # (4000 - 200) / 500 = 7.6 → 7 items per page
    """
    available_tokens = target_threshold - overhead_tokens
    if available_tokens <= 0:
        return 1

    page_size = available_tokens // avg_item_tokens
    return max(1, page_size)
