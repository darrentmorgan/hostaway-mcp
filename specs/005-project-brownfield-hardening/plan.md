# Implementation Plan: MCP Server Context Window Protection

**Branch**: `005-project-brownfield-hardening` | **Date**: 2025-10-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-project-brownfield-hardening/spec.md`

## Summary

This plan implements brownfield hardening for the existing Hostaway MCP server to prevent context window overflow. The solution adds cursor-based pagination, automatic response summarization, dynamic content chunking, and token budget awareness through middleware-based interception. All capabilities are configurable and backwards compatible with existing clients.

**Primary Goals:**
1. Prevent context overflow by default (99.9% session success rate vs current 60%)
2. Reduce average token usage per response by 60% (6000 → 2400 tokens)
3. Enable runtime configuration without code changes
4. Maintain full backwards compatibility with existing clients

**Technical Approach:**
- Middleware-based token estimation and response shaping
- Cursor-based pagination with opaque, signed cursors
- Field projection and semantic summarization for verbose responses
- Feature flags for gradual, per-endpoint rollout
- Comprehensive telemetry for observability and optimization

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: FastAPI 0.100+, fastapi-mcp 0.4+, httpx 0.27+, Pydantic 2.0+, pydantic-settings
**Storage**: Supabase PostgreSQL (multi-tenant with RLS), Redis/in-memory for pagination cursor cache
**Testing**: pytest + pytest-asyncio, pytest-cov (80% minimum coverage)
**Target Platform**: Linux server (uvicorn ASGI)
**Project Type**: Single server (FastAPI web application with MCP protocol integration)
**Performance Goals**:
- API response time: <500ms (p95)
- MCP tool invocation: <1s total
- Concurrent requests: 100+ simultaneous
- Pagination overhead: <50ms per request
- Token estimation: <20ms for responses up to 100KB
**Constraints**:
- Backwards compatible JSON shapes (additive fields only)
- No changes to MCP protocol or transport
- Response time increase ≤10% (p95)
- Metric recording overhead ≤10ms
**Scale/Scope**:
- ~20 MCP tools (listings, bookings, financial, analytics)
- Mixed workload: 10s to 100k+ items per endpoint
- Multi-tenant with organization-level isolation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. API-First Design ✅ PASS

**Requirement**: Every feature exposed as FastAPI endpoint before MCP tool
**Compliance**: This feature enhances existing FastAPI endpoints with pagination/summarization middleware. All endpoints already follow API-first pattern.
**Action**: No violations. Middleware augments existing endpoints without changing API-first architecture.

### II. Type Safety (NON-NEGOTIABLE) ✅ PASS

**Requirement**: All code must pass `mypy --strict`, use Pydantic models, type annotations
**Compliance**: Plan requires:
- Pydantic models for configuration (TokenBudgetConfig, PaginationConfig)
- Typed cursor encoding/decoding functions
- Type-annotated middleware classes
- Typed response wrappers (PaginatedResponse[T], SummaryResponse[T])
**Action**: All new code will maintain strict type safety per constitution.

### III. Security by Default ✅ PASS

**Requirement**: Authentication, input validation, rate limiting, audit logging
**Compliance**:
- Pagination cursors will be cryptographically signed (prevent tampering)
- All parameters validated via Pydantic (limit ranges, cursor format)
- No new authentication required (uses existing MCPAuthMiddleware)
- Token estimation metadata doesn't leak sensitive internals
**Action**: Security-by-default maintained. No new attack surfaces.

### IV. Test-Driven Development ✅ PASS

**Requirement**: 80% coverage, unit/integration/E2E tests
**Compliance**: Plan includes:
- Unit tests: cursor encoding, token estimation, field projection, summary logic
- Integration tests: paginated endpoint responses, configuration reload
- Contract tests: backwards compatibility validation
- Load tests: p95 latency verification
- E2E tests: multi-turn pagination with Claude Desktop
**Action**: TDD enforced. All code will meet 80% coverage threshold.

### V. Async Performance ✅ PASS

**Requirement**: All I/O async, no blocking calls, connection pooling
**Compliance**:
- Middleware uses async/await throughout
- Token estimation is synchronous but <20ms (acceptable)
- Cursor storage uses async Redis client (aioredis)
- No blocking calls in request path
**Action**: Async-first maintained. Performance targets met.

### Re-evaluation Gate (Post-Design)

✅ **PASS** - All constitution principles satisfied. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```
specs/005-project-brownfield-hardening/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0: Token estimation, cursor encoding research
├── data-model.md        # Phase 1: Pagination, budget, summary entities
├── quickstart.md        # Phase 1: Developer guide for using pagination/summarization
├── contracts/           # Phase 1: OpenAPI schemas for enhanced endpoints
│   ├── pagination.yaml
│   ├── token-budget.yaml
│   └── summarization.yaml
└── tasks.md             # Phase 2: Task breakdown (NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/
├── models/
│   ├── pagination.py         # PaginatedResponse[T], PaginationCursor, PageMetadata
│   ├── token_budget.py       # TokenBudget, TokenEstimator, BudgetMetadata
│   └── summarization.py      # SummaryResponse[T], FieldProjection, SummaryStrategy
│
├── services/
│   ├── pagination_service.py     # Cursor encoding/decoding, page state management
│   ├── token_estimator.py        # Character-based estimation, accuracy tracking
│   ├── summarization_service.py  # Field projection, text truncation, summary generation
│   └── cursor_storage.py         # Redis/in-memory cursor cache with TTL
│
├── api/
│   ├── middleware/
│   │   ├── token_aware_middleware.py  # Output shaper, token estimation, preview mode
│   │   ├── pagination_middleware.py   # Cursor extraction, pagination envelope injection
│   │   └── telemetry_middleware.py    # Metrics recording, oversized event tracking
│   │
│   ├── routes/
│   │   ├── listings.py        # Enhanced with pagination/summarization
│   │   ├── bookings.py        # Enhanced with pagination/summarization
│   │   ├── financial.py       # Enhanced with pagination/summarization
│   │   └── analytics.py       # Enhanced with pagination/summarization
│   │
│   └── dependencies.py        # Pagination/budget dependency injection
│
├── mcp/
│   ├── config.py              # Extended with context protection config
│   └── schemas/
│       ├── projection_maps.py # Per-endpoint field projection definitions
│       └── summary_templates.py # Summary format templates
│
└── utils/
    ├── cursor_codec.py        # Opaque cursor encoding/decoding with signing
    └── field_projector.py     # JSON field selection utility

