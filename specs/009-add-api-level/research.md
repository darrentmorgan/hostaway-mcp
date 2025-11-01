# Research: API-Level Response Summarization

**Feature**: `009-add-api-level`
**Date**: 2025-10-29
**Status**: Complete

---

## Overview

This document captures technical decisions and patterns for implementing API-level response summarization to prevent context window bloat for MCP consumers.

---

## Technical Decisions

### 1. Query Parameter Implementation

**Decision**: Implement `summary` parameter as optional boolean query parameter on list endpoints

**Rationale**:
- Follows REST API best practices for resource representation control
- Similar patterns: GraphQL field selection, REST partial responses (Google APIs)
- Backward compatible - absence of parameter maintains current behavior
- Explicit opt-in avoids surprising consumers with reduced responses

**Alternatives Considered**:
- **Accept header negotiation** (`Accept: application/vnd.hostaway.summary+json`): Rejected - overly complex for simple use case, requires client header management
- **Separate endpoints** (`/listings/summary`): Rejected - duplicates routing logic, violates DRY
- **Always summarized with expand parameter**: Rejected - breaks backward compatibility

**Implementation Pattern**:
```python
summary: bool = Query(False, description="Return summarized response with essential fields only")
```

---

### 2. Field Projection Strategy

**Decision**: Use fixed field sets per entity type, configured in response models

**Rationale**:
- Predictable response schema for consumers
- Easier testing and validation
- Aligns with existing PaginatedResponse pattern in codebase
- Avoids complexity of dynamic field selection

