# Quick Start: Implementing MCP Server Issues Resolution

**Feature**: 008-fix-issues-identified
**Target Developers**: Backend engineers familiar with FastAPI and Python
**Estimated Time**: 4-6 hours for all three issues

---

## Overview

This guide provides step-by-step instructions for implementing fixes to three issues identified in the MCP server test report:

1. **404 vs 401 Priority** - Return 404 for non-existent routes (not 401)
2. **Rate Limit Headers** - Add industry-standard rate limit headers to responses
3. **API Key Generation** - Create CLI script for generating test API keys

---

## Prerequisites

✅ Python 3.12+
✅ FastAPI 0.100+ project setup
✅ Existing middleware: `MCPAuthMiddleware`, `RateLimiterMiddleware`
✅ Supabase database with `api_keys` table
✅ Development environment: `uv` or `pip` for package management

---

## Issue 1: Fix 404 vs 401 Priority

### Problem

Currently, requests to non-existent routes return `401 Unauthorized` instead of `404 Not Found` because authentication middleware executes before route matching.

### Solution

Add a custom 404 exception handler that bypasses authentication.

### Implementation Steps

**Step 1: Open `src/api/main.py`**

Locate the FastAPI app initialization:
```python
app = FastAPI(
    title="Hostaway MCP Server",
    version="0.1.0",
    # ...
)
```

**Step 2: Add 404 Exception Handler**

Add this function after middleware setup:

```python
from fastapi import Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Return 404 for non-existent routes without requiring authentication.

    This handler is invoked BEFORE authentication middleware, ensuring that
    clients receive accurate HTTP status codes even without valid credentials.
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"Route '{request.url.path}' not found"},
        headers={
            "X-Correlation-ID": getattr(request.state, "correlation_id", "unknown"),
            "Access-Control-Allow-Origin": "*",  # Maintain CORS
        },
    )
```

**Step 3: Test the Change**

```bash
# Test non-existent route (should return 404)
curl -i http://localhost:8000/api/nonexistent
# Expected: HTTP/1.1 404 Not Found

# Test existing route without auth (should return 401)
curl -i http://localhost:8000/api/listings
# Expected: HTTP/1.1 401 Unauthorized

# Test with valid auth (should work)
curl -i -H "X-API-Key: mcp_..." http://localhost:8000/api/listings
# Expected: HTTP/1.1 200 OK
```

**Step 4: Add Integration Test**

Create `tests/integration/test_404_vs_401_priority.py`:

```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_nonexistent_route_returns_404():
    """Non-existent routes should return 404, not 401."""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_existing_route_requires_auth():
    """Existing routes should still return 401 without auth."""
    response = client.get("/api/listings")
    assert response.status_code == 401
    assert "api key" in response.json()["detail"].lower()

def test_existing_route_with_invalid_auth():
    """Invalid auth should return 401, not 404."""
    response = client.get(
        "/api/listings",
        headers={"X-API-Key": "invalid-key"}
    )
    assert response.status_code == 401

def test_405_method_not_allowed_still_works():
    """Unsupported methods should return 405, not 404 or 401."""
    response = client.delete("/health")  # DELETE not allowed on /health
    assert response.status_code == 405
```

---

## Issue 2: Add Rate Limit Headers

### Problem

Rate limiting is implemented but not transparent to clients. No headers indicate limit status.

### Solution

Extend `RateLimiterMiddleware` to add `X-RateLimit-*` headers to all responses.

### Implementation Steps

**Step 1: Open `src/api/middleware/rate_limiter.py`**

Locate the `RateLimiterMiddleware` class:

```python
class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Existing rate limit check logic...
        pass
```

**Step 2: Add Header Logic After Rate Limit Check**

Update the `dispatch` method to attach headers:

```python
from datetime import datetime, timezone
from typing import Dict, Any

class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Existing rate limit check logic...
        # (Get client identifier, check limits, etc.)

        # Calculate rate limit info
        client_id = self._get_client_identifier(request)
        limit_info = self._get_rate_limit_info(client_id, request)

        # Store in request state for header addition
        request.state.rate_limit_info = limit_info

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        if hasattr(request.state, "rate_limit_info"):
            info = request.state.rate_limit_info
            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(info["reset_time"])

        return response

    def _get_rate_limit_info(self, client_id: str, request: Request) -> Dict[str, Any]:
        """
        Calculate current rate limit status for client.

        Returns:
            {
                "limit": 15 or 20 (IP-based or account-based),
                "remaining": requests remaining in window,
                "reset_time": Unix timestamp when window resets
            }
        """
        # Determine limit type
        is_authenticated = hasattr(request.state, "organization_id")
        limit = 20 if is_authenticated else 15
        window_seconds = 10

        # Get current usage from in-memory state
        state = self._rate_limit_state.get(client_id, {
            "count": 0,
            "window_start": datetime.now(timezone.utc).timestamp()
        })

        # Calculate remaining and reset time
        current_time = datetime.now(timezone.utc).timestamp()
        time_elapsed = current_time - state["window_start"]

        if time_elapsed > window_seconds:
            # Window expired, reset
            remaining = limit
            reset_time = int(current_time + window_seconds)
        else:
            # Within window
            remaining = max(0, limit - state["count"])
            reset_time = int(state["window_start"] + window_seconds)

        return {
            "limit": limit,
            "remaining": remaining,
            "reset_time": reset_time
        }
```