tests/
├── unit/
│   ├── test_pagination_service.py
│   ├── test_token_estimator.py
│   ├── test_summarization_service.py
│   ├── test_cursor_codec.py
│   └── test_field_projector.py
│
├── integration/
│   ├── test_pagination_endpoints.py    # List endpoints with cursor navigation
│   ├── test_summarization_endpoints.py # Large responses triggering preview mode
│   ├── test_token_budget_middleware.py # Budget threshold enforcement
│   └── test_config_reload.py           # Hot reload verification
│
├── contract/
│   ├── test_backwards_compatibility.py # Golden responses validation
│   └── test_response_schemas.py        # Additive fields only
│
└── e2e/
    ├── test_multi_turn_pagination.py   # Claude Desktop pagination workflow
    └── test_token_budget_simulation.py # Context overflow prevention

dashboard/
└── (existing Next.js dashboard - no changes required)
```

**Structure Decision**: Single-project layout maintained. All context protection features implemented as middleware and services within existing `src/` structure. Leverages FastAPI middleware pipeline for request/response interception. No changes to dashboard required (server-side only).

## Complexity Tracking

*No constitution violations requiring justification. This section intentionally left empty.*

## Phase 0: Research & Technical Decisions

### Research Areas

**R001**: Token Estimation Strategies
- **Question**: What's the optimal balance between estimation speed and accuracy?
- **Options**: Character-based (4 chars/token), byte-based, tiktoken library, ML model
- **Decision Needed**: Choose estimation method and validate accuracy vs latency trade-off

**R002**: Cursor Encoding Format
- **Question**: How should pagination cursors be encoded securely and efficiently?
- **Options**: Base64 + HMAC, JWT, encrypted position, hash-based
- **Decision Needed**: Select encoding strategy balancing security, size, and performance

**R003**: Summarization Techniques
- **Question**: What summarization approaches work best for structured API responses?
- **Options**: Field projection, extractive (top-K), abstractive (LLM), hybrid
- **Decision Needed**: Define summarization strategy per data type (list vs detail)

**R004**: Configuration Hot-Reload Mechanism
- **Question**: How to reload configuration without dropping in-flight requests?
- **Options**: File watcher + reload, signal handler (SIGHUP), external config service
- **Decision Needed**: Implement safe hot-reload without request interruption

**R005**: Cursor Storage Backend
- **Question**: Where to store pagination state for 10-minute TTL?
- **Options**: Redis, in-memory (dict + TTL), database table, file cache
- **Decision Needed**: Select storage with TTL support and acceptable performance

### Research Outputs

See [research.md](./research.md) for detailed findings and decisions.

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](./data-model.md) for complete entity definitions, relationships, and validation rules.

**Key Entities** (summary):

1. **PaginationCursor**: Opaque token encoding page position, valid for 10 minutes
2. **TokenBudget**: Per-request token limit tracking and threshold enforcement
3. **ResponseSummary**: Condensed representation with essential fields + drill-down instructions
4. **ContentChunk**: Semantic segment of large content with continuation cursor
5. **TelemetryRecord**: Per-request metrics (tokens, bytes, items, latency, optimizations)

### API Contracts

See [contracts/](./contracts/) for OpenAPI 3.0 schemas.

**Enhanced Response Envelope** (additive, backwards compatible):

```yaml
# contracts/pagination.yaml
PaginatedResponse:
  type: object
  properties:
    items:
      type: array
      items:
        $ref: '#/components/schemas/ListingItem'  # Example
    nextCursor:
      type: string
      nullable: true
      description: Opaque cursor for next page (null on final page)
    meta:
      type: object
      properties:
        totalCount:
          type: integer
          description: Total items across all pages
        pageSize:
          type: integer
          description: Items per page (actual, may be less than limit on final page)
        hasMore:
          type: boolean
          description: Whether additional pages exist

