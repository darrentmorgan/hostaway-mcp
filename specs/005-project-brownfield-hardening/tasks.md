# Implementation Tasks: MCP Server Context Window Protection

**Feature Branch**: `005-project-brownfield-hardening`
**Specification**: [spec.md](./spec.md)
**Implementation Plan**: [plan.md](./plan.md)
**Generated**: 2025-10-15

## Overview

This document breaks down the implementation into actionable tasks organized by user story. Each phase represents an independently testable increment delivering specific value.

**Total Tasks**: 85 tasks
**Estimated Duration**: 15-16 days (with parallelization)
**MVP Scope**: User Story 1 (Paginated List Results) - 25 tasks

---

## Task Organization Strategy

Tasks are organized to enable **incremental delivery per user story**:

1. **Phase 1: Setup** (Infrastructure shared across all stories)
2. **Phase 2: Foundational Prerequisites** (Must complete before any story)
3. **Phase 3: US1 - Paginated List Results (P1)** - MVP
4. **Phase 4: US2 - Automatic Response Summarization (P1)**
5. **Phase 5: US3 - Configurable Token Budgets (P2)**
6. **Phase 6: US4 - Response Chunking (P2)**
7. **Phase 7: US5 - Telemetry and Monitoring (P3)**
8. **Phase 8: Polish & Cross-Cutting Concerns**

**Parallelization**: Tasks marked with `[P]` can run in parallel within their phase.

---

## Phase 1: Setup (Infrastructure)

**Goal**: Initialize project structure and shared utilities needed by all user stories

**Duration**: 1-2 days | **Parallelizable**: All tasks [P]

### T001: [Setup][P] Install watchdog dependency
**File**: `pyproject.toml`
**Description**: Add `watchdog>=3.0.0` to dependencies for file watcher (config hot-reload)
**Acceptance**: Dependency added, `uv sync` or `pip install` succeeds
**Story**: Shared Infrastructure

### T002: [Setup][P] Create cursor codec utility
**File**: `src/utils/cursor_codec.py`
**Description**: Implement Base64+HMAC-SHA256 cursor encoding/decoding per research.md R002
```python
def encode_cursor(payload: dict, secret: str) -> str
def decode_cursor(cursor: str, secret: str) -> dict | raises ValueError
```
**Acceptance**: Cursors are opaque, signed, decode-able, tamper-proof
**Story**: Shared Infrastructure

### T003: [Setup][P] Create field projector utility
**File**: `src/utils/field_projector.py`
**Description**: Implement JSON path field projection utility
```python
def project_fields(obj: dict, field_paths: list[str]) -> dict
```
**Acceptance**: Can select nested fields like `"price.basePrice"`, returns partial object
**Story**: Shared Infrastructure

### T004: [Setup][P] Create in-memory cursor storage
**File**: `src/services/cursor_storage.py`
**Description**: Implement thread-safe in-memory cursor storage with 10-minute TTL
```python
class InMemoryCursorStorage:
    def store(cursor_id: str, payload: dict) -> None
    def retrieve(cursor_id: str) -> Optional[dict]
    def cleanup_expired() -> int
```
**Acceptance**: TTL enforced, expired cursors cleaned up, thread-safe
**Story**: Shared Infrastructure

---

## Phase 2: Foundational Prerequisites

**Goal**: Core infrastructure that blocks all user stories - must complete first

**Duration**: 2-3 days | **Parallelizable**: T005-T008 [P], then T009-T010 sequentially

### T005: [Foundation][P] Write unit tests for cursor codec
**File**: `tests/unit/test_cursor_codec.py`
**Description**: Test encoding, decoding, signature validation, expiry, tampering
**Acceptance**: 80%+ coverage, signature validation prevents tampering
**Story**: Foundation - TDD

### T006: [Foundation][P] Write unit tests for field projector
**File**: `tests/unit/test_field_projector.py`
**Description**: Test field selection, nested paths, missing fields, edge cases
**Acceptance**: 80%+ coverage, handles nested objects correctly
**Story**: Foundation - TDD

### T007: [Foundation][P] Write unit tests for cursor storage
**File**: `tests/unit/test_cursor_storage.py`
**Description**: Test store, retrieve, TTL expiration, cleanup, thread safety
**Acceptance**: 80%+ coverage, TTL works correctly
**Story**: Foundation - TDD

### T008: [Foundation][P] Extend HostawayConfig base
**File**: `src/mcp/config.py`
**Description**: Add base configuration fields for context protection (without story-specific fields yet)
```python
class ContextProtectionConfig(BaseSettings):
    enabled: bool = True
    # Story-specific fields added in their phases
```
**Acceptance**: Pydantic validation works, environment variable overrides work
**Story**: Foundation

