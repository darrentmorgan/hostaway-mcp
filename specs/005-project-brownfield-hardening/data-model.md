# Data Model: MCP Server Context Window Protection

**Feature**: 005-project-brownfield-hardening
**Date**: 2025-10-15
**Status**: Complete

## Entity Definitions

### 1. PaginationCursor

Opaque token encoding position in result set, valid for 10 minutes.

**Fields**:
- `cursor_id`: str - Unique identifier (Base64-encoded signed payload)
- `offset`: int - Current position in result set
- `timestamp`: float - Cursor creation time (Unix timestamp)
- `order_by`: str - Sort column and direction (e.g., "created_desc")
- `filters`: dict[str, Any] - Query filters at cursor creation time
- `signature`: str - HMAC-SHA256 signature for tamper protection

**Validation Rules**:
- `offset` >= 0
- `timestamp` within last 10 minutes
- `signature` must match HMAC of payload
- `cursor_id` must be valid Base64

**State Transitions**:
- Created → Active (on first use)
- Active → Expired (after 10 minutes)
- Active → Invalid (if signature check fails)

**Relationships**:
- Stored in `CursorStorage` with TTL
- Referenced in `PaginatedResponse.nextCursor`

---

### 2. PaginatedResponse[T]

Generic wrapper for paginated list responses.

**Type Parameters**:
- `T`: Item type (e.g., Listing, Booking, Financial Transaction)

**Fields**:
- `items`: list[T] - Current page of items
- `nextCursor`: str | None - Opaque cursor for next page (null on final page)
- `meta`: PageMetadata - Pagination metadata

**Validation Rules**:
- `items` length <= configured page size
- `nextCursor` present if `meta.hasMore` is True
- `nextCursor` null if `meta.hasMore` is False

**Example**:
```python
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar('T')

class PageMetadata(BaseModel):
    totalCount: int
    pageSize: int
    hasMore: bool

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    nextCursor: str | None
    meta: PageMetadata
```

---

### 3. TokenBudget

Per-request token limit tracking and threshold enforcement.

**Fields**:
- `threshold`: int - Configured token limit (default 4000)
- `hard_cap`: int - Absolute maximum (default 12000)
- `estimated_tokens`: int - Estimated tokens in candidate response
- `budget_used`: float - Percentage of threshold used (0.0-1.0)
- `summary_mode`: bool - Whether summarization was triggered

**Validation Rules**:
- `threshold` > 0
- `hard_cap` >= `threshold`
- `budget_used` = `estimated_tokens` / `threshold`
- `summary_mode` = True if `estimated_tokens` > `threshold`

**Calculation**:
```python
class TokenBudget(BaseModel):
    threshold: int = 4000
    hard_cap: int = 12000
    estimated_tokens: int

    @property
    def budget_used(self) -> float:
        return min(self.estimated_tokens / self.threshold, 1.0)

    @property
    def summary_mode(self) -> bool:
        return self.estimated_tokens > self.threshold
```

---

### 4. SummaryResponse[T]

Condensed representation with essential fields + drill-down instructions.

**Type Parameters**:
- `T`: Original object type being summarized

**Fields**:
- `summary`: dict[str, Any] - Projected essential fields
- `meta`: SummaryMetadata - Summary information

**SummaryMetadata**:
- `kind`: Literal["preview", "full"] - Response type
- `totalFields`: int - Total fields in full object
- `projectedFields`: list[str] - Fields included in summary
- `detailsAvailable`: DetailsFetchInfo - How to get full details

**DetailsFetchInfo**:
- `endpoint`: str - API endpoint for full details
- `parameters`: dict[str, Any] - Parameters to include in request

**Example**:
```python
# Full booking object (verbose)
{
  "id": "BK12345",
  "status": "confirmed",
  "guestName": "John Doe",
  "guestEmail": "john@example.com",
  "guestPhone": "+1-555-0100",
  "guestAddress": {...},  # 10 fields
  "checkInDate": "2025-11-01",
  "checkOutDate": "2025-11-05",
  "totalPrice": 1200.00,
  "currency": "USD",
  "priceBreakdown": {...},  # 15 fields
  "propertyId": "PR789",
  "propertyDetails": {...},  # 20 fields
  "amenities": [...],  # 30 items
  "policies": {...}  # 8 fields
}

# Summarized response
{
  "summary": {
    "id": "BK12345",
    "status": "confirmed",
    "guestName": "John Doe",
    "checkInDate": "2025-11-01",
    "checkOutDate": "2025-11-05",
    "totalPrice": 1200.00,
    "propertyId": "PR789"
  },
  "meta": {
    "kind": "preview",
    "totalFields": 8,
    "projectedFields": ["id", "status", "guestName", "checkInDate", "checkOutDate", "totalPrice", "propertyId"],
    "detailsAvailable": {
      "endpoint": "/api/v1/bookings/{id}",
      "parameters": {"fields": "guestDetails,priceBreakdown,propertyDetails,amenities,policies"}
    }
  }
}
```

---

### 5. ContentChunk

Semantic segment of large content with continuation cursor.

**Fields**:
- `content`: str - Chunk content (respects semantic boundaries)
- `chunkIndex`: int - Current chunk number (0-indexed)
- `totalChunks`: int - Total chunks in full content
- `nextCursor`: str | None - Cursor for next chunk (null on final chunk)
- `metadata`: ChunkMetadata - Additional chunk information

**ChunkMetadata**:
- `startLine`: int - Starting line number in full content
- `endLine`: int - Ending line number (inclusive)
- `totalLines`: int - Total lines in full content
- `bytesInChunk`: int - Size of this chunk in bytes

