"""FastAPI-MCP server instance for Hostaway tools.

Provides MCP tool registration and ASGI transport for AI agent integration.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi_mcp import FastApiMCP  # type: ignore[import-untyped]

# Placeholder for MCP instance - will be initialized in main.py after app creation
mcp: "FastApiMCP | None" = None


def initialize_mcp(app: Any) -> "FastApiMCP":
    """Initialize FastApiMCP with the FastAPI app.

    Args:
        app: FastAPI application instance

    Returns:
        Initialized FastApiMCP instance
    """
    from fastapi_mcp import FastApiMCP

    global mcp
    mcp = FastApiMCP(app, name="hostaway-mcp")

    # Mount ASGI transport for MCP protocol communication
    mcp.mount()

    return mcp


# MCP Tools will be registered via FastAPI routes in routes/auth.py
# FastAPI-MCP automatically converts FastAPI endpoints into MCP tools
