# Implementation Plan: Hostaway MCP Server with Authentication

**Branch**: `001-we-need-to` | **Date**: 2025-10-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-we-need-to/spec.md`

## Summary

Build a FastAPI-based MCP server that enables AI agents to interact with Hostaway's property management platform through authenticated, rate-limited API access. The server exposes OAuth 2.0 authenticated tools for property listings, booking management, guest communication, and financial reporting.

**Technical Approach** (from research):
- OAuth 2.0 Client Credentials Grant with automatic token refresh
- Token Bucket + Semaphore rate limiting (15 req/10s IP, 20 req/10s account)
- httpx.AsyncClient with connection pooling and retry logic
- FastAPI-MCP ASGI transport for direct tool invocation
- Purpose-built MCP tools mapped to user scenarios

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: FastAPI 0.100+, fastapi-mcp 0.4+, httpx 0.27+, Pydantic 2.0+
**Storage**: In-memory (OAuth tokens), no database required
**Testing**: pytest + pytest-asyncio, httpx mocking, MCP protocol tests
**Target Platform**: Linux server / Docker container
**Project Type**: Single project (API server with MCP integration)
**Performance Goals**: <500ms API response (p95), <1s MCP tool invocation, 100+ concurrent requests
**Constraints**: 15 req/10s per IP, 20 req/10s per account (Hostaway rate limits), <100MB memory per worker
**Scale/Scope**: Single Hostaway account, 5-8 core MCP tools, ~1000 lines of application code

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: API-First Design ✅

**Compliance**: PASS
- All MCP tools exposed as FastAPI endpoints first
- Each endpoint has explicit `operation_id`
- Pydantic models for all request/response
- Comprehensive docstrings for tool descriptions
- Tags used for logical grouping (auth, listings, bookings, guests)

### Principle II: Type Safety (NON-NEGOTIABLE) ✅

**Compliance**: PASS
- Full type annotations for all functions and methods
- Pydantic models with `Field` constraints for validation
- pydantic-settings for configuration management
- mypy --strict enforcement planned in pre-commit hooks
- All API responses type-validated via Pydantic

### Principle III: Security by Default ✅

**Compliance**: PASS
- OAuth 2.0 authentication via FastAPI `Depends()`
- Input validation with Pydantic `Field` constraints
- Environment variables for all credentials (no hardcoding)
- Rate limiting enforced client-side
- Audit logging for all MCP tool invocations
- HTTPS-only token transmission
- Error messages sanitized (no credential leakage)

### Principle IV: Test-Driven Development ✅

**Compliance**: PASS
- Unit tests for all Pydantic models and business logic
- Integration tests for FastAPI endpoints
- MCP protocol tests for tool discovery/invocation
- E2E tests for critical workflows (auth → list → search)
- Target: 80% line coverage, 70% branch coverage
- Mock Hostaway API responses for isolated testing

### Principle V: Async Performance ✅

**Compliance**: PASS
- All endpoints defined as `async def`
- httpx.AsyncClient for all external API calls
- No database (avoiding async driver complexity)
- Connection pooling (50 max, 20 keep-alive)
- No blocking I/O operations
- Performance target: <1s MCP tool response

**Gate Result**: ✅ **PASS** - All constitutional principles satisfied

## Project Structure

### Documentation (this feature)

```
specs/001-we-need-to/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output (COMPLETE)
├── data-model.md        # Phase 1 output (see below)
├── quickstart.md        # Phase 1 output (see below)
├── contracts/           # Phase 1 output (see below)
│   ├── authentication.yaml
│   ├── listings.yaml
│   ├── bookings.yaml
│   └── guests.yaml
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```
src/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   └── routes/
│       ├── __init__.py
│       ├── listings.py      # Property listing endpoints
│       ├── bookings.py      # Booking/reservation endpoints
│       └── guests.py        # Guest communication endpoints
├── mcp/
│   ├── __init__.py
│   ├── server.py            # MCP server setup and tool registration
│   ├── config.py            # Configuration via pydantic-settings
│   └── auth.py              # OAuth authentication & token management
├── services/
│   ├── __init__.py
│   ├── hostaway_client.py   # Async Hostaway API client
│   └── rate_limiter.py      # Token bucket + semaphore rate limiting
└── models/
    ├── __init__.py
    ├── listings.py          # Listing Pydantic models
    ├── bookings.py          # Booking Pydantic models
    ├── guests.py            # Guest Pydantic models
    └── auth.py              # Authentication models

tests/
├── unit/
│   ├── test_models.py       # Pydantic model validation
│   ├── test_auth.py         # Token management logic
│   └── test_rate_limiter.py # Rate limiting logic
├── integration/
│   ├── test_listings_api.py # Listing endpoint tests
│   ├── test_bookings_api.py # Booking endpoint tests
│   └── test_guests_api.py   # Guest endpoint tests
└── mcp/
    ├── test_tool_discovery.py # MCP tool listing
    └── test_tool_invocation.py # MCP tool execution
```

