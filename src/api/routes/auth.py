"""Authentication routes for MCP tools.

Provides manual authentication and token refresh endpoints for testing/debugging.
These endpoints are automatically exposed as MCP tools via FastAPI-MCP.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, SecretStr

from src.mcp.auth import TokenManager, get_authenticated_client
from src.mcp.config import HostawayConfig
from src.services.hostaway_client import HostawayClient

router = APIRouter()


class AuthenticateRequest(BaseModel):
    """Request model for manual authentication."""

    account_id: str = Field(..., description="Hostaway account identifier")
    secret_key: str = Field(..., description="Hostaway API secret key")


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""

    access_token: str = Field(..., description="OAuth 2.0 access token")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    token_type: str = Field(default="Bearer", description="Token type")


@router.post(
    "/authenticate",
    response_model=TokenResponse,
    summary="Manually authenticate with Hostaway API",
    description="Authenticate with Hostaway using account credentials for testing/debugging",
    tags=["Authentication"],
)
async def authenticate_hostaway(request: AuthenticateRequest) -> TokenResponse:
    """
    Manually authenticate with Hostaway API for testing/debugging.

    This tool creates a temporary authentication session with the provided
    credentials and returns a valid access token. Useful for:
    - Testing API connectivity
    - Debugging authentication issues
    - Manual token generation

    Args:
        request: Authentication request with account_id and secret_key

    Returns:
        TokenResponse with access_token, expires_in, and token_type

    Raises:
        ValueError: If credentials are invalid (401)
        PermissionError: If insufficient API permissions (403)
        RuntimeError: If rate limit exceeded (429)
        ConnectionError: If Hostaway API unavailable (5xx)
    """
    # Create temporary config with provided credentials
    # Use env var aliases for constructor parameters
    config = HostawayConfig(
        HOSTAWAY_ACCOUNT_ID=request.account_id, HOSTAWAY_SECRET_KEY=SecretStr(request.secret_key)
    )

    # Create temporary token manager
    token_manager = TokenManager(config=config)

    try:
        # Get token (will authenticate if needed)
        token = await token_manager.get_token()

        return TokenResponse(
            access_token=token.access_token, expires_in=token.expires_in, token_type="Bearer"
        )
    finally:
        # Clean up resources
        await token_manager.aclose()


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Manually refresh the Hostaway access token",
    description="Force refresh of the current access token",
    tags=["Authentication"],
)
async def refresh_token(
    client: HostawayClient = Depends(get_authenticated_client),
) -> TokenResponse:
    """
    Manually refresh the Hostaway access token.

    This tool invalidates the current token and forces a refresh,
    obtaining a new access token from the Hostaway API. Useful for:
    - Testing token refresh logic
    - Recovering from authentication errors
    - Manual token rotation

    Args:
        client: Authenticated Hostaway client (injected)

    Returns:
        TokenResponse with new access_token, expires_in, and token_type

    Raises:
        ValueError: If credentials are invalid (401)
        PermissionError: If insufficient API permissions (403)
        RuntimeError: If rate limit exceeded (429) or refresh fails
        ConnectionError: If Hostaway API unavailable (5xx)
    """
    # Invalidate current token to force refresh
    await client.token_manager.invalidate_token()

    # Get new token (will trigger refresh)
    token = await client.token_manager.get_token()

    return TokenResponse(
        access_token=token.access_token, expires_in=token.expires_in, token_type="Bearer"
    )
