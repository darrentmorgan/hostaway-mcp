# Implementation Plan: API-Level Response Summarization

**Branch**: `009-add-api-level` | **Date**: 2025-10-29 | **Spec**: [spec.md](./spec.md)
**Status**: ✅ Complete | **Deployed**: 2025-10-30 | **PR**: #7

**Input**: Feature specification from `/specs/009-add-api-level/spec.md`

---

## Summary

Add API-level response summarization to prevent context window bloat for MCP consumers. Implement optional `summary=true` query parameter on list endpoints (`/api/listings`, `/api/reservations`) that returns compact responses with essential fields only, reducing response size by 80-90%. The feature maintains 100% backward compatibility (default behavior unchanged) and leverages existing FastAPI/Pydantic infrastructure without requiring new dependencies.

**Technical Approach**: Conditional response models based on boolean query parameter, using fixed field projection patterns with Pydantic validation. Response transformation happens in route handlers after fetching full data from Hostaway API.

---

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: FastAPI 0.100+, Pydantic 2.0+, httpx 0.27+ (all existing)
**Storage**: N/A (stateless API, all data from Hostaway)
**Testing**: pytest with pytest-asyncio (existing)
**Target Platform**: Linux server (VPS: 72.60.233.157) + local development
**Project Type**: Single (backend API server with MCP integration)
**Performance Goals**: <500ms API response time (95th percentile), 80-90% response size reduction, <1s MCP tool invocation
**Constraints**: 100% backward compatibility required, no new dependencies, must pass mypy --strict, >80% test coverage
**Scale/Scope**: 10-20 properties per typical request, 100+ concurrent AI assistant requests, minimal computational overhead (<5ms per 100 items)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### I. API-First Design ✅ PASS

- ✅ Feature implemented as FastAPI endpoint enhancements (existing `/api/listings` and `/api/reservations`)
- ✅ Explicit `operation_id` for OpenAPI schema generation
- ✅ Pydantic models for request/response (SummarizedListing, SummarizedBooking)
- ✅ Comprehensive docstrings documenting summary parameter
- ✅ `response_model` specified for FastAPI schema generation
- ✅ FastAPI tags for logical grouping (Listings, Bookings)

**Rationale**: API-first design maintained. MCP tools automatically updated via fastapi-mcp OpenAPI introspection.

### II. Type Safety (NON-NEGOTIABLE) ✅ PASS

- ✅ All functions have type annotations (Query parameters, response models)
- ✅ Pydantic models with Field constraints (ge=0 for bedrooms, ISO 8601 validators)
- ✅ Configuration uses pydantic-settings (no new config needed)
- ✅ Code must pass `mypy --strict` (enforced in CI/CD)
- ✅ All API responses serializable and type-validated

**Enforcement**: Pre-commit hook + CI/CD pipeline

### III. Security by Default ✅ PASS

- ✅ No new authentication required (uses existing API key/OAuth2)
- ✅ Boolean query parameter validated by FastAPI (no injection risk)
- ✅ Field projection happens post-authentication (no bypass risk)
- ✅ Rate limiting applies equally (no DoS risk)
- ✅ Audit logging includes organization_id and correlation_id
- ✅ No new sensitive data exposure (same fields, just filtered)

**Security Layers**: Unchanged from existing implementation

### IV. Test-Driven Development ✅ PASS

- ✅ Unit tests for Pydantic models (SummarizedListing, SummarizedBooking)
- ✅ Integration tests for endpoints with summary parameter
- ✅ Integration tests for backward compatibility (no summary parameter)
- ✅ E2E tests for detail endpoint behavior (parameter ignored)
- ✅ Coverage target: >80% (existing requirement maintained)
- ✅ Test isolation with httpx_mock for external dependencies

**Test Categories**: Unit (models), Integration (endpoints), E2E (workflows), Performance (response sizes)

### V. Async Performance ✅ PASS

- ✅ All endpoint functions remain `async def`
- ✅ External API calls use `httpx.AsyncClient` (existing)
- ✅ No blocking operations introduced
- ✅ Connection pooling maintained (existing infrastructure)
- ✅ Minimal overhead: dictionary comprehension + Pydantic validation (<5ms/100 items)

