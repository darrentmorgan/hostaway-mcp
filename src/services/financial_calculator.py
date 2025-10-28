"""Calculate financial reports from reservation data.

This module provides a workaround for the unavailable Hostaway financial reports API
by calculating revenue, expenses, and profitability from reservation data.
"""

from datetime import datetime
from typing import Any, ClassVar


class FinancialCalculator:
    """Calculate financial metrics from reservation data."""

    # Booking statuses that represent confirmed revenue
    REVENUE_STATUSES: ClassVar[set[str]] = {
        "confirmed",
        "checked_in",
        "checked_out",
        "completed",
    }

    # Booking statuses that should be excluded
    EXCLUDED_STATUSES: ClassVar[set[str]] = {
        "cancelled",
        "declined",
        "pending",
        "inquiry",
        "inquiryNotPossible",
        "modified",  # Modified bookings may have incorrect totals
    }

    @staticmethod
    def calculate_financial_report(
        reservations: list[dict[str, Any]],
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """Calculate financial report from reservation data.

        Args:
            reservations: List of reservation dictionaries
            start_date: Report start date (YYYY-MM-DD)
            end_date: Report end date (YYYY-MM-DD)

        Returns:
            Financial report with revenue, expenses, and metrics
        """
        # Parse dates for filtering
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Filter reservations by date range and status
        filtered_reservations = []
        for res in reservations:
            # Skip if status is excluded
            status = res.get("status", "").lower()
            if status in FinancialCalculator.EXCLUDED_STATUSES:
                continue

            # Check if arrival or departure date is in range
            arrival_str = res.get("arrivalDate")
            departure_str = res.get("departureDate")

            if not arrival_str or not departure_str:
                continue

            try:
                arrival = datetime.strptime(arrival_str, "%Y-%m-%d").date()
                departure = datetime.strptime(departure_str, "%Y-%m-%d").date()

                # Include if any part of the stay overlaps with the report period
                if arrival <= end and departure >= start:
                    filtered_reservations.append(res)
            except (ValueError, TypeError):
                continue  # Skip reservations with invalid dates

        # Calculate metrics
        total_revenue = 0.0
        total_cleaning_fees = 0.0
        total_channel_commission = 0.0
        total_hostaway_commission = 0.0
        total_taxes = 0.0
        total_nights = 0
        total_bookings = len(filtered_reservations)
        revenue_by_channel: dict[str, float] = {}
        currency = "USD"  # Default currency

        for res in filtered_reservations:
            # Get currency (use first non-null currency found)
            if res.get("currency") and currency == "USD":
                currency = res.get("currency", "USD")

            # Revenue
            total_price = float(res.get("totalPrice") or 0)
            total_revenue += total_price

            # Fees and commissions
            cleaning_fee = float(res.get("cleaningFee") or 0)
            total_cleaning_fees += cleaning_fee

            channel_commission = float(res.get("channelCommissionAmount") or 0)
            total_channel_commission += channel_commission

            hostaway_commission = float(res.get("hostawayCommissionAmount") or 0)
            total_hostaway_commission += hostaway_commission

            tax_amount = float(res.get("taxAmount") or 0)
            total_taxes += tax_amount

            # Nights
            nights = int(res.get("nights") or 0)
            total_nights += nights

            # Revenue by channel
            channel_name = res.get("channelName", "Unknown")
            revenue_by_channel[channel_name] = (
                revenue_by_channel.get(channel_name, 0.0) + total_price
            )

        # Calculate derived metrics
        total_expenses = total_channel_commission + total_hostaway_commission
        net_income = total_revenue - total_expenses
        average_daily_rate = total_revenue / total_nights if total_nights > 0 else 0.0
        average_booking_value = total_revenue / total_bookings if total_bookings > 0 else 0.0

        # Build report structure matching expected format
        return {
            "period": {
                "startDate": start_date,
                "endDate": end_date,
            },
            "currency": currency,
            "revenue": {
                "totalRevenue": round(total_revenue, 2),
                "cleaningFees": round(total_cleaning_fees, 2),
                "taxes": round(total_taxes, 2),
                "byChannel": {
                    channel: round(amount, 2) for channel, amount in revenue_by_channel.items()
                },
            },
            "expenses": {
                "totalExpenses": round(total_expenses, 2),
                "channelCommissions": round(total_channel_commission, 2),
                "hostawayCommissions": round(total_hostaway_commission, 2),
            },
            "profitability": {
                "netIncome": round(net_income, 2),
                "profitMargin": round(
                    (net_income / total_revenue * 100) if total_revenue > 0 else 0.0, 2
                ),
            },
            "metrics": {
                "totalBookings": total_bookings,
                "totalNights": total_nights,
                "averageDailyRate": round(average_daily_rate, 2),
                "averageBookingValue": round(average_booking_value, 2),
            },
            "dataSource": "calculated_from_reservations",
            "note": "This report is calculated from reservation data as the Hostaway financial reports API is not available for your account.",
        }

    @staticmethod
    def calculate_property_financials(
        reservations: list[dict[str, Any]],
        property_id: int,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """Calculate financial report for a specific property.

        Args:
            reservations: List of all reservation dictionaries
            property_id: Property/listing ID to filter by
            start_date: Report start date (YYYY-MM-DD)
            end_date: Report end date (YYYY-MM-DD)

        Returns:
            Property-specific financial report
        """
        # Filter to specific property
        property_reservations = [
            res for res in reservations if res.get("listingMapId") == property_id
        ]

        # Calculate using standard logic
        report = FinancialCalculator.calculate_financial_report(
            property_reservations,
            start_date,
            end_date,
        )

        # Add property-specific fields
        if property_reservations:
            report["listingId"] = property_id
            report["listingName"] = property_reservations[0].get("listingName", "Unknown")

        return report
