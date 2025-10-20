"""Test to measure financial endpoint response size.

This test measures the actual response size from the /api/financialReports endpoint
to verify if responses exceed the 4000 token threshold and overwhelm context windows.
"""

import json
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.services.hostaway_client import HostawayClient


def create_large_financial_report(days: int = 30, properties: int = 50) -> dict[str, Any]:
    """Create a realistic large financial report.

    Args:
        days: Number of days in the report
        properties: Number of properties in the portfolio

    Returns:
        Large financial report structure mimicking Hostaway API response
    """
    # Base report structure
    report = {
        "periodStart": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
        "periodEnd": datetime.now().strftime("%Y-%m-%d"),
        "periodType": "custom",
        "summary": {
            "totalRevenue": 125000.00,
            "totalExpenses": 45000.00,
            "netIncome": 80000.00,
            "totalBookings": 150,
            "totalNightsBooked": 850,
            "averageDailyRate": 147.06,
            "occupancyRate": 73.5,
            "currency": "USD",
        },
        "revenueByChannel": {
            "airbnb": 65000.00,
            "vrbo": 35000.00,
            "bookingCom": 15000.00,
            "direct": 10000.00,
            "other": 0.00,
        },
        "expensesByCategory": {
            "cleaning": 18000.00,
            "maintenance": 8000.00,
            "utilities": 5000.00,
            "platformFees": 10000.00,
            "supplies": 3000.00,
            "other": 1000.00,
        },
        "properties": [],
        "dailyBreakdown": [],
    }

    # Add property-level details
    for i in range(properties):
        property_data = {
            "listingId": 10000 + i,
            "listingName": f"Property {i + 1} - {'Beachfront' if i % 3 == 0 else 'Downtown' if i % 3 == 1 else 'Mountain'} {['Villa', 'Apartment', 'Condo', 'House'][i % 4]}",
            "internalName": f"PROP-{i + 1:03d}",
            "address": {
                "street": f"{100 + i} Main Street",
                "city": ["San Francisco", "Los Angeles", "Miami", "Austin", "Seattle"][i % 5],
                "state": ["CA", "CA", "FL", "TX", "WA"][i % 5],
                "zip": f"9{i % 10}{i % 10}{i % 10}{i % 10}",
                "country": "USA",
            },
            "revenue": {
                "totalRevenue": 2500.00 + (i * 50),
                "directBookings": 500.00 + (i * 10),
                "airbnb": 1300.00 + (i * 25),
                "vrbo": 500.00 + (i * 10),
                "bookingCom": 200.00 + (i * 5),
            },
            "expenses": {
                "totalExpenses": 900.00 + (i * 18),
                "cleaning": 360.00 + (i * 7),
                "maintenance": 160.00 + (i * 3),
                "utilities": 100.00 + (i * 2),
                "platformFees": 250.00 + (i * 5),
                "supplies": 30.00 + (i * 1),
            },
            "netIncome": 1600.00 + (i * 32),
            "bookings": [],
            "occupancyRate": 65.0 + (i % 35),
            "averageDailyRate": 120.00 + (i * 3),
            "totalBookings": 3 + (i % 5),
            "totalNights": 15 + (i % 20),
        }

        # Add booking details for each property
        for j in range(property_data["totalBookings"]):
            booking = {
                "bookingId": f"BK{i:03d}{j:02d}",
                "checkIn": (datetime.now() - timedelta(days=days - (j * 5))).strftime("%Y-%m-%d"),
                "checkOut": (datetime.now() - timedelta(days=days - (j * 5) - 3)).strftime(
                    "%Y-%m-%d"
                ),
                "guestName": f"Guest {j + 1} (Booking {i}-{j})",
                "guestEmail": f"guest{i}_{j}@example.com",
                "channel": ["airbnb", "vrbo", "bookingCom", "direct"][j % 4],
                "status": "completed",
                "revenue": 800.00 + (j * 100),
                "nights": 3 + (j % 4),
                "guests": 2 + (j % 3),
            }
            property_data["bookings"].append(booking)

        report["properties"].append(property_data)

    # Add daily breakdown
    for day in range(min(days, 90)):  # Cap at 90 days for size
        date_obj = datetime.now() - timedelta(days=days - day)
        daily_data = {
            "date": date_obj.strftime("%Y-%m-%d"),
            "revenue": 2500.00 + (day * 100),
            "expenses": 900.00 + (day * 35),
            "netIncome": 1600.00 + (day * 65),
            "bookings": 2 + (day % 8),
            "checkIns": 1 + (day % 4),
            "checkOuts": 1 + (day % 4),
            "occupancyRate": 60.0 + (day % 40),
        }
        report["dailyBreakdown"].append(daily_data)

    return report


