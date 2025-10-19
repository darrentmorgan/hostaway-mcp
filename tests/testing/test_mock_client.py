"""Tests for mock Hostaway client.

Tests deterministic mock client behavior for testing.
"""

import pytest

from src.mcp.config import HostawayConfig
from src.testing.mock_client import MockHostawayClient


class TestMockHostawayClient:
    """Test mock client returns deterministic data."""

    @pytest.fixture
    def mock_client(self):
        """Create mock client instance."""
        config = HostawayConfig(
            account_id="test-account",
            secret_key="test-secret",
            base_url="https://api.hostaway.com/v1",
        )
        # MockHostawayClient doesn't need token_manager or rate_limiter
        # since it doesn't make real API calls
        return MockHostawayClient(config=config, token_manager=None, rate_limiter=None)

    @pytest.mark.asyncio
    async def test_get_listings_returns_mock_data(self, mock_client):
        """Test get_listings returns deterministic mock listings."""
        listings = await mock_client.get_listings(limit=10)

        assert isinstance(listings, list)
        assert len(listings) == 10
        # Verify it's using mock data
        assert all("id" in listing for listing in listings)

    @pytest.mark.asyncio
    async def test_get_listings_respects_limit(self, mock_client):
        """Test get_listings respects limit parameter."""
        listings_5 = await mock_client.get_listings(limit=5)
        listings_20 = await mock_client.get_listings(limit=20)

        assert len(listings_5) == 5
        assert len(listings_20) == 20

    @pytest.mark.asyncio
    async def test_get_listings_respects_offset(self, mock_client):
        """Test get_listings respects offset for pagination."""
        page1 = await mock_client.get_listings(limit=10, offset=0)
        page2 = await mock_client.get_listings(limit=10, offset=10)

        # Should return different listings
        assert page1[0]["id"] != page2[0]["id"]

    @pytest.mark.asyncio
    async def test_get_listings_offset_beyond_total_returns_empty(self, mock_client):
        """Test get_listings returns empty list when offset exceeds total."""
        listings = await mock_client.get_listings(limit=10, offset=1000)

        assert listings == []

    @pytest.mark.asyncio
    async def test_get_listings_limit_exceeds_available(self, mock_client):
        """Test get_listings returns only available items."""
        # Request 50 items starting at offset 90
        # Should only return 10 items (90-99)
        listings = await mock_client.get_listings(limit=50, offset=90)

        assert len(listings) == 10  # Only 10 remaining

    @pytest.mark.asyncio
    async def test_search_bookings_returns_mock_data(self, mock_client):
        """Test search_bookings returns deterministic mock bookings."""
        bookings = await mock_client.search_bookings(limit=10)

        assert isinstance(bookings, list)
        assert len(bookings) == 10
        assert all("id" in booking for booking in bookings)

    @pytest.mark.asyncio
    async def test_search_bookings_respects_limit(self, mock_client):
        """Test search_bookings respects limit parameter."""
        bookings_5 = await mock_client.search_bookings(limit=5)
        bookings_25 = await mock_client.search_bookings(limit=25)

        assert len(bookings_5) == 5
        assert len(bookings_25) == 25

    @pytest.mark.asyncio
    async def test_search_bookings_respects_offset(self, mock_client):
        """Test search_bookings respects offset for pagination."""
        page1 = await mock_client.search_bookings(limit=10, offset=0)
        page2 = await mock_client.search_bookings(limit=10, offset=10)

        # Should return different bookings
        assert page1[0]["id"] != page2[0]["id"]

    @pytest.mark.asyncio
    async def test_search_bookings_offset_beyond_total_returns_empty(self, mock_client):
        """Test search_bookings returns empty list when offset exceeds total."""
        bookings = await mock_client.search_bookings(limit=10, offset=1000)

        assert bookings == []

    @pytest.mark.asyncio
    async def test_search_bookings_limit_exceeds_available(self, mock_client):
        """Test search_bookings returns only available items."""
        # Request 50 items starting at offset 90
        # Should only return 10 items (90-99)
        bookings = await mock_client.search_bookings(limit=50, offset=90)

        assert len(bookings) == 10  # Only 10 remaining

    @pytest.mark.asyncio
    async def test_search_bookings_accepts_filter_parameters(self, mock_client):
        """Test search_bookings accepts all filter parameters (even if ignored)."""
        # Mock client currently ignores filters but should accept them
        bookings = await mock_client.search_bookings(
            listing_id=123,
            check_in_from="2024-01-01",
            check_in_to="2024-01-31",
            check_out_from="2024-01-05",
            check_out_to="2024-02-05",
            status=["confirmed", "pending"],
            guest_email="test@example.com",
            booking_source="airbnb",
            min_guests=2,
            max_guests=4,
            limit=10,
        )

        # Should still return mock data
        assert isinstance(bookings, list)
        assert len(bookings) == 10

    @pytest.mark.asyncio
    async def test_mock_client_total_listings_constant(self, mock_client):
        """Test TOTAL_LISTINGS constant is respected."""
        assert MockHostawayClient.TOTAL_LISTINGS == 100

        # Verify total is actually 100
        all_listings = await mock_client.get_listings(limit=200, offset=0)
        assert len(all_listings) == 100

    @pytest.mark.asyncio
    async def test_mock_client_total_bookings_constant(self, mock_client):
        """Test TOTAL_BOOKINGS constant is respected."""
        assert MockHostawayClient.TOTAL_BOOKINGS == 100

        # Verify total is actually 100
        all_bookings = await mock_client.search_bookings(limit=200, offset=0)
        assert len(all_bookings) == 100
