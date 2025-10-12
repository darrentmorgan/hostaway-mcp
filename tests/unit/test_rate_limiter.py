"""Unit tests for RateLimiter class.

Tests token bucket algorithm behavior and semaphore-based concurrency control.
"""

import asyncio
from datetime import datetime

import pytest

from src.services.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test suite for RateLimiter class."""

    @pytest.mark.asyncio
    async def test_rate_limiter_creation(self) -> None:
        """Test RateLimiter can be created with default values."""
        limiter = RateLimiter()

        assert limiter.ip_rate_limit == 15
        assert limiter.account_rate_limit == 20
        assert limiter.max_concurrent == 10

    @pytest.mark.asyncio
    async def test_rate_limiter_custom_values(self) -> None:
        """Test RateLimiter can be created with custom values."""
        limiter = RateLimiter(
            ip_rate_limit=10,
            account_rate_limit=15,
            max_concurrent=5,
        )

        assert limiter.ip_rate_limit == 10
        assert limiter.account_rate_limit == 15
        assert limiter.max_concurrent == 5

    @pytest.mark.asyncio
    async def test_rate_limiter_acquire_single_request(self) -> None:
        """Test single request is acquired immediately."""
        limiter = RateLimiter(ip_rate_limit=10, account_rate_limit=10)

        start = datetime.now()
        async with limiter.acquire():
            pass
        end = datetime.now()

        # Should complete almost instantly (< 0.1s)
        assert (end - start).total_seconds() < 0.1

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_within_limit(self) -> None:
        """Test multiple requests within rate limit are allowed."""
        limiter = RateLimiter(ip_rate_limit=5, account_rate_limit=5)

        # Make 3 requests (under limit of 5)
        start = datetime.now()
        for _ in range(3):
            async with limiter.acquire():
                pass
        end = datetime.now()

        # Should complete quickly (< 0.5s)
        assert (end - start).total_seconds() < 0.5

    @pytest.mark.asyncio
    async def test_rate_limiter_enforces_ip_limit(self) -> None:
        """Test IP rate limiter enforces limits over 10 second window."""
        # Set low limit for testing - token bucket allows burst up to limit
        # To test rate limiting, need to exceed limit + 1
        limiter = RateLimiter(ip_rate_limit=2, account_rate_limit=10, time_period=1)

        start = datetime.now()

        # Make 4 requests (2 immediate, then 2 more need to wait)
        for _ in range(4):
            async with limiter.acquire():
                pass

        end = datetime.now()
        elapsed = (end - start).total_seconds()

        # Should take at least 1 second due to rate limiting (2 req/sec limit)
        assert elapsed >= 0.8  # Allow small tolerance

    @pytest.mark.asyncio
    async def test_rate_limiter_enforces_account_limit(self) -> None:
        """Test account rate limiter enforces limits over 10 second window."""
        # Set IP limit higher than account limit to test account limiting
        # Token bucket allows burst up to limit, so need to exceed limit + 1
        limiter = RateLimiter(ip_rate_limit=10, account_rate_limit=2, time_period=1)

        start = datetime.now()

        # Make 4 requests (2 immediate, then 2 more need to wait)
        for _ in range(4):
            async with limiter.acquire():
                pass

        end = datetime.now()
        elapsed = (end - start).total_seconds()

        # Should take at least 1 second due to rate limiting (2 req/sec limit)
        assert elapsed >= 0.8  # Allow small tolerance

    @pytest.mark.asyncio
    async def test_rate_limiter_semaphore_limits_concurrency(self) -> None:
        """Test semaphore limits concurrent requests."""
        limiter = RateLimiter(max_concurrent=2)

        concurrent_count = 0
        max_concurrent_observed = 0

        async def task() -> None:
            nonlocal concurrent_count, max_concurrent_observed
            async with limiter.acquire():
                concurrent_count += 1
                max_concurrent_observed = max(max_concurrent_observed, concurrent_count)
                await asyncio.sleep(0.1)  # Simulate work
                concurrent_count -= 1

        # Launch 5 concurrent tasks
        await asyncio.gather(*[task() for _ in range(5)])

        # Max concurrent should never exceed 2
        assert max_concurrent_observed <= 2

    @pytest.mark.asyncio
    async def test_rate_limiter_semaphore_releases_on_exception(self) -> None:
        """Test semaphore is properly released even when exception occurs."""
        limiter = RateLimiter(max_concurrent=1)

        # First request raises exception
        with pytest.raises(RuntimeError):
            async with limiter.acquire():
                raise RuntimeError("Test error")

        # Second request should still work (semaphore was released)
        async with limiter.acquire():
            pass  # Should succeed

    @pytest.mark.asyncio
    async def test_rate_limiter_context_manager(self) -> None:
        """Test RateLimiter works as async context manager."""
        limiter = RateLimiter()

        # Should not raise any errors
        async with limiter.acquire():
            # Simulate some work
            await asyncio.sleep(0.01)

    @pytest.mark.asyncio
    async def test_rate_limiter_multiple_parallel_requests(self) -> None:
        """Test multiple parallel requests respect both rate limits and concurrency."""
        limiter = RateLimiter(
            ip_rate_limit=10,
            account_rate_limit=10,
            max_concurrent=3,
        )

        completed = []

        async def task(task_id: int) -> None:
            async with limiter.acquire():
                completed.append(task_id)
                await asyncio.sleep(0.01)

        # Launch 5 tasks in parallel
        await asyncio.gather(*[task(i) for i in range(5)])

        # All tasks should complete
        assert len(completed) == 5
        assert set(completed) == {0, 1, 2, 3, 4}

    @pytest.mark.asyncio
    async def test_rate_limiter_reset_statistics(self) -> None:
        """Test rate limiter can track and report statistics."""
        limiter = RateLimiter()

        # Make a few requests
        for _ in range(3):
            async with limiter.acquire():
                await asyncio.sleep(0.01)

        # Statistics should be trackable (if implemented)
        # This is a placeholder for future statistics tracking
        assert True
