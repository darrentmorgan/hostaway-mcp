"""HTTP client for Hostaway API with connection pooling, rate limiting, and retry logic.

Provides a singleton AsyncClient configured for optimal performance and reliability
when communicating with Hostaway API endpoints.
"""

from typing import Any, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.mcp.auth import TokenManager
from src.mcp.config import HostawayConfig
from src.services.rate_limiter import RateLimiter


class HostawayClient:
    """Async HTTP client for Hostaway API with rate limiting and retry logic.

    Features:
    - Connection pooling for improved performance
    - Exponential backoff retry logic for transient failures
    - Automatic token refresh on 401 errors
    - Rate limiting to prevent API lockout
    - Proper timeout configuration for external API calls

    This client should be used as a singleton within the application lifecycle.
    """

    def __init__(
        self,
        config: HostawayConfig,
        token_manager: TokenManager,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        """Initialize Hostaway API client.

        Args:
            config: Hostaway configuration with API base URL and limits
            token_manager: Manager for OAuth token acquisition and refresh
            rate_limiter: Optional rate limiter (creates default if None)
        """
        self.config = config
        self.token_manager = token_manager
        self.rate_limiter = rate_limiter or RateLimiter(
            ip_rate_limit=config.rate_limit_ip,
            account_rate_limit=config.rate_limit_account,
            max_concurrent=config.max_concurrent_requests,
        )

        # Configure connection pooling
        limits = httpx.Limits(
            max_keepalive_connections=20,  # Reuse up to 20 connections
            max_connections=50,  # Total connection limit
            keepalive_expiry=30.0,  # Close idle connections after 30s
        )

        # Configure timeouts
        timeout = httpx.Timeout(
            connect=5.0,  # 5s to establish connection
            read=30.0,  # 30s to read response
            write=10.0,  # 10s to send request
            pool=5.0,  # 5s to acquire connection from pool
        )

        # Create async client with connection pooling
        self._client = httpx.AsyncClient(
            base_url=config.api_base_url,
            limits=limits,
            timeout=timeout,
            http2=False,  # Disable HTTP/2 (requires httpx[http2])
            follow_redirects=True,
        )

    async def get(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make GET request to Hostaway API.

        Args:
            endpoint: API endpoint path (e.g., "/listings")
            params: Optional query parameters
            **kwargs: Additional arguments passed to httpx.get()

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPStatusError: If API returns error status code
            httpx.TimeoutException: If request times out after retries
            httpx.NetworkError: If network error occurs after retries
        """
        return await self._request("GET", endpoint, params=params, **kwargs)

    async def post(
        self,
        endpoint: str,
        json: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make POST request to Hostaway API.

        Args:
            endpoint: API endpoint path (e.g., "/reservations")
            json: Optional JSON request body
            data: Optional form data
            **kwargs: Additional arguments passed to httpx.post()

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPStatusError: If API returns error status code
            httpx.TimeoutException: If request times out after retries
            httpx.NetworkError: If network error occurs after retries
        """
        return await self._request("POST", endpoint, json=json, data=data, **kwargs)

    async def put(
        self,
        endpoint: str,
        json: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make PUT request to Hostaway API.

        Args:
            endpoint: API endpoint path (e.g., "/listings/{id}")
            json: Optional JSON request body
            **kwargs: Additional arguments passed to httpx.put()

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPStatusError: If API returns error status code
            httpx.TimeoutException: If request times out after retries
            httpx.NetworkError: If network error occurs after retries
        """
        return await self._request("PUT", endpoint, json=json, **kwargs)

    async def delete(
        self,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make DELETE request to Hostaway API.

        Args:
            endpoint: API endpoint path (e.g., "/calendar/block/{id}")
            **kwargs: Additional arguments passed to httpx.delete()

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPStatusError: If API returns error status code
            httpx.TimeoutException: If request times out after retries
            httpx.NetworkError: If network error occurs after retries
        """
        return await self._request("DELETE", endpoint, **kwargs)

    @retry(
        wait=wait_exponential(multiplier=2, min=2, max=8),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError)
        ),
        reraise=True,
    )
    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request with exponential backoff retry logic.

        This method implements retry logic for transient failures:
        - 3 retry attempts (total 4 attempts including initial)
        - Exponential backoff: 2s, 4s, 8s
        - Only retries on network/timeout errors, not client errors (4xx)

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional arguments passed to httpx.request()

        Returns:
            HTTP response object

        Raises:
            httpx.TimeoutException: If all retries exhausted due to timeout
            httpx.NetworkError: If all retries exhausted due to network error
        """
        # Get fresh token for each request attempt
        token = await self.token_manager.get_token()

        # Add Authorization header
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token.access_token}"

        # Make request with rate limiting
        async with self.rate_limiter.acquire():
            response = await self._client.request(method, endpoint, headers=headers, **kwargs)

        return response

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Internal method to make authenticated API request.

        Handles token refresh on 401 errors and response validation.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional arguments passed to httpx.request()

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPStatusError: If API returns error status code
        """
        try:
            response = await self._request_with_retry(method, endpoint, **kwargs)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except httpx.HTTPStatusError as e:
            # Handle token expiration - invalidate and retry once
            if e.response.status_code == 401:
                await self.token_manager.invalidate_token()
                # Retry once with fresh token
                response = await self._request_with_retry(method, endpoint, **kwargs)
                response.raise_for_status()
                result_retry: dict[str, Any] = response.json()
                return result_retry
            # Re-raise other HTTP errors
            raise

    async def aclose(self) -> None:
        """Close the HTTP client and cleanup resources.

        This should be called during application shutdown to gracefully
        close all connections.
        """
        await self._client.aclose()