class TestFinancialResponseSize:
    """Test suite to measure financial endpoint response sizes."""

    @pytest.mark.asyncio
    async def test_measure_small_financial_report(
        self, test_config: Any, mock_http_client: AsyncMock, mock_token_manager: AsyncMock
    ) -> None:
        """Test response size for a small financial report (7 days, 5 properties)."""
        # Create small report
        mock_report = create_large_financial_report(days=7, properties=5)

        # Mock the HTTP response
        mock_http_client.get = AsyncMock()
        mock_http_client.get.return_value.status_code = 200
        mock_http_client.get.return_value.json.return_value = {
            "status": "success",
            "result": mock_report,
        }
        mock_http_client.get.return_value.raise_for_status = lambda: None

        # Create client
        client = HostawayClient(config=test_config, token_manager=mock_token_manager)
        client._client = mock_http_client

        # Get report
        result = await client.get_financial_report(start_date="2025-10-13", end_date="2025-10-20")

        # Measure size
        response_text = json.dumps(result, indent=2)
        response_bytes = len(response_text.encode("utf-8"))
        estimated_tokens = int(response_bytes * 0.75)

        print(f"\n{'='*80}")
        print("SMALL FINANCIAL REPORT (7 days, 5 properties)")
        print(f"{'='*80}")
        print(f"Response Size: {response_bytes:,} bytes")
        print(f"Estimated Tokens: {estimated_tokens:,}")
        print(f"Exceeds 4000 Threshold: {'⚠️  YES' if estimated_tokens > 4000 else '✓ NO'}")

        # Assert it's under threshold
        assert estimated_tokens < 4000, "Small report should be under 4000 tokens"

    @pytest.mark.asyncio
    async def test_measure_medium_financial_report(
        self, test_config: Any, mock_http_client: AsyncMock, mock_token_manager: AsyncMock
    ) -> None:
        """Test response size for a medium financial report (30 days, 25 properties)."""
        # Create medium report
        mock_report = create_large_financial_report(days=30, properties=25)

        # Mock the HTTP response
        mock_http_client.get = AsyncMock()
        mock_http_client.get.return_value.status_code = 200
        mock_http_client.get.return_value.json.return_value = {
            "status": "success",
            "result": mock_report,
        }
        mock_http_client.get.return_value.raise_for_status = lambda: None

        # Create client
        client = HostawayClient(config=test_config, token_manager=mock_token_manager)
        client._client = mock_http_client

        # Get report
        result = await client.get_financial_report(start_date="2025-09-20", end_date="2025-10-20")

        # Measure size
        response_text = json.dumps(result, indent=2)
        response_bytes = len(response_text.encode("utf-8"))
        estimated_tokens = int(response_bytes * 0.75)

        print(f"\n{'='*80}")
        print("MEDIUM FINANCIAL REPORT (30 days, 25 properties)")
        print(f"{'='*80}")
        print(f"Response Size: {response_bytes:,} bytes")
        print(f"Estimated Tokens: {estimated_tokens:,}")
        print(f"Exceeds 4000 Threshold: {'⚠️  YES' if estimated_tokens > 4000 else '✓ NO'}")
        print("\nResponse Structure:")
        print(f"  - Properties: {len(result['properties'])}")
        print(f"  - Daily Breakdown: {len(result['dailyBreakdown'])}")
        print(f"  - Total Bookings: {sum(len(p['bookings']) for p in result['properties'])}")

        # This will likely exceed threshold
        if estimated_tokens > 4000:
            print(
                f"\n⚠️  WARNING: Response exceeds 4000 token threshold by {estimated_tokens - 4000:,} tokens"
            )
            print("   TokenAwareMiddleware should summarize this response")

    @pytest.mark.asyncio
    async def test_measure_large_financial_report(
        self, test_config: Any, mock_http_client: AsyncMock, mock_token_manager: AsyncMock
    ) -> None:
        """Test response size for a large financial report (90 days, 50 properties)."""
        # Create large report
        mock_report = create_large_financial_report(days=90, properties=50)

        # Mock the HTTP response
        mock_http_client.get = AsyncMock()
        mock_http_client.get.return_value.status_code = 200
        mock_http_client.get.return_value.json.return_value = {
            "status": "success",
            "result": mock_report,
        }
        mock_http_client.get.return_value.raise_for_status = lambda: None

        # Create client
        client = HostawayClient(config=test_config, token_manager=mock_token_manager)
        client._client = mock_http_client

        # Get report
        result = await client.get_financial_report(start_date="2025-07-22", end_date="2025-10-20")

        # Measure size
        response_text = json.dumps(result, indent=2)
        response_bytes = len(response_text.encode("utf-8"))
        estimated_tokens = int(response_bytes * 0.75)

        print(f"\n{'='*80}")
        print("LARGE FINANCIAL REPORT (90 days, 50 properties)")
        print(f"{'='*80}")
        print(f"Response Size: {response_bytes:,} bytes")
        print(f"Estimated Tokens: {estimated_tokens:,}")
        print(f"Exceeds 4000 Threshold: {'⚠️  YES' if estimated_tokens > 4000 else '✓ NO'}")
        print("\nResponse Structure:")
        print(f"  - Properties: {len(result['properties'])}")
        print(f"  - Daily Breakdown: {len(result['dailyBreakdown'])}")
        print(f"  - Total Bookings: {sum(len(p['bookings']) for p in result['properties'])}")

        # This will definitely exceed threshold
        if estimated_tokens > 4000:
            overflow = estimated_tokens - 4000
            overflow_pct = (overflow / 4000) * 100
            print(
                f"\n⚠️  CRITICAL: Response exceeds 4000 token threshold by {overflow:,} tokens ({overflow_pct:.1f}% overflow)"
            )
            print("   TokenAwareMiddleware MUST summarize this response")
            print("   Without summarization, Claude's context window will be overwhelmed")

        # Assert that it does exceed threshold (proving the problem exists)
        assert (
            estimated_tokens > 4000
        ), "Large report should exceed 4000 tokens (demonstrating the problem)"

    @pytest.mark.asyncio
    async def test_summary_report(self) -> None:
        """Generate summary of all test scenarios."""
        print(f"\n{'='*80}")
        print("FINANCIAL ENDPOINT RESPONSE SIZE ANALYSIS SUMMARY")
        print(f"{'='*80}")

        scenarios = [
            ("Small (7 days, 5 props)", 7, 5),
            ("Medium (30 days, 25 props)", 30, 25),
            ("Large (90 days, 50 props)", 90, 50),
            ("Extra Large (90 days, 100 props)", 90, 100),
        ]

        results = []
        for name, days, properties in scenarios:
            report = create_large_financial_report(days=days, properties=properties)
            response_text = json.dumps(report, indent=2)
            response_bytes = len(response_text.encode("utf-8"))
            estimated_tokens = int(response_bytes * 0.75)

            results.append(
                {
                    "scenario": name,
                    "bytes": response_bytes,
                    "tokens": estimated_tokens,
                    "exceeds": estimated_tokens > 4000,
                    "properties": len(report["properties"]),
                    "bookings": sum(len(p["bookings"]) for p in report["properties"]),
                }
            )

        print("\n| Scenario | Size | Tokens | Exceeds? | Properties | Bookings |")
        print("|----------|------|--------|----------|------------|----------|")
        for r in results:
            exceeds_mark = "⚠️  YES" if r["exceeds"] else "✓ NO"
            print(
                f"| {r['scenario']:<28} | {r['bytes']:>7,} | {r['tokens']:>7,} | {exceeds_mark:>8} | {r['properties']:>10} | {r['bookings']:>8} |"
            )

        print(f"\n{'='*80}")
        print("RECOMMENDATIONS")
        print(f"{'='*80}")
        print("1. ✓ Small reports (<4000 tokens): No summarization needed")
        print("2. ⚠️  Medium reports (4000-10000 tokens): Summary recommended")
        print("3. ⚠️  Large reports (>10000 tokens): Summary REQUIRED")
        print("\nTokenAwareMiddleware should be enabled to handle large responses automatically.")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    """Run the test standalone."""
    import asyncio

    test = TestFinancialResponseSize()
    asyncio.run(test.test_summary_report())
