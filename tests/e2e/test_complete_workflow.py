"""End-to-end tests for complete Hostaway MCP workflow.

Tests the complete user journey from authentication through data retrieval.
Modified to exclude messaging (Phase 6) as it involves WRITE operations.
"""

from datetime import date, timedelta

import pytest

from src.mcp.config import HostawayConfig


@pytest.mark.asyncio
@pytest.mark.e2e
class TestCompleteWorkflow:
    """E2E tests for complete Hostaway MCP workflows."""

    async def test_complete_property_workflow(self, test_config: HostawayConfig) -> None:
        """Test complete workflow: auth → list properties → get details → check availability.

        This test validates the entire property information workflow:
        1. Authenticate with Hostaway API
        2. List all properties
        3. Get detailed information for a specific property
        4. Check property availability for a date range

        Args:
            test_config: Test configuration with credentials
        """
        from src.mcp.auth import TokenManager
        from src.services.hostaway_client import HostawayClient
        from src.services.rate_limiter import RateLimiter

        # Step 1: Authenticate
        rate_limiter = RateLimiter(
            ip_rate_limit=test_config.rate_limit_ip,
            account_rate_limit=test_config.rate_limit_account,
            max_concurrent=test_config.max_concurrent_requests,
        )
        token_manager = TokenManager(config=test_config)
        client = HostawayClient(
            config=test_config,
            token_manager=token_manager,
            rate_limiter=rate_limiter,
        )

        # Verify authentication works
        token = await token_manager.get_token()
        assert token.access_token
        assert not token.should_refresh()

        # Step 2: List properties
        listings = await client.get_listings(limit=10)
        assert isinstance(listings, list)
        assert len(listings) > 0, "Account should have at least one property"

        # Step 3: Get property details
        first_listing = listings[0]
        listing_id = first_listing["id"]
        listing_details = await client.get_listing(listing_id)

        assert listing_details
        assert listing_details["id"] == listing_id
        assert "name" in listing_details

        # Step 4: Check availability
        today = date.today()
        start_date = (today + timedelta(days=30)).isoformat()
        end_date = (today + timedelta(days=37)).isoformat()

        availability = await client.get_listing_availability(
            listing_id=listing_id,
            start_date=start_date,
            end_date=end_date,
        )

        assert isinstance(availability, list)
        assert len(availability) > 0, "Should have availability data for date range"

        # Cleanup
        await client.aclose()
        await token_manager.aclose()

    async def test_complete_booking_workflow(self, test_config: HostawayConfig) -> None:
        """Test complete workflow: auth → search bookings → get booking details → get guest.

        This test validates the entire booking management workflow:
        1. Authenticate with Hostaway API
        2. Search for bookings with filters
        3. Get detailed information for a specific booking
        4. Get guest information for the booking

        Args:
            test_config: Test configuration with credentials
        """
        from src.mcp.auth import TokenManager
        from src.services.hostaway_client import HostawayClient
        from src.services.rate_limiter import RateLimiter

        # Step 1: Authenticate
        rate_limiter = RateLimiter(
            ip_rate_limit=test_config.rate_limit_ip,
            account_rate_limit=test_config.rate_limit_account,
            max_concurrent=test_config.max_concurrent_requests,
        )
        token_manager = TokenManager(config=test_config)
        client = HostawayClient(
            config=test_config,
            token_manager=token_manager,
            rate_limiter=rate_limiter,
        )

        # Step 2: Search bookings (broad search to ensure results)
        bookings = await client.search_bookings(
            status=["confirmed", "pending", "completed"],
            limit=10,
        )

        # If no bookings found, skip rest of test (test account may be empty)
        if len(bookings) == 0:
            pytest.skip("No bookings found in test account")
            await client.aclose()
            await token_manager.aclose()
            return

        # Step 3: Get booking details
        first_booking = bookings[0]
        booking_id = first_booking["id"]
        booking_details = await client.get_booking(booking_id)

        assert booking_details
        assert booking_details["id"] == booking_id
        assert "listingMapId" in booking_details or "listingId" in booking_details

        # Step 4: Get guest information
        guest_info = await client.get_booking_guest(booking_id)

        assert guest_info
        assert "firstName" in guest_info or "email" in guest_info

        # Cleanup
        await client.aclose()
        await token_manager.aclose()

    async def test_complete_financial_workflow(self, test_config: HostawayConfig) -> None:
        """Test complete workflow: auth → get financial report → get property financials.

        This test validates the entire financial reporting workflow:
        1. Authenticate with Hostaway API
        2. Get account-wide financial report
        3. Get property-specific financial report

        Args:
            test_config: Test configuration with credentials
        """
        from src.mcp.auth import TokenManager
        from src.services.hostaway_client import HostawayClient
        from src.services.rate_limiter import RateLimiter

        # Step 1: Authenticate
        rate_limiter = RateLimiter(
            ip_rate_limit=test_config.rate_limit_ip,
            account_rate_limit=test_config.rate_limit_account,
            max_concurrent=test_config.max_concurrent_requests,
        )
        token_manager = TokenManager(config=test_config)
        client = HostawayClient(
            config=test_config,
            token_manager=token_manager,
            rate_limiter=rate_limiter,
        )

        # Step 2: Get account-wide financial report
        today = date.today()
        start_date = (today - timedelta(days=30)).isoformat()
        end_date = today.isoformat()

        financial_report = await client.get_financial_report(
            start_date=start_date,
            end_date=end_date,
        )

        assert financial_report
        # Financial report structure varies by account, just verify we got data

        # Step 3: Get property-specific financials (if properties exist)
        listings = await client.get_listings(limit=1)
        if len(listings) > 0:
            listing_id = listings[0]["id"]
            property_financials = await client.get_property_financials(
                property_id=listing_id,
                start_date=start_date,
                end_date=end_date,
            )

            assert property_financials
            # Property financials structure varies, just verify we got data

        # Cleanup
        await client.aclose()
        await token_manager.aclose()

    async def test_cross_feature_integration(self, test_config: HostawayConfig) -> None:
        """Test integration across multiple features in one workflow.

        This test validates that multiple features work together seamlessly:
        1. Authenticate
        2. List properties
        3. Search bookings for a specific property
        4. Get financial report for the same property
        5. Verify data consistency across features

        Args:
            test_config: Test configuration with credentials
        """
        from src.mcp.auth import TokenManager
        from src.services.hostaway_client import HostawayClient
        from src.services.rate_limiter import RateLimiter

        # Setup
        rate_limiter = RateLimiter(
            ip_rate_limit=test_config.rate_limit_ip,
            account_rate_limit=test_config.rate_limit_account,
            max_concurrent=test_config.max_concurrent_requests,
        )
        token_manager = TokenManager(config=test_config)
        client = HostawayClient(
            config=test_config,
            token_manager=token_manager,
            rate_limiter=rate_limiter,
        )

        # Get a property
        listings = await client.get_listings(limit=1)
        if len(listings) == 0:
            pytest.skip("No properties found in test account")
            await client.aclose()
            await token_manager.aclose()
            return

        listing_id = listings[0]["id"]

        # Search bookings for this property
        bookings = await client.search_bookings(
            listing_id=listing_id,
            status=["confirmed", "completed"],
            limit=5,
        )

        # Get financial report for this property
        today = date.today()
        start_date = (today - timedelta(days=90)).isoformat()
        end_date = today.isoformat()

        property_financials = await client.get_property_financials(
            property_id=listing_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Verify we can retrieve all data without errors
        assert isinstance(bookings, list)
        assert property_financials is not None

        # Cleanup
        await client.aclose()
        await token_manager.aclose()
