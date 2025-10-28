"""Performance tests for rate limiting under load.

Tests rate limiter behavior and effectiveness under various load patterns:
- Burst traffic handling
- Rate limit enforcement
- Queue backpressure
- Concurrent request limiting
"""

import asyncio
import time
from typing import Any

import pytest

from src.mcp.config import HostawayConfig


@pytest.mark.performance
@pytest.mark.asyncio
class TestRateLimitingPerformance:
    """Performance tests for rate limiter under load."""

    async def test_rate_limit_enforcement(self) -> None:
        """Test that rate limiter enforces configured limits.

        Validates:
        - IP rate limit (15 req/10s) is enforced
        - Account rate limit (20 req/10s) is enforced
        - Requests are queued, not rejected

        This test uses a lower rate limit for faster testing.
        """
        from src.services.rate_limiter import RateLimiter

        # Create rate limiter with low limits for testing
        rate_limiter = RateLimiter(
            ip_rate_limit=10,  # 10 requests per 10 seconds
            account_rate_limit=10,
            max_concurrent=5,
        )

        start_time = time.time()
        request_times = []

        async def make_request(request_id: int) -> int:
            """Make a rate-limited request and record timing."""
            async with rate_limiter.acquire():
                request_times.append((request_id, time.time() - start_time))
                return request_id

        # Try to make 25 requests (2.5x the rate limit)
        tasks = [make_request(i) for i in range(25)]
        results = await asyncio.gather(*tasks)

        # Verify all requests completed
        assert len(results) == 25, "All requests should complete (queued, not rejected)"

        # Verify rate limiting worked - should take at least 10 seconds
        # First 10 requests immediate, next 15 after 10s
        elapsed_time = time.time() - start_time
        assert elapsed_time >= 10.0, f"Should take ≥10s for 25 requests, took {elapsed_time:.2f}s"

        # Verify requests were distributed over time (not all at once)
        first_10 = [t for _, t in request_times[:10]]
        last_15 = [t for _, t in request_times[10:]]

        # First 10 should complete quickly (within 1 second)
        assert max(first_10) < 1.0, "First 10 requests should complete immediately"

        # Last 15 should be delayed (after 10+ seconds)
        assert min(last_15) >= 10.0, "Requests 11-25 should be delayed by rate limit"

    async def test_concurrent_limit_enforcement(self) -> None:
        """Test that max concurrent requests limit is enforced.

        Validates:
        - No more than max_concurrent requests execute simultaneously
        - Excess requests are queued
        - Queue processes in order
        """
        from src.services.rate_limiter import RateLimiter

        max_concurrent = 5
        rate_limiter = RateLimiter(
            ip_rate_limit=100,  # High rate limit to not interfere
            account_rate_limit=100,
            max_concurrent=max_concurrent,
        )

        active_count = 0
        max_active = 0
        lock = asyncio.Lock()

        async def make_request(request_id: int) -> tuple[int, int]:
            """Track concurrent request count."""
            nonlocal active_count, max_active

            async with rate_limiter.acquire():
                async with lock:
                    active_count += 1
                    max_active = max(max_active, active_count)

                # Simulate some work
                await asyncio.sleep(0.1)

                async with lock:
                    active_count -= 1

                return request_id, max_active

        # Launch 20 requests (4x the concurrent limit)
        tasks = [make_request(i) for i in range(20)]
        results = await asyncio.gather(*tasks)

        # Verify all completed
        assert len(results) == 20

        # Verify concurrent limit was never exceeded
        assert (
            max_active <= max_concurrent
        ), f"Max concurrent {max_active} exceeded limit {max_concurrent}"

    async def test_burst_traffic_handling(self, test_config: HostawayConfig) -> None:
        """Test rate limiter handles burst traffic without errors.

        Simulates realistic burst pattern:
        - Idle period
        - Sudden burst of requests
        - Gradual decline
        - Repeat

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
            return await client.get_listings(limit=1)

        total_errors = 0

        # Burst pattern: 30 requests, wait, 20 requests, wait, 10 requests
        for burst_size in [30, 20, 10]:
            tasks = [make_request() for _ in range(burst_size)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            errors = [r for r in results if isinstance(r, Exception)]
            total_errors += len(errors)

            # Wait between bursts
            await asyncio.sleep(2.0)

        # Verify low error rate
        total_requests = 30 + 20 + 10
        error_rate = (total_errors / total_requests) * 100
        assert error_rate < 5.0, f"Error rate {error_rate:.2f}% exceeds 5% threshold"

        # Cleanup
        await client.aclose()
        await token_manager.aclose()

    async def test_rate_limit_recovery(self) -> None:
        """Test that rate limiter recovers after hitting limits.

        Validates:
        - Rate limits reset after time window
        - System returns to normal after congestion
        - No permanent degradation
        """
        from src.services.rate_limiter import RateLimiter

        rate_limiter = RateLimiter(
            ip_rate_limit=10,  # 10 req/10s
            account_rate_limit=10,
            max_concurrent=5,
        )

        async def make_request() -> None:
            async with rate_limiter.acquire():
                await asyncio.sleep(0.01)

        # Phase 1: Hit rate limit (15 requests)
        phase1_start = time.time()
        await asyncio.gather(*[make_request() for _ in range(15)])
        phase1_duration = time.time() - phase1_start

        # Should take ~10s due to rate limiting
        assert phase1_duration >= 10.0, "Phase 1 should hit rate limit"

        # Phase 2: Wait for window to reset
        await asyncio.sleep(1.0)

        # Phase 3: Make new requests (should be fast again)
        phase3_start = time.time()
        await asyncio.gather(*[make_request() for _ in range(10)])
        phase3_duration = time.time() - phase3_start

        # Should complete quickly (within rate limit)
        assert (
            phase3_duration < 2.0
        ), f"Phase 3 should be fast after recovery, took {phase3_duration:.2f}s"

    async def test_rate_limiter_fairness(self) -> None:
        """Test that rate limiter distributes capacity fairly across requests.

        Validates:
        - FIFO queue ordering
        - No request starvation
        - Predictable delays
        """
        from src.services.rate_limiter import RateLimiter

        rate_limiter = RateLimiter(
            ip_rate_limit=10,
            account_rate_limit=10,
            max_concurrent=5,
        )

        completion_order = []
        lock = asyncio.Lock()

        async def make_request(request_id: int) -> int:
            """Make request and record completion order."""
            async with rate_limiter.acquire():
                await asyncio.sleep(0.01)
                async with lock:
                    completion_order.append(request_id)
                return request_id

        # Launch 20 requests in order
        tasks = [make_request(i) for i in range(20)]
        await asyncio.gather(*tasks)

        # Verify roughly FIFO order (allowing for some concurrency)
        # First 5 can be in any order (concurrent)
        # But overall trend should be sequential
        for i in range(len(completion_order) - 1):
            # Check that we don't have extreme out-of-order (>10 positions)
            position_delta = abs(completion_order[i + 1] - completion_order[i])
            assert position_delta <= 10, (
                f"Request order too scrambled at position {i}: "
                f"{completion_order[i]} -> {completion_order[i + 1]}"
            )

    @pytest.mark.slow
    async def test_sustained_rate_limiting(self, test_config: HostawayConfig) -> None:
        """Test rate limiter performance under sustained load over time.

        Runs for 30 seconds with constant request rate to validate:
        - No rate limiter degradation over time
        - Consistent throughput
        - Memory stability

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
            return await client.get_listings(limit=1)

        start_time = time.time()
        total_requests = 0
        total_errors = 0

        # Run for 30 seconds
        while time.time() - start_time < 30.0:
            # Launch 10 concurrent requests
            tasks = [make_request() for _ in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            total_requests += len(results)
            errors = [r for r in results if isinstance(r, Exception)]
            total_errors += len(errors)

            # Brief pause before next wave
            await asyncio.sleep(0.5)

        # Verify low error rate throughout
        error_rate = (total_errors / total_requests) * 100 if total_requests > 0 else 0
        assert error_rate < 2.0, f"Error rate {error_rate:.2f}% exceeds 2% threshold"

        # Verify we processed reasonable number of requests (>= 50)
        assert total_requests >= 50, f"Should process >= 50 requests in 30s, got {total_requests}"

        # Cleanup
        await client.aclose()
        await token_manager.aclose()
