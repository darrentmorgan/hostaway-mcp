"""Unit tests for src/api/middleware/usage_tracking.py"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, Response

from src.api.middleware.usage_tracking import UsageTrackingMiddleware

# === Test _extract_tool_name ===


def test_extract_tool_name_valid_path():
    """Test tool name extraction from valid API path"""
    # Arrange
    path = "/api/v1/properties/123"

    # Act
    tool_name = UsageTrackingMiddleware._extract_tool_name(path)

    # Assert
    assert tool_name == "properties"


def test_extract_tool_name_various_resources():
    """Test tool name extraction for different resource types"""
    # Arrange & Act & Assert
    assert UsageTrackingMiddleware._extract_tool_name("/api/v1/reservations") == "reservations"
    assert UsageTrackingMiddleware._extract_tool_name("/api/v1/listings/456") == "listings"
    assert UsageTrackingMiddleware._extract_tool_name("/api/v1/webhooks/test") == "webhooks"


def test_extract_tool_name_with_trailing_slash():
    """Test tool name extraction with trailing slash"""
    # Arrange
    path = "/api/v1/properties/"

    # Act
    tool_name = UsageTrackingMiddleware._extract_tool_name(path)

    # Assert
    assert tool_name == "properties"


def test_extract_tool_name_malformed_path():
    """Test tool name extraction from malformed path returns 'unknown'"""
    # Arrange & Act & Assert
    assert UsageTrackingMiddleware._extract_tool_name("/api") == "unknown"
    assert UsageTrackingMiddleware._extract_tool_name("/api/v1") == "unknown"
    assert UsageTrackingMiddleware._extract_tool_name("/") == "unknown"
    assert UsageTrackingMiddleware._extract_tool_name("") == "unknown"


# === Test _track_usage ===


@pytest.mark.asyncio
@patch("src.api.middleware.usage_tracking.get_supabase_client")
async def test_track_usage_success(mock_get_client):
    """Test successful usage tracking"""
    # Arrange
    mock_supabase = MagicMock()
    mock_supabase.rpc.return_value = mock_supabase
    mock_supabase.execute.return_value = MagicMock(data={"success": True})
    mock_get_client.return_value = mock_supabase

    organization_id = "org-123"
    tool_name = "properties"

    # Act
    await UsageTrackingMiddleware._track_usage(
        organization_id=organization_id,
        tool_name=tool_name,
    )

    # Assert
    mock_supabase.rpc.assert_called_once_with(
        "increment_usage_metrics",
        {
            "p_organization_id": organization_id,
            "p_tool_name": tool_name,
        },
    )
    mock_supabase.execute.assert_called_once()


@pytest.mark.asyncio
@patch("src.api.middleware.usage_tracking.get_supabase_client")
async def test_track_usage_no_data_returned(mock_get_client, capsys):
    """Test usage tracking when RPC returns no data (logs warning)"""
    # Arrange
    mock_supabase = MagicMock()
    mock_supabase.rpc.return_value = mock_supabase
    mock_supabase.execute.return_value = MagicMock(data=None)
    mock_get_client.return_value = mock_supabase

    organization_id = "org-456"
    tool_name = "listings"

    # Act
    await UsageTrackingMiddleware._track_usage(
        organization_id=organization_id,
        tool_name=tool_name,
    )

    # Assert
    captured = capsys.readouterr()
    assert "Warning: Usage tracking returned no data" in captured.out
    assert organization_id in captured.out


@pytest.mark.asyncio
@patch("src.api.middleware.usage_tracking.get_supabase_client")
async def test_track_usage_rpc_failure(mock_get_client, capsys):
    """Test usage tracking handles RPC failure gracefully"""
    # Arrange
    mock_supabase = MagicMock()
    mock_supabase.rpc.return_value = mock_supabase
    mock_supabase.execute.side_effect = Exception("Database connection failed")
    mock_get_client.return_value = mock_supabase

    organization_id = "org-789"
    tool_name = "webhooks"

    # Act - should not raise exception
    await UsageTrackingMiddleware._track_usage(
        organization_id=organization_id,
        tool_name=tool_name,
    )

    # Assert - error logged but not propagated
    captured = capsys.readouterr()
    assert "Failed to track usage" in captured.out
    assert organization_id in captured.out


@pytest.mark.asyncio
@patch("src.api.middleware.usage_tracking.get_supabase_client")
async def test_track_usage_multiple_tools(mock_get_client):
    """Test tracking multiple different tools for same organization"""
    # Arrange
    mock_supabase = MagicMock()
    mock_supabase.rpc.return_value = mock_supabase
    mock_supabase.execute.return_value = MagicMock(data={"success": True})
    mock_get_client.return_value = mock_supabase

    organization_id = "org-multi"

    # Act
    await UsageTrackingMiddleware._track_usage(organization_id, "properties")
    await UsageTrackingMiddleware._track_usage(organization_id, "reservations")
    await UsageTrackingMiddleware._track_usage(organization_id, "listings")

    # Assert
    assert mock_supabase.rpc.call_count == 3
    calls = list(mock_supabase.rpc.call_args_list)

    assert calls[0][0][1]["p_tool_name"] == "properties"
    assert calls[1][0][1]["p_tool_name"] == "reservations"
    assert calls[2][0][1]["p_tool_name"] == "listings"


# === Test dispatch method ===


@pytest.mark.asyncio
async def test_dispatch_tracks_api_routes():
    """Test middleware tracks /api/* routes"""
    # Arrange
    middleware = UsageTrackingMiddleware(app=MagicMock())

    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/api/v1/properties/123"
    mock_request.state.organization_id = "org-123"

    mock_response = Response(content=b"test", status_code=200)
    mock_call_next = AsyncMock(return_value=mock_response)

    # Act
    with patch.object(
        UsageTrackingMiddleware, "_track_usage", new_callable=AsyncMock
    ) as mock_track:
        response = await middleware.dispatch(mock_request, mock_call_next)

    # Assert
    assert response == mock_response
    mock_call_next.assert_called_once_with(mock_request)
    mock_track.assert_called_once_with(
        organization_id="org-123",
        tool_name="properties",
    )


@pytest.mark.asyncio
async def test_dispatch_skips_non_api_routes():
    """Test middleware skips tracking for non-API routes"""
    # Arrange
    middleware = UsageTrackingMiddleware(app=MagicMock())

    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/health"

    mock_response = Response(content=b"ok", status_code=200)
    mock_call_next = AsyncMock(return_value=mock_response)

    # Act
    with patch.object(
        UsageTrackingMiddleware, "_track_usage", new_callable=AsyncMock
    ) as mock_track:
        response = await middleware.dispatch(mock_request, mock_call_next)

    # Assert
    assert response == mock_response
    mock_call_next.assert_called_once_with(mock_request)
    mock_track.assert_not_called()  # Should not track non-API routes


@pytest.mark.asyncio
async def test_dispatch_skips_tracking_without_organization_id():
    """Test middleware skips tracking when organization_id is missing"""
    # Arrange
    middleware = UsageTrackingMiddleware(app=MagicMock())

    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/api/v1/properties"
    mock_request.state.organization_id = None  # No org_id

    mock_response = Response(content=b"test", status_code=200)
    mock_call_next = AsyncMock(return_value=mock_response)

    # Act
    with patch.object(
        UsageTrackingMiddleware, "_track_usage", new_callable=AsyncMock
    ) as mock_track:
        response = await middleware.dispatch(mock_request, mock_call_next)

    # Assert
    assert response == mock_response
    mock_track.assert_not_called()  # Should not track without org_id


@pytest.mark.asyncio
async def test_dispatch_continues_on_tracking_failure(capsys):
    """Test middleware doesn't fail request if tracking fails"""
    # Arrange
    middleware = UsageTrackingMiddleware(app=MagicMock())

    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/api/v1/listings"
    mock_request.state.organization_id = "org-fail"

    mock_response = Response(content=b"success", status_code=200)
    mock_call_next = AsyncMock(return_value=mock_response)

    # Act
    with patch.object(
        UsageTrackingMiddleware, "_track_usage", new_callable=AsyncMock
    ) as mock_track:
        mock_track.side_effect = Exception("Tracking error")

        response = await middleware.dispatch(mock_request, mock_call_next)

    # Assert
    assert response == mock_response  # Request succeeds despite tracking failure
    captured = capsys.readouterr()
    assert "Usage tracking error" in captured.out


@pytest.mark.asyncio
async def test_dispatch_multiple_requests_same_org():
    """Test multiple requests from same organization"""
    # Arrange
    middleware = UsageTrackingMiddleware(app=MagicMock())

    organization_id = "org-repeat"

    mock_response = Response(content=b"test", status_code=200)
    mock_call_next = AsyncMock(return_value=mock_response)

    # Act
    with patch.object(
        UsageTrackingMiddleware, "_track_usage", new_callable=AsyncMock
    ) as mock_track:
        # Request 1
        mock_request1 = MagicMock(spec=Request)
        mock_request1.url.path = "/api/v1/properties"
        mock_request1.state.organization_id = organization_id
        await middleware.dispatch(mock_request1, mock_call_next)

        # Request 2
        mock_request2 = MagicMock(spec=Request)
        mock_request2.url.path = "/api/v1/reservations"
        mock_request2.state.organization_id = organization_id
        await middleware.dispatch(mock_request2, mock_call_next)

    # Assert
    assert mock_track.call_count == 2
    calls = list(mock_track.call_args_list)

    assert calls[0][1]["organization_id"] == organization_id
    assert calls[0][1]["tool_name"] == "properties"

    assert calls[1][1]["organization_id"] == organization_id
    assert calls[1][1]["tool_name"] == "reservations"


@pytest.mark.asyncio
async def test_dispatch_different_organizations():
    """Test requests from different organizations are tracked separately"""
    # Arrange
    middleware = UsageTrackingMiddleware(app=MagicMock())

    mock_response = Response(content=b"test", status_code=200)
    mock_call_next = AsyncMock(return_value=mock_response)

    # Act
    with patch.object(
        UsageTrackingMiddleware, "_track_usage", new_callable=AsyncMock
    ) as mock_track:
        # Org 1
        mock_request1 = MagicMock(spec=Request)
        mock_request1.url.path = "/api/v1/properties"
        mock_request1.state.organization_id = "org-1"
        await middleware.dispatch(mock_request1, mock_call_next)

        # Org 2
        mock_request2 = MagicMock(spec=Request)
        mock_request2.url.path = "/api/v1/properties"
        mock_request2.state.organization_id = "org-2"
        await middleware.dispatch(mock_request2, mock_call_next)

    # Assert
    assert mock_track.call_count == 2
    calls = list(mock_track.call_args_list)

    assert calls[0][1]["organization_id"] == "org-1"
    assert calls[1][1]["organization_id"] == "org-2"


@pytest.mark.asyncio
async def test_dispatch_with_error_response():
    """Test middleware tracks usage even when API returns error"""
    # Arrange
    middleware = UsageTrackingMiddleware(app=MagicMock())

    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/api/v1/properties/999"
    mock_request.state.organization_id = "org-error"

    # Simulate error response (404)
    mock_error_response = Response(content=b"Not Found", status_code=404)
    mock_call_next = AsyncMock(return_value=mock_error_response)

    # Act
    with patch.object(
        UsageTrackingMiddleware, "_track_usage", new_callable=AsyncMock
    ) as mock_track:
        response = await middleware.dispatch(mock_request, mock_call_next)

    # Assert
    assert response.status_code == 404
    mock_track.assert_called_once()  # Should still track failed requests


@pytest.mark.asyncio
async def test_dispatch_request_state_without_org_attribute():
    """Test middleware handles request.state without organization_id attribute"""
    # Arrange
    middleware = UsageTrackingMiddleware(app=MagicMock())

    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/api/v1/properties"
    # Mock state without organization_id attribute
    mock_request.state = MagicMock()
    del mock_request.state.organization_id  # Ensure attribute doesn't exist

    mock_response = Response(content=b"test", status_code=200)
    mock_call_next = AsyncMock(return_value=mock_response)

    # Act
    with patch.object(
        UsageTrackingMiddleware, "_track_usage", new_callable=AsyncMock
    ) as mock_track:
        response = await middleware.dispatch(mock_request, mock_call_next)

    # Assert
    assert response == mock_response
    mock_track.assert_not_called()  # Should not track without org_id
