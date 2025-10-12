# FastAPI-MCP Integration Guide

## Overview

### What is FastAPI-MCP?

FastAPI-MCP is a library that bridges FastAPI applications with the Model Context Protocol (MCP), allowing you to expose your existing FastAPI endpoints as MCP tools that can be consumed by AI assistants like Claude. This enables AI agents to interact with your APIs in a standardized, type-safe manner.

### Why Use FastAPI-MCP for Hostaway Integration?

FastAPI-MCP provides several key advantages for the hostaway-mcp project:

- **Zero Refactoring**: Convert existing FastAPI endpoints into MCP tools without rewriting code
- **Type Safety**: Leverages FastAPI's Pydantic models for automatic schema validation
- **Authentication**: Built-in support for FastAPI's dependency injection and authentication patterns
- **Performance**: Uses ASGI transport for efficient, asynchronous communication
- **Documentation**: Automatically preserves OpenAPI schemas and documentation
- **Separation of Concerns**: Keep your REST API and MCP interface in sync without duplication

### Key Features

- **Automatic Tool Generation**: FastAPI endpoints become MCP tools automatically
- **Schema Preservation**: Request/response schemas are converted to MCP tool schemas
- **Authentication Support**: Use FastAPI dependencies for secure tool access
- **ASGI Transport**: Efficient bidirectional communication
- **HTTP Fallback**: Optional HTTP transport for testing and debugging
- **Framework Agnostic**: Works with any FastAPI application structure

### Use Cases for Hostaway-MCP

1. **Property Management**: Expose listing, booking, and calendar operations as AI-callable tools
2. **Guest Communication**: Allow AI to send messages, respond to inquiries, and manage guest interactions
3. **Reporting & Analytics**: Provide data retrieval tools for AI-powered insights
4. **Automation**: Enable AI to trigger workflows like check-in notifications, cleaning schedules
5. **Integration Testing**: Use MCP tools to test Hostaway API integrations programmatically

---

## Installation & Setup

### Prerequisites

**System Requirements:**
- Python 3.10 or higher (Python 3.12 recommended)
- uv or pip package manager
- FastAPI application (existing or new)

**Knowledge Requirements:**
- Familiarity with FastAPI framework
- Basic understanding of async Python
- REST API concepts
- (Optional) Understanding of MCP protocol basics

### Installation

#### Using uv (Recommended)

```bash
# Navigate to project directory
cd /Users/darrenmorgan/AI_Projects/hostaway-mcp

# Add fastapi-mcp to project
uv add fastapi-mcp

# Verify installation
uv pip list | grep fastapi-mcp
```

#### Using pip

```bash
# Activate your virtual environment first
source .venv/bin/activate  # or your virtualenv path

# Install fastapi-mcp
pip install fastapi-mcp

# Verify installation
pip show fastapi-mcp
```

### Initial Configuration

#### Project Structure

Organize your project to separate MCP concerns:

```
hostaway-mcp/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   └── routes/
│   │       ├── listings.py      # Hostaway listings endpoints
│   │       ├── bookings.py      # Hostaway bookings endpoints
│   │       └── guests.py        # Hostaway guest endpoints
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py            # MCP server setup
│   │   └── config.py            # MCP configuration
│   ├── services/
│   │   └── hostaway_client.py   # Hostaway API client
│   └── models/
│       └── schemas.py           # Pydantic models
├── tests/
├── docs/
└── pyproject.toml
```

#### Basic Server Setup

Create `src/mcp/server.py`:

```python
"""MCP Server for Hostaway Integration."""
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

from src.api.routes import listings, bookings, guests


def create_mcp_server() -> FastAPI:
    """Create and configure the FastAPI MCP server."""
    app = FastAPI(
        title="Hostaway MCP Server",
        description="Model Context Protocol server for Hostaway property management",
        version="0.1.0",
    )

    # Include your API routes
    app.include_router(listings.router, prefix="/listings", tags=["Listings"])
    app.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
    app.include_router(guests.router, prefix="/guests", tags=["Guests"])

    # Initialize MCP integration
    mcp = FastApiMCP(app)

    # Mount MCP transport (use ASGI for production)
    mcp.mount()  # ASGI transport

    return app


# For development/testing, you can also expose HTTP transport
def create_dev_server() -> FastAPI:
    """Create server with HTTP transport for testing."""
    app = create_mcp_server()
    mcp = FastApiMCP(app)
    mcp.mount_http()  # Adds HTTP endpoints for testing
    return app
```

#### Environment Configuration

Create `src/mcp/config.py`:

```python
"""MCP Server Configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    """MCP server settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MCP_",
        case_sensitive=False,
    )

    # Server settings
    server_name: str = "hostaway-mcp"
    server_version: str = "0.1.0"

    # Hostaway API credentials
    hostaway_api_key: str
    hostaway_account_id: str
    hostaway_base_url: str = "https://api.hostaway.com/v1"

    # Authentication
    enable_auth: bool = True
    api_key_header: str = "X-API-Key"
    allowed_api_keys: list[str] = []

    # Transport settings
    use_http_transport: bool = False  # Set to True for development

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60


settings = MCPSettings()
```

#### Environment Variables

Create `.env` file in project root:

```bash
# Hostaway API Configuration
MCP_HOSTAWAY_API_KEY=your_hostaway_api_key_here
MCP_HOSTAWAY_ACCOUNT_ID=your_account_id_here
MCP_HOSTAWAY_BASE_URL=https://api.hostaway.com/v1

# MCP Server Configuration
MCP_SERVER_NAME=hostaway-mcp
MCP_SERVER_VERSION=0.1.0

# Authentication
MCP_ENABLE_AUTH=true
MCP_API_KEY_HEADER=X-API-Key
MCP_ALLOWED_API_KEYS=["key1","key2"]  # JSON array format

# Development settings
MCP_USE_HTTP_TRANSPORT=false
```

**Important**: Add `.env` to `.gitignore` to protect credentials.

---

## Core Concepts

### MCP Protocol Basics

The Model Context Protocol (MCP) is a standardized protocol for AI assistants to interact with external tools and data sources. Key concepts:

