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


# Markdown formatting functions
def format_property_markdown(property_data: dict) -> str:
    """Format a single property as Markdown.

    Args:
        property_data: Property dict from API

    Returns:
        Markdown-formatted property information
    """
    prop_id = property_data.get("id", "N/A")
    name = property_data.get("name", "Unnamed Property")
    city = property_data.get("city", "N/A")
    country = property_data.get("country", "N/A")
    bedrooms = property_data.get("bedrooms", 0)
    status = property_data.get("status", "unknown")

    return f"""### {name}
**ID**: {prop_id}
**Location**: {city}, {country}
**Bedrooms**: {bedrooms}
**Status**: {status}
"""


def format_properties_list_markdown(data: dict) -> str:
    """Format properties list response as Markdown.

    Args:
        data: API response with items and pagination metadata

    Returns:
        Markdown-formatted properties list
    """
    items = data.get("items", [])
    meta = data.get("meta", {})

    if not items:
        return "No properties found."

    output = f"# Properties ({len(items)} results)\n\n"

    for item in items:
        output += format_property_markdown(item)
        output += "\n---\n\n"

    # Add pagination info
    if meta.get("hasMore"):
        output += (
            f"**More results available** - Use nextCursor: `{data.get('nextCursor', 'N/A')}`\n"
        )

    if meta.get("note"):
        output += f"\n*{meta['note']}*\n"

    return output


def format_booking_markdown(booking_data: dict) -> str:
    """Format a single booking as Markdown.

    Args:
        booking_data: Booking dict from API

    Returns:
        Markdown-formatted booking information
    """
    booking_id = booking_data.get("id", "N/A")
    guest_name = booking_data.get("guestName", "Unknown Guest")
    check_in = booking_data.get("checkIn", "N/A")
    check_out = booking_data.get("checkOut", "N/A")
    listing_id = booking_data.get("listingId", "N/A")
    status = booking_data.get("status", "unknown")
    total_price = booking_data.get("totalPrice", 0)

    return f"""### Booking #{booking_id}
**Guest**: {guest_name}
**Property**: #{listing_id}
**Check-in**: {check_in}
**Check-out**: {check_out}
**Status**: {status}
**Total Price**: ${total_price:,.2f}
"""


def format_bookings_list_markdown(data: dict) -> str:
    """Format bookings list response as Markdown.

    Args:
        data: API response with items and pagination metadata

    Returns:
        Markdown-formatted bookings list
    """
    items = data.get("items", [])
    meta = data.get("meta", {})

    if not items:
        return "No bookings found."

    output = f"# Bookings ({len(items)} results)\n\n"

    for item in items:
        output += format_booking_markdown(item)
        output += "\n---\n\n"

    # Add pagination info
    if meta.get("hasMore"):
        output += (
            f"**More results available** - Use nextCursor: `{data.get('nextCursor', 'N/A')}`\n"
        )

    if meta.get("note"):
        output += f"\n*{meta['note']}*\n"

    return output


def format_property_details_markdown(property_data: dict) -> str:
    """Format detailed property information as Markdown.

    Args:
        property_data: Full property details from API

    Returns:
        Markdown-formatted detailed property information
    """
    name = property_data.get("name", "Unnamed Property")
    prop_id = property_data.get("id", "N/A")

    output = f"# {name}\n\n"
    output += f"**Property ID**: {prop_id}\n\n"

    # Location
    output += "## Location\n"
    output += f"- **City**: {property_data.get('city', 'N/A')}\n"
    output += f"- **Country**: {property_data.get('country', 'N/A')}\n"
    output += f"- **Address**: {property_data.get('address', 'N/A')}\n\n"

    # Property Details
    output += "## Property Details\n"
    output += f"- **Bedrooms**: {property_data.get('bedrooms', 'N/A')}\n"
    output += f"- **Bathrooms**: {property_data.get('bathrooms', 'N/A')}\n"
    output += f"- **Max Guests**: {property_data.get('maxGuests', 'N/A')}\n"
    output += f"- **Property Type**: {property_data.get('propertyType', 'N/A')}\n"
    output += f"- **Status**: {property_data.get('status', 'N/A')}\n\n"

    # Description
    description = property_data.get("description", "")
    if description:
        output += "## Description\n"
        output += f"{description}\n\n"

    # Amenities
    amenities = property_data.get("amenities", [])
    if amenities:
        output += "## Amenities\n"
        for amenity in amenities:
            output += f"- {amenity}\n"
        output += "\n"

    return output


