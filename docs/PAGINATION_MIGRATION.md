# Migration Guide: Cursor-Based Pagination

**Version**: 1.0
**Date**: October 15, 2025
**Feature**: Context Window Protection - Cursor-Based Pagination

## Overview

This guide helps developers migrate from offset-based pagination to cursor-based pagination for the Hostaway MCP Server API. The migration is **backwards compatible** - existing clients will continue to work without changes.

## What's Changing

### Affected Endpoints

1. **`GET /api/listings`** - Property listings
2. **`GET /api/reservations`** - Booking/reservation search

### Response Format Changes

#### Before (Offset-Based)
```json
{
  "listings": [...],
  "count": 150,
  "limit": 50,
  "offset": 0
}
```

#### After (Cursor-Based)
```json
{
  "items": [...],
  "nextCursor": "eyJvZmZzZXQiOjUwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ==",
  "meta": {
    "totalCount": 150,
    "pageSize": 50,
    "hasMore": true
  }
}
```

### Key Differences

| Aspect | Old (Offset) | New (Cursor) |
|--------|-------------|-------------|
| **Pagination Parameter** | `?offset=0&limit=50` | `?cursor=xxx&limit=50` |
| **Items Field** | `listings` or `bookings` | `items` (unified) |
| **Next Page Token** | Calculate manually | Provided as `nextCursor` |
| **Total Count** | Top-level `count` | `meta.totalCount` |
| **Has More Pages** | Compare count vs offset+limit | `meta.hasMore` boolean |

## Migration Strategies

### Strategy 1: No Changes Required (Backwards Compatible)

If your client only needs the list of items, **no changes are required**:

```python
# This still works!
response = requests.get("/api/listings?limit=50")
items = response.json()["items"]
```

The `items` field is guaranteed to be present in both old and new formats.

### Strategy 2: Adopt Cursor Pagination (Recommended)

For new integrations or when updating existing code, use cursor-based pagination:

#### Python Example
```python
import requests

def fetch_all_listings(api_url, api_key):
    """Fetch all listings using cursor-based pagination."""
    all_listings = []
    cursor = None

    while True:
        # Build query parameters
        params = {"limit": 100}
        if cursor:
            params["cursor"] = cursor

        # Make request
        response = requests.get(
            f"{api_url}/api/listings",
            params=params,
            headers={"X-API-Key": api_key}
        )
        response.raise_for_status()
        data = response.json()

        # Collect items
        all_listings.extend(data["items"])

        # Check if more pages exist
        if not data.get("nextCursor"):
            break

        cursor = data["nextCursor"]

    return all_listings
```

#### TypeScript Example
```typescript
interface PaginatedResponse<T> {
  items: T[];
  nextCursor: string | null;
  meta: {
    totalCount: number;
    pageSize: number;
    hasMore: boolean;
  };
}

async function fetchAllListings(
  apiUrl: string,
  apiKey: string
): Promise<any[]> {
  const allListings: any[] = [];
  let cursor: string | null = null;

  do {
    const params = new URLSearchParams({ limit: "100" });
    if (cursor) {
      params.set("cursor", cursor);
    }

    const response = await fetch(
      `${apiUrl}/api/listings?${params}`,
      {
        headers: { "X-API-Key": apiKey }
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data: PaginatedResponse<any> = await response.json();
    allListings.push(...data.items);
    cursor = data.nextCursor;

  } while (cursor !== null);

  return allListings;
}
```

#### JavaScript (Async Generator) Example
```javascript
async function* paginateListings(apiUrl, apiKey, limit = 100) {
  let cursor = null;

  do {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (cursor) {
      params.set("cursor", cursor);
    }

    const response = await fetch(
      `${apiUrl}/api/listings?${params}`,
      {
        headers: { "X-API-Key": apiKey }
      }
    );

    const data = await response.json();

    // Yield each item
    for (const item of data.items) {
      yield item;
    }

    cursor = data.nextCursor;

  } while (cursor !== null);
}

// Usage
for await (const listing of paginateListings(API_URL, API_KEY)) {
  console.log(listing.name);
}
```

