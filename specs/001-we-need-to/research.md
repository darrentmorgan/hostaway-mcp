# Research: Hostaway MCP Server Integration

**Feature Branch**: `001-we-need-to`
**Created**: 2025-10-12
**Status**: Complete

## Executive Summary

This research document evaluates technical approaches for building a FastAPI-based MCP server that integrates with the Hostaway property management API. The focus areas include OAuth 2.0 authentication, rate limiting, async HTTP client configuration, FastAPI-MCP integration patterns, and Hostaway API endpoint mapping.

---

## 1. OAuth 2.0 Implementation Patterns

### Decision: Token-Based Authentication with Automatic Refresh

**Approach**:
- Use OAuth 2.0 Client Credentials Grant flow
- Implement token storage in memory with thread-safe access
- Automatic token refresh before expiration (24-month validity)
- FastAPI dependency injection for token management

**Rationale**:
1. **Hostaway Requirements**: Hostaway uses OAuth 2.0 Client Credentials Grant as the standard authentication method
2. **Long Token Lifetime**: 24-month token validity reduces refresh frequency concerns
3. **Thread Safety**: FastAPI's async nature requires thread-safe token management for concurrent requests
4. **Zero Downtime**: Proactive token refresh ensures uninterrupted service

**Alternatives Considered**:

| Alternative | Why Rejected |
|------------|--------------|
| API Key Only | Hostaway requires OAuth 2.0; not supported |
| User-Based OAuth | Not applicable for server-to-server integration |
| Token per Request | Inefficient; wastes API calls and adds latency |
| External Token Store (Redis) | Over-engineering for single-tenant deployment |

**Implementation Notes**:

```python
# Authentication endpoint
POST https://api.hostaway.com/v1/accessTokens
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
client_id={HOSTAWAY_ACCOUNT_ID}
client_secret={HOSTAWAY_SECRET_KEY}
scope=general
```

**Token Management Strategy**:
1. **Storage**: In-memory singleton with asyncio.Lock for thread safety
2. **Refresh Logic**: Check expiration before each request; refresh if <7 days remaining
3. **FastAPI Integration**: Use `Depends()` to inject authenticated client into route handlers
4. **Error Handling**: Fail fast on invalid credentials; auto-retry on transient token errors

**Key Libraries**:
- `httpx.AsyncClient` for OAuth requests
- `asyncio.Lock` for thread-safe token access
- `pydantic-settings` for secure credential loading from environment

**Security Considerations**:
- Store credentials in environment variables only (never in code/logs)
- Transmit tokens over HTTPS exclusively
- Implement token rotation before expiration to avoid service disruption
- Log authentication events (success/failure) for audit trail

---

## 2. Rate Limiting Strategies

### Decision: Token Bucket Algorithm with Semaphore-Based Concurrency Control

**Approach**:
- Implement Token Bucket algorithm for per-second rate limiting
- Use `asyncio.Semaphore` for concurrent request limiting
- Client-side rate limiting to prevent API lockout
- Separate limits for IP (15 req/10s) and account (20 req/10s)

**Rationale**:
1. **Hostaway Limits**: Dual rate limits (15 per 10s per IP, 20 per 10s per account) require sophisticated client-side enforcement
2. **Token Bucket Advantages**: Smooths burst traffic, allows slight overages, natural fit for async Python
3. **Semaphore for Concurrency**: Prevents overwhelming the API with simultaneous requests from multiple AI sessions
4. **Proactive Prevention**: Client-side limiting is more reliable than handling 429 responses

**Alternatives Considered**:

| Alternative | Why Rejected |
|------------|--------------|
| Fixed Window | Allows bursts at window boundaries; less smooth traffic |
| Sliding Window | More complex to implement; token bucket sufficient for our needs |
| Reactive (429 Handling Only) | Risks API lockout; doesn't prevent issues |
| Server-Side Only | No control; relies on Hostaway's enforcement |

**Implementation Notes**:

```python
# Using aiolimiter for token bucket
from aiolimiter import AsyncLimiter

# Rate limiters
ip_limiter = AsyncLimiter(max_rate=15, time_period=10)  # 15 req per 10s
account_limiter = AsyncLimiter(max_rate=20, time_period=10)  # 20 req per 10s

# Concurrency limiter
concurrency_semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests

async def make_request(client, endpoint):
    async with concurrency_semaphore:
        async with ip_limiter:
            async with account_limiter:
                return await client.get(endpoint)
```

