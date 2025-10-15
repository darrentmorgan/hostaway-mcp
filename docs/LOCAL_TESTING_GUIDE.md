# Local Testing Guide
# Cursor-Based Pagination

**Version**: 1.0
**Date**: October 15, 2025

## Quick Start

This guide walks through testing the cursor-based pagination feature locally before production deployment.

## Prerequisites

- [ ] Python 3.12+ installed
- [ ] Virtual environment activated (`.venv`)
- [ ] Dependencies installed (`uv sync`)
- [ ] Environment variables configured
- [ ] Local database running (if using Supabase locally)

## Environment Setup

### 1. Configure Environment Variables

Create `.env` file in project root:

```bash
# Hostaway API Credentials
HOSTAWAY_ACCOUNT_ID=your_account_id
HOSTAWAY_SECRET_KEY=your_secret_key
HOSTAWAY_API_BASE_URL=https://api.hostaway.com/v1

# Supabase Configuration (for API key auth)
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key

# Rate Limiting
RATE_LIMIT_IP=15
RATE_LIMIT_ACCOUNT=20
MAX_CONCURRENT_REQUESTS=50

# Logging
LOG_LEVEL=INFO
```

### 2. Start the Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Start the FastAPI server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Server should start on http://localhost:8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Test Scenarios

### Test 1: Health Endpoint

Verify the server is running and context protection metrics are available.

```bash
curl http://localhost:8000/health | jq .
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-15T...",
  "version": "0.1.0",
  "service": "hostaway-mcp",
  "context_protection": {
    "total_requests": 0,
    "pagination_adoption": 0,
    "summarization_adoption": 0,
    "avg_response_size_bytes": 0,
    "avg_latency_ms": 0,
    "oversized_events": 0,
    "uptime_seconds": 5
  }
}
```

✅ **Pass Criteria**: HTTP 200, status = "healthy"

### Test 2: API Documentation

Check that Swagger UI shows the updated pagination endpoints.

```bash
# Open in browser
open http://localhost:8000/docs
```

**Verify:**
- [ ] `/api/listings` shows `PaginatedResponse[dict]` response
- [ ] `cursor` parameter is documented
- [ ] `limit` parameter has min=1, max=200
- [ ] Response schema shows `items`, `nextCursor`, `meta`

### Test 3: First Page Pagination (Listings)

Fetch the first page of listings.

```bash
# Set your API key
export API_KEY="your_test_api_key"

# Request first page
curl -X GET "http://localhost:8000/api/listings?limit=10" \
  -H "X-API-Key: $API_KEY" \
  | jq .
```

**Expected Response:**
```json
{
  "items": [
    {
      "id": 12345,
      "name": "Property Name",
      ...
    }
  ],
  "nextCursor": "eyJvZmZzZXQiOjEwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ==",
  "meta": {
    "totalCount": 150,
    "pageSize": 10,
    "hasMore": true
  }
}
```

✅ **Pass Criteria**:
- HTTP 200 status
- `items` is an array
- `nextCursor` is a non-null string
- `meta.hasMore` is true
- `meta.pageSize` matches requested limit

### Test 4: Cursor Navigation

Use the cursor from Test 3 to fetch the next page.

```bash
# Save cursor from previous response
export CURSOR="eyJvZmZzZXQiOjEwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ=="

# Request second page
curl -X GET "http://localhost:8000/api/listings?cursor=$CURSOR" \
  -H "X-API-Key: $API_KEY" \
  | jq .
```

**Expected Response:**
```json
{
  "items": [
    {
      "id": 12355,
      "name": "Different Property",
      ...
    }
  ],
  "nextCursor": "eyJvZmZzZXQiOjIwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ==",
  "meta": {
    "totalCount": 150,
    "pageSize": 10,
    "hasMore": true
  }
}
```

✅ **Pass Criteria**:
- Items are different from first page
- Cursor value has changed
- No duplicate items across pages

### Test 5: Invalid Cursor Handling

Test error handling for invalid cursors.

```bash
# Test with completely invalid cursor
curl -X GET "http://localhost:8000/api/listings?cursor=invalid-cursor" \
  -H "X-API-Key: $API_KEY" \
  -w "\nHTTP Status: %{http_code}\n"
```

**Expected Response:**
```json
{
  "detail": "Invalid cursor: Signature verification failed"
}
HTTP Status: 400
```

✅ **Pass Criteria**:
- HTTP 400 status
- Clear error message
- No server crash

### Test 6: Final Page (No More Results)

Fetch a page with fewer items than requested (last page).

```bash
# Request with high limit to potentially hit last page
curl -X GET "http://localhost:8000/api/listings?limit=200" \
  -H "X-API-Key: $API_KEY" \
  | jq '.meta'
```

**Expected Response:**
```json
{
  "totalCount": 25,
  "pageSize": 25,
  "hasMore": false
}
```

If there's a `nextCursor`, navigate to the last page and verify:

✅ **Pass Criteria**:
- `nextCursor` is null on last page
- `meta.hasMore` is false
- `meta.pageSize` < requested limit (if fewer items exist)

### Test 7: Bookings Pagination

Test pagination on the reservations endpoint.

```bash
# First page
curl -X GET "http://localhost:8000/api/reservations?limit=20" \
  -H "X-API-Key: $API_KEY" \
  | jq '{itemCount: (.items | length), hasMore: .meta.hasMore, cursor: .nextCursor}'
```

**Expected Response:**
```json
{
  "itemCount": 20,
  "hasMore": true,
  "cursor": "eyJvZmZzZXQiOjIwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ=="
}
```

✅ **Pass Criteria**:
- Same pagination structure as listings
- Cursor navigation works
- Filters still work with pagination

