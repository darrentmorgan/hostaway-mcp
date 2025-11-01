#!/usr/bin/env python3
"""
Native MCP stdio server for Hostaway API.

Provides MCP tools via stdio protocol for Claude Desktop.
Connects to remote Hostaway MCP server with API key authentication.
"""

import asyncio
import json
import os
import re
from typing import Any

import httpx
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp.server import Server

# Create MCP server
app = Server("hostaway-mcp")

# HTTP client for API calls - use remote server
BASE_URL = os.getenv("REMOTE_MCP_URL", "http://72.60.233.157:8080")
API_KEY = os.getenv("REMOTE_MCP_API_KEY", "")
CHARACTER_LIMIT = 25000  # MCP best practice: 25,000 character limit


def truncate_response(text: str, limit: int = CHARACTER_LIMIT) -> str:
    """Truncate response text if it exceeds character limit."""
    if len(text) <= limit:
        return text

    truncate_at = int(limit * 0.8)
    truncated_text = text[:truncate_at]

    guidance_message = f"""

---

⚠️ **Response Truncated**

Original: {len(text):,} chars, truncated to {len(truncated_text):,} chars.

**To see more:**
1. Reduce limit parameter
2. Add filters
3. Use pagination

**Need specific data?** Use detail endpoints for individual items.
"""

    return truncated_text + guidance_message


def create_error_response(message: str, is_error: bool = True) -> list[TextContent]:
    """Create a standardized error response.

    Args:
        message: Error message with actionable guidance
        is_error: Whether this is an error (True) or warning (False)

    Returns:
        List of TextContent for MCP response
    """
    # Note: Python MCP SDK doesn't support isError flag in TextContent
    # So we prefix error messages clearly
    prefix = "ERROR: " if is_error else "WARNING: "
    return [TextContent(type="text", text=f"{prefix}{message}")]


def create_http_error_response(error: httpx.HTTPError, context: str) -> list[TextContent]:
    """Create actionable error response from HTTP error.

    Args:
        error: HTTP error from httpx
        context: Context about what operation failed

    Returns:
        List of TextContent with actionable guidance
    """
    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code

        if status_code == 401:
            return create_error_response(
                f"Authentication failed while {context}. "
                f"The REMOTE_MCP_API_KEY environment variable may be invalid or expired. "
                f"Contact your administrator to verify API key configuration."
            )
        if status_code == 403:
            return create_error_response(
                f"Permission denied while {context}. "
                f"Your API key does not have permission to access this resource. "
                f"Contact your Hostaway administrator to request access."
            )
        if status_code == 404:
            return create_error_response(
                f"Resource not found while {context}. "
                f"The requested property or booking may not exist. "
                f"Use hostaway_list_properties or hostaway_search_bookings to find valid IDs."
            )
        if status_code == 429:
            return create_error_response(
                f"Rate limit exceeded while {context}. "
                f"Too many requests in a short time. "
                f"Wait 10 seconds and try again, or reduce the 'limit' parameter to fetch fewer results."
            )
        if status_code >= 500:
            return create_error_response(
                f"Server error while {context} (HTTP {status_code}). "
                f"The Hostaway API is experiencing issues. "
                f"Wait a few minutes and try again. If the problem persists, contact Hostaway support."
            )
        return create_error_response(
            f"HTTP {status_code} error while {context}: {error.response.text}"
        )

    if isinstance(error, httpx.TimeoutException):
        return create_error_response(
            f"Request timeout while {context}. "
            f"The operation took longer than 30 seconds. "
            f"Try reducing the 'limit' parameter or adding date filters to narrow the search."
        )

    if isinstance(error, httpx.ConnectError):
        return create_error_response(
            f"Connection error while {context}. "
            f"Cannot reach the Hostaway MCP server at {BASE_URL}. "
            f"Check that REMOTE_MCP_URL is correctly configured and the server is running."
        )

    return create_error_response(
        f"Network error while {context}: {error!s}. "
        f"Check your internet connection and try again."
    )


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Hostaway API tools."""
    return [
        Tool(
            name="hostaway_list_properties",
            description="""List all Hostaway properties with cursor-based pagination.

Returns summarized property information optimized for AI context windows (ID, name, location, bedrooms, status).

**When to use:**
- Browsing all available properties
- Finding properties by specific criteria
- Building property catalogs or inventories

