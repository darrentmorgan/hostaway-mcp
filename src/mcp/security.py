"""Security middleware for MCP endpoint authentication.

Provides API key authentication for MCP endpoints to prevent unauthorized access.
Uses Supabase database for multi-tenant API key validation.
"""

import hashlib
import os
import secrets

from fastapi import Header, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from src.mcp.logging import get_logger
from supabase import Client, create_client

logger = get_logger(__name__)

# API Key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    """Generate a secure random API key with mcp_ prefix.

    Returns:
        A secure API key starting with mcp_
    """
    return f"mcp_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage.

    Args:
        api_key: The plaintext API key

    Returns:
        SHA-256 hash of the API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_supabase_client() -> Client:
    """Get Supabase client for database access.

    Returns:
        Supabase client instance

    Raises:
        ValueError: If Supabase credentials are not configured
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be configured")

    return create_client(supabase_url, supabase_key)


async def verify_api_key(
    request: Request,
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> dict:
    """Verify API key from request header against Supabase database.

    Args:
        request: The incoming request
        x_api_key: API key from X-API-Key header

    Returns:
        Dictionary containing organization_id and api_key_id

    Raises:
        HTTPException: If API key is missing or invalid
    """
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

    try:
        # Hash the provided API key
        key_hash = hash_api_key(x_api_key)

        # Query Supabase for the API key
        supabase = get_supabase_client()
        response = (
            supabase.table("api_keys")
            .select("*")
            .eq("key_hash", key_hash)
            .eq("is_active", True)
            .single()
            .execute()
        )

        if not response.data:
            logger.warning(
                "Invalid or inactive API key",
                extra={
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else "unknown",
                    "key_prefix": x_api_key[:8] + "..." if len(x_api_key) >= 8 else "***",
                },
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        api_key_data = response.data
        organization_id = api_key_data["organization_id"]
        api_key_id = api_key_data["id"]

        # Update last_used_at timestamp
        supabase.table("api_keys").update({"last_used_at": "now()"}).eq("id", api_key_id).execute()

        logger.info(
            "API key authenticated successfully",
            extra={
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
                "organization_id": organization_id,
                "api_key_id": api_key_id,
            },
        )

        # Store authentication context in request state
        request.state.organization_id = organization_id
        request.state.api_key_id = api_key_id

        return {
            "organization_id": organization_id,
            "api_key_id": api_key_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "API key verification failed",
            extra={
                "error": str(e),
                "path": request.url.path,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "ApiKey"},
        )
