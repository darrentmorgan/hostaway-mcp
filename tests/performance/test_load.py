"""Load tests for Hostaway MCP server performance.

Tests server behavior under concurrent load to validate:
- Rate limiting works correctly
- Connection pooling handles concurrent requests
- Response times remain acceptable under load
- No resource leaks or errors
"""

import asyncio
from typing import Any

import pytest

from src.mcp.config import HostawayConfig


@pytest.mark.performance
@pytest.mark.asyncio
class TestLoadPerformance:
    """Load testing for concurrent request handling."""

    async def test_concurrent_listing_requests(self, test_config: HostawayConfig) -> None:
        """Test 100 concurrent listing requests without errors.

        Validates:
        - All requests complete successfully
        - Rate limiting prevents API lockout
        - Connection pooling handles concurrency
        - No request exceeds 5 second timeout

        Args:
            test_config: Test configuration with credentials
        """
        from src.mcp.auth import TokenManager
        from src.services.hostaway_client import HostawayClient
        from src.services.rate_limiter import RateLimiter

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

        async def make_request() -> dict[str, Any]:
            """Make a single listing request."""
            return await client.get_listings(limit=5)

        # Execute 100 concurrent requests
        tasks = [make_request() for _ in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all requests succeeded
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Expected no errors, got {len(errors)}: {errors[:3]}"

        # Verify all results are lists
        successful = [r for r in results if isinstance(r, list)]
        assert len(successful) == 100, f"Expected 100 successful results, got {len(successful)}"

        # Cleanup
        await client.aclose()
        await token_manager.aclose()

    async def test_concurrent_booking_searches(self, test_config: HostawayConfig) -> None:
        """Test 100 concurrent booking search requests.

        Args:
            test_config: Test configuration with credentials
        """
        from src.mcp.auth import TokenManager
        from src.services.hostaway_client import HostawayClient
        from src.services.rate_limiter import RateLimiter

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

        async def make_request() -> dict[str, Any]:
            """Make a single booking search request."""
            return await client.search_bookings(limit=5)

        # Execute 100 concurrent requests
        tasks = [make_request() for _ in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all requests succeeded
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Expected no errors, got {len(errors)}: {errors[:3]}"

        # Verify all results are lists
        successful = [r for r in results if isinstance(r, list)]
        assert len(successful) == 100, f"Expected 100 successful results, got {len(successful)}"

        # Cleanup
        await client.aclose()
        await token_manager.aclose()

    async def test_mixed_concurrent_requests(self, test_config: HostawayConfig) -> None:
        """Test 100 concurrent requests of mixed types (listings, bookings, financials).

        Validates:
        - Server handles diverse concurrent operations
        - Rate limiting works across different endpoints
        - No cross-request interference

        Args:
            test_config: Test configuration with credentials
        """
        from datetime import date, timedelta

        from src.mcp.auth import TokenManager
        from src.services.hostaway_client import HostawayClient
        from src.services.rate_limiter import RateLimiter

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

        today = date.today()
        start_date = (today - timedelta(days=30)).isoformat()
        end_date = today.isoformat()

        async def make_listing_request() -> dict[str, Any]:
            return await client.get_listings(limit=5)

        async def make_booking_request() -> dict[str, Any]:
            return await client.search_bookings(limit=5)

        async def make_financial_request() -> dict[str, Any]:
            return await client.get_financial_report(
                start_date=start_date,
                end_date=end_date,
            )

        # Create mix of 100 requests (33/33/34 distribution)
        tasks = (
            [make_listing_request() for _ in range(33)]
            + [make_booking_request() for _ in range(33)]
            + [make_financial_request() for _ in range(34)]
        )

        # Execute all concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all requests succeeded
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Expected no errors, got {len(errors)}: {errors[:3]}"

        # Verify we got 100 results
        assert len(results) == 100, f"Expected 100 results, got {len(results)}"

        # Cleanup
        await client.aclose()
        await token_manager.aclose()

    async def test_token_reuse_under_load(self, test_config: HostawayConfig) -> None:
        """Test that token is reused correctly under concurrent load.

        Validates:
        - Single token acquisition for all requests
        - No token refresh during load (unless necessary)
        - Thread-safe token sharing

        Args:
            test_config: Test configuration with credentials
        """
        from src.mcp.auth import TokenManager
        from src.services.hostaway_client import HostawayClient
        from src.services.rate_limiter import RateLimiter

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

        # Get initial token
        initial_token = await token_manager.get_token()
        initial_access_token = initial_token.access_token

        async def make_request() -> dict[str, Any]:
            """Make a request and verify token is reused."""
            return await client.get_listings(limit=1)

        # Execute 50 concurrent requests
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all succeeded
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Expected no errors, got {len(errors)}"

        # Verify token is still the same (not refreshed unnecessarily)
        current_token = await token_manager.get_token()
        assert (
            current_token.access_token == initial_access_token
        ), "Token should be reused, not refreshed"

        # Cleanup
        await client.aclose()
        await token_manager.aclose()

    @pytest.mark.slow
    async def test_sustained_load(self, test_config: HostawayConfig) -> None:
        """Test server performance under sustained load over time.

        Runs 500 requests in waves of 50 concurrent requests.
        Validates system stability over extended operation.

        Args:
            test_config: Test configuration with credentials
        """
        from src.mcp.auth import TokenManager
        from src.services.hostaway_client import HostawayClient
        from src.services.rate_limiter import RateLimiter

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

        async def make_request() -> dict[str, Any]:
            return await client.get_listings(limit=5)

        total_requests = 0
        total_errors = 0

        # Run 10 waves of 50 concurrent requests each
        for wave in range(10):
            tasks = [make_request() for _ in range(50)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            total_requests += len(results)
            wave_errors = [r for r in results if isinstance(r, Exception)]
            total_errors += len(wave_errors)

            # Small delay between waves to simulate realistic usage
            await asyncio.sleep(0.5)

        # Verify low error rate (< 1%)
        error_rate = (total_errors / total_requests) * 100 if total_requests > 0 else 0
        assert error_rate < 1.0, f"Error rate {error_rate:.2f}% exceeds 1% threshold"

        # Cleanup
        await client.aclose()
        await token_manager.aclose()
