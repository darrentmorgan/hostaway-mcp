"""Authentication models for Hostaway OAuth 2.0 integration.

This module provides Pydantic models for OAuth token management, including
AccessToken with expiration tracking and token refresh request/response models.
"""

from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field


class AccessToken(BaseModel):
    """OAuth 2.0 access token for Hostaway API authentication.

    Tokens are valid for 24 months from issuance. The model includes
    expiration tracking and automatic refresh logic.
    """

    access_token: str = Field(
        ...,
        description="Bearer token for API authentication",
        min_length=20,
    )

    token_type: str = Field(
        default="Bearer",
        description="Token type (always 'Bearer' for Hostaway)",
        pattern=r"^Bearer$",
    )

    expires_in: int = Field(
        ...,
        description="Token lifetime in seconds (typically 63072000 = 24 months)",
        ge=1,
    )

    issued_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when token was issued (UTC)",
    )

    scope: str = Field(
        default="general",
        description="OAuth scope (Hostaway uses 'general')",
    )

    @property
    def expires_at(self) -> datetime:
        """Calculate token expiration timestamp."""
        return self.issued_at + timedelta(seconds=self.expires_in)

    @property
    def is_expired(self) -> bool:
        """Check if token is currently expired."""
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def days_until_expiration(self) -> int:
        """Calculate days remaining until token expires."""
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)

    def should_refresh(self, threshold_days: int = 7) -> bool:
        """Determine if token should be refreshed.

        Args:
            threshold_days: Refresh if expiring within this many days

        Returns:
            True if token should be refreshed
        """
        return self.days_until_expiration <= threshold_days

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 63072000,
                "issued_at": "2025-10-12T10:30:00Z",
                "scope": "general",
            }
        }
    }


class TokenRefreshRequest(BaseModel):
    """OAuth 2.0 token request using Client Credentials Grant.

    Sent as application/x-www-form-urlencoded to POST /v1/accessTokens
    """

    grant_type: str = Field(
        default="client_credentials",
        description="OAuth grant type (always 'client_credentials')",
        pattern=r"^client_credentials$",
    )

    client_id: str = Field(
        ...,
        description="Hostaway account ID",
        min_length=1,
    )

    client_secret: str = Field(
        ...,
        description="Hostaway secret key",
        min_length=1,
    )

    scope: str = Field(
        default="general",
        description="OAuth scope (Hostaway uses 'general')",
    )

    def to_form_data(self) -> dict[str, str]:
        """Convert to form-encoded data for HTTP request."""
        return {
            "grant_type": self.grant_type,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
        }

    model_config = {
        "json_schema_extra": {
            "example": {
                "grant_type": "client_credentials",
                "client_id": "12345",
                "client_secret": "secret_abc123xyz",
                "scope": "general",
            }
        }
    }


class TokenRefreshResponse(BaseModel):
    """OAuth token response from Hostaway API.

    Returned from POST /v1/accessTokens
    """

    access_token: str = Field(
        ...,
        description="JWT access token",
        min_length=20,
    )

    token_type: str = Field(
        ...,
        description="Token type (always 'Bearer')",
    )

    expires_in: int = Field(
        ...,
        description="Token lifetime in seconds",
        ge=1,
    )

    scope: str = Field(
        default="general",
        description="OAuth scope",
    )

    def to_access_token(self) -> AccessToken:
        """Convert to AccessToken model."""
        return AccessToken(
            access_token=self.access_token,
            token_type=self.token_type,
            expires_in=self.expires_in,
            scope=self.scope,
        )

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 63072000,
                "scope": "general",
            }
        }
    }