**Step 3: Update 429 Response Handler**

Ensure 429 responses also include headers:

```python
# In rate limit check logic, when limit exceeded:
if state["count"] >= limit:
    info = self._get_rate_limit_info(client_id, request)
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
        headers={
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(info["reset_time"]),
            "Retry-After": str(info["reset_time"] - int(datetime.now(timezone.utc).timestamp()))
        }
    )
```

**Step 4: Test the Change**

```bash
# Make authenticated request, check headers
curl -i -H "X-API-Key: mcp_..." http://localhost:8000/health

# Expected headers:
# X-RateLimit-Limit: 20
# X-RateLimit-Remaining: 19
# X-RateLimit-Reset: 1698765432

# Make multiple requests to trigger rate limit
for i in {1..25}; do
  curl -i -H "X-API-Key: mcp_..." http://localhost:8000/health
done

# Last response should be 429 with remaining=0
```

**Step 5: Add Unit Tests**

Create `tests/unit/test_rate_limiter_headers.py`:

```python
import pytest
from datetime import datetime, timezone
from src.api.middleware.rate_limiter import RateLimiterMiddleware

def test_rate_limit_info_calculation():
    """Test rate limit info calculation logic."""
    middleware = RateLimiterMiddleware(app=None)

    # Mock request state
    class MockRequest:
        state = type('obj', (object,), {'organization_id': 123})()

    request = MockRequest()
    client_id = "test-client"

    # Get rate limit info
    info = middleware._get_rate_limit_info(client_id, request)

    # Assertions
    assert info["limit"] == 20  # Authenticated
    assert 0 <= info["remaining"] <= 20
    assert info["reset_time"] > datetime.now(timezone.utc).timestamp()

def test_rate_limit_headers_present():
    """Test headers are added to response."""
    # Use TestClient to make request
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    response = client.get("/health")

    # Check headers present
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers

def test_rate_limit_headers_decrement():
    """Test remaining count decrements correctly."""
    client = TestClient(app)

    # First request
    response1 = client.get("/health")
    remaining1 = int(response1.headers["X-RateLimit-Remaining"])

    # Second request
    response2 = client.get("/health")
    remaining2 = int(response2.headers["X-RateLimit-Remaining"])

    # Remaining should decrement
    assert remaining2 == remaining1 - 1
```

---

## Issue 3: Create API Key Generation Script

### Problem

No documented way to generate test API keys for local development.

### Solution

Create a CLI script using Click framework for interactive key generation.

### Implementation Steps

**Step 1: Install Click (if not already installed)**

```bash
uv add click>=8.1.0
# or
pip install click>=8.1.0
```

**Step 2: Create `src/scripts/generate_api_key.py`**