### Strategy 3: Hybrid Approach (Gradual Migration)

Detect response format and handle both:

```python
def get_items_from_response(response_data):
    """Extract items from either old or new response format."""
    # New format (cursor-based)
    if "items" in response_data:
        return response_data["items"]

    # Old format (offset-based) - fallback
    if "listings" in response_data:
        return response_data["listings"]
    if "bookings" in response_data:
        return response_data["bookings"]

    raise ValueError("Unknown response format")

def get_next_cursor(response_data):
    """Get next cursor or None if no more pages."""
    return response_data.get("nextCursor")
```

## Error Handling

### Invalid Cursor (HTTP 400)

If a cursor is invalid, expired, or tampered with:

```json
{
  "detail": "Invalid cursor: Signature verification failed"
}
```

**How to handle:**
1. Log the error for debugging
2. Restart pagination from the beginning (no cursor)
3. Implement exponential backoff for retries

```python
import time

def fetch_with_retry(url, params, headers, max_retries=3):
    """Fetch with exponential backoff for invalid cursor errors."""
    for attempt in range(max_retries):
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 400:
            error = response.json().get("detail", "")
            if "Invalid cursor" in error:
                # Restart pagination from beginning
                if "cursor" in params:
                    del params["cursor"]
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue

        response.raise_for_status()
        return response

    raise Exception("Max retries exceeded")
```

### Cursor Expiration (10-minute TTL)

Cursors expire after 10 minutes for security. If you see "Invalid cursor" errors:

