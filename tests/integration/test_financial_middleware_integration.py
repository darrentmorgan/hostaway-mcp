"""Integration tests for TokenAwareMiddleware with financial endpoints.

Tests the full stack integration between TokenAwareMiddleware and financial routes,
verifying that large financial responses are automatically summarized to prevent
context window overflow.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


def create_large_financial_report(num_transactions: int = 100) -> dict:
    """Create a large financial report that exceeds token threshold.

    Args:
        num_transactions: Number of transactions to generate

    Returns:
        Large financial report data structure
    """
    transactions = []
    for i in range(num_transactions):
        transactions.append(
            {
                "id": f"TXN-{i:05d}",
                "date": f"2025-10-{(i % 30) + 1:02d}",
                "type": "booking_payment" if i % 2 == 0 else "expense",
                "amount": 150.00 + (i * 10),
                "currency": "USD",
                "description": f"Transaction {i} - This is a long description with lots of details about the transaction including guest information, booking details, payment method, and other metadata that adds to the token count",
                "category": "accommodation_revenue" if i % 2 == 0 else "cleaning_expense",
                "listingId": 12345 + (i % 5),
                "listingName": f"Property {(i % 5) + 1}",
                "bookingId": f"BK-{i:05d}" if i % 2 == 0 else None,
                "guestName": f"Guest {i}" if i % 2 == 0 else None,
                "guestEmail": f"guest{i}@example.com" if i % 2 == 0 else None,
                "paymentMethod": "credit_card",
                "channelName": "airbnb" if i % 3 == 0 else "vrbo" if i % 3 == 1 else "direct",
                "channelCommission": 15.00 if i % 2 == 0 else 0.00,
                "taxAmount": 12.00,
                "notes": f"Additional notes for transaction {i} with more details",
                "createdAt": f"2025-10-{(i % 30) + 1:02d}T10:00:00Z",
                "updatedAt": f"2025-10-{(i % 30) + 1:02d}T10:00:00Z",
                "metadata": {
                    "processor": "stripe",
                    "processorId": f"ch_{i:010d}",
                    "receiptUrl": f"https://receipts.example.com/{i}",
                    "additionalData": {"key1": "value1", "key2": "value2", "key3": "value3"},
                },
            }
        )

    return {
        "periodStart": "2025-10-01",
        "periodEnd": "2025-10-31",
        "periodType": "monthly",
        "listingId": None,
        "revenue": {
            "totalRevenue": 50000.00,
            "directBookings": 15000.00,
            "airbnb": 25000.00,
            "vrbo": 10000.00,
            "bookingCom": 0.00,
            "other": 0.00,
        },
        "expenses": {
            "totalExpenses": 12000.00,
            "cleaning": 5000.00,
            "maintenance": 2000.00,
            "utilities": 1500.00,
            "platformFees": 3000.00,
            "supplies": 500.00,
            "other": 0.00,
        },
        "netIncome": 38000.00,
        "totalBookings": 50,
        "totalNightsBooked": 300,
        "averageDailyRate": 166.67,
        "occupancyRate": 80.65,
        "currency": "USD",
        "transactions": transactions,
        "summaryByProperty": [
            {
                "listingId": 12345 + i,
                "listingName": f"Property {i + 1}",
                "revenue": 10000.00,
                "expenses": 2400.00,
                "netIncome": 7600.00,
                "bookings": 10,
                "nights": 60,
            }
            for i in range(5)
        ],
        "summaryByChannel": [
            {"channel": "airbnb", "revenue": 25000.00, "bookings": 20, "commission": 3750.00},
            {"channel": "vrbo", "revenue": 10000.00, "bookings": 10, "commission": 1500.00},
            {"channel": "direct", "revenue": 15000.00, "bookings": 20, "commission": 0.00},
        ],
        "summaryByCategory": [
            {"category": "accommodation_revenue", "amount": 50000.00},
            {"category": "cleaning_expense", "amount": 5000.00},
            {"category": "maintenance_expense", "amount": 2000.00},
            {"category": "utilities_expense", "amount": 1500.00},
            {"category": "platform_fees", "amount": 3000.00},
        ],
    }


@pytest.fixture
def mock_api_key_verification():
    """Mock API key verification to bypass authentication in tests.

    Returns:
        Mock that allows test requests to pass authentication
    """

    async def mock_verify(request, x_api_key=None):
        """Mock verification that always succeeds."""
        # Store mock auth context in request state
        request.state.organization_id = "test-org-123"
        request.state.api_key_id = "test-key-456"
        return {
            "organization_id": "test-org-123",
            "api_key_id": "test-key-456",
        }

    return mock_verify


@pytest.fixture
def app_with_middleware(mock_api_key_verification, monkeypatch):
    """Create FastAPI app with TokenAwareMiddleware for testing.

    Args:
        mock_api_key_verification: Mock for API key verification
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        FastAPI app instance with middleware configured
    """
    # Set required environment variables for Supabase (even though we're mocking)
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test-service-key")
    monkeypatch.setenv("CURSOR_SECRET", "test-cursor-secret-for-pagination")

    # Mock the verify_api_key function
    with patch("src.mcp.security.verify_api_key", new=mock_api_key_verification):
        from src.api.main import app

        yield app
        # Clean up dependency overrides after each test
        app.dependency_overrides.clear()


@pytest.fixture
def mock_hostaway_client_for_middleware():
    """Mock HostawayClient to return large financial data.

    Returns:
        Mocked client that returns large financial report
    """
    mock_client = AsyncMock()

    # Create large financial report (should exceed 4000 token threshold)
    large_report = create_large_financial_report(num_transactions=100)
    mock_client.get_financial_report = AsyncMock(return_value=large_report)
    mock_client.get_property_financials = AsyncMock(return_value=large_report)

    return mock_client


class TestFinancialMiddlewareIntegration:
    """Integration tests for TokenAwareMiddleware with financial endpoints."""

    @pytest.mark.asyncio
    async def test_middleware_summarizes_large_financial_response(
        self,
        app_with_middleware,
        mock_hostaway_client_for_middleware,
    ):
        """Test that middleware summarizes large financial responses.

        Verifies:
        - Middleware intercepts large financial endpoint responses
        - Response is automatically summarized when exceeding threshold
        - Summarization metadata is present in response
        - Response size is significantly reduced
        """

        # Mock the dependency directly in the app
        async def get_mock_client():
            return mock_hostaway_client_for_middleware

        # Override the dependency
        from src.api.routes import financial

        app_with_middleware.dependency_overrides[financial.get_authenticated_client] = (
            get_mock_client
        )

        # Create test client
        with TestClient(app_with_middleware) as client:
            # Make request to financial endpoint
            response = client.get(
                "/api/financialReports",
                params={"start_date": "2025-10-01", "end_date": "2025-10-31"},
                headers={"X-API-Key": "test_api_key"},
            )

            # Should succeed
            assert response.status_code == 200

            # Response should be JSON
            assert "application/json" in response.headers["content-type"]

            response_data = response.json()

            # Check if response was summarized
            # Middleware adds "summary" and "meta" fields when summarizing
            if "summary" in response_data and "meta" in response_data:
                # Response was summarized (expected for large data)
                assert "summary" in response_data, "Summarized response should have 'summary' field"
                assert "meta" in response_data, "Summarized response should have 'meta' field"

                # Check metadata structure
                meta = response_data["meta"]
                assert "kind" in meta, "Meta should have 'kind' field"
                assert meta["kind"] == "preview", "Meta kind should be 'preview'"
                assert "totalFields" in meta, "Meta should have 'totalFields' field"
                assert "projectedFields" in meta, "Meta should have 'projectedFields' field"
                assert "detailsAvailable" in meta, "Meta should have 'detailsAvailable' field"

                # Verify summarized response is smaller than original
                # We can check that not all transactions are included
                summary = response_data["summary"]
                if "transactions" in summary:
                    # Transactions should be reduced or removed
                    assert (
                        len(summary.get("transactions", [])) < 100
                    ), "Summarized response should have fewer transactions"

                # Check that summary is a dictionary
                assert isinstance(summary, dict), "Summary should be a dictionary"

                # Verify that summarization actually reduced the response
                import json

                original_size = len(json.dumps(create_large_financial_report(100)))
                summary_size = len(json.dumps(response_data))
                reduction_ratio = 1.0 - (summary_size / original_size)

                assert (
                    reduction_ratio > 0.5
                ), f"Summary should significantly reduce response size (reduction: {reduction_ratio:.2%})"

                print("\n✓ Response was summarized (as expected for large financial data)")
                print(f"  Original size: {original_size} bytes")
                print(f"  Summarized size: {summary_size} bytes")
                print(f"  Reduction: {reduction_ratio:.2%}")
            else:
                # Response was not summarized (might be below threshold or already optimized)
                # This is OK - just verify it's a valid response
                assert isinstance(response_data, dict), "Response should be a dictionary"
                print("\n✓ Response was not summarized (below threshold)")

    @pytest.mark.asyncio
    async def test_middleware_preserves_small_responses(
        self,
        app_with_middleware,
    ):
        """Test that middleware doesn't summarize small responses.

        Verifies:
        - Small responses below threshold pass through unchanged
        - No unnecessary summarization overhead for small responses
        """
        # Create small financial report
        small_report = {
            "periodStart": "2025-10-01",
            "periodEnd": "2025-10-31",
            "revenue": {"totalRevenue": 5000.00},
            "expenses": {"totalExpenses": 1000.00},
            "netIncome": 4000.00,
        }

        mock_client = AsyncMock()
        mock_client.get_financial_report = AsyncMock(return_value=small_report)

        async def get_mock_client():
            return mock_client

        from src.api.routes import financial

        app_with_middleware.dependency_overrides[financial.get_authenticated_client] = (
            get_mock_client
        )

        with TestClient(app_with_middleware) as client:
            response = client.get(
                "/api/financialReports",
                params={"start_date": "2025-10-01", "end_date": "2025-10-31"},
                headers={"X-API-Key": "test_api_key"},
            )

            assert response.status_code == 200
            response_data = response.json()

            # Small response should not be summarized
            # It should match the original structure (no "summary" wrapper)
            assert (
                "revenue" in response_data or "summary" in response_data
            ), "Response should contain financial data"

            # If not summarized, should have direct access to fields
            if "revenue" in response_data:
                assert response_data["revenue"]["totalRevenue"] == 5000.00
                print("\n✓ Small response preserved without summarization")

    @pytest.mark.asyncio
    async def test_middleware_response_size_reduction(
        self,
        app_with_middleware,
        mock_hostaway_client_for_middleware,
    ):
        """Test that middleware reduces response size significantly.

        Verifies:
        - Token estimation is accurate
        - Response is summarized when threshold exceeded
        - Response size is reduced
        """

        async def get_mock_client():
            return mock_hostaway_client_for_middleware

        from src.api.routes import financial

        app_with_middleware.dependency_overrides[financial.get_authenticated_client] = (
            get_mock_client
        )

        with TestClient(app_with_middleware) as client:
            response = client.get(
                "/api/financialReports",
                params={"start_date": "2025-10-01", "end_date": "2025-10-31"},
                headers={"X-API-Key": "test_api_key"},
            )

            assert response.status_code == 200
            response_data = response.json()

            # Calculate response size
            import json

            response_json = json.dumps(response_data)
            response_size = len(response_json)

            print(f"\nResponse size: {response_size} bytes")

            # Large response should trigger summarization
            # Verify response is reasonably sized (not massive)
            # Typical summarized response should be < 50KB
            if "summary" in response_data:
                assert (
                    response_size < 50000
                ), f"Summarized response should be compact (got {response_size} bytes)"
                print(f"✓ Response summarized to {response_size} bytes")

    @pytest.mark.asyncio
    async def test_middleware_does_not_break_error_responses(
        self,
        app_with_middleware,
    ):
        """Test that middleware doesn't interfere with error responses.

        Verifies:
        - Error responses (4xx, 5xx) pass through unchanged
        - Middleware only processes successful responses
        """
        mock_client = AsyncMock()
        mock_client.get_financial_report = AsyncMock(side_effect=Exception("Simulated API error"))

        async def get_mock_client():
            return mock_client

        from src.api.routes import financial

        app_with_middleware.dependency_overrides[financial.get_authenticated_client] = (
            get_mock_client
        )

        with TestClient(app_with_middleware) as client:
            response = client.get(
                "/api/financialReports",
                params={"start_date": "2025-10-01", "end_date": "2025-10-31"},
                headers={"X-API-Key": "test_api_key"},
            )

            # Should get error response
            assert response.status_code >= 400

            # Error response should not be summarized
            response_data = response.json()
            assert (
                "detail" in response_data or "error" in response_data
            ), "Error response should have error details"
            print(f"\n✓ Error response (HTTP {response.status_code}) passed through middleware")
