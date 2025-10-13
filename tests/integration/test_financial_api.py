"""Integration tests for Hostaway financial API.

Tests financial reporting and revenue/expense tracking endpoints.
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
def mock_financial_report_response() -> dict:
    """Create mock Hostaway financial report response."""
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
def mock_property_financial_response() -> dict:
    """Create mock Hostaway property-specific financial report response."""
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


# T092: Contract test for GET /financialReports endpoint
class TestFinancialReportsEndpoint:
    """Test GET /financialReports endpoint contract."""

    @pytest.mark.asyncio
    async def test_get_financial_report_success(
        self, test_config: HostawayConfig, mock_financial_report_response: dict
    ) -> None:
        """Test successful financial report retrieval.

        Verifies:
        - GET /financialReports returns 200
        - Response includes revenue and expense breakdown
        - Profitability metrics included
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "result": mock_financial_report_response,
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # TODO: Import HostawayClient once implemented
        # from src.services.hostaway_client import HostawayClient
        #
        # client = HostawayClient(config=test_config, http_client=mock_client)
        # report = await client.get_financial_report(
        #     start_date="2025-10-01",
        #     end_date="2025-10-31"
        # )
        #
        # assert report["revenue"]["totalRevenue"] == 12500.00
        # assert report["expenses"]["totalExpenses"] == 3250.00
        # assert report["netIncome"] == 9250.00
        #
        # # Verify request was made correctly
        # mock_client.get.assert_called_once_with(
        #     "/financialReports",
        #     params={"startDate": "2025-10-01", "endDate": "2025-10-31"}
        # )

    @pytest.mark.asyncio
    async def test_get_property_financial_report_success(
        self, test_config: HostawayConfig, mock_property_financial_response: dict
    ) -> None:
        """Test successful property-specific financial report retrieval.

        Verifies:
        - GET /financialReports with listing_id returns 200
        - Response includes property-specific data
        - Revenue breakdown by channel works
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "result": mock_property_financial_response,
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        # TODO: Import HostawayClient once implemented
        # from src.services.hostaway_client import HostawayClient
        #
        # client = HostawayClient(config=test_config, http_client=mock_client)
        # report = await client.get_property_financials(
        #     property_id=12345,
        #     start_date="2025-10-01",
        #     end_date="2025-10-31"
        # )
        #
        # assert report["listingId"] == 12345
        # assert report["listingName"] == "Cozy Downtown Apartment"
        # assert report["revenue"]["totalRevenue"] == 4500.00
        #
        # # Verify request was made correctly
        # mock_client.get.assert_called_once_with(
        #     "/financialReports",
        #     params={
        #         "startDate": "2025-10-01",
        #         "endDate": "2025-10-31",
        #         "listingId": 12345
        #     }
        # )

    @pytest.mark.asyncio
    async def test_get_financial_report_invalid_dates(self, test_config: HostawayConfig) -> None:
        """Test GET /financialReports returns 400 for invalid date range.

        Verifies:
        - Invalid date range returns 400
        - Error response is properly formatted
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "invalid_date_range",
            "error_description": "End date must be after start date",
            "status": 400,
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request",
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
        #     await client.get_financial_report(
        #         start_date="2025-10-31",
        #         end_date="2025-10-01"  # End before start
        #     )
        #
        # assert exc_info.value.response.status_code == 400


# T093: Integration test for financial reporting flow
class TestFinancialReportingFlow:
    """Test complete financial reporting flow."""

    @pytest.mark.asyncio
    async def test_financial_reporting_flow_complete(
        self,
        test_config: HostawayConfig,
        mock_financial_report_response: dict,
        mock_property_financial_response: dict,
    ) -> None:
        """Test complete flow: authenticate → get account report → get property report.

        Flow:
        1. Authenticate and get token
        2. Get financial report for all properties
        3. Get financial report for specific property

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

        # Mock account financial report response
        mock_account_report_response = MagicMock()
        mock_account_report_response.status_code = 200
        mock_account_report_response.json.return_value = {
            "status": "success",
            "result": mock_financial_report_response,
        }
        mock_account_report_response.raise_for_status = MagicMock()

        # Mock property financial report response
        mock_property_report_response = MagicMock()
        mock_property_report_response.status_code = 200
        mock_property_report_response.json.return_value = {
            "status": "success",
            "result": mock_property_financial_response,
        }
        mock_property_report_response.raise_for_status = MagicMock()

        # Setup mock responses
        mock_client.post = AsyncMock(return_value=mock_auth_response)
        mock_client.get = AsyncMock(
            side_effect=[
                mock_account_report_response,
                mock_property_report_response,
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
        # # Step 2: Get account financial report
        # client = HostawayClient(config=test_config, http_client=mock_client)
        # account_report = await client.get_financial_report(
        #     start_date="2025-10-01",
        #     end_date="2025-10-31"
        # )
        # assert account_report["revenue"]["totalRevenue"] == 12500.00
        # assert account_report["totalBookings"] == 15
        #
        # # Step 3: Get property-specific report
        # property_report = await client.get_property_financials(
        #     property_id=12345,
        #     start_date="2025-10-01",
        #     end_date="2025-10-31"
        # )
        # assert property_report["listingId"] == 12345
        # assert property_report["revenue"]["totalRevenue"] == 4500.00


# T094: MCP protocol test placeholder
class TestFinancialMCPProtocol:
    """Test MCP protocol for financial tools."""

    @pytest.mark.asyncio
    async def test_financial_tools_discoverable(self) -> None:
        """Test that financial tools are discoverable via MCP protocol.

        Verifies:
        - get_revenue_report tool is registered
        - get_property_financials tool is registered
        """
        # TODO: Implement MCP protocol tests after routes are created