**Rate Limiting Configuration**:
- **IP Rate Limit**: 15 requests per 10 seconds (conservative; actual limit 15/10s)
- **Account Rate Limit**: 20 requests per 10 seconds (conservative; actual limit 20/10s)
- **Concurrency Limit**: 10 simultaneous requests (prevents connection pool exhaustion)
- **Burst Allowance**: Token bucket naturally allows small bursts when tokens available

**Key Libraries**:
- `aiolimiter` - Token bucket implementation with async support
- `asyncio.Semaphore` - Built-in concurrency limiting
- `asyncio.Lock` - Thread-safe rate limiter access

**Monitoring & Adjustment**:
- Log rate limit near-misses (>90% capacity)
- Track 429 responses despite client-side limiting
- Adjust limits based on production traffic patterns
- Consider dynamic limits based on time of day

---

## 3. FastAPI-MCP Integration Patterns

### Decision: Direct Mounting with Purpose-Built Tools

**Approach**:
- Mount MCP server directly to FastAPI app at `/mcp` endpoint
- Use FastAPI's dependency injection for authentication
- Create high-level, purpose-built MCP tools (not 1:1 API endpoint mapping)
- ASGI transport for direct communication (no HTTP overhead)

**Rationale**:
1. **Best Practice 2025**: FastAPI-MCP is designed as a native extension, not a converter
2. **Authentication Integration**: Leverage existing FastAPI `Depends()` for secure tool access
3. **Performance**: ASGI transport eliminates HTTP call overhead between MCP and FastAPI
4. **Maintainability**: Purpose-built tools are clearer for AI agents than raw API endpoints

**Alternatives Considered**:

| Alternative | Why Rejected |
|------------|--------------|
| Separate MCP Deployment | Adds deployment complexity; requires HTTP calls between services |
| Auto-Generate All Endpoints | Overloads toolset; confuses AI with too many low-level options |
| Custom MCP Protocol | Reinventing the wheel; FastAPI-MCP handles this well |
| REST-Only (No MCP) | Doesn't meet requirement for AI-callable tools |

**Implementation Notes**:

```python
# FastAPI app with MCP integration
from fastapi import FastAPI, Depends
from fastapi_mcp import FastMCP

app = FastAPI()
mcp = FastMCP()

# High-level tool example
@mcp.tool()
async def search_available_properties(
    check_in: str,
    check_out: str,
    guests: int = 2,
    client: HostawayClient = Depends(get_authenticated_client)
) -> list[PropertySummary]:
    """Search for available properties in date range.

    This tool combines listing retrieval, availability checking,
    and guest capacity filtering into one AI-friendly operation.
    """
    listings = await client.get_listings()
    available = await client.check_availability(listings, check_in, check_out)
    return [p for p in available if p.capacity >= guests]

# Mount MCP to FastAPI
app.mount("/mcp", mcp.app)
```

**Tool Design Principles**:
1. **High-Level Operations**: Combine multiple API calls into single tools (e.g., "search available properties" vs separate listing/availability calls)
2. **Clear Descriptions**: Every tool has detailed docstrings explaining purpose, parameters, and return values
3. **Selective Exposure**: Only expose endpoints useful and safe for AI agents
4. **Input Validation**: Use Pydantic models for all tool parameters
5. **Error Context**: Return actionable error messages when operations fail

**Authentication Flow**:
```python
# Dependency injection for auth
async def get_authenticated_client() -> HostawayClient:
    token = await token_manager.get_valid_token()
    return HostawayClient(token=token)

# Applied to tools automatically
@mcp.tool()
async def get_booking(
    booking_id: int,
    client: HostawayClient = Depends(get_authenticated_client)
) -> BookingDetails:
    return await client.get_booking(booking_id)
```

**Key Libraries**:
- `fastapi-mcp` (v0.3.0+) - MCP integration for FastAPI
- `fastapi` (v0.115+) - Web framework
- `pydantic` (v2.0+) - Data validation and serialization

**Best Practices Applied**:
1. **Lifespan Management**: Use nested async context managers for proper initialization order
2. **Schema Validation**: MCP Inspector automatically validates tool schemas
3. **Security**: Authenticate all tools via FastAPI dependencies
4. **Logging**: Enable detailed logging for debugging tool invocations
5. **Testing**: Test tool schemas with MCP Inspector before deployment

---

## 4. Hostaway API Endpoints

### Decision: Comprehensive Endpoint Coverage with Priority-Based Implementation

