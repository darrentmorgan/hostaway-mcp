"""Integration tests for 404 vs 401 priority fix (User Story 1).

Tests that non-existent routes return HTTP 404 instead of 401,
improving API consumer developer experience.

These tests follow TDD - written FIRST, must FAIL before implementation.
"""

from fastapi.testclient import TestClient


def test_nonexistent_route_returns_404(test_client: TestClient) -> None:
    """Test that non-existent routes return 404 without auth headers.

    This is the core behavior fix: routes that don't exist should return
    404 BEFORE authentication is checked, not 401.

    Args:
        test_client: FastAPI TestClient fixture
    """
    # Request to a route that definitely doesn't exist
    response = test_client.get("/api/nonexistent")

    # Should return 404 Not Found, not 401 Unauthorized
    assert response.status_code == 404, (
        f"Expected 404 for non-existent route, got {response.status_code}. "
        "Route existence should be checked BEFORE authentication."
    )

    # Response should include route path in error message
    assert "nonexistent" in response.json()["detail"].lower()


def test_nonexistent_route_with_auth_returns_404(
    test_client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Test that non-existent routes return 404 even WITH valid auth.

    Even if authentication is provided, a non-existent route should
    still return 404, not 200 or any other status.

    Args:
        test_client: FastAPI TestClient fixture
        auth_headers: Valid authentication headers
    """
    # Request to non-existent route WITH authentication
    response = test_client.get("/api/nonexistent", headers=auth_headers)

    # Should still return 404, not 401 or 200
    assert response.status_code == 404, (
        f"Expected 404 for non-existent route even with auth, got {response.status_code}"
    )


def test_existing_route_requires_auth(test_client: TestClient) -> None:
    """Test that existing routes still check authentication.

    This ensures the fix doesn't bypass authentication middleware for valid routes.
    Note: The actual auth check is mocked by global Supabase fixture,
    so this test verifies the route exists and is processed by middleware.

    Args:
        test_client: FastAPI TestClient fixture
    """
    # Request to an existing protected route WITHOUT authentication
    response = test_client.get("/api/listings")

    # Due to test Supabase mocking, this will pass auth but fail at endpoint
    # The important thing is it doesn't return 404 (which would mean route not found)
    # It should return either 401 (auth failed) or 500 (endpoint error after auth)
    # but NOT 404 (which was the original bug)
    assert response.status_code != 404, (
        f"Expected existing route to not return 404, got {response.status_code}. "
        "The 404 fix should not affect existing routes."
    )

    # Verify it's a protected route by checking it doesn't return 200 without proper setup
    assert response.status_code in [401, 500], (
        f"Expected 401 or 500 for protected route without full test setup, got {response.status_code}"
    )


def test_405_method_not_allowed_still_works(test_client: TestClient) -> None:
    """Test that 405 Method Not Allowed handling is preserved.

    When a route exists but the HTTP method is not allowed,
    should return 405, not 404 or 401.

    Args:
        test_client: FastAPI TestClient fixture
    """
    # GET /api/listings exists, but DELETE might not be allowed
    # (assuming DELETE is not implemented for this endpoint)
    response = test_client.delete("/api/listings")

    # Should return either 405 (method not allowed) or 401 (auth required first)
    # Both are acceptable depending on middleware order
    assert response.status_code in [
        405,
        401,
    ], f"Expected 405 or 401 for disallowed method, got {response.status_code}"


def test_public_routes_remain_accessible(test_client: TestClient) -> None:
    """Test that public routes (/, /health, /docs) are not affected.

    Public routes should still be accessible without authentication
    and should not return 404.

    Args:
        test_client: FastAPI TestClient fixture
    """
    # Test root endpoint
    response_root = test_client.get("/")
    assert response_root.status_code == 200, "Root endpoint should be public"

    # Test health endpoint
    response_health = test_client.get("/health")
    assert response_health.status_code == 200, "Health endpoint should be public"

    # Test docs endpoint
    response_docs = test_client.get("/docs")
    assert response_docs.status_code == 200, "Docs endpoint should be public"


def test_404_response_includes_correlation_id(
    test_client: TestClient, correlation_id_headers: dict[str, str]
) -> None:
    """Test that 404 responses preserve correlation ID for tracing.

    Args:
        test_client: FastAPI TestClient fixture
        correlation_id_headers: Correlation ID header fixture
    """
    # Request non-existent route with correlation ID
    response = test_client.get("/api/nonexistent", headers=correlation_id_headers)

    assert response.status_code == 404
    # Correlation ID should be in response headers for request tracing
    assert "x-correlation-id" in response.headers or "X-Correlation-ID" in response.headers


def test_404_response_preserves_cors_headers(test_client: TestClient) -> None:
    """Test that 404 responses preserve CORS headers.

    CORS middleware should still apply to 404 responses to prevent
    browser CORS errors on non-existent routes.

    Args:
        test_client: FastAPI TestClient fixture
    """
    # Request with Origin header (simulating cross-origin request)
    headers = {"Origin": "http://example.com"}
    response = test_client.get("/api/nonexistent", headers=headers)

    assert response.status_code == 404
    # CORS headers should be present
    # Note: Exact header depends on CORSMiddleware configuration
    # At minimum, Access-Control-Allow-Origin should be present
    assert (
        "access-control-allow-origin" in response.headers
        or "Access-Control-Allow-Origin" in response.headers
    ), "CORS headers should be preserved in 404 responses"
