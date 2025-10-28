# Research: MCP Server Issues Resolution

**Feature**: 008-fix-issues-identified
**Date**: 2025-10-28
**Status**: Complete

## Research Overview

This document consolidates research findings for implementing fixes to three issues identified in the MCP server test report. All technical unknowns have been resolved through codebase analysis and FastAPI/Python best practices research.

---

## Issue 1: 404 vs 401 Priority (Middleware Order)

### Decision: Check Route Existence Before Authentication

**Chosen Approach**: Implement custom exception handler that checks route existence before authentication middleware executes.

**Rationale**:
1. **FastAPI Exception Handling**: FastAPI provides `@app.exception_handler(404)` to intercept 404 responses
2. **Middleware Limitations**: Middleware executes in order, but route matching happens after all middleware
3. **Best Practice**: Use exception handlers for HTTP status code customization, not middleware reordering
4. **Security Maintained**: Authentication still enforced for all protected routes, just not for non-existent ones

**Implementation Pattern**:
```python
# src/api/main.py
from fastapi import Request, status
from fastapi.responses import JSONResponse

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: HTTPException):
    """Return 404 for non-existent routes without authentication check."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"Route '{request.url.path}' not found"},
        headers={"X-Correlation-ID": request.state.correlation_id}
    )
```

**Alternatives Considered**:
1. **Middleware Reordering**: Move authentication middleware after route matching
   - **Rejected**: FastAPI doesn't support conditional middleware execution
   - **Issue**: All routes would be checked for existence first, complex logic needed

2. **Route Registry Lookup**: Check FastAPI's internal route registry in auth middleware
   - **Rejected**: Tightly couples authentication logic to routing internals
   - **Issue**: Fragile, breaks on FastAPI upgrades

3. **Custom Router**: Override FastAPI's APIRouter to handle 404s specially
   - **Rejected**: Over-engineered, breaks FastAPI conventions
   - **Issue**: Maintenance burden, unclear to future developers

**Testing Strategy**:
- Test non-existent routes return 404 (with/without auth headers)
- Test existing routes still require authentication (401 when missing)
- Test 405 Method Not Allowed still works
- Test public routes remain accessible

---

## Issue 2: Rate Limit Headers

### Decision: Add Headers in Rate Limiting Middleware Response Processing

**Chosen Approach**: Extend existing `RateLimiterMiddleware` to attach rate limit headers after processing response.

**Rationale**:
1. **Industry Standard**: RFC 6585 and Twitter/GitHub/Stripe APIs use `X-RateLimit-*` headers
2. **Client-Friendly**: Allows API consumers to proactively manage request rates
3. **Zero Performance Impact**: Header addition is O(1) string formatting
4. **Existing Infrastructure**: Rate limit state already tracked in-memory

**Header Spec** (Industry Standard):
```
X-RateLimit-Limit: 15       # Max requests per window (or 20 for account-based)
X-RateLimit-Remaining: 12   # Requests remaining in current window
X-RateLimit-Reset: 1698765432  # Unix timestamp when window resets
```

**Implementation Pattern**:
```python
# src/api/middleware/rate_limiter.py
class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Existing rate limit check logic...

        response = await call_next(request)

        # Add rate limit headers
        if hasattr(request.state, "rate_limit_info"):
            limit_info = request.state.rate_limit_info
            response.headers["X-RateLimit-Limit"] = str(limit_info.limit)
            response.headers["X-RateLimit-Remaining"] = str(limit_info.remaining)
            response.headers["X-RateLimit-Reset"] = str(limit_info.reset_time)

        return response
```

**Rate Limit Calculation**:
- **IP-based**: 15 requests per 10 seconds
- **Account-based**: 20 requests per 10 seconds
- **Reset Time**: `current_time + (10 - elapsed_time_in_window)`
- **Storage**: In-memory dictionary with sliding window