**Alternatives Considered**:
- **Dynamic field selection** (`fields=id,name,city`): Rejected - out of scope per spec, adds parsing complexity
- **Middleware-based projection**: Rejected - separation of concerns (response building belongs in route handlers)
- **Database-level projection**: Rejected - we fetch from Hostaway API (can't control upstream query)

**Implementation Pattern**:
Based on existing `src/models/pagination.py` PaginatedResponse pattern:

```python
class SummarizedListing(BaseModel):
    id: int
    name: str
    city: str | None
    country: str | None
    bedrooms: int
    status: str  # derived from isActive

class SummarizedBooking(BaseModel):
    id: int
    guestName: str
    checkIn: str  # ISO 8601 YYYY-MM-DD
    checkOut: str  # ISO 8601 YYYY-MM-DD
    listingId: int
    status: str
    totalPrice: float
```

---

### 3. Response Structure

**Decision**: Maintain existing PaginatedResponse structure, add "note" field for guidance

**Rationale**:
- Consistent with existing API contract (keeps PageMetadata intact)
- Minimal breaking changes
- Guidance field improves discoverability

**Alternatives Considered**:
- **Completely new response structure**: Rejected - unnecessary complexity, breaks existing contracts
- **Separate metadata object**: Rejected - PaginatedResponse already handles metadata well

**Implementation Pattern**:
```python
PaginatedResponse[SummarizedListing](
    items=[...],  # Summarized items
    nextCursor=cursor,
    metadata=PageMetadata(
        total=total_count,
        limit=limit,
        note="Use GET /api/listings/{id} to see full property details"
    )
)
```

---

### 4. Caching Strategy

**Decision**: Use same cache TTL for both modes, differentiate by full URL (including query params)

**Rationale**:
- Existing caching infrastructure (if any) handles query param variations automatically
- No special-case logic needed
- Simplified operations

**Alternatives Considered**:
- **Longer TTL for summaries**: Rejected - premature optimization, no data to support different cache durations
- **No caching for summaries**: Rejected - defeats performance benefits

**Implementation Note**:
If caching is implemented later, FastAPI's standard caching middleware or `httpx` client-side caching will automatically differentiate `/listings` vs `/listings?summary=true` by full URL.

---

### 5. Logging Strategy

**Decision**: Log summary parameter usage at INFO level with structured logging

**Rationale**:
- Enables usage analytics (track adoption)
- Helps measure success criteria (SC-005: API documentation effectiveness)
- Supports operational troubleshooting
- Minimal performance impact with structured logging

**Implementation Pattern**:
Based on existing `src/mcp/logging.py` structured logging:

```python
logger.info(
    "Summary mode request",
    extra={
        "endpoint": "/api/listings",
        "summary": True,
        "user_agent": request.headers.get("user-agent"),
        "organization_id": org_context.organization_id,
        "correlation_id": correlation_id,
    }
)
```

---

### 6. Detail Endpoint Behavior

**Decision**: Silently ignore `summary` parameter on detail endpoints (GET /listings/{id})

**Rationale**:
- Detail endpoints always return full data (their purpose is complete information)
- Silent ignoring avoids error handling complexity
- Common API pattern (e.g., GitHub API ignores unsupported params)

**Alternatives Considered**:
- **Return 400 Bad Request**: Rejected - overly strict, poor UX
- **Return warning in response**: Rejected - pollutes response structure, inconsistent schema

---

## Best Practices Research

### FastAPI Query Parameter Patterns

**Source**: FastAPI documentation - Query Parameters

**Pattern**: Use Pydantic models or Query() for typed parameters with defaults

```python
from fastapi import Query

summary: bool = Query(
    default=False,
    description="Return summarized response with essential fields only"
)
```

**Validation**: FastAPI automatically handles:
- Type coercion (`"true"` → `True`, `"1"` → `True`)
- Invalid values (returns 422 with validation details)

---

### Response Model Patterns

**Source**: Existing codebase (`src/api/routes/listings.py`, `src/models/pagination.py`)

**Pattern**: Use Pydantic response_model for OpenAPI generation and validation

```python
@router.get(
    "/listings",
    response_model=PaginatedResponse[dict] | PaginatedResponse[SummarizedListing],
    summary="Get all property listings",
    tags=["Listings"],
)
async def get_listings(
    summary: bool = Query(False),
    ...
) -> PaginatedResponse[dict] | PaginatedResponse[SummarizedListing]:
    ...
```

**Note**: Union return types allow conditional response schemas based on `summary` parameter.

---

### ISO 8601 Date Formatting

**Source**: Python `datetime` module, ISO 8601 standard

**Pattern**: Use `datetime.date.isoformat()` for YYYY-MM-DD format

```python
from datetime import date

check_in_date: str = booking["checkIn"]  # Assuming already ISO format from Hostaway
# If datetime object: check_in_date = date_obj.isoformat()
```

**Validation**: Pydantic automatically validates ISO 8601 strings when field type is `str` with Field description.

---

### Structured Logging

**Source**: Existing `src/mcp/logging.py`

**Pattern**: Use Python's `logging` with `extra` dict for structured fields

```python
import logging

logger = logging.getLogger(__name__)

logger.info(
    "Summary mode request",
    extra={
        "endpoint": request.url.path,
        "summary_mode": summary,
        "organization_id": org_context.organization_id,
        "correlation_id": get_correlation_id(request),
    }
)
```

**Integration**: Existing `python-json-logger` dependency handles JSON formatting automatically.

---

## Integration Points

### 1. Existing Routes

**Files to Modify**:
- `src/api/routes/listings.py` - Add summary parameter to `get_listings()`
- `src/api/routes/bookings.py` - Add summary parameter to list bookings endpoint

**Pattern**: Conditional response model based on `summary` flag

```python
if summary:
    summarized_items = [
        SummarizedListing(
            id=item["id"],
            name=item["name"],
            city=item.get("city"),
            country=item.get("country"),
            bedrooms=item.get("bedrooms", 0),
            status="Available" if item.get("isActive") else "Inactive"
        )
        for item in raw_items
    ]
    return PaginatedResponse[SummarizedListing](
        items=summarized_items,
        nextCursor=next_cursor,
        metadata=PageMetadata(
            total=total_count,
            limit=limit,
            note="Use GET /api/listings/{id} to see full property details"
        )
    )
else:
    # Existing full response logic
    return PaginatedResponse[dict](items=raw_items, ...)
```

---

### 2. Pydantic Models

**New Models to Create**:
- `src/models/summarized.py` - SummarizedListing, SummarizedBooking

**Pattern**: Leverage existing PageMetadata, extend with `note` field

```python
# src/models/pagination.py - extend existing PageMetadata
class PageMetadata(BaseModel):
    total: int
    limit: int
    offset: int | None = None
    note: str | None = Field(None, description="Additional guidance for consumers")
```

---

### 3. Logging Integration

**Files to Modify**:
- `src/api/routes/listings.py` - Add summary logging
- `src/api/routes/bookings.py` - Add summary logging

**Pattern**: Use existing correlation ID middleware

```python
from src.mcp.logging import get_logger

logger = get_logger(__name__)

@router.get("/listings")
async def get_listings(
    summary: bool = Query(False),
    request: Request,  # Inject for correlation_id
    org_context: OrganizationContext = Depends(get_organization_context),
    ...
):
    if summary:
        logger.info(
            "Summary mode request",
            extra={
                "endpoint": "/api/listings",
                "summary": True,
                "organization_id": org_context.organization_id,
                "correlation_id": request.state.correlation_id,
            }
        )
    ...
```

---

## Dependencies

**No New Dependencies Required**:
- ✅ FastAPI - Already available (0.100+)
- ✅ Pydantic - Already available (2.0+)
- ✅ python-json-logger - Already available (4.0+)
- ✅ httpx - Already available (0.27+)

---

## Testing Strategy

### 1. Unit Tests

**Test File**: `tests/unit/test_summarized_models.py`

**Coverage**:
- SummarizedListing validation (required fields, type coercion)
- SummarizedBooking validation (ISO 8601 date format)
- PageMetadata with note field

---

### 2. Integration Tests

**Test Files**:
- `tests/integration/test_listings_summary.py`
- `tests/integration/test_bookings_summary.py`

**Coverage**:
- GET /api/listings?summary=true returns summarized response
- GET /api/listings without summary returns full response (backward compat)
- GET /api/listings/{id}?summary=true silently ignores parameter
- Response size validation (80-90% reduction)
- PageMetadata includes note field

---

### 3. MCP Protocol Tests

**Test File**: `tests/mcp/test_summary_tools.py`

**Coverage**:
- MCP tool schema includes summary parameter
- Tool invocation with summary=true returns summarized data
- Tool description documents summary parameter

---

## Performance Considerations

### Response Size Reduction

**Baseline** (full property response):
- Average property: ~15KB (with descriptions, amenities, pricing rules, availability)
- 10 properties: ~150KB

**Target** (summarized response):
- Average summarized property: ~1-2KB (id, name, city, country, bedrooms, status)
- 10 properties: ~10-20KB

**Expected Reduction**: 85-90% (aligns with SC-001)

---

### Computational Overhead

**Summarization Cost**:
- Dictionary comprehension over items (O(n) where n = item count)
- Pydantic validation per item (minimal overhead for simple fields)

**Expected Impact**: <5ms for 100 items (negligible compared to API fetch time)

---

### Caching Benefits

**Without Caching**: Each summary request still fetches full data from Hostaway, then filters
**With Caching**: Summary responses cached separately from full responses (by URL)

**Future Optimization**: If upstream API supports field selection, could reduce Hostaway fetch size

---

## Security Considerations

### No New Attack Vectors

- ✅ Boolean query parameter (no injection risk)
- ✅ Field projection happens after authentication (no bypass risk)
- ✅ Same rate limiting applies (no DoS risk)
- ✅ Logging includes organization_id (audit trail maintained)

### Data Exposure

- ✅ Summary includes only public-facing fields (no PII reduction)
- ✅ No new permissions required
- ✅ Same authentication enforcement

---

## Deployment Considerations

### Backward Compatibility

- ✅ **100% compatible**: Default behavior unchanged (summary=false)
- ✅ No migrations required (no database changes)
- ✅ No configuration changes needed (optional feature)

### Rollout Strategy

1. **Deploy to staging**: Validate with test consumers
2. **Monitor logs**: Track summary parameter adoption (INFO level)
3. **Deploy to production**: Feature available immediately
4. **Update documentation**: Add summary parameter to OpenAPI docs (auto-generated)
5. **Announce to consumers**: Notify AI assistant integrators, API users

### Monitoring

**Metrics to Track**:
- Summary mode request count (per endpoint)
- Summary mode adoption rate (% of list requests with summary=true)
- Response size distribution (full vs. summary)
- Response time distribution (full vs. summary)

**Alerts**:
- Unexpected summary mode failures (>1% error rate)
- Summary response size exceeds threshold (>5KB per item)

---

## Documentation Updates

### OpenAPI Schema

**Auto-Generated** via FastAPI:
- Query parameter schema includes `summary` boolean
- Response schema shows union type (full | summarized)
- Tool descriptions include summary parameter documentation

### API Documentation

**Manual Updates Required**:
- README.md - Add summary parameter example
- docs/API.md - Document summarization feature (if exists)
- CHANGELOG.md - Add entry for v0.2.0 (or next version)

---

## Success Validation

### SC-001: Response Size Reduction

**Measurement**: Compare `len(response.json())` for 10 items

```python
full_size = len(full_response.json())
summary_size = len(summary_response.json())
reduction = (full_size - summary_size) / full_size * 100
assert reduction >= 80, f"Expected ≥80% reduction, got {reduction}%"
```

### SC-002: Response Time

**Measurement**: Time API calls in integration tests

```python
import time
start = time.time()
response = client.get("/api/listings?summary=true&limit=10")
duration = time.time() - start
assert duration < 1.0, f"Expected <1s, got {duration}s"
```

### SC-003: Backward Compatibility

**Measurement**: Run full test suite without summary parameter

```python
# All existing tests pass without modification
pytest tests/integration/ -k "not summary"
```

### SC-004: Context Window Management

**Measurement**: Manual validation with Claude Desktop

```
# Request 20 properties with summary=true
# Verify no context overflow errors
# Verify Claude can process and analyze all properties
```

### SC-005: Documentation Clarity

**Measurement**: Post-launch support ticket tracking

```
# Track "summary parameter" related support tickets
# Target: ≤10% of previous "response too large" tickets
```

---

## Conclusion

All technical unknowns resolved. Ready for Phase 1 (Design & Contracts).

**Key Takeaways**:
- No new dependencies required
- Minimal changes to existing codebase
- 100% backward compatible
- Clear integration points identified
- Testing strategy defined
- Performance impact negligible
- Security posture maintained

**Next Phase**: Generate data models and API contracts