**Approach**:
- Map all critical Hostaway endpoints to MCP tools
- Implement Priority 1 (P1) endpoints first: authentication, listings, bookings
- Use Pydantic models for request/response validation
- Design tools around user scenarios, not raw API structure

**Hostaway API Overview**:

| Category | Endpoints | Response Schema | Priority |
|----------|-----------|-----------------|----------|
| **Authentication** | `POST /v1/accessTokens` | `{access_token, expires_in}` | P1 |
| **Listings** | `GET /listings`<br>`GET /listings/{id}`<br>`POST /listings`<br>`PUT /listings/{id}` | Property details, amenities, pricing, capacity | P1 |
| **Bookings/Reservations** | `GET /reservations`<br>`GET /reservations/{id}`<br>`POST /reservations`<br>`PUT /reservations/{id}` | Guest info, dates, payment status, property link | P1 |
| **Calendar** | `GET /calendar`<br>`POST /calendar/block`<br>`DELETE /calendar/block` | Available/blocked dates, existing reservations | P2 |
| **Guest Communication** | `POST /messages`<br>`GET /conversations` | Message content, delivery channel, history | P2 |
| **Financial** | `GET /financialReports`<br>`GET /reservations/{id}/payments` | Revenue, expenses, payment methods | P3 |

**Key Listing Object Fields**:
```python
class Listing(BaseModel):
    id: int
    name: str
    address: str
    description: str
    capacity: int
    bedrooms: int
    bathrooms: float
    amenities: list[str]
    pricing: PricingInfo
    availability: AvailabilityInfo
    cancellation_policy: str
    images: list[str]
    channel_ids: dict[str, str]  # Airbnb, VRBO, Booking.com
```

**Key Reservation Object Fields**:
```python
class Reservation(BaseModel):
    id: int
    listing_id: int
    guest_id: int
    check_in: date
    check_out: date
    guests: int
    status: str  # confirmed, cancelled, pending, etc.
    total_price: float
    payment_status: str
    booking_source: str
    guest_name: str
    guest_email: str
    guest_phone: str
```

**API Features**:
- **Partial Updates**: Listing endpoint supports partial updates (pass only changed fields)
- **Multi-Channel**: Listings can be synced to Airbnb, VRBO, Booking.com
- **Webhooks**: Available for reservation changes and new messages
- **Pagination**: Large result sets paginated (default 100 items per page)

**Rate Limits (Reiterated)**:
- 15 requests per 10 seconds per IP
- 20 requests per 10 seconds per account
- Access tokens valid for 24 months

**Implementation Priority**:

**Phase 1 (P1) - Core Operations**:
- Authentication (token exchange)
- List all properties
- Get property details
- Search bookings (date range, status filters)
- Get booking details

**Phase 2 (P2) - Enhanced Features**:
- Check calendar availability
- Block/unblock dates
- Send guest messages
- View conversation history

**Phase 3 (P3) - Analytics & Reporting**:
- Financial reports
- Revenue aggregation
- Payment tracking

**Webhook Considerations**:
- Webhooks available for push notifications (reservation updates, new messages)
- Consider implementing webhook receiver for real-time updates
- Reduces polling frequency for calendar/booking changes
- Out of scope for initial implementation; add in future iteration

---

## 5. Async HTTP Client Best Practices

### Decision: httpx.AsyncClient with Connection Pooling and Retry Logic

**Approach**:
- Use `httpx.AsyncClient` as singleton with connection pooling
- Configure connection limits based on rate limits
- Implement exponential backoff with jitter for retry logic
- Set appropriate timeouts for external API calls

**Rationale**:
1. **Connection Pooling**: Reusing connections reduces latency and overhead
2. **Async Native**: httpx designed for asyncio; integrates seamlessly with FastAPI
3. **Retry Logic**: Transient network errors are common; automatic retries improve reliability
4. **Resource Management**: Proper limits prevent resource exhaustion under load

**Alternatives Considered**:

| Alternative | Why Rejected |
|------------|--------------|
| requests (sync) | Blocking; incompatible with FastAPI async handlers |
| aiohttp | Less mature; httpx has better type hints and simpler API |
| urllib3 | Too low-level; requires manual async handling |
| Multiple Client Instances | Defeats connection pooling; wastes resources |

**Implementation Notes**:

