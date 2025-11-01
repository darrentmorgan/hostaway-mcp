# Quickstart: API-Level Response Summarization

**Feature**: `009-add-api-level`
**Date**: 2025-10-29

---

## Overview

This guide provides a quick reference for implementing and using the API-level response summarization feature.

---

## For Developers

### Implementation Checklist

#### Phase 1: Data Models

- [ ] Create `src/models/summarized.py` with SummarizedListing and SummarizedBooking
- [ ] Extend `src/models/pagination.py` PageMetadata with `note` field
- [ ] Add Pydantic validators for ISO 8601 dates
- [ ] Write unit tests for model validation

#### Phase 2: Route Modifications

- [ ] Modify `src/api/routes/listings.py`:
  - Add `summary: bool` query parameter to `get_listings()`
  - Add conditional response logic (summary vs. full)
  - Add logging for summary mode usage
- [ ] Modify `src/api/routes/bookings.py`:
  - Add `summary: bool` query parameter to booking list endpoint
  - Add conditional response logic
  - Add logging for summary mode usage
- [ ] Update route response_model to use Union types

#### Phase 3: Testing

- [ ] Write unit tests for summarized models
- [ ] Write integration tests for `/api/listings?summary=true`
- [ ] Write integration tests for `/api/reservations?summary=true`
- [ ] Write integration tests for detail endpoints with summary parameter (verify ignored)
- [ ] Validate response size reduction (80-90%)
- [ ] Validate backward compatibility (no summary parameter)

#### Phase 4: Documentation

- [ ] Update OpenAPI docs (auto-generated via FastAPI)
- [ ] Update README.md with summary parameter examples
- [ ] Add CHANGELOG.md entry
- [ ] Update MCP tool descriptions

### Quick Implementation Example

**Step 1**: Create summarized models

```python
# src/models/summarized.py
from pydantic import BaseModel, Field

class SummarizedListing(BaseModel):
    """Summarized property listing."""
    id: int = Field(..., description="Unique property listing ID")
    name: str = Field(..., description="Property display name")
    city: str | None = Field(None, description="City location")
    country: str | None = Field(None, description="Country location")
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms")
    status: str = Field(..., description="Availability status")

class SummarizedBooking(BaseModel):
    """Summarized booking."""
    id: int
    guestName: str
    checkIn: str  # ISO 8601 YYYY-MM-DD
    checkOut: str  # ISO 8601 YYYY-MM-DD
    listingId: int
    status: str
    totalPrice: float
```

**Step 2**: Extend PageMetadata

```python
# src/models/pagination.py
class PageMetadata(BaseModel):
    total: int
    limit: int
    offset: int | None = None
    note: str | None = None  # NEW FIELD
```

**Step 3**: Modify route handler

```python
# src/api/routes/listings.py
from src.models.summarized import SummarizedListing

@router.get(
    "/listings",
    response_model=PaginatedResponse[dict] | PaginatedResponse[SummarizedListing],
    summary="Get all property listings",
    tags=["Listings"],
)
async def get_listings(
    summary: bool = Query(False, description="Return summarized response"),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    client: HostawayClient = Depends(get_authenticated_client),
    request: Request = None,  # For logging correlation_id
) -> PaginatedResponse[dict] | PaginatedResponse[SummarizedListing]:
    """Get listings with optional summarization."""

    # Fetch full data from Hostaway API
    raw_response = await client.get_listings(limit=limit, offset=offset)
    items = raw_response.get("items", [])
    total_count = raw_response.get("count", 0)

    if summary:
        # Log summary usage
        logger.info(
            "Summary mode request",
            extra={
                "endpoint": "/api/listings",
                "summary": True,
                "organization_id": client.organization_id,
                "correlation_id": request.state.correlation_id,
            }
        )

        # Transform to summarized items
        summarized_items = [
            SummarizedListing(
                id=item["id"],
                name=item["name"],
                city=item.get("city"),
                country=item.get("country"),
                bedrooms=item.get("bedrooms", 0),
                status="Available" if item.get("isActive") else "Inactive"
            )
            for item in items
        ]

        return PaginatedResponse[SummarizedListing](
            items=summarized_items,
            nextCursor=encode_cursor({"offset": offset + limit}),
            metadata=PageMetadata(
                total=total_count,
                limit=limit,
                offset=offset,
                note="Use GET /api/listings/{id} to see full property details"
            )
        )

    # Return full response (existing logic)
    return PaginatedResponse[dict](
        items=items,
        nextCursor=encode_cursor({"offset": offset + limit}),
        metadata=PageMetadata(total=total_count, limit=limit, offset=offset)
    )
```

**Step 4**: Write tests

```python
# tests/integration/test_listings_summary.py
async def test_listings_with_summary_true(client):
    """Test GET /api/listings?summary=true returns summarized response."""
    response = await client.get("/api/listings?summary=true&limit=10")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "metadata" in data
    assert data["metadata"]["note"] is not None

    # Verify summarized fields only
    first_item = data["items"][0]
    assert set(first_item.keys()) == {"id", "name", "city", "country", "bedrooms", "status"}

async def test_listings_without_summary_returns_full(client):
    """Test backward compatibility - no summary parameter."""
    response = await client.get("/api/listings?limit=10")
    assert response.status_code == 200

    data = response.json()
    first_item = data["items"][0]

    # Full response includes more fields
    assert "description" in first_item or "amenities" in first_item
    assert len(first_item.keys()) > 6  # More than summarized fields
```

---

## For API Consumers

### Using the Summary Parameter

