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

# Try to import test mode check, skip if testing module not available (production)
try:
    from src.testing.hostaway_mocks import is_test_mode
except (ImportError, ModuleNotFoundError):

    def is_test_mode():
        return False  # Always False in production


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

    # Use mock client in test mode, real client otherwise
    if is_test_mode():
        from src.testing.mock_client import MockHostawayClient

        logger.info("TEST MODE: Using MockHostawayClient with deterministic data")
        hostaway_client = MockHostawayClient(
            config=config,
            token_manager=token_manager,
            rate_limiter=rate_limiter,
        )
    else:
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


# Custom 404 exception handler (Issue #008-US1: Return 404 for non-existent routes)
# This must be registered BEFORE middleware to handle route matching failures
# before authentication is checked
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: Exception) -> dict:
    """Return 404 for non-existent routes without authentication check.

    This handler ensures that non-existent routes return HTTP 404 instead of 401,
    improving API consumer developer experience. Route existence should be checked
    BEFORE authentication.

    Args:
        request: Incoming HTTP request
        exc: Exception that triggered the handler (StarletteHTTPException)

    Returns:
        JSON response with 404 status and route path in error message
    """
    from fastapi.responses import JSONResponse

    # Get correlation ID from request state (set by CorrelationIdMiddleware)
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    # Build error response with route path
    response_content = {
        "detail": f"Route '{request.url.path}' not found",
        "path": request.url.path,
        "method": request.method,
    }

    # Create JSON response with 404 status
    response = JSONResponse(
        status_code=404,
        content=response_content,
    )

    # Preserve correlation ID header for request tracing
    response.headers["X-Correlation-ID"] = correlation_id

    return response


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


# Error Recovery Middleware for graceful degradation
class ErrorRecoveryMiddleware(BaseHTTPMiddleware):
    """Middleware for graceful error recovery and partial success handling.

    Catches unhandled exceptions and returns structured error responses,
    logging the full context for debugging while preventing sensitive data leakage.
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        """Handle request errors gracefully.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response (normal or error response)
        """
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the error with full context for debugging
            logger.error(
                "Unhandled error in request",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "query_params": dict(request.query_params),
                },
                exc_info=True,  # Include stack trace in logs
            )

            # Return 500 with sanitized error details
            from fastapi.responses import JSONResponse

            return JSONResponse(
                content={
                    "detail": "Internal server error - operation may have partially completed",
                    "error_type": type(e).__name__,
                    "path": request.url.path,
                },
                status_code=500,
            )


app.add_middleware(ErrorRecoveryMiddleware)

# Rate Limiter Middleware (Issue #008-US2: Add rate limit visibility headers)
from src.api.middleware.rate_limiter import RateLimiterMiddleware

app.add_middleware(RateLimiterMiddleware, ip_limit=15, time_window=10)


# MCP API Key Authentication Middleware
class MCPAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce API key authentication for MCP endpoints.

    ISSUE #008-US1 FIX: This middleware now checks route existence BEFORE
    enforcing authentication, allowing 404 errors to be returned for
    non-existent routes instead of 401.
    """

    def _route_exists(self, request: Request) -> bool:
        """Check if a route exists in FastAPI's router.

        Args:
            request: Incoming HTTP request

        Returns:
            True if route exists, False otherwise
        """
        # Access FastAPI's router to check if route exists
        for route in request.app.routes:
            # Check if this route matches the request path and method
            match, _ = route.matches(request.scope)
            if match.name in ("full", "partial"):
                return True
        return False

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
            # ISSUE #008-US1 FIX: Check if route exists BEFORE enforcing authentication
            # This prevents 401 responses for non-existent routes
            if not self._route_exists(request):
                # Route doesn't exist - let it pass through to get proper 404 response
                response = await call_next(request)
                return response

            # Route exists - enforce authentication
            from fastapi import HTTPException

            from src.mcp.security import verify_api_key

            # Extract API key from header manually since we're not using dependency injection
            x_api_key = request.headers.get("X-API-Key")

            try:
                # Call with extracted header value
                await verify_api_key(request, x_api_key)
            except HTTPException as e:
                # Authentication failed - verify_api_key raised HTTP exception
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail},
                    headers=e.headers or {},
                )

            # Authentication passed - continue with request
            response = await call_next(request)
            return response

        # Path doesn't require authentication - continue with request
        response = await call_next(request)
        return response


from src.api.middleware.usage_tracking import UsageTrackingMiddleware

app.add_middleware(UsageTrackingMiddleware)

# Token-Aware Middleware for response optimization (prevents context window overflow)
from src.api.middleware.token_aware_middleware import TokenAwareMiddleware

app.add_middleware(TokenAwareMiddleware)

app.add_middleware(MCPAuthMiddleware)

# Usage Tracking Middleware (T047: Track API usage for billing/metrics)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint for monitoring and deployment verification.

    Returns:
        Status message with timestamp, version, and context protection metrics
    """
    from datetime import datetime

    from src.services.telemetry_service import get_telemetry_service

    telemetry = get_telemetry_service()
    metrics = telemetry.get_metrics()

    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "0.1.0",
        "service": "hostaway-mcp",
        "context_protection": {
            "total_requests": metrics["total_requests"],
            "pagination_adoption": metrics["pagination_adoption"],
            "summarization_adoption": metrics["summarization_adoption"],
            "avg_response_size_bytes": metrics["avg_response_size"],
            "avg_latency_ms": metrics["avg_latency_ms"],
            "oversized_events": metrics["oversized_events"],
            "uptime_seconds": metrics["uptime_seconds"],
        },
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
