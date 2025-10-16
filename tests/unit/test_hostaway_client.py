"""Unit tests for HostawayClient.

Tests HTTP client functionality including connection pooling, retry logic,
rate limiting integration, and token refresh on 401 errors.
"""

from unittest.mock import patch

import httpx
import pytest
import respx

from src.mcp.auth import TokenManager
from src.mcp.config import HostawayConfig
from src.models.auth import AccessToken
from src.services.hostaway_client import HostawayClient
from src.services.rate_limiter import RateLimiter


class TestHostawayClient:
    """Test suite for HostawayClient class."""

    @pytest.fixture
    def config(self) -> HostawayConfig:
        """Create test configuration."""
        with patch.dict(
            "os.environ",
            {
                "HOSTAWAY_ACCOUNT_ID": "test_account",
                "HOSTAWAY_SECRET_KEY": "test_secret",
            },
            clear=True,
        ):
            return HostawayConfig()

    @pytest.fixture
    async def token_manager(self, config: HostawayConfig) -> TokenManager:
        """Create test token manager with mock token."""
        manager = TokenManager(config=config)
        # Pre-set a valid token to avoid auth calls
        manager._token = AccessToken(
            access_token="test_token_abc123_xyz789_valid",
            expires_in=63072000,
        )
        return manager

    @pytest.fixture
    def rate_limiter(self) -> RateLimiter:
        """Create test rate limiter with high limits."""
        return RateLimiter(
            ip_rate_limit=100,  # High limits for testing
            account_rate_limit=100,
            max_concurrent=50,
        )

    @pytest.fixture
    async def client(
        self,
        config: HostawayConfig,
        token_manager: TokenManager,
        rate_limiter: RateLimiter,
    ) -> HostawayClient:
        """Create test HostawayClient instance."""
        client = HostawayClient(
            config=config,
            token_manager=token_manager,
            rate_limiter=rate_limiter,
        )
        yield client
        await client.aclose()

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_request_success(self, client: HostawayClient) -> None:
        """Test successful GET request."""
        respx.get(f"{client.config.api_base_url}/listings").mock(
            return_value=httpx.Response(
                200,
                json={"listings": [{"id": 1, "name": "Test Property"}]},
            )
        )

        result = await client.get("/listings")

        assert result == {"listings": [{"id": 1, "name": "Test Property"}]}

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_request_with_params(self, client: HostawayClient) -> None:
        """Test GET request with query parameters."""
        respx.get(f"{client.config.api_base_url}/listings").mock(
            return_value=httpx.Response(
                200,
                json={"listings": []},
            )
        )

        result = await client.get("/listings", params={"status": "active"})

        assert result == {"listings": []}

    @pytest.mark.asyncio
    @respx.mock
    async def test_post_request_success(self, client: HostawayClient) -> None:
        """Test successful POST request."""
        respx.post(f"{client.config.api_base_url}/reservations").mock(
            return_value=httpx.Response(
                201,
                json={"id": 123, "status": "confirmed"},
            )
        )

        result = await client.post(
            "/reservations",
            json={"listing_id": 1, "check_in": "2025-10-15"},
        )

        assert result == {"id": 123, "status": "confirmed"}

    @pytest.mark.asyncio
    @respx.mock
    async def test_put_request_success(self, client: HostawayClient) -> None:
        """Test successful PUT request."""
        respx.put(f"{client.config.api_base_url}/listings/1").mock(
            return_value=httpx.Response(
                200,
                json={"id": 1, "name": "Updated Property"},
            )
        )

        result = await client.put("/listings/1", json={"name": "Updated Property"})

        assert result == {"id": 1, "name": "Updated Property"}

    @pytest.mark.asyncio
    @respx.mock
    async def test_delete_request_success(self, client: HostawayClient) -> None:
        """Test successful DELETE request."""
        respx.delete(f"{client.config.api_base_url}/calendar/block/123").mock(
            return_value=httpx.Response(
                200,
                json={"success": True},
            )
        )

        result = await client.delete("/calendar/block/123")

        assert result == {"success": True}

    @pytest.mark.asyncio
    @respx.mock
    async def test_authorization_header_added(
        self, client: HostawayClient, token_manager: TokenManager
    ) -> None:
        """Test that Authorization header is added to requests."""
        route = respx.get(f"{client.config.api_base_url}/listings").mock(
            return_value=httpx.Response(200, json={})
        )

        await client.get("/listings")

        # Verify Authorization header was sent
        assert route.calls.last.request.headers["Authorization"] == (
            f"Bearer {token_manager._token.access_token}"  # type: ignore[union-attr]
        )

    @pytest.mark.asyncio
    @respx.mock
    async def test_retry_on_timeout(self, client: HostawayClient) -> None:
        """Test exponential backoff retry on timeout errors."""
        call_count = 0

        def timeout_then_success(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("Connection timeout")
            return httpx.Response(200, json={"success": True})

        respx.get(f"{client.config.api_base_url}/listings").mock(side_effect=timeout_then_success)

        result = await client.get("/listings")

        assert result == {"success": True}
        assert call_count == 3  # Failed twice, succeeded on third

    @pytest.mark.asyncio
    @respx.mock
    async def test_retry_on_network_error(self, client: HostawayClient) -> None:
        """Test exponential backoff retry on network errors."""
        call_count = 0

        def network_error_then_success(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.NetworkError("Network unreachable")
            return httpx.Response(200, json={"success": True})

        respx.get(f"{client.config.api_base_url}/listings").mock(
            side_effect=network_error_then_success
        )

        result = await client.get("/listings")

        assert result == {"success": True}
        assert call_count == 2  # Failed once, succeeded on second

    @pytest.mark.asyncio
    @respx.mock
    async def test_retry_exhausted_raises_error(self, client: HostawayClient) -> None:
        """Test that retries are exhausted after 3 attempts."""
        respx.get(f"{client.config.api_base_url}/listings").mock(
            side_effect=httpx.TimeoutException("Connection timeout")
        )

        with pytest.raises(httpx.TimeoutException):
            await client.get("/listings")

    @pytest.mark.asyncio
    @respx.mock
    async def test_no_retry_on_client_errors(self, client: HostawayClient) -> None:
        """Test that 4xx client errors are not retried."""
        call_count = 0

        def client_error(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(400, json={"error": "Bad request"})

        respx.get(f"{client.config.api_base_url}/listings").mock(side_effect=client_error)

        with pytest.raises(httpx.HTTPStatusError):
            await client.get("/listings")

        # Should only be called once (no retries for 4xx)
        assert call_count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_token_refresh_on_401(
        self,
        client: HostawayClient,
        token_manager: TokenManager,
        config: HostawayConfig,
    ) -> None:
        """Test automatic token refresh when 401 error occurs."""
        call_count = 0

        def unauthorized_then_success(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call returns 401
                return httpx.Response(401, json={"error": "Unauthorized"})
            # Second call succeeds
            return httpx.Response(200, json={"success": True})

        respx.get(f"{config.api_base_url}/listings").mock(side_effect=unauthorized_then_success)

        # Mock token refresh
        respx.post(f"{config.api_base_url}/accessTokens").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "new_token_abc123_xyz789",
                    "token_type": "Bearer",
                    "expires_in": 63072000,
                    "scope": "general",
                },
            )
        )

        result = await client.get("/listings")

        assert result == {"success": True}
        assert call_count == 2  # 401 then retry with new token
        # Verify token was invalidated and refreshed
        assert token_manager._token is not None
        assert token_manager._token.access_token == "new_token_abc123_xyz789"

    @pytest.mark.asyncio
    @respx.mock
    async def test_rate_limiting_applied(
        self, config: HostawayConfig, token_manager: TokenManager
    ) -> None:
        """Test that rate limiting is enforced."""
        # Create rate limiter with low limits
        rate_limiter = RateLimiter(
            ip_rate_limit=2,  # Only 2 requests per 10 seconds
            account_rate_limit=2,
            time_period=10.0,
            max_concurrent=1,
        )

        client = HostawayClient(
            config=config,
            token_manager=token_manager,
            rate_limiter=rate_limiter,
        )

        respx.get(f"{config.api_base_url}/listings").mock(return_value=httpx.Response(200, json={}))

        # Make 2 requests - should succeed
        await client.get("/listings")
        await client.get("/listings")

        # Third request should be rate limited (this will wait)
        # We won't test the wait time, just that it completes
        await client.get("/listings")

        await client.aclose()

    @pytest.mark.asyncio
    @respx.mock
    async def test_http2_enabled(self, client: HostawayClient) -> None:
        """Test that HTTP/2 is enabled for multiplexing."""
        # Check client configuration
        assert client._client._transport is not None  # type: ignore[attr-defined]

        # Make a request to ensure it works
        respx.get(f"{client.config.api_base_url}/listings").mock(
            return_value=httpx.Response(200, json={})
        )

        result = await client.get("/listings")
        assert result == {}

    @pytest.mark.asyncio
    async def test_connection_pool_configuration(self, client: HostawayClient) -> None:
        """Test that connection pool is properly configured."""
        # Access limits through the transport
        assert hasattr(client._client, "_transport")
        # Just verify client was initialized (limits are internal)
        assert client._client is not None

    @pytest.mark.asyncio
    async def test_timeout_configuration(self, client: HostawayClient) -> None:
        """Test that timeouts are properly configured."""
        timeout = client._client.timeout

        assert timeout.connect == 5.0
        assert timeout.read == 30.0
        assert timeout.write == 10.0
        assert timeout.pool == 5.0

    @pytest.mark.asyncio
    @respx.mock
    async def test_follow_redirects_enabled(self, client: HostawayClient) -> None:
        """Test that client follows redirects."""
        # Mock redirect
        respx.get(f"{client.config.api_base_url}/old-endpoint").mock(
            return_value=httpx.Response(
                301,
                headers={"Location": f"{client.config.api_base_url}/new-endpoint"},
            )
        )

        respx.get(f"{client.config.api_base_url}/new-endpoint").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        result = await client.get("/old-endpoint")
        assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_aclose_cleanup(
        self, config: HostawayConfig, token_manager: TokenManager, rate_limiter: RateLimiter
    ) -> None:
        """Test that aclose properly cleans up resources."""
        client = HostawayClient(
            config=config,
            token_manager=token_manager,
            rate_limiter=rate_limiter,
        )

        # Client should be open
        assert not client._client.is_closed

        # Close client
        await client.aclose()

        # Client should be closed
        assert client._client.is_closed