# contracts/token-budget.yaml
TokenBudgetMetadata:
  type: object
  properties:
    estimatedTokens:
      type: integer
      description: Estimated tokens in this response
    budgetThreshold:
      type: integer
      description: Configured token limit for this endpoint
    budgetUsed:
      type: number
      format: float
      description: Percentage of budget used (0.0-1.0)
    summaryMode:
      type: boolean
      description: Whether response was summarized to stay under budget

# contracts/summarization.yaml
SummaryResponse:
  type: object
  properties:
    summary:
      type: object
      description: Condensed essential fields
    meta:
      type: object
      properties:
        kind:
          type: string
          enum: [preview, full]
        totalFields:
          type: integer
          description: Total fields available in full object
        projectedFields:
          type: array
          items:
            type: string
          description: Fields included in this summary
        detailsAvailable:
          type: object
          description: How to fetch full details
          properties:
            endpoint:
              type: string
            parameters:
              type: object
```

**Pagination Parameters** (query params, optional, backwards compatible):

```yaml
PaginationParams:
  - name: limit
    in: query
    schema:
      type: integer
      minimum: 1
      maximum: 200
      default: 50
    description: Items per page (default 50, max 200)

  - name: cursor
    in: query
    schema:
      type: string
    description: Opaque cursor from previous page's nextCursor field
