# Data Model: API-Level Response Summarization

**Feature**: `009-add-api-level`
**Date**: 2025-10-29

---

## Overview

This document defines the data models and entities for the API-level response summarization feature. All models use Pydantic for validation and FastAPI integration.

---

## Entities

### 1. SummarizedListing

**Purpose**: Compact representation of a property listing with only essential information for browsing and filtering.

**Location**: `src/models/summarized.py`

**Schema**:

```python
class SummarizedListing(BaseModel):
    """Summarized property listing with essential fields only."""

    id: int = Field(..., description="Unique property listing ID")
    name: str = Field(..., description="Property display name")
    city: str | None = Field(None, description="City location")
    country: str | None = Field(None, description="Country location")
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms")
    status: str = Field(..., description="Availability status (Available or Inactive)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 12345,
                "name": "Luxury Villa in Seminyak",
                "city": "Seminyak",
                "country": "Indonesia",
                "bedrooms": 3,
                "status": "Available"
            }
        }
    )
```

**Field Mapping from Full Response**:
- `id` ← `listing["id"]`
- `name` ← `listing["name"]`
- `city` ← `listing.get("city")`
- `country` ← `listing.get("country")`
- `bedrooms` ← `listing.get("bedrooms", 0)`
- `status` ← `"Available" if listing.get("isActive") else "Inactive"`

**Validation Rules**:
- `id`: Must be positive integer
- `name`: Non-empty string
- `bedrooms`: Non-negative integer (≥0)
- `status`: Enum-like ("Available", "Inactive")
- `city`, `country`: Optional strings (may be null)

**State Transitions**: None (read-only model)

---

### 2. SummarizedBooking

**Purpose**: Compact representation of a booking with core information for list views.

**Location**: `src/models/summarized.py`

**Schema**:

```python
class SummarizedBooking(BaseModel):
    """Summarized booking with essential fields only."""

    id: int = Field(..., description="Unique booking ID")
    guestName: str = Field(..., description="Guest full name", alias="guest_name")
    checkIn: str = Field(..., description="Check-in date (ISO 8601: YYYY-MM-DD)", alias="check_in")
    checkOut: str = Field(..., description="Check-out date (ISO 8601: YYYY-MM-DD)", alias="check_out")
    listingId: int = Field(..., description="Associated property listing ID", alias="listing_id")
    status: str = Field(..., description="Booking status (e.g., confirmed, cancelled)")
    totalPrice: float = Field(..., ge=0, description="Total booking price", alias="total_price")

    @field_validator("checkIn", "checkOut")
    @classmethod
    def validate_iso_date(cls, v: str) -> str:
        """Validate ISO 8601 date format (YYYY-MM-DD)."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 date format: {v}") from e

    model_config = ConfigDict(
        populate_by_name=True,  # Allow both camelCase and snake_case
        json_schema_extra={
            "example": {
                "id": 67890,
                "guestName": "John Doe",
                "checkIn": "2025-11-15",
                "checkOut": "2025-11-22",
                "listingId": 12345,
                "status": "confirmed",
                "totalPrice": 2500.00
            }
        }
    )
```

**Field Mapping from Full Response**:
- `id` ← `booking["id"]`
- `guestName` ← `booking.get("guestName")`
- `checkIn` ← `booking.get("checkIn")` (already ISO 8601 from Hostaway)
- `checkOut` ← `booking.get("checkOut")` (already ISO 8601 from Hostaway)
- `listingId` ← `booking.get("listingId")`
- `status` ← `booking.get("status")`
- `totalPrice` ← `booking.get("totalPrice", 0.0)`

**Validation Rules**:
- `id`, `listingId`: Must be positive integers
- `guestName`: Non-empty string
- `checkIn`, `checkOut`: Must be valid ISO 8601 dates (YYYY-MM-DD)
- `checkIn` ≤ `checkOut` (business rule validation - optional enhancement)
- `status`: String (enum-like, but not strictly validated)
- `totalPrice`: Non-negative float (≥0)

**State Transitions**: None (read-only model)

---

### 3. PageMetadata (Extended)

**Purpose**: Pagination and guidance metadata for list responses.

**Location**: `src/models/pagination.py` (existing, extend with `note` field)

