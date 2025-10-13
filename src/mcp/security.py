"""Security middleware for MCP endpoint authentication.

Provides API key authentication for MCP endpoints to prevent unauthorized access.
"""

import secrets

from fastapi import Header, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from src.mcp.config import HostawayConfig
from src.mcp.logging import get_logger

logger = get_logger(__name__)

# API Key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    """Generate a secure random API key.

    Returns:
        A 64-character hexadecimal API key
    """
    return secrets.token_hex(32)


async def verify_api_key(
    request: Request,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> None:
    """Verify API key from request header.

    Args:
        request: The incoming request
        x_api_key: API key from X-API-Key header

    Raises:
        HTTPException: If API key is missing or invalid
    """
    # Get expected API key from environment
    config = HostawayConfig()  # type: ignore[call-arg]
    expected_key = getattr(config, "mcp_api_key", None)

    # If no API key configured, allow all (development mode)
    if not expected_key:
        logger.warning(
            "MCP_API_KEY not configured - authentication disabled (INSECURE)",
            extra={"path": request.url.path},
        )
        return

    # Check if API key provided
    if not x_api_key:
        logger.warning(
            "Missing API key",
            extra={
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify API key
    if not secrets.compare_digest(x_api_key, expected_key):
        logger.warning(
            "Invalid API key",
            extra={
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
                "key_prefix": x_api_key[:8] + "..." if len(x_api_key) >= 8 else "***",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.info(
        "API key authenticated successfully",
        extra={
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
        },
    )
