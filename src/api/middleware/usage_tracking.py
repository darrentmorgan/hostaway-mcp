"""Usage metrics tracking middleware for MCP API requests.

Tracks each MCP tool invocation and updates usage_metrics table for billing
and analytics. Logs API requests, tool names, and response status for audit trail.
"""

import time
from collections.abc import Callable
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.services.supabase_client import get_supabase_client


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track API usage metrics for each organization.

    Logs each MCP API request to usage_metrics table with:
    - Total API request count (incremented per request)
    - Unique tools used (array of tool names)
    - Request timestamp and response status

    Only tracks requests to /api/* endpoints (MCP tools).
    Requires X-API-Key header with valid organization context.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track API usage for MCP tool invocations.

        Args:
            request: FastAPI request object
            call_next: Next middleware/route handler

        Returns:
            Response from the next handler
        """
        # Only track /api/* routes (MCP endpoints)
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        # Start timing
        start_time = time.time()

        # Get organization_id from request state (set by get_organization_context dependency)
        organization_id = getattr(request.state, "organization_id", None)

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Track usage if organization is identified
        if organization_id:
            try:
                await self._track_usage(
                    organization_id=organization_id,
                    tool_name=self._extract_tool_name(request.url.path),
                )
            except Exception as e:
                # Don't fail the request if tracking fails
                print(f"Usage tracking error: {e}")

        return response

    @staticmethod
    def _extract_tool_name(path: str) -> str:
        """Extract MCP tool name from API path.

        Args:
            path: URL path like /api/v1/properties/123

        Returns:
            Tool name like 'properties'
        """
        parts = path.strip("/").split("/")
        # Path format: /api/v1/resource_name/...
        if len(parts) >= 3:
            return parts[2]  # Extract resource name
        return "unknown"

    @staticmethod
    async def _track_usage(
        organization_id: str,
        tool_name: str,
    ) -> None:
        """Update usage metrics in database.

        Uses increment_usage_metrics RPC function to atomically:
        1. Increment total_api_requests counter
        2. Add tool_name to unique_tools_used array (if not exists)
        3. Update month_year for current billing period

        Args:
            organization_id: UUID of the organization
            tool_name: Name of the MCP tool invoked
        """
        try:
            supabase = get_supabase_client()

            # Calculate current month in YYYY-MM format
            month_year = datetime.now().strftime("%Y-%m")

            # Debug logging
            print(
                f"Tracking usage - org: {organization_id}, month: {month_year}, tool: {tool_name}"
            )

            # Call RPC function to increment usage metrics
            # Parameters must match database function signature: org_id, month, tool
            result = supabase.rpc(
                "increment_usage_metrics",
                {
                    "org_id": organization_id,
                    "month": month_year,
                    "tool": tool_name,
                },
            ).execute()

            if result.data:
                print(f"Usage tracked successfully for org {organization_id}")
            else:
                print(f"Warning: Usage tracking returned no data for org {organization_id}")

        except Exception as e:
            # Log error but don't propagate (don't fail API requests due to tracking)
            print(f"Failed to track usage for org {organization_id}: {e}")
