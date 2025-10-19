"""Mock Hostaway client for testing with deterministic responses.

Provides a MockHostawayClient that returns predictable data without
hitting the real Hostaway API, enabling fast, reliable, deterministic tests.
"""

from typing import Any

from src.services.hostaway_client import HostawayClient
from src.testing.hostaway_mocks import generate_mock_bookings, generate_mock_listings


class MockHostawayClient(HostawayClient):
    """Mock implementation of HostawayClient for testing.

    Returns deterministic mock data for all API methods, avoiding external
    API calls and ensuring consistent test behavior across runs.

    Total dataset sizes (controlled constants):
    - TOTAL_LISTINGS: 100 mock properties
    - TOTAL_BOOKINGS: 100 mock reservations
    """

    TOTAL_LISTINGS = 100
    TOTAL_BOOKINGS = 100

    async def get_listings(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Return deterministic mock listings.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip for pagination

        Returns:
            List of mock listing dictionaries (empty if offset >= total)
        """
        # If offset is beyond dataset, return empty array
        if offset >= self.TOTAL_LISTINGS:
            return []

        # Calculate how many items are available from this offset
        available = self.TOTAL_LISTINGS - offset

        # Return min(limit, available) items
        actual_limit = min(limit, available)

        return generate_mock_listings(actual_limit, offset)

    async def search_bookings(
        self,
        listing_id: int | None = None,
        check_in_from: str | None = None,
        check_in_to: str | None = None,
        check_out_from: str | None = None,
        check_out_to: str | None = None,
        status: list[str] | None = None,
        guest_email: str | None = None,
        booking_source: str | None = None,
        min_guests: int | None = None,
        max_guests: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Return deterministic mock bookings.

        Args:
            listing_id: Filter by specific property ID (ignored in mock)
            check_in_from: Filter by check-in date (ignored in mock)
            check_in_to: Filter by check-in date (ignored in mock)
            check_out_from: Filter by check-out date (ignored in mock)
            check_out_to: Filter by check-out date (ignored in mock)
            status: Filter by booking status (ignored in mock)
            guest_email: Filter by guest email (ignored in mock)
            booking_source: Filter by channel (ignored in mock)
            min_guests: Filter by guest count (ignored in mock)
            max_guests: Filter by guest count (ignored in mock)
            limit: Maximum number of results to return
            offset: Number of results to skip for pagination

        Returns:
            List of mock booking dictionaries (empty if offset >= total)

        Note:
            All filter parameters are currently ignored for simplicity.
            The mock returns the full dataset paginated by limit/offset.
        """
        # If offset is beyond dataset, return empty array
        if offset >= self.TOTAL_BOOKINGS:
            return []

        # Calculate how many items are available from this offset
        available = self.TOTAL_BOOKINGS - offset

        # Return min(limit, available) items
        actual_limit = min(limit, available)

        return generate_mock_bookings(actual_limit, offset)