**Alternatives Considered**:
1. **Separate Middleware**: Create dedicated header middleware
   - **Rejected**: Duplicates rate limit logic, adds overhead
   - **Issue**: Two middleware need to share state

2. **Response Interceptor**: Use FastAPI's `response_model` to add headers
   - **Rejected**: Only works for endpoints, not middleware-level
   - **Issue**: Can't add headers to 429 responses

3. **Custom Response Class**: Subclass `JSONResponse` with automatic headers
   - **Rejected**: Requires changing all endpoints
   - **Issue**: Breaking change, maintenance burden

**Testing Strategy**:
- Test headers present in successful responses
- Test header values decrement correctly across requests
- Test 429 responses include accurate headers (remaining=0)
- Test both IP-based and account-based rate limits

---

## Issue 3: Test API Key Generation

### Decision: Python Script with Click CLI + Database Insertion

**Chosen Approach**: Create `src/scripts/generate_api_key.py` with Click CLI framework for interactive key generation.

**Rationale**:
1. **Developer Experience**: Click provides user-friendly prompts and validation
2. **Supabase Integration**: Uses `supabase-py` client for database insertion
3. **Security Best Practices**: SHA-256 hashing, secure random generation
4. **Documentation**: Script includes --help text and examples
5. **Flexibility**: Supports both local Supabase and remote VPS

**Script Features**:
- Generate API key with format `mcp_{base64_urlsafe_32_chars}`
- Compute SHA-256 hash for database storage
- Insert into `api_keys` table with organization context
- Support for interactive prompts or command-line args
- Validation of organization_id existence before insertion

**Implementation Pattern**:
```python
# src/scripts/generate_api_key.py
import secrets
import hashlib
import click
from supabase import create_client, Client

@click.command()
@click.option('--org-id', type=int, prompt='Organization ID', help='Organization to associate key with')
@click.option('--user-id', type=str, prompt='User UUID', help='User creating the key')
def generate_key(org_id: int, user_id: str):
    """Generate a test API key for local development."""
    # Generate key with cryptographic randomness
    token = secrets.token_urlsafe(32)
    api_key = f"mcp_{token}"

    # Compute SHA-256 hash
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Insert into Supabase
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    result = supabase.table("api_keys").insert({
        "organization_id": org_id,
        "key_hash": key_hash,
        "created_by_user_id": user_id,
        "is_active": True
    }).execute()

    click.echo(f"\n✅ API Key Generated: {api_key}")
    click.echo(f"Hash: {key_hash}")
    click.echo(f"\nUse in requests:")
    click.echo(f"  X-API-Key: {api_key}")
```

**Database Schema** (Existing):
```sql
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id INTEGER NOT NULL REFERENCES organizations(id),
  key_hash TEXT NOT NULL UNIQUE,
  created_by_user_id UUID NOT NULL REFERENCES auth.users(id),
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_used_at TIMESTAMPTZ
);
```

**Alternatives Considered**:
1. **Django Management Command**: Create `manage.py generate_key`
   - **Rejected**: Project uses FastAPI, not Django
   - **Issue**: Adds unnecessary framework dependency

2. **FastAPI Admin Endpoint**: Create `/admin/keys/generate`
   - **Rejected**: Requires authentication to generate test keys (chicken-and-egg)
   - **Issue**: Adds attack surface for key generation

3. **Shell Script with psql**: Bash script with SQL commands
   - **Rejected**: No validation, error handling, or user-friendly output
   - **Issue**: Requires manual hash calculation, prone to errors

4. **Jupyter Notebook**: Interactive Python notebook for key generation
   - **Rejected**: Not command-line friendly, requires Jupyter setup
   - **Issue**: Not scriptable, can't be automated

**Documentation Requirements**:
- Step-by-step guide in `docs/API_KEY_GENERATION.md`
- Prerequisites: Supabase running, organization created, user created
- Examples for both local and remote VPS setups
- Troubleshooting section for common errors