**Validation Rules**:
- `chunkIndex` < `totalChunks`
- `startLine` <= `endLine`
- Content must end at semantic boundary (sentence/paragraph/log entry)
- `nextCursor` present if `chunkIndex` < `totalChunks - 1`

**Example**:
```python
class ChunkMetadata(BaseModel):
    startLine: int
    endLine: int
    totalLines: int
    bytesInChunk: int

class ContentChunk(BaseModel):
    content: str
    chunkIndex: int
    totalChunks: int
    nextCursor: str | None
    metadata: ChunkMetadata
```

---

### 6. TelemetryRecord

Per-request metrics capturing token usage and optimization strategies.

**Fields**:
- `request_id`: str - Correlation ID for request tracing
- `endpoint`: str - API endpoint path
- `timestamp`: datetime - Request timestamp
- `estimated_tokens`: int - Estimated tokens in response
- `response_bytes`: int - Actual response size in bytes
- `item_count`: int - Number of items returned (for lists)
- `latency_ms`: int - Request processing time in milliseconds
- `pagination_used`: bool - Whether pagination was applied
- `summarization_used`: bool - Whether summarization was triggered
- `chunking_used`: bool - Whether content chunking was applied
- `optimization_metadata`: dict[str, Any] - Additional optimization details

**Validation Rules**:
- `latency_ms` >= 0
- `response_bytes` >= 0
- `item_count` >= 0
- At most one of `pagination_used`, `chunking_used` can be True simultaneously

**Example**:
```python
from datetime import datetime
from pydantic import BaseModel

class TelemetryRecord(BaseModel):
    request_id: str
    endpoint: str
    timestamp: datetime
    estimated_tokens: int
    response_bytes: int
    item_count: int
    latency_ms: int
    pagination_used: bool
    summarization_used: bool
    chunking_used: bool
    optimization_metadata: dict[str, Any] = {}

    # Computed fields
    @property
    def tokens_per_item(self) -> float:
        return self.estimated_tokens / max(self.item_count, 1)
```

---

## Entity Relationships

```
┌─────────────────┐
│ PaginatedResponse│
│  <items>        │──┐
│  nextCursor ────┼──┼──> PaginationCursor
│  meta           │  │     (stored in CursorStorage)
└─────────────────┘  │
                     │
                     │
┌─────────────────┐  │
│ SummaryResponse │  │
│  summary        │  │
│  meta ──────────┼──┼──> DetailsFetchInfo
└─────────────────┘  │     (links to full endpoint)
                     │
                     │
┌─────────────────┐  │
│ ContentChunk    │  │
│  content        │  │
│  nextCursor ────┼──┘
│  metadata       │
└─────────────────┘

        ▲
        │
        │ observes
        │
┌─────────────────┐
│ TelemetryRecord │
│  request_id     │
│  endpoint       │
│  *_used flags   │
└─────────────────┘
```

**Key Relationships**:
1. `PaginatedResponse.nextCursor` → `PaginationCursor` (via cursor storage)
2. `SummaryResponse.meta.detailsAvailable` → Full detail endpoint
3. `ContentChunk.nextCursor` → `PaginationCursor` (reuses same encoding)
4. `TelemetryRecord` observes all optimization strategies (pagination, summarization, chunking)

---

## Validation Rules Summary

| Entity | Validation Rule | Enforcement |
|--------|----------------|-------------|
| PaginationCursor | Signature must be valid HMAC | `decode_cursor()` raises ValueError |
| PaginationCursor | Timestamp within 10 minutes | `decode_cursor()` raises ValueError |
| PaginatedResponse | `nextCursor` null ⟺ `meta.hasMore` false | Pydantic validator |
| TokenBudget | `threshold` > 0 | Pydantic Field(gt=0) |
| SummaryResponse | `projectedFields` ⊆ all fields in T | Runtime check |
| ContentChunk | Content ends at semantic boundary | Chunking service validation |
| TelemetryRecord | `latency_ms` >= 0 | Pydantic Field(ge=0) |

---

## Example Usage Flows

### Pagination Flow

```python
# Request 1: First page
GET /api/v1/listings?limit=50

# Response 1
{
  "items": [...50 listings...],
  "nextCursor": "eyJvZmZzZXQiOjUwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ==",
  "meta": {
    "totalCount": 500,
    "pageSize": 50,
    "hasMore": true
  }
}

# Request 2: Next page
GET /api/v1/listings?cursor=eyJvZmZzZXQiOjUwLCJ0cyI6MTY5NzQ1MjgwMC4wfQ==

# Response 2
{
  "items": [...50 listings...],
  "nextCursor": "eyJvZmZzZXQiOjEwMCwidHMiOjE2OTc0NTI4MDAuMH0=",
  "meta": {
    "totalCount": 500,
    "pageSize": 50,
    "hasMore": true
  }
}
```

### Summarization Flow

```python
# Request: Large booking details
GET /api/v1/bookings/BK12345

# Response: Automatic summarization (exceeded 4000 token threshold)
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
    "projectedFields": ["id", "status", "guestName", ...],
    "detailsAvailable": {
      "endpoint": "/api/v1/bookings/BK12345",
      "parameters": {"fields": "all"}
    }
  }
}

# Follow-up: Request full details
GET /api/v1/bookings/BK12345?fields=all

# Response: Full booking object (client explicitly requested)
{
  "id": "BK12345",
  "status": "confirmed",
  ...all fields...
}
```

---

**Status**: Data model complete. Ready for contract generation (Phase 1 continued).