```

### Developer Quickstart

See [quickstart.md](./quickstart.md) for comprehensive developer guide covering:
- How to use pagination in tool calls
- How to interpret summary responses
- How to configure token budgets
- How to observe telemetry data
- Common patterns and troubleshooting

## Phase 2: Implementation Roadmap

### Epic 1: Pagination Foundation (P1)

**Goal**: Enable cursor-based pagination on high-volume list endpoints

**Components**:
1. Pagination models (PaginatedResponse[T], PaginationCursor)
2. Cursor encoding service (signed, opaque cursors)
3. Cursor storage (Redis with 10-minute TTL)
4. Pagination middleware (cursor extraction, envelope injection)
5. Configuration (default/max page sizes, feature flags)

**Tests**:
- Unit: Cursor encoding/decoding, signature validation
- Integration: List endpoints with cursor navigation
- Contract: Backwards compatibility (no cursor = first page)

**Acceptance Criteria** (from spec):
- FR-001 to FR-008 satisfied
- SC-003: 95% pagination adoption within 2 weeks

### Epic 2: Token Budget Awareness (P1)

**Goal**: Automatically summarize responses exceeding token thresholds

**Components**:
1. Token estimation service (character-based + accuracy tracking)
2. Token budget models (TokenBudget, BudgetMetadata)
3. Token-aware middleware (estimation, threshold comparison, preview mode)
4. Configuration (budget thresholds, hard caps, feature flags)

**Tests**:
- Unit: Token estimation accuracy (within 20% for 90% of responses)
- Integration: Oversized responses trigger summarization
- Chaos: Forced oversize responses activate preview mode

**Acceptance Criteria** (from spec):
- FR-009 to FR-014 satisfied
- SC-002: 60% token reduction (6000 → 2400 avg)
- SC-008: Estimation accuracy ≥90% within 20% margin

### Epic 3: Summarization & Compression (P1)

**Goal**: Provide condensed representations of verbose data

**Components**:
1. Summarization models (SummaryResponse[T], FieldProjection)
2. Field projection service (JSON path selection)
3. Projection maps per endpoint (booking summary, listing summary, etc.)
4. Text truncation utilities (semantic boundaries)
5. Summary template system (instructions for fetching details)

**Tests**:
- Unit: Field projection correctness, text truncation semantics
- Integration: Summaries retain identifying fields, provide drill-down instructions
- E2E: Multi-turn workflow (summary → detail request)

**Acceptance Criteria** (from spec):
- FR-015 to FR-019 satisfied
- SC-007: 95% successful pagination navigation

### Epic 4: Content Chunking (P2)

**Goal**: Progressive access to large text content

**Components**:
1. Content chunk models (ContentChunk, chunk metadata)
2. Chunking service (semantic boundary detection)
3. Range-based request handling (startLine, endLine)
4. Chunk cursor generation

**Tests**:
- Unit: Semantic boundary detection (no mid-sentence splits)
- Integration: Large log files chunked correctly
- E2E: Multi-chunk retrieval workflow

**Acceptance Criteria** (from spec):
- FR-020 to FR-023 satisfied

### Epic 5: Configuration & Feature Flags (P2)

**Goal**: Runtime configuration without code changes

**Components**:
1. Extended HostawayConfig (Pydantic settings with new fields)
2. Configuration schema validation
3. Hot-reload mechanism (file watcher or SIGHUP)
4. Feature flag system (per-endpoint enable/disable)
5. Environment variable overrides

**Tests**:
- Unit: Configuration validation, default values
- Integration: Hot-reload without dropped requests
- Contract: Invalid config reverts to previous state

**Acceptance Criteria** (from spec):
- FR-024 to FR-028 satisfied
- SC-005: Latency increase ≤10% (p95)

### Epic 6: Telemetry & Observability (P3)

**Goal**: Metrics and logging for optimization and debugging

**Components**:
1. Telemetry models (TelemetryRecord)
2. Telemetry middleware (per-request metrics recording)
3. Metrics emission (Prometheus/StatsD compatible)
4. Oversized event logging and sampling
5. Health endpoint extensions (pagination adoption, avg response size)

**Tests**:
- Unit: Metrics recording accuracy
- Integration: Metrics queryable by endpoint/time/outcome
- Load: Telemetry overhead ≤10ms

**Acceptance Criteria** (from spec):
- FR-029 to FR-032 satisfied
- SC-006: 5-minute diagnostics (vs 30+ min currently)

### Epic 7: Backwards Compatibility & Rollout (P2)

**Goal**: Gradual, safe deployment with rollback capability

**Components**:
1. Contract tests (golden response validation)
2. Feature flags per endpoint
3. Canary deployment configuration
4. A/B testing mode
5. Rollback procedures

**Tests**:
- Contract: Old clients receive first page without cursors
- Integration: Feature flags isolate endpoint changes
- E2E: Multi-client compatibility (paginated + non-paginated)

**Acceptance Criteria** (from spec):
- FR-033 to FR-036 satisfied
- Risk mitigation: Canary 5% → 25% → 50% → 100% over 2 weeks

## Testing Strategy

### Test Pyramid

```
          E2E (5%)
       ┌──────────┐
      │  Multi-turn │
     │   workflows  │
    └────────────────┘

    Integration (25%)
  ┌──────────────────┐
 │  Endpoint responses │
