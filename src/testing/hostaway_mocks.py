"""HTTP mocking for Hostaway API using respx.

Provides controlled, deterministic mock responses for testing pagination,
error handling, and other behaviors without hitting the real API.
"""

import os
from typing import Any

import httpx
import respx
from respx import MockRouter


def is_test_mode() -> bool:
    """Check if running in test mode based on environment variable."""
    return os.getenv("HOSTAWAY_TEST_MODE", "false").lower() == "true"


def generate_mock_listings(count: int, offset: int = 0) -> list[dict[str, Any]]:
    """Generate deterministic mock listing data.

    Args:
        count: Number of listings to generate
        offset: Starting offset for ID generation

    Returns:
        List of mock listing dictionaries
    """
    listings = []
    for i in range(count):
        listing_id = 400000 + offset + i
        listings.append(
            {
                "id": listing_id,
                "name": f"Property {listing_id}",
                "address": f"{i + 1} Main Street",
                "city": "Test City",
                "state": "TC",
                "country": "US",
                "zipCode": f"{10000 + i}",
                "bedrooms": (i % 4) + 1,
                "bathrooms": (i % 3) + 1,
                "maxGuests": (i % 8) + 2,
                "basePrice": 100 + (i * 10),
                "currency": "USD",
                "status": "active",
            }
        )
    return listings


def generate_mock_bookings(count: int, offset: int = 0) -> list[dict[str, Any]]:
    """Generate deterministic mock booking data.

    Args:
        count: Number of bookings to generate
        offset: Starting offset for ID generation

    Returns:
        List of mock booking dictionaries
    """
    bookings = []
    for i in range(count):
        booking_id = 500000 + offset + i
        bookings.append(
            {
                "id": booking_id,
                "listingId": 400000 + (i % 10),
                "channelName": "airbnb" if i % 2 == 0 else "vrbo",
                "guestName": f"Guest {i}",
                "checkIn": f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                "checkOut": f"2025-{(i % 12) + 1:02d}-{((i % 28) + 5):02d}",
                "status": "confirmed",
                "totalPrice": 500 + (i * 50),
                "numberOfGuests": (i % 6) + 1,
            }
        )
    return bookings


def setup_hostaway_mocks(router: MockRouter | None = None) -> MockRouter:
    """Setup comprehensive Hostaway API mocks.

    Args:
        router: Optional existing respx router to add mocks to

    Returns:
        MockRouter with all Hostaway API endpoints mocked
    """
    if router is None:
        router = respx.mock(assert_all_called=False, base_url="https://api.hostaway.com")

    # Total items in mock dataset
    total_listings = 100
    total_bookings = 100

    # Mock OAuth token endpoint
    router.post("https://api.hostaway.com/v1/accessTokens").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "mock_token_12345",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
        )
    )

    # Mock listings endpoint with dynamic pagination
    def listings_handler(request: httpx.Request) -> httpx.Response:
        """Handle listings requests with proper pagination."""
        params = dict(request.url.params)
        limit = int(params.get("limit", 50))
        offset = int(params.get("offset", 0))

        # Clamp limit
        limit = min(limit, 200)

        # Generate page of results
        listings = generate_mock_listings(min(limit, total_listings - offset), offset)
        has_more = offset + len(listings) < total_listings

        return httpx.Response(
            200,
            json={
                "status": "success",
                "result": listings,
                "count": len(listings),
                "limit": limit,
                "offset": offset,
                "hasMore": has_more,
            },
        )

    router.get("https://api.hostaway.com/v1/listings").mock(side_effect=listings_handler)

    # Mock bookings/reservations endpoint with dynamic pagination
    def bookings_handler(request: httpx.Request) -> httpx.Response:
        """Handle bookings requests with proper pagination."""
        params = dict(request.url.params)
        limit = int(params.get("limit", 50))
        offset = int(params.get("offset", 0))

        # Clamp limit
        limit = min(limit, 200)

        # Generate page of results
        bookings = generate_mock_bookings(min(limit, total_bookings - offset), offset)
        has_more = offset + len(bookings) < total_bookings

        return httpx.Response(
            200,
            json={
                "status": "success",
                "result": bookings,
                "count": len(bookings),
                "limit": limit,
                "offset": offset,
                "hasMore": has_more,
            },
        )

    router.get("https://api.hostaway.com/v1/reservations").mock(side_effect=bookings_handler)

    # Start the router to activate mocking
    router.start()

    return router