**Performance Impact**: Slight improvement due to reduced serialization overhead

### Constitution Check Summary: ✅ ALL GATES PASSED

No violations detected. Feature aligns with all core principles:
- API-first design preserved
- Type safety maintained
- Security posture unchanged
- TDD workflow required
- Async performance maintained

**Re-check After Phase 1**: ✅ CONFIRMED - Design adheres to all principles

---

## Project Structure

### Documentation (this feature)

```
specs/009-add-api-level/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (technical decisions, patterns)
├── data-model.md        # Phase 1 output (entity definitions, schemas)
├── quickstart.md        # Phase 1 output (developer/consumer guide)
├── contracts/           # Phase 1 output (OpenAPI specification)
│   └── api-specification.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT YET CREATED)
```

### Source Code (repository root)

```
src/
├── models/
│   ├── pagination.py          # MODIFY: Extend PageMetadata with note field
│   └── summarized.py          # CREATE: SummarizedListing, SummarizedBooking
├── api/
│   ├── routes/
│   │   ├── listings.py        # MODIFY: Add summary parameter to get_listings()
│   │   └── bookings.py        # MODIFY: Add summary parameter to search_bookings()
│   └── main.py                # NO CHANGE: FastAPI app, MCP integration unaffected
└── mcp/
    └── logging.py             # NO CHANGE: Existing structured logging used as-is

tests/
├── unit/
│   └── models/
│       └── test_summarized.py # CREATE: Model validation tests
├── integration/
│   ├── test_listings_summary.py  # CREATE: Listings endpoint tests
│   └── test_bookings_summary.py  # CREATE: Bookings endpoint tests
└── e2e/
    └── test_summary_workflows.py # CREATE: End-to-end workflow tests
```

**Structure Decision**: Single project architecture maintained. Changes localized to models and route handlers. No new modules or services required, keeping complexity minimal.

---

## Complexity Tracking

*No violations requiring justification.*

All constitution principles pass without exceptions. Feature implements straightforward query parameter with conditional response transformation, aligned with existing patterns.

---

## Phase 0: Research Summary

**Output**: `research.md` (completed)

**Key Decisions**:

1. **Query Parameter Implementation**: Optional boolean query parameter (`summary: bool = Query(False)`)
2. **Field Projection**: Fixed field sets per entity type (no dynamic selection)
3. **Response Structure**: Maintain existing PaginatedResponse, extend PageMetadata with `note` field
4. **Caching**: Use same TTL, differentiate by full URL (automatic with standard caching)
5. **Logging**: INFO level structured logging with correlation IDs
6. **Detail Endpoint Behavior**: Silently ignore summary parameter (no warnings/errors)

**Alternatives Rejected**:
- Accept header negotiation (too complex)
- Separate endpoints (DRY violation)
- Dynamic field selection (out of scope)
- Middleware-based projection (wrong separation of concerns)

**Dependencies**: None required (all existing)

**Performance**: 80-90% response size reduction, <5ms computational overhead per 100 items

**Security**: No new attack vectors, same authentication/rate limiting

---

## Phase 1: Design & Contracts Summary

**Outputs**: `data-model.md`, `contracts/api-specification.yaml`, `quickstart.md` (completed)

### Data Models

#### New Models (Create `src/models/summarized.py`)

1. **SummarizedListing**
   - Fields: id, name, city, country, bedrooms, status
   - Validation: bedrooms ≥0, status enum-like
   - Derives status from isActive boolean

2. **SummarizedBooking**
   - Fields: id, guestName, checkIn, checkOut, listingId, status, totalPrice
   - Validation: ISO 8601 dates (YYYY-MM-DD), totalPrice ≥0
   - Custom validator for date format

#### Modified Models (Extend `src/models/pagination.py`)

3. **PageMetadata**
   - Added field: `note: str | None` for consumer guidance
   - Example: "Use GET /api/listings/{id} to see full property details"

