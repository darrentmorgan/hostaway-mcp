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
            description="List all Hostaway properties with pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max results (default 10)"},
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
            description="Get detailed information about a specific property",
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
            description="Check property availability for a date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "listing_id": {"type": "integer", "description": "Property ID"},
                    "start_date": {
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
            description="Search bookings with filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max results"},
                    "offset": {"type": "integer", "description": "Offset"},
                    "status": {"type": "string", "description": "Booking status"},
                    "start_date": {"type": "string", "description": "Filter by start date"},
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
            description="Get detailed booking information",
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
            description="Get guest information for a booking",
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
            description="Get financial reports with revenue/expense breakdown",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
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
