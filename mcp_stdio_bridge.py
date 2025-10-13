#!/usr/bin/env python3
"""
MCP stdio bridge for Claude Desktop.

Bridges stdio (Claude Desktop) to HTTP/SSE (FastAPI-MCP server).
"""

import asyncio
import json
import sys

import httpx


async def main() -> None:
    """Bridge stdio to MCP HTTP/SSE endpoint."""
    base_url = "http://localhost:8000"
    session_id: str | None = None

    # Initialize session
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get MCP endpoint and session
        async with client.stream("GET", f"{base_url}/mcp") as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    endpoint = line[6:]  # Remove "data: " prefix
                    if "/messages/" in endpoint:
                        session_id = endpoint.split("session_id=")[1]
                        break

        if not session_id:
            print(
                json.dumps({"error": "Failed to initialize MCP session"}),
                file=sys.stderr,
            )
            sys.exit(1)

        messages_url = f"{base_url}/mcp/messages/?session_id={session_id}"

        # Handle stdio <-> HTTP bridge
        async def read_stdin() -> None:
            """Read from stdin and send to MCP server."""
            loop = asyncio.get_event_loop()
            while True:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                try:
                    message = json.loads(line)
                    response = await client.post(messages_url, json=message)
                    result = response.json()
                    print(json.dumps(result), flush=True)
                except Exception as e:
                    print(
                        json.dumps({"error": str(e)}),
                        file=sys.stderr,
                        flush=True,
                    )

        await read_stdin()


if __name__ == "__main__":
    asyncio.run(main())