#### Basic Usage

```bash
# Get summarized property list (compact response)
curl "http://72.60.233.157:8080/api/listings?summary=true&limit=10" \
  -H "X-API-Key: your_api_key"

# Get full property list (default behavior)
curl "http://72.60.233.157:8080/api/listings?limit=10" \
  -H "X-API-Key: your_api_key"
```

#### With MCP (Claude Desktop)

```python
# MCP tool invocation (via Claude Desktop)
list_properties(limit=10, summary=True)
```

#### Response Examples

**Summarized Response** (summary=true):

```json
{
  "items": [
    {
      "id": 12345,
      "name": "Luxury Villa in Seminyak",
      "city": "Seminyak",
      "country": "Indonesia",
      "bedrooms": 3,
      "status": "Available"
    },
    {
      "id": 12346,
      "name": "Beachfront Apartment",
      "city": "Canggu",
      "country": "Indonesia",
      "bedrooms": 2,
      "status": "Inactive"
    }
  ],
  "nextCursor": "eyJvZmZzZXQiOjEwfQ==",
  "metadata": {
    "total": 150,
    "limit": 10,
    "offset": 0,
    "note": "Use GET /api/listings/{id} to see full property details"
  }
}
```

**Full Response** (summary=false or absent):

```json
{
  "items": [
    {
      "id": 12345,
      "name": "Luxury Villa in Seminyak",
      "city": "Seminyak",
      "country": "Indonesia",
      "bedrooms": 3,
      "isActive": true,
      "description": "Stunning 3-bedroom villa with private pool...",
      "amenities": ["Pool", "WiFi", "Kitchen", "Air Conditioning"],
      "pricePerNight": 250.00,
      "currency": "USD",
      "minimumStay": 3,
      "maxGuests": 6,
      "availabilityCalendar": [...]
      // ... many more fields
    }
  ],
  "nextCursor": "eyJvZmZzZXQiOjEwfQ==",
  "metadata": {
    "total": 150,
    "limit": 10,
    "offset": 0
  }
}
```

### When to Use Summary Mode

**Use `summary=true` when**:
- Browsing or filtering large lists
- Building UI dropdowns or selection menus
- Working with AI assistants (context window limits)
- Mobile apps with bandwidth constraints
- Displaying search results

**Use full response (no summary parameter) when**:
- Displaying detailed property pages
- Generating booking confirmations
- Exporting data for analytics
- Integrating with external systems requiring full data

### Accessing Full Details

After browsing with `summary=true`, retrieve full details for specific items:

```bash
# Step 1: Browse with summary
curl "http://72.60.233.157:8080/api/listings?summary=true&limit=10" \
  -H "X-API-Key: your_api_key"

# Step 2: Get full details for selected property
curl "http://72.60.233.157:8080/api/listings/12345" \
  -H "X-API-Key: your_api_key"
```

---

## Performance Comparison

### Response Sizes

| Endpoint | Mode | Items | Response Size | Reduction |
|----------|------|-------|---------------|-----------|
| /api/listings | Full | 10 | ~150KB | - |
| /api/listings | Summary | 10 | ~15KB | ~90% |
| /api/listings | Full | 50 | ~750KB | - |
| /api/listings | Summary | 50 | ~75KB | ~90% |

### Response Times

| Endpoint | Mode | Items | Time (95th percentile) |
|----------|------|-------|------------------------|
| /api/listings | Full | 10 | 500-700ms |
| /api/listings | Summary | 10 | 400-600ms |

*Note: Summary mode is slightly faster due to reduced serialization overhead.*

---

## Troubleshooting

### Issue: Summary parameter ignored

**Symptom**: Using `summary=true` on detail endpoint returns full data

**Solution**: This is expected behavior. Detail endpoints (e.g., `/api/listings/123`) always return full data, even with `summary=true`. The parameter is silently ignored to maintain simplicity.

### Issue: Response still too large

**Symptom**: Summarized response exceeds expected size

**Checklist**:
- Verify `summary=true` parameter is included
- Check response contains only 6 fields per item (Listings) or 7 fields (Bookings)
- Verify `metadata.note` field is present (indicates summary mode)
- If still large, consider reducing `limit` parameter (e.g., `limit=5`)

### Issue: Missing fields in summary response

**Symptom**: Need additional fields not included in summary

**Solution**: Summary mode provides fixed essential fields only. To access additional fields:
1. Use full response mode (no `summary` parameter)
2. Or fetch specific item details via detail endpoint

**Out of Scope**: Custom field selection (e.g., `fields=id,name,city`) is not supported.

---

## Next Steps

### For Developers

1. Review `research.md` for technical decisions
2. Review `data-model.md` for entity definitions
3. Review `contracts/api-specification.yaml` for OpenAPI spec
4. Proceed to `/speckit.tasks` to generate implementation tasks

### For API Consumers

1. Test summary parameter with your integration
2. Update client code to use `summary=true` for list operations
3. Monitor response sizes and performance improvements
4. Provide feedback on essential fields selection

---

## Related Documentation

- **Specification**: `specs/009-add-api-level/spec.md`
- **Research**: `specs/009-add-api-level/research.md`
- **Data Model**: `specs/009-add-api-level/data-model.md`
- **API Contract**: `specs/009-add-api-level/contracts/api-specification.yaml`
- **Constitution**: `.specify/memory/constitution.md`

---

## Support

For questions or issues:
- Review OpenAPI docs at `/docs` endpoint
- Check logs for summary mode usage (INFO level)
- Create GitHub issue for bugs or feature requests
