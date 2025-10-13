"""FastAPI dependencies for multi-tenant organization context.

Provides dependency injection for organization-scoped requests, API key validation,
and decrypted Hostaway credentials retrieval.
"""

import hashlib
from typing import NamedTuple

from fastapi import Header, HTTPException, status

from src.services.credential_service import DecryptedCredentials
from src.services.supabase_client import get_supabase_client


class OrganizationContext(NamedTuple):
    """Organization context for authenticated MCP requests."""

    organization_id: int
    api_key_id: int
    hostaway_credentials: DecryptedCredentials


class AuthenticationError(HTTPException):
    """Raised when API key validation fails."""

    def __init__(self, detail: str = "Invalid or inactive API key") -> None:
        """Initialize authentication error with 401 status."""
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class CredentialError(HTTPException):
    """Raised when Hostaway credentials are missing or invalid."""

    def __init__(self, detail: str = "Hostaway credentials not configured or invalid") -> None:
        """Initialize credential error with 403 status."""
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


def hash_api_key(api_key: str) -> str:
    """Hash API key using SHA-256 for database lookup.

    Args:
        api_key: Raw API key from X-API-Key header

    Returns:
        64-character hexadecimal SHA-256 hash

    Example:
        >>> hash_api_key("api_abc123")
        '9f86d081884c7d659a2feaa0c55ad015...'  # 64 chars
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_organization_context(
    x_api_key: str = Header(..., description="MCP API key for organization"),
) -> OrganizationContext:
    """Validate X-API-Key header and return organization context with decrypted credentials.

    This dependency:
    1. Hashes the provided API key using SHA-256
    2. Looks up the key in api_keys table (must be active)
    3. Retrieves organization_id from api_keys record
    4. Fetches encrypted Hostaway credentials for the organization
    5. Decrypts credentials using Supabase Vault
    6. Updates last_used_at timestamp for the API key
    7. Returns OrganizationContext with org_id and decrypted credentials

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        OrganizationContext with organization ID and decrypted Hostaway credentials

    Raises:
        AuthenticationError: If API key is invalid, inactive, or not found
        CredentialError: If Hostaway credentials missing or decryption fails

    Example:
        >>> from fastapi import Depends
        >>> @app.get("/api/properties")
        >>> async def get_properties(
        ...     ctx: OrganizationContext = Depends(get_organization_context)
        ... ):
        ...     # ctx.organization_id: 123
        ...     # ctx.hostaway_credentials.account_id: "ACC_12345"
        ...     # ctx.hostaway_credentials.secret_key: "sk_live_abc..."
        ...     pass
    """
    supabase = get_supabase_client()
    key_hash = hash_api_key(x_api_key)

    # 1. Validate API key and get organization_id
    try:
        api_key_response = (
            supabase.table("api_keys")
            .select("id, organization_id, is_active")
            .eq("key_hash", key_hash)
            .eq("is_active", True)
            .single()
            .execute()
        )

        if not api_key_response.data:
            raise AuthenticationError("API key not found or inactive")

        api_key_data = api_key_response.data
        api_key_id: int = api_key_data["id"]
        organization_id: int = api_key_data["organization_id"]

    except Exception as e:
        # Log error and return generic auth failure
        raise AuthenticationError(f"API key validation failed: {e!s}") from e

    # 2. Get Hostaway credentials for organization
    try:
        creds_response = (
            supabase.table("hostaway_credentials")
            .select("account_id, encrypted_secret_key, credentials_valid")
            .eq("organization_id", organization_id)
            .single()
            .execute()
        )

        if not creds_response.data:
            raise CredentialError("Hostaway credentials not configured for organization")

        creds_data = creds_response.data

        # Check if credentials marked as invalid (e.g., 401 from Hostaway)
        if not creds_data.get("credentials_valid", True):
            raise CredentialError(
                "Hostaway credentials are invalid. Please re-authenticate in dashboard."
            )

        account_id: str = creds_data["account_id"]  # Plain text account ID
        encrypted_secret_key: str = creds_data["encrypted_secret_key"]

    except CredentialError:
        # Re-raise credential errors as-is
        raise
    except Exception as e:
        raise CredentialError(f"Failed to retrieve Hostaway credentials: {e!s}") from e

    # 3. Decrypt secret key using Vault (account_id is stored in plain text)
    try:
        # Decrypt only the secret key
        secret_response = supabase.rpc(
            "decrypt_hostaway_credential",
            {"ciphertext": encrypted_secret_key},
        ).execute()

        if not secret_response.data:
            raise CredentialError("Failed to decrypt secret key")

        secret_key: str = secret_response.data

        # Create decrypted credentials (account_id is already plain text)
        decrypted = DecryptedCredentials(
            account_id=account_id,
            secret_key=secret_key,
        )
    except Exception as e:
        raise CredentialError(f"Failed to decrypt Hostaway credentials: {e!s}") from e

    # 4. Update API key last_used_at timestamp (fire and forget)
    try:
        supabase.rpc(
            "update_api_key_last_used",
            {"key_hash": key_hash},
        ).execute()
    except Exception:
        # Non-critical - log but don't fail request
        pass

    return OrganizationContext(
        organization_id=organization_id,
        api_key_id=api_key_id,
        hostaway_credentials=decrypted,
    )
