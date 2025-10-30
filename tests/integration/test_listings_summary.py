"""Integration tests for listings API summary parameter.

Tests the summary=true query parameter on GET /api/listings endpoint.
Verifies:
- Summarized response returns only essential fields
- Backward compatibility (no summary parameter)
- Response size reduction
- Note field presence in metadata
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.mcp.config import HostawayConfig


@pytest.fixture
def test_config(monkeypatch: pytest.MonkeyPatch) -> HostawayConfig:
    """Create test configuration."""
    monkeypatch.setenv("HOSTAWAY_ACCOUNT_ID", "test_account_123")
    monkeypatch.setenv("HOSTAWAY_SECRET_KEY", "test_secret_key_456")
    monkeypatch.setenv("HOSTAWAY_API_BASE_URL", "https://api.hostaway.com/v1")
    return HostawayConfig()  # type: ignore[call-arg]


@pytest.fixture
def mock_full_listing_response() -> list[dict]:
    """Create mock Hostaway full listing response with all fields."""
    return [
        {
            "id": 12345,
            "name": "Luxury Villa in Seminyak",
            "address": "123 Sunset Blvd",
            "city": "Seminyak",
            "state": "Bali",
            "country": "Indonesia",
            "postal_code": "80361",
            "description": "Stunning 3-bedroom villa with private pool...",
            "capacity": 6,
            "bedrooms": 3,
            "bathrooms": 2.5,
            "property_type": "villa",
            "base_price": 250.00,
            "isActive": True,
            "amenities": ["Pool", "WiFi", "Kitchen", "Air Conditioning"],
            "images": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
        },
        {
            "id": 12346,
            "name": "Beachfront Apartment",
            "address": "456 Ocean Ave",
            "city": "Canggu",
            "state": "Bali",
            "country": "Indonesia",
            "postal_code": "80351",
            "description": "Modern 2-bedroom apartment steps from beach...",
            "capacity": 4,
            "bedrooms": 2,
            "bathrooms": 2,
            "property_type": "apartment",
            "base_price": 180.00,
            "isActive": False,  # Inactive listing
            "amenities": ["WiFi", "Kitchen", "Parking"],
            "images": ["https://example.com/img3.jpg"],
        },
    ]


@pytest.mark.asyncio
async def test_get_listings_with_summary_true(
    test_config: HostawayConfig, mock_full_listing_response: list[dict]
) -> None:
    """Test GET /listings?summary=true returns summarized response.

    Verifies:
    - Returns 200 OK
    - Response items contain only summarized fields
    - metadata.note field is present
    - Status field is derived from isActive
    """
    from fastapi.testclient import TestClient

    from src.api.main import app

    with patch("src.mcp.auth.get_authenticated_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.config = test_config
        mock_client.get_listings = AsyncMock(return_value=mock_full_listing_response)
        mock_get_client.return_value = mock_client

        client = TestClient(app)
        response = client.get("/api/listings?summary=true&limit=10")

    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert "nextCursor" in data

    # Verify metadata contains note field
    assert data["meta"]["note"] is not None
    assert "GET /api/listings/{id}" in data["meta"]["note"]

    # Verify first item has only summarized fields
    first_item = data["items"][0]
    assert set(first_item.keys()) == {"id", "name", "city", "country", "bedrooms", "status"}
    assert first_item["id"] == 12345
    assert first_item["name"] == "Luxury Villa in Seminyak"
    assert first_item["city"] == "Seminyak"
    assert first_item["country"] == "Indonesia"
    assert first_item["bedrooms"] == 3
    assert first_item["status"] == "Available"  # Derived from isActive=True

    # Verify second item (inactive listing)
    second_item = data["items"][1]
    assert second_item["id"] == 12346
    assert second_item["status"] == "Inactive"  # Derived from isActive=False

    # Verify no full fields are present
    assert "description" not in first_item
    assert "amenities" not in first_item
    assert "address" not in first_item
    assert "base_price" not in first_item


@pytest.mark.asyncio
async def test_get_listings_without_summary_returns_full_response(
    test_config: HostawayConfig, mock_full_listing_response: list[dict]
) -> None:
    """Test GET /listings (no summary parameter) returns full response.

    Verifies backward compatibility:
    - Returns 200 OK
    - Response items contain all fields
    - metadata.note field is NOT present
    """
    from fastapi.testclient import TestClient

    from src.api.main import app

    with patch("src.mcp.auth.get_authenticated_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.config = test_config
        mock_client.get_listings = AsyncMock(return_value=mock_full_listing_response)
        mock_get_client.return_value = mock_client

        client = TestClient(app)
        response = client.get("/api/listings?limit=10")

    assert response.status_code == 200

    data = response.json()
    assert "items" in data

    # Verify first item has full fields
    first_item = data["items"][0]
    assert first_item["id"] == 12345
    assert "description" in first_item
    assert "amenities" in first_item
    assert "address" in first_item
    assert "base_price" in first_item

    # Verify metadata does NOT contain note field (or is None)
    assert data["meta"].get("note") is None


@pytest.mark.asyncio
async def test_get_listings_summary_false_returns_full_response(
    test_config: HostawayConfig, mock_full_listing_response: list[dict]
) -> None:
    """Test GET /listings?summary=false returns full response.

    Verifies:
    - Explicit summary=false behaves same as no parameter
    """
    from fastapi.testclient import TestClient

    from src.api.main import app

    with patch("src.mcp.auth.get_authenticated_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.config = test_config
        mock_client.get_listings = AsyncMock(return_value=mock_full_listing_response)
        mock_get_client.return_value = mock_client

        client = TestClient(app)
        response = client.get("/api/listings?summary=false&limit=10")

    assert response.status_code == 200

    data = response.json()
    first_item = data["items"][0]

    # Verify full fields present
    assert "description" in first_item
    assert "amenities" in first_item


@pytest.mark.asyncio
async def test_get_listings_summary_with_null_optional_fields(test_config: HostawayConfig) -> None:
    """Test summary mode handles null optional fields gracefully.

    Verifies:
    - city=None is accepted
    - country=None is accepted
    - bedrooms defaults to 0 if missing
    """
    from fastapi.testclient import TestClient

    from src.api.main import app

    mock_listing_with_nulls = [
        {
            "id": 1,
            "name": "Test Property",
            "city": None,  # Null city
            "country": None,  # Null country
            # bedrooms missing
            "isActive": True,
        }
    ]

    with patch("src.mcp.auth.get_authenticated_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.config = test_config
        mock_client.get_listings = AsyncMock(return_value=mock_listing_with_nulls)
        mock_get_client.return_value = mock_client

        client = TestClient(app)
        response = client.get("/api/listings?summary=true")

    assert response.status_code == 200

    data = response.json()
    first_item = data["items"][0]

    assert first_item["city"] is None
    assert first_item["country"] is None
    assert first_item["bedrooms"] == 0  # Default value


@pytest.mark.asyncio
async def test_get_listings_summary_response_size_reduction(
    test_config: HostawayConfig, mock_full_listing_response: list[dict]
) -> None:
    """Test summary mode achieves significant response size reduction.

    Verifies:
    - Summary response is at least 70% smaller than full response
    """
    import json

    from fastapi.testclient import TestClient

    from src.api.main import app

    with patch("src.mcp.auth.get_authenticated_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.config = test_config
        mock_client.get_listings = AsyncMock(return_value=mock_full_listing_response)
        mock_get_client.return_value = mock_client

        client = TestClient(app)

        # Get full response
        full_response = client.get("/api/listings?limit=10")
        full_size = len(json.dumps(full_response.json()))

        # Get summary response
        summary_response = client.get("/api/listings?summary=true&limit=10")
        summary_size = len(json.dumps(summary_response.json()))

    # Calculate reduction percentage
    reduction = ((full_size - summary_size) / full_size) * 100

    # Verify at least 70% reduction (target is 80-90%)
    assert reduction >= 70, f"Expected >=70% reduction, got {reduction:.2f}%"
