# Usage Tracking Fix - Production Incident Resolution

**Date:** 2025-10-14
**Status:** ✅ RESOLVED
**Severity:** Medium

## Problem
Usage tracking middleware was not recording metrics for MCP tool calls in production, despite API requests working correctly.

## Root Causes Identified

### 1. Path Mismatch
- **Issue:** Middleware only tracked `/api/` paths
- **Reality:** MCP tool calls use `/mcp` endpoint
- **Impact:** No MCP requests were being tracked

### 2. Missing Environment Variables
- **Issue:** Systemd service didn't load `.env` file
- **Impact:** Supabase credentials unavailable, RPC calls failed silently
- **Fix:** Added `EnvironmentFile=/opt/hostaway-mcp/.env` to service

### 3. Middleware Registration Order
- **Issue:** UsageTrackingMiddleware registered AFTER MCPAuthMiddleware
- **Reality:** Middleware executes in reverse registration order
- **Impact:** Tracking ran before `organization_id` was set by auth
- **Fix:** Moved UsageTrackingMiddleware registration BEFORE auth

### 4. Authentication Header Extraction
- **Issue:** MCPAuthMiddleware passed Header object to `verify_api_key`
- **Fix:** Manually extract header value: `request.headers.get("X-API-Key")`

## Fixes Applied

### 1. Updated Middleware Path Tracking
**File:** `src/api/middleware/usage_tracking.py`

```python
# Before: Only /api/*
if not request.url.path.startswith("/api/"):
    return await call_next(request)

# After: Both /api/* and /mcp
path = request.url.path
is_tracked = path.startswith("/api/") or path.startswith("/mcp")

if not is_tracked:
    return await call_next(request)
```

### 2. Enhanced Tool Name Extraction
**File:** `src/api/middleware/usage_tracking.py`

```python
@staticmethod
def _extract_tool_name(path: str) -> str:
    # Handle MCP endpoints specially
    if path.startswith("/mcp"):
        parts = path.strip("/").split("/")
        if len(parts) > 1:
            return parts[1]
        return "mcp_root"
    else:
        # API paths: /api/v1/resource_name/...
        parts = path.strip("/").split("/")
        if len(parts) >= 3:
            return parts[2]
    return "unknown"
```

### 3. Fixed Middleware Order
**File:** `src/api/main.py`

```python
# Correct order: UsageTracking BEFORE Auth (so it runs AFTER)
app.add_middleware(UsageTrackingMiddleware)
app.add_middleware(MCPAuthMiddleware)
```

### 4. Fixed Auth Middleware
**File:** `src/api/main.py`

```python
# Protect both MCP and API endpoints
if request.url.path.startswith("/mcp") or request.url.path.startswith("/api/"):
    # Extract API key from header manually
    x_api_key = request.headers.get("X-API-Key")

    try:
        await verify_api_key(request, x_api_key)
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"detail": str(e)},
            headers={"WWW-Authenticate": "ApiKey"},
        )
```

### 5. Updated Systemd Service
**File:** `/etc/systemd/system/hostaway-mcp.service`

```ini
[Service]
EnvironmentFile=/opt/hostaway-mcp/.env  # ← Added this line
```

### 6. Added Debug Logging
**File:** `src/api/middleware/usage_tracking.py`

```python
# File-based logging for production debugging
import logging
file_handler = logging.FileHandler('/tmp/usage_tracking.log')
logger = logging.getLogger('usage_tracking')
logger.addHandler(file_handler)
logger.info(f"Tracking usage for org {organization_id}, path: {path}")
```

## Verification

### Database Metrics
```sql
SELECT * FROM usage_metrics WHERE month_year = '2025-10';
```

**Results:**
- Organization ID: 1
- Total Requests: 5
- Unique Tools: ['test_listings', 'unknown', '400569', 'revenue']
- Last Updated: 2025-10-15T03:09:56.884913+00:00

### Test Commands
```bash
# Check service status
systemctl status hostaway-mcp

# View tracking logs
tail -f /tmp/usage_tracking.log

# Query database
psql -c "SELECT * FROM usage_metrics WHERE organization_id = 1;"
```

## Deployment Steps (For Future Reference)

1. **Update code on server:**
   ```bash
   cd /opt/hostaway-mcp
   tar -xzf hostaway-mcp-deploy.tar.gz
   ```

2. **Update systemd service:**
   ```bash
   vi /etc/systemd/system/hostaway-mcp.service
   # Add: EnvironmentFile=/opt/hostaway-mcp/.env
   systemctl daemon-reload
   ```

3. **Restart service:**
   ```bash
   systemctl restart hostaway-mcp
   ```

4. **Verify tracking:**
   ```bash
   # Make test request
   curl -H "X-API-Key: YOUR_KEY" http://localhost:8080/api/v1/listings

   # Check logs
   tail /tmp/usage_tracking.log

   # Check database
   # (Query shown above)
   ```

## Lessons Learned

1. **Middleware order matters:** FastAPI/Starlette executes middleware in reverse registration order
2. **Environment loading:** Systemd services need explicit `EnvironmentFile` directive
3. **Path assumptions:** Don't assume all API traffic uses `/api/` prefix
4. **Silent failures:** Try/except blocks should log to files in production, not just stdout
5. **Header extraction:** Dependency injection doesn't work in middleware - extract manually

## Future Improvements

1. **Better tool name extraction:** Current logic shows some "unknown" and numeric values
2. **Metrics aggregation:** Consider hourly/daily rollups for performance
3. **Alerting:** Add monitoring for when tracking fails
4. **Testing:** Add integration tests for middleware execution order

## Related Files

- `src/api/middleware/usage_tracking.py` - Main tracking logic
- `src/api/main.py` - Middleware registration and auth
- `/etc/systemd/system/hostaway-mcp.service` - Service configuration
- `supabase/migrations/20251013000004_functions.sql` - RPC function
