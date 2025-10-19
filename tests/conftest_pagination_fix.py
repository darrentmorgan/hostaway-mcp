"""Pytest configuration for pagination tests with proper mocking.

This provides fixtures that properly mock all dependencies needed for
API endpoint tests including Supabase, authentication, and Hostaway client.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(scope="function")
def mock_supabase_client():
    """Create a mock Supabase client for usage tracking."""
    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock())
    mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
        return_value=MagicMock(data={"id": "test-org-123", "name": "Test Org"})
    )
    return mock_client


@pytest.fixture(scope="function", autouse=True)
def mock_supabase_for_all_tests(mock_supabase_client):
    """Automatically mock Supabase for all tests to prevent connection errors."""
    with patch(
        "src.services.supabase_client.get_supabase_client", return_value=mock_supabase_client
    ):
        with patch(
            "src.api.middleware.usage_tracking.get_supabase_client",
            return_value=mock_supabase_client,
        ):
            yield
