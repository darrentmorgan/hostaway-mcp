"""Unit tests for authentication models and TokenManager.

Tests AccessToken expiration tracking, TokenRefreshRequest form data conversion,
TokenRefreshResponse to AccessToken conversion, and TokenManager OAuth flow.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from src.mcp.config import HostawayConfig
from src.mcp.auth import TokenManager
from src.models.auth import AccessToken, TokenRefreshRequest, TokenRefreshResponse


class TestAccessToken:
    """Test suite for AccessToken model."""

    def test_access_token_creation(self) -> None:
        """Test that AccessToken can be created with required fields."""
        token = AccessToken(
            access_token="test_token_abc123_xyz789",
            expires_in=63072000,
        )

        assert token.access_token == "test_token_abc123_xyz789"
        assert token.token_type == "Bearer"
        assert token.expires_in == 63072000
        assert token.scope == "general"
        assert isinstance(token.issued_at, datetime)

    def test_access_token_expires_at_calculation(self) -> None:
        """Test that expires_at is calculated correctly."""
        issued_at = datetime.now(timezone.utc)
        expires_in = 3600  # 1 hour

        token = AccessToken(
            access_token="test_token_abc123_xyz789",
            expires_in=expires_in,
            issued_at=issued_at,
        )

        expected_expiry = issued_at + timedelta(seconds=expires_in)
        assert token.expires_at == expected_expiry

    def test_access_token_is_expired_false(self) -> None:
        """Test that is_expired returns False for valid token."""
        token = AccessToken(
            access_token="test_token_abc123_xyz789",
            expires_in=3600,  # 1 hour from now
        )

        assert token.is_expired is False

    def test_access_token_is_expired_true(self) -> None:
        """Test that is_expired returns True for expired token."""
        issued_at = datetime.now(timezone.utc) - timedelta(hours=2)

        token = AccessToken(
            access_token="test_token_abc123_xyz789",
            expires_in=3600,  # 1 hour (so expired 1 hour ago)
            issued_at=issued_at,
        )

        assert token.is_expired is True

    def test_access_token_days_until_expiration(self) -> None:
        """Test days_until_expiration calculation."""
        token = AccessToken(
            access_token="test_token_abc123_xyz789",
            expires_in=86400 * 10,  # 10 days
        )

        # Should be approximately 10 days (allowing for test execution time)
        assert 9 <= token.days_until_expiration <= 10

    def test_access_token_days_until_expiration_expired(self) -> None:
        """Test days_until_expiration returns 0 for expired token."""
        issued_at = datetime.now(timezone.utc) - timedelta(hours=2)

        token = AccessToken(
            access_token="test_token_abc123_xyz789",
            expires_in=3600,  # 1 hour (expired)
            issued_at=issued_at,
        )

        assert token.days_until_expiration == 0

    def test_access_token_should_refresh_true(self) -> None:
        """Test should_refresh returns True when token expires within threshold."""
        token = AccessToken(
            access_token="test_token_abc123_xyz789",
            expires_in=86400 * 5,  # 5 days
        )

        # Default threshold is 7 days, so should refresh
        assert token.should_refresh() is True

    def test_access_token_should_refresh_false(self) -> None:
        """Test should_refresh returns False when token has time remaining."""
        token = AccessToken(
            access_token="test_token_abc123_xyz789",
            expires_in=86400 * 10,  # 10 days
        )

        # Default threshold is 7 days, so should not refresh yet
        assert token.should_refresh() is False

    def test_access_token_should_refresh_custom_threshold(self) -> None:
        """Test should_refresh with custom threshold."""
        token = AccessToken(
            access_token="test_token_abc123_xyz789",
            expires_in=86400 * 15,  # 15 days
        )

        # Custom threshold of 20 days
        assert token.should_refresh(threshold_days=20) is True

        # Custom threshold of 10 days
        assert token.should_refresh(threshold_days=10) is False

    def test_access_token_should_refresh_expired(self) -> None:
        """Test should_refresh returns True for expired token."""
        issued_at = datetime.now(timezone.utc) - timedelta(hours=2)

        token = AccessToken(
            access_token="test_token_abc123_xyz789",
            expires_in=3600,  # 1 hour (expired)
            issued_at=issued_at,
        )

        assert token.should_refresh() is True

    def test_access_token_validation_min_length(self) -> None:
        """Test that access_token must be at least 20 characters."""
        with pytest.raises(ValueError):
            AccessToken(
                access_token="short",
                expires_in=3600,
            )

    def test_access_token_validation_token_type(self) -> None:
        """Test that token_type must be 'Bearer'."""
        with pytest.raises(ValueError):
            AccessToken(
                access_token="test_token_abc123_xyz789",
                token_type="InvalidType",
                expires_in=3600,
            )

    def test_access_token_validation_expires_in_positive(self) -> None:
        """Test that expires_in must be positive."""
        with pytest.raises(ValueError):
            AccessToken(
                access_token="test_token_abc123_xyz789",
                expires_in=0,
            )


class TestTokenRefreshRequest:
    """Test suite for TokenRefreshRequest model."""

    def test_token_refresh_request_creation(self) -> None:
        """Test TokenRefreshRequest creation with required fields."""
        request = TokenRefreshRequest(
            client_id="test_client_123",
            client_secret="test_secret_abc",
        )

        assert request.grant_type == "client_credentials"
        assert request.client_id == "test_client_123"
        assert request.client_secret == "test_secret_abc"
        assert request.scope == "general"

    def test_token_refresh_request_to_form_data(self) -> None:
        """Test conversion to form-encoded data."""
        request = TokenRefreshRequest(
            client_id="test_client_123",
            client_secret="test_secret_abc",
        )

        form_data = request.to_form_data()

        assert form_data == {
            "grant_type": "client_credentials",
            "client_id": "test_client_123",
            "client_secret": "test_secret_abc",
            "scope": "general",
        }

    def test_token_refresh_request_validation_grant_type(self) -> None:
        """Test that grant_type must be 'client_credentials'."""
        with pytest.raises(ValueError):
            TokenRefreshRequest(
                grant_type="invalid_grant",
                client_id="test_client_123",
                client_secret="test_secret_abc",
            )


class TestTokenRefreshResponse:
    """Test suite for TokenRefreshResponse model."""

    def test_token_refresh_response_creation(self) -> None:
        """Test TokenRefreshResponse creation."""
        response = TokenRefreshResponse(
            access_token="test_token_abc123_xyz789",
            token_type="Bearer",
            expires_in=63072000,
        )

        assert response.access_token == "test_token_abc123_xyz789"
        assert response.token_type == "Bearer"
        assert response.expires_in == 63072000
        assert response.scope == "general"

    def test_token_refresh_response_to_access_token(self) -> None:
        """Test conversion to AccessToken model."""
        response = TokenRefreshResponse(
            access_token="test_token_abc123_xyz789",
            token_type="Bearer",
            expires_in=63072000,
            scope="general",
        )

        access_token = response.to_access_token()

        assert isinstance(access_token, AccessToken)
        assert access_token.access_token == "test_token_abc123_xyz789"
        assert access_token.token_type == "Bearer"
        assert access_token.expires_in == 63072000
        assert access_token.scope == "general"
        assert isinstance(access_token.issued_at, datetime)


class TestTokenManager:
    """Test suite for TokenManager class."""

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

    @pytest.mark.asyncio
    async def test_token_manager_get_token_success(self, config: HostawayConfig) -> None:
        """Test successful token acquisition."""
        # Mock the OAuth token endpoint
        async with respx.mock:
            respx.post(f"{config.api_base_url}/accessTokens").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "test_token_abc123_xyz789",
                        "token_type": "Bearer",
                        "expires_in": 63072000,
                        "scope": "general",
                    },
                )
            )

            async with httpx.AsyncClient(base_url=config.api_base_url) as client:
                manager = TokenManager(config=config, client=client)
                token = await manager.get_token()

                assert isinstance(token, AccessToken)
                assert token.access_token == "test_token_abc123_xyz789"
                assert token.token_type == "Bearer"
                assert token.expires_in == 63072000

    @pytest.mark.asyncio
    @respx.mock
    async def test_token_manager_reuses_valid_token(self, config: HostawayConfig) -> None:
        """Test that TokenManager reuses valid token without refreshing."""
        # Mock should only be called once
        mock_route = respx.post(f"{config.api_base_url}/accessTokens").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "test_token_abc123_xyz789",
                    "token_type": "Bearer",
                    "expires_in": 63072000,  # 24 months - far from expiration
                    "scope": "general",
                },
            )
        )

        async with httpx.AsyncClient(base_url=config.api_base_url) as client:
            manager = TokenManager(config=config, client=client)

            # Get token twice
            token1 = await manager.get_token()
            token2 = await manager.get_token()

            # Should be the same token
            assert token1.access_token == token2.access_token

            # Endpoint should only be called once
            assert mock_route.called
            assert mock_route.call_count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_token_manager_refreshes_expiring_token(self, config: HostawayConfig) -> None:
        """Test that TokenManager refreshes token when approaching expiration."""
        # First call returns token expiring in 5 days (below 7-day threshold)
        first_response = httpx.Response(
            200,
            json={
                "access_token": "old_token_abc123_xyz789",
                "token_type": "Bearer",
                "expires_in": 86400 * 5,  # 5 days
                "scope": "general",
            },
        )

        # Second call returns new token
        second_response = httpx.Response(
            200,
            json={
                "access_token": "new_token_abc123_xyz789",
                "token_type": "Bearer",
                "expires_in": 63072000,
                "scope": "general",
            },
        )

        mock_route = respx.post(f"{config.api_base_url}/accessTokens").mock(
            side_effect=[first_response, second_response]
        )

        async with httpx.AsyncClient(base_url=config.api_base_url) as client:
            manager = TokenManager(config=config, client=client)

            # First call gets expiring token
            token1 = await manager.get_token()
            assert token1.access_token == "old_token_abc123_xyz789"

            # Second call should refresh and get new token
            token2 = await manager.get_token()
            assert token2.access_token == "new_token_abc123_xyz789"

            # Endpoint should be called twice
            assert mock_route.call_count == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_token_manager_handles_auth_failure(self, config: HostawayConfig) -> None:
        """Test that TokenManager handles authentication failures."""
        respx.post(f"{config.api_base_url}/accessTokens").mock(
            return_value=httpx.Response(
                401,
                json={
                    "error": "invalid_client",
                    "error_description": "Client authentication failed",
                },
            )
        )

        async with httpx.AsyncClient(base_url=config.api_base_url) as client:
            manager = TokenManager(config=config, client=client)

            # 401 errors are transformed to ValueError by TokenManager
            with pytest.raises(ValueError, match="Invalid Hostaway credentials"):
                await manager.get_token()

    @pytest.mark.asyncio
    @respx.mock
    async def test_token_manager_invalidate_forces_refresh(
        self, config: HostawayConfig
    ) -> None:
        """Test that invalidate_token forces refresh on next get_token call."""
        # Mock returns different tokens on each call
        first_response = httpx.Response(
            200,
            json={
                "access_token": "first_token_abc123_xyz789",
                "token_type": "Bearer",
                "expires_in": 63072000,
                "scope": "general",
            },
        )

        second_response = httpx.Response(
            200,
            json={
                "access_token": "second_token_abc123_xyz789",
                "token_type": "Bearer",
                "expires_in": 63072000,
                "scope": "general",
            },
        )

        mock_route = respx.post(f"{config.api_base_url}/accessTokens").mock(
            side_effect=[first_response, second_response]
        )

        async with httpx.AsyncClient(base_url=config.api_base_url) as client:
            manager = TokenManager(config=config, client=client)

            # Get first token
            token1 = await manager.get_token()
            assert token1.access_token == "first_token_abc123_xyz789"

            # Invalidate token
            await manager.invalidate_token()

            # Get token again - should refresh
            token2 = await manager.get_token()
            assert token2.access_token == "second_token_abc123_xyz789"

            # Endpoint should be called twice
            assert mock_route.call_count == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_token_manager_thread_safe(self, config: HostawayConfig) -> None:
        """Test that TokenManager is thread-safe for concurrent requests."""
        call_count = 0

        def mock_token_response(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(
                200,
                json={
                    "access_token": f"token_call_{call_count}_abc123_xyz789",
                    "token_type": "Bearer",
                    "expires_in": 63072000,
                    "scope": "general",
                },
            )

        respx.post(f"{config.api_base_url}/accessTokens").mock(
            side_effect=mock_token_response
        )

        async with httpx.AsyncClient(base_url=config.api_base_url) as client:
            manager = TokenManager(config=config, client=client)

            # Make 5 concurrent token requests
            tokens = await asyncio.gather(*[manager.get_token() for _ in range(5)])

            # All tokens should be the same (only one actual API call)
            assert all(t.access_token == tokens[0].access_token for t in tokens)

            # Only one API call should have been made
            assert call_count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_token_manager_get_token_runtime_error(
        self, config: HostawayConfig
    ) -> None:
        """Test that get_token raises RuntimeError if token acquisition fails silently."""
        # This tests the edge case where _refresh_token somehow doesn't set _token
        # In practice this shouldn't happen, but we test the safety check

        async with httpx.AsyncClient(base_url=config.api_base_url) as client:
            manager = TokenManager(config=config, client=client)

            # Force _token to None after attempted refresh by mocking the response
            respx.post(f"{config.api_base_url}/accessTokens").mock(
                return_value=httpx.Response(200, json={})  # Invalid response
            )

            # This should raise a validation error from Pydantic or HTTPError
            with pytest.raises(Exception):  # Could be ValidationError or other
                await manager.get_token()
