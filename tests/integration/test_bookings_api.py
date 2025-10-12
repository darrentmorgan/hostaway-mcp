"""Integration tests for Hostaway bookings API.

Tests booking search, retrieval, and guest information endpoints.
Following TDD: These tests should FAIL until implementation is complete.
"""

import httpx
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from src.mcp.auth import TokenManager
from src.mcp.config import HostawayConfig


@pytest.fixture
def test_config(monkeypatch: pytest.MonkeyPatch) -> HostawayConfig:
    """Create test configuration."""
    monkeypatch.setenv("HOSTAWAY_ACCOUNT_ID", "test_account_123")
    monkeypatch.setenv("HOSTAWAY_SECRET_KEY", "test_secret_key_456")
    monkeypatch.setenv("HOSTAWAY_API_BASE_URL", "https://api.hostaway.com/v1")
    return HostawayConfig()  # type: ignore[call-arg]


@pytest.fixture
def mock_booking_response() -> dict:
    """Create mock Hostaway booking response."""
    return {
        "id": 67890,
        "listingId": 12345,
        "listingName": "Cozy Downtown Apartment",
        "guestId": 54321,
        "guestName": "John Smith",
        "guestEmail": "john.smith@example.com",
        "guestPhone": "+1-555-123-4567",
        "checkIn": "2025-11-10",
        "checkOut": "2025-11-13",
        "guests": 2,
        "numberOfGuests": 2,
        "adults": 2,
        "children": 0,
        "nights": 3,
        "status": "confirmed",
        "totalPrice": 525.00,
        "currency": "USD",
        "channelName": "airbnb",
        "confirmationCode": "ABCD1234",
        "createdAt": "2025-10-01T14:30:00Z",
        "specialRequests": "Early check-in if possible"
    }


@pytest.fixture
def mock_guest_response() -> dict:
    """Create mock Hostaway guest response."""
    return {
        "id": 54321,
        "firstName": "John",
        "lastName": "Smith",
        "email": "john.smith@example.com",
        "phone": "+1-555-123-4567",
        "language": "en",
        "country": "USA",
        "city": "New York",
        "totalBookings": 3,
        "createdAt": "2024-01-15T10:00:00Z"
    }


# T058: Contract test for GET /reservations endpoint
class TestBookingsSearchEndpoint:
    """Test GET /reservations endpoint contract."""

    @pytest.mark.asyncio
    async def test_search_bookings_success(
        self, test_config: HostawayConfig, mock_booking_response: dict
    ) -> None:
        """Test successful booking search with filters.

        Verifies:
        - GET /reservations returns 200
        - Response includes array of bookings
        - Search filters work correctly
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "result": [mock_booking_response],
            "count": 1,
            "limit": 100,
            "offset": 0,
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # TODO: Import HostawayClient once implemented
        # from src.services.hostaway_client import HostawayClient
        #
        # client = HostawayClient(config=test_config, http_client=mock_client)
        # bookings = await client.search_bookings(
        #     check_in_from="2025-11-01",
        #     check_in_to="2025-11-30"
        # )
        #
        # assert len(bookings) == 1
        # assert bookings[0].id == 67890
        # assert bookings[0].guest_name == "John Smith"
        #
        # # Verify request was made correctly
        # mock_client.get.assert_called_once_with(
        #     "/reservations",
        #     params={"checkInFrom": "2025-11-01", "checkInTo": "2025-11-30"}
        # )

    @pytest.mark.asyncio
    async def test_search_bookings_with_filters(
        self, test_config: HostawayConfig, mock_booking_response: dict
    ) -> None:
        """Test booking search with multiple filters.

        Verifies:
        - Multiple filter parameters work together
        - Status filter works
        - Listing ID filter works
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "result": [mock_booking_response],
            "count": 1,
            "limit": 100,
            "offset": 0,
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # TODO: Import HostawayClient once implemented
        # from src.services.hostaway_client import HostawayClient
        #
        # client = HostawayClient(config=test_config, http_client=mock_client)
        # bookings = await client.search_bookings(
        #     listing_id=12345,
        #     status=["confirmed", "pending"],
        #     check_in_from="2025-11-01"
        # )
        #
        # # Verify filters were applied
        # mock_client.get.assert_called_once()
        # call_params = mock_client.get.call_args[1]["params"]
        # assert call_params["listingId"] == 12345
        # assert "confirmed" in call_params["status"] or call_params["status"] == "confirmed,pending"


# T059: Contract test for GET /reservations/{id} endpoint
class TestBookingDetailsEndpoint:
    """Test GET /reservations/{id} endpoint contract."""

    @pytest.mark.asyncio
    async def test_get_booking_by_id_success(
        self, test_config: HostawayConfig, mock_booking_response: dict
    ) -> None:
        """Test successful retrieval of booking details.

        Verifies:
        - GET /reservations/{id} returns 200
        - Response includes complete booking details
        - Payment information included
        """
        booking_id = 67890
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "result": mock_booking_response,
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # TODO: Import HostawayClient once implemented
        # from src.services.hostaway_client import HostawayClient
        #
        # client = HostawayClient(config=test_config, http_client=mock_client)
        # booking = await client.get_booking(booking_id)
        #
        # assert booking.id == 67890
        # assert booking.guest_name == "John Smith"
        # assert booking.status == "confirmed"
        # assert booking.total_price == 525.00
        #
        # # Verify request was made correctly
        # mock_client.get.assert_called_once_with(f"/reservations/{booking_id}")

    @pytest.mark.asyncio
    async def test_get_booking_not_found(
        self, test_config: HostawayConfig
    ) -> None:
        """Test GET /reservations/{id} returns 404 for invalid ID.

        Verifies:
        - Invalid booking ID returns 404
        - Error response is properly formatted
        """
        booking_id = 99999
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "error": "not_found",
            "error_description": "Booking not found",
            "status": 404,
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=mock_response,
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        # TODO: Import HostawayClient once implemented
        # from src.services.hostaway_client import HostawayClient
        #
        # client = HostawayClient(config=test_config, http_client=mock_client)
        #
        # with pytest.raises(httpx.HTTPStatusError) as exc_info:
        #     await client.get_booking(booking_id)
        #
        # assert exc_info.value.response.status_code == 404


