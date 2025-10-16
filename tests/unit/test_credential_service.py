"""Unit tests for src/services/credential_service.py"""

from datetime import datetime

import httpx
import pytest
import respx

from src.services.credential_service import check_credential_validity


@pytest.mark.asyncio
async def test_check_credential_validity_success():
    """Test successful credential validation with 200 response"""
    # Arrange
    account_id = "test_account_123"
    secret_key = "test_secret_key"
    mock_response = {
        "status": "success",
        "result": [
            {
                "id": 12345,
                "name": "Test Listing",
            }
        ],
    }

    # Act
    with respx.mock:
        respx.get("https://api.hostaway.com/v1/listings").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = await check_credential_validity(account_id, secret_key)

    # Assert
    assert result["valid"] is True
    assert "validated_at" in result
    assert "error" not in result

    # Verify timestamp is ISO format
    validated_at = datetime.fromisoformat(result["validated_at"])
    assert isinstance(validated_at, datetime)


@pytest.mark.asyncio
async def test_check_credential_validity_invalid_credentials():
    """Test invalid credentials with 401 response"""
    # Arrange
    account_id = "invalid_account"
    secret_key = "invalid_secret"

    # Act
    with respx.mock:
        respx.get("https://api.hostaway.com/v1/listings").mock(
            return_value=httpx.Response(401, json={"error": "Unauthorized"})
        )

        result = await check_credential_validity(account_id, secret_key)

    # Assert
    assert result["valid"] is False
    assert result["error"] == "Invalid or expired credentials"
    assert "validated_at" not in result


@pytest.mark.asyncio
async def test_check_credential_validity_unexpected_status():
    """Test handling of unexpected HTTP status codes"""
    # Arrange
    account_id = "test_account"
    secret_key = "test_secret"

    # Act
    with respx.mock:
        respx.get("https://api.hostaway.com/v1/listings").mock(
            return_value=httpx.Response(500, json={"error": "Internal Server Error"})
        )

        result = await check_credential_validity(account_id, secret_key)

    # Assert
    assert result["valid"] is False
    assert "Unexpected status: 500" in result["error"]


@pytest.mark.asyncio
async def test_check_credential_validity_forbidden():
    """Test 403 Forbidden response"""
    # Arrange
    account_id = "test_account"
    secret_key = "test_secret"

    # Act
    with respx.mock:
        respx.get("https://api.hostaway.com/v1/listings").mock(
            return_value=httpx.Response(403, json={"error": "Forbidden"})
        )

        result = await check_credential_validity(account_id, secret_key)

    # Assert
    assert result["valid"] is False
    assert "Unexpected status: 403" in result["error"]


@pytest.mark.asyncio
async def test_check_credential_validity_network_timeout():
    """Test network timeout exception handling"""
    # Arrange
    account_id = "test_account"
    secret_key = "test_secret"

    # Act
    with respx.mock:
        respx.get("https://api.hostaway.com/v1/listings").mock(
            side_effect=httpx.TimeoutException("Connection timeout")
        )

        result = await check_credential_validity(account_id, secret_key)

    # Assert
    assert result["valid"] is False
    assert "Connection timeout" in result["error"]


@pytest.mark.asyncio
async def test_check_credential_validity_network_error():
    """Test general network error handling"""
    # Arrange
    account_id = "test_account"
    secret_key = "test_secret"

    # Act
    with respx.mock:
        respx.get("https://api.hostaway.com/v1/listings").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        result = await check_credential_validity(account_id, secret_key)

    # Assert
    assert result["valid"] is False
    assert "Connection refused" in result["error"]


@pytest.mark.asyncio
async def test_check_credential_validity_headers():
    """Test that correct headers are sent in the API request"""
    # Arrange
    account_id = "test_account"
    secret_key = "test_secret_key"

    # Act & Assert
    with respx.mock as mock_router:
        route = respx.get("https://api.hostaway.com/v1/listings").mock(
            return_value=httpx.Response(200, json={"result": []})
        )

        await check_credential_validity(account_id, secret_key)

        # Verify the request was made with correct headers
        assert route.called
        request = route.calls.last.request
        assert request.headers["Authorization"] == f"Bearer {secret_key}"
        assert request.headers["Content-type"] == "application/json"


@pytest.mark.asyncio
async def test_check_credential_validity_query_params():
    """Test that correct query parameters are sent"""
    # Arrange
    account_id = "test_account"
    secret_key = "test_secret"

    # Act & Assert
    with respx.mock as mock_router:
        route = respx.get("https://api.hostaway.com/v1/listings").mock(
            return_value=httpx.Response(200, json={"result": []})
        )

        await check_credential_validity(account_id, secret_key)

        # Verify query parameters
        assert route.called
        request = route.calls.last.request
        assert "limit=1" in str(request.url)


@pytest.mark.asyncio
async def test_check_credential_validity_empty_response():
    """Test handling of empty 200 response"""
    # Arrange
    account_id = "test_account"
    secret_key = "test_secret"

    # Act
    with respx.mock:
        respx.get("https://api.hostaway.com/v1/listings").mock(
            return_value=httpx.Response(200, json={"result": []})
        )

        result = await check_credential_validity(account_id, secret_key)

    # Assert
    assert result["valid"] is True
    assert "validated_at" in result
    # Empty results still mean valid credentials


@pytest.mark.asyncio
async def test_check_credential_validity_malformed_json():
    """Test handling of malformed JSON response"""
    # Arrange
    account_id = "test_account"
    secret_key = "test_secret"

    # Act
    with respx.mock:
        respx.get("https://api.hostaway.com/v1/listings").mock(
            return_value=httpx.Response(200, text="Not JSON")
        )

        # Should still be valid - we only check status code
        result = await check_credential_validity(account_id, secret_key)

    # Assert
    assert result["valid"] is True
    assert "validated_at" in result