#### Existing Models (No Changes)

4. **PaginatedResponse[T]**
   - Generic wrapper, supports SummarizedListing and SummarizedBooking via type parameter
   - No modifications needed

### API Contracts

**OpenAPI Specification**: `contracts/api-specification.yaml`

**Modified Endpoints**:

1. **GET /api/listings**
   - Added parameter: `summary: bool` (default: false)
   - Response type: `PaginatedResponse[SummarizedListing] | PaginatedResponse[dict]` (conceptual)
   - **Implementation Note**: Due to FastAPI limitations with Union types in generic responses, the actual implementation uses `response_model=None` with `Any` return type. FastAPI still generates correct OpenAPI schemas via type inference from the returned Pydantic models.
   - Backward compatible: absence of parameter returns full response

2. **GET /api/listings/{listing_id}**
   - Accepts `summary` parameter but silently ignores it
   - Always returns full listing details

3. **GET /api/reservations**
   - Added parameter: `summary: bool` (default: false)
   - Response type: `PaginatedResponse[SummarizedBooking] | PaginatedResponse[dict]` (conceptual)
   - **Implementation Note**: Uses same `response_model=None` workaround as listings endpoint
   - Filters out nested objects when summary=true

**Schema Generation**: Automatic via FastAPI Pydantic integration (type inference)

**MCP Tool Updates**: Automatic via fastapi-mcp OpenAPI introspection

### Developer Guide

**Quickstart**: `quickstart.md`

**Covers**:
- Implementation checklist (4 phases)
- Code examples (models, routes, tests)
- API consumer usage guide
- Performance comparison table
- Troubleshooting common issues

---

## Integration Points

### 1. Existing Routes (Modify)

**Files**: `src/api/routes/listings.py`, `src/api/routes/bookings.py`

**Changes**:
- Add `summary: bool = Query(False)` parameter
- Add conditional logic: `if summary: transform_to_summarized() else: return_full()`
- Add logging for summary mode usage (`logger.info(...)`)
- Set `response_model=None` with `Any` return type (FastAPI Union limitation workaround)
- Update function return type annotation to `Any` for type checking

**Pattern**: Fetch full data → Check summary flag → Transform if true → Return

### 2. Pydantic Models (Create/Extend)

**New File**: `src/models/summarized.py`
- SummarizedListing
- SummarizedBooking

**Modified File**: `src/models/pagination.py`
- PageMetadata with `note` field

### 3. Logging (Use Existing)

**File**: `src/mcp/logging.py` (no changes)

**Usage**: Call `logger.info()` with structured extra dict when summary=true

### 4. Testing (Create New Tests)

**New Files**:
- `tests/unit/models/test_summarized.py`
- `tests/integration/test_listings_summary.py`
- `tests/integration/test_bookings_summary.py`
- `tests/e2e/test_summary_workflows.py`

---

## Implementation Phases

### Phase 0: Research ✅ COMPLETE

- [x] Technical decisions documented
- [x] Best practices researched
- [x] Integration points identified
- [x] Performance considerations analyzed
- [x] Security review completed

### Phase 1: Design & Contracts ✅ COMPLETE

- [x] Data models defined (SummarizedListing, SummarizedBooking, PageMetadata extension)
- [x] OpenAPI contracts generated (api-specification.yaml)
- [x] Developer quickstart created
- [x] Agent context updated

### Phase 2: Task Generation (Next Command: `/speckit.tasks`)

- [ ] Break down implementation into atomic tasks
- [ ] Organize tasks by dependency order
- [ ] Assign task types (create/modify/test/document)
- [ ] Generate actionable checklist for implementation

---

## Success Criteria Validation

### SC-001: Response Size Reduction (80-90%)

**Measurement**:
```python
full_size = len(full_response.json())
summary_size = len(summary_response.json())
reduction = (full_size - summary_size) / full_size * 100
assert reduction >= 80
```

### SC-002: Response Time (<1 second for 10 properties)

**Measurement**:
```python
start = time.time()
response = client.get("/api/listings?summary=true&limit=10")
duration = time.time() - start
assert duration < 1.0
```

