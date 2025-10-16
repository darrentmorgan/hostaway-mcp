"""Token-aware middleware for response optimization.

Intercepts responses and applies pagination/summarization based on token budget.
Integrates all context protection services for automated response shaping.
"""

import json
import logging
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.models.token_budget import TokenBudget
from src.services.config_service import get_config_service
from src.services.summarization_service import get_summarization_service
from src.utils.token_estimator import estimate_tokens

logger = logging.getLogger(__name__)


class TokenAwareMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic response optimization.

    Monitors response token usage and applies summarization when needed.
    Works in conjunction with pagination middleware for list endpoints.
    """

    def __init__(self, app: Any) -> None:
        """Initialize middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.config_service = get_config_service()
        self.summarization_service = get_summarization_service()

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request and optimize response if needed.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain

        Returns:
            Potentially optimized HTTP response
        """
        # Get response from endpoint
        response = await call_next(request)

        # Only process JSON responses
        if not self._is_json_response(response):
            return response

        # Skip if not a successful response
        if response.status_code >= 400:
            return response

        # Get endpoint configuration
        endpoint_path = request.url.path
        (
            threshold,
            hard_cap,
            _,
            summarization_enabled,
            _,
        ) = self.config_service.get_endpoint_config(endpoint_path)

        # Skip if summarization disabled for this endpoint
        if not summarization_enabled:
            return response

        # Read response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        # Parse JSON
        try:
            response_data = json.loads(response_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Return original response if not parseable
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        # Skip if already paginated (has "items" and "meta")
        if self._is_paginated_response(response_data):
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        # Skip if already summarized (has "summary" and "meta")
        if self._is_summary_response(response_data):
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        # Estimate tokens
        estimated_tokens = estimate_tokens(response_body.decode("utf-8"))

        # Create token budget
        budget = TokenBudget(
            threshold=threshold,
            hard_cap=hard_cap,
            estimated_tokens=estimated_tokens,
        )

        # Check if summarization needed
        if not budget.summary_mode:
            # Within budget, return original response
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        # Apply summarization
        logger.info(
            f"Response exceeds token budget ({estimated_tokens} > {threshold}), "
            f"applying summarization for {endpoint_path}"
        )

        summarized_data = self._summarize_response(
            response_data=response_data,
            endpoint_path=endpoint_path,
        )

        # Return summarized response
        return JSONResponse(
            content=summarized_data,
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    def _is_json_response(self, response: Response) -> bool:
        """Check if response is JSON.

        Args:
            response: HTTP response

        Returns:
            True if response is JSON
        """
        content_type = response.headers.get("content-type", "")
        return "application/json" in content_type

    def _is_paginated_response(self, data: Any) -> bool:
        """Check if response is already paginated.

        Args:
            data: Response data

        Returns:
            True if response has pagination structure
        """
        if not isinstance(data, dict):
            return False

        return "items" in data and "meta" in data

    def _is_summary_response(self, data: Any) -> bool:
        """Check if response is already summarized.

        Args:
            data: Response data

        Returns:
            True if response has summary structure
        """
        if not isinstance(data, dict):
            return False

        return "summary" in data and "meta" in data

    def _summarize_response(
        self,
        response_data: Any,
        endpoint_path: str,
    ) -> dict[str, Any]:
        """Summarize response data.

        Args:
            response_data: Original response data
            endpoint_path: API endpoint path

        Returns:
            Summarized response data
        """
        # Detect object type from endpoint
        obj_type = self._detect_object_type(endpoint_path)

        # If single object, summarize it
        if isinstance(response_data, dict):
            summary_response = self.summarization_service.summarize_object(
                obj=response_data,
                obj_type=obj_type,
                endpoint=endpoint_path,
            )
            return summary_response.model_dump()

        # If list, this should have been handled by pagination middleware
        # Return as-is (shouldn't reach here in normal operation)
        logger.warning(
            f"Token-aware middleware received list response for {endpoint_path}, "
            "should be handled by pagination middleware"
        )
        return response_data

    def _detect_object_type(self, endpoint_path: str) -> str:
        """Detect object type from endpoint path.

        Args:
            endpoint_path: API endpoint path

        Returns:
            Object type (e.g., "booking", "listing")
        """
        # Simple heuristic based on path segments
        if "booking" in endpoint_path:
            return "booking"
        elif "listing" in endpoint_path:
            return "listing"
        elif "financial" in endpoint_path or "transaction" in endpoint_path:
            return "financial_transaction"
        elif "conversation" in endpoint_path or "message" in endpoint_path:
            return "conversation"
        elif "review" in endpoint_path:
            return "review"
        else:
            return "unknown"
