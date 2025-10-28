"""Unit tests for MCP security module.

Tests API key generation, hashing, and validation.
"""

import hashlib
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from src.mcp.security import (
    generate_api_key,
    get_supabase_client,
    hash_api_key,
    verify_api_key,
)


class TestApiKeyGeneration:
    """Test suite for API key generation and hashing."""

    def test_generate_api_key_format(self):
        """Test generated API key has correct format."""
        api_key = generate_api_key()

        assert api_key.startswith("mcp_")
        assert len(api_key) > 40  # mcp_ prefix + 32+ characters

    def test_generate_api_key_uniqueness(self):
        """Test generated keys are unique."""
        keys = [generate_api_key() for _ in range(100)]

        assert len(set(keys)) == 100  # All unique

    def test_hash_api_key(self):
        """Test API key hashing produces consistent results."""
        api_key = "mcp_test_key_12345"

        hash1 = hash_api_key(api_key)
        hash2 = hash_api_key(api_key)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest is 64 characters
        assert hash1 == hashlib.sha256(api_key.encode()).hexdigest()

    def test_hash_api_key_different_keys(self):
        """Test different keys produce different hashes."""
        key1 = "mcp_key_1"
        key2 = "mcp_key_2"

        hash1 = hash_api_key(key1)
        hash2 = hash_api_key(key2)

        assert hash1 != hash2


class TestSupabaseClient:
    """Test suite for Supabase client initialization."""

    @patch.dict(
        os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_SERVICE_KEY": "test-key"}
    )
    @patch("src.mcp.security.create_client")
    def test_get_supabase_client_success(self, mock_create_client):
        """Test Supabase client creation with valid credentials."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        client = get_supabase_client()

        assert client == mock_client
        mock_create_client.assert_called_once_with("https://test.supabase.co", "test-key")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_supabase_client_missing_url(self):
        """Test error when SUPABASE_URL missing."""
        with pytest.raises(
            ValueError, match="SUPABASE_URL and SUPABASE_SERVICE_KEY must be configured"
        ):
            get_supabase_client()

    @patch.dict(os.environ, {"SUPABASE_URL": "https://test.supabase.co"}, clear=True)
    def test_get_supabase_client_missing_key(self):
        """Test error when SUPABASE_SERVICE_KEY missing."""
        with pytest.raises(
            ValueError, match="SUPABASE_URL and SUPABASE_SERVICE_KEY must be configured"
        ):
            get_supabase_client()


class TestVerifyApiKey:
    """Test suite for API key verification."""

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/test"
        request.client.host = "127.0.0.1"
        request.state = MagicMock()
        return request

    @pytest.mark.asyncio
    async def test_verify_api_key_missing(self, mock_request):
        """Test verification fails when API key missing."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(mock_request, x_api_key=None)

        assert exc_info.value.status_code == 401
        assert "Missing API key" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("src.mcp.security.get_supabase_client")
    async def test_verify_api_key_invalid(self, mock_get_client, mock_request):
        """Test verification fails with invalid API key."""
        # Mock Supabase response for invalid key
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = None
        mock_client.table().select().eq().eq().single().execute.return_value = mock_response
        mock_get_client.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(mock_request, x_api_key="invalid_key")

        assert exc_info.value.status_code == 401
        assert "Invalid or inactive API key" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("src.mcp.security.get_supabase_client")
    async def test_verify_api_key_success(self, mock_get_client, mock_request):
        """Test successful API key verification."""
        api_key = "mcp_valid_key_12345"

        # Mock Supabase response for valid key
        mock_client = MagicMock()
        mock_select_response = MagicMock()
        mock_select_response.data = {
            "id": "key-123",
            "organization_id": "org-456",
            "key_hash": hash_api_key(api_key),
            "is_active": True,
        }

        # Build the chain of method calls
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.single.return_value = mock_query
        mock_query.execute.return_value = mock_select_response

        # Mock update call
        mock_update_query = MagicMock()
        mock_query.update.return_value = mock_update_query
        mock_update_query.eq.return_value = mock_update_query
        mock_update_query.execute.return_value = MagicMock()

        mock_get_client.return_value = mock_client

        result = await verify_api_key(mock_request, x_api_key=api_key)

        assert result["organization_id"] == "org-456"
        assert result["api_key_id"] == "key-123"
        assert mock_request.state.organization_id == "org-456"
        assert mock_request.state.api_key_id == "key-123"

    @pytest.mark.asyncio
    @patch("src.mcp.security.get_supabase_client")
    async def test_verify_api_key_updates_last_used(self, mock_get_client, mock_request):
        """Test that last_used_at timestamp is updated."""
        api_key = "mcp_valid_key_12345"

        # Mock Supabase client
        mock_client = MagicMock()
        mock_select_response = MagicMock()
        mock_select_response.data = {
            "id": "key-123",
            "organization_id": "org-456",
            "key_hash": hash_api_key(api_key),
            "is_active": True,
        }

        # Build query chain
        mock_query = MagicMock()
        mock_client.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.single.return_value = mock_query
        mock_query.execute.return_value = mock_select_response

        # Mock update call
        mock_update_query = MagicMock()
        mock_query.update.return_value = mock_update_query
        mock_update_query.eq.return_value = mock_update_query
        mock_update_query.execute.return_value = MagicMock()

        mock_get_client.return_value = mock_client

        await verify_api_key(mock_request, x_api_key=api_key)

        # Verify update was called
        mock_query.update.assert_called_once_with({"last_used_at": "now()"})

    @pytest.mark.asyncio
    @patch("src.mcp.security.get_supabase_client")
    async def test_verify_api_key_database_error(self, mock_get_client, mock_request):
        """Test handling of database errors."""
        mock_client = MagicMock()
        mock_client.table().select().eq().eq().single().execute.side_effect = Exception(
            "Database error"
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(mock_request, x_api_key="some_key")

        assert exc_info.value.status_code == 401
        assert "Authentication failed" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("src.mcp.security.get_supabase_client")
    async def test_verify_api_key_inactive(self, mock_get_client, mock_request):
        """Test verification fails for inactive API key."""
        api_key = "mcp_inactive_key"

        # Mock Supabase response for inactive key (is_active=False won't match query)
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = None  # .eq("is_active", True) filters it out
        mock_client.table().select().eq().eq().single().execute.return_value = mock_response
        mock_get_client.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(mock_request, x_api_key=api_key)

        assert exc_info.value.status_code == 401
        assert "Invalid or inactive API key" in exc_info.value.detail
