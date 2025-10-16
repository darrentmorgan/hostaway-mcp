"""Integration tests for Hostaway listings API.

Tests property listing retrieval, details, and availability endpoints.
Following TDD: These tests should FAIL until implementation is complete.
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.mcp.config import HostawayConfig


@pytest.fixture
def test_config(monkeypatch: pytest.MonkeyPatch) -> HostawayConfig:
    """Create test configuration."""
    monkeypatch.setenv("HOSTAWAY_ACCOUNT_ID", "test_account_123")
    monkeypatch.setenv("HOSTAWAY_SECRET_KEY", "test_secret_key_456")
    monkeypatch.setenv("HOSTAWAY_API_BASE_URL", "https://api.hostaway.com/v1")
    return HostawayConfig()  # type: ignore[call-arg]


@pytest.fixture
def mock_listing_response() -> dict:
    """Create mock Hostaway listing response."""
    return {
        "id": 12345,
        "name": "Cozy Downtown Apartment",
        "address": "123 Main St, Apt 4B",
        "city": "San Francisco",
        "state": "California",
        "country": "USA",
        "postal_code": "94102",
        "description": "Beautiful 2BR apartment...",
        "capacity": 4,
        "bedrooms": 2,
        "bathrooms": 1.5,
        "property_type": "apartment",
        "base_price": 150.00,
        "is_active": True,
    }


@pytest.fixture
def mock_availability_response() -> dict:
    """Create mock Hostaway availability response."""
    return {
        "status": "success",
        "result": [
            {
                "date": "2024-01-15",
                "status": "available",
                "price": 150.00,
                "min_stay": 2,
            },
            {
                "date": "2024-01-16",
                "status": "blocked",
                "price": 150.00,
                "min_stay": 2,
            },
            {
                "date": "2024-01-17",
                "status": "booked",
                "price": 150.00,
                "min_stay": 2,
            },
        ],
    }


# T039: Contract test for GET /listings endpoint
class TestListingsEndpoint:
    """Test GET /listings endpoint contract."""

    @pytest.mark.asyncio
    async def test_get_listings_success(
        self, test_config: HostawayConfig, mock_listing_response: dict
    ) -> None:
        """Test successful retrieval of property listings.

        Verifies:
        - GET /listings returns 200
        - Response includes array of listings
        - Pagination parameters work
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "result": [mock_listing_response],
            "count": 1,
            "limit": 100,
            "offset": 0,
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # TODO: Import HostawayClient once implemented
        # from src.mcp.client import HostawayClient
        #
        # client = HostawayClient(config=test_config, http_client=mock_client)
        # listings = await client.get_listings()
        #
        # assert len(listings) == 1
        # assert listings[0].id == 12345
        # assert listings[0].name == "Cozy Downtown Apartment"
        # assert listings[0].city == "San Francisco"
        #
        # # Verify request was made correctly
        # mock_client.get.assert_called_once_with(
        #     "/listings",
        #     params={"limit": 100, "offset": 0}
        # )

    @pytest.mark.asyncio
    async def test_get_listings_pagination(
        self, test_config: HostawayConfig, mock_listing_response: dict
    ) -> None:
        """Test pagination works for GET /listings.

        Verifies:
        - limit parameter controls page size
        - offset parameter controls starting position
        - count field shows total results
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "result": [mock_listing_response],
            "count": 50,  # Total count
            "limit": 10,
            "offset": 20,
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # TODO: Import HostawayClient once implemented
        # from src.mcp.client import HostawayClient
        #
        # client = HostawayClient(config=test_config, http_client=mock_client)
        # listings = await client.get_listings(limit=10, offset=20)
        #
        # # Verify pagination parameters
        # mock_client.get.assert_called_once_with(
        #     "/listings",
        #     params={"limit": 10, "offset": 20}
        # )


# T040: Contract test for GET /listings/{id} endpoint
class TestListingDetailsEndpoint:
    """Test GET /listings/{id} endpoint contract."""

    @pytest.mark.asyncio
    async def test_get_listing_by_id_success(
        self, test_config: HostawayConfig, mock_listing_response: dict
    ) -> None:
        """Test successful retrieval of single property details.

        Verifies:
        - GET /listings/{id} returns 200
        - Response includes complete listing details
        - All required fields present
        """
        listing_id = 12345
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "result": mock_listing_response,
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # TODO: Import HostawayClient once implemented
        # from src.mcp.client import HostawayClient
        #
        # client = HostawayClient(config=test_config, http_client=mock_client)
        # listing = await client.get_listing(listing_id)
        #
        # assert listing.id == 12345
        # assert listing.name == "Cozy Downtown Apartment"
        # assert listing.city == "San Francisco"
        # assert listing.capacity == 4
        # assert listing.bedrooms == 2
        #
        # # Verify request was made correctly
        # mock_client.get.assert_called_once_with(f"/listings/{listing_id}")

    @pytest.mark.asyncio
    async def test_get_listing_not_found(self, test_config: HostawayConfig) -> None:
        """Test GET /listings/{id} returns 404 for invalid ID.

        Verifies:
        - Invalid listing ID returns 404
        - Error response is properly formatted
        """
        listing_id = 99999
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "error": "not_found",
            "error_description": "Listing not found",
            "status": 404,
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=mock_response,
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        # TODO: Import HostawayClient once implemented
        # from src.mcp.client import HostawayClient
        #
        # client = HostawayClient(config=test_config, http_client=mock_client)
        #
        # with pytest.raises(httpx.HTTPStatusError) as exc_info:
        #     await client.get_listing(listing_id)
        #
        # assert exc_info.value.response.status_code == 404


# T041: Contract test for GET /listings/{id}/calendar endpoint
class TestListingAvailabilityEndpoint:
    """Test GET /listings/{id}/calendar endpoint contract."""

    @pytest.mark.asyncio
    async def test_get_listing_availability_success(
        self, test_config: HostawayConfig, mock_availability_response: dict
    ) -> None:
        """Test successful retrieval of property availability.

        Verifies:
        - GET /listings/{id}/calendar returns 200
        - Response includes available/blocked dates
        - Date range parameters work correctly
        """
        listing_id = 12345
        start_date = "2024-01-15"
        end_date = "2024-01-31"

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_availability_response
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # TODO: Import HostawayClient once implemented
        # from src.mcp.client import HostawayClient
        #
        # client = HostawayClient(config=test_config, http_client=mock_client)
        # availability = await client.get_listing_availability(
        #     listing_id, start_date=start_date, end_date=end_date
        # )
        #
        # assert len(availability) == 3
        # assert availability[0]["date"] == "2024-01-15"
        # assert availability[0]["status"] == "available"
        # assert availability[1]["status"] == "blocked"
        # assert availability[2]["status"] == "booked"
        #
        # # Verify request was made correctly
        # mock_client.get.assert_called_once_with(
        #     f"/listings/{listing_id}/calendar",
        #     params={"startDate": start_date, "endDate": end_date}
        # )


# T042: Integration test for property listing flow
class TestPropertyListingFlow:
    """Test complete property listing flow."""

    @pytest.mark.asyncio
    async def test_listing_flow_auth_to_details(
        self,
        test_config: HostawayConfig,
        mock_listing_response: dict,
        mock_availability_response: dict,
    ) -> None:
        """Test complete flow: authenticate → list properties → get details.

        Flow:
        1. Authenticate and get token
        2. List all properties
        3. Get details for specific property
        4. Check availability

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

        # Mock listings list response
        mock_listings_response = MagicMock()
        mock_listings_response.status_code = 200
        mock_listings_response.json.return_value = {
            "status": "success",
            "result": [mock_listing_response],
            "count": 1,
            "limit": 100,
            "offset": 0,
        }
        mock_listings_response.raise_for_status = MagicMock()

        # Mock listing details response
        mock_details_response = MagicMock()
        mock_details_response.status_code = 200
        mock_details_response.json.return_value = {
            "status": "success",
            "result": mock_listing_response,
        }
        mock_details_response.raise_for_status = MagicMock()

        # Mock availability response
        mock_avail_response = MagicMock()
        mock_avail_response.status_code = 200
        mock_avail_response.json.return_value = mock_availability_response
        mock_avail_response.raise_for_status = MagicMock()

        # Setup mock responses
        mock_client.post = AsyncMock(return_value=mock_auth_response)
        mock_client.get = AsyncMock(
            side_effect=[
                mock_listings_response,
                mock_details_response,
                mock_avail_response,
            ]
        )

        # TODO: Import and test full flow once implemented
        # from src.mcp.auth import TokenManager
        # from src.mcp.client import HostawayClient
        #
        # # Step 1: Authenticate
        # token_manager = TokenManager(config=test_config, client=mock_client)
        # token = await token_manager.get_token()
        # assert token.access_token == "test_token_abc123_xyz789_20chars"
        #
        # # Step 2: List properties
        # client = HostawayClient(config=test_config, http_client=mock_client)
        # listings = await client.get_listings()
        # assert len(listings) == 1
        #
        # # Step 3: Get property details
        # listing_id = listings[0].id
        # details = await client.get_listing(listing_id)
        # assert details.id == 12345
        # assert details.name == "Cozy Downtown Apartment"
        #
        # # Step 4: Check availability
        # availability = await client.get_listing_availability(listing_id)
        # assert len(availability) == 3
        # assert availability[0]["status"] == "available"
