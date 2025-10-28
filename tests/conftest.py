"""Shared pytest fixtures for all tests.

Provides common fixtures for testing Hostaway API client, authentication,
and MCP protocol endpoints.
"""

from datetime import UTC
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.mcp.config import HostawayConfig
from src.services.hostaway_client import HostawayClient


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client for usage tracking.

    This fixture prevents tests from trying to connect to a real Supabase instance.
    """
    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock())
    mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
        return_value=MagicMock(data={"id": "test-org-123", "name": "Test Org"})
    )
    return mock_client


@pytest.fixture(autouse=True)
def mock_supabase_for_all_tests(mock_supabase_client, monkeypatch):
    """Automatically mock Supabase for all tests to prevent connection errors.

    This autouse fixture ensures no test tries to connect to a real Supabase instance.
    """
    # Set cursor secret for pagination tests
    monkeypatch.setenv("CURSOR_SECRET", "test-cursor-secret-for-pagination")

    with patch(
        "src.services.supabase_client.get_supabase_client", return_value=mock_supabase_client
    ):
        with patch(
            "src.api.middleware.usage_tracking.get_supabase_client",
            return_value=mock_supabase_client,
        ):
            yield


@pytest.fixture
def test_config(monkeypatch: pytest.MonkeyPatch) -> HostawayConfig:
    """Create test configuration with environment variables.

    Returns:
        HostawayConfig configured for testing
    """
    monkeypatch.setenv("HOSTAWAY_ACCOUNT_ID", "test_account_123")
    monkeypatch.setenv("HOSTAWAY_SECRET_KEY", "test_secret_key_456")
    monkeypatch.setenv("HOSTAWAY_API_BASE_URL", "https://api.hostaway.com/v1")
    return HostawayConfig()  # type: ignore[call-arg]


@pytest.fixture
def mock_http_client() -> AsyncMock:
    """Create mock httpx.AsyncClient.

    Returns:
        Mock AsyncClient for testing HTTP interactions
    """
    mock = AsyncMock(spec=httpx.AsyncClient)
    mock.aclose = AsyncMock()
    return mock


@pytest.fixture
def mock_response() -> MagicMock:
    """Create mock httpx.Response.

    Returns:
        Mock Response for testing API responses
    """
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = {"status": "success", "result": {}}
    response.raise_for_status = MagicMock()
    response.text = ""
    return response


@pytest.fixture
def mock_token_manager() -> AsyncMock:
    """Create mock TokenManager for testing.

    Returns:
        Mock TokenManager that returns valid access token
    """
    from src.models.auth import AccessToken

    mock = AsyncMock()
    mock.get_token.return_value = AccessToken(
        access_token="test_token_abc123_xyz789_20chars",  # Must be >= 20 chars
        token_type="Bearer",
        expires_in=63072000,
        scope="general",
    )
    mock.invalidate_token = AsyncMock()
    return mock


@pytest.fixture
def mock_rate_limiter() -> MagicMock:
    """Create mock RateLimiter for testing.

    Returns:
        Mock RateLimiter that always allows requests
    """

    class MockAcquire:
        """Mock async context manager for rate limiter."""

        async def __aenter__(self) -> None:
            """Enter context."""

        async def __aexit__(self, *args: Any) -> None:
            """Exit context."""

    mock = MagicMock()
    mock.acquire.return_value = MockAcquire()
    return mock


@pytest.fixture
def mock_client(
    test_config: HostawayConfig,
    mock_token_manager: AsyncMock,
    mock_rate_limiter: MagicMock,
    mock_http_client: AsyncMock,
) -> HostawayClient:
    """Create mock HostawayClient for testing.

    Args:
        test_config: Test configuration
        mock_token_manager: Mock token manager
        mock_rate_limiter: Mock rate limiter
        mock_http_client: Mock HTTP client

    Returns:
        HostawayClient configured with mocks for testing
    """
    client = HostawayClient(
        config=test_config,
        token_manager=mock_token_manager,
        rate_limiter=mock_rate_limiter,
    )
    # Replace the internal HTTP client with mock
    client._client = mock_http_client
    return client


# Financial test data fixtures


@pytest.fixture
def mock_financial_report_response() -> dict[str, Any]:
    """Create mock Hostaway financial report response.

    Returns:
        Complete financial report data structure
    """
    return {
        "periodStart": "2025-10-01",
        "periodEnd": "2025-10-31",
        "periodType": "monthly",
        "listingId": None,  # All properties
        "revenue": {
            "totalRevenue": 12500.00,
            "directBookings": 3000.00,
            "airbnb": 6000.00,
            "vrbo": 2500.00,
            "bookingCom": 1000.00,
            "other": 0.00,
        },
        "expenses": {
            "totalExpenses": 3250.00,
            "cleaning": 1200.00,
            "maintenance": 500.00,
            "utilities": 300.00,
            "platformFees": 1000.00,
            "supplies": 200.00,
            "other": 50.00,
        },
        "netIncome": 9250.00,
        "totalBookings": 15,
        "totalNightsBooked": 75,
        "averageDailyRate": 166.67,
        "occupancyRate": 80.65,
        "currency": "USD",
    }


@pytest.fixture
def mock_property_financial_response() -> dict[str, Any]:
    """Create mock property-specific financial report.

    Returns:
        Property-specific financial report data
    """
    return {
        "periodStart": "2025-10-01",
        "periodEnd": "2025-10-31",
        "periodType": "monthly",
        "listingId": 12345,
        "listingName": "Cozy Downtown Apartment",
        "revenue": {
            "totalRevenue": 4500.00,
            "directBookings": 1500.00,
            "airbnb": 2500.00,
            "vrbo": 500.00,
            "bookingCom": 0.00,
            "other": 0.00,
        },
        "expenses": {
            "totalExpenses": 1200.00,
            "cleaning": 600.00,
            "maintenance": 200.00,
            "utilities": 150.00,
            "platformFees": 200.00,
            "supplies": 50.00,
            "other": 0.00,
        },
        "netIncome": 3300.00,
        "totalBookings": 6,
        "totalNightsBooked": 28,
        "averageDailyRate": 160.71,
        "occupancyRate": 90.32,
        "currency": "USD",
    }


# Listing test data fixtures


@pytest.fixture
def mock_listing_response() -> dict[str, Any]:
    """Create mock listing response.

    Returns:
        Complete listing data structure
    """
    return {
        "id": 12345,
        "name": "Cozy Downtown Apartment",
        "listingName": "Cozy Downtown Apartment",
        "internalName": "Apartment A",
        "address": "123 Main St, San Francisco, CA 94102",
        "bedrooms": 2,
        "bathrooms": 1,
        "maxGuests": 4,
        "status": "active",
        "currency": "USD",
        "basePrice": 150.00,
    }


@pytest.fixture
def mock_listings_response() -> list[dict[str, Any]]:
    """Create mock listings list response.

    Returns:
        List of listing data structures
    """
    return [
        {
            "id": 12345,
            "name": "Cozy Downtown Apartment",
            "bedrooms": 2,
            "bathrooms": 1,
            "maxGuests": 4,
            "status": "active",
        },
        {
            "id": 12346,
            "name": "Beachfront Villa",
            "bedrooms": 4,
            "bathrooms": 3,
            "maxGuests": 8,
            "status": "active",
        },
    ]


# Booking test data fixtures


@pytest.fixture
def mock_booking_response() -> dict[str, Any]:
    """Create mock booking response.

    Returns:
        Complete booking data structure
    """
    return {
        "id": 98765,
        "listingId": 12345,
        "channelId": 2001,
        "channelName": "airbnb",
        "guestName": "John Doe",
        "guestEmail": "john.doe@example.com",
        "checkIn": "2025-10-15",
        "checkOut": "2025-10-20",
        "numberOfGuests": 2,
        "status": "confirmed",
        "totalPrice": 750.00,
        "currency": "USD",
    }


@pytest.fixture
def mock_bookings_response() -> list[dict[str, Any]]:
    """Create mock bookings list response.

    Returns:
        List of booking data structures
    """
    return [
        {
            "id": 98765,
            "listingId": 12345,
            "guestName": "John Doe",
            "checkIn": "2025-10-15",
            "checkOut": "2025-10-20",
            "status": "confirmed",
        },
        {
            "id": 98766,
            "listingId": 12346,
            "guestName": "Jane Smith",
            "checkIn": "2025-10-22",
            "checkOut": "2025-10-27",
            "status": "confirmed",
        },
    ]


# Middleware testing fixtures for 008-fix-issues-identified


@pytest.fixture
def mock_request():
    """Create mock FastAPI Request for middleware testing.

    Returns:
        Mock Request with correlation_id and state
    """
    from unittest.mock import MagicMock

    from starlette.requests import Request

    request = MagicMock(spec=Request)
    request.state = MagicMock()
    request.state.correlation_id = "test-correlation-id-12345"
    request.url = MagicMock()
    request.url.path = "/api/test"
    request.headers = {}
    return request


@pytest.fixture
def mock_rate_limit_state():
    """Create mock rate limit state for testing header calculations.

    Returns:
        Dictionary with rate limit state (count, window_start)
    """
    from datetime import datetime

    return {
        "count": 5,
        "window_start": datetime.now(UTC).timestamp(),
        "limit": 15,
    }