### T009: [Foundation] Update main.py to initialize cursor storage
**File**: `src/api/main.py`
**Description**: Initialize InMemoryCursorStorage in lifespan, add cleanup background task
**Acceptance**: Storage available globally, cleanup runs every 60 seconds
**Story**: Foundation
**Depends On**: T004, T008

### T010: [Foundation] Create projection maps skeleton
**File**: `src/mcp/schemas/projection_maps.py`
**Description**: Create empty projection map structure (populated per story)
```python
PROJECTION_MAPS: dict[str, list[str]] = {}
```
**Acceptance**: Module exists, ready for story-specific maps
**Story**: Foundation

**Checkpoint**: ✅ Foundation complete. All user stories can now proceed in parallel.

---

## Phase 3: US1 - Paginated List Results (P1) **MVP**

**User Story**: Claude requests lists and receives manageable pages with cursors

**Goal**: Enable cursor-based pagination on high-volume list endpoints

**Duration**: 3-4 days | **Independent Test**: Call list endpoint with 500 items, verify first 50 returned with cursor

### Models & Services (Parallelizable)

### T011: [US1][P] Write unit tests for pagination models
**File**: `tests/unit/test_pagination_models.py`
**Description**: Test PaginatedResponse, PageMetadata, validation rules
**Acceptance**: 80%+ coverage, generic types work, validation catches errors
**Story**: US1 - TDD

### T012: [US1][P] Create pagination models
**File**: `src/models/pagination.py`
**Description**: Define Pydantic models per data-model.md
```python
class PageMetadata(BaseModel): ...
class PaginatedResponse(BaseModel, Generic[T]): ...
```
**Acceptance**: Type-safe, generic, passes unit tests
**Story**: US1
**Depends On**: T011

### T013: [US1][P] Write unit tests for pagination service
**File**: `tests/unit/test_pagination_service.py`
**Description**: Test cursor generation, page extraction, ordering, final page detection
**Acceptance**: 80%+ coverage, cursors are stable and consistent
**Story**: US1 - TDD

### T014: [US1][P] Create pagination service
**File**: `src/services/pagination_service.py`
**Description**: Implement pagination logic using cursor codec and storage
```python
class PaginationService:
    def paginate(items: list[T], limit: int, cursor: str | None) -> PaginatedResponse[T]
    def generate_cursor(offset: int, order_by: str) -> str
```
**Acceptance**: Generates signed cursors, handles final page, passes unit tests
**Story**: US1
**Depends On**: T002, T004, T013

### Middleware (Sequential - depends on models/services)

### T015: [US1] Write unit tests for pagination middleware
**File**: `tests/unit/test_pagination_middleware.py`
**Description**: Test cursor extraction, envelope injection, backwards compatibility
**Acceptance**: 80%+ coverage, non-paginated clients get first page
**Story**: US1 - TDD
**Depends On**: T012, T014

### T016: [US1] Create pagination middleware
**File**: `src/api/middleware/pagination_middleware.py`
**Description**: Middleware to extract cursor param, inject pagination envelope
**Acceptance**: Intercepts list responses, adds nextCursor/meta, passes tests
**Story**: US1
**Depends On**: T012, T014, T015

### T017: [US1] Register pagination middleware in main.py
**File**: `src/api/main.py`
**Description**: Add PaginationMiddleware to middleware stack (after auth, before response)
**Acceptance**: Middleware active, logs show pagination decisions
**Story**: US1
**Depends On**: T016

### Configuration

### T018: [US1] Add pagination config to HostawayConfig
**File**: `src/mcp/config.py`
**Description**: Add pagination-specific config fields
```python
default_page_size: int = 50
max_page_size: int = 200
pagination_enabled: bool = True
```
**Acceptance**: Environment variables override defaults, validation enforces limits
**Story**: US1
**Depends On**: T008

### Endpoint Integration (Parallelizable)

### T019: [US1][P] Write integration tests for listings pagination
**File**: `tests/integration/test_pagination_endpoints.py`
**Description**: Test GET /api/v1/listings with cursor navigation, final page
**Acceptance**: Multi-page retrieval works, cursor expiry handled, no cursor = first page
**Story**: US1 - TDD

### T020: [US1][P] Add pagination to listings endpoint
**File**: `src/api/routes/listings.py`
**Description**: Modify `get_listings` to use PaginationService, return PaginatedResponse
**Acceptance**: Returns paginated results, passes integration tests
**Story**: US1
**Depends On**: T012, T014, T017, T019

### T021: [US1][P] Add pagination to bookings endpoint
**File**: `src/api/routes/bookings.py`
**Description**: Modify `get_bookings` to use PaginationService
**Acceptance**: Returns paginated results, consistent with listings
**Story**: US1
**Depends On**: T012, T014, T017