### SC-003: Backward Compatibility (100%)

**Measurement**: Run existing test suite without summary parameter
```bash
pytest tests/integration/ -k "not summary"  # All pass
```

### SC-004: Context Window Management (20+ properties)

**Measurement**: Manual validation with Claude Desktop
- Request 20 properties with summary=true
- Verify no context overflow errors

### SC-005: Documentation Clarity (90% reduction in support requests)

**Measurement**: Track support tickets post-launch
- Monitor "summary parameter" related tickets
- Compare to baseline "response too large" tickets

---

## Risk Assessment

### Low Risk ✅

**Backward Compatibility**: 100% maintained (default behavior unchanged, feature is opt-in)

**Type Safety**: Enforced by Pydantic + mypy --strict (CI/CD gate)

**Security**: No new attack vectors (boolean query parameter, post-auth projection)

**Performance**: Minimal overhead (<5ms/100 items), slight serialization improvement

### Mitigation Strategies

**Testing**: Comprehensive unit/integration/E2E tests (>80% coverage required)

**Rollout**: Deploy to staging first, monitor logs (INFO level) for adoption tracking

**Monitoring**: Track summary mode usage, response sizes, error rates

**Rollback**: Feature is additive only - can disable by removing query parameter (no data migrations needed)

---

## Next Steps

1. **Validate Plan**: Review with stakeholders
2. **Generate Tasks**: Run `/speckit.tasks` to create actionable task list
3. **Implement**: Execute tasks following TDD workflow
4. **Test**: Achieve >80% coverage
5. **Deploy**: Staging → Production with monitoring

---

## Related Artifacts

- **Specification**: `spec.md` (requirements, user stories, acceptance criteria)
- **Clarifications**: `spec.md` § Clarifications (5 questions resolved)
- **Research**: `research.md` (technical decisions, patterns, best practices)
- **Data Model**: `data-model.md` (entity definitions, validation rules, schemas)
- **API Contract**: `contracts/api-specification.yaml` (OpenAPI 3.1 specification)
- **Quickstart**: `quickstart.md` (developer/consumer guide, examples)
- **Constitution**: `.specify/memory/constitution.md` (project principles, gates)

---

## Appendix: Technical Details

### Response Transformation Logic

```python
def transform_to_summarized_listing(full_item: dict) -> SummarizedListing:
    """Transform full listing to summarized format."""
    return SummarizedListing(
        id=full_item["id"],
        name=full_item["name"],
        city=full_item.get("city"),
        country=full_item.get("country"),
        bedrooms=full_item.get("bedrooms", 0),
        status="Available" if full_item.get("isActive") else "Inactive"
    )

def transform_to_summarized_booking(full_booking: dict) -> SummarizedBooking:
    """Transform full booking to summarized format."""
    return SummarizedBooking(
        id=full_booking["id"],
        guestName=full_booking.get("guestName"),
        checkIn=full_booking.get("checkIn"),  # Already ISO 8601 from Hostaway
        checkOut=full_booking.get("checkOut"),
        listingId=full_booking.get("listingId"),
        status=full_booking.get("status"),
        totalPrice=full_booking.get("totalPrice", 0.0)
    )
```

### Logging Pattern

```python
if summary:
    logger.info(
        "Summary mode request",
        extra={
            "endpoint": request.url.path,
            "summary": True,
            "organization_id": org_context.organization_id,
            "correlation_id": request.state.correlation_id,
        }
    )
```

### Test Coverage Targets

- **Unit Tests**: 100% coverage for Pydantic models
- **Integration Tests**: >80% coverage for route handlers
- **E2E Tests**: Critical workflows (browse → detail)
- **Overall**: >80% project-wide (existing requirement)

---

**Plan Status**: ✅ COMPLETE - Ready for `/speckit.tasks`

**Estimated Complexity**: Low-Medium (localized changes, no new dependencies, well-defined scope)

**Estimated Implementation Time**: 4-6 hours (2h models/routes, 2h tests, 1-2h documentation/polish)
