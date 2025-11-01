"""Rate limiting middleware with industry-standard headers.

Provides transparent rate limiting with X-RateLimit-* headers for all responses.
Issue #008-US2: Add rate limit visibility for API consumers.
"""

import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Middleware that adds rate limit headers to all responses.

    Implements industry-standard rate limit headers:
    - X-RateLimit-Limit: Maximum requests allowed per window
    - X-RateLimit-Remaining: Requests remaining in current window
    - X-RateLimit-Reset: Unix timestamp when window resets
    """

    def __init__(self, app: ASGIApp, ip_limit: int = 15, time_window: int = 10) -> None:
        """Initialize rate limiter middleware.

        Args:
            app: FastAPI application
            ip_limit: Maximum requests per time window (default: 15)
            time_window: Time window in seconds (default: 10)
        """
        super().__init__(app)
        self.ip_limit = ip_limit
        self.time_window = time_window

        # In-memory rate limit tracking (per IP)
        # Structure: {ip: {"count": int, "window_start": float}}
        self._rate_limits: dict[str, dict[str, Any]] = {}

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request.

        Args:
            request: Incoming HTTP request

        Returns:
            Client IP address string
        """
        if request.client:
            return request.client.host
        return "unknown"

    def _get_rate_limit_info(self, client_ip: str) -> dict[str, int]:
        """Calculate current rate limit information for a client.

        Args:
            client_ip: Client IP address

        Returns:
            Dictionary with limit, remaining, and reset_time
        """
        current_time = time.time()

        # Get or initialize rate limit state for this IP
        if client_ip not in self._rate_limits:
            self._rate_limits[client_ip] = {
                "count": 0,
                "window_start": current_time,
            }

        state = self._rate_limits[client_ip]
        window_start = state["window_start"]
        count = state["count"]

        # Check if window has expired
        elapsed = current_time - window_start
        if elapsed >= self.time_window:
            # Reset window
            state["window_start"] = current_time
            state["count"] = 0
            count = 0
            window_start = current_time

        # Calculate remaining requests and reset time
        remaining = max(0, self.ip_limit - count)
        reset_time = int(window_start + self.time_window)

        return {
            "limit": self.ip_limit,
            "remaining": remaining,
            "reset_time": reset_time,
        }

    def _increment_rate_limit(self, client_ip: str) -> None:
        """Increment request count for a client.

        Args:
            client_ip: Client IP address
        """
        if client_ip in self._rate_limits:
            self._rate_limits[client_ip]["count"] += 1

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Add rate limit headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with rate limit headers
        """
        # Get client IP
        client_ip = self._get_client_ip(request)

        # Get current rate limit info
        rate_limit_info = self._get_rate_limit_info(client_ip)

        # Store in request state for access in endpoints if needed
        request.state.rate_limit_info = rate_limit_info

        # Increment request count
        self._increment_rate_limit(client_ip)

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset_time"])

        # Check if rate limit exceeded (for next request)
        if rate_limit_info["remaining"] == 0:
            # Add Retry-After header for convenience
            retry_after = rate_limit_info["reset_time"] - int(time.time())
            if retry_after > 0:
                response.headers["Retry-After"] = str(retry_after)

        return response