### T022: [US1][P] Add pagination to financial endpoint
**File**: `src/api/routes/financial.py`
**Description**: Modify `get_transactions` to use PaginationService
**Acceptance**: Returns paginated results, consistent with listings
**Story**: US1
**Depends On**: T012, T014, T017

### Contract & E2E Tests

### T023: [US1] Write contract tests for backwards compatibility
**File**: `tests/contract/test_backwards_compatibility.py`
**Description**: Validate non-paginated clients still work, golden response comparison
**Acceptance**: Old clients unaffected, response schemas unchanged (additive only)
**Story**: US1 - TDD
**Depends On**: T020, T021, T022

### T024: [US1] Write E2E test for multi-turn pagination
**File**: `tests/e2e/test_multi_turn_pagination.py`
**Description**: Simulate Claude Desktop fetching multiple pages sequentially
**Acceptance**: Can navigate all pages, final page detected, cursor expiry handled
**Story**: US1 - TDD
**Depends On**: T020

### T025: [US1] US1 acceptance validation
**Description**: Run all US1 tests, verify acceptance scenarios from spec
**Acceptance**:
- ✅ 500 bookings → first 50 + cursor + totalCount
- ✅ Cursor navigation returns next batch with updated cursor
- ✅ 10 items → all returned without pagination overhead
- ✅ Final page → no nextCursor provided
**Story**: US1
**Depends On**: T011-T024

**Checkpoint**: ✅ US1 complete. MVP ready for deployment. Paginated lists prevent context overflow.

---

## Phase 4: US2 - Automatic Response Summarization (P1)

**User Story**: Verbose responses are automatically summarized with drill-down instructions

**Goal**: Prevent single-item context bloat through field projection and summarization

**Duration**: 3-4 days | **Independent Test**: Request verbose booking, verify summary with drill-down instructions

### Models & Services (Parallelizable)

### T026: [US2][P] Write unit tests for token estimator
**File**: `tests/unit/test_token_estimator.py`
**Description**: Test character-based estimation, accuracy tracking, safety margin
**Acceptance**: 80%+ coverage, estimates within 20% for test cases
**Story**: US2 - TDD

### T027: [US2][P] Create token estimator service
**File**: `src/services/token_estimator.py`
**Description**: Implement character-based estimation per research.md R001
```python
def estimate_tokens(text: str) -> int  # 4 chars/token + 20% margin
def track_accuracy(estimated: int, actual: int) -> None
```
**Acceptance**: <20ms for 100KB, accuracy tracked, passes tests
**Story**: US2
**Depends On**: T026

### T028: [US2][P] Write unit tests for token budget models
**File**: `tests/unit/test_token_budget_models.py`
**Description**: Test TokenBudget, BudgetMetadata, threshold comparison
**Acceptance**: 80%+ coverage, budget_used calculation correct
**Story**: US2 - TDD

### T029: [US2][P] Create token budget models
**File**: `src/models/token_budget.py`
**Description**: Define Pydantic models per data-model.md
```python
class TokenBudget(BaseModel):
    threshold: int = 4000
    estimated_tokens: int
    @property budget_used() -> float
    @property summary_mode() -> bool
```
**Acceptance**: Type-safe, passes unit tests
**Story**: US2
**Depends On**: T028

### T030: [US2][P] Write unit tests for summarization models
**File**: `tests/unit/test_summarization_models.py`
**Description**: Test SummaryResponse, SummaryMetadata, DetailsFetchInfo
**Acceptance**: 80%+ coverage, generic types work
**Story**: US2 - TDD

### T031: [US2][P] Create summarization models
**File**: `src/models/summarization.py`
**Description**: Define Pydantic models per data-model.md
```python
class SummaryResponse(BaseModel, Generic[T]): ...
class SummaryMetadata(BaseModel): ...
```
**Acceptance**: Type-safe, passes unit tests
**Story**: US2
**Depends On**: T030

### T032: [US2][P] Write unit tests for summarization service
**File**: `tests/unit/test_summarization_service.py`
**Description**: Test field projection, text truncation, summary generation
**Acceptance**: 80%+ coverage, retains identifying fields, provides drill-down instructions
**Story**: US2 - TDD

### T033: [US2][P] Create summarization service
**File**: `src/services/summarization_service.py`
**Description**: Implement field projection + extractive summarization per research.md R003
```python
def summarize(obj: dict, projection_map: list[str]) -> SummaryResponse
def truncate_text(text: str, max_length: int) -> str
```
**Acceptance**: Uses field projector, semantic truncation, passes tests
**Story**: US2
**Depends On**: T003, T032

### Middleware (Sequential)

### T034: [US2] Write unit tests for token-aware middleware
**File**: `tests/unit/test_token_aware_middleware.py`
**Description**: Test token estimation, threshold comparison, preview mode activation
**Acceptance**: 80%+ coverage, oversized responses trigger summarization
**Story**: US2 - TDD
**Depends On**: T027, T029, T033