**Schema** (existing + addition):

```python
class PageMetadata(BaseModel):
    """Metadata for paginated responses."""

    total: int = Field(..., description="Total number of items available")
    limit: int = Field(..., description="Maximum items per page")
    offset: int | None = Field(None, description="Current pagination offset")
    # NEW FIELD:
    note: str | None = Field(None, description="Additional guidance for API consumers")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 150,
                "limit": 10,
                "offset": 0,
                "note": "Use GET /api/listings/{id} to see full property details"
            }
        }
    )
```

**New Field**:
- `note`: Optional string providing guidance on accessing full details

**Usage**:
- Included in all PaginatedResponse instances when `summary=true`
- Contains endpoint-specific guidance message

---

### 4. PaginatedResponse (Existing, No Changes)

**Purpose**: Generic paginated response wrapper (already exists).

**Location**: `src/models/pagination.py`

**Schema** (existing, for reference):

```python
from typing import Generic, TypeVar

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[T] = Field(..., description="List of items")
    nextCursor: str | None = Field(None, description="Cursor for next page")
    metadata: PageMetadata = Field(..., description="Pagination metadata")

    model_config = ConfigDict(arbitrary_types_allowed=True)
```

**Usage with Summarization**:
- `PaginatedResponse[SummarizedListing]` - summarized property list
- `PaginatedResponse[dict]` - full property list (existing)
- `PaginatedResponse[SummarizedBooking]` - summarized booking list

---

## Relationships

```
PaginatedResponse[SummarizedListing]
├── items: List[SummarizedListing]
└── metadata: PageMetadata (with note field)

PaginatedResponse[SummarizedBooking]
├── items: List[SummarizedBooking]
└── metadata: PageMetadata (with note field)

SummarizedBooking
└── listingId references SummarizedListing.id (logical relationship)
```

---

## Data Flow

### Property Listing Summarization

```
1. Client Request: GET /api/listings?summary=true
2. FastAPI Route Handler (get_listings)
   ↓
3. Fetch full data from Hostaway API
   ↓
4. Check summary parameter
   ↓ (if summary=true)
5. Transform full items → List[SummarizedListing]
   - Extract essential fields
   - Derive status from isActive
   ↓
6. Build PaginatedResponse[SummarizedListing]
   - Include note in metadata
   ↓
7. Return JSON response
```

### Booking Summarization

```
1. Client Request: GET /api/reservations?summary=true
2. FastAPI Route Handler (search_bookings or similar)
   ↓
3. Fetch full data from Hostaway API
   ↓
4. Check summary parameter
   ↓ (if summary=true)
5. Transform full items → List[SummarizedBooking]
   - Extract essential fields
   - Validate ISO 8601 dates
   ↓
6. Build PaginatedResponse[SummarizedBooking]
   - Include note in metadata
   ↓
7. Return JSON response
```

---

## Validation Examples

### Valid SummarizedListing

```json
{
  "id": 12345,
  "name": "Beachfront Villa",
  "city": "Ubud",
  "country": "Indonesia",
  "bedrooms": 4,
  "status": "Available"
}
```

### Valid SummarizedBooking

```json
{
  "id": 67890,
  "guestName": "Jane Smith",
  "checkIn": "2025-12-01",
  "checkOut": "2025-12-10",
  "listingId": 12345,
  "status": "confirmed",
  "totalPrice": 3500.50
}
```

### Invalid Examples

```json
// Invalid: Missing required field
{
  "id": 12345,
  "name": "Villa"
  // Missing: bedrooms, status
}

// Invalid: Wrong date format
{
  "id": 67890,
  "guestName": "John Doe",
  "checkIn": "2025/12/01",  // Wrong format (should be YYYY-MM-DD)
  ...
}

// Invalid: Negative bedrooms
{
  "id": 12345,
  "name": "Villa",
  "bedrooms": -1,  // Must be ≥0
  ...
}
```

---

## Storage

**No Database Storage Required**:
- All models are response DTOs (Data Transfer Objects)
- Data sourced from Hostaway API (upstream)
- No persistence layer needed

**Future Optimization** (out of scope):
- Could cache summarized responses in Redis
- Would require separate cache keys per summary mode

