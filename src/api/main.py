"""FastAPI application with MCP server integration.

Provides REST API and MCP tool endpoints for Hostaway property management.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.mcp.auth import TokenManager
from src.mcp.config import HostawayConfig
from src.mcp.logging import (
    clear_correlation_id,
    get_logger,
    set_correlation_id,
    setup_logging,
)
from src.mcp.server import initialize_mcp
from src.services.hostaway_client import HostawayClient
from src.services.rate_limiter import RateLimiter

logger = get_logger(__name__)


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

    # Setup structured logging
    setup_logging(
        level=config.log_level if hasattr(config, "log_level") else "INFO",
        json_format=True,
    )
    logger.info("Starting Hostaway MCP Server", extra={"version": "0.1.0"})

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

    logger.info("Hostaway MCP Server started successfully")

    yield

    # Shutdown: Cleanup resources
    logger.info("Shutting down Hostaway MCP Server")
    await hostaway_client.aclose()
    await token_manager.aclose()
    logger.info("Hostaway MCP Server shut down complete")


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


# Correlation ID middleware for request tracing
class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to handle correlation IDs for request tracing."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        """Extract or generate correlation ID and add to context.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response with correlation ID header
        """
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            import uuid

            correlation_id = str(uuid.uuid4())

        # Set correlation ID in context for logging
        set_correlation_id(correlation_id)

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        # Clear correlation ID from context
        clear_correlation_id()

        return response


app.add_middleware(CorrelationIdMiddleware)


# MCP API Key Authentication Middleware
class MCPAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce API key authentication for MCP endpoints."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        """Check API key for MCP endpoint access.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response or 401 if authentication fails
        """
        # Protect both MCP and API endpoints that need authentication
        if request.url.path.startswith("/mcp") or request.url.path.startswith("/api/"):
            from src.mcp.security import verify_api_key

            # Extract API key from header manually since we're not using dependency injection
            x_api_key = request.headers.get("X-API-Key")

            try:
                # Call with extracted header value
                await verify_api_key(request, x_api_key)
            except Exception as e:
                # Authentication failed, return error response
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=401,
                    content={"detail": str(e)},
                    headers={"WWW-Authenticate": "ApiKey"},
                )

        # Continue with request
        response = await call_next(request)
        return response


from src.api.middleware.usage_tracking import UsageTrackingMiddleware

app.add_middleware(UsageTrackingMiddleware)


app.add_middleware(MCPAuthMiddleware)

# Usage Tracking Middleware (T047: Track API usage for billing/metrics)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring and deployment verification.

    Returns:
        Status message with timestamp and version for health monitoring
    """
    from datetime import datetime

    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
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

# Register financial routes
from src.api.routes import financial

app.include_router(financial.router, prefix="/api", tags=["Financial"])

# Register analytics routes (T057: AI-powered MCP operations)
from src.api.routes import analytics

app.include_router(analytics.router, prefix="/api", tags=["Analytics"])

# Initialize MCP server (wraps the FastAPI app)
# This must come AFTER all routes are registered
mcp = initialize_mcp(app)
