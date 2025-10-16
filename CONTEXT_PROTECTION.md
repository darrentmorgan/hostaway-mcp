# Context Window Protection

This document describes the context window protection features implemented in the Hostaway MCP Server to prevent Claude context overflow and optimize token usage.

## Overview

The MCP server implements automatic response optimization to prevent large API responses from overflowing Claude's context window. This includes:

- **Cursor-based pagination** for list endpoints
- **Automatic response summarization** for large objects
- **Configurable token budgets** per endpoint
- **Hot-reload configuration** without server restart
- **Comprehensive telemetry** for observability

## Features

### 1. Cursor-Based Pagination

List endpoints automatically paginate results when response size would exceed token budgets.

**Example Request:**
```http
GET /api/v1/listings?limit=50
```

**Example Response:**
```json
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

**Fetching Next Page:**
```http
GET /api/v1/listings?cursor=eyJvZmZzZXQiOjUwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ==
```

### 2. Automatic Summarization

When a single object response exceeds the token threshold, the server automatically returns a summary with essential fields.

**Example Summarized Response:**
```json
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
    "totalFields": 20,
    "projectedFields": ["id", "status", "guestName", "checkInDate", "checkOutDate", "totalPrice"],
    "detailsAvailable": {
      "endpoint": "/api/v1/bookings/BK12345",
      "parameters": {"fields": "all"}
    }
  }
}
```

**Requesting Full Details:**
```http
GET /api/v1/bookings/BK12345?fields=all
```

### 3. Token Budget Configuration

Configure token limits globally or per-endpoint via YAML file.

**Configuration File:** `config.yaml`

```yaml
context_protection:
  # Global settings
  output_token_threshold: 4000
  hard_output_token_cap: 12000
  default_page_size: 50
  max_page_size: 200
  enable_summarization: true
  enable_pagination: true

  # Per-endpoint overrides
  endpoints:
    /api/v1/listings:
      page_size: 50
      threshold: 4000

    /api/v1/analytics:
      summarization_enabled: false  # Always return full data
```

**Hot-Reload:** Changes to `config.yaml` are automatically detected and applied without server restart (typically within 1 second).

### 4. Telemetry and Observability

Monitor context protection metrics via the health endpoint.

**Request:**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-15T14:30:00Z",
  "version": "0.1.0",
  "service": "hostaway-mcp",
  "context_protection": {
    "total_requests": 1247,
    "pagination_adoption": 0.87,
    "summarization_adoption": 0.23,
    "avg_response_size_bytes": 2400,
    "avg_latency_ms": 145,
    "oversized_events": 12,
    "uptime_seconds": 3600
  }
}
```

## Architecture

### Components

1. **Cursor Codec** (`src/utils/cursor_codec.py`)
   - Encodes/decodes pagination cursors with HMAC-SHA256 signatures
   - 10-minute TTL for cursor validity
   - Tamper-proof with signature verification

2. **Token Estimator** (`src/utils/token_estimator.py`)
   - Character-based token estimation (1 token ≈ 4 chars)
   - 20% safety margin
   - <20ms performance target

3. **Field Projector** (`src/utils/field_projector.py`)
   - Extracts essential fields from objects
   - Supports nested field paths (e.g., `guestAddress.city`)
   - Pre-defined essential fields per object type

4. **Pagination Service** (`src/services/pagination_service.py`)
   - Manages cursor creation and validation
   - Builds paginated responses with metadata
   - Validates page size limits

5. **Summarization Service** (`src/services/summarization_service.py`)
   - Applies field projection for summarization
   - Calculates reduction metrics
   - Provides drill-down instructions

6. **Config Service** (`src/services/config_service.py`)
   - Loads configuration from YAML
   - Hot-reload using watchdog file watcher
   - Per-endpoint override support

7. **Telemetry Service** (`src/services/telemetry_service.py`)
   - Tracks optimization metrics
   - Aggregates statistics per endpoint
   - In-memory storage with configurable limits

8. **Token-Aware Middleware** (`src/api/middleware/token_aware_middleware.py`)
   - Intercepts responses before sending to client
   - Applies summarization when token threshold exceeded
   - Integrates with config and telemetry services

## Usage Examples

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

### Handling Summarized Responses

```python
async def get_booking_details(booking_id: str):
    """Get booking details, requesting full details if summarized."""
    response = await client.get(f"/api/v1/bookings/{booking_id}")

    # Check if response was summarized
    if response.get("meta", {}).get("kind") == "preview":
        # Request full details
        endpoint = response["meta"]["detailsAvailable"]["endpoint"]
        params = response["meta"]["detailsAvailable"]["parameters"]
        response = await client.get(endpoint, params=params)

    return response
```

## Performance Targets

- **Cursor encoding/decoding:** <1ms per operation
- **Token estimation:** <20ms for typical API responses
- **Config reload:** <100ms from file change to application
- **Cursor size:** ~100 bytes per cursor

## Security

- **Cursor signatures:** HMAC-SHA256 with secret key
- **Cursor expiration:** 10-minute TTL prevents replay attacks
- **Tamper detection:** Signature verification on decode
- **Rate limiting:** Inherited from existing middleware

## Backwards Compatibility

All features are **additive** and **backwards compatible**:

- Non-paginated clients receive first page automatically
- All new response fields are optional
- Existing endpoints continue to work unchanged
- Feature flags allow gradual rollout

## Monitoring

Track these metrics in production:

1. **Pagination adoption rate** - % of list requests using pagination
2. **Summarization rate** - % of responses being summarized
3. **Average response size** - Monitor token reduction effectiveness
4. **Oversized events** - Count of responses exceeding 4000 tokens
5. **Configuration reload latency** - Time to apply config changes

## Troubleshooting

### "Invalid cursor" Error

**Cause:** Cursor expired (>10 minutes old) or tampered with

**Solution:** Re-query from beginning (no cursor parameter)

### "Limit exceeds maximum" Error

**Cause:** Requested `limit` > `max_page_size` (default 200)

**Solution:** Use smaller `limit` value

### Response Still Too Large

**Cause:** Single object exceeds token budget even after summarization

**Solution:** Use field projection via query parameters:
```http
GET /api/v1/bookings/BK12345?fields=guestDetails,priceBreakdown
```

## Configuration Reference

See `config.example.yaml` for complete configuration options and examples.

## Implementation Status

✅ **Completed:**
- Cursor encoding/decoding with HMAC signatures
- Token estimation with safety margins
- Field projection and summarization
- Pagination service
- Configuration hot-reload
- Telemetry and metrics
- Token-aware middleware
- Health endpoint integration

🚧 **In Progress:**
- Integration tests
- Production deployment
- Performance benchmarking

📋 **Planned:**
- Content chunking for very large text responses
- Redis-based cursor storage (migration from in-memory)
- Prometheus metrics export
- OpenAPI spec updates