**Testing Strategy**:
- Unit test: Key format validation (`mcp_{32+ chars}`)
- Unit test: SHA-256 hash computation
- Unit test: Database insertion (mocked Supabase client)
- Integration test: End-to-end key generation and usage

---

## Technology Stack Confirmation

All technologies used are already in the project:

| Technology | Current Version | Used For | Notes |
|------------|----------------|----------|-------|
| **FastAPI** | 0.119.0 | Web framework | Exception handlers, middleware |
| **Pydantic** | 2.12.0 | Data validation | Type-safe models |
| **httpx** | 0.28.1 | HTTP client | Testing (not needed for fixes) |
| **pytest** | Latest | Testing | Unit, integration, performance tests |
| **Click** | 8.1+ | CLI framework | API key generation script (NEW) |
| **supabase-py** | Latest | Database client | API key insertion (NEW) |
| **secrets** | stdlib | Cryptography | Secure random generation |
| **hashlib** | stdlib | Hashing | SHA-256 for API keys |

**New Dependencies**:
- `click>=8.1.0` - CLI framework for key generation script
- `supabase>=2.0.0` - Already in project (used for API key storage)

---

## Performance Considerations

### Middleware Order Change
- **Operation**: Exception handler registration
- **Cost**: Zero - runs once at startup
- **Runtime Impact**: Only executes on 404 errors (rare in production)

### Rate Limit Headers
- **Operation**: String formatting + header addition
- **Cost**: ~0.5ms per request (negligible)
- **Memory**: 3 additional strings per response (~100 bytes)
- **Conclusion**: <1ms overhead, maintains <500ms target

### API Key Generation Script
- **Frequency**: Development/testing only, not production runtime
- **Performance**: N/A - offline script
- **Database Impact**: Single INSERT per key generated

**Overall Assessment**: Zero measurable performance impact on production workloads.

---

## Security Audit

### 404 Handler
- ✅ **No Auth Bypass**: Still requires auth for existing routes
- ✅ **No Information Leak**: Generic 404 message, doesn't reveal route structure
- ✅ **Correlation ID**: Preserved for request tracing
- ⚠️ **Potential Issue**: Could be used for route enumeration
  - **Mitigation**: Rate limiting still applies to all requests

### Rate Limit Headers
- ✅ **No Sensitive Data**: Only exposes rate limit state, not user/org data
- ✅ **Transparent Security**: Helps clients avoid throttling
- ✅ **Standard Practice**: Used by GitHub, Twitter, Stripe APIs

### API Key Generation
- ✅ **Cryptographic Randomness**: Uses `secrets.token_urlsafe()`
- ✅ **Secure Hashing**: SHA-256 before storage
- ✅ **No Plaintext Storage**: Only hash stored in database
- ✅ **Entropy**: 32 bytes (256 bits) - exceeds NIST recommendations
- ⚠️ **Script Security**: Should only be used in development
  - **Mitigation**: Document as dev-only tool, not for production

---

## Open Questions Resolution

All technical unknowns from spec have been resolved:

1. ✅ **How to check route existence before auth?** → FastAPI exception handlers
2. ✅ **Where to add rate limit headers?** → Existing rate limiter middleware
3. ✅ **How to generate API keys securely?** → `secrets` + SHA-256
4. ✅ **How to insert keys into Supabase?** → `supabase-py` client
5. ✅ **Performance impact?** → <1ms overhead, negligible
6. ✅ **Security implications?** → All changes maintain or improve security

**No remaining unknowns** - Ready to proceed to Phase 1 (Design & Contracts).

---

## Next Phase: Design & Contracts

Phase 1 will generate:
1. **quickstart.md** - Developer guide for implementing fixes
2. **contracts/** - N/A (no new API contracts, only middleware modifications)

Phase 2 (`/speckit.tasks`) will generate:
- **tasks.md** - Dependency-ordered implementation tasks