**Structure Decision**: Single project structure (Option 1) selected because:
- No frontend component (MCP tools only)
- API and MCP server integrated in same process
- Simplified deployment (single Docker image)
- FastAPI + MCP in same codebase for tight integration

## Complexity Tracking

*No constitutional violations - this section is empty*

## Phase 0: Outline & Research ✅ COMPLETE

**Status**: Research complete - see [research.md](./research.md)

### Key Decisions Made

1. **OAuth 2.0 Implementation**: Token-based auth with automatic refresh via FastAPI dependency injection
2. **Rate Limiting**: Token Bucket + Semaphore (15 req/10s IP, 20 req/10s account)
3. **HTTP Client**: httpx.AsyncClient singleton with connection pooling (50 max, 20 keep-alive)
4. **MCP Integration**: Direct ASGI mounting with purpose-built tools
5. **Retry Logic**: Exponential backoff (2s, 4s, 8s) with 3 retry attempts

### Technologies Selected

- **Python**: 3.12+
- **Framework**: FastAPI 0.100+
- **MCP**: fastapi-mcp 0.4+
- **HTTP Client**: httpx 0.27+ (async)
- **Validation**: Pydantic 2.0+
- **Config**: pydantic-settings
- **Rate Limiting**: aiolimiter
- **Retry Logic**: tenacity 8.0+
- **Testing**: pytest, pytest-asyncio

## Phase 1: Design & Contracts

### Data Model Design

See [data-model.md](./data-model.md) for complete entity definitions.

**Core Entities**:

1. **HostawayConfig** - OAuth credentials and API settings
2. **AccessToken** - OAuth token with expiration tracking
3. **Listing** - Property details, amenities, pricing, capacity
4. **Booking** - Reservation with guest info, dates, payment status
5. **Guest** - Contact information and communication preferences
6. **Message** - Guest communication with delivery channel
7. **FinancialReport** - Revenue and expense aggregation

### API Contracts

MCP tools organized by domain:

#### Authentication Tools
- `authenticate_hostaway` - Obtain OAuth access token
- `refresh_token` - Manually refresh expiring token (auto-refresh built-in)

#### Listing Tools
- `list_all_properties` - Retrieve all managed properties
- `get_property_details` - Get specific property by ID
- `check_property_availability` - Check calendar for date range

#### Booking Tools
- `search_bookings` - Filter by date, status, property
- `get_booking_details` - Retrieve specific reservation
- `get_booking_guest_info` - Guest contact for booking

#### Guest Communication Tools
- `send_guest_message` - Send via email/SMS/platform
- `get_conversation_history` - Message thread for booking

#### Financial Tools (P3)
- `get_revenue_report` - Financial summary for date range
- `get_property_financials` - Property-specific revenue

See [contracts/](./contracts/) for OpenAPI specifications.

### Quickstart Guide

See [quickstart.md](./quickstart.md) for:
- Environment setup instructions
- Configuration examples
- First MCP tool invocation
- Testing and validation steps

## Phase 2: Implementation Plan (Next Steps)

### Week 1: Foundation