**Tools**: Functions that AI can invoke (your FastAPI endpoints)
**Resources**: Data sources AI can read (optional, for static data)
**Prompts**: Reusable prompt templates (optional, for common queries)

FastAPI-MCP automatically converts your API endpoints into MCP tools with proper schemas.

### How FastAPI Endpoints Become MCP Tools

FastAPI-MCP uses FastAPI's introspection capabilities to automatically convert endpoints:

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()


class Listing(BaseModel):
    id: int
    name: str
    address: str
    max_guests: int


class ListingResponse(BaseModel):
    listing: Listing
    success: bool


@router.get("/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: int):
    """
    Retrieve a specific Hostaway listing by ID.

    This endpoint fetches detailed information about a property listing
    including name, address, and capacity.
    """
    # Your implementation here
    pass
```

**This becomes an MCP tool with:**
- **Tool Name**: `get_listing`
- **Description**: Extracted from docstring
- **Input Schema**: Parameters (listing_id: int)
- **Output Schema**: ListingResponse model

### Authentication and Authorization Flow

FastAPI-MCP leverages FastAPI's dependency injection for authentication:

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from src.mcp.config import settings

api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Verify API key from request header."""
    if not settings.enable_auth:
        return "dev_mode"

    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    if api_key not in settings.allowed_api_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key


# Use in your endpoints
@router.get("/listings", dependencies=[Depends(verify_api_key)])
async def list_all_listings():
    """List all Hostaway listings (authenticated)."""
    pass
```

**Authentication Flow:**
1. AI client sends request with API key in header
2. FastAPI dependency checks key validity
3. If valid, endpoint executes and returns result
4. If invalid, HTTP 401/403 returned to AI client

### ASGI Transport Explanation

**ASGI (Asynchronous Server Gateway Interface)** is the transport mechanism used by FastAPI-MCP:

**Benefits:**
- **Bidirectional**: Server can push updates to clients
- **Efficient**: Low overhead, multiplexed connections
- **Async Native**: Works seamlessly with FastAPI's async capabilities
- **Scalable**: Handles many concurrent AI requests

**When to Use:**
- Production deployments
- High-concurrency scenarios
- Real-time updates needed

**HTTP Transport Alternative:**
- Development and testing
- Simple request/response patterns
- Debugging tool schemas

```python
# ASGI transport (default)
mcp.mount()  # Registers ASGI transport

# HTTP transport (for testing)
mcp.mount_http()  # Adds /mcp/tools, /mcp/invoke endpoints
```

---

## Implementation Guide

### Basic Server Setup

#### Step 1: Create the FastAPI Application

`src/api/main.py`:

```python
"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import listings, bookings, guests
from src.mcp.config import settings


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Hostaway API",
        description="REST API for Hostaway property management",
        version="1.0.0",
    )

    # CORS middleware (if needed)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(listings.router, prefix="/api/v1/listings", tags=["Listings"])
    app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["Bookings"])
    app.include_router(guests.router, prefix="/api/v1/guests", tags=["Guests"])

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": settings.server_name}

    return app


app = create_app()
```

#### Step 2: Add MCP Integration

`src/mcp/server.py`:

```python
"""MCP Server integration."""
from fastapi_mcp import FastApiMCP
from src.api.main import create_app
from src.mcp.config import settings


def create_mcp_server():
    """Create FastAPI app with MCP integration."""
    app = create_app()

    # Initialize MCP
    mcp = FastApiMCP(
        app,
        server_name=settings.server_name,
        server_version=settings.server_version,
    )

    # Mount appropriate transport
    if settings.use_http_transport:
        mcp.mount_http()  # Development
    else:
        mcp.mount()  # Production (ASGI)

    return app


# Entry point
mcp_app = create_mcp_server()
```

#### Step 3: Run the Server

**Development Mode:**

```bash
# Using uvicorn directly
uvicorn src.mcp.server:mcp_app --reload --port 8000

# Or with environment variables
MCP_USE_HTTP_TRANSPORT=true uvicorn src.mcp.server:mcp_app --reload
```

**Production Mode:**

```bash
# Using gunicorn with uvicorn workers
gunicorn src.mcp.server:mcp_app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120
```

### Adding Endpoints That Expose as Tools

#### Example 1: Simple Listing Retrieval

`src/api/routes/listings.py`:

```python
"""Hostaway listings endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.services.hostaway_client import HostawayClient
from src.mcp.auth import verify_api_key

router = APIRouter()


class Listing(BaseModel):
    """Hostaway listing model."""
    id: int
    name: str
    address: str
    city: str
    max_guests: int
    bedrooms: int
    bathrooms: int
    property_type: str


class ListingResponse(BaseModel):
    """Response model for listing retrieval."""
    listing: Listing
    success: bool = True
    message: str = "Listing retrieved successfully"


@router.get(
    "/{listing_id}",
    response_model=ListingResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Get listing by ID",
)
async def get_listing(
    listing_id: int = Field(..., description="The unique ID of the listing"),
    client: HostawayClient = Depends(),
):
    """
    Retrieve detailed information about a specific Hostaway listing.

    This tool fetches comprehensive property details including:
    - Property name and address
    - Guest capacity and bedroom/bathroom count
    - Property type (apartment, house, etc.)

    Use this when you need complete information about a single property.
    """
    try:
        listing_data = await client.get_listing(listing_id)
        return ListingResponse(listing=Listing(**listing_data))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Listing not found: {str(e)}")
```

**AI Tool Usage:**
```json
{
  "tool": "get_listing",
  "arguments": {
    "listing_id": 12345
  }
}
```

#### Example 2: Complex Booking Search

`src/api/routes/bookings.py`:

```python
"""Hostaway bookings endpoints."""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

router = APIRouter()


class BookingSearchFilters(BaseModel):
    """Search filters for bookings."""
    listing_id: Optional[int] = Field(None, description="Filter by listing ID")
    check_in_from: Optional[date] = Field(None, description="Check-in date range start")
    check_in_to: Optional[date] = Field(None, description="Check-in date range end")
    status: Optional[str] = Field(None, description="Booking status (confirmed, pending, cancelled)")
    guest_name: Optional[str] = Field(None, description="Guest name search")


class Booking(BaseModel):
    """Booking information."""
    id: int
    listing_id: int
    guest_name: str
    check_in: date
    check_out: date
    status: str
    total_price: float
    num_guests: int


class BookingSearchResponse(BaseModel):
    """Response for booking search."""
    bookings: list[Booking]
    total_count: int
    page: int
    page_size: int
    success: bool = True


@router.post(
    "/search",
    response_model=BookingSearchResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Search bookings with filters",
)
async def search_bookings(
    filters: BookingSearchFilters,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    client: HostawayClient = Depends(),
):
    """
    Search Hostaway bookings with multiple filter criteria.

    This tool allows comprehensive booking searches with filters for:
    - Specific listings or all properties
    - Date ranges for check-in/check-out
    - Booking status (confirmed, pending, cancelled)
    - Guest name search

    Returns paginated results with booking details including pricing,
    guest information, and dates.

    Use this when you need to:
    - Find bookings for a specific date range
    - Check availability for a listing
    - Search for guest reservations
    - Generate booking reports
    """
    try:
        results = await client.search_bookings(
            filters=filters.model_dump(exclude_none=True),
            page=page,
            page_size=page_size,
        )

        return BookingSearchResponse(
            bookings=[Booking(**b) for b in results["bookings"]],
            total_count=results["total"],
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
```

**AI Tool Usage:**
```json
{
  "tool": "search_bookings",
  "arguments": {
    "filters": {
      "listing_id": 12345,
      "check_in_from": "2025-11-01",
      "check_in_to": "2025-11-30",
      "status": "confirmed"
    },
    "page": 1,
    "page_size": 50
  }
}
```

#### Example 3: Guest Communication Tool

`src/api/routes/guests.py`:

```python
"""Guest communication endpoints."""
from enum import Enum
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

router = APIRouter()


class MessageChannel(str, Enum):
    """Communication channels."""
    EMAIL = "email"
    SMS = "sms"
    AIRBNB = "airbnb"
    BOOKING_COM = "booking_com"


class SendMessageRequest(BaseModel):
    """Request to send message to guest."""
    booking_id: int = Field(..., description="Booking ID to send message for")
    channel: MessageChannel = Field(..., description="Communication channel")
    message: str = Field(..., min_length=1, max_length=5000, description="Message content")
    subject: Optional[str] = Field(None, description="Email subject (required for email)")

    @field_validator("subject")
    def validate_subject_for_email(cls, v, info):
        """Ensure subject is provided for email messages."""
        if info.data.get("channel") == MessageChannel.EMAIL and not v:
            raise ValueError("Subject is required for email messages")
        return v


class SendMessageResponse(BaseModel):
    """Response for message sending."""
    message_id: str
    booking_id: int
    channel: str
    sent_at: str
    success: bool = True
    message: str = "Message sent successfully"


@router.post(
    "/messages/send",
    response_model=SendMessageResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Send message to guest",
)
async def send_guest_message(
    request: SendMessageRequest,
    client: HostawayClient = Depends(),
):
    """
    Send a message to a guest for a specific booking.

    This tool enables communication with guests through various channels:
    - Email: For detailed information, confirmations, instructions
    - SMS: For time-sensitive notifications
    - Airbnb: Through Airbnb messaging system
    - Booking.com: Through Booking.com messaging system

    The message will be sent through the specified channel associated
    with the booking. For email messages, a subject line is required.

    Use this when you need to:
    - Send check-in instructions
    - Provide local recommendations
    - Respond to guest inquiries
    - Send booking confirmations or updates
    - Notify about property issues or changes

    Note: Messages are logged in the booking timeline for record-keeping.
    """
    try:
        result = await client.send_message(
            booking_id=request.booking_id,
            channel=request.channel.value,
            message=request.message,
            subject=request.subject,
        )

        return SendMessageResponse(
            message_id=result["id"],
            booking_id=request.booking_id,
            channel=request.channel.value,
            sent_at=result["sent_at"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message: {str(e)}"
        )
```

### Authentication Configuration

#### Option 1: API Key Authentication

`src/mcp/auth.py`:

```python
"""Authentication for MCP server."""
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from src.mcp.config import settings

api_key_header = APIKeyHeader(
    name=settings.api_key_header,
    auto_error=False,
    description="API key for MCP server access",
)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key from request header.

    Args:
        api_key: API key from request header

    Returns:
        Validated API key

    Raises:
        HTTPException: If authentication fails
    """
    # Skip auth in development mode
    if not settings.enable_auth:
        return "dev_mode"

    # Check if key provided
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate key
    if api_key not in settings.allowed_api_keys:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
        )

    return api_key


# Optional: Add rate limiting per API key
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict

_rate_limit_tracker: Dict[str, list[datetime]] = defaultdict(list)


async def rate_limit_check(api_key: str = Depends(verify_api_key)) -> str:
    """
    Check rate limits for API key.

    Limits requests per minute based on settings.
    """
    if not settings.rate_limit_enabled:
        return api_key

    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=1)

    # Clean old requests
    _rate_limit_tracker[api_key] = [
        ts for ts in _rate_limit_tracker[api_key] if ts > cutoff
    ]

    # Check limit
    if len(_rate_limit_tracker[api_key]) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later.",
        )

    # Record request
    _rate_limit_tracker[api_key].append(now)

    return api_key
```

#### Option 2: OAuth2 Bearer Token

`src/mcp/auth.py`:

```python
"""OAuth2 authentication for MCP server."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT settings
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    scopes: list[str] = []


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Verify JWT token from request.

    Args:
        token: JWT token from Authorization header

    Returns:
        Decoded token data

    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(
            username=username,
            scopes=payload.get("scopes", [])
        )
    except JWTError:
        raise credentials_exception

    return token_data


# Use in endpoints
@router.get("/protected", dependencies=[Depends(verify_token)])
async def protected_endpoint():
    """Protected endpoint requiring valid JWT."""
    pass
```

### Deployment Strategies

#### Strategy 1: Docker Deployment

`Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["uv", "run", "uvicorn", "src.mcp.server:mcp_app", "--host", "0.0.0.0", "--port", "8000"]
```

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  hostaway-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MCP_HOSTAWAY_API_KEY=${HOSTAWAY_API_KEY}
      - MCP_HOSTAWAY_ACCOUNT_ID=${HOSTAWAY_ACCOUNT_ID}
      - MCP_ENABLE_AUTH=true
      - MCP_ALLOWED_API_KEYS=["${MCP_API_KEY}"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

#### Strategy 2: Systemd Service (Linux)

`/etc/systemd/system/hostaway-mcp.service`:

```ini
[Unit]
Description=Hostaway MCP Server
After=network.target

[Service]
Type=notify
User=mcp-user
Group=mcp-user
WorkingDirectory=/opt/hostaway-mcp
EnvironmentFile=/opt/hostaway-mcp/.env
ExecStart=/opt/hostaway-mcp/.venv/bin/gunicorn \
    src.mcp.server:mcp_app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile /var/log/hostaway-mcp/access.log \
    --error-logfile /var/log/hostaway-mcp/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable hostaway-mcp
sudo systemctl start hostaway-mcp
sudo systemctl status hostaway-mcp
```

#### Strategy 3: Cloud Platform (AWS Lambda with Mangum)

Install Mangum for AWS Lambda:

```bash
uv add mangum
```

`src/mcp/lambda_handler.py`:

```python
"""AWS Lambda handler for MCP server."""
from mangum import Mangum
from src.mcp.server import create_mcp_server

app = create_mcp_server()
handler = Mangum(app, lifespan="off")
```

Deploy with AWS SAM or Serverless Framework.

---

## Best Practices

### Security Considerations

#### 1. API Key Management

**DO:**
- Store API keys in environment variables or secrets managers
- Use different keys for development, staging, and production
- Rotate keys regularly (every 90 days)
- Implement key scoping (different permissions per key)

**DON'T:**
- Commit keys to version control
- Share keys across environments
- Use predictable or weak keys
- Log API keys in application logs

```python
# Good: Key rotation with multiple valid keys
class KeyStore:
    """Manage multiple API keys with rotation."""

    def __init__(self):
        self.active_keys = set(settings.allowed_api_keys)
        self.deprecated_keys = set()  # Keys being phased out

    def is_valid(self, key: str) -> bool:
        """Check if key is valid."""
        return key in self.active_keys or key in self.deprecated_keys

    def rotate_key(self, old_key: str, new_key: str):
        """Rotate API key."""
        self.deprecated_keys.add(old_key)
        self.active_keys.add(new_key)
        # Remove old key after grace period
```

#### 2. Input Validation

Always validate and sanitize inputs:

```python
from pydantic import BaseModel, Field, field_validator, model_validator

class SafeInput(BaseModel):
    """Safe input model with validation."""

    listing_id: int = Field(..., gt=0, description="Must be positive")
    message: str = Field(..., min_length=1, max_length=5000)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')

    @field_validator('message')
    def sanitize_message(cls, v):
        """Remove potentially dangerous content."""
        # Strip HTML tags
        import re
        v = re.sub(r'<[^>]+>', '', v)
        # Remove SQL injection attempts
        dangerous_patterns = ['DROP TABLE', 'DELETE FROM', '--', ';']
        for pattern in dangerous_patterns:
            if pattern.lower() in v.lower():
                raise ValueError("Message contains prohibited content")
        return v
```

#### 3. Rate Limiting

Implement comprehensive rate limiting:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limits
@router.get("/listings")
@limiter.limit("10/minute")
async def get_listings(request: Request):
    """Rate-limited endpoint."""
    pass
```

#### 4. Audit Logging

Log all MCP tool invocations:

```python
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def log_tool_invocation(
    tool_name: str,
    user_id: str,
    parameters: dict,
    response_status: int,
):
    """Log MCP tool usage for audit trail."""
    logger.info(
        "MCP Tool Invocation",
        extra={
            "timestamp": datetime.utcnow().isoformat(),
            "tool": tool_name,
            "user": user_id,
            "parameters": parameters,
            "status": response_status,
        }
    )
```

### Performance Optimization

#### 1. Use Async Throughout

```python
# Good: Async all the way
@router.get("/listings/{listing_id}")
async def get_listing(listing_id: int, client: HostawayClient = Depends()):
    """Async endpoint for better concurrency."""
    result = await client.get_listing(listing_id)
    return result

# Bad: Blocking calls
@router.get("/listings/{listing_id}")
def get_listing_sync(listing_id: int):
    """Blocking endpoint - avoid!"""
    result = requests.get(f"https://api.hostaway.com/listings/{listing_id}")
    return result.json()
```

#### 2. Connection Pooling

```python
import httpx
from contextlib import asynccontextmanager

class HostawayClient:
    """Hostaway API client with connection pooling."""

    def __init__(self):
        self._client = None

    @asynccontextmanager
    async def _get_client(self):
        """Get HTTP client with connection pooling."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                )
            )
        try:
            yield self._client
        finally:
            pass  # Keep connection alive

    async def close(self):
        """Close client connections."""
        if self._client:
            await self._client.aclose()
```

#### 3. Caching

```python
from functools import lru_cache
from datetime import datetime, timedelta
from typing import Optional

class CachedResponse:
    """Cache with TTL."""

    def __init__(self, value, expires_at: datetime):
        self.value = value
        self.expires_at = expires_at

    def is_valid(self) -> bool:
        """Check if cache entry is still valid."""
        return datetime.utcnow() < self.expires_at

_cache: dict[str, CachedResponse] = {}

async def get_listing_cached(listing_id: int) -> dict:
    """Get listing with caching."""
    cache_key = f"listing:{listing_id}"

    # Check cache
    if cache_key in _cache and _cache[cache_key].is_valid():
        return _cache[cache_key].value

    # Fetch from API
    result = await client.get_listing(listing_id)

    # Cache for 5 minutes
    _cache[cache_key] = CachedResponse(
        value=result,
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )

    return result
```

#### 4. Database Query Optimization

If using a database alongside Hostaway API:

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Good: Eager loading
async def get_bookings_with_listings():
    """Fetch bookings with related listings in one query."""
    stmt = (
        select(Booking)
        .options(selectinload(Booking.listing))
        .where(Booking.status == "confirmed")
    )
    result = await session.execute(stmt)
    return result.scalars().all()

# Bad: N+1 queries
async def get_bookings_n_plus_one():
    """Inefficient - causes N+1 queries."""
    bookings = await session.execute(select(Booking))
    for booking in bookings:
        listing = await session.execute(
            select(Listing).where(Listing.id == booking.listing_id)
        )
```

### Error Handling

#### 1. Structured Error Responses

```python
from fastapi import HTTPException
from pydantic import BaseModel

class ErrorDetail(BaseModel):
    """Structured error detail."""
    code: str
    message: str
    field: Optional[str] = None

class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: ErrorDetail
    timestamp: str
    request_id: str

# Use in exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured response."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=f"HTTP_{exc.status_code}",
                message=exc.detail,
            ),
            timestamp=datetime.utcnow().isoformat(),
            request_id=request.state.request_id,
        ).model_dump()
    )
```

#### 2. Retry Logic for External APIs

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import httpx

class HostawayAPIError(Exception):
    """Hostaway API error."""
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
)
async def fetch_from_hostaway(endpoint: str) -> dict:
    """
    Fetch data from Hostaway API with retry logic.

    Retries up to 3 times with exponential backoff.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.hostaway_base_url}/{endpoint}",
            headers={"Authorization": f"Bearer {settings.hostaway_api_key}"},
        )
        response.raise_for_status()
        return response.json()