```python
import httpx
from httpx import Limits, Timeout

# Connection pool configuration
limits = Limits(
    max_keepalive_connections=20,  # Reuse up to 20 connections
    max_connections=50,            # Total connection limit
    keepalive_expiry=30.0          # Close idle connections after 30s
)

# Timeout configuration
timeout = Timeout(
    connect=5.0,   # 5s to establish connection
    read=30.0,     # 30s to read response
    write=10.0,    # 10s to send request
    pool=5.0       # 5s to acquire connection from pool
)

# Singleton async client
client = httpx.AsyncClient(
    base_url="https://api.hostaway.com/v1",
    limits=limits,
    timeout=timeout,
    http2=True,  # Enable HTTP/2 for multiplexing
    follow_redirects=True
)
```

**Retry Logic with Exponential Backoff**:

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    reraise=True
)
async def make_api_request(endpoint: str, **kwargs):
    async with rate_limiters:
        response = await client.get(endpoint, **kwargs)
        response.raise_for_status()
        return response.json()
```

**Retry Strategy Details**:
- **Attempts**: Retry up to 3 times (total 4 attempts including initial)
- **Backoff**: Exponential with base 2 seconds (2s, 4s, 8s)
- **Max Delay**: Cap at 10 seconds to avoid excessive waits
- **Jitter**: Add randomness to prevent thundering herd (built into tenacity)
- **Retry Conditions**: Only retry on network/timeout errors, not on 4xx client errors
- **Final Failure**: Re-raise exception if all retries exhausted

**Timeout Strategy**:
- **Connect**: 5 seconds (reasonable for API)
- **Read**: 30 seconds (some endpoints may be slow)
- **Write**: 10 seconds (requests are small)
- **Pool**: 5 seconds (fail fast if no connections available)

**Connection Pool Sizing**:
- **Max Connections (50)**: Based on concurrent semaphore limit (10) with safety margin
- **Keep-Alive (20)**: Matches expected concurrent usage; reduces connection overhead
- **Keep-Alive Expiry (30s)**: Balances resource usage with connection freshness

**Error Handling**:

```python
# Distinguish error types
try:
    response = await make_api_request("/listings")
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        # Rate limit exceeded (shouldn't happen with client-side limiting)
        log.error("Rate limit exceeded despite client-side limiting")
        raise RateLimitError("Too many requests")
    elif e.response.status_code == 401:
        # Authentication failure
        await token_manager.invalidate_token()
        raise AuthenticationError("Invalid or expired token")
    else:
        raise APIError(f"HTTP {e.response.status_code}: {e.response.text}")
except httpx.TimeoutException:
    # All retries exhausted
    raise APIError("Request timed out after retries")
except httpx.NetworkError:
    # Network connectivity issues
    raise APIError("Network error; check connectivity")
