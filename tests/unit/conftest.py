"""Unit test configuration and fixtures.

Provides helpers for testing rate limit state management, middleware logic,
and isolated component behavior without full integration.
"""

from datetime import UTC, datetime
from typing import Any

import pytest


@pytest.fixture
def rate_limit_state() -> dict[str, Any]:
    """Create mock rate limit state for unit tests.

    Returns:
        Dictionary with rate limit state (count, window_start, limit)
    """
    return {
        "count": 5,
        "window_start": datetime.now(UTC).timestamp(),
        "limit": 15,
    }


@pytest.fixture
def rate_limit_headers_expected() -> dict[str, str]:
    """Define expected rate limit header format.

    Returns:
        Dictionary with expected header names
    """
    return {
        "X-RateLimit-Limit": "15",
        "X-RateLimit-Remaining": "10",
        "X-RateLimit-Reset": "1698765432",  # Example Unix timestamp
    }


@pytest.fixture
def mock_rate_limiter_state() -> dict[str, Any]:
    """Create comprehensive rate limiter state for testing.

    Returns:
        Dictionary with IP-based and account-based rate limit states
    """
    current_time = datetime.now(UTC).timestamp()
    return {
        "ip_based": {
            "192.168.1.100": {"count": 5, "window_start": current_time, "limit": 15},
            "192.168.1.101": {"count": 12, "window_start": current_time, "limit": 15},
        },
        "account_based": {
            "org-123": {"count": 8, "window_start": current_time, "limit": 20},
            "org-456": {"count": 15, "window_start": current_time, "limit": 20},
        },
    }
