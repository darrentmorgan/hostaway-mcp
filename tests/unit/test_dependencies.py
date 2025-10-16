"""Unit tests for src/api/dependencies.py"""

import hashlib
from unittest.mock import MagicMock

import pytest

from src.api.dependencies import (
    AuthenticationError,
    CredentialError,
    OrganizationContext,
    get_organization_context,
    hash_api_key,
)
from src.services.credential_service import DecryptedCredentials

# === Test hash_api_key ===


def test_hash_api_key_returns_sha256_hex():
    """Test that hash_api_key returns 64-character SHA-256 hex digest"""
    # Arrange
    api_key = "test_api_key_123"

    # Act
    result = hash_api_key(api_key)

    # Assert
    assert len(result) == 64  # SHA-256 produces 64-character hex string
    assert all(c in "0123456789abcdef" for c in result)  # All hex characters


def test_hash_api_key_consistent():
    """Test that same input produces same hash"""
    # Arrange
    api_key = "my_secret_key"

    # Act
    hash1 = hash_api_key(api_key)
    hash2 = hash_api_key(api_key)

    # Assert
    assert hash1 == hash2


def test_hash_api_key_different_inputs():
    """Test that different inputs produce different hashes"""
    # Arrange
    key1 = "key_one"
    key2 = "key_two"

    # Act
    hash1 = hash_api_key(key1)
    hash2 = hash_api_key(key2)

    # Assert
    assert hash1 != hash2


def test_hash_api_key_matches_sha256():
    """Test that hash matches manual SHA-256 computation"""
    # Arrange
    api_key = "test123"
    expected_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Act
    result = hash_api_key(api_key)

    # Assert
    assert result == expected_hash


