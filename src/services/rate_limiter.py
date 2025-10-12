"""Rate limiting for Hostaway API requests.

Implements token bucket algorithm for IP and account-based rate limiting,
plus semaphore-based concurrency control.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from aiolimiter import AsyncLimiter


class RateLimiter:
    """Rate limiter combining token bucket algorithm and concurrency control.

    Hostaway API rate limits:
    - 15 requests per 10 seconds per IP address
    - 20 requests per 10 seconds per account
    - Additional concurrency limit to prevent connection pool exhaustion

    Uses aiolimiter's AsyncLimiter for token bucket implementation and
    asyncio.Semaphore for concurrency control.
    """

    def __init__(
        self,
        ip_rate_limit: int = 15,
        account_rate_limit: int = 20,
        time_period: float = 10.0,
        max_concurrent: int = 10,
    ) -> None:
        """Initialize rate limiter.

        Args:
            ip_rate_limit: Maximum requests per time_period for IP (default: 15)
            account_rate_limit: Maximum requests per time_period for account (default: 20)
            time_period: Time period in seconds for rate limits (default: 10.0)
            max_concurrent: Maximum concurrent requests (default: 10)
        """
        self.ip_rate_limit = ip_rate_limit
        self.account_rate_limit = account_rate_limit
        self.time_period = time_period
        self.max_concurrent = max_concurrent

        # Token bucket limiters
        self._ip_limiter = AsyncLimiter(max_rate=ip_rate_limit, time_period=time_period)
        self._account_limiter = AsyncLimiter(
            max_rate=account_rate_limit, time_period=time_period
        )

        # Concurrency control
        self._semaphore = asyncio.Semaphore(max_concurrent)

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[None]:
        """Acquire rate limit permission for a request.

        This async context manager enforces both rate limits (IP and account)
        and concurrency limits. It will wait (block) if limits are exceeded.

        Usage:
            async with rate_limiter.acquire():
                # Make API request here
                response = await client.get("/endpoint")

        Raises:
            Any exception raised within the context is re-raised after
            properly releasing the semaphore.
        """
        # Acquire semaphore first to limit concurrent requests
        async with self._semaphore:
            # Then enforce rate limits (token bucket)
            async with self._ip_limiter:
                async with self._account_limiter:
                    # All limits satisfied, allow request to proceed
                    yield
