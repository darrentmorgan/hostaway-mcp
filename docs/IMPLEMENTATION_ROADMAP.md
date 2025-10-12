# Hostaway MCP Server Implementation Roadmap

## Project Overview

**Goal:** Build a FastAPI-based Model Context Protocol (MCP) server that exposes Hostaway property management operations as AI-callable tools.

**Technology Stack:**
- **FastAPI-MCP**: Bridge between FastAPI and MCP protocol
- **Python 3.12**: Runtime environment
- **Spec-Kit**: Spec-driven development workflow
- **Hostaway API**: Property management backend

---

## Phase 1: Project Setup & Foundation

### 1.1 Environment Setup

**Tasks:**
- [x] Install spec-kit and initialize project
- [x] Create .gitignore for sensitive data
- [x] Initialize git repository
- [ ] Set up Python virtual environment
- [ ] Install FastAPI-MCP and dependencies
- [ ] Configure environment variables

**Commands:**
```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
uv add fastapi fastapi-mcp uvicorn httpx pydantic-settings

# Or using pip
pip install fastapi fastapi-mcp uvicorn httpx pydantic-settings
```

**Environment Variables (.env):**
```bash
# Hostaway API Configuration
MCP_HOSTAWAY_API_KEY=your_api_key_here
MCP_HOSTAWAY_ACCOUNT_ID=your_account_id
MCP_HOSTAWAY_BASE_URL=https://api.hostaway.com/v1

# MCP Server Configuration
MCP_SERVER_NAME=hostaway-mcp
MCP_SERVER_VERSION=0.1.0
MCP_ENABLE_AUTH=true
MCP_API_KEY_HEADER=X-API-Key
MCP_ALLOWED_API_KEYS=["dev-key-123"]

# Development
MCP_USE_HTTP_TRANSPORT=true
```

### 1.2 Project Structure

**Create Directory Structure:**
```bash
mkdir -p src/{api/routes,mcp,services,models}
mkdir -p tests/{unit,integration,e2e}
mkdir -p docs
```

**Final Structure:**
```
hostaway-mcp/
├── .claude/                    # Spec-kit commands
├── .specify/                   # Spec-kit templates
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── listings.py    # Listing endpoints
│   │       ├── bookings.py    # Booking endpoints
│   │       └── guests.py      # Guest endpoints
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py          # MCP server setup
│   │   ├── config.py          # Configuration
│   │   └── auth.py            # Authentication
│   ├── services/
│   │   ├── __init__.py
│   │   └── hostaway_client.py # Hostaway API client
│   └── models/
│       ├── __init__.py
│       └── schemas.py         # Pydantic models
├── tests/
├── docs/
│   ├── FASTAPI_MCP_GUIDE.md
│   └── IMPLEMENTATION_ROADMAP.md
├── .env
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## Phase 2: Core MCP Server Implementation

### 2.1 Configuration Module

**File:** `src/mcp/config.py`

**Purpose:** Centralize all configuration using Pydantic settings

**Key Features:**
- Environment variable loading
- Type validation
- Default values
- Secret management

**Implementation Priority:** HIGH

### 2.2 Hostaway API Client

**File:** `src/services/hostaway_client.py`

**Purpose:** Async HTTP client for Hostaway API interactions

**Key Features:**
- Connection pooling
- Retry logic
- Error handling
- Rate limiting awareness

**Implementation Priority:** HIGH

### 2.3 Authentication System

**File:** `src/mcp/auth.py`

**Purpose:** Secure MCP tool access

**Options:**
1. **API Key (Recommended for MVP)**
   - Simple header-based auth
   - Easy to implement
   - Good for initial deployment

2. **OAuth2 (Future)**
   - Token-based authentication
   - Better for multi-user scenarios

**Implementation Priority:** HIGH

### 2.4 Main FastAPI Application

**File:** `src/api/main.py`

**Purpose:** Core FastAPI application with routes

**Key Components:**
- Router registration
- Middleware setup
- Health check endpoint
- CORS configuration

**Implementation Priority:** HIGH

### 2.5 MCP Server Setup

**File:** `src/mcp/server.py`

**Purpose:** Initialize FastAPI-MCP integration

**Key Features:**
- FastAPI app wrapping
- Transport layer selection (HTTP/ASGI)
- Tool registration
- Configuration injection

**Implementation Priority:** HIGH

---

## Phase 3: Hostaway API Endpoints

### 3.1 Listings Module

**File:** `src/api/routes/listings.py`

**Endpoints to Implement:**

1. **GET /listings/{listing_id}**
   - Retrieve single listing details
   - MCP Tool: `get_listing`
   - Priority: HIGH

2. **GET /listings**
   - List all listings with pagination
   - MCP Tool: `list_listings`
   - Priority: HIGH

3. **GET /listings/{listing_id}/availability**
   - Check availability for date range
   - MCP Tool: `check_availability`
   - Priority: MEDIUM

**Models:**
```python
class Listing(BaseModel):
    id: int
    name: str
    address: str
    city: str
    max_guests: int
    bedrooms: int
    bathrooms: int
    property_type: str