# === Test get_organization_context ===


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client"""
    mock = MagicMock()
    mock.table.return_value = mock
    mock.select.return_value = mock
    mock.eq.return_value = mock
    mock.single.return_value = mock
    mock.rpc.return_value = mock
    return mock


@pytest.mark.asyncio
async def test_get_organization_context_success(mock_supabase, monkeypatch):
    """Test successful organization context retrieval"""
    # Arrange
    api_key = "valid_api_key_123"
    key_hash = hash_api_key(api_key)

    # Mock all execute calls in order: api_key lookup, credentials lookup, decrypt, update_last_used
    mock_execute_calls = [
        MagicMock(
            data={
                "id": 1,
                "organization_id": 100,
                "is_active": True,
            }
        ),
        MagicMock(
            data={
                "account_id": "ACC_12345",
                "encrypted_secret_key": "encrypted_secret",
                "credentials_valid": True,
            }
        ),
        MagicMock(data="decrypted_secret_key"),  # RPC decrypt response
        MagicMock(data=None),  # Update last_used_at response (fire and forget)
    ]
    mock_supabase.execute.side_effect = mock_execute_calls

    # Patch get_supabase_client
    monkeypatch.setattr(
        "src.api.dependencies.get_supabase_client",
        lambda: mock_supabase,
    )

    # Act
    context = await get_organization_context(x_api_key=api_key)

    # Assert
    assert isinstance(context, OrganizationContext)
    assert context.organization_id == 100
    assert context.api_key_id == 1
    assert context.hostaway_credentials.account_id == "ACC_12345"
    assert context.hostaway_credentials.secret_key == "decrypted_secret_key"

    # Verify calls
    assert mock_supabase.table.call_count == 2  # api_keys, hostaway_credentials
    assert mock_supabase.rpc.call_count == 2  # decrypt, update_last_used


@pytest.mark.asyncio
async def test_get_organization_context_invalid_api_key(mock_supabase, monkeypatch):
    """Test with invalid API key (not found)"""
    # Arrange
    api_key = "invalid_key"

    # Mock API key lookup returning no data
    mock_supabase.execute.return_value = MagicMock(data=None)

    monkeypatch.setattr(
        "src.api.dependencies.get_supabase_client",
        lambda: mock_supabase,
    )

    # Act & Assert
    with pytest.raises(AuthenticationError) as exc_info:
        await get_organization_context(x_api_key=api_key)

    assert "API key not found or inactive" in str(exc_info.value.detail)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_organization_context_inactive_api_key(mock_supabase, monkeypatch):
    """Test with inactive API key"""
    # Arrange
    api_key = "inactive_key"

    # Mock query that returns no data (filtered by is_active=True)
    mock_supabase.execute.return_value = MagicMock(data=None)

    monkeypatch.setattr(
        "src.api.dependencies.get_supabase_client",
        lambda: mock_supabase,
    )

    # Act & Assert
    with pytest.raises(AuthenticationError) as exc_info:
        await get_organization_context(x_api_key=api_key)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_organization_context_missing_credentials(mock_supabase, monkeypatch):
    """Test when organization has no Hostaway credentials configured"""
    # Arrange
    api_key = "valid_key"

    # Mock API key lookup success
    mock_execute_calls = [
        MagicMock(
            data={
                "id": 1,
                "organization_id": 100,
                "is_active": True,
            }
        ),
        MagicMock(data=None),  # No credentials found
    ]
    mock_supabase.execute.side_effect = mock_execute_calls

    monkeypatch.setattr(
        "src.api.dependencies.get_supabase_client",
        lambda: mock_supabase,
    )

    # Act & Assert
    with pytest.raises(CredentialError) as exc_info:
        await get_organization_context(x_api_key=api_key)

    assert "Hostaway credentials not configured" in str(exc_info.value.detail)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_organization_context_invalid_credentials(mock_supabase, monkeypatch):
    """Test when Hostaway credentials are marked as invalid"""
    # Arrange
    api_key = "valid_key"

    # Mock API key lookup success, credentials marked invalid
    mock_execute_calls = [
        MagicMock(
            data={
                "id": 1,
                "organization_id": 100,
                "is_active": True,
            }
        ),
        MagicMock(
            data={
                "account_id": "ACC_12345",
                "encrypted_secret_key": "encrypted_secret",
                "credentials_valid": False,  # Marked invalid
            }
        ),
    ]
    mock_supabase.execute.side_effect = mock_execute_calls

    monkeypatch.setattr(
        "src.api.dependencies.get_supabase_client",
        lambda: mock_supabase,
    )

    # Act & Assert
    with pytest.raises(CredentialError) as exc_info:
        await get_organization_context(x_api_key=api_key)

    assert "Hostaway credentials are invalid" in str(exc_info.value.detail)
    assert "re-authenticate" in str(exc_info.value.detail)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_organization_context_decryption_failure(mock_supabase, monkeypatch):
    """Test when credential decryption fails"""
    # Arrange
    api_key = "valid_key"

    # Mock API key and credentials lookup success, decryption fails
    mock_execute_calls = [
        MagicMock(
            data={
                "id": 1,
                "organization_id": 100,
                "is_active": True,
            }
        ),
        MagicMock(
            data={
                "account_id": "ACC_12345",
                "encrypted_secret_key": "encrypted_secret",
                "credentials_valid": True,
            }
        ),
        MagicMock(data=None),  # RPC decrypt returns None
    ]
    mock_supabase.execute.side_effect = mock_execute_calls

    monkeypatch.setattr(
        "src.api.dependencies.get_supabase_client",
        lambda: mock_supabase,
    )

    # Act & Assert
    with pytest.raises(CredentialError) as exc_info:
        await get_organization_context(x_api_key=api_key)

    assert "Failed to decrypt" in str(exc_info.value.detail)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_organization_context_updates_last_used(mock_supabase, monkeypatch):
    """Test that last_used_at timestamp is updated"""
    # Arrange
    api_key = "valid_key"
    key_hash = hash_api_key(api_key)

    # Mock all successful responses
    mock_execute_calls = [
        MagicMock(
            data={
                "id": 1,
                "organization_id": 100,
                "is_active": True,
            }
        ),
        MagicMock(
            data={
                "account_id": "ACC_12345",
                "encrypted_secret_key": "encrypted_secret",
                "credentials_valid": True,
            }
        ),
        MagicMock(data="decrypted_secret"),
        MagicMock(data={"success": True}),  # Update last_used_at
    ]
    mock_supabase.execute.side_effect = mock_execute_calls

    monkeypatch.setattr(
        "src.api.dependencies.get_supabase_client",
        lambda: mock_supabase,
    )

    # Act
    await get_organization_context(x_api_key=api_key)

    # Assert
    # Verify RPC was called with correct parameters
    rpc_calls = list(mock_supabase.rpc.call_args_list)
    assert len(rpc_calls) == 2  # decrypt and update_last_used

    # Check update_last_used call
    update_call = rpc_calls[1]
    assert update_call[0][0] == "update_api_key_last_used"
    assert update_call[0][1]["key_hash"] == key_hash


@pytest.mark.asyncio
async def test_get_organization_context_last_used_failure_ignored(mock_supabase, monkeypatch):
    """Test that failures in last_used_at update don't fail the request"""
    # Arrange
    api_key = "valid_key"

    # Mock successful flow but last_used_at update fails
    mock_execute_calls = [
        MagicMock(
            data={
                "id": 1,
                "organization_id": 100,
                "is_active": True,
            }
        ),
        MagicMock(
            data={
                "account_id": "ACC_12345",
                "encrypted_secret_key": "encrypted_secret",
                "credentials_valid": True,
            }
        ),
        MagicMock(data="decrypted_secret"),
    ]
    mock_supabase.execute.side_effect = mock_execute_calls

    # Make the update RPC call raise an exception
    def rpc_side_effect(function_name, *args, **kwargs):
        if function_name == "update_api_key_last_used":
            raise Exception("Database error")
        return mock_supabase

    mock_supabase.rpc.side_effect = rpc_side_effect

    monkeypatch.setattr(
        "src.api.dependencies.get_supabase_client",
        lambda: mock_supabase,
    )

    # Act - should succeed despite last_used_at failure
    context = await get_organization_context(x_api_key=api_key)

    # Assert
    assert context.organization_id == 100


