"""Integration test configuration and fixtures.

Provides shared fixtures for integration testing including TestClient setup
and mocked authentication for testing API endpoints end-to-end.
"""

from collections.abc import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.api.main import app


@pytest.fixture
def test_client() -> TestClient:
    """Create FastAPI TestClient for integration tests.

    Returns:
        TestClient configured with the FastAPI app
    """
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for integration tests.

    Yields:
        AsyncClient for async endpoint testing
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def valid_api_key() -> str:
    """Provide a valid API key for authenticated requests.

    Returns:
        Test API key that passes authentication
    """
    return "mcp_test_key_for_integration_testing_12345"


@pytest.fixture
def auth_headers(valid_api_key: str) -> dict[str, str]:
    """Create authentication headers for integration tests.

    Args:
        valid_api_key: Valid API key fixture

    Returns:
        Dictionary with X-API-Key header
    """
    return {"X-API-Key": valid_api_key}


@pytest.fixture
def correlation_id_headers() -> dict[str, str]:
    """Create correlation ID headers for request tracing.

    Returns:
        Dictionary with X-Correlation-ID header
    """
    return {"X-Correlation-ID": "test-correlation-id-integration"}