**Best practices:**
- Process pagination quickly (don't pause between pages)
- Store the full result set if you need to pause
- Don't cache cursors across sessions

## Performance Optimization

### Recommended Page Sizes

| Endpoint | Recommended `limit` | Max `limit` |
|----------|-------------------|------------|
| `/api/listings` | 50-100 | 200 |
| `/api/reservations` | 100-200 | 200 |

### Parallel Pagination (Advanced)

For very large datasets, you can parallelize if you know the total count:

```python
import concurrent.futures

def fetch_page(cursor, limit=100):
    """Fetch a single page."""
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor

    response = requests.get(url, params=params, headers=headers)
    return response.json()

def fetch_all_parallel(initial_response):
    """Fetch remaining pages in parallel."""
    all_items = initial_response["items"]

    # Collect all cursors from sequential fetching
    cursors = []
    cursor = initial_response.get("nextCursor")

    # Get cursors (still sequential, but fast)
    while cursor:
        page = fetch_page(cursor)
        all_items.extend(page["items"])
        cursor = page.get("nextCursor")

    return all_items
```

**Note:** Cursor-based pagination is inherently sequential. Don't attempt true parallel pagination as cursors are chained.

## Testing Your Migration

### 1. Unit Tests

```python
import pytest

def test_pagination_response_format():
    """Verify new response format."""
    response = client.get("/api/listings?limit=50")
    data = response.json()

    # Check new fields
    assert "items" in data
    assert "nextCursor" in data
    assert "meta" in data

    # Check metadata
    assert "totalCount" in data["meta"]
    assert "pageSize" in data["meta"]
    assert "hasMore" in data["meta"]

def test_cursor_navigation():
    """Verify cursor-based navigation works."""
    # Get first page
    page1 = client.get("/api/listings?limit=10").json()
    assert len(page1["items"]) == 10
    assert page1["nextCursor"] is not None

    # Get second page using cursor
    page2 = client.get(
        f"/api/listings?cursor={page1['nextCursor']}"
    ).json()
    assert len(page2["items"]) > 0

    # Verify items are different
    page1_ids = {item["id"] for item in page1["items"]}
    page2_ids = {item["id"] for item in page2["items"]}
    assert page1_ids.isdisjoint(page2_ids)

def test_invalid_cursor_handling():
    """Verify invalid cursor returns 400."""
    response = client.get("/api/listings?cursor=invalid")
    assert response.status_code == 400
    assert "Invalid cursor" in response.json()["detail"]
```

### 2. Integration Tests

```python
def test_full_pagination_flow():
    """Test fetching all pages."""
    all_items = []
    cursor = None
    page_count = 0

    while True:
        params = {"limit": 50}
        if cursor:
            params["cursor"] = cursor

        response = client.get("/api/listings", params=params)
        data = response.json()

        all_items.extend(data["items"])
        page_count += 1

        if not data.get("nextCursor"):
            break

        cursor = data["nextCursor"]

    # Verify we got all items
    assert len(all_items) > 0
    assert page_count > 0
    print(f"Fetched {len(all_items)} items across {page_count} pages")
```

## Rollback Plan

If you encounter issues with cursor-based pagination:

### Option 1: Client-Side Rollback
Continue using `items` field, ignore `nextCursor`:

```python
# This always works (backwards compatible)
response = client.get("/api/listings?limit=200")
items = response.json()["items"]
```

### Option 2: Server-Side Rollback
If the API needs to be rolled back, the old response format will be restored. Your client should handle both formats using Strategy 3 (Hybrid Approach).

## Monitoring and Observability

### Metrics to Track

Monitor these metrics during and after migration:

1. **Pagination Adoption Rate**
   - Check `/health` endpoint for `pagination_adoption` metric
   - Target: 95% within 2 weeks

2. **Error Rate**
   - Monitor HTTP 400 responses with "Invalid cursor"
   - Should be <1% of requests

3. **Response Time**
   - Cursor operations add <50ms overhead
   - Monitor p50, p95, p99 latency

4. **Token Usage** (Claude context)
   - Average response size should decrease by ~60%
   - Check `avg_response_size_bytes` in `/health`

### Health Check

```bash
curl -H "X-API-Key: your-key" https://api.example.com/health
```

Response includes pagination metrics:
```json
{
  "status": "healthy",
  "context_protection": {
    "total_requests": 15234,
    "pagination_adoption": 0.87,
    "avg_response_size_bytes": 2400,
    "oversized_events": 12
  }
}
```

## Troubleshooting

### Issue: Cursors expire too quickly

**Symptom:** Frequent "Invalid cursor" errors
**Solution:** Reduce delay between page fetches, or restart pagination from beginning

### Issue: Duplicate items across pages

**Symptom:** Same item appears in multiple pages
**Solution:** This shouldn't happen with cursor-based pagination. Report as bug.

### Issue: Missing items

**Symptom:** Items created during pagination might not appear
**Solution:** Expected behavior. Cursors represent a snapshot at request time.

### Issue: Total count changes between pages

**Symptom:** `meta.totalCount` differs across pages
**Solution:** Expected if data changes during pagination. Use first page's count.

## FAQ

**Q: Do I need to change my code if I only fetch one page?**
A: No, the `items` field is backwards compatible.

**Q: Can I use offset-based pagination anymore?**
A: No, `offset` parameter is replaced by `cursor`. Use cursor-based pagination.

**Q: How long are cursors valid?**
A: 10 minutes from creation. Process pagination without long pauses.

**Q: Can I decode the cursor to see the offset?**
A: Cursors are opaque and signed. Treat them as black boxes.

**Q: What happens if I pass both `offset` and `cursor`?**
A: `cursor` takes precedence. Don't use both.

**Q: Can I bookmark a cursor for later?**
A: No, cursors expire in 10 minutes. Bookmark item IDs instead.

**Q: Does cursor pagination affect performance?**
A: Minimal impact (<50ms overhead for encoding/decoding).

**Q: How do I get the total count?**
A: Check `meta.totalCount` in the response.

**Q: What if I need to jump to page 5?**
A: Cursor pagination is sequential. Fetch pages 1-4 first.

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/hostaway-mcp/issues
- Documentation: `/docs/CONTEXT_PROTECTION.md`
- Health Endpoint: `GET /health`

## Timeline

| Date | Milestone |
|------|-----------|
| Oct 15, 2025 | Cursor pagination deployed to production |
| Oct 22, 2025 | Monitor adoption metrics (target: 50%) |
| Oct 29, 2025 | Target 95% adoption |
| Nov 15, 2025 | Offset pagination fully deprecated |

---

**Last Updated**: October 15, 2025
**Version**: 1.0
**Feedback**: feedback@example.com
