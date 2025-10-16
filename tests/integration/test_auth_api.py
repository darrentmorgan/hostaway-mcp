"""Integration tests for Hostaway authentication API.

Tests OAuth 2.0 token exchange, authentication flow, and automatic token refresh.
Following TDD: These tests should FAIL until implementation is complete.
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.mcp.auth import TokenManager
from src.mcp.config import HostawayConfig
from src.models.auth import AccessToken


@pytest.fixture
def test_config(monkeypatch: pytest.MonkeyPatch) -> HostawayConfig:
    """Create test configuration."""
    # Set environment variables for pydantic-settings
    monkeypatch.setenv("HOSTAWAY_ACCOUNT_ID", "test_account_123")
    monkeypatch.setenv("HOSTAWAY_SECRET_KEY", "test_secret_key_456")
    monkeypatch.setenv("HOSTAWAY_API_BASE_URL", "https://api.hostaway.com/v1")
    monkeypatch.setenv("HOSTAWAY_RATE_LIMIT_IP", "15")
    monkeypatch.setenv("HOSTAWAY_RATE_LIMIT_ACCOUNT", "20")
    monkeypatch.setenv("HOSTAWAY_MAX_CONCURRENT_REQUESTS", "5")
    monkeypatch.setenv("HOSTAWAY_TOKEN_REFRESH_THRESHOLD_DAYS", "7")

    return HostawayConfig()  # type: ignore[call-arg]


@pytest.fixture
def mock_token_response() -> dict[str, str | int]:
    """Create mock Hostaway token response."""
    return {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.mock_token_data",
        "token_type": "Bearer",
        "expires_in": 63072000,  # 24 months in seconds
        "scope": "general",
    }


@pytest.fixture
def client() -> TestClient:
    """Create test client for FastAPI app."""
    return TestClient(app)


# T030: Contract test for OAuth token endpoint
class TestOAuthTokenEndpoint:
    """Test OAuth 2.0 /accessTokens endpoint contract."""

    @pytest.mark.asyncio
    async def test_token_exchange_success(
        self, test_config: HostawayConfig, mock_token_response: dict[str, str | int]
    ) -> None:
        """Test successful token exchange with client_credentials grant.

        Verifies:
        - POST /accessTokens accepts form-encoded credentials
        - Returns access_token, expires_in, token_type
        - Token type is 'Bearer'
        - expires_in is positive integer
        """
        # Mock httpx client response
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()  # Use MagicMock for sync methods like json()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_token_response
        mock_response.raise_for_status = MagicMock()  # raise_for_status is also sync
        mock_client.post = AsyncMock(return_value=mock_response)

        # Create TokenManager with mock client
        token_manager = TokenManager(config=test_config, client=mock_client)

        # Exchange credentials for token
        token = await token_manager.get_token()

        # Verify token structure
        assert isinstance(token, AccessToken)
        assert token.access_token == mock_token_response["access_token"]
        assert token.token_type == "Bearer"
        assert token.expires_in == mock_token_response["expires_in"]
        assert token.scope == "general"

        # Verify request was made correctly
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/accessTokens"
        assert call_args[1]["headers"]["Content-Type"] == "application/x-www-form-urlencoded"

    @pytest.mark.asyncio
    async def test_token_exchange_invalid_credentials(self, test_config: HostawayConfig) -> None:
        """Test token exchange with invalid credentials returns 401.

        Verifies:
        - Invalid client_id/client_secret raises HTTPStatusError
        - Error status code is 401
        - Error response contains 'invalid_client'
        """
        # Mock httpx client with 401 error
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()  # Use MagicMock for sync methods
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": "invalid_client",
            "error_description": "Client authentication failed",
            "status": 401,
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=mock_response,
        )
        mock_client.post = AsyncMock(return_value=mock_response)

        token_manager = TokenManager(config=test_config, client=mock_client)

        # Attempt token exchange should raise ValueError (transformed from 401)
        with pytest.raises(ValueError, match="Invalid Hostaway credentials"):
            await token_manager.get_token()

    @pytest.mark.asyncio
    async def test_token_exchange_missing_parameters(self, test_config: HostawayConfig) -> None:
        """Test token exchange with missing required parameters returns 400.

        Verifies:
        - Missing client_id or client_secret returns 400
        - Error response indicates missing parameter
        """
        # Mock httpx client with 400 error
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()  # Use MagicMock for sync methods like json()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": "invalid_request",
            "error_description": "Missing required parameter: client_id",
            "status": 400,
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request",
            request=MagicMock(),
            response=mock_response,
        )
        mock_client.post = AsyncMock(return_value=mock_response)

        token_manager = TokenManager(config=test_config, client=mock_client)

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await token_manager.get_token()

        assert exc_info.value.response.status_code == 400


# T031: Integration test for authentication flow
class TestAuthenticationFlow:
    """Test complete authentication flow with valid/invalid credentials."""

    @pytest.mark.asyncio
    async def test_authentication_flow_valid_credentials(
        self, test_config: HostawayConfig, mock_token_response: dict[str, str | int]
    ) -> None:
        """Test complete authentication flow with valid credentials.

        Flow:
        1. Provide valid account_id and secret_key
        2. TokenManager exchanges credentials for token
        3. Token is stored and accessible
        4. Subsequent requests use cached token
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()  # Use MagicMock for sync methods like json()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_token_response
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        token_manager = TokenManager(config=test_config, client=mock_client)

        # First token request
        token1 = await token_manager.get_token()
        assert token1.access_token == mock_token_response["access_token"]

        # Second request should use cached token (no additional API call)
        token2 = await token_manager.get_token()
        assert token2.access_token == token1.access_token

        # Verify only one API call was made
        assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_authentication_flow_invalid_credentials(
        self, test_config: HostawayConfig
    ) -> None:
        """Test authentication flow with invalid credentials.

        Verifies:
        - Invalid credentials result in HTTPStatusError
        - Error is 401 Unauthorized
        - Token is not stored
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()  # Use MagicMock for sync methods like json()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": "invalid_client",
            "error_description": "Client authentication failed",
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=mock_response,
        )
        mock_client.post = AsyncMock(return_value=mock_response)

        token_manager = TokenManager(config=test_config, client=mock_client)

        # Authentication should fail with ValueError (transformed from 401)
        with pytest.raises(ValueError, match="Invalid Hostaway credentials"):
            await token_manager.get_token()

        # Token should not be stored
        assert token_manager._token is None

    @pytest.mark.asyncio
    async def test_authentication_flow_rate_limit_exceeded(
        self, test_config: HostawayConfig
    ) -> None:
        """Test authentication flow when rate limit is exceeded.

        Verifies:
        - Rate limit error (429) is raised
        - Error response includes retry_after
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()  # Use MagicMock for sync methods like json()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": "rate_limit_exceeded",
            "error_description": "Too many requests",
            "status": 429,
            "retry_after": 10,
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429 Too Many Requests",
            request=MagicMock(),
            response=mock_response,
        )
        mock_client.post = AsyncMock(return_value=mock_response)

        token_manager = TokenManager(config=test_config, client=mock_client)

        # Rate limit error is transformed to RuntimeError
        with pytest.raises(RuntimeError, match="Rate limit exceeded"):
            await token_manager.get_token()


