#!/usr/bin/env python3
"""MCP Remote Bridge - Connects Claude Desktop (stdio) to Remote HTTP MCP Server.

This bridge allows Claude Desktop to connect to a remote HTTP-based MCP server
while maintaining the stdio protocol that Claude Desktop expects.
"""

import asyncio
import json
import os
import sys
from typing import Any

import httpx
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp.server import Server

# Get remote server config from environment
REMOTE_URL = os.getenv("REMOTE_MCP_URL", "http://72.60.233.157:8080/mcp")
API_KEY = os.getenv("REMOTE_MCP_API_KEY", "")

# Create MCP server
app = Server("hostaway-mcp-bridge")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Forward tool listing to remote MCP server."""
    headers = {"X-API-Key": API_KEY} if API_KEY else {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Call remote server's list_tools
            response = await client.post(
                f"{REMOTE_URL}/tools/list",
                headers=headers,
                json={"method": "tools/list", "params": {}},
            )
            response.raise_for_status()
            data = response.json()

            # Convert remote tools to MCP Tool objects
            tools = []
            for tool_data in data.get("tools", []):
                tools.append(
                    Tool(
                        name=tool_data["name"],
                        description=tool_data.get("description", ""),
                        inputSchema=tool_data.get(
                            "inputSchema", {"type": "object", "properties": {}}
                        ),
                    )
                )

            return tools
        except Exception as e:
            print(f"Error listing tools from remote server: {e}", file=sys.stderr)
            return []


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Forward tool calls to remote MCP server."""
    headers = {"X-API-Key": API_KEY} if API_KEY else {}

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Call remote server's call_tool
            response = await client.post(
                f"{REMOTE_URL}/tools/call",
                headers=headers,
                json={"method": "tools/call", "params": {"name": name, "arguments": arguments}},
            )
            response.raise_for_status()
            data = response.json()

            # Convert response to TextContent
            if "content" in data:
                content = data["content"]
                if isinstance(content, list):
                    return [TextContent(type="text", text=json.dumps(item)) for item in content]
                return [TextContent(type="text", text=json.dumps(content))]
            if "result" in data:
                return [TextContent(type="text", text=json.dumps(data["result"]))]
            return [TextContent(type="text", text=json.dumps(data))]

        except Exception as e:
            error_msg = f"Error calling tool '{name}' on remote server: {e}"
            print(error_msg, file=sys.stderr)
            return [TextContent(type="text", text=json.dumps({"error": error_msg}))]


async def main():
    """Run the MCP bridge server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
