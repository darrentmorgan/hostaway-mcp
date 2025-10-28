"""Performance test configuration and fixtures.

Provides utilities for measuring middleware overhead, response times,
and ensuring no performance degradation from feature changes.
"""

import time
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def test_client() -> TestClient:
    """Create FastAPI TestClient for performance tests.

    Returns:
        TestClient configured with the FastAPI app
    """
    return TestClient(app)


@pytest.fixture
def performance_threshold_ms() -> int:
    """Define acceptable response time threshold.

    Returns:
        Maximum acceptable response time in milliseconds (500ms target)
    """
    return 500


@pytest.fixture
def measure_response_time() -> Callable[[Callable[[], Any]], float]:
    """Create a utility function to measure response time.

    Returns:
        Function that measures execution time of a callable in milliseconds
    """

    def _measure(func: Callable[[], Any]) -> float:
        """Measure execution time of a function.

        Args:
            func: Function to measure

        Returns:
            Execution time in milliseconds
        """
        start_time = time.perf_counter()
        func()
        end_time = time.perf_counter()
        return (end_time - start_time) * 1000  # Convert to ms

    return _measure


@pytest.fixture
def valid_api_key() -> str:
    """Provide a valid API key for authenticated performance tests.

    Returns:
        Test API key that passes authentication
    """
    return "mcp_test_key_for_performance_testing_12345"


@pytest.fixture
def auth_headers(valid_api_key: str) -> dict[str, str]:
    """Create authentication headers for performance tests.

    Args:
        valid_api_key: Valid API key fixture

    Returns:
        Dictionary with X-API-Key header
    """
    return {"X-API-Key": valid_api_key}