### T035: [US2] Create token-aware middleware
**File**: `src/api/middleware/token_aware_middleware.py`
**Description**: Middleware to estimate tokens, switch to preview mode if over threshold
**Acceptance**: Intercepts responses, estimates tokens, applies summarization, passes tests
**Story**: US2
**Depends On**: T027, T029, T033, T034

### T036: [US2] Register token-aware middleware in main.py
**File**: `src/api/main.py`
**Description**: Add TokenAwareMiddleware before pagination (runs after, sees full response)
**Acceptance**: Middleware active, logs show summarization decisions
**Story**: US2
**Depends On**: T035

### Configuration & Projection Maps

### T037: [US2] Add token budget config to HostawayConfig
**File**: `src/mcp/config.py`
**Description**: Add token budget config fields
```python
output_token_threshold: int = 4000
hard_output_token_cap: int = 12000
summarization_enabled: bool = True
```
**Acceptance**: Environment overrides work, validation enforces limits
**Story**: US2
**Depends On**: T018

### T038: [US2][P] Define projection map for bookings
**File**: `src/mcp/schemas/projection_maps.py`
**Description**: Add booking summary field list (id, status, guest, dates, price, property)
**Acceptance**: 7 essential fields, ~70% size reduction
**Story**: US2
**Depends On**: T010

### T039: [US2][P] Define projection map for listings
**File**: `src/mcp/schemas/projection_maps.py`
**Description**: Add listing summary field list (id, name, status, bedrooms, price, location)
**Acceptance**: Essential fields, ~70% size reduction
**Story**: US2
**Depends On**: T010

### T040: [US2][P] Define projection map for financial records
**File**: `src/mcp/schemas/projection_maps.py`
**Description**: Add financial summary field list (id, type, amount, date, status)
**Acceptance**: Essential fields, ~70% size reduction
**Story**: US2
**Depends On**: T010

### Endpoint Integration (Parallelizable)

### T041: [US2][P] Write integration tests for summarization
**File**: `tests/integration/test_summarization_endpoints.py`
**Description**: Test oversized booking → summary, small booking → full, drill-down
**Acceptance**: Threshold triggers summarization, metadata includes drill-down instructions
**Story**: US2 - TDD

### T042: [US2][P] Apply summarization to booking details endpoint
**File**: `src/api/routes/bookings.py`
**Description**: Modify `get_booking_by_id` to support field projection via `?fields=` param
**Acceptance**: Returns summary if oversized, accepts fields param for drill-down
**Story**: US2
**Depends On**: T033, T036, T038, T041

### T043: [US2][P] Apply summarization to listing details endpoint
**File**: `src/api/routes/listings.py`
**Description**: Modify `get_listing_by_id` to support field projection
**Acceptance**: Returns summary if oversized, accepts fields param
**Story**: US2
**Depends On**: T033, T036, T039

### T044: [US2] US2 acceptance validation
**Description**: Run all US2 tests, verify acceptance scenarios from spec
**Acceptance**:
- ✅ 2000+ token booking → summary with essential fields + drill-down instructions
- ✅ Request full financial section → only that section returned
- ✅ <500 token resource → full details without summarization
- ✅ Summary metadata shows estimated tokens, budget used, budget remaining
**Story**: US2
**Depends On**: T026-T043

**Checkpoint**: ✅ US2 complete. Verbose responses no longer cause context overflow. US1+US2 deployed together.

---

## Phase 5: US3 - Configurable Token Budgets (P2)

**User Story**: Operations teams can configure limits via environment/files without code changes

**Goal**: Runtime configuration with hot-reload and per-endpoint overrides

**Duration**: 2-3 days | **Independent Test**: Update config, verify reload without restart

### Configuration System (Parallelizable)

### T045: [US3][P] Write unit tests for extended config
**File**: `tests/unit/test_context_protection_config.py`
**Description**: Test all config fields, validation, defaults, environment overrides
**Acceptance**: 80%+ coverage, invalid values rejected
**Story**: US3 - TDD

### T046: [US3][P] Extend HostawayConfig with all context protection fields
**File**: `src/mcp/config.py`
**Description**: Consolidate all config from US1-US4 into complete ContextProtectionConfig
```python
class ContextProtectionConfig(BaseSettings):
    # Pagination (from US1)
    default_page_size: int = 50
    max_page_size: int = 200
    # Token Budget (from US2)
    output_token_threshold: int = 4000
    hard_output_token_cap: int = 12000
    # Chunking (for US4)
    chunk_size_bytes: int = 8192
    # Feature Flags
    endpoint_overrides: dict[str, dict] = {}
```
**Acceptance**: All fields present, Pydantic validation works, passes tests
**Story**: US3
**Depends On**: T045

