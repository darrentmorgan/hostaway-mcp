"""Integration tests for pagination in API endpoints.

Tests cursor-based pagination for listings and bookings endpoints.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.mcp.auth import get_authenticated_client
from src.utils.cursor_codec import decode_cursor


@pytest.fixture
def mock_hostaway_client(mocker):
    """Create a mock Hostaway client."""
    mock = mocker.MagicMock()
    mock.get_listings = AsyncMock()
    mock.search_bookings = AsyncMock()
    return mock


@pytest.fixture
def client(mock_hostaway_client, mocker):
    """Create test client with dependency overrides and mocked auth."""
    # Override the authentication dependency to return our mock
    app.dependency_overrides[get_authenticated_client] = lambda: mock_hostaway_client

    # Mock the API key verification to always succeed
    async def mock_verify_api_key(request, x_api_key=None):
        # Store mock auth context in request state
        request.state.organization_id = "test-org-123"
        request.state.api_key_id = "test-key-123"
        return {"organization_id": "test-org-123", "api_key_id": "test-key-123"}

    mocker.patch("src.mcp.security.verify_api_key", side_effect=mock_verify_api_key)

    client = TestClient(app)
    yield client

    # Cleanup: remove overrides
    app.dependency_overrides.clear()


class TestListingsPagination:
    """Test pagination for listings endpoint."""

    def test_listings_first_page_returns_paginated_response(self, client, mock_hostaway_client):
        """Test that first page request returns PaginatedResponse structure."""
        # Configure mock to return 50 listings
        mock_hostaway_client.get_listings.return_value = [
            {"id": i, "name": f"Listing {i}"} for i in range(50)
        ]

        # Request first page
        response = client.get("/api/listings?limit=50", headers={"X-API-Key": "test-key"})

        assert response.status_code == 200
        data = response.json()

        # Verify paginated response structure
        assert "items" in data
        assert "nextCursor" in data
        assert "meta" in data

        # Verify metadata
        assert data["meta"]["pageSize"] == 50
        assert data["meta"]["hasMore"] is True
        assert data["nextCursor"] is not None

        # Verify items
        assert len(data["items"]) == 50

    def test_listings_cursor_navigation(self, client, mock_hostaway_client):
        """Test navigating through pages using cursor."""
        # Configure mock for multiple pages
        first_page_items = [{"id": i, "name": f"Listing {i}"} for i in range(50)]
        second_page_items = [{"id": i, "name": f"Listing {i}"} for i in range(50, 100)]

        mock_hostaway_client.get_listings.side_effect = [first_page_items, second_page_items]

        # Get first page
        response1 = client.get("/api/listings?limit=50", headers={"X-API-Key": "test-key"})

        assert response1.status_code == 200
        data1 = response1.json()
        cursor = data1["nextCursor"]
        assert cursor is not None

        # Use cursor to get second page
        response2 = client.get(f"/api/listings?cursor={cursor}", headers={"X-API-Key": "test-key"})

        assert response2.status_code == 200
        data2 = response2.json()

        # Verify second page structure
        assert "items" in data2
        assert len(data2["items"]) == 50

        # Verify cursor contains offset=50
        cursor_data = decode_cursor(cursor, secret="hostaway-cursor-secret")
        assert cursor_data["offset"] == 50

    def test_listings_invalid_cursor_returns_400(self, client, mock_hostaway_client):
        """Test that invalid cursor returns 400 error."""
        # Request with invalid cursor
        response = client.get(
            "/api/listings?cursor=invalid-cursor", headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 400
        assert "Invalid cursor" in response.json()["detail"]

    def test_listings_final_page_no_next_cursor(self, client, mock_hostaway_client):
        """Test that final page has no nextCursor."""
        # Mock the Hostaway client to return < page_size items
        mock_hostaway_client.get_listings.return_value = [
            {"id": i, "name": f"Listing {i}"} for i in range(25)
        ]

        # Request page
        response = client.get("/api/listings?limit=50", headers={"X-API-Key": "test-key"})

        assert response.status_code == 200
        data = response.json()

        # Verify no next cursor (final page)
        assert data["nextCursor"] is None
        assert data["meta"]["hasMore"] is False
        assert data["meta"]["pageSize"] == 25


class TestBookingsPagination:
    """Test pagination for bookings endpoint."""

    def test_bookings_first_page_returns_paginated_response(self, client, mock_hostaway_client):
        """Test that first page request returns PaginatedResponse structure."""
        # Configure mock to return 100 bookings
        mock_hostaway_client.search_bookings.return_value = [
            {"id": i, "guestName": f"Guest {i}"} for i in range(100)
        ]

        # Request first page
        response = client.get("/api/reservations?limit=100", headers={"X-API-Key": "test-key"})

        assert response.status_code == 200
        data = response.json()

        # Verify paginated response structure
        assert "items" in data
        assert "nextCursor" in data
        assert "meta" in data

        # Verify metadata
        assert data["meta"]["pageSize"] == 100
        assert data["meta"]["hasMore"] is True

    def test_bookings_with_filters_and_pagination(self, client, mock_hostaway_client):
        """Test pagination works with query filters."""
        # Configure mock to return filtered bookings
        mock_hostaway_client.search_bookings.return_value = [
            {"id": i, "status": "confirmed"} for i in range(50)
        ]

        # Request with filters
        response = client.get(
            "/api/reservations?limit=50&status=confirmed&listing_id=123",
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response
        assert "items" in data
        assert len(data["items"]) == 50

        # Verify client was called with correct filters
        mock_hostaway_client.search_bookings.assert_called_once()
        call_kwargs = mock_hostaway_client.search_bookings.call_args.kwargs
        assert call_kwargs["status"] == ["confirmed"]
        assert call_kwargs["listing_id"] == 123

    def test_bookings_cursor_preserves_offset(self, client, mock_hostaway_client):
        """Test that cursor correctly encodes and decodes offset."""
        # Configure mock to return 100 bookings
        mock_hostaway_client.search_bookings.return_value = [{"id": i} for i in range(100)]

        # Get first page
        response = client.get("/api/reservations?limit=100", headers={"X-API-Key": "test-key"})

        assert response.status_code == 200
        data = response.json()
        cursor = data["nextCursor"]

        # Decode cursor and verify offset
        cursor_data = decode_cursor(cursor, secret="hostaway-cursor-secret")
        assert cursor_data["offset"] == 100
        assert "ts" in cursor_data  # Timestamp should be present


class TestPaginationBackwardsCompatibility:
    """Test that pagination changes are backwards compatible."""

    def test_old_clients_can_ignore_new_fields(self, client, mock_hostaway_client):
        """Test that old clients can ignore nextCursor and meta fields."""
        # Configure mock to return a single listing
        mock_hostaway_client.get_listings.return_value = [{"id": 1, "name": "Listing 1"}]

        # Request
        response = client.get("/api/listings?limit=10", headers={"X-API-Key": "test-key"})

        assert response.status_code == 200
        data = response.json()

        # Old client would look for "items" field
        assert "items" in data
        assert len(data["items"]) == 1

        # New fields are present but optional for old clients
        assert "nextCursor" in data
        assert "meta" in data
