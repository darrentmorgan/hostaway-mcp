"""Hostaway API configuration loaded from environment variables.

This module provides the HostawayConfig model for loading OAuth credentials
and API settings from environment variables using pydantic-settings.
"""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class HostawayConfig(BaseSettings):
    """Hostaway API configuration loaded from environment variables.

    Required environment variables:
    - HOSTAWAY_ACCOUNT_ID: OAuth client ID
    - HOSTAWAY_SECRET_KEY: OAuth client secret
    - HOSTAWAY_API_BASE_URL: Base API URL (default: https://api.hostaway.com/v1)

    Optional environment variables for rate limiting and concurrency:
    - RATE_LIMIT_IP: IP-based rate limit (default: 15 req/10s)
    - RATE_LIMIT_ACCOUNT: Account-based rate limit (default: 20 req/10s)
    - MAX_CONCURRENT_REQUESTS: Max concurrent requests (default: 10)
    - TOKEN_REFRESH_THRESHOLD_DAYS: Days before expiration to refresh token (default: 7)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    account_id: str = Field(
        ...,
        description="Hostaway account ID (OAuth client ID)",
        min_length=1,
        alias="HOSTAWAY_ACCOUNT_ID",
    )

    secret_key: SecretStr = Field(
        ...,
        description="Hostaway secret key (OAuth client secret)",
        alias="HOSTAWAY_SECRET_KEY",
    )

    api_base_url: str = Field(
        default="https://api.hostaway.com/v1",
        description="Hostaway API base URL",
        alias="HOSTAWAY_API_BASE_URL",
    )

    rate_limit_ip: int = Field(
        default=15,
        description="IP-based rate limit (requests per 10 seconds)",
        ge=1,
        le=15,
        alias="RATE_LIMIT_IP",
    )

    rate_limit_account: int = Field(
        default=20,
        description="Account-based rate limit (requests per 10 seconds)",
        ge=1,
        le=20,
        alias="RATE_LIMIT_ACCOUNT",
    )

    max_concurrent_requests: int = Field(
        default=10,
        description="Maximum concurrent requests",
        ge=1,
        le=50,
        alias="MAX_CONCURRENT_REQUESTS",
    )

    token_refresh_threshold_days: int = Field(
        default=7,
        description="Days before expiration to refresh token",
        ge=1,
        le=30,
        alias="TOKEN_REFRESH_THRESHOLD_DAYS",
    )