```python
"""
API Key Generation Script for Hostaway MCP Server

Usage:
    python -m src.scripts.generate_api_key --org-id 999 --user-id <uuid>

Generates a test API key with format: mcp_{base64_urlsafe_32_chars}
Stores SHA-256 hash in Supabase api_keys table.
"""

import secrets
import hashlib
import sys
from typing import Optional
import click
from supabase import create_client, Client
from pydantic import ValidationError

@click.command()
@click.option(
    '--org-id',
    type=int,
    prompt='Organization ID',
    help='Organization to associate key with (must exist in organizations table)'
)
@click.option(
    '--user-id',
    type=str,
    prompt='User UUID',
    help='UUID of user creating the key (must exist in auth.users table)'
)
@click.option(
    '--supabase-url',
    type=str,
    envvar='SUPABASE_URL',
    default='http://127.0.0.1:54321',
    help='Supabase URL (default: local instance)'
)
@click.option(
    '--supabase-key',
    type=str,
    envvar='SUPABASE_SERVICE_KEY',
    prompt=True,
    hide_input=True,
    help='Supabase service key (will prompt if not provided)'
)
def generate_key(org_id: int, user_id: str, supabase_url: str, supabase_key: str):
    """Generate a test API key for local development."""

    click.echo("\n🔑 Generating API Key...")
    click.echo("-" * 50)

    # Step 1: Generate cryptographically secure random token
    token = secrets.token_urlsafe(32)
    api_key = f"mcp_{token}"

    # Step 2: Compute SHA-256 hash for storage
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    click.echo(f"✓ Key generated: {api_key[:15]}...{api_key[-10:]}")
    click.echo(f"✓ Hash computed: {key_hash[:16]}...")

    # Step 3: Validate organization exists
    try:
        supabase: Client = create_client(supabase_url, supabase_key)

        click.echo(f"\n🔍 Validating organization {org_id}...")
        org_check = supabase.table("organizations").select("id").eq("id", org_id).execute()

        if not org_check.data:
            click.echo(f"❌ Error: Organization {org_id} not found", err=True)
            click.echo("   Create organization first or use existing ID")
            sys.exit(1)

        click.echo(f"✓ Organization {org_id} exists")

    except Exception as e:
        click.echo(f"❌ Error connecting to Supabase: {e}", err=True)
        sys.exit(1)

    # Step 4: Insert into api_keys table
    try:
        click.echo(f"\n💾 Inserting key into database...")

        result = supabase.table("api_keys").insert({
            "organization_id": org_id,
            "key_hash": key_hash,
            "created_by_user_id": user_id,
            "is_active": True
        }).execute()

        click.echo(f"✓ Key inserted with ID: {result.data[0]['id']}")

    except Exception as e:
        click.echo(f"❌ Error inserting key: {e}", err=True)
        sys.exit(1)

    # Step 5: Display success and usage instructions
    click.echo("\n" + "=" * 50)
    click.echo("✅ API Key Generated Successfully!")
    click.echo("=" * 50)
    click.echo(f"\n🔑 Your API Key (copy this):")
    click.echo(f"   {api_key}")
    click.echo(f"\n📝 Hash (for verification):")
    click.echo(f"   {key_hash}")
    click.echo(f"\n🚀 Usage in API requests:")
    click.echo(f"   curl -H 'X-API-Key: {api_key}' http://localhost:8000/api/listings")
    click.echo(f"\n📋 Key Details:")
    click.echo(f"   Organization ID: {org_id}")
    click.echo(f"   Created By: {user_id}")
    click.echo(f"   Status: Active")
    click.echo("\n⚠️  Store this key securely - it cannot be retrieved later!")
    click.echo()

if __name__ == '__main__':
    generate_key()
```

**Step 3: Create Documentation**

Create `docs/API_KEY_GENERATION.md`:

```markdown
# API Key Generation Guide

## Quick Start

Generate a test API key for local development:

\`\`\`bash
# Using environment variables
export SUPABASE_URL="http://127.0.0.1:54321"
export SUPABASE_SERVICE_KEY="your-service-key"

python -m src.scripts.generate_api_key --org-id 999 --user-id <uuid>
\`\`\`

## Prerequisites

1. Supabase running (local or remote)
2. Organization created in `organizations` table
3. User created in `auth.users` table
4. Supabase service key (from Supabase dashboard)

## Step-by-Step Setup

### 1. Start Supabase (Local Development)

\`\`\`bash
supabase start
\`\`\`

### 2. Create Test Organization

\`\`\`bash
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres <<EOF
INSERT INTO organizations (id, name, owner_user_id)
VALUES (999, 'Test Organization', '00000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO NOTHING;
EOF
\`\`\`

### 3. Generate API Key

\`\`\`bash
python -m src.scripts.generate_api_key \
  --org-id 999 \
  --user-id 00000000-0000-0000-0000-000000000001
\`\`\`

### 4. Test API Key

\`\`\`bash
curl -H "X-API-Key: mcp_..." http://localhost:8000/health
\`\`\`

## Troubleshooting

**Error: Organization not found**
- Create organization first (see step 2 above)

**Error: User not found**
- Create user in auth.users table or use existing UUID

**Error: Connection refused**
- Check Supabase is running: `supabase status`
\`\`\`

**Step 4: Test the Script**

```bash
# Run script
python -m src.scripts.generate_api_key \
  --org-id 999 \
  --user-id 00000000-0000-0000-0000-000000000001