### T047: [US3][P] Write unit tests for config reloader
**File**: `tests/unit/test_config_reloader.py`
**Description**: Test file watching, hot-reload, validation before swap, fail-safe
**Acceptance**: 80%+ coverage, invalid config keeps previous, reload <100ms
**Story**: US3 - TDD

### T048: [US3][P] Create config reloader service
**File**: `src/services/config_reloader.py`
**Description**: Implement watchdog-based config reloader per research.md R004
```python
class ConfigReloader:
    def reload() -> None  # Atomic read-validate-swap
    def get_config() -> ContextProtectionConfig
```
**Acceptance**: Thread-safe, validates before applying, passes tests
**Story**: US3
**Depends On**: T001, T046, T047

### T049: [US3] Wire config reloader into main.py lifespan
**File**: `src/api/main.py`
**Description**: Start ConfigReloader observer in lifespan startup, stop in shutdown
**Acceptance**: Config changes detected within 100ms, no request drops
**Story**: US3
**Depends On**: T048

### T050: [US3] Write integration test for config hot-reload
**File**: `tests/integration/test_config_reload.py`
**Description**: Modify config file, verify middleware respects new limits without restart
**Acceptance**: Threshold change reflected in behavior, in-flight requests unaffected
**Story**: US3
**Depends On**: T049

### Feature Flags (Parallelizable)

### T051: [US3][P] Implement per-endpoint feature flag logic
**File**: `src/api/middleware/pagination_middleware.py` and `token_aware_middleware.py`
**Description**: Check `endpoint_overrides` config before applying pagination/summarization
**Acceptance**: Can disable pagination for specific endpoint, others unaffected
**Story**: US3
**Depends On**: T046

### T052: [US3] Write integration test for feature flags
**File**: `tests/integration/test_feature_flags.py`
**Description**: Disable pagination for one endpoint, verify others still paginated
**Acceptance**: Granular control per endpoint works
**Story**: US3
**Depends On**: T051

### T053: [US3] US3 acceptance validation
**Description**: Run all US3 tests, verify acceptance scenarios from spec
**Acceptance**:
- ✅ Update threshold 4000→8000, subsequent responses respect 8000
- ✅ Feature flag enables pagination for specific endpoint only
- ✅ New deployment uses documented safe defaults (4000 tokens, 50 items/page)
- ✅ Invalid config → error logged, current config remains active
**Story**: US3
**Depends On**: T045-T052

**Checkpoint**: ✅ US3 complete. Operations teams can tune limits without code deployments.

---

## Phase 6: US4 - Response Chunking (P2)

**User Story**: Large text content chunked with semantic boundaries and continuation cursors

**Goal**: Progressive access to logs, descriptions, documents

**Duration**: 2-3 days | **Independent Test**: Request 50KB log file, verify chunked with semantic boundaries

### Models & Services (Parallelizable)

### T054: [US4][P] Write unit tests for content chunk models
**File**: `tests/unit/test_content_chunk_models.py`
**Description**: Test ContentChunk, ChunkMetadata, validation rules
**Acceptance**: 80%+ coverage, chunk index validation works
**Story**: US4 - TDD

### T055: [US4][P] Create content chunk models
**File**: `src/models/content_chunk.py`
**Description**: Define Pydantic models per data-model.md
```python
class ChunkMetadata(BaseModel): ...
class ContentChunk(BaseModel): ...
```
**Acceptance**: Type-safe, passes unit tests
**Story**: US4
**Depends On**: T054

### T056: [US4][P] Write unit tests for chunking service
**File**: `tests/unit/test_chunking_service.py`
**Description**: Test semantic boundary detection, range requests, chunk cursor generation
**Acceptance**: 80%+ coverage, no mid-sentence splits, respects line/paragraph boundaries
**Story**: US4 - TDD

### T057: [US4][P] Create chunking service
**File**: `src/services/chunking_service.py`
**Description**: Implement chunking with semantic boundaries per research.md
```python
def chunk_content(content: str, chunk_size: int) -> ContentChunk
def chunk_by_range(content: str, start_line: int, end_line: int) -> ContentChunk
```
**Acceptance**: Semantic boundaries respected, passes tests
**Story**: US4
**Depends On**: T002, T056

### Endpoint Integration

### T058: [US4] Add chunking config to HostawayConfig
**File**: `src/mcp/config.py`
**Description**: Add `chunk_size_bytes: int = 8192` to config
**Acceptance**: Environment override works
**Story**: US4
**Depends On**: T046

### T059: [US4] Write integration test for chunking
**File**: `tests/integration/test_content_chunking.py`
**Description**: Test large log file → chunks, range request, multi-chunk retrieval
**Acceptance**: Chunks respect semantic boundaries, continuation cursors work
**Story**: US4 - TDD