# T032: Integration test for token refresh flow
class TestTokenRefreshFlow:
    """Test automatic token refresh when token is near expiration."""

    @pytest.mark.asyncio
    async def test_token_auto_refresh_when_expiring_soon(
        self, test_config: HostawayConfig, mock_token_response: dict[str, str | int]
    ) -> None:
        """Test automatic token refresh when expiring within threshold.

        Verifies:
        - Token is refreshed when days_until_expiration <= 7
        - New token replaces old token
        - Refresh is triggered automatically by get_token()
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        # First response: token expiring in 5 days
        expiring_token_response = mock_token_response.copy()
        expiring_token_response["expires_in"] = 5 * 24 * 60 * 60  # 5 days in seconds

        # Second response: fresh token with 24 months
        fresh_token_response = mock_token_response.copy()
        fresh_token_response["access_token"] = "fresh_token_xyz_20_chars_minimum"

        mock_response1 = MagicMock()  # Use MagicMock for sync methods like json()
        mock_response1.status_code = 200
        mock_response1.json.return_value = expiring_token_response
        mock_response1.raise_for_status = MagicMock()

        mock_response2 = MagicMock()  # Use MagicMock for sync methods like json()
        mock_response2.status_code = 200
        mock_response2.json.return_value = fresh_token_response
        mock_response2.raise_for_status = MagicMock()

        mock_client.post = AsyncMock(side_effect=[mock_response1, mock_response2])

        token_manager = TokenManager(config=test_config, client=mock_client)

        # First call: get expiring token
        token1 = await token_manager.get_token()
        assert token1.days_until_expiration <= 7

        # Second call: should auto-refresh
        token2 = await token_manager.get_token()
        assert token2.access_token == "fresh_token_xyz_20_chars_minimum"
        assert token2.access_token != token1.access_token

        # Verify two API calls were made
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_token_refresh_manual_invalidation(
        self, test_config: HostawayConfig, mock_token_response: dict[str, str | int]
    ) -> None:
        """Test manual token invalidation triggers refresh.

        Verifies:
        - invalidate_token() clears cached token
        - Next get_token() call fetches new token
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        # Two different tokens (must be 20+ chars for validation)
        token_response1 = mock_token_response.copy()
        token_response1["access_token"] = "token_1_with_20_chars_min"

        token_response2 = mock_token_response.copy()
        token_response2["access_token"] = "token_2_with_20_chars_min"

        mock_response1 = MagicMock()  # Use MagicMock for sync methods like json()
        mock_response1.status_code = 200
        mock_response1.json.return_value = token_response1
        mock_response1.raise_for_status = MagicMock()

        mock_response2 = MagicMock()  # Use MagicMock for sync methods like json()
        mock_response2.status_code = 200
        mock_response2.json.return_value = token_response2
        mock_response2.raise_for_status = MagicMock()

        mock_client.post = AsyncMock(side_effect=[mock_response1, mock_response2])

        token_manager = TokenManager(config=test_config, client=mock_client)

        # Get first token
        token1 = await token_manager.get_token()
        assert token1.access_token == "token_1_with_20_chars_min"

        # Invalidate token
        await token_manager.invalidate_token()

        # Get token again - should fetch new token
        token2 = await token_manager.get_token()
        assert token2.access_token == "token_2_with_20_chars_min"

        # Verify two API calls
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_token_no_refresh_when_valid(
        self, test_config: HostawayConfig, mock_token_response: dict[str, str | int]
    ) -> None:
        """Test token is NOT refreshed when still valid.

        Verifies:
        - Token with >7 days until expiration is not refreshed
        - Cached token is reused
        """
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()  # Use MagicMock for sync methods like json()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_token_response
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        token_manager = TokenManager(config=test_config, client=mock_client)

        # Get token
        token1 = await token_manager.get_token()

        # Get token again (should use cache)
        token2 = await token_manager.get_token()

        # Tokens should be identical (cached)
        assert token1.access_token == token2.access_token
        assert token1.issued_at == token2.issued_at

        # Only one API call should have been made
        assert mock_client.post.call_count == 1
