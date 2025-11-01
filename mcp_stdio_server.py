#!/usr/bin/env python3
"""
Native MCP stdio server for Hostaway API.

Provides MCP tools via stdio protocol for Claude Desktop.
Connects to remote Hostaway MCP server with API key authentication.
"""

import asyncio
import json
import os
from typing import Any

import httpx

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Create MCP server
app = Server("hostaway-mcp")

# HTTP client for API calls - use remote server
BASE_URL = os.getenv("REMOTE_MCP_URL", "http://72.60.233.157:8080")
API_KEY = os.getenv("REMOTE_MCP_API_KEY", "")


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
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
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
                return [TextContent(type="text", text=json.dumps(data, indent=2))]

            if name == "get_property_details":
                listing_id = arguments["listing_id"]
                response = await client.get(f"{BASE_URL}/api/listings/{listing_id}")
                response.raise_for_status()
                data = response.json()
                return [TextContent(type="text", text=json.dumps(data, indent=2))]

            if name == "check_availability":
                listing_id = arguments["listing_id"]
                params = {
                    "start_date": arguments["start_date"],
                    "end_date": arguments["end_date"],
                }
                response = await client.get(
                    f"{BASE_URL}/api/listings/{listing_id}/calendar",
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
                return [TextContent(type="text", text=json.dumps(data, indent=2))]

            if name == "search_bookings":
                params = {k: v for k, v in arguments.items() if v is not None}
                # Use summary=true to prevent context window overflow
                params["summary"] = "true"
                response = await client.get(f"{BASE_URL}/api/reservations", params=params)
                response.raise_for_status()
                data = response.json()
                return [TextContent(type="text", text=json.dumps(data, indent=2))]

            if name == "get_booking_details":
                booking_id = arguments["booking_id"]
                response = await client.get(f"{BASE_URL}/api/reservations/{booking_id}")
                response.raise_for_status()
                data = response.json()
                return [TextContent(type="text", text=json.dumps(data, indent=2))]

            if name == "get_guest_info":
                booking_id = arguments["booking_id"]
                response = await client.get(f"{BASE_URL}/api/reservations/{booking_id}/guest")
                response.raise_for_status()
                data = response.json()
                return [TextContent(type="text", text=json.dumps(data, indent=2))]

            if name == "get_financial_reports":
                params = {k: v for k, v in arguments.items() if v is not None}
                response = await client.get(f"{BASE_URL}/api/financialReports", params=params)
                response.raise_for_status()
                data = response.json()
                return [TextContent(type="text", text=json.dumps(data, indent=2))]

            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except httpx.HTTPError as e:
            return [
                TextContent(
                    type="text",
                    text=f"HTTP Error: {e}\n\nResponse: {getattr(e, 'response', None)}",
                )
            ]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {e}")]


async def main() -> None:
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
