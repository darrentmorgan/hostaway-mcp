# Developer Quickstart: MCP Server Context Window Protection

**Feature**: 005-project-brownfield-hardening
**Date**: 2025-10-15

## Overview

This guide shows how to use pagination, summarization, and token budgets in the Hostaway MCP Server.

## Using Pagination

### Basic List Request (Default Behavior)

```python
# Request first page (50 items by default)
GET /api/v1/listings

# Response includes pagination metadata
{
  "items": [...50 listings...],
  "nextCursor": "eyJvZmZzZXQiOjUwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ==",
  "meta": {
    "totalCount": 500,
    "pageSize": 50,
    "hasMore": true
  }
}
```

### Fetching Additional Pages

```python
# Use nextCursor from previous response
GET /api/v1/listings?cursor=eyJvZmZzZXQiOjUwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ==

# Final page has no nextCursor
{
  "items": [...remaining listings...],
  "nextCursor": null,
  "meta": {
    "totalCount": 500,
    "pageSize": 23,
    "hasMore": false
  }
}
```

### Custom Page Size

```python
# Request 100 items per page (max 200)
GET /api/v1/listings?limit=100
```

## Understanding Summaries

### Automatic Summarization

When a response exceeds the token budget (default 4000 tokens), the server automatically returns a summary:

```python
GET /api/v1/bookings/BK12345

# Response (summarized due to token budget)
{
  "summary": {
    "id": "BK12345",
    "status": "confirmed",
    "guestName": "John Doe",
    "checkInDate": "2025-11-01",
    "checkOutDate": "2025-11-05",
    "totalPrice": 1200.00
  },
  "meta": {
    "kind": "preview",
    "totalFields": 8,
    "projectedFields": ["id", "status", ...],
    "detailsAvailable": {
      "endpoint": "/api/v1/bookings/BK12345",
      "parameters": {"fields": "all"}
    }
  }
}
```

### Requesting Full Details

```python
# Follow instructions in detailsAvailable
GET /api/v1/bookings/BK12345?fields=all

# Returns full booking object (may still be large!)
```

## Configuration

### Environment Variables

```bash
# Token budget threshold (default: 4000)
export MCP_OUTPUT_TOKEN_THRESHOLD=6000

# Hard cap (force preview above this, default: 12000)
export MCP_HARD_OUTPUT_TOKEN_CAP=15000

# Default page size (default: 50)
export MCP_DEFAULT_PAGE_SIZE=100

# Max page size (default: 200)
export MCP_MAX_PAGE_SIZE=500

# Feature flags
export MCP_FEATURE_PAGINATION=true
export MCP_FEATURE_SUMMARY_PREVIEW=true
```

### Configuration File

```yaml
# /opt/hostaway-mcp/config.yaml
context_protection:
  output_token_threshold: 4000
  hard_output_token_cap: 12000
  default_page_size: 50
  max_page_size: 200

  # Per-endpoint overrides
  endpoints:
    /api/v1/listings:
      page_size: 50
      pagination_enabled: true

    /api/v1/bookings:
      page_size: 100
      summarization_enabled: true

    /api/v1/analytics:
      summarization_enabled: false  # Always full details
```

## Observing Telemetry

### Metrics Endpoint

```python
GET /health

# Response includes context protection metrics
{
  "status": "healthy",
  "metrics": {
    "pagination_adoption": 0.95,
    "avg_response_size": 2400,
    "oversized_events": 12
  }
}
```

### Logs

All optimization decisions are logged:

```json
{
  "level": "INFO",
  "message": "Pagination applied",
  "endpoint": "/api/v1/listings",
  "item_count": 50,
  "total_count": 500,
  "cursor_generated": true
}

{
  "level": "INFO",
  "message": "Summarization triggered",
  "endpoint": "/api/v1/bookings/BK12345",
  "estimated_tokens": 6500,
  "threshold": 4000,
  "fields_projected": 7
}
```

## Common Patterns

### Paginating Through All Results

```python
async def fetch_all_listings():
    """Fetch all listings using pagination."""
    all_listings = []
    cursor = None

    while True:
        params = {"limit": 100}
        if cursor:
            params["cursor"] = cursor

        response = await client.get("/api/v1/listings", params=params)
        all_listings.extend(response["items"])

        if not response["meta"]["hasMore"]:
            break

        cursor = response["nextCursor"]

    return all_listings
```

### Handling Summaries in Workflows

```python
async def get_booking_details(booking_id: str):
    """Get booking details, requesting full details if summarized."""
    response = await client.get(f"/api/v1/bookings/{booking_id}")

    # Check if response was summarized
    if response.get("meta", {}).get("kind") == "preview":
        # Get full details
        details_endpoint = response["meta"]["detailsAvailable"]["endpoint"]
        params = response["meta"]["detailsAvailable"]["parameters"]
        response = await client.get(details_endpoint, params=params)

    return response
```

## Troubleshooting

### "Invalid cursor" Error

**Cause**: Cursor expired (10-minute TTL) or was tampered with

**Solution**: Re-query from the beginning (no cursor parameter)

### "Limit exceeds maximum" Error

**Cause**: Requested page size > `MCP_MAX_PAGE_SIZE` (default 200)

**Solution**: Use smaller `limit` value

### Response Still Too Large

**Cause**: Single item exceeds token budget even after summarization

**Solution**: Use field projection to select specific sections:
```python
GET /api/v1/bookings/BK12345?fields=guestDetails,priceBreakdown
```

---

**Status**: Quickstart complete. Ready for implementation.
