"""Unit tests for financial API error handling.

Tests error cases and validation for financial endpoints.
"""

from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException

from src.api.routes.financial import get_financial_report
from src.services.hostaway_client import HostawayClient


class TestFinancialErrorHandling:
    """Test error handling in financial endpoints."""

    @pytest.mark.asyncio
    async def test_get_financial_report_http_500(
        self,
        mock_client: HostawayClient,
    ) -> None:
        """Test 500 error handling from Hostaway API."""
        # Configure mock to raise HTTPStatusError with 500
        error_response = httpx.Response(
            status_code=500,
            text="Internal Server Error",
            request=httpx.Request("GET", "https://api.hostaway.com/v1/financialReports"),
        )
        mock_client._client.request = AsyncMock(return_value=error_response)

        with pytest.raises(HTTPException) as exc_info:
            await get_financial_report(
                start_date="2025-10-01",
                end_date="2025-10-31",
                client=mock_client,
            )

        assert exc_info.value.status_code == 502
        assert "Hostaway API error" in exc_info.value.detail["error"]
        assert "correlation_id" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_financial_report_invalid_dates(
        self,
        mock_client: HostawayClient,
    ) -> None:
        """Test validation of invalid date range."""
        with pytest.raises(HTTPException) as exc_info:
            await get_financial_report(
                start_date="2025-10-31",  # End before start
                end_date="2025-10-01",
                client=mock_client,
            )

        assert exc_info.value.status_code == 400
        assert "End date must be on or after start date" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_financial_report_malformed_date(
        self,
        mock_client: HostawayClient,
    ) -> None:
        """Test validation of malformed date string."""
        with pytest.raises(HTTPException) as exc_info:
            await get_financial_report(
                start_date="not-a-date",
                end_date="2025-10-31",
                client=mock_client,
            )

        assert exc_info.value.status_code == 400
        assert "Invalid date format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_financial_report_malformed_response(
        self,
        mock_client: HostawayClient,
    ) -> None:
        """Test handling of malformed JSON response."""
        # Configure mock to return invalid JSON
        error_response = httpx.Response(
            status_code=200,
            text="not json",
            request=httpx.Request("GET", "https://api.hostaway.com/v1/financialReports"),
        )
        error_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))
        mock_client._client.request = AsyncMock(return_value=error_response)

        with pytest.raises(HTTPException) as exc_info:
            await get_financial_report(
                start_date="2025-10-01",
                end_date="2025-10-31",
                client=mock_client,
            )

        assert exc_info.value.status_code == 500
        assert "correlation_id" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_financial_report_timeout(
        self,
        mock_client: HostawayClient,
    ) -> None:
        """Test handling of request timeout."""
        # Configure mock to timeout
        mock_client._client.request = AsyncMock(
            side_effect=httpx.TimeoutException("Connection timed out")
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_financial_report(
                start_date="2025-10-01",
                end_date="2025-10-31",
                client=mock_client,
            )

        assert exc_info.value.status_code == 500
        assert "correlation_id" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_financial_report_http_404(
        self,
        mock_client: HostawayClient,
    ) -> None:
        """Test 404 error handling - endpoint not available."""
        error_response = httpx.Response(
            status_code=404,
            text="Not Found",
            request=httpx.Request("GET", "https://api.hostaway.com/v1/financialReports"),
        )
        mock_client._client.request = AsyncMock(return_value=error_response)

        with pytest.raises(HTTPException) as exc_info:
            await get_financial_report(
                start_date="2025-10-01",
                end_date="2025-10-31",
                client=mock_client,
            )

        assert exc_info.value.status_code == 404
        assert "correlation_id" in exc_info.value.detail
        assert "not available" in exc_info.value.detail["error"]

    @pytest.mark.asyncio
    async def test_get_financial_report_http_403(
        self,
        mock_client: HostawayClient,
    ) -> None:
        """Test 403 error handling - permission denied."""
        error_response = httpx.Response(
            status_code=403,
            text="Forbidden",
            request=httpx.Request("GET", "https://api.hostaway.com/v1/financialReports"),
        )
        mock_client._client.request = AsyncMock(return_value=error_response)

        with pytest.raises(HTTPException) as exc_info:
            await get_financial_report(
                start_date="2025-10-01",
                end_date="2025-10-31",
                client=mock_client,
            )

        assert exc_info.value.status_code == 403
        assert "correlation_id" in exc_info.value.detail
        assert "Permission denied" in exc_info.value.detail["error"]

    @pytest.mark.asyncio
    async def test_correlation_id_format(
        self,
        mock_client: HostawayClient,
    ) -> None:
        """Test that correlation IDs are properly formatted."""
        error_response = httpx.Response(
            status_code=500,
            text="Internal Server Error",
            request=httpx.Request("GET", "https://api.hostaway.com/v1/financialReports"),
        )
        mock_client._client.request = AsyncMock(return_value=error_response)

        with pytest.raises(HTTPException) as exc_info:
            await get_financial_report(
                start_date="2025-10-01",
                end_date="2025-10-31",
                client=mock_client,
            )

        # Validate correlation_id exists and has reasonable length (nanoid with size=10)
        correlation_id = exc_info.value.detail["correlation_id"]
        assert isinstance(correlation_id, str)
        assert len(correlation_id) == 10
        assert correlation_id.replace("_", "").replace("-", "").isalnum()

    @pytest.mark.asyncio
    async def test_get_financial_report_empty_response(
        self,
        mock_client: HostawayClient,
    ) -> None:
        """Test handling of empty financial report response."""
        # Configure mock to return empty result
        empty_response = httpx.Response(
            status_code=200,
            json={"status": "success", "result": {}},
            request=httpx.Request("GET", "https://api.hostaway.com/v1/financialReports"),
        )
        mock_client._client.request = AsyncMock(return_value=empty_response)

        with pytest.raises(HTTPException) as exc_info:
            await get_financial_report(
                start_date="2025-10-01",
                end_date="2025-10-31",
                client=mock_client,
            )

        assert exc_info.value.status_code == 404
        assert "No financial data found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_property_financial_report_empty_response(
        self,
        mock_client: HostawayClient,
    ) -> None:
        """Test handling of empty property-specific financial report."""
        # Configure mock to return empty result
        empty_response = httpx.Response(
            status_code=200,
            json={"status": "success", "result": {}},
            request=httpx.Request("GET", "https://api.hostaway.com/v1/financialReports"),
        )
        mock_client._client.request = AsyncMock(return_value=empty_response)

        with pytest.raises(HTTPException) as exc_info:
            await get_financial_report(
                start_date="2025-10-01",
                end_date="2025-10-31",
                listing_id=99999,
                client=mock_client,
            )

        assert exc_info.value.status_code == 404
        assert "No financial data found" in exc_info.value.detail