### T060: [US4] Add chunking to hypothetical logs endpoint (if exists)
**File**: `src/api/routes/analytics.py` (or create new logs route)
**Description**: Apply chunking service to large text responses (logs, descriptions)
**Acceptance**: >2000 token content chunked, <1000 token content returned whole
**Story**: US4
**Depends On**: T057, T058, T059

### T061: [US4] US4 acceptance validation
**Description**: Run all US4 tests, verify acceptance scenarios from spec
**Acceptance**:
- ✅ 10,000 line log → first 200 lines + cursor + total count
- ✅ Chunks end at log entry/paragraph/sentence completion (no mid-splits)
- ✅ Range request (startLine=100, endLine=200) → only that range
- ✅ <1000 token content → full content without chunking
**Story**: US4
**Depends On**: T054-T060

**Checkpoint**: ✅ US4 complete. Large content accessible progressively without context overflow.

---

## Phase 7: US5 - Telemetry and Monitoring (P3)

**User Story**: Engineers observe token usage, pagination adoption, overflow attempts via dashboards

**Goal**: Operational visibility for optimization and debugging

**Duration**: 2-3 days | **Independent Test**: Make 100 requests, verify metrics captured accurately

### Models & Services (Parallelizable)

### T062: [US5][P] Write unit tests for telemetry models
**File**: `tests/unit/test_telemetry_models.py`
**Description**: Test TelemetryRecord, computed properties, validation
**Acceptance**: 80%+ coverage, tokens_per_item calculation correct
**Story**: US5 - TDD

### T063: [US5][P] Create telemetry models
**File**: `src/models/telemetry.py`
**Description**: Define Pydantic models per data-model.md
```python
class TelemetryRecord(BaseModel):
    request_id: str
    endpoint: str
    estimated_tokens: int
    response_bytes: int
    pagination_used: bool
    summarization_used: bool
    # ... etc
```
**Acceptance**: Type-safe, passes unit tests
**Story**: US5
**Depends On**: T062

### Middleware

### T064: [US5] Write unit tests for telemetry middleware
**File**: `tests/unit/test_telemetry_middleware.py`
**Description**: Test metrics recording, overhead <10ms, fire-and-forget (no failures)
**Acceptance**: 80%+ coverage, telemetry failures don't affect requests
**Story**: US5 - TDD

### T065: [US5] Create telemetry middleware
**File**: `src/api/middleware/telemetry_middleware.py`
**Description**: Middleware to record per-request metrics
**Acceptance**: Captures all required fields, <10ms overhead, passes tests
**Story**: US5
**Depends On**: T063, T064

### T066: [US5] Register telemetry middleware in main.py
**File**: `src/api/main.py`
**Description**: Add TelemetryMiddleware (runs first, sees full request/response cycle)
**Acceptance**: Middleware active, metrics logged at INFO level
**Story**: US5
**Depends On**: T065

### Metrics & Logging

### T067: [US5][P] Implement metrics emission (Prometheus format)
**File**: `src/services/metrics_emitter.py`
**Description**: Emit metrics in Prometheus/StatsD format for external collection
```python
def emit_metric(record: TelemetryRecord) -> None
```
**Acceptance**: Metrics queryable by endpoint, time range, outcome
**Story**: US5

### T068: [US5][P] Add oversized event logging
**File**: `src/api/middleware/token_aware_middleware.py`
**Description**: Log oversized response attempts (original size, final size, reduction %)
**Acceptance**: INFO logs include context for debugging
**Story**: US5
**Depends On**: T035

### T069: [US5][P] Add accuracy sampling logic
**File**: `src/services/token_estimator.py`
**Description**: Sample 1% of responses, log estimated vs actual (if actual available)
**Acceptance**: Sampling rate configurable, logs enable accuracy tuning
**Story**: US5
**Depends On**: T027

### Health Endpoint Extensions

### T070: [US5] Extend /health endpoint with pagination metrics
**File**: `src/api/main.py`
**Description**: Add pagination adoption rate, avg response size to health response
```python
{
  "status": "healthy",
  "metrics": {
    "pagination_adoption": 0.95,
    "avg_response_size": 2400,
    "oversized_events": 12
  }
}
```
**Acceptance**: Metrics updated in real-time from TelemetryRecords
**Story**: US5
**Depends On**: T065

### Integration Tests

### T071: [US5] Write integration test for telemetry
**File**: `tests/integration/test_telemetry_recording.py`
**Description**: Make 100 requests, verify all metrics captured accurately
**Acceptance**: Metrics match actual request characteristics
**Story**: US5 - TDD
**Depends On**: T066