**Authentication & Infrastructure**
1. Set up project structure (`src/`, `tests/`)
2. Implement `HostawayConfig` with pydantic-settings
3. Create `TokenManager` for OAuth flow
4. Build `HostawayClient` with httpx.AsyncClient
5. Implement rate limiting with aiolimiter + Semaphore
6. Add retry logic with tenacity
7. Write unit tests for auth and rate limiting

**Deliverables**:
- ✅ OAuth token exchange working
- ✅ Rate limiting enforced
- ✅ HTTP client configured
- ✅ 80% test coverage

### Week 2: Core MCP Tools

**Property & Booking Management**
1. Define Pydantic models (Listing, Booking)
2. Create FastAPI routes for listings
3. Create FastAPI routes for bookings
4. Register MCP tools via fastapi-mcp
5. Implement tool descriptions and schemas
6. Write integration tests for endpoints
7. Write MCP protocol tests

**Deliverables**:
- ✅ `list_all_properties` MCP tool
- ✅ `get_property_details` MCP tool
- ✅ `search_bookings` MCP tool
- ✅ `get_booking_details` MCP tool
- ✅ All tools tested via MCP protocol

### Week 3: Communication & Analytics

**Guest Communication & Reporting**
1. Define Guest and Message models
2. Create guest communication routes
3. Implement message sending logic
4. Create financial reporting routes
5. Add calendar availability tools
6. Write E2E workflow tests
7. Performance testing and optimization

**Deliverables**:
- ✅ `send_guest_message` MCP tool
- ✅ `get_conversation_history` MCP tool
- ✅ `get_revenue_report` MCP tool
- ✅ E2E tests passing
- ✅ Performance targets met

### Week 4: Deployment & Documentation

**Production Readiness**
1. Create Dockerfile and docker-compose
2. Set up CI/CD pipeline (GitHub Actions)
3. Configure pre-commit hooks (ruff, mypy)
4. Add monitoring and logging
5. Write deployment documentation
6. Create runbook for operations
7. Final security review

**Deliverables**:
- ✅ Docker deployment working
- ✅ CI/CD pipeline passing
- ✅ Pre-commit hooks enforced
- ✅ Documentation complete
- ✅ Production deployment successful

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Hostaway API Downtime** | High | Circuit breaker pattern, cached responses, clear error messages to AI |
| **Rate Limit Exhaustion** | Medium | Client-side enforcement, monitoring alerts, request queuing with backoff |
| **Token Expiration Mid-Request** | Low | Proactive refresh (7 days before expiry), automatic retry with new token |
| **Connection Pool Exhaustion** | Medium | Semaphore limits (10 concurrent), pool sizing (50 max), monitoring |
| **Slow API Responses** | Medium | Timeouts (30s read), async operations, status feedback to AI agent |
| **Credential Leakage** | High | Environment variables only, no logging, secrets rotation capability |

## Success Metrics

### Performance
- ✅ Authentication completes in <5 seconds
- ✅ 100 concurrent requests handled without failures
- ✅ 99% of requests return within 2 seconds
- ✅ Token auto-refresh with zero downtime

### Reliability
- ✅ Zero rate limit violations (client-side enforcement)
- ✅ 95% of auth errors resolved in one retry
- ✅ 99.9% uptime (excluding Hostaway downtime)

### User Value
- ✅ 10+ hours/week saved for property managers
- ✅ 75% faster guest response times
- ✅ 50% more booking inquiries resolved
- ✅ 98% property data accuracy

## Next Commands

1. **Review Plan**: Validate architecture decisions
2. **Generate Tasks**: Run `/speckit.tasks` to create actionable task list
3. **Begin Implementation**: Start with Week 1 foundation tasks
4. **Continuous Testing**: Run tests after each component

---

**Plan Status**: ✅ COMPLETE - Ready for task generation
**Research**: ✅ COMPLETE - See [research.md](./research.md)
**Data Model**: ⏳ PENDING - See below
**Contracts**: ⏳ PENDING - See contracts/ directory
**Quickstart**: ⏳ PENDING - See [quickstart.md](./quickstart.md)
