"""HTTP client for Hostaway API with connection pooling, rate limiting, and retry logic.

Provides a singleton AsyncClient configured for optimal performance and reliability
when communicating with Hostaway API endpoints.
"""

from typing import Any

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
        rate_limiter: RateLimiter | None = None,
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
        params: dict[str, Any] | None = None,
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
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
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
        json: dict[str, Any] | None = None,
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

    # Listings API methods

    async def get_listings(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Retrieve property listings with pagination.

        Args:
            limit: Maximum number of results to return (default: 100)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            List of listing dictionaries from API response

        Raises:
            httpx.HTTPStatusError: If API returns error status code
        """
        response = await self.get(
            "/listings",
            params={"limit": limit, "offset": offset},
        )
        # Hostaway wraps results in a "result" field
        return response.get("result", [])

    async def get_listing(self, listing_id: int) -> dict[str, Any]:
        """Retrieve detailed information for a specific property listing.

        Args:
            listing_id: Unique identifier for the listing

        Returns:
            Listing details dictionary from API response

        Raises:
            httpx.HTTPStatusError: If API returns error status code (e.g., 404 not found)
        """
        response = await self.get(f"/listings/{listing_id}")
        # Hostaway wraps result in a "result" field
        return response.get("result", {})

    async def get_listing_availability(
        self,
        listing_id: int,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        """Retrieve availability calendar for a listing.

        Args:
            listing_id: Unique identifier for the listing
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)

        Returns:
            List of availability records for each date in range

        Raises:
            httpx.HTTPStatusError: If API returns error status code
        """
        response = await self.get(
            f"/listings/{listing_id}/calendar",
            params={"startDate": start_date, "endDate": end_date},
        )
        # Hostaway wraps results in a "result" field
        return response.get("result", [])

    # Bookings/Reservations API methods

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
        """Search bookings/reservations with filters.

        Args:
            listing_id: Filter by specific property ID
            check_in_from: Filter bookings with check-in on or after this date (YYYY-MM-DD)
            check_in_to: Filter bookings with check-in on or before this date (YYYY-MM-DD)
            check_out_from: Filter bookings with check-out on or after this date (YYYY-MM-DD)
            check_out_to: Filter bookings with check-out on or before this date (YYYY-MM-DD)
            status: Filter by booking status (multiple allowed)
            guest_email: Filter by guest email address
            booking_source: Filter by booking channel (airbnb, vrbo, etc.)
            min_guests: Filter bookings with at least this many guests
            max_guests: Filter bookings with at most this many guests
            limit: Maximum number of results to return (default: 100)
            offset: Number of results to skip for pagination (default: 0)

        Returns:
            List of booking dictionaries from API response

        Raises:
            httpx.HTTPStatusError: If API returns error status code
        """
        # Build query parameters, only including non-None values
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        if listing_id is not None:
            params["listingId"] = listing_id
        if check_in_from is not None:
            params["checkInFrom"] = check_in_from
        if check_in_to is not None:
            params["checkInTo"] = check_in_to
        if check_out_from is not None:
            params["checkOutFrom"] = check_out_from
        if check_out_to is not None:
            params["checkOutTo"] = check_out_to
        if status is not None:
            params["status"] = ",".join(status)
        if guest_email is not None:
            params["guestEmail"] = guest_email
        if booking_source is not None:
            params["channelName"] = booking_source
        if min_guests is not None:
            params["minGuests"] = min_guests
        if max_guests is not None:
            params["maxGuests"] = max_guests

        response = await self.get("/reservations", params=params)
        # Hostaway wraps results in a "result" field
        return response.get("result", [])

    async def get_booking(self, booking_id: int) -> dict[str, Any]:
        """Retrieve detailed information for a specific booking/reservation.

        Args:
            booking_id: Unique identifier for the booking

        Returns:
            Booking details dictionary from API response

        Raises:
            httpx.HTTPStatusError: If API returns error status code (e.g., 404 not found)
        """
        response = await self.get(f"/reservations/{booking_id}")
        # Hostaway wraps result in a "result" field
        return response.get("result", {})

    async def get_booking_guest(self, booking_id: int) -> dict[str, Any]:
        """Retrieve guest information for a specific booking/reservation.

        Args:
            booking_id: Unique identifier for the booking

        Returns:
            Guest details dictionary from API response

        Raises:
            httpx.HTTPStatusError: If API returns error status code (e.g., 404 not found)
        """
        response = await self.get(f"/reservations/{booking_id}/guest")
        # Hostaway wraps result in a "result" field
        return response.get("result", {})

    # Financial Reports API methods

    async def get_financial_report(
        self,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """Retrieve financial report for date range.

        Args:
            start_date: Report start date in ISO format (YYYY-MM-DD)
            end_date: Report end date in ISO format (YYYY-MM-DD)

        Returns:
            Financial report with revenue, expenses, and profitability metrics

        Raises:
            httpx.HTTPStatusError: If API returns error status code (e.g., 400 for invalid dates)
        """
        response = await self.get(
            "/financialReports",
            params={"startDate": start_date, "endDate": end_date},
        )
        # Hostaway wraps result in a "result" field
        return response.get("result", {})

    async def get_property_financials(
        self,
        property_id: int,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """Retrieve financial report for a specific property.

        Args:
            property_id: Unique identifier for the property
            start_date: Report start date in ISO format (YYYY-MM-DD)
            end_date: Report end date in ISO format (YYYY-MM-DD)

        Returns:
            Property-specific financial report

        Raises:
            httpx.HTTPStatusError: If API returns error status code
        """
        response = await self.get(
            "/financialReports",
            params={
                "startDate": start_date,
                "endDate": end_date,
                "listingId": property_id,
            },
        )
        # Hostaway wraps result in a "result" field
        return response.get("result", {})

    async def execute_batch(
        self,
        operations: list,  # List of async callables
        operation_ids: list[str] | None = None,
    ):  # type: ignore[no-untyped-def]
        """Execute multiple operations and return partial success results.

        Executes all operations independently, capturing successes and failures.
        Returns a PartialFailureResponse containing both successful and failed results.

        Example:
            >>> operations = [
            ...     lambda: client.get_listing(1),
            ...     lambda: client.get_listing(999),  # May fail
            ...     lambda: client.get_listing(3),
            ... ]
            >>> result = await client.execute_batch(operations)
            >>> result.success_count  # 2 (listings 1 and 3)
            >>> result.failure_count  # 1 (listing 999 not found)

        Args:
            operations: List of async callables to execute
            operation_ids: Optional IDs for tracking each operation

        Returns:
            PartialFailureResponse with successful and failed operations

        Raises:
            No exceptions - all failures are captured in the response
        """
        from src.mcp.logging import get_logger
        from src.models.errors import OperationResult, PartialFailureResponse

        logger = get_logger(__name__)

        if operation_ids is None:
            operation_ids = [f"op_{i}" for i in range(len(operations))]

        successful: list[OperationResult[Any]] = []
        failed: list[OperationResult[Any]] = []

        # Execute all operations, capturing individual results
        for op_id, operation in zip(operation_ids, operations, strict=False):
            try:
                result = await operation()
                successful.append(
                    OperationResult[Any](
                        success=True,
                        data=result,
                        operation_id=op_id,
                    )
                )
            except Exception as e:
                logger.warning(
                    f"Batch operation {op_id} failed",
                    extra={"operation_id": op_id, "error": str(e), "error_type": type(e).__name__},
                )
                failed.append(
                    OperationResult[Any](
                        success=False,
                        error=str(e),
                        operation_id=op_id,
                    )
                )

        return PartialFailureResponse[Any](
            successful=successful,
            failed=failed,
            total_count=len(operations),
            success_count=len(successful),
            failure_count=len(failed),
        )

    async def aclose(self) -> None:
        """Close the HTTP client and cleanup resources.

        This should be called during application shutdown to gracefully
        close all connections.
        """
        await self._client.aclose()