def format_availability_markdown(data: dict) -> str:
    """Format availability calendar as Markdown.

    Args:
        data: Availability data from API

    Returns:
        Markdown-formatted availability calendar
    """
    listing_id = data.get("listing_id", "N/A")
    start_date = data.get("start_date", "N/A")
    end_date = data.get("end_date", "N/A")
    availability = data.get("availability", [])

    output = f"# Availability for Property #{listing_id}\n\n"
    output += f"**Date Range**: {start_date} to {end_date}\n\n"

    if not availability:
        return output + "No availability data for this date range."

    output += "| Date | Status | Price | Min Stay |\n"
    output += "|------|--------|-------|----------|\n"

    for record in availability:
        date = record.get("date", "N/A")
        status = record.get("status", "unknown")
        price = record.get("price")
        min_stay = record.get("min_stay", "N/A")

        price_str = f"${price:,.2f}" if price else "N/A"

        output += f"| {date} | {status} | {price_str} | {min_stay} |\n"

    return output


def format_financial_report_markdown(data: dict) -> str:
    """Format financial report as Markdown.

    Args:
        data: Financial report data from API

    Returns:
        Markdown-formatted financial report
    """
    start_date = data.get("start_date", "N/A")
    end_date = data.get("end_date", "N/A")
    total_revenue = data.get("total_revenue", 0)
    total_expenses = data.get("total_expenses", 0)
    net_income = total_revenue - total_expenses

    output = "# Financial Report\n\n"
    output += f"**Period**: {start_date} to {end_date}\n\n"

    output += "## Summary\n\n"
    output += f"- **Total Revenue**: ${total_revenue:,.2f}\n"
    output += f"- **Total Expenses**: ${total_expenses:,.2f}\n"
    output += f"- **Net Income**: ${net_income:,.2f}\n\n"

    # Revenue breakdown
    revenue_breakdown = data.get("revenue_breakdown", {})
    if revenue_breakdown:
        output += "## Revenue Breakdown\n\n"
        for category, amount in revenue_breakdown.items():
            output += f"- **{category}**: ${amount:,.2f}\n"
        output += "\n"

    # Expense breakdown
    expense_breakdown = data.get("expense_breakdown", {})
    if expense_breakdown:
        output += "## Expense Breakdown\n\n"
        for category, amount in expense_breakdown.items():
            output += f"- **{category}**: ${amount:,.2f}\n"
        output += "\n"

    return output


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
                    "response_format": {
                        "type": "string",
                        "enum": ["json", "markdown"],
                        "default": "markdown",
                        "description": "Response format: 'markdown' for human-readable output (default), 'json' for programmatic processing",
                    },
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
                    "response_format": {
                        "type": "string",
                        "enum": ["json", "markdown"],
                        "default": "markdown",
                        "description": "Response format: 'markdown' for human-readable output (default), 'json' for programmatic processing",
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
                    "response_format": {
                        "type": "string",
                        "enum": ["json", "markdown"],
                        "default": "markdown",
                        "description": "Response format: 'markdown' for human-readable output (default), 'json' for programmatic processing",
                    },
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
                    "response_format": {
                        "type": "string",
                        "enum": ["json", "markdown"],
                        "default": "markdown",
                        "description": "Response format: 'markdown' for human-readable output (default), 'json' for programmatic processing",
                    },
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
                    "response_format": {
                        "type": "string",
                        "enum": ["json", "markdown"],
                        "default": "markdown",
                        "description": "Response format: 'markdown' for human-readable output (default), 'json' for programmatic processing",
                    },
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
                    "response_format": {
                        "type": "string",
                        "enum": ["json", "markdown"],
                        "default": "markdown",
                        "description": "Response format: 'markdown' for human-readable output (default), 'json' for programmatic processing",
                    },
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
                    "response_format": {
                        "type": "string",
                        "enum": ["json", "markdown"],
                        "default": "markdown",
                        "description": "Response format: 'markdown' for human-readable output (default), 'json' for programmatic processing",
                    },
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
async def call_tool(name: str, arguments: Any) -> list[TextContent]:  # noqa: PLR0912,PLR0915
    """Execute a tool by calling the HTTP API."""
    # Add API key to headers if configured
    headers = {"X-API-Key": API_KEY} if API_KEY else {}

    # Extract response_format parameter (default to markdown)
    response_format = arguments.get("response_format", "markdown")

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        try:
            if name == "hostaway_list_properties":
                params = {k: v for k, v in arguments.items() if v is not None}
                # Remove response_format from API params
                params.pop("response_format", None)
                # Use summary=true to prevent context window overflow
                params["summary"] = "true"
                response = await client.get(f"{BASE_URL}/api/listings", params=params)
                response.raise_for_status()
                data = response.json()

                # Format based on response_format
                if response_format == "markdown":
                    formatted_text = format_properties_list_markdown(data)
                    return [TextContent(type="text", text=formatted_text)]
                return [TextContent(type="text", text=json.dumps(data, indent=2))]

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

                # Format based on response_format
                if response_format == "markdown":
                    formatted_text = format_property_details_markdown(data)
                    return [TextContent(type="text", text=formatted_text)]
                return [TextContent(type="text", text=json.dumps(data, indent=2))]

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

                # Format based on response_format
                if response_format == "markdown":
                    formatted_text = format_availability_markdown(data)
                    return [TextContent(type="text", text=formatted_text)]
                return [TextContent(type="text", text=json.dumps(data, indent=2))]

            if name == "hostaway_search_bookings":
                params = {k: v for k, v in arguments.items() if v is not None}
                # Remove response_format from API params
                params.pop("response_format", None)
                # Use summary=true to prevent context window overflow
                params["summary"] = "true"
                response = await client.get(f"{BASE_URL}/api/reservations", params=params)
                response.raise_for_status()
                data = response.json()

                # Format based on response_format
                if response_format == "markdown":
                    formatted_text = format_bookings_list_markdown(data)
                    return [TextContent(type="text", text=formatted_text)]
                return [TextContent(type="text", text=json.dumps(data, indent=2))]

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

                # Format based on response_format
                if response_format == "markdown":
                    formatted_text = format_booking_markdown(data)
                    return [TextContent(type="text", text=formatted_text)]
                return [TextContent(type="text", text=json.dumps(data, indent=2))]

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

                # Guest info is typically small, markdown formatting optional
                if response_format == "markdown":
                    # Simple markdown format for guest
                    guest = data.get("guest", {})
                    formatted_text = f"""# Guest Information

**Name**: {guest.get('name', 'N/A')}
**Email**: {guest.get('email', 'N/A')}
**Phone**: {guest.get('phone', 'N/A')}
**Country**: {guest.get('country', 'N/A')}
"""
                    return [TextContent(type="text", text=formatted_text)]
                return [TextContent(type="text", text=json.dumps(data, indent=2))]

            if name == "hostaway_get_financial_reports":
                params = {k: v for k, v in arguments.items() if v is not None}
                # Remove response_format from API params
                params.pop("response_format", None)
                response = await client.get(f"{BASE_URL}/api/financialReports", params=params)
                response.raise_for_status()
                data = response.json()

                # Format based on response_format
                if response_format == "markdown":
                    formatted_text = format_financial_report_markdown(data)
                    return [TextContent(type="text", text=formatted_text)]
                return [TextContent(type="text", text=json.dumps(data, indent=2))]

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