# Expected output:
# 🔑 Generating API Key...
# ✓ Key generated: mcp_C_Fo9M7N5wV...
# ✓ Organization 999 exists
# ✓ Key inserted
# ✅ API Key Generated Successfully!
```

**Step 5: Add Unit Tests**

Create `tests/unit/test_api_key_generation.py`:

```python
import pytest
import hashlib
import re
from src.scripts.generate_api_key import generate_key
from click.testing import CliRunner

def test_api_key_format():
    """Test generated key follows mcp_{base64} format."""
    runner = CliRunner()
    result = runner.invoke(generate_key, [
        '--org-id', '999',
        '--user-id', '00000000-0000-0000-0000-000000000001',
        '--supabase-url', 'http://localhost:54321',
        '--supabase-key', 'test-key'
    ])

    # Extract key from output
    key_pattern = r'mcp_[A-Za-z0-9_-]{32,}'
    matches = re.findall(key_pattern, result.output)

    assert len(matches) > 0, "No API key found in output"
    api_key = matches[0]

    # Validate format
    assert api_key.startswith('mcp_')
    assert len(api_key) > 36  # mcp_ (4 chars) + 32+ chars

def test_sha256_hash_computation():
    """Test SHA-256 hash is computed correctly."""
    test_key = "mcp_test123456789"
    expected_hash = hashlib.sha256(test_key.encode()).hexdigest()

    # Script should compute same hash
    computed_hash = hashlib.sha256(test_key.encode()).hexdigest()
    assert computed_hash == expected_hash
```

---

## Testing All Fixes Together

### Integration Test Suite

Create `tests/integration/test_all_fixes.py`:

```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_404_returns_before_auth_check():
    """Test 1: 404 for non-existent routes."""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404

def test_rate_limit_headers_present():
    """Test 2: Rate limit headers in responses."""
    response = client.get("/health")
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers

def test_api_key_works_after_generation():
    """Test 3: Generated API key works in requests."""
    # Generate key using script
    from src.scripts.generate_api_key import generate_key
    # ... (invoke script)

    # Use key in request
    response = client.get(
        "/api/listings",
        headers={"X-API-Key": "mcp_generated_key_here"}
    )
    assert response.status_code == 200
```

### Performance Test

Create `tests/performance/test_middleware_performance.py`:

```python
import pytest
import time
from fastapi.testclient import TestClient
from src.api.main import app

def test_middleware_performance_no_regression():
    """Ensure middleware changes don't degrade performance."""
    client = TestClient(app)

    # Baseline: measure 100 requests
    start = time.time()
    for _ in range(100):
        response = client.get("/health")
        assert response.status_code == 200
    elapsed = time.time() - start

    # Average response time should be < 5ms (500ms / 100)
    avg_time = elapsed / 100
    assert avg_time < 0.005, f"Performance regression: {avg_time*1000:.2f}ms per request"
```

---

## Deployment Checklist

Before merging:

- [ ] All unit tests pass (`pytest tests/unit/`)
- [ ] All integration tests pass (`pytest tests/integration/`)
- [ ] Performance tests pass (`pytest tests/performance/`)
- [ ] Type checking passes (`mypy --strict src/`)
- [ ] Linting passes (`ruff check src/`)
- [ ] Documentation updated (`docs/API_KEY_GENERATION.md`)
- [ ] Pre-commit hooks pass
- [ ] Manual testing completed:
  - [ ] 404 for non-existent routes
  - [ ] Rate limit headers visible in curl
  - [ ] API key script works end-to-end

---

## Troubleshooting

**Issue: 404 handler not triggering**
- Check handler is registered AFTER middleware setup
- Verify exception handler syntax: `@app.exception_handler(404)`

**Issue: Rate limit headers missing**
- Check `request.state.rate_limit_info` is set before `call_next()`
- Verify headers are added AFTER response is generated

**Issue: API key script fails**
- Check Supabase is running: `supabase status`
- Verify organization and user exist in database
- Check service key has proper permissions

---

## Estimated Time Breakdown

| Task | Time | Difficulty |
|------|------|------------|
| Issue 1: 404 handler | 1 hour | Easy |
| Issue 2: Rate limit headers | 2 hours | Medium |
| Issue 3: API key script | 2 hours | Medium |
| Testing (all issues) | 1 hour | Easy |
| **Total** | **6 hours** | **Medium** |

---

## Next Steps

After implementation:

1. Run `/speckit.tasks` to generate detailed task breakdown
2. Execute tasks in dependency order
3. Run full test suite before merging
4. Update CHANGELOG.md with fixes
5. Deploy to staging for validation
6. Monitor production metrics after deployment

---

**Questions?** See [research.md](./research.md) for detailed technical decisions and alternatives considered.
