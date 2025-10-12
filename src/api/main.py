"""FastAPI application with MCP server integration.

Provides REST API and MCP tool endpoints for Hostaway property management.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.mcp.config import HostawayConfig
from src.mcp.server import initialize_mcp
from src.services.hostaway_client import HostawayClient
from src.services.rate_limiter import RateLimiter
from src.mcp.auth import TokenManager


# Global instances (initialized in lifespan)
config: HostawayConfig
token_manager: TokenManager
rate_limiter: RateLimiter
hostaway_client: HostawayClient


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle: startup and shutdown.

    Initializes global services on startup and properly cleans up
    resources on shutdown.
    """
    # Startup: Initialize services
    global config, token_manager, rate_limiter, hostaway_client

    config = HostawayConfig()  # type: ignore[call-arg]
    rate_limiter = RateLimiter(
        ip_rate_limit=config.rate_limit_ip,
        account_rate_limit=config.rate_limit_account,
        max_concurrent=config.max_concurrent_requests,
    )
    token_manager = TokenManager(config=config)
    hostaway_client = HostawayClient(
        config=config,
        token_manager=token_manager,
        rate_limiter=rate_limiter,
    )

    yield

    # Shutdown: Cleanup resources
    await hostaway_client.aclose()
    await token_manager.aclose()


# Create FastAPI app
app = FastAPI(
    title="Hostaway MCP Server",
    description="MCP server for Hostaway property management API integration",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring and deployment verification.

    Returns:
        Status message with timestamp and version for health monitoring
    """
    from datetime import datetime, timezone

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0",
        "service": "hostaway-mcp",
    }


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with service information.

    Returns:
        Service metadata
    """
    return {
        "service": "Hostaway MCP Server",
        "version": "0.1.0",
        "mcp_endpoint": "/mcp",
        "docs": "/docs",
    }


# Register authentication routes BEFORE MCP initialization
# (so they're automatically exposed as MCP tools)
from src.api.routes import auth
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Register listings routes
from src.api.routes import listings
app.include_router(listings.router, prefix="/api", tags=["Listings"])

# Register bookings routes
from src.api.routes import bookings
app.include_router(bookings.router, prefix="/api", tags=["Bookings"])

# Initialize MCP server (wraps the FastAPI app)
# This must come AFTER all routes are registered
mcp = initialize_mcp(app)
