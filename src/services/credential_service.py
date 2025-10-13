"""Credential encryption/decryption service using Supabase Vault.

Provides secure encryption and decryption of Hostaway API credentials
using pgsodium Vault with hardware-backed encryption keys.
"""

from typing import NamedTuple

from src.services.supabase_client import SupabaseClientError, get_supabase_client
from supabase import Client


class EncryptedCredentials(NamedTuple):
    """Encrypted Hostaway API credentials."""

    encrypted_account_id: str
    encrypted_secret_key: str


class DecryptedCredentials(NamedTuple):
    """Decrypted Hostaway API credentials."""

    account_id: str
    secret_key: str


class CredentialServiceError(Exception):
    """Base exception for credential service errors."""


class EncryptionError(CredentialServiceError):
    """Raised when credential encryption fails."""


class DecryptionError(CredentialServiceError):
    """Raised when credential decryption fails."""


class CredentialService:
    """Service for encrypting and decrypting Hostaway credentials using Supabase Vault.

    Uses pgsodium extension with hardware-backed encryption keys stored in
    vault.secrets. Encryption is performed server-side using PostgreSQL functions.

    The encryption pattern:
    1. Vault key stored in vault.secrets (created via Supabase Dashboard)
    2. encrypt_hostaway_credential() RPC function encrypts plaintext
    3. decrypt_hostaway_credential() RPC function decrypts ciphertext
    4. All encryption happens in database - credentials never in plaintext on backend
    """

    def __init__(self, supabase: Client | None = None) -> None:
        """Initialize credential service.

        Args:
            supabase: Optional Supabase client (creates singleton if None)
        """
        self.supabase = supabase or get_supabase_client()

    async def encrypt_credentials(
        self,
        account_id: str,
        secret_key: str,
    ) -> EncryptedCredentials:
        """Encrypt Hostaway API credentials using Supabase Vault.

        Calls the encrypt_hostaway_credential RPC function created in migration
        20251013_003_vault_setup.sql. Encryption uses pgsodium with nonce
        generation and base64 encoding.

        Args:
            account_id: Hostaway account ID (plaintext)
            secret_key: Hostaway secret key (plaintext)

        Returns:
            EncryptedCredentials with base64-encoded ciphertext

        Raises:
            EncryptionError: If encryption fails

        Example:
            >>> service = CredentialService()
            >>> encrypted = await service.encrypt_credentials(
            ...     account_id="ACC_12345",
            ...     secret_key="sk_live_abc123..."
            ... )
            >>> print(encrypted.encrypted_account_id)  # Base64 ciphertext
        """
        try:
            # Encrypt account ID
            account_response = self.supabase.rpc(
                "encrypt_hostaway_credential",
                {"plaintext": account_id},
            ).execute()

            if not account_response.data:
                raise EncryptionError("Failed to encrypt account_id: No data returned")

            encrypted_account_id: str = account_response.data

            # Encrypt secret key
            secret_response = self.supabase.rpc(
                "encrypt_hostaway_credential",
                {"plaintext": secret_key},
            ).execute()

            if not secret_response.data:
                raise EncryptionError("Failed to encrypt secret_key: No data returned")

            encrypted_secret_key: str = secret_response.data

            return EncryptedCredentials(
                encrypted_account_id=encrypted_account_id,
                encrypted_secret_key=encrypted_secret_key,
            )

        except SupabaseClientError as e:
            raise EncryptionError(
                f"Vault encryption failed: {e!s}. "
                "Ensure encryption key exists in vault.secrets with name 'hostaway_encryption_key'"
            ) from e
        except Exception as e:
            raise EncryptionError(f"Unexpected encryption error: {e!s}") from e

    async def decrypt_credentials(
        self,
        encrypted_account_id: str,
        encrypted_secret_key: str,
    ) -> DecryptedCredentials:
        """Decrypt Hostaway API credentials using Supabase Vault.

        Calls the decrypt_hostaway_credential RPC function created in migration
        20251013_003_vault_setup.sql. Decryption uses pgsodium to reverse the
        encryption process.

        Args:
            encrypted_account_id: Base64-encoded encrypted account ID
            encrypted_secret_key: Base64-encoded encrypted secret key

        Returns:
            DecryptedCredentials with plaintext values

        Raises:
            DecryptionError: If decryption fails (invalid ciphertext or missing key)

        Example:
            >>> service = CredentialService()
            >>> decrypted = await service.decrypt_credentials(
            ...     encrypted_account_id="base64_ciphertext...",
            ...     encrypted_secret_key="base64_ciphertext..."
            ... )
            >>> print(decrypted.account_id)  # ACC_12345
            >>> print(decrypted.secret_key)  # sk_live_abc123...
        """
        try:
            # Decrypt account ID
            account_response = self.supabase.rpc(
                "decrypt_hostaway_credential",
                {"ciphertext": encrypted_account_id},
            ).execute()

            if not account_response.data:
                raise DecryptionError("Failed to decrypt account_id: No data returned")

            account_id: str = account_response.data

            # Decrypt secret key
            secret_response = self.supabase.rpc(
                "decrypt_hostaway_credential",
                {"ciphertext": encrypted_secret_key},
            ).execute()

            if not secret_response.data:
                raise DecryptionError("Failed to decrypt secret_key: No data returned")

            secret_key: str = secret_response.data

            return DecryptedCredentials(
                account_id=account_id,
                secret_key=secret_key,
            )

        except SupabaseClientError as e:
            raise DecryptionError(
                f"Vault decryption failed: {e!s}. "
                "Ciphertext may be corrupted or encryption key missing from vault.secrets"
            ) from e
        except Exception as e:
            raise DecryptionError(f"Unexpected decryption error: {e!s}") from e

    async def validate_and_encrypt(
        self,
        account_id: str,
        secret_key: str,
    ) -> tuple[EncryptedCredentials, bool]:
        """Validate Hostaway credentials and encrypt if valid.

        This is a convenience method that combines validation with encryption.
        In a full implementation, this would make a test API call to Hostaway
        to verify credentials before encrypting.

        Args:
            account_id: Hostaway account ID (plaintext)
            secret_key: Hostaway secret key (plaintext)

        Returns:
            Tuple of (encrypted_credentials, is_valid)

        Raises:
            EncryptionError: If encryption fails

        Example:
            >>> service = CredentialService()
            >>> encrypted, valid = await service.validate_and_encrypt(
            ...     account_id="ACC_12345",
            ...     secret_key="sk_live_abc123..."
            ... )
            >>> if valid:
            ...     # Store encrypted credentials in database
            ...     pass
        """
        # TODO: Implement Hostaway API validation
        # For now, assume valid if both values provided
        is_valid = bool(account_id and secret_key)

        if not is_valid:
            raise EncryptionError("Both account_id and secret_key are required")

        encrypted = await self.encrypt_credentials(account_id, secret_key)
        return encrypted, is_valid