@pytest.mark.asyncio
async def test_get_organization_context_organization_isolation(mock_supabase, monkeypatch):
    """Test that different API keys map to different organizations"""
    # Arrange
    api_key_org_1 = "org1_key"
    api_key_org_2 = "org2_key"

    # Test org 1
    mock_execute_calls = [
        MagicMock(data={"id": 1, "organization_id": 100, "is_active": True}),
        MagicMock(
            data={
                "account_id": "ACC_ORG1",
                "encrypted_secret_key": "encrypted1",
                "credentials_valid": True,
            }
        ),
        MagicMock(data="secret1"),
        MagicMock(data=None),
    ]
    mock_supabase.execute.side_effect = mock_execute_calls

    monkeypatch.setattr(
        "src.api.dependencies.get_supabase_client",
        lambda: mock_supabase,
    )

    context1 = await get_organization_context(x_api_key=api_key_org_1)

    # Test org 2
    mock_execute_calls = [
        MagicMock(data={"id": 2, "organization_id": 200, "is_active": True}),
        MagicMock(
            data={
                "account_id": "ACC_ORG2",
                "encrypted_secret_key": "encrypted2",
                "credentials_valid": True,
            }
        ),
        MagicMock(data="secret2"),
        MagicMock(data=None),
    ]
    mock_supabase.execute.side_effect = mock_execute_calls

    context2 = await get_organization_context(x_api_key=api_key_org_2)

    # Assert
    assert context1.organization_id == 100
    assert context1.hostaway_credentials.account_id == "ACC_ORG1"

    assert context2.organization_id == 200
    assert context2.hostaway_credentials.account_id == "ACC_ORG2"

    # Organizations are isolated
    assert context1.organization_id != context2.organization_id


@pytest.mark.asyncio
async def test_get_organization_context_database_error(mock_supabase, monkeypatch):
    """Test handling of database connection errors"""
    # Arrange
    api_key = "valid_key"

    # Mock database error
    mock_supabase.execute.side_effect = Exception("Database connection failed")

    monkeypatch.setattr(
        "src.api.dependencies.get_supabase_client",
        lambda: mock_supabase,
    )

    # Act & Assert
    with pytest.raises(AuthenticationError) as exc_info:
        await get_organization_context(x_api_key=api_key)

    assert "API key validation failed" in str(exc_info.value.detail)
    assert exc_info.value.status_code == 401


# === Test exception classes ===


def test_authentication_error_defaults():
    """Test AuthenticationError default values"""
    # Act
    error = AuthenticationError()

    # Assert
    assert error.status_code == 401
    assert "Invalid or inactive API key" in error.detail
    assert error.headers == {"WWW-Authenticate": "Bearer"}


def test_authentication_error_custom_detail():
    """Test AuthenticationError with custom detail"""
    # Act
    error = AuthenticationError(detail="Custom auth error")

    # Assert
    assert error.status_code == 401
    assert error.detail == "Custom auth error"


def test_credential_error_defaults():
    """Test CredentialError default values"""
    # Act
    error = CredentialError()

    # Assert
    assert error.status_code == 403
    assert "Hostaway credentials" in error.detail


def test_credential_error_custom_detail():
    """Test CredentialError with custom detail"""
    # Act
    error = CredentialError(detail="Custom credential error")

    # Assert
    assert error.status_code == 403
    assert error.detail == "Custom credential error"


# === Test OrganizationContext ===


def test_organization_context_creation():
    """Test OrganizationContext creation"""
    # Arrange
    creds = DecryptedCredentials(account_id="ACC_123", secret_key="secret")

    # Act
    context = OrganizationContext(
        organization_id=100,
        api_key_id=1,
        hostaway_credentials=creds,
    )

    # Assert
    assert context.organization_id == 100
    assert context.api_key_id == 1
    assert context.hostaway_credentials.account_id == "ACC_123"
    assert context.hostaway_credentials.secret_key == "secret"