│  Config reload, etc. │
└────────────────────────┘

        Unit (70%)
┌────────────────────────────┐
│ Cursor codec, estimator,   │
│ projector, chunking logic  │
└────────────────────────────┘
```

### Test Categories

**Unit Tests** (70% of test count):
- Cursor encoding/decoding + signature validation
- Token estimation accuracy (character-based heuristic)
- Field projection correctness (JSON path selection)
- Summary generation (field retention rules)
- Chunking semantics (boundary detection)
- Configuration validation and defaults

**Integration Tests** (25% of test count):
- Paginated list endpoints (cursor navigation, final page detection)
- Summarized detail endpoints (preview mode activation)
- Token budget middleware (threshold enforcement)
- Configuration hot-reload (no dropped requests)
- Telemetry recording (metrics accuracy)

**Contract Tests** (Subset of integration):
- Golden response validation (before/after comparison)
- Backwards compatibility (non-paginated clients)
- Response schema additive-only validation

**Load Tests** (Performance verification):
- p95 latency impact (target: ≤10% increase)
- Pagination overhead (target: <50ms)
- Token estimation performance (target: <20ms for 100KB)
- Concurrent request handling (target: 100+ simultaneous)

**E2E Tests** (5% of test count):
- Multi-turn pagination workflow with Claude Desktop
- Summary → detail drill-down workflow
- Token budget simulation (context overflow prevention)
- Mixed paginated/non-paginated client scenarios

**Chaos Tests** (Resilience verification):
- Forced oversized responses → preview mode activation
- Cursor expiration handling (graceful error + re-query guidance)
- Invalid pagination parameters (descriptive errors)
- Configuration errors (fail-safe to previous config)

## Non-Functional Requirements

### Performance Targets

- **API Response Time**: <500ms (p95) - no change from baseline
- **Pagination Overhead**: <50ms per request (cursor lookup, state management)
- **Token Estimation**: <20ms for responses up to 100KB
- **Configuration Reload**: <100ms without dropped requests
- **Metric Recording**: ≤10ms latency addition
- **Token Estimation Accuracy**: ≥90% of responses within 20% of actual

### Reliability

- **Cursor Expiration**: Graceful error with clear re-query instructions
- **Token Estimation Failures**: Fall back to byte-based limits (safe default)
- **Configuration Errors**: Revert to previous known-good state, log error
- **Telemetry Failures**: Fire-and-forget (no request failures due to metrics)

### Security

- **Pagination Cursors**: Cryptographically signed (HMAC-SHA256)
- **Token Budget Metadata**: No internal structure leakage
- **Configuration Validation**: Schema checks, range enforcement
- **Cursor Tampering**: Signature verification rejects invalid cursors

### Observability

- **Decision Logging**: All pagination/summarization/chunking decisions at INFO level
- **Accuracy Sampling**: 1% of responses validated against actual tokenizer
- **Configuration Changes**: Logged with old/new values and timestamp
- **Oversized Alerts**: Triggered when >5% of traffic exceeds budget

## Rollout Plan

### Phase 1: Foundation (Week 1)

**Goal**: Audit endpoints, establish metrics scaffolding, design sign-off

**Tasks**:
1. Audit all endpoints → classify as bounded (<50 items) vs eligible (>50 items)
2. Establish telemetry infrastructure (metrics emission, dashboards)
3. Technical design review and constitution re-check
4. Create feature flag configuration for gradual rollout

**Output**: Endpoint classification, metrics dashboards, approved design

### Phase 2: Core Implementation (Weeks 2-3)

**Goal**: Pagination + token shaper for top 3 high-volume endpoints

**Tasks**:
1. Implement pagination models, cursor service, storage
2. Implement token estimator and budget-aware middleware
3. Add pagination to listings, bookings, financial endpoints
4. Write unit and integration tests for core components
5. Validate accuracy and performance targets

**Output**: Top 3 endpoints paginated, token-aware, tested

### Phase 3: Expansion (Week 4)

**Goal**: Extend to remaining endpoints, add summarization, complete observability

**Tasks**:
1. Add pagination to remaining eligible endpoints
2. Implement summarization service and projection maps
3. Add content chunking for large text responses
4. Complete telemetry middleware and dashboards
5. Write E2E tests with Claude Desktop

**Output**: All endpoints hardened, full observability, E2E validated

### Phase 4: Canary & GA (Week 5)

**Goal**: Gradual rollout with monitoring, tune thresholds, go to GA

**Tasks**:
1. Canary deployment: 5% traffic → monitor metrics
2. Expand canary: 25% → 50% → 100% over 2 weeks
3. Tune token thresholds based on telemetry
4. Monitor support tickets for truncation/overflow issues
5. Final performance validation and GA sign-off

**Output**: Production deployment, 95% pagination adoption, 80% ticket reduction

## Risk Mitigation

### Risk 1: Hidden Client Dependencies

**Mitigation**:
- Feature flags per endpoint (gradual enable)
- Default page size 200 (higher than typical for soft landing)
- Contract tests validate no breaking changes
- Canary rollout with fast rollback capability

### Risk 2: Pagination Round-trip Overhead

**Mitigation**:
- Intelligent default page size (50 items balances scenarios)
- Server-side cursor prefetch for "next page"
- Telemetry identifies excessive pagination for tuning
- Batch operations where feasible (e.g., "get pages 1-3")

### Risk 3: Token Estimation Inaccuracy

**Mitigation**:
- 20% safety margin built into estimation
- Continuous accuracy monitoring (1% sampling)
- Hard byte limits as secondary safety (10KB cap)
- Model retraining based on actual vs estimated deltas

### Risk 4: Configuration Errors

**Mitigation**:
- Schema validation before applying changes
- Fail-safe: invalid config reverts to previous state
- Configuration changes logged and audited
- Dry-run mode for testing before production

## Dependencies

**External**:
- Redis (or in-memory cache) for cursor storage with TTL
- Metrics backend (Prometheus/StatsD/CloudWatch compatible)
- Configuration file watcher (e.g., watchdog library)

**Internal**:
- Existing FastAPI middleware pipeline (for interception)
- Existing Pydantic models (for response typing)
- Existing HostawayConfig (for settings extension)

## Success Metrics (Recap from Spec)

- **SC-001**: 99.9% sessions without context overflow (from ~60%)
- **SC-002**: 60% token reduction (6000 → 2400 avg)
- **SC-003**: 95% pagination adoption within 2 weeks
- **SC-004**: 80% reduction in truncation tickets
- **SC-005**: ≤10% latency increase (p95)
- **SC-006**: 5-minute diagnostics (vs 30+ min)
- **SC-007**: 95% successful pagination navigation
- **SC-008**: 90% estimation accuracy within 20%

## Next Steps

1. ✅ **Phase 0 Complete**: Run research tasks (see research.md)
2. ✅ **Phase 1 Complete**: Define data models and contracts (see data-model.md, contracts/, quickstart.md)
3. ⏭️ **Phase 2 Pending**: Run `/speckit.tasks` to generate actionable task breakdown
4. ⏭️ **Implementation**: Execute tasks with TDD approach per constitution

---

**Status**: Planning Complete | **Ready for**: `/speckit.tasks` command