```

**Key Libraries**:
- `httpx` (v0.27+) - Async HTTP client with HTTP/2 support
- `tenacity` (v8.0+) - Retry logic with exponential backoff
- `aiolimiter` - Rate limiting (from section 2)

**Performance Considerations**:
- **Connection Reuse**: Keep-alive connections reduce latency by ~50ms per request
- **HTTP/2 Multiplexing**: Multiple requests over single connection
- **Connection Pool Warmup**: Pre-establish connections on startup (optional)
- **Monitoring**: Track connection pool metrics (active, idle, wait time)

**Resource Cleanup**:
```python
# Proper shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()  # Close all connections gracefully
```

---

## Implementation Recommendations

### Priority 1: Foundation (Week 1)
1. **Authentication System**
   - OAuth 2.0 token exchange
   - Token storage with thread-safe access
   - Automatic refresh logic
   - FastAPI dependency for authenticated client

2. **HTTP Client Setup**
   - Configure httpx.AsyncClient singleton
   - Implement connection pooling
   - Add retry logic with exponential backoff
   - Set appropriate timeouts

3. **Rate Limiting**
   - Token bucket implementation with aiolimiter
   - Semaphore-based concurrency control
   - Monitoring for rate limit violations

### Priority 2: Core Tools (Week 2)
4. **Property Management Tools**
   - `list_listings` - Retrieve all properties
   - `get_listing` - Get property details
   - `check_availability` - Calendar availability

5. **Booking Management Tools**
   - `search_bookings` - Filter by date/status/property
   - `get_booking` - Retrieve booking details
   - `get_booking_guest` - Guest information

### Priority 3: Communication & Analytics (Week 3)
6. **Guest Communication**
   - `send_guest_message` - Email/SMS/platform messaging
   - `get_conversation_history` - Message thread

7. **Financial & Calendar**
   - `get_financial_report` - Revenue/expenses
   - `block_dates` - Calendar management

### Testing Strategy
- **Unit Tests**: Mock HTTP responses for fast testing
- **Integration Tests**: Use Hostaway sandbox environment
- **Load Tests**: Verify rate limiting under concurrent load
- **Security Tests**: Validate credential handling and token refresh

### Monitoring & Observability
- **Metrics to Track**:
  - Token refresh frequency and failures
  - Rate limit capacity usage (percentage)
  - API latency percentiles (p50, p95, p99)
  - Retry rates by error type
  - Connection pool utilization

- **Logging**:
  - All authentication events
  - Rate limit near-misses
  - Tool invocations with parameters (sanitized)
  - API errors with full context

### Deployment Considerations
- **Environment Variables**:
  - `HOSTAWAY_ACCOUNT_ID` - OAuth client ID
  - `HOSTAWAY_SECRET_KEY` - OAuth client secret
  - `RATE_LIMIT_IP` - IP rate limit (default 15/10s)
  - `RATE_LIMIT_ACCOUNT` - Account rate limit (default 20/10s)
  - `LOG_LEVEL` - Logging verbosity (default INFO)

- **Infrastructure**:
  - Deploy behind HTTPS load balancer
  - Use secrets manager for credentials (AWS Secrets Manager, HashiCorp Vault)
  - Enable health check endpoint (`/health`)
  - Configure graceful shutdown for connection cleanup

- **Scaling**:
  - Horizontal scaling limited by account rate limit (20 req/10s)
  - Consider multiple Hostaway accounts for higher throughput
  - Use distributed rate limiting (Redis) for multi-instance deployments

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Hostaway API Downtime** | High | Implement circuit breaker; return cached data; clear error messages |
| **Rate Limit Exhaustion** | Medium | Client-side enforcement; monitoring alerts; request queuing |
| **Token Expiration During Operation** | Low | Proactive refresh; automatic retry with new token |
| **Connection Pool Exhaustion** | Medium | Semaphore limits; connection pool sizing; monitoring |
| **Slow API Responses** | Medium | Appropriate timeouts; async operations; status feedback to AI |
| **Credential Leakage** | High | Environment variables only; no logging; secrets rotation |

---

## Open Questions

1. **Webhook Implementation**: Should we implement webhook receiver for real-time updates, or rely on polling?
   - *Recommendation*: Start with polling; add webhooks in iteration 2 if needed

2. **Multi-Tenant Support**: Should the server support multiple Hostaway accounts?
   - *Recommendation*: Single account per deployment for MVP; multi-tenant in future if demand exists

3. **Caching Strategy**: Should we cache property/booking data to reduce API calls?
   - *Recommendation*: Start without caching; add TTL-based caching if rate limits become constraint

4. **Error Recovery**: How should the system handle partial failures (e.g., 5 of 10 properties retrieved)?
   - *Recommendation*: Return partial results with error context; AI can decide whether to retry

5. **Token Storage**: Should tokens be persisted to disk for server restarts?
   - *Recommendation*: In-memory only for MVP; tokens are long-lived (24 months), re-auth on restart is acceptable

---

## References

1. **Hostaway API Documentation**: https://api.hostaway.com/documentation
2. **FastAPI-MCP GitHub**: https://github.com/tadata-org/fastapi_mcp
3. **MCP Specification**: https://modelcontextprotocol.io/
4. **httpx Documentation**: https://www.python-httpx.org/
5. **OAuth 2.0 RFC 6749**: https://datatracker.ietf.org/doc/html/rfc6749
6. **aiolimiter**: https://github.com/mjpieters/aiolimiter
7. **tenacity**: https://tenacity.readthedocs.io/

---

## Conclusion

The recommended architecture combines:
- **FastAPI-MCP** for native MCP integration with ASGI transport
- **OAuth 2.0** with automatic token refresh and dependency injection
- **Token Bucket + Semaphore** for comprehensive rate limiting
- **httpx.AsyncClient** with connection pooling and retry logic
- **Purpose-Built Tools** that map to user scenarios, not raw API endpoints

This approach balances performance, reliability, maintainability, and security while adhering to FastAPI-MCP best practices and Hostaway API requirements.

**Next Steps**:
1. Proceed to `/speckit.plan` for detailed implementation planning
2. Create data models for Hostaway API responses
3. Define API contracts for MCP tools
4. Generate implementation tasks with `/speckit.tasks`