---

## Constraints

### Business Rules

1. **Listing Status Derivation**:
   - `isActive=true` → `status="Available"`
   - `isActive=false` → `status="Inactive"`

2. **Date Format**:
   - All dates MUST be ISO 8601: YYYY-MM-DD
   - No time or timezone components

3. **Null Handling**:
   - Optional fields (city, country) may be null
   - Required fields MUST be present (validation error if missing)

### Technical Constraints

1. **Type Safety**:
   - All models MUST pass Pydantic validation
   - All fields MUST have type annotations

2. **JSON Serialization**:
   - All models MUST be JSON-serializable
   - No custom serializers needed (Pydantic handles this)

3. **OpenAPI Schema**:
   - All models MUST generate valid OpenAPI schema
   - Field descriptions MUST be present (for tool documentation)

---

## Testing Considerations

### Unit Tests (Model Validation)

**Test File**: `tests/unit/models/test_summarized.py`

```python
def test_summarized_listing_valid():
    """Test valid SummarizedListing creation."""
    listing = SummarizedListing(
        id=1,
        name="Test Villa",
        city="Ubud",
        country="Indonesia",
        bedrooms=3,
        status="Available"
    )
    assert listing.id == 1
    assert listing.bedrooms == 3

def test_summarized_listing_invalid_bedrooms():
    """Test negative bedrooms raise validation error."""
    with pytest.raises(ValidationError):
        SummarizedListing(
            id=1,
            name="Test",
            bedrooms=-1,  # Invalid
            status="Available"
        )

def test_summarized_booking_invalid_date():
    """Test invalid ISO 8601 date format."""
    with pytest.raises(ValidationError):
        SummarizedBooking(
            id=1,
            guestName="Test",
            checkIn="2025/12/01",  # Wrong format
            checkOut="2025-12-10",
            listingId=1,
            status="confirmed",
            totalPrice=1000.0
        )
```

### Integration Tests (Transformation)

**Test File**: `tests/integration/test_summarization_transform.py`

```python
async def test_listings_summarization_transform():
    """Test full listing transformed to summarized."""
    full_listing = {
        "id": 1,
        "name": "Villa",
        "city": "Ubud",
        "country": "Indonesia",
        "bedrooms": 3,
        "isActive": True,
        "description": "...",  # Excluded in summary
        "amenities": [...],  # Excluded in summary
    }

    summarized = SummarizedListing(
        id=full_listing["id"],
        name=full_listing["name"],
        city=full_listing.get("city"),
        country=full_listing.get("country"),
        bedrooms=full_listing.get("bedrooms", 0),
        status="Available" if full_listing.get("isActive") else "Inactive"
    )

    assert summarized.id == 1
    assert summarized.status == "Available"
    assert not hasattr(summarized, "description")  # Excluded
```

---

## Migration Notes

**No Database Migration Required**:
- Models are API response DTOs only
- No schema changes to upstream Hostaway API
- No local database tables affected

**Code Changes Required**:
1. Create `src/models/summarized.py` (new file)
2. Extend `src/models/pagination.py` PageMetadata with `note` field
3. No breaking changes to existing models

---

## OpenAPI Schema Generation

FastAPI automatically generates OpenAPI schema from Pydantic models:

```yaml
# Auto-generated for SummarizedListing
SummarizedListing:
  type: object
  required: [id, name, bedrooms, status]
  properties:
    id:
      type: integer
      description: Unique property listing ID
    name:
      type: string
      description: Property display name
    city:
      type: string
      nullable: true
      description: City location
    country:
      type: string
      nullable: true
      description: Country location
    bedrooms:
      type: integer
      minimum: 0
      description: Number of bedrooms
    status:
      type: string
      description: Availability status (Available or Inactive)
```

**MCP Tool Schema**:
FastAPI-MCP converts this to MCP tool input/output schema automatically.

---

## Conclusion

All data models defined with:
- ✅ Clear field types and constraints
- ✅ Validation rules
- ✅ Pydantic compatibility
- ✅ OpenAPI schema generation support
- ✅ Example payloads
- ✅ Testing strategy

**Ready for**: API contract definition (OpenAPI spec generation)