### Test 8: Pagination with Filters

Test that filters work correctly with pagination.

```bash
# Filter by status
curl -X GET "http://localhost:8000/api/reservations?limit=10&status=confirmed" \
  -H "X-API-Key: $API_KEY" \
  | jq '{items: .items | length, status: .items[0].status}'
```

✅ **Pass Criteria**:
- Filters applied correctly
- Pagination works with filters
- Cursor preserves filter context

### Test 9: Performance Testing

Measure cursor encode/decode performance.

```bash
# Make 10 requests and measure average response time
for i in {1..10}; do
  curl -X GET "http://localhost:8000/api/listings?limit=50" \
    -H "X-API-Key: $API_KEY" \
    -w "Time: %{time_total}s\n" \
    -o /dev/null -s
done
```

✅ **Pass Criteria**:
- Response time <500ms p95
- No degradation over time
- Memory usage stable

### Test 10: Cursor Expiration (10 minute TTL)

Test that cursors expire after 10 minutes.

```bash
# Get a cursor
CURSOR=$(curl -s -X GET "http://localhost:8000/api/listings?limit=10" \
  -H "X-API-Key: $API_KEY" | jq -r '.nextCursor')

echo "Cursor: $CURSOR"
echo "Waiting 11 minutes for expiration..."

# Wait 11 minutes (661 seconds)
# sleep 661

# Try to use expired cursor
# curl -X GET "http://localhost:8000/api/listings?cursor=$CURSOR" \
#   -H "X-API-Key: $API_KEY"
```

**Expected Response (after 11 min):**
```json
{
  "detail": "Invalid cursor: Cursor expired"
}
```

✅ **Pass Criteria**: HTTP 400 after TTL expiration

### Test 11: Backwards Compatibility

Verify old clients can still access data.

```bash
# Old client just reading items array
curl -X GET "http://localhost:8000/api/listings?limit=10" \
  -H "X-API-Key: $API_KEY" \
  | jq '.items | length'
```

**Expected Output:** `10` (just the count)

✅ **Pass Criteria**: `items` field always present and accessible

### Test 12: Metrics Collection

Verify metrics are being collected.

```bash
# Make several requests
for i in {1..5}; do
  curl -s -X GET "http://localhost:8000/api/listings?limit=10" \
    -H "X-API-Key: $API_KEY" > /dev/null
done

# Check metrics
curl -s http://localhost:8000/health | jq '.context_protection'
```

**Expected Response:**
```json
{
  "total_requests": 5,
  "pagination_adoption": 1.0,
  "avg_response_size_bytes": 2400,
  ...
}
```

✅ **Pass Criteria**:
- `total_requests` increasing
- `pagination_adoption` > 0
- Metrics updating in real-time

## Integration Test Suite

Run the automated integration tests:

```bash
# Run pagination integration tests
pytest tests/api/routes/test_pagination.py -v

# Expected output:
# 8 passed in 0.52s
```

## Load Testing (Optional)

### Simple Load Test with Apache Bench

```bash
# Install ab (Apache Bench)
# macOS: already installed
# Linux: sudo apt-get install apache2-utils

# Run 1000 requests with 10 concurrent
ab -n 1000 -c 10 \
  -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/listings?limit=50
```

**Review:**
- Requests per second
- Time per request
- Failed requests (should be 0)

### Load Test with Locust

```bash
# Install locust
pip install locust

# Create locustfile (see MONITORING_OBSERVABILITY.md)
# Run load test
locust -f locustfile.py --host=http://localhost:8000 --users=50 --spawn-rate=5
```

## Troubleshooting

### Issue: Server won't start

**Error:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Make sure you're in the project root
pwd
# Should be: /Users/.../hostaway-mcp

# Install dependencies
uv sync

# Try again
uvicorn src.api.main:app --reload
```

### Issue: 401 Unauthorized

**Error:** `{"detail": "Missing API key. Provide X-API-Key header."}`

**Solution:**
```bash
# Make sure you're passing the API key header
curl -H "X-API-Key: your-key-here" http://localhost:8000/api/listings
```

### Issue: No listings returned

**Error:** `{"items": [], "nextCursor": null, ...}`

**Solution:**
- Check Hostaway credentials in `.env`
- Verify your account has listings
- Check logs for API errors

### Issue: Cursor decode errors

**Error:** `{"detail": "Invalid cursor: Invalid format"}`

**Solution:**
- Cursor may be URL-encoded incorrectly
- Make sure to copy the full cursor string
- Check cursor isn't being truncated

## Test Results Checklist

Mark tests as you complete them:

- [ ] Test 1: Health endpoint ✅
- [ ] Test 2: API documentation ✅
- [ ] Test 3: First page pagination ✅
- [ ] Test 4: Cursor navigation ✅
- [ ] Test 5: Invalid cursor handling ✅
- [ ] Test 6: Final page ✅
- [ ] Test 7: Bookings pagination ✅
- [ ] Test 8: Pagination with filters ✅
- [ ] Test 9: Performance testing ✅
- [ ] Test 10: Cursor expiration ⏱️
- [ ] Test 11: Backwards compatibility ✅
- [ ] Test 12: Metrics collection ✅
- [ ] Integration tests ✅

## Next Steps

After successful local testing:

1. [ ] Document any issues found
2. [ ] Fix any failing tests
3. [ ] Re-run full test suite
4. [ ] Deploy to staging environment
5. [ ] Run same tests on staging
6. [ ] Schedule production deployment

---

**Last Updated**: October 15, 2025
**Tested By**: _____________
**Date Tested**: _____________