```

### 3.2 Bookings Module

**File:** `src/api/routes/bookings.py`

**Endpoints to Implement:**

1. **POST /bookings/search**
   - Search bookings with filters
   - MCP Tool: `search_bookings`
   - Priority: HIGH

2. **GET /bookings/{booking_id}**
   - Get booking details
   - MCP Tool: `get_booking`
   - Priority: HIGH

3. **POST /bookings**
   - Create new booking
   - MCP Tool: `create_booking`
   - Priority: MEDIUM

4. **PATCH /bookings/{booking_id}**
   - Update booking
   - MCP Tool: `update_booking`
   - Priority: LOW

**Models:**
```python
class Booking(BaseModel):
    id: int
    listing_id: int
    guest_name: str
    check_in: date
    check_out: date
    status: str
    total_price: float
    num_guests: int
```

### 3.3 Guests Module

**File:** `src/api/routes/guests.py`

**Endpoints to Implement:**

1. **POST /guests/messages/send**
   - Send message to guest
   - MCP Tool: `send_guest_message`
   - Priority: HIGH

2. **GET /guests/{guest_id}**
   - Get guest details
   - MCP Tool: `get_guest`
   - Priority: MEDIUM

3. **GET /bookings/{booking_id}/messages**
   - Get message history
   - MCP Tool: `get_message_history`
   - Priority: LOW

**Models:**
```python
class MessageChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    AIRBNB = "airbnb"
    BOOKING_COM = "booking_com"

class SendMessageRequest(BaseModel):
    booking_id: int
    channel: MessageChannel
    message: str
    subject: Optional[str] = None
```

---

## Phase 4: Testing & Validation

### 4.1 Unit Tests

**Purpose:** Test individual components in isolation

**Coverage Areas:**
- Pydantic model validation
- Authentication logic
- Hostaway client methods
- Utility functions

**Framework:** pytest + pytest-asyncio

**Example:**
```python
@pytest.mark.asyncio
async def test_get_listing_success(mock_hostaway_client):
    client = HostawayClient()
    listing = await client.get_listing(123)
    assert listing["id"] == 123
```

### 4.2 Integration Tests

**Purpose:** Test FastAPI endpoints with MCP integration

**Coverage Areas:**
- Endpoint responses
- Authentication flow
- Error handling
- MCP tool registration

**Example:**
```python
def test_listing_endpoint_authenticated(test_client):
    response = test_client.get(
        "/api/v1/listings/123",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 200
```

### 4.3 MCP Protocol Tests

**Purpose:** Verify MCP client can discover and call tools

**Coverage Areas:**
- Tool discovery
- Tool invocation
- Schema validation
- Error responses

**Example:**
```python
@pytest.mark.asyncio
async def test_mcp_tool_discovery(mcp_session):
    tools = await mcp_session.list_tools()
    tool_names = [t.name for t in tools.tools]
    assert "get_listing" in tool_names
```

### 4.4 End-to-End Tests

**Purpose:** Test complete workflows through MCP

**Scenarios:**
1. Search → Get → Message workflow
2. Availability check → Booking creation
3. Multi-step guest communication

---

## Phase 5: Deployment & Production

### 5.1 Containerization

**Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy source
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s \
    CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["uv", "run", "uvicorn", "src.mcp.server:mcp_app", \
     "--host", "0.0.0.0", "--port", "8000"]
```

### 5.2 Deployment Options

**Option 1: Docker Compose (Recommended for Dev/Staging)**
- Easy local deployment
- Environment isolation
- Simple configuration

**Option 2: Cloud Platform (Production)**
- AWS Lambda + Mangum (serverless)
- Google Cloud Run (containerized)
- DigitalOcean App Platform (simple)

**Option 3: VPS with Systemd**
- Traditional deployment
- Full control
- Good for dedicated servers

### 5.3 Monitoring & Logging

**Logging Setup:**
```python
import logging
import structlog

# Structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Log MCP tool calls
logger.info("mcp_tool_called",
            tool="get_listing",
            user="api_key_123",
            listing_id=456)
```

**Metrics to Track:**
- Request latency
- Error rates
- Tool usage frequency
- Authentication failures
- Hostaway API response times

---

## Phase 6: Documentation & Maintenance

### 6.1 Documentation

**Required Documentation:**
- [x] FastAPI-MCP integration guide
- [x] Implementation roadmap (this document)
- [ ] API reference (auto-generated from OpenAPI)
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] Security best practices

### 6.2 CI/CD Pipeline

**GitHub Actions Workflow:**
```yaml
name: CI/CD

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install uv
      - run: uv sync
      - run: uv run pytest
      - run: uv run ruff check
      - run: uv run mypy src/

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: ./scripts/deploy.sh
```

---

## Implementation Timeline

### Sprint 1 (Week 1): Foundation
- ✅ Spec-kit setup
- ✅ Git repository initialization
- ⬜ Python environment setup
- ⬜ FastAPI-MCP installation
- ⬜ Project structure creation
- ⬜ Configuration module
- ⬜ Basic FastAPI app