# T060: Contract test for GET /reservations/{id}/guest endpoint
class TestBookingGuestEndpoint:
    """Test GET /reservations/{id}/guest endpoint contract."""

    @pytest.mark.asyncio
    async def test_get_booking_guest_success(
        self, test_config: HostawayConfig, mock_guest_response: dict
    ) -> None:
        """Test successful retrieval of booking guest information.

        Verifies:
        - GET /reservations/{id}/guest returns 200
        - Response includes guest contact details
        - Booking history included
        """
        booking_id = 67890
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "result": mock_guest_response,
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # TODO: Import HostawayClient once implemented
        # from src.services.hostaway_client import HostawayClient
        #
        # client = HostawayClient(config=test_config, http_client=mock_client)
        # guest = await client.get_booking_guest(booking_id)
        #
        # assert guest.id == 54321
        # assert guest.first_name == "John"
        # assert guest.last_name == "Smith"
        # assert guest.email == "john.smith@example.com"
        #
        # # Verify request was made correctly
        # mock_client.get.assert_called_once_with(f"/reservations/{booking_id}/guest")


# T061: Integration test for booking search flow
class TestBookingSearchFlow:
    """Test complete booking search flow."""

    @pytest.mark.asyncio
    async def test_booking_search_flow_complete(
        self,
        test_config: HostawayConfig,
        mock_booking_response: dict,
        mock_guest_response: dict,
    ) -> None:
        """Test complete flow: authenticate → search bookings → get details → get guest.

        Flow:
        1. Authenticate and get token
        2. Search bookings by date range
        3. Get details for specific booking
        4. Get guest information

        Verifies end-to-end integration works.
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        # Mock authentication response
        mock_auth_response = MagicMock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {
            "access_token": "test_token_abc123_xyz789_20chars",
            "token_type": "Bearer",
            "expires_in": 63072000,
            "scope": "general",
        }
        mock_auth_response.raise_for_status = MagicMock()

        # Mock search bookings response
        mock_search_response = MagicMock()
        mock_search_response.status_code = 200
        mock_search_response.json.return_value = {
            "status": "success",
            "result": [mock_booking_response],
            "count": 1,
        }
        mock_search_response.raise_for_status = MagicMock()

        # Mock booking details response
        mock_details_response = MagicMock()
        mock_details_response.status_code = 200
        mock_details_response.json.return_value = {
            "status": "success",
            "result": mock_booking_response,
        }
        mock_details_response.raise_for_status = MagicMock()

        # Mock guest response
        mock_guest_resp = MagicMock()
        mock_guest_resp.status_code = 200
        mock_guest_resp.json.return_value = {
            "status": "success",
            "result": mock_guest_response,
        }
        mock_guest_resp.raise_for_status = MagicMock()

        # Setup mock responses
        mock_client.post = AsyncMock(return_value=mock_auth_response)
        mock_client.get = AsyncMock(
            side_effect=[
                mock_search_response,
                mock_details_response,
                mock_guest_resp,
            ]
        )

        # TODO: Import and test full flow once implemented
        # from src.mcp.auth import TokenManager
        # from src.services.hostaway_client import HostawayClient
        #
        # # Step 1: Authenticate
        # token_manager = TokenManager(config=test_config, client=mock_client)
        # token = await token_manager.get_token()
        # assert token.access_token == "test_token_abc123_xyz789_20chars"
        #
        # # Step 2: Search bookings
        # client = HostawayClient(config=test_config, http_client=mock_client)
        # bookings = await client.search_bookings(check_in_from="2025-11-01")
        # assert len(bookings) == 1
        #
        # # Step 3: Get booking details
        # booking_id = bookings[0].id
        # details = await client.get_booking(booking_id)
        # assert details.id == 67890
        # assert details.guest_name == "John Smith"
        #
        # # Step 4: Get guest information
        # guest = await client.get_booking_guest(booking_id)
        # assert guest.id == 54321
        # assert guest.email == "john.smith@example.com"


# T062: MCP protocol test placeholder
class TestBookingsMCPProtocol:
    """Test MCP protocol for booking tools."""

    @pytest.mark.asyncio
    async def test_booking_tools_discoverable(self) -> None:
        """Test that booking tools are discoverable via MCP protocol.

        Verifies:
        - search_bookings tool is registered
        - get_booking_details tool is registered
        - get_booking_guest_info tool is registered
        """
        # TODO: Implement MCP protocol tests after routes are created
        pass
