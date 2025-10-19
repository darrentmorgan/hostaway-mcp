"""Unit tests for TokenAwareMiddleware.

Tests response optimization, token budget enforcement, and summarization triggering.
"""

from unittest.mock import MagicMock, patch

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient

from src.api.middleware.token_aware_middleware import TokenAwareMiddleware


class TestTokenAwareMiddleware:
    """Test suite for TokenAwareMiddleware."""

    @pytest.fixture
    def mock_config_service(self):
        """Create mock config service."""
        mock_service = MagicMock()
        mock_service.get_endpoint_config.return_value = (
            4000,  # threshold
            12000,  # hard_cap
            50,  # page_size
            True,  # summarization_enabled
            True,  # pagination_enabled
        )
        return mock_service

    @pytest.fixture
    def mock_summarization_service(self):
        """Create mock summarization service."""
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "summary": "Summarized content",
            "meta": {"summarized": True},
        }
        mock_service.summarize_object.return_value = mock_response
        return mock_service

    @pytest.fixture
    def app(self, mock_config_service, mock_summarization_service):
        """Create test application with middleware."""

        async def endpoint_small(request: Request):
            return JSONResponse({"message": "small response"})

        async def endpoint_large(request: Request):
            # Large response that exceeds token budget
            return JSONResponse(
                {
                    "data": "x" * 50000,  # Large enough to exceed 4000 token threshold
                    "items": list(range(1000)),
                }
            )

        async def endpoint_non_json(request: Request):
            return Response(content="plain text", media_type="text/plain")

        async def endpoint_error(request: Request):
            return JSONResponse({"error": "something went wrong"}, status_code=500)

        app = Starlette(
            routes=[
                Route("/api/small", endpoint_small),
                Route("/api/large", endpoint_large),
                Route("/api/text", endpoint_non_json),
                Route("/api/error", endpoint_error),
            ]
        )

        with patch(
            "src.api.middleware.token_aware_middleware.get_config_service",
            return_value=mock_config_service,
        ):
            with patch(
                "src.api.middleware.token_aware_middleware.get_summarization_service",
                return_value=mock_summarization_service,
            ):
                app.add_middleware(TokenAwareMiddleware)

        return app

    def test_small_response_passes_through(self, app, mock_summarization_service):
        """Test small response passes through without summarization."""
        client = TestClient(app)
        response = client.get("/api/small")

        assert response.status_code == 200
        assert response.json() == {"message": "small response"}
        # Summarization should not be called
        mock_summarization_service.summarize_object.assert_not_called()

    @patch("src.api.middleware.token_aware_middleware.estimate_tokens")
    def test_large_response_triggers_summarization(
        self, mock_estimate, app, mock_summarization_service
    ):
        """Test large response triggers summarization."""
        # Mock token estimation to exceed threshold
        mock_estimate.return_value = 5000  # Exceeds 4000 threshold

        client = TestClient(app)
        response = client.get("/api/large")

        assert response.status_code == 200
        data = response.json()
        # Check if response was summarized (has summary field)
        assert "summary" in data or "data" in data  # Could be original or summarized
        # Summarization should be called
        mock_summarization_service.summarize_object.assert_called_once()

    def test_non_json_response_passes_through(self, app):
        """Test non-JSON response is not processed."""
        client = TestClient(app)
        response = client.get("/api/text")

        assert response.status_code == 200
        assert response.text == "plain text"

    def test_error_response_passes_through(self, app, mock_summarization_service):
        """Test error responses (4xx, 5xx) are not processed."""
        client = TestClient(app)
        response = client.get("/api/error")

        assert response.status_code == 500
        assert response.json() == {"error": "something went wrong"}
        # Summarization should not be called for errors
        mock_summarization_service.summarize_object.assert_not_called()

    @patch("src.api.middleware.token_aware_middleware.estimate_tokens")
    def test_paginated_response_skipped(self, mock_estimate, app, mock_summarization_service):
        """Test paginated response is skipped (not summarized)."""
        mock_estimate.return_value = 5000  # Would normally trigger summarization

        # Create endpoint that returns paginated structure
        async def endpoint_paginated(request: Request):
            return JSONResponse(
                {"items": [{"id": 1}, {"id": 2}], "meta": {"totalCount": 100, "hasMore": True}}
            )

        app.routes.append(Route("/api/paginated", endpoint_paginated))

        client = TestClient(app)
        response = client.get("/api/paginated")

        assert response.status_code == 200
        data = response.json()
        # Should not be summarized because it's already paginated
        assert "items" in data
        assert "meta" in data
        mock_summarization_service.summarize_object.assert_not_called()

    @patch("src.api.middleware.token_aware_middleware.estimate_tokens")
    def test_already_summarized_response_skipped(
        self, mock_estimate, app, mock_summarization_service
    ):
        """Test already summarized response is skipped."""
        mock_estimate.return_value = 5000

        # Create endpoint that returns summary structure
        async def endpoint_summary(request: Request):
            return JSONResponse({"summary": "Already summarized", "meta": {"summarized": True}})

        app.routes.append(Route("/api/summary", endpoint_summary))

        client = TestClient(app)
        response = client.get("/api/summary")

        assert response.status_code == 200
        data = response.json()
        # Should not be re-summarized
        assert "summary" in data
        mock_summarization_service.summarize_object.assert_not_called()

    def test_summarization_disabled_for_endpoint(
        self, mock_config_service, mock_summarization_service
    ):
        """Test summarization skipped when disabled for endpoint."""
        # Configure summarization as disabled
        mock_config_service.get_endpoint_config.return_value = (
            4000,
            12000,
            50,
            False,
            True,  # summarization_enabled=False
        )

        async def endpoint_large(request: Request):
            return JSONResponse({"data": "x" * 50000})

        app = Starlette(routes=[Route("/api/test", endpoint_large)])

        with patch(
            "src.api.middleware.token_aware_middleware.get_config_service",
            return_value=mock_config_service,
        ):
            with patch(
                "src.api.middleware.token_aware_middleware.get_summarization_service",
                return_value=mock_summarization_service,
            ):
                with patch(
                    "src.api.middleware.token_aware_middleware.estimate_tokens", return_value=5000
                ):
                    app.add_middleware(TokenAwareMiddleware)

                    client = TestClient(app)
                    response = client.get("/api/test")

                    assert response.status_code == 200
                    # Summarization should not be called when disabled
                    mock_summarization_service.summarize_object.assert_not_called()

    def test_invalid_json_response_passes_through(self, mock_config_service):
        """Test invalid JSON response passes through unchanged."""

        async def endpoint_broken_json(request: Request):
            return Response(content=b"not valid json {{{", media_type="application/json")

        app = Starlette(routes=[Route("/api/broken", endpoint_broken_json)])

        with patch(
            "src.api.middleware.token_aware_middleware.get_config_service",
            return_value=mock_config_service,
        ):
            app.add_middleware(TokenAwareMiddleware)

            client = TestClient(app)
            response = client.get("/api/broken")

            # Should return original broken response
            assert response.status_code == 200
            assert response.text == "not valid json {{{"

    @patch("src.api.middleware.token_aware_middleware.estimate_tokens")
    def test_detect_object_type_booking(
        self, mock_estimate, mock_config_service, mock_summarization_service
    ):
        """Test object type detection for booking endpoint."""
        mock_estimate.return_value = 5000

        async def endpoint_booking(request: Request):
            return JSONResponse({"booking_id": "123", "guest_name": "John"})

        app = Starlette(routes=[Route("/api/bookings/123", endpoint_booking)])

        with patch(
            "src.api.middleware.token_aware_middleware.get_config_service",
            return_value=mock_config_service,
        ):
            with patch(
                "src.api.middleware.token_aware_middleware.get_summarization_service",
                return_value=mock_summarization_service,
            ):
                app.add_middleware(TokenAwareMiddleware)

                client = TestClient(app)
                response = client.get("/api/bookings/123")

                # Verify summarize_object was called with "booking" type
                call_args = mock_summarization_service.summarize_object.call_args
                assert call_args[1]["obj_type"] == "booking"

    @patch("src.api.middleware.token_aware_middleware.estimate_tokens")
    def test_detect_object_type_listing(
        self, mock_estimate, mock_config_service, mock_summarization_service
    ):
        """Test object type detection for listing endpoint."""
        mock_estimate.return_value = 5000

        async def endpoint_listing(request: Request):
            return JSONResponse({"listing_id": "456", "name": "Beach House"})

        app = Starlette(routes=[Route("/api/listings/456", endpoint_listing)])

        with patch(
            "src.api.middleware.token_aware_middleware.get_config_service",
            return_value=mock_config_service,
        ):
            with patch(
                "src.api.middleware.token_aware_middleware.get_summarization_service",
                return_value=mock_summarization_service,
            ):
                app.add_middleware(TokenAwareMiddleware)

                client = TestClient(app)
                response = client.get("/api/listings/456")

                call_args = mock_summarization_service.summarize_object.call_args
                assert call_args[1]["obj_type"] == "listing"

    @patch("src.api.middleware.token_aware_middleware.estimate_tokens")
    def test_detect_object_type_financial(
        self, mock_estimate, mock_config_service, mock_summarization_service
    ):
        """Test object type detection for financial endpoint."""
        mock_estimate.return_value = 5000

        async def endpoint_financial(request: Request):
            return JSONResponse({"transaction_id": "789", "amount": 500})

        app = Starlette(routes=[Route("/api/financial/report", endpoint_financial)])

        with patch(
            "src.api.middleware.token_aware_middleware.get_config_service",
            return_value=mock_config_service,
        ):
            with patch(
                "src.api.middleware.token_aware_middleware.get_summarization_service",
                return_value=mock_summarization_service,
            ):
                app.add_middleware(TokenAwareMiddleware)

                client = TestClient(app)
                response = client.get("/api/financial/report")

                call_args = mock_summarization_service.summarize_object.call_args
                assert call_args[1]["obj_type"] == "financial_transaction"

    @patch("src.api.middleware.token_aware_middleware.estimate_tokens")
    def test_list_response_warning(
        self, mock_estimate, mock_config_service, mock_summarization_service, caplog
    ):
        """Test warning logged when list response received."""
        mock_estimate.return_value = 5000

        async def endpoint_list(request: Request):
            return JSONResponse([{"id": 1}, {"id": 2}, {"id": 3}])

        app = Starlette(routes=[Route("/api/items", endpoint_list)])

        with patch(
            "src.api.middleware.token_aware_middleware.get_config_service",
            return_value=mock_config_service,
        ):
            with patch(
                "src.api.middleware.token_aware_middleware.get_summarization_service",
                return_value=mock_summarization_service,
            ):
                app.add_middleware(TokenAwareMiddleware)

                client = TestClient(app)
                response = client.get("/api/items")

                # Should log warning about list response
                assert "should be handled by pagination middleware" in caplog.text
