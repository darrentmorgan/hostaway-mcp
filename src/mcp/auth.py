"""Token management for Hostaway OAuth 2.0 authentication.

Handles OAuth token exchange, automatic refresh, and thread-safe token storage.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import httpx

from src.mcp.config import HostawayConfig
from src.models.auth import AccessToken, TokenRefreshRequest, TokenRefreshResponse

if TYPE_CHECKING:
    from src.services.hostaway_client import HostawayClient

# Configure structured logging for authentication events
logger = logging.getLogger(__name__)


class TokenManager:
    """Manages OAuth 2.0 access tokens for Hostaway API.

    Features:
    - OAuth 2.0 Client Credentials Grant flow
    - Automatic token refresh before expiration
    - Thread-safe token storage using asyncio.Lock
    - Proactive refresh based on configurable threshold
    """

    def __init__(self, config: HostawayConfig, client: httpx.AsyncClient | None = None):
        """Initialize token manager.

        Args:
            config: Hostaway configuration with OAuth credentials
            client: Optional httpx client (for testing); creates new one if None
        """
        self.config = config
        self._client = client or httpx.AsyncClient(
            base_url=config.api_base_url,
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
        )
        self._token: AccessToken | None = None
        self._lock = asyncio.Lock()

    async def get_token(self) -> AccessToken:
        """Get a valid access token, refreshing if necessary.

        Returns:
            Valid AccessToken

        Raises:
            ValueError: If credentials are invalid
            PermissionError: If insufficient API permissions
            RuntimeError: If rate limit exceeded or token refresh fails
            ConnectionError: If Hostaway API unavailable
            httpx.TimeoutException: If token request times out
        """
        async with self._lock:
            # Check if we need to obtain or refresh token
            if self._token is None or self._token.should_refresh(
                self.config.token_refresh_threshold_days
            ):
                # Log token refresh event
                if self._token is not None:
                    logger.info(
                        json.dumps(
                            {
                                "event": "token_refresh",
                                "timestamp": datetime.now(UTC).isoformat(),
                            }
                        )
                    )
                await self._refresh_token()

            # Double-check token is valid
            if self._token is None:
                raise RuntimeError("Failed to obtain access token")

            return self._token

    async def _refresh_token(self) -> None:
        """Exchange credentials for a new access token.

        This method should only be called while holding the lock.

        Raises:
            ValueError: If credentials are invalid (401)
            PermissionError: If insufficient API permissions (403)
            RuntimeError: If rate limit exceeded (429)
            ConnectionError: If Hostaway API unavailable (5xx)
            httpx.HTTPStatusError: For other HTTP errors
        """
        request = TokenRefreshRequest(
            client_id=self.config.account_id,
            client_secret=self.config.secret_key.get_secret_value(),
        )

        try:
            response = await self._client.post(
                "/accessTokens",
                data=request.to_form_data(),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()

            token_response = TokenRefreshResponse(**response.json())
            self._token = token_response.to_access_token()

            # Log successful authentication
            logger.info(
                json.dumps(
                    {
                        "event": "auth_success",
                        "account_id": self.config.account_id,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )
            )

        except httpx.HTTPStatusError as e:
            # Log authentication failure
            log_data = {
                "event": "auth_failed",
                "reason": f"HTTP {e.response.status_code}",
                "timestamp": datetime.now(UTC).isoformat(),
            }
            logger.error(json.dumps(log_data))

            # Handle specific HTTP status codes with appropriate exceptions
            if e.response.status_code == 401:
                raise ValueError("Invalid Hostaway credentials") from e
            if e.response.status_code == 403:
                raise PermissionError("Insufficient API permissions") from e
            if e.response.status_code == 429:
                raise RuntimeError("Rate limit exceeded") from e
            if 500 <= e.response.status_code < 600:
                raise ConnectionError("Hostaway API unavailable") from e
            # Re-raise for other status codes
            raise

    async def invalidate_token(self) -> None:
        """Invalidate current token, forcing refresh on next request.

        Useful for handling authentication errors.
        """
        async with self._lock:
            self._token = None

    async def aclose(self) -> None:
        """Close the HTTP client and cleanup resources."""
        await self._client.aclose()


async def get_authenticated_client() -> "HostawayClient":
    """FastAPI dependency for getting authenticated Hostaway client.

    This dependency provides an authenticated HostawayClient instance
    for use in MCP tool handlers and API routes.

    Returns:
        Authenticated HostawayClient instance

    Raises:
        RuntimeError: If global client not initialized (app not started)

    Usage:
        @mcp.tool()
        async def get_listings(
            client: HostawayClient = Depends(get_authenticated_client)
        ) -> list[Listing]:
            return await client.get("/listings")
    """
    # Import here to avoid circular dependency
    from src.api.main import hostaway_client

    if hostaway_client is None:
        raise RuntimeError("HostawayClient not initialized. Ensure app is running.")

    return hostaway_client