```

#### 3. Graceful Degradation

```python
@router.get("/listings/{listing_id}")
async def get_listing_safe(listing_id: int):
    """
    Get listing with graceful degradation.

    Falls back to cached data if Hostaway API is unavailable.
    """
    try:
        # Try to fetch from Hostaway
        result = await client.get_listing(listing_id)
        return {"listing": result, "source": "live"}

    except httpx.HTTPStatusError as e:
        # Try cache if API fails
        cached = await get_from_cache(f"listing:{listing_id}")
        if cached:
            logger.warning(f"Hostaway API unavailable, using cache: {e}")
            return {"listing": cached, "source": "cache", "stale": True}

        # No cache available
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable"
        )
```

### Testing Strategies

#### 1. Unit Tests for Tools

`tests/test_listings.py`:

```python
"""Unit tests for listing endpoints."""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.mcp.server import create_mcp_server

@pytest.fixture
def client():
    """Test client fixture."""
    app = create_mcp_server()
    return TestClient(app)

@pytest.fixture
def mock_hostaway_client():
    """Mock Hostaway client."""
    with patch("src.api.routes.listings.HostawayClient") as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        yield mock_instance

def test_get_listing_success(client, mock_hostaway_client):
    """Test successful listing retrieval."""
    # Setup mock
    mock_hostaway_client.get_listing.return_value = {
        "id": 123,
        "name": "Beautiful Beach House",
        "address": "123 Ocean Drive",
        "city": "Miami",
        "max_guests": 6,
        "bedrooms": 3,
        "bathrooms": 2,
        "property_type": "house",
    }

    # Make request
    response = client.get(
        "/api/v1/listings/123",
        headers={"X-API-Key": "test-key"}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["listing"]["name"] == "Beautiful Beach House"
    assert data["listing"]["max_guests"] == 6

def test_get_listing_not_found(client, mock_hostaway_client):
    """Test listing not found error."""
    mock_hostaway_client.get_listing.side_effect = Exception("Not found")

    response = client.get(
        "/api/v1/listings/999",
        headers={"X-API-Key": "test-key"}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_get_listing_unauthorized(client):
    """Test authentication required."""
    response = client.get("/api/v1/listings/123")
    assert response.status_code == 401
```

#### 2. Integration Tests with MCP Protocol

`tests/test_mcp_integration.py`:

```python
"""Integration tests for MCP protocol."""
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_mcp_tool_discovery():
    """Test MCP tool discovery."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()

            # Assert expected tools exist
            tool_names = [t.name for t in tools.tools]
            assert "get_listing" in tool_names
            assert "search_bookings" in tool_names
            assert "send_guest_message" in tool_names

@pytest.mark.asyncio
async def test_mcp_tool_invocation():
    """Test MCP tool invocation."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Invoke tool
            result = await session.call_tool(
                "get_listing",
                arguments={"listing_id": 123}
            )

            # Assert result structure
            assert result.content[0].type == "text"
            data = json.loads(result.content[0].text)
            assert data["success"] is True
            assert "listing" in data
```

#### 3. End-to-End Tests

`tests/e2e/test_booking_workflow.py`:

```python
"""End-to-end tests for booking workflow."""
import pytest
from datetime import date, timedelta

@pytest.mark.e2e
async def test_complete_booking_workflow(mcp_client):
    """Test complete booking workflow through MCP."""

    # Step 1: Search for available listings
    search_result = await mcp_client.call_tool(
        "search_bookings",
        arguments={
            "filters": {
                "check_in_from": str(date.today()),
                "check_in_to": str(date.today() + timedelta(days=30)),
                "status": "confirmed"
            }
        }
    )
    assert search_result.success

    # Step 2: Get specific listing details
    listing_id = search_result.data["bookings"][0]["listing_id"]
    listing_result = await mcp_client.call_tool(
        "get_listing",
        arguments={"listing_id": listing_id}
    )
    assert listing_result.success

    # Step 3: Send message to guest
    booking_id = search_result.data["bookings"][0]["id"]
    message_result = await mcp_client.call_tool(
        "send_guest_message",
        arguments={
            "booking_id": booking_id,
            "channel": "email",
            "subject": "Check-in Instructions",
            "message": "Welcome! Here are your check-in instructions..."
        }
    )
    assert message_result.success
```

#### 4. Load Testing

`tests/performance/test_load.py`:

```python
"""Load testing for MCP server."""
import asyncio
import time
from locust import HttpUser, task, between

class MCPServerUser(HttpUser):
    """Simulated MCP client user."""

    wait_time = between(1, 3)

    @task(3)
    def get_listing(self):
        """Simulate getting listing (most common operation)."""
        self.client.get(
            "/api/v1/listings/123",
            headers={"X-API-Key": "test-key"}
        )

    @task(2)
    def search_bookings(self):
        """Simulate booking search."""
        self.client.post(
            "/api/v1/bookings/search",
            json={"filters": {"status": "confirmed"}},
            headers={"X-API-Key": "test-key"}
        )

    @task(1)
    def send_message(self):
        """Simulate message sending (less common)."""
        self.client.post(
            "/api/v1/guests/messages/send",
            json={
                "booking_id": 123,
                "channel": "email",
                "subject": "Test",
                "message": "Test message"
            },
            headers={"X-API-Key": "test-key"}
        )

# Run with: locust -f tests/performance/test_load.py --host=http://localhost:8000
```

---

## Examples

### Example 1: Simple Authenticated Endpoint

Complete example of a simple listing retrieval tool:

```python
"""
Complete example: Simple listing retrieval with authentication.
File: src/api/routes/listings_simple.py
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

# Router setup
router = APIRouter()

# Models
class SimpleListing(BaseModel):
    """Minimal listing information."""
    id: int
    name: str
    address: str
    max_guests: int

class SimpleListingResponse(BaseModel):
    """Response for simple listing retrieval."""
    listing: SimpleListing
    success: bool = True

# Authentication dependency
from fastapi.security import APIKeyHeader
from src.mcp.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_key(key: str = Depends(api_key_header)) -> str:
    """Verify API key."""
    if key not in settings.allowed_api_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return key

# Endpoint
@router.get(
    "/{listing_id}",
    response_model=SimpleListingResponse,
    dependencies=[Depends(verify_key)],
    summary="Get listing",
    description="Retrieve basic information about a Hostaway listing",
)
async def get_simple_listing(
    listing_id: int = Field(..., gt=0, description="Listing ID"),
):
    """
    Get basic listing information by ID.

    This tool returns essential property details including name,
    address, and guest capacity.
    """
    # In real implementation, fetch from Hostaway API
    listing_data = {
        "id": listing_id,
        "name": "Cozy Downtown Apartment",
        "address": "456 Main St, Apt 3B",
        "max_guests": 4,
    }

    return SimpleListingResponse(listing=SimpleListing(**listing_data))
```

**Usage in AI Client:**

```python
# AI client code
from mcp import ClientSession

async with ClientSession(read, write) as session:
    await session.initialize()

    # Call the tool
    result = await session.call_tool(
        "get_simple_listing",
        arguments={"listing_id": 12345}
    )

    print(result)
    # Output: {"listing": {"id": 12345, "name": "Cozy Downtown Apartment", ...}, "success": true}
```

### Example 2: Complex Tool with Multiple Parameters

Comprehensive booking creation tool:

```python
"""
Complete example: Complex booking creation with validation.
File: src/api/routes/bookings_complex.py
"""
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

router = APIRouter()

# Request models
class GuestInfo(BaseModel):
    """Guest information."""
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    phone: str = Field(..., pattern=r'^\+?1?\d{9,15}$')
    num_adults: int = Field(..., ge=1, le=20)
    num_children: int = Field(default=0, ge=0, le=10)

class PaymentInfo(BaseModel):
    """Payment details."""
    total_amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", pattern=r'^[A-Z]{3}$')
    payment_method: str = Field(..., pattern=r'^(card|bank_transfer|cash)$')
    deposit_amount: Optional[float] = Field(None, ge=0)

class CreateBookingRequest(BaseModel):
    """Request to create a new booking."""
    listing_id: int = Field(..., gt=0)
    check_in: date = Field(...)
    check_out: date = Field(...)
    guest: GuestInfo
    payment: PaymentInfo
    special_requests: Optional[str] = Field(None, max_length=1000)
    source: str = Field(default="direct", pattern=r'^(direct|airbnb|booking_com|vrbo)$')

    @model_validator(mode='after')
    def validate_dates(self):
        """Ensure check-out is after check-in."""
        if self.check_out <= self.check_in:
            raise ValueError("Check-out must be after check-in")

        # Check minimum stay (1 night)
        stay_duration = (self.check_out - self.check_in).days
        if stay_duration < 1:
            raise ValueError("Minimum stay is 1 night")

        # Check not in the past
        if self.check_in < date.today():
            raise ValueError("Check-in date cannot be in the past")

        return self

    @field_validator('guest')
    def validate_guest_count(cls, v):
        """Validate total guest count."""
        total_guests = v.num_adults + v.num_children
        if total_guests < 1:
            raise ValueError("At least one guest required")
        if total_guests > 30:
            raise ValueError("Maximum 30 guests allowed")
        return v

# Response models
class BookingDetails(BaseModel):
    """Created booking details."""
    booking_id: int
    confirmation_code: str
    listing_id: int
    guest_name: str
    check_in: date
    check_out: date
    total_amount: float
    status: str
    created_at: datetime

class CreateBookingResponse(BaseModel):
    """Response for booking creation."""
    booking: BookingDetails
    success: bool = True
    message: str = "Booking created successfully"

# Endpoint
@router.post(
    "/create",
    response_model=CreateBookingResponse,
    status_code=201,
    dependencies=[Depends(verify_key)],
    summary="Create new booking",
)
async def create_booking(
    request: CreateBookingRequest,
    client: HostawayClient = Depends(),
):
    """
    Create a new booking in Hostaway.

    This tool creates a complete booking with guest information,
    dates, and payment details. It performs comprehensive validation
    including:
    - Date validation (check-in/check-out, minimum stay)
    - Guest capacity verification
    - Payment amount validation
    - Listing availability check

    The booking will be created with "pending" status and requires
    payment confirmation before being confirmed.

    Returns:
        Booking details including confirmation code and booking ID

    Raises:
        400: Invalid booking data or dates
        404: Listing not found or unavailable
        409: Dates conflict with existing booking
        500: Hostaway API error
    """
    try:
        # Check listing availability
        available = await client.check_availability(
            listing_id=request.listing_id,
            check_in=request.check_in,
            check_out=request.check_out,
        )

        if not available:
            raise HTTPException(
                status_code=409,
                detail="Listing not available for selected dates"
            )

        # Verify listing capacity
        listing = await client.get_listing(request.listing_id)
        total_guests = request.guest.num_adults + request.guest.num_children

        if total_guests > listing["max_guests"]:
            raise HTTPException(
                status_code=400,
                detail=f"Listing capacity is {listing['max_guests']} guests"
            )

        # Create booking in Hostaway
        booking_data = await client.create_booking(
            listing_id=request.listing_id,
            check_in=request.check_in.isoformat(),
            check_out=request.check_out.isoformat(),
            guest_first_name=request.guest.first_name,
            guest_last_name=request.guest.last_name,
            guest_email=request.guest.email,
            guest_phone=request.guest.phone,
            num_adults=request.guest.num_adults,
            num_children=request.guest.num_children,
            total_amount=request.payment.total_amount,
            currency=request.payment.currency,
            source=request.source,
            special_requests=request.special_requests,
        )

        # Format response
        booking_details = BookingDetails(
            booking_id=booking_data["id"],
            confirmation_code=booking_data["confirmationCode"],
            listing_id=request.listing_id,
            guest_name=f"{request.guest.first_name} {request.guest.last_name}",
            check_in=request.check_in,
            check_out=request.check_out,
            total_amount=request.payment.total_amount,
            status=booking_data["status"],
            created_at=datetime.fromisoformat(booking_data["createdAt"]),
        )

        return CreateBookingResponse(
            booking=booking_details,
            message=f"Booking {booking_details.confirmation_code} created successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create booking: {str(e)}"
        )
```

**AI Tool Usage:**

```json
{
  "tool": "create_booking",
  "arguments": {
    "listing_id": 12345,
    "check_in": "2025-12-01",
    "check_out": "2025-12-05",
    "guest": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "phone": "+12025551234",
      "num_adults": 2,
      "num_children": 1
    },
    "payment": {
      "total_amount": 850.00,
      "currency": "USD",
      "payment_method": "card",
      "deposit_amount": 200.00
    },
    "special_requests": "Early check-in if possible",
    "source": "direct"
  }
}
```

### Example 3: Resource and Prompt Exposure

FastAPI-MCP primarily focuses on tools (endpoints), but you can expose resources and prompts using MCP's resource and prompt protocols:

```python
"""
Example: Exposing resources and prompts alongside tools.
File: src/mcp/resources.py
"""
from typing import List
from fastapi_mcp import FastApiMCP
from mcp.server.models import Resource, Prompt, PromptMessage

async def register_resources(mcp: FastApiMCP):
    """Register MCP resources."""

    @mcp.resource("hostaway://listings/schema")
    async def listing_schema() -> str:
        """Return listing data schema."""
        return """{
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "address": {"type": "string"},
                "max_guests": {"type": "integer"}
            }
        }"""

    @mcp.resource("hostaway://config/rate-limits")
    async def rate_limits() -> str:
        """Return current rate limit configuration."""
        return f"""
        Rate Limits:
        - Requests per minute: {settings.rate_limit_per_minute}
        - Enabled: {settings.rate_limit_enabled}
        """

async def register_prompts(mcp: FastApiMCP):
    """Register MCP prompts."""

    @mcp.prompt("check-in-instructions")
    async def check_in_instructions_prompt(
        listing_name: str,
        check_in_time: str,
        access_code: str,
    ) -> List[PromptMessage]:
        """Generate check-in instructions prompt."""
        return [
            PromptMessage(
                role="user",
                content=f"""
Generate friendly check-in instructions for a guest at {listing_name}.

Details:
- Check-in time: {check_in_time}
- Access code: {access_code}

Include:
1. Warm welcome message
2. Directions to property
3. Access instructions
4. Emergency contacts
5. Local recommendations
"""
            )
        ]

    @mcp.prompt("booking-confirmation")
    async def booking_confirmation_prompt(
        guest_name: str,
        listing_name: str,
        check_in: str,
        check_out: str,
    ) -> List[PromptMessage]:
        """Generate booking confirmation email prompt."""
        return [
            PromptMessage(
                role="user",
                content=f"""
Write a booking confirmation email for:

Guest: {guest_name}
Property: {listing_name}
Check-in: {check_in}
Check-out: {check_out}

Include:
- Confirmation of reservation details
- Payment summary
- What to expect next
- Contact information
- Cancellation policy reminder

Tone: Professional but warm and welcoming
"""
            )
        ]

# Register in main server setup
def create_mcp_server():
    """Create MCP server with resources and prompts."""
    app = create_app()
    mcp = FastApiMCP(app)

    # Register resources and prompts
    asyncio.create_task(register_resources(mcp))
    asyncio.create_task(register_prompts(mcp))

    mcp.mount()
    return app
```

**Using Resources:**

```python
# AI client code
result = await session.read_resource("hostaway://listings/schema")
print(result.contents[0].text)  # JSON schema
```

**Using Prompts:**

```python
# AI client code
prompt = await session.get_prompt(
    "check-in-instructions",
    arguments={
        "listing_name": "Beach House Paradise",
        "check_in_time": "3:00 PM",
        "access_code": "1234#"
    }
)
# Use prompt.messages with AI model
```

---

## Troubleshooting

### Common Issues

#### 1. "Tools not appearing in MCP client"

**Symptoms:** MCP client doesn't see your FastAPI endpoints as tools

**Solutions:**
- Verify `mcp.mount()` is called after all routes are registered
- Check endpoint has proper docstring (used as tool description)
- Ensure response_model is set (required for output schema)
- Verify server is running and accessible

```python
# Correct order
app.include_router(router)  # Register routes first
mcp = FastApiMCP(app)
mcp.mount()  # Mount MCP after routes
```

#### 2. "Authentication always fails"

**Symptoms:** All requests return 401/403 errors

**Solutions:**
- Check API keys in `.env` are loaded correctly
- Verify header name matches (`X-API-Key` by default)
- Ensure `MCP_ENABLE_AUTH` is set to `true` (not `True` or `1`)
- Test with auth disabled first: `MCP_ENABLE_AUTH=false`

```bash
# Debug authentication
curl -v http://localhost:8000/api/v1/listings/123 \
  -H "X-API-Key: your-key-here"
```

#### 3. "Async errors / Event loop issues"

**Symptoms:** RuntimeError about event loops, asyncio warnings

**Solutions:**
- Ensure all endpoints are `async def`
- Use `await` for all async operations
- Don't mix sync and async code
- Use proper async HTTP clients (httpx, aiohttp)

```python
# Wrong: Mixing sync/async
@router.get("/listings")
async def get_listings():
    result = requests.get(url)  # Sync call in async function!
    return result.json()

# Correct: Fully async
@router.get("/listings")
async def get_listings():
    async with httpx.AsyncClient() as client:
        result = await client.get(url)
    return result.json()
```

#### 4. "Schema validation errors"

**Symptoms:** MCP client rejects tool calls with schema errors

**Solutions:**
- Ensure all parameters have proper Pydantic types
- Add Field() with descriptions for better schema documentation
- Check for required vs optional parameters
- Test schemas with Pydantic's validation

```python
# Good schema definition
class BookingInput(BaseModel):
    listing_id: int = Field(..., gt=0, description="Listing ID")
    check_in: date = Field(..., description="Check-in date (YYYY-MM-DD)")
    optional_note: Optional[str] = Field(None, max_length=500)
```

### Getting Help

**Resources:**
- FastAPI-MCP Documentation: https://fastapi-mcp.tadata.com/
- FastAPI-MCP GitHub: https://github.com/tadata-org/fastapi_mcp
- MCP Specification: https://modelcontextprotocol.io/
- FastAPI Documentation: https://fastapi.tiangolo.com/

**When reporting issues:**
1. Include FastAPI-MCP version: `pip show fastapi-mcp`
2. Provide minimal reproduction code
3. Include error messages and stack traces
4. Show MCP client logs if available
5. Describe expected vs actual behavior

---

## Appendix

### Quick Reference

#### Key Commands

```bash
# Installation
uv add fastapi-mcp

# Run development server
uvicorn src.mcp.server:mcp_app --reload

# Run production server
gunicorn src.mcp.server:mcp_app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Test API endpoint
curl -X GET http://localhost:8000/api/v1/listings/123 -H "X-API-Key: your-key"

# View OpenAPI docs
open http://localhost:8000/docs
```

#### Essential Imports

```python
# FastAPI core
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query, Path, Body

# FastAPI-MCP
from fastapi_mcp import FastApiMCP

# Pydantic models
from pydantic import BaseModel, Field, field_validator, model_validator

# Authentication
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

# Async HTTP
import httpx
```

#### Configuration Checklist

- [ ] Python 3.12 installed
- [ ] fastapi-mcp package installed
- [ ] Environment variables configured (.env file)
- [ ] API keys secured (not in version control)
- [ ] Authentication enabled for production
- [ ] Rate limiting configured
- [ ] Logging configured
- [ ] Error handling implemented
- [ ] Tests written and passing
- [ ] Documentation updated

### File Path Reference

All file paths used in this guide:

- `/Users/darrenmorgan/AI_Projects/hostaway-mcp/src/api/main.py` - Main FastAPI app
- `/Users/darrenmorgan/AI_Projects/hostaway-mcp/src/mcp/server.py` - MCP server setup
- `/Users/darrenmorgan/AI_Projects/hostaway-mcp/src/mcp/config.py` - Configuration
- `/Users/darrenmorgan/AI_Projects/hostaway-mcp/src/mcp/auth.py` - Authentication
- `/Users/darrenmorgan/AI_Projects/hostaway-mcp/src/api/routes/listings.py` - Listings endpoints
- `/Users/darrenmorgan/AI_Projects/hostaway-mcp/src/api/routes/bookings.py` - Bookings endpoints
- `/Users/darrenmorgan/AI_Projects/hostaway-mcp/src/api/routes/guests.py` - Guest endpoints
- `/Users/darrenmorgan/AI_Projects/hostaway-mcp/src/services/hostaway_client.py` - Hostaway client
- `/Users/darrenmorgan/AI_Projects/hostaway-mcp/.env` - Environment variables
- `/Users/darrenmorgan/AI_Projects/hostaway-mcp/tests/` - Test directory

---

## Conclusion

FastAPI-MCP provides a powerful, zero-refactoring path to exposing your Hostaway integration as AI-callable tools. By following this guide, you can:

1. **Rapidly prototype** MCP servers using familiar FastAPI patterns
2. **Maintain type safety** through Pydantic models and automatic schema generation
3. **Secure your tools** with FastAPI's robust authentication system
4. **Scale efficiently** using ASGI transport and async patterns
5. **Test thoroughly** with standard FastAPI testing tools

### Next Steps

1. **Install FastAPI-MCP** in your hostaway-mcp project
2. **Create a simple endpoint** and verify it appears as an MCP tool
3. **Add authentication** using the patterns in this guide
4. **Build out your Hostaway tools** (listings, bookings, guests)
5. **Test with an MCP client** (Claude Desktop, custom client)
6. **Deploy to production** using Docker or your preferred platform

### Additional Resources

- **Example Projects**: Check `/examples` directory for complete working examples
- **API Reference**: See `/docs/API_REFERENCE.md` for detailed API documentation
- **Architecture Guide**: Read `/docs/ARCHITECTURE.md` for system design patterns
- **Deployment Guide**: See `/docs/DEPLOYMENT.md` for production deployment strategies

---

**Document Version:** 1.0.0
**Last Updated:** 2025-10-12
**Author:** Technical Documentation Team
**Project:** hostaway-mcp
**License:** MIT
