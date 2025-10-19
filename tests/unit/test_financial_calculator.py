"""Unit tests for FinancialCalculator.

Tests financial report calculation from reservation data.
"""

import pytest

from src.services.financial_calculator import FinancialCalculator


class TestFinancialCalculator:
    """Test suite for FinancialCalculator."""

    @pytest.fixture
    def sample_reservations(self):
        """Create sample reservations for testing."""
        return [
            {
                "id": "res-1",
                "status": "confirmed",
                "arrivalDate": "2024-01-10",
                "departureDate": "2024-01-15",
                "totalPrice": 1000.00,
                "cleaningFee": 100.00,
                "channelCommissionAmount": 50.00,
                "hostawayCommission": 25.00,
                "taxAmount": 75.00,
                "numberOfNights": 5,
                "channelName": "Airbnb",
                "currency": "USD",
            },
            {
                "id": "res-2",
                "status": "checked_out",
                "arrivalDate": "2024-01-20",
                "departureDate": "2024-01-25",
                "totalPrice": 1500.00,
                "cleaningFee": 150.00,
                "channelCommissionAmount": 75.00,
                "hostawayCommission": 35.00,
                "taxAmount": 100.00,
                "numberOfNights": 5,
                "channelName": "Booking.com",
                "currency": "USD",
            },
            {
                "id": "res-3",
                "status": "cancelled",
                "arrivalDate": "2024-01-15",
                "departureDate": "2024-01-18",
                "totalPrice": 600.00,
                "cleaningFee": 60.00,
                "channelCommissionAmount": 30.00,
                "numberOfNights": 3,
                "channelName": "Airbnb",
                "currency": "USD",
            },
        ]

    def test_calculate_financial_report_basic(self, sample_reservations):
        """Test basic financial report calculation."""
        report = FinancialCalculator.calculate_financial_report(
            reservations=sample_reservations,
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        # Should exclude cancelled reservation
        assert report["metrics"]["totalBookings"] == 2
        assert report["revenue"]["totalRevenue"] == 2500.00  # 1000 + 1500
        assert report["currency"] == "USD"

    def test_calculate_financial_report_excludes_cancelled(self, sample_reservations):
        """Test that cancelled reservations are excluded."""
        report = FinancialCalculator.calculate_financial_report(
            reservations=sample_reservations,
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        assert report["metrics"]["totalBookings"] == 2
        # Should not include cancelled reservation revenue
        assert report["revenue"]["totalRevenue"] != 3100.00

    def test_calculate_financial_report_date_filtering(self):
        """Test date range filtering."""
        reservations = [
            {
                "status": "confirmed",
                "arrivalDate": "2024-01-10",
                "departureDate": "2024-01-15",
                "totalPrice": 1000.00,
                "cleaningFee": 100.00,
                "numberOfNights": 5,
                "channelName": "Airbnb",
                "currency": "USD",
            },
            {
                "status": "confirmed",
                "arrivalDate": "2024-02-10",
                "departureDate": "2024-02-15",
                "totalPrice": 1000.00,
                "cleaningFee": 100.00,
                "numberOfNights": 5,
                "channelName": "Airbnb",
                "currency": "USD",
            },
        ]

        report = FinancialCalculator.calculate_financial_report(
            reservations=reservations,
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        # Only January booking should be included
        assert report["metrics"]["totalBookings"] == 1
        assert report["revenue"]["totalRevenue"] == 1000.00

    def test_calculate_financial_report_empty_reservations(self):
        """Test report with no reservations."""
        report = FinancialCalculator.calculate_financial_report(
            reservations=[],
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        assert report["metrics"]["totalBookings"] == 0
        assert report["revenue"]["totalRevenue"] == 0.0

    def test_calculate_financial_report_invalid_dates(self):
        """Test handling of invalid reservation dates."""
        reservations = [
            {
                "status": "confirmed",
                "arrivalDate": "invalid-date",
                "departureDate": "2024-01-15",
                "totalPrice": 1000.00,
            },
            {
                "status": "confirmed",
                "arrivalDate": None,
                "departureDate": "2024-01-15",
                "totalPrice": 500.00,
            },
        ]

        report = FinancialCalculator.calculate_financial_report(
            reservations=reservations,
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        # Invalid dates should be skipped
        assert report["metrics"]["totalBookings"] == 0

    def test_revenue_statuses(self):
        """Test that only revenue statuses are included."""
        reservations = [
            {
                "status": "confirmed",
                "arrivalDate": "2024-01-10",
                "departureDate": "2024-01-15",
                "totalPrice": 100,
            },
            {
                "status": "checked_in",
                "arrivalDate": "2024-01-10",
                "departureDate": "2024-01-15",
                "totalPrice": 100,
            },
            {
                "status": "checked_out",
                "arrivalDate": "2024-01-10",
                "departureDate": "2024-01-15",
                "totalPrice": 100,
            },
            {
                "status": "completed",
                "arrivalDate": "2024-01-10",
                "departureDate": "2024-01-15",
                "totalPrice": 100,
            },
            {
                "status": "pending",
                "arrivalDate": "2024-01-10",
                "departureDate": "2024-01-15",
                "totalPrice": 100,
            },
            {
                "status": "inquiry",
                "arrivalDate": "2024-01-10",
                "departureDate": "2024-01-15",
                "totalPrice": 100,
            },
        ]

        report = FinancialCalculator.calculate_financial_report(
            reservations=reservations,
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        # Should include only revenue statuses (confirmed, checked_in, checked_out, completed)
        assert report["metrics"]["totalBookings"] == 4

    def test_currency_detection(self):
        """Test currency detection from reservations."""
        reservations = [
            {
                "status": "confirmed",
                "arrivalDate": "2024-01-10",
                "departureDate": "2024-01-15",
                "totalPrice": 1000.00,
                "currency": "EUR",
            },
        ]

        report = FinancialCalculator.calculate_financial_report(
            reservations=reservations,
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        assert report["currency"] == "EUR"

    def test_overlapping_date_ranges(self):
        """Test reservations that partially overlap with report period."""
        reservations = [
            {
                "status": "confirmed",
                "arrivalDate": "2023-12-28",  # Starts before period
                "departureDate": "2024-01-05",  # Ends in period
                "totalPrice": 1000.00,
                "numberOfNights": 8,
            },
            {
                "status": "confirmed",
                "arrivalDate": "2024-01-28",  # Starts in period
                "departureDate": "2024-02-05",  # Ends after period
                "totalPrice": 1000.00,
                "numberOfNights": 8,
            },
        ]

        report = FinancialCalculator.calculate_financial_report(
            reservations=reservations,
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        # Both should be included as they overlap
        assert report["metrics"]["totalBookings"] == 2