**When NOT to use:**
- Getting complete details for a single property → Use hostaway_get_property_details instead
- Checking availability for specific dates → Use hostaway_check_availability instead""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max results (default 10)"},
                    "minimum": 1,
                    "maximum": 200,
                    "default": 10,
                    "offset": {"type": "integer", "description": "Offset for pagination"},
                },
            },
            annotations={
                "title": "List Properties",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True,
            },
        ),
        Tool(
            name="hostaway_get_property_details",
            description="""Get detailed information about a specific Hostaway property.

Returns complete property data including amenities, pricing, policies, and calendar information.

**When to use:**
- Need full property specifications (amenities, policies, etc.)
- Preparing detailed property descriptions
- Reviewing complete property configuration

**When NOT to use:**
- Just need basic property info → Use hostaway_list_properties instead
- Checking availability → Use hostaway_check_availability instead""",
            inputSchema={
                "type": "object",
                "properties": {
                    "listing_id": {
                        "type": "integer",
                        "description": "Property listing ID",
                    },
                },
                "required": ["listing_id"],
            },
            annotations={
                "title": "Get Property Details",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True,
            },
        ),
        Tool(
            name="hostaway_check_availability",
            description="""Check if a Hostaway property is available for specific dates.

Returns availability status and pricing for the requested date range.

**When to use:**
- Checking if property is available for booking
- Getting pricing for specific dates
- Verifying date range before creating reservation

**Required inputs:**
- listing_id: Property ID from hostaway_list_properties
- start_date: Check-in date (YYYY-MM-DD format)
- end_date: Check-out date (YYYY-MM-DD format)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "listing_id": {"type": "integer", "description": "Property ID"},
                    "start_date": {
                        "format": "date",
                        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD)",
                    },
                    "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                },
                "required": ["listing_id", "start_date", "end_date"],
            },
            annotations={
                "title": "Check Availability",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True,
            },
        ),
        Tool(
            name="hostaway_search_bookings",
            description="""Search and filter Hostaway bookings with pagination.

Returns booking summaries matching specified criteria (date range, status, property).

**When to use:**
- Finding bookings by date range
- Filtering bookings by status (confirmed, cancelled, etc.)
- Getting recent bookings for a property

**Common filters:**
- status: confirmed, cancelled, inquiry, reserved
- start_date/end_date: Filter by booking dates
- limit/offset: Control pagination""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max results"},
                    "minimum": 1,
                    "maximum": 200,
                    "default": 10,
                    "offset": {"type": "integer", "description": "Offset"},
                    "status": {"type": "string", "description": "Booking status"},
                    "start_date": {"type": "string", "description": "Filter by start date"},
                    "format": "date",
                    "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                    "end_date": {"type": "string", "description": "Filter by end date"},
                },
            },
            annotations={
                "title": "Search Bookings",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True,
            },
        ),
        Tool(
            name="hostaway_get_booking_details",
            description="""Get complete details for a specific Hostaway booking.

Returns full booking information including guest details, pricing, payments, and status.

**When to use:**
- Need complete booking information
- Reviewing payment and pricing details
- Accessing guest communication history

**Required inputs:**
- booking_id: Booking ID from hostaway_search_bookings""",
            inputSchema={
                "type": "object",
                "properties": {
                    "booking_id": {"type": "integer", "description": "Booking ID"},
                },
                "required": ["booking_id"],
            },
            annotations={
                "title": "Get Booking Details",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True,
            },
        ),
        Tool(
            name="hostaway_get_guest_info",
            description="""Get guest contact and personal information for a Hostaway booking.

Returns guest name, email, phone, and other contact details associated with the booking.

**When to use:**
- Contacting guests about their reservation
- Verifying guest information
- Preparing check-in instructions

**Required inputs:**
- booking_id: Booking ID from hostaway_search_bookings""",
            inputSchema={
                "type": "object",
                "properties": {
                    "booking_id": {"type": "integer", "description": "Booking ID"},
                },
                "required": ["booking_id"],
            },
            annotations={
                "title": "Get Guest Info",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True,
            },
        ),
        Tool(
            name="hostaway_get_financial_reports",
            description="""Get financial reports with revenue and expense breakdown for Hostaway properties.

Returns detailed financial data including revenue, expenses, and net income for specified date range.

**When to use:**
- Generating financial summaries
- Analyzing property performance
- Preparing accounting reports

**Required inputs:**
- start_date: Report start date (YYYY-MM-DD)
- end_date: Report end date (YYYY-MM-DD)

**Optional filters:**
- listing_id: Limit report to specific property""",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "format": "date",
                        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD)",
                    },
                    "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                    "listing_id": {"type": "integer", "description": "Filter by property"},
                },
                "required": ["start_date", "end_date"],
            },
            annotations={
                "title": "Get Financial Reports",
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": False,
                "openWorldHint": True,
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:  # noqa: PLR0912, PLR0915
    """Execute a tool by calling the HTTP API."""
    # Add API key to headers if configured
    headers = {"X-API-Key": API_KEY} if API_KEY else {}

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        try:
            if name == "hostaway_list_properties":
                params = {k: v for k, v in arguments.items() if v is not None}
                # Use summary=true to prevent context window overflow
                params["summary"] = "true"
                response = await client.get(f"{BASE_URL}/api/listings", params=params)
                response.raise_for_status()
                data = response.json()
                response_text = json.dumps(data, indent=2)
                return [TextContent(type="text", text=truncate_response(response_text))]

            if name == "hostaway_get_property_details":
                listing_id = arguments["listing_id"]

                # NEW: Add input validation
                if not isinstance(listing_id, int) or listing_id <= 0:
                    return create_error_response(
                        f"Invalid listing_id: {listing_id}. "
                        f"Property ID must be a positive integer. "
                        f"Use hostaway_list_properties to find valid property IDs."
                    )

                response = await client.get(f"{BASE_URL}/api/listings/{listing_id}")
                response.raise_for_status()
                data = response.json()
                response_text = json.dumps(data, indent=2)
                return [TextContent(type="text", text=truncate_response(response_text))]

            if name == "hostaway_check_availability":
                listing_id = arguments["listing_id"]
                start_date = arguments["start_date"]
                end_date = arguments["end_date"]

                # NEW: Add input validation
                if not isinstance(listing_id, int) or listing_id <= 0:
                    return create_error_response(
                        f"Invalid listing_id: {listing_id}. Must be a positive integer."
                    )

                # Validate date format (basic check)
                date_pattern = r"^\d{4}-\d{2}-\d{2}$"
                if not re.match(date_pattern, start_date):
                    return create_error_response(
                        f"Invalid start_date format: {start_date}. "
                        f"Must be YYYY-MM-DD (e.g., 2025-11-01)."
                    )
                if not re.match(date_pattern, end_date):
                    return create_error_response(
                        f"Invalid end_date format: {end_date}. "
                        f"Must be YYYY-MM-DD (e.g., 2025-11-30)."
                    )

                params = {"start_date": start_date, "end_date": end_date}
                response = await client.get(
                    f"{BASE_URL}/api/listings/{listing_id}/calendar",
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
                response_text = json.dumps(data, indent=2)
                return [TextContent(type="text", text=truncate_response(response_text))]

            if name == "hostaway_search_bookings":
                params = {k: v for k, v in arguments.items() if v is not None}
                # Use summary=true to prevent context window overflow
                params["summary"] = "true"
                response = await client.get(f"{BASE_URL}/api/reservations", params=params)
                response.raise_for_status()
                data = response.json()
                response_text = json.dumps(data, indent=2)
                return [TextContent(type="text", text=truncate_response(response_text))]

            if name == "hostaway_get_booking_details":
                booking_id = arguments["booking_id"]

                # NEW: Add input validation
                if not isinstance(booking_id, int) or booking_id <= 0:
                    return create_error_response(
                        f"Invalid booking_id: {booking_id}. "
                        f"Booking ID must be a positive integer. "
                        f"Use hostaway_search_bookings to find valid booking IDs."
                    )

                response = await client.get(f"{BASE_URL}/api/reservations/{booking_id}")
                response.raise_for_status()
                data = response.json()
                response_text = json.dumps(data, indent=2)
                return [TextContent(type="text", text=truncate_response(response_text))]

            if name == "hostaway_get_guest_info":
                booking_id = arguments["booking_id"]

                # NEW: Add input validation
                if not isinstance(booking_id, int) or booking_id <= 0:
                    return create_error_response(
                        f"Invalid booking_id: {booking_id}. Must be a positive integer."
                    )

                response = await client.get(f"{BASE_URL}/api/reservations/{booking_id}/guest")
                response.raise_for_status()
                data = response.json()
                response_text = json.dumps(data, indent=2)
                return [TextContent(type="text", text=truncate_response(response_text))]

            if name == "hostaway_get_financial_reports":
                start_date = arguments["start_date"]
                end_date = arguments["end_date"]

                # NEW: Add date validation
                date_pattern = r"^\d{4}-\d{2}-\d{2}$"
                if not re.match(date_pattern, start_date):
                    return create_error_response(
                        f"Invalid start_date format: {start_date}. Must be YYYY-MM-DD."
                    )
                if not re.match(date_pattern, end_date):
                    return create_error_response(
                        f"Invalid end_date format: {end_date}. Must be YYYY-MM-DD."
                    )

                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{BASE_URL}/api/financialReports", params=params)
                response.raise_for_status()
                data = response.json()
                response_text = json.dumps(data, indent=2)
                return [TextContent(type="text", text=truncate_response(response_text))]

            return create_error_response(
                f"Unknown tool: {name}. "
                f"Available tools: hostaway_list_properties, hostaway_get_property_details, "
                f"hostaway_check_availability, hostaway_search_bookings, "
                f"hostaway_get_booking_details, hostaway_get_guest_info, "
                f"hostaway_get_financial_reports"
            )

        except httpx.HTTPError as e:
            # NEW: Use actionable error messages
            return create_http_error_response(e, f"calling {name}")

        except KeyError as e:
            # NEW: Handle missing required parameters
            return create_error_response(
                f"Missing required parameter: {e}. "
                f"Check the tool's inputSchema for required fields."
            )

        except Exception as e:
            # NEW: Generic fallback with context
            return create_error_response(
                f"Unexpected error while calling {name}: {e!s}. "
                f"Please try again or contact support if the problem persists."
            )


async def main() -> None:
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