### T072: [US5] Write load test for telemetry overhead
**File**: `tests/integration/test_telemetry_performance.py`
**Description**: Verify telemetry adds ≤10ms latency under 100 concurrent requests
**Acceptance**: p95 latency increase ≤10ms
**Story**: US5 - TDD
**Depends On**: T066

### T073: [US5] US5 acceptance validation
**Description**: Run all US5 tests, verify acceptance scenarios from spec
**Acceptance**:
- ✅ 100 requests → all record tokens, bytes, items, latency
- ✅ Oversized event → log includes original size, final size, reduction %
- ✅ Pagination usage tracked separately from non-paginated requests
- ✅ Alerts triggered when oversized attempts >5% of traffic
**Story**: US5
**Depends On**: T062-T072

**Checkpoint**: ✅ US5 complete. Full observability enables data-driven optimization.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Goal**: Final integration, documentation, and deployment readiness

**Duration**: 2-3 days

### Documentation

### T074: [Polish] Update API documentation (OpenAPI)
**File**: FastAPI auto-generated docs
**Description**: Ensure pagination params, token budget metadata documented in /docs
**Acceptance**: OpenAPI spec includes all new fields, backwards compatibility noted
**Story**: Polish

### T075: [Polish] Create operator runbook
**File**: `docs/CONTEXT_PROTECTION_RUNBOOK.md`
**Description**: Document tuning thresholds, reading dashboards, common errors, troubleshooting
**Acceptance**: Runbook covers all operational scenarios from quickstart.md
**Story**: Polish

### Contract & E2E Validation

### T076: [Polish] Write contract test for response schema additive-only
**File**: `tests/contract/test_response_schemas.py`
**Description**: Validate all enhanced responses are additive (no removed fields)
**Acceptance**: Golden response comparison passes, breaking changes detected
**Story**: Polish

### T077: [Polish] Write E2E test for summary → detail drill-down
**File**: `tests/e2e/test_summary_drilldown.py`
**Description**: Request summary, follow detailsAvailable instructions, verify full object
**Acceptance**: Multi-turn workflow works end-to-end
**Story**: Polish
**Depends On**: US1+US2 complete

### T078: [Polish] Write E2E test for token budget simulation
**File**: `tests/e2e/test_token_budget_simulation.py`
**Description**: Simulate context overflow scenarios, verify prevention
**Acceptance**: No requests exceed hard cap, summarization activates correctly
**Story**: Polish
**Depends On**: US2 complete

### Load & Performance Testing

### T079: [Polish] Write load test for pagination overhead
**File**: `tests/integration/test_pagination_performance.py`
**Description**: Verify pagination adds <50ms latency under 100 concurrent requests
**Acceptance**: p95 pagination overhead <50ms
**Story**: Polish
**Depends On**: US1 complete

### T080: [Polish] Write load test for token estimation performance
**File**: `tests/integration/test_token_estimation_performance.py`
**Description**: Verify estimation completes <20ms for 100KB responses
**Acceptance**: p95 estimation time <20ms
**Story**: Polish
**Depends On**: US2 complete

### T081: [Polish] Write load test for overall system performance
**File**: `tests/integration/test_system_performance.py`
**Description**: Verify overall p95 latency increase ≤10% with all features enabled
**Acceptance**: Baseline vs hardened comparison, <10% increase
**Story**: Polish
**Depends On**: All US complete

### Deployment Preparation

### T082: [Polish] Create feature flag configuration template
**File**: `config/context_protection.yaml.example`
**Description**: Document all config options with safe defaults for production
**Acceptance**: Example config covers all scenarios from quickstart.md
**Story**: Polish

### T083: [Polish] Create canary deployment checklist
**File**: `docs/CANARY_DEPLOYMENT.md`
**Description**: Document 5% → 25% → 50% → 100% rollout process, metrics to monitor, rollback procedure
**Acceptance**: Checklist actionable for operations team
**Story**: Polish

### T084: [Polish] Write A/B testing mode toggle
**File**: `src/mcp/config.py`
**Description**: Add `ab_test_mode: bool` to compare responses with/without hardening
**Acceptance**: Can run dual mode for validation
**Story**: Polish
**Depends On**: T046

### Final Validation

### T085: [Polish] Full acceptance criteria validation
**Description**: Run all tests, verify all success criteria from spec.md
**Acceptance**:
- ✅ All 5 user story acceptance scenarios pass
- ✅ All 36 functional requirements (FR-001 to FR-036) satisfied
- ✅ All 8 success criteria (SC-001 to SC-008) achievable
- ✅ 80%+ code coverage across all modules
- ✅ No regressions in existing functionality
**Story**: Polish
**Depends On**: T001-T084

**Checkpoint**: ✅ All phases complete. Feature ready for canary deployment.

---

## Dependency Graph