### Sprint 2 (Week 2): Core Features
- ⬜ Hostaway API client
- ⬜ Authentication system
- ⬜ MCP server setup
- ⬜ Listings endpoints (GET)
- ⬜ Basic unit tests

### Sprint 3 (Week 3): Extended Features
- ⬜ Bookings search endpoint
- ⬜ Guest messaging endpoint
- ⬜ Integration tests
- ⬜ MCP protocol tests
- ⬜ Error handling improvements

### Sprint 4 (Week 4): Polish & Deploy
- ⬜ E2E tests
- ⬜ Documentation completion
- ⬜ Docker setup
- ⬜ CI/CD pipeline
- ⬜ Production deployment
- ⬜ Monitoring setup

---

## Success Criteria

### Functional Requirements
- [ ] MCP client can discover all Hostaway tools
- [ ] All tools execute successfully with valid inputs
- [ ] Authentication prevents unauthorized access
- [ ] Error responses are structured and informative
- [ ] All tests pass with >80% coverage

### Non-Functional Requirements
- [ ] Response time < 500ms for most operations
- [ ] Support 100 concurrent requests
- [ ] 99.9% uptime in production
- [ ] Logs are structured and searchable
- [ ] Documentation is complete and accurate

### Security Requirements
- [ ] API keys stored securely (not in code)
- [ ] All inputs validated
- [ ] Rate limiting implemented
- [ ] Audit logging for all tool calls
- [ ] HTTPS required in production

---

## Risk Mitigation

### Risk 1: Hostaway API Rate Limits
**Mitigation:**
- Implement request caching
- Add retry logic with backoff
- Monitor API usage
- Consider request batching

### Risk 2: Authentication Bypass
**Mitigation:**
- Use FastAPI's security dependencies
- Implement API key rotation
- Add IP whitelisting option
- Log all auth attempts

### Risk 3: Schema Changes
**Mitigation:**
- Use Pydantic for validation
- Version API endpoints
- Monitor Hostaway API changes
- Implement schema compatibility tests

### Risk 4: Performance Degradation
**Mitigation:**
- Use async throughout
- Implement connection pooling
- Add response caching
- Load test before production

---

## Next Steps

### Immediate Actions (Today)
1. ✅ Review FastAPI-MCP documentation
2. ⬜ Set up Python virtual environment
3. ⬜ Install FastAPI-MCP dependencies
4. ⬜ Create basic project structure
5. ⬜ Initialize configuration module

### This Week
1. ⬜ Implement Hostaway API client
2. ⬜ Create authentication system
3. ⬜ Build first MCP endpoint (get_listing)
4. ⬜ Test with MCP client (Claude Desktop)
5. ⬜ Write initial unit tests

### This Month
1. ⬜ Complete all core endpoints
2. ⬜ Achieve test coverage goals
3. ⬜ Deploy to staging environment
4. ⬜ Conduct security review
5. ⬜ Prepare for production launch

---

## Integration with Spec-Kit

### Using Spec-Kit Commands

**1. Define Project Constitution:**
```bash
/speckit.constitution
```
Define principles for the Hostaway MCP server:
- API-first design
- Type safety
- Security by default
- Comprehensive testing

**2. Create Feature Specifications:**
```bash
/speckit.specify
```
Specify each feature (listings, bookings, guests) with:
- Requirements
- API contracts
- Success criteria

**3. Generate Implementation Plan:**
```bash
/speckit.plan
```
Create detailed technical plan for each feature

**4. Generate Task Lists:**
```bash
/speckit.tasks
```
Break down into actionable tasks

**5. Execute Implementation:**
```bash
/speckit.implement
```
Use AI to help implement based on specs

---

## Resources

### Documentation
- **FastAPI-MCP Guide:** `/Users/darrenmorgan/AI_Projects/hostaway-mcp/docs/FASTAPI_MCP_GUIDE.md`
- **Implementation Roadmap:** This document
- **Spec-Kit Commands:** `.claude/commands/speckit.*.md`

### External Links
- [FastAPI-MCP Repository](https://github.com/tadata-org/fastapi_mcp)
- [FastAPI-MCP Docs](https://fastapi-mcp.tadata.com/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Hostaway API Docs](https://docs.hostaway.com/)

### Key Files
- Configuration: `src/mcp/config.py`
- MCP Server: `src/mcp/server.py`
- Authentication: `src/mcp/auth.py`
- Hostaway Client: `src/services/hostaway_client.py`

---

## Conclusion

This roadmap provides a structured approach to building a production-ready Hostaway MCP server using FastAPI-MCP. By following this plan, you'll create a secure, scalable, and maintainable system that enables AI assistants to interact with Hostaway property management operations.

**Key Success Factors:**
1. Start with a solid foundation (config, auth, client)
2. Implement incrementally (listings → bookings → guests)
3. Test continuously (unit → integration → E2E)
4. Document thoroughly (code, API, deployment)
5. Deploy safely (staging → production)

Ready to begin? Start with Phase 1, Task 1.1: Environment Setup!

---

**Document Version:** 1.0.0
**Last Updated:** 2025-10-12
**Status:** Initial Draft
**Next Review:** After Sprint 1 completion