```
Setup (T001-T004) [ALL PARALLEL]
    ↓
Foundation (T005-T010) [T005-T008 PARALLEL, then T009-T010]
    ↓
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│              │              │              │              │              │
US1 (T011-T025)│ US2 (T026-T044)│ US3 (T045-T053)│ US4 (T054-T061)│ US5 (T062-T073)│
P1 - MVP       │ P1           │ P2           │ P2           │ P3           │
│              │              │              │              │              │
│  (US1 must   │  (Depends    │  (Depends    │  (Can run    │  (Can run    │
│  complete    │  on US1)     │  on US1+US2) │  parallel    │  parallel    │
│  first)      │              │              │  with US3)   │  with US3+US4)│
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │              │              │
       └──────────────┴──────────────┴──────────────┴──────────────┘
                                     ↓
                         Polish (T074-T085)
                         (Final integration)
```

**Critical Path**:
1. Setup → Foundation → US1 (MVP)
2. US1 → US2 (builds on pagination)
3. US2 → US3 (needs token budget to configure)
4. US3 → US4, US5 can run in parallel
5. All → Polish & Final Validation

---

## Parallel Execution Examples

### Example 1: Phase 1 (Setup) - 4 parallel tasks
```bash
# All 4 tasks can run simultaneously (different files, no dependencies)
Developer 1: T001 (pyproject.toml)
Developer 2: T002 (cursor_codec.py)
Developer 3: T003 (field_projector.py)
Developer 4: T004 (cursor_storage.py)

Timeline: 1 day (vs 4 days sequential)
```

### Example 2: US1 Models & Services - 4 parallel tasks
```bash
# After T011-T013 tests written, implementation can parallelize:
Developer 1: T012 (pagination models)
Developer 2: T014 (pagination service)
Developer 3: T019 (integration tests)
Developer 4: T020 (listings endpoint)

Timeline: 1 day (vs 4 days sequential)
```

### Example 3: US2 Projection Maps - 3 parallel tasks
```bash
# Different files, independent definitions:
Developer 1: T038 (bookings projection map)
Developer 2: T039 (listings projection map)
Developer 3: T040 (financial projection map)

Timeline: 0.5 days (vs 1.5 days sequential)
```

---

## Implementation Strategy

### MVP First (US1 Only)

**Recommended Approach**: Deploy US1 alone to production first

**Rationale**:
- Addresses 80% of context overflow issues (unbounded lists)
- Independently testable and valuable
- Lower risk for first deployment
- Validates infrastructure before adding complexity

**MVP Tasks**: T001-T025 (25 tasks, ~5 days with 3 developers)

**Validation**: After US1 deployed, monitor for 1 week:
- Pagination adoption rate
- Context overflow reduction
- Performance impact
- Client compatibility

### Incremental Rollout

1. **Week 1**: US1 (MVP) - Paginated lists
2. **Week 2**: US2 - Summarization (builds on US1)
3. **Week 3**: US3 + US4 in parallel - Configuration + Chunking
4. **Week 4**: US5 + Polish - Telemetry + Final validation
5. **Week 5**: Canary deployment and GA

---

## Task Count Summary

| Phase | Tasks | Parallelizable | Estimated Days |
|-------|-------|----------------|----------------|
| Setup | 4 | 4 (100%) | 1-2 |
| Foundation | 6 | 4 (67%) | 2-3 |
| US1 (MVP) | 15 | 9 (60%) | 3-4 |
| US2 | 19 | 11 (58%) | 3-4 |
| US3 | 9 | 6 (67%) | 2-3 |
| US4 | 8 | 5 (63%) | 2-3 |
| US5 | 12 | 6 (50%) | 2-3 |
| Polish | 12 | 6 (50%) | 2-3 |
| **TOTAL** | **85** | **51 (60%)** | **15-16** |

---

## Success Metrics Validation

After T085 completion, verify these metrics are achievable:

- **SC-001**: 99.9% sessions without context overflow → Run E2E tests with 1000 multi-step workflows
- **SC-002**: 60% token reduction → Compare baseline vs hardened avg response size
- **SC-003**: 95% pagination adoption → Check health endpoint metrics after 2 weeks
- **SC-004**: 80% truncation ticket reduction → Monitor support tickets for 1 month
- **SC-005**: ≤10% latency increase → Load test results (T081)
- **SC-006**: 5-min diagnostics → Time troubleshooting scenarios with telemetry
- **SC-007**: 95% successful pagination → Contract tests + E2E tests pass rate
- **SC-008**: 90% estimation accuracy → Sampling logs from T069

---

**Status**: Tasks generated. Ready for implementation. Start with T001-T004 (Setup phase).

**Next Steps**:
1. Review task breakdown with team
2. Assign T001-T004 to developers (all parallelizable)
3. Begin TDD implementation
4. Track progress using task completion checkboxes
5. Deploy US1 (MVP) after T025 validation
