# Feature Specification: Automated Overflow-Safety Test Suite

**Feature ID**: 006-overflow-safety-test-suite
**Status**: Draft
**Created**: 2025-10-16
**Last Updated**: 2025-10-16

---

## 1. Overview

### 1.1 Problem Statement

In production environments, the Hostaway MCP server can return oversized payloads or error bodies that bloat Claude's context window and potentially halt conversations:

- **Unbounded Data Returns**: Some endpoints (e.g., `list_properties`, `search_bookings`) can return hundreds of records without pagination
- **Large Error Bodies**: 500 errors may include full HTML stack traces (10-50KB+)
- **Context Window Exhaustion**: Large payloads consume Claude's token budget, preventing further conversation
- **Cost Overruns**: Excessive token usage increases API costs and degrades performance

**Current State**:
- No automated testing for payload size constraints
- Manual verification of pagination behavior
- Production incidents discovered only when context windows are exhausted
- No regression detection for endpoints that start returning unbounded data

**Desired State**:
- Automated, repeatable tests that validate payload size constraints
- Fast CI feedback before deployment
- Comprehensive coverage of all high-volume endpoints
- Regression detection for overflow scenarios

### 1.2 Goals & Objectives

**Primary Goals**:

1. **Safety by Default**: Guarantee all high-volume tools are paginated, chunked, or summarized
2. **Regression Detection**: Detect when endpoints start returning unbounded data
3. **Fast Feedback**: Provide CI validation before production deployment
4. **Production Confidence**: Ensure context window safety across all endpoints

**Success Metrics**:

- ✅ 0 tests exceed hard token cap in steady state
- ✅ ≥95% of eligible endpoints return paginated/summarized results under forced-small caps
- ✅ CI runs complete in <5 minutes
- ✅ Test flake rate <1%
- ✅ 100% coverage of high-volume endpoints

### 1.3 Scope

**In Scope**:

**Endpoint Categories**:
1. **Properties**
   - `list_properties` - Pagination required
   - `get_property_details` - Projection/field limits

2. **Availability**
   - `check_availability` - Bounded time windows

3. **Bookings**
   - `search_bookings` - Paging + filters
   - `get_booking_details` - Projection/chunking
   - `get_guest_info` - Projection

4. **Financial**
   - `get_financial_reports` - Preview/summary + drilldown for large datasets

5. **MCP Resources** (if exposed)
   - `resources/list` - Cursor/nextCursor contract
   - `resources/read` - Size-bounded reads

**Cross-Cutting Behaviors**:
- Token-cap enforcement
- Preview mode activation
- Dynamic chunking
- Failure hygiene (500/429 errors)
- Rate-limit guidance

**Out of Scope**:

- ❌ Rewriting business logic or changing public schemas (beyond additive metadata)
- ❌ UI/agent-level changes
- ❌ Performance optimization (speed focus is on CI runtime, not endpoint performance)
- ❌ Schema validation (covered by existing contract tests)

### 1.4 Target Users

**Primary Users**:

1. **Platform/Agent Engineers**
   - Need: Prevent context overflows and runaway costs
   - Benefit: Automated validation before deployment

2. **SRE/QA Teams**
   - Need: Reproducible checks for pagination/summarization
   - Benefit: Fast regression detection in CI

3. **MCP Server Maintainers**
   - Need: Confidence in endpoint safety
   - Benefit: Clear test coverage metrics

**Secondary Users**:

- Product managers (cost control visibility)
- Security team (failure hygiene validation)

---

## 2. Requirements

### 2.1 Functional Requirements

#### FR1: Pagination Testing

**FR1.1**: `list_properties` Pagination
- **Requirement**: Endpoint MUST respect `limit` parameter
- **Validation**:
  - Request with `limit=10` returns ≤10 properties
  - Returns `nextCursor` when more results available
  - Subsequent calls with `cursor` return disjoint pages
  - Total results across pages match expected count
- **Priority**: P0 (Critical)

**FR1.2**: `search_bookings` Pagination
- **Requirement**: Endpoint MUST implement cursor-based pagination
- **Validation**:
  - Default page size respects `MCP_DEFAULT_PAGE_SIZE`
  - `nextCursor` present when hasMore=true
  - Cursor navigation returns stable, non-overlapping results
- **Priority**: P0 (Critical)

**FR1.3**: MCP Resources List Pagination
- **Requirement**: If resources exposed, MUST use cursor/nextCursor
- **Validation**:
  - `resources/list` returns cursor metadata
  - Cursor-based traversal completes without duplicates
- **Priority**: P1 (High)

#### FR2: Preview & Summarization

**FR2.1**: Financial Reports Preview
- **Requirement**: Large date ranges MUST trigger preview mode
- **Validation**:
  - Projected tokens >threshold returns summary + next steps
  - Summary includes: total records, date range, top insights
  - No raw oversized dump in preview mode
  - Provides cursor for drilldown pagination
- **Priority**: P0 (Critical)

**FR2.2**: Token Threshold Enforcement
- **Requirement**: Responses exceeding soft threshold activate preview
- **Validation**:
  - Configure `MCP_OUTPUT_TOKEN_THRESHOLD=1000`
  - Large responses return preview with `meta.summary`
  - Preview includes actionable next steps
- **Priority**: P0 (Critical)

#### FR3: Field Projection & Chunking

**FR3.1**: Property Details Projection
- **Requirement**: Support field selection to limit payload size
- **Validation**:
  - `fields` parameter filters response
  - Projected response significantly smaller than full payload
  - Large nested sections (reviews, availability) are chunked
- **Priority**: P1 (High)

**FR3.2**: Booking Details Chunking
- **Requirement**: Large booking records are chunked intelligently
- **Validation**:
  - Core booking data always present
  - Nested collections (line items, guests) paginated separately
  - Chunk metadata indicates more data available
- **Priority**: P1 (High)

**FR3.3**: Guest Info Projection
- **Requirement**: Return minimal guest data by default
- **Validation**:
  - Default fields exclude large collections
  - Optional `includeHistory` parameter for full data
- **Priority**: P2 (Medium)

#### FR4: Error Hygiene

**FR4.1**: 500 Error Compactness
- **Requirement**: 500 errors MUST return compact JSON-RPC errors
- **Validation**:
  - No HTML stack traces in response
  - Error payload <2KB
  - Includes correlation ID for debugging
  - Actionable error message for client
- **Priority**: P0 (Critical)

**FR4.2**: 429 Rate Limit Metadata
- **Requirement**: Rate limit errors include retry guidance
- **Validation**:
  - Returns `retryAfter` in seconds
  - Includes `rateLimitRemaining` if available
  - Error message explains limit and retry timing
- **Priority**: P1 (High)

#### FR5: Token Cap Enforcement

**FR5.1**: Hard Cap Validation
- **Requirement**: No response exceeds `MCP_HARD_OUTPUT_TOKEN_CAP`
- **Validation**:
  - All endpoints tested with cap=5000 tokens
  - Responses automatically truncate/preview when approaching cap
  - Truncation metadata indicates original size
- **Priority**: P0 (Critical)

**FR5.2**: Soft Cap Preview
- **Requirement**: Soft threshold triggers preview without truncation
- **Validation**:
  - `MCP_OUTPUT_TOKEN_THRESHOLD` triggers preview mode
  - Preview includes summary + next steps
  - No data loss, just deferred detail retrieval
- **Priority**: P0 (Critical)

### 2.2 Non-Functional Requirements

#### NFR1: Performance
- Test suite completes in <5 minutes in CI
- Individual tests complete in <10 seconds
- Parallel execution supported for test isolation

#### NFR2: Reliability
- Flake rate <1% over 100 runs
- Tests are deterministic and repeatable
- Mock failures don't cascade

#### NFR3: Maintainability
- Clear test names describing scenario
- Reusable fixtures and utilities
- Documented test setup and teardown

#### NFR4: Coverage
- 100% of high-volume endpoints tested
- All pagination paths exercised
- Error scenarios comprehensively covered

#### NFR5: CI Integration
- Runs on every PR
- Blocks merge if tests fail
- Clear failure messages in PR comments

---

## 3. Assumptions & Constraints

### 3.1 Assumptions

1. **MCP Communication**: Server communicates over stdio (existing pattern)
2. **Hostaway API Access**: API is reachable OR can be mocked
3. **Configuration**: Environment variables available for cap tuning:
   - `MCP_OUTPUT_TOKEN_THRESHOLD` (default: 50000)
   - `MCP_HARD_OUTPUT_TOKEN_CAP` (default: 100000)
   - `MCP_DEFAULT_PAGE_SIZE` (default: 50)
4. **Backward Compatibility**: Only additive changes allowed (e.g., `nextCursor`, `meta.summary`)
5. **Test Environment**: Dedicated test database/fixtures available

### 3.2 Constraints

1. **Schema Stability**: Cannot break existing client contracts
2. **Performance**: CI time budget is 5 minutes total
3. **External Dependencies**: Hostaway API rate limits apply to live tests
4. **Token Estimation**: Approximation acceptable (±10% accuracy)
5. **Test Data**: Must not use real customer data

### 3.3 Dependencies

**Internal**:
- Existing MCP server (`src/api/main.py`)
- Token estimator utility (`src/utils/token_estimator.py`)
- Pagination service (`src/services/pagination_service.py`)
- Summarization service (`src/services/summarization_service.py`)

**External**:
- Hostaway API (for live integration tests)
- Vitest/Jest (test framework)
- TypeScript (test language)
- Mock server (http-mock-server or msw)

---

## 4. Acceptance Criteria

### 4.1 Core Acceptance Criteria

**AC1**: Pagination Validation
- ✅ `list_properties` with `limit=10` returns ≤10 results
- ✅ `nextCursor` present when hasMore=true
- ✅ Cursor navigation returns disjoint pages
- ✅ All pages combined match expected total

**AC2**: Preview Mode Activation
- ✅ Financial reports with large date ranges return preview
- ✅ Preview includes summary + cursor for drilldown
- ✅ No oversized raw dumps

**AC3**: Token Cap Enforcement
- ✅ Hard cap never exceeded across all endpoints
- ✅ Soft threshold triggers preview mode
- ✅ Truncation metadata present when needed

**AC4**: Error Hygiene
- ✅ 500 errors return compact JSON (<2KB)
- ✅ 429 errors include `retryAfter` metadata
- ✅ No HTML stack traces in any error response

**AC5**: CI Integration
- ✅ Test suite runs in <5 minutes
- ✅ Flake rate <1%
- ✅ Clear failure reporting in PRs

### 4.2 Test Coverage Requirements

**Coverage Targets**:
- ✅ 100% of high-volume endpoints tested
- ✅ All pagination paths exercised (first page, middle page, last page)
- ✅ Preview mode tested with various thresholds
- ✅ Error scenarios (500, 429, 400) covered
- ✅ Token cap boundaries tested (at threshold, over threshold, at hard cap)

### 4.3 Edge Cases

**EC1**: Empty Results
- Pagination metadata correct for 0 results
- No `nextCursor` when no results

**EC2**: Exactly One Page
- Single page returns all results without cursor
- Subsequent cursor call returns empty

**EC3**: Token Estimation Edge Cases
- Very small responses (<100 tokens)
- Responses near soft threshold (±5%)
- Responses at hard cap boundary

**EC4**: Concurrent Requests
- Multiple paginated requests don't interfere
- Cursors remain stable across parallel calls

---

## 5. User Experience

### 5.1 Developer Experience

**Test Execution**:
```bash
# Run all overflow-safety tests
npm test -- overflow-safety

# Run specific endpoint tests
npm test -- overflow-safety/properties

# Run with custom caps (for debugging)
MCP_OUTPUT_TOKEN_THRESHOLD=1000 npm test -- overflow-safety

# Run live integration tests (slower)
TEST_MODE=live npm test -- overflow-safety/integration
```

**Test Output**:
```
✓ list_properties respects limit parameter (45ms)
✓ list_properties returns nextCursor when hasMore (52ms)
✓ list_properties cursor pagination returns disjoint pages (89ms)
✓ financial_reports activates preview for large date ranges (124ms)
✓ get_property_details respects field projection (38ms)
✗ search_bookings exceeds token threshold (234ms)
  Expected: <50000 tokens
  Actual: 67543 tokens
  Endpoint: search_bookings
  Parameters: {status: 'all', limit: 100}
```

### 5.2 CI/CD Experience

**PR Check Output**:
```markdown
## 🔒 Overflow-Safety Tests

**Status**: ❌ Failed

### Failed Tests (1)
- `search_bookings` exceeded soft token threshold
  - Expected: ≤50,000 tokens
  - Actual: 67,543 tokens
  - Fix: Reduce default page size or enable preview mode

### Coverage
- Endpoints tested: 12/12 (100%)
- Pagination paths: 36/36 (100%)
- Error scenarios: 8/8 (100%)

### Performance
- Duration: 3m 42s
- Flakes: 0
```

### 5.3 Monitoring & Alerts

**Production Metrics** (future enhancement):
- Token usage per endpoint (P95, P99)
- Preview mode activation rate
- Pagination cursor utilization
- Error response sizes

---

## 6. Technical Approach

### 6.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Test Harness (Vitest)                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────┐  ┌──────────────────┐              │
│  │  Test Scenarios│  │  Token Estimator │              │
│  │  - Pagination  │  │  - Count tokens  │              │
│  │  - Preview     │  │  - Validate caps │              │
│  │  - Errors      │  │                  │              │
│  └────────┬───────┘  └────────┬─────────┘              │
│           │                   │                         │
│           ▼                   ▼                         │
│  ┌─────────────────────────────────────┐               │
│  │      MCP Client (stdio)              │               │
│  └──────────────┬──────────────────────┘               │
│                 │                                        │
└─────────────────┼────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              MCP Server (Python)                         │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Pagination   │  │ Preview      │  │ Token        │  │
│  │ Service      │  │ Service      │  │ Estimator    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         ▼                 ▼                 ▼           │
│  ┌─────────────────────────────────────────────┐       │
│  │          Endpoint Handlers                  │       │
│  └───────────────────┬─────────────────────────┘       │
└────────────────────────┼───────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Mock Hostaway API  │
              │   (for unit tests)   │
              └──────────────────────┘
```

### 6.2 Test Categories

**Unit Tests** (fast, mocked):
- Pagination logic
- Token estimation accuracy
- Preview mode activation
- Error formatting

**Integration Tests** (slower, live API):
- End-to-end pagination flows
- Real token counts
- Error scenarios with actual API
- Rate limit handling

**Contract Tests**:
- Schema validation
- Backward compatibility
- Metadata presence (nextCursor, meta.summary)

### 6.3 Key Components

**Test Harness** (`tests/overflow-safety/`):
```typescript
// tests/overflow-safety/harness.ts
export class OverflowTestHarness {
  constructor(
    private mcpClient: MCPClient,
    private tokenEstimator: TokenEstimator,
    private config: TestConfig
  ) {}

  async testPagination(
    endpoint: string,
    params: Record<string, any>
  ): Promise<PaginationTestResult> {
    // Test pagination behavior
  }

  async testPreview(
    endpoint: string,
    largeParams: Record<string, any>
  ): Promise<PreviewTestResult> {
    // Test preview mode activation
  }

  async testTokenCap(
    endpoint: string,
    params: Record<string, any>
  ): Promise<TokenCapTestResult> {
    // Validate token caps
  }
}
```

**Token Estimator** (existing, enhanced):
```python
# src/utils/token_estimator.py
class TokenEstimator:
    def estimate(self, text: str) -> int:
        """Estimate token count (±10% accuracy)"""

    def will_exceed_threshold(
        self,
        response: dict,
        threshold: int
    ) -> bool:
        """Check if response will exceed threshold"""

    def get_truncation_point(
        self,
        response: dict,
        max_tokens: int
    ) -> int:
        """Find safe truncation point"""
```

**Mock Server** (`tests/mocks/hostaway-api.ts`):
```typescript
// Mock Hostaway API for deterministic testing
export const mockHostawayAPI = setupServer(
  rest.get('/v1/listings', (req, res, ctx) => {
    const limit = parseInt(req.url.searchParams.get('limit') || '50')
    const offset = parseInt(req.url.searchParams.get('offset') || '0')

    return res(
      ctx.json({
        result: generateProperties(limit),
        count: 500, // Total available
        limit,
        offset
      })
    )
  })
)
```

---

## 7. Testing Strategy

### 7.1 Test Matrix

| Endpoint | Pagination | Preview | Projection | Error | Token Cap |
|----------|-----------|---------|------------|-------|-----------|
| `list_properties` | ✅ | N/A | ✅ | ✅ | ✅ |
| `get_property_details` | N/A | ✅ | ✅ | ✅ | ✅ |
| `check_availability` | ✅ | N/A | N/A | ✅ | ✅ |
| `search_bookings` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `get_booking_details` | N/A | ✅ | ✅ | ✅ | ✅ |
| `get_guest_info` | N/A | N/A | ✅ | ✅ | ✅ |
| `get_financial_reports` | ✅ | ✅ | ✅ | ✅ | ✅ |

### 7.2 Test Scenarios

**Pagination Scenarios**:
1. First page with limit
2. Middle page navigation
3. Last page (no nextCursor)
4. Empty results
5. Single page results
6. Cursor stability across retries

**Preview Scenarios**:
1. Below threshold (no preview)
2. At threshold boundary
3. Above threshold (preview activated)
4. Preview with drilldown cursor
5. Preview summary accuracy

**Token Cap Scenarios**:
1. Well below soft threshold
2. At soft threshold (±5%)
3. Between soft and hard cap
4. At hard cap boundary
5. Forced truncation

**Error Scenarios**:
1. 500 with correlation ID
2. 429 with retryAfter
3. 400 with validation details
4. Network timeout
5. Invalid cursor

### 7.3 Test Data Strategy

**Fixtures** (`tests/fixtures/`):
```
fixtures/
├── properties/
│   ├── small-set.json (10 properties)
│   ├── medium-set.json (100 properties)
│   └── large-set.json (1000 properties)
├── bookings/
│   ├── minimal.json (1 booking, core fields)
│   ├── detailed.json (1 booking, all fields)
│   └── collection.json (50 bookings)
└── errors/
    ├── 500-html.html (large error body)
    ├── 500-compact.json (desired format)
    └── 429-rate-limit.json
```

**Generators**:
```typescript
// tests/fixtures/generators.ts
export function generateProperties(count: number): Property[] {
  // Generate realistic property data
}

export function generateLargeFinancialReport(): FinancialReport {
  // Generate report that exceeds threshold
}
```

---

## 8. Risks & Mitigations

### 8.1 Technical Risks

**Risk 1**: Flaky External API
- **Impact**: High (unreliable tests)
- **Probability**: Medium
- **Mitigation**:
  - Use HTTP mocks for unit tests
  - Run live integration tests nightly only
  - Implement retry logic with exponential backoff

**Risk 2**: Token Estimation Inaccuracy
- **Impact**: Medium (false positives/negatives)
- **Probability**: Low
- **Mitigation**:
  - Validate estimator against real Claude API
  - Use ±10% tolerance bands
  - Log discrepancies for tuning

**Risk 3**: Test Performance Degradation
- **Impact**: Medium (slow CI)
- **Probability**: Medium
- **Mitigation**:
  - Parallel test execution
  - Mock by default, live tests opt-in
  - Optimize fixture generation

### 8.2 Product Risks

**Risk 4**: Breaking Client Compatibility
- **Impact**: High (production incidents)
- **Probability**: Low
- **Mitigation**:
  - Additive-only changes
  - Contract tests validate schemas
  - Feature flags for gradual rollout

**Risk 5**: Hidden Client Reliance on Unbounded Payloads
- **Impact**: High (broken integrations)
- **Probability**: Low
- **Mitigation**:
  - Audit existing client usage
  - Provide migration guide
  - Support legacy mode temporarily

### 8.3 Operational Risks

**Risk 6**: CI Pipeline Instability
- **Impact**: Medium (blocked PRs)
- **Probability**: Low
- **Mitigation**:
  - Quarantine flaky tests
  - Manual override for known issues
  - Test health dashboard

---

## 9. Implementation Plan

### 9.1 Phases

**Phase 1: Foundation** (Week 1)
- Set up test harness infrastructure
- Create mock Hostaway API
- Implement token estimator utility
- Basic pagination tests for 2 endpoints

**Phase 2: Core Coverage** (Week 2)
- Complete pagination tests for all endpoints
- Implement preview mode tests
- Add error hygiene tests
- CI integration

**Phase 3: Edge Cases** (Week 3)
- Token cap boundary tests
- Concurrent request tests
- Field projection validation
- Performance optimization

**Phase 4: Integration & Documentation** (Week 4)
- Live integration tests
- Test documentation
- Runbook for CI failures
- Metrics dashboard

### 9.2 Deliverables

**Code**:
- [ ] Test harness (`tests/overflow-safety/harness.ts`)
- [ ] Test scenarios (`tests/overflow-safety/scenarios/`)
- [ ] Mock server (`tests/mocks/hostaway-api.ts`)
- [ ] Token estimator enhancements (`src/utils/token_estimator.py`)
- [ ] CI workflow (`.github/workflows/overflow-safety.yml`)

**Documentation**:
- [ ] Test guide (`docs/OVERFLOW_SAFETY_TESTING.md`)
- [ ] Runbook (`docs/OVERFLOW_SAFETY_RUNBOOK.md`)
- [ ] Configuration reference (`docs/TOKEN_CAP_CONFIG.md`)

**Infrastructure**:
- [ ] Test fixtures (`tests/fixtures/`)
- [ ] CI pipeline configuration
- [ ] Metrics collection (optional)

---

## 10. Success Criteria & Validation

### 10.1 Launch Criteria

**Before Merge to Main**:
- ✅ All P0 tests passing
- ✅ CI runtime <5 minutes
- ✅ Flake rate <1% over 100 runs
- ✅ Code review approved
- ✅ Documentation complete

**Before Production**:
- ✅ Live integration tests passing
- ✅ No regressions in existing functionality
- ✅ Metrics dashboard deployed (if included)

### 10.2 Post-Launch Validation

**Week 1**:
- Monitor CI success rate (target: >99%)
- Track test execution time (target: <5 min)
- Collect feedback from engineers

**Month 1**:
- Review production token usage metrics
- Validate preview mode activation rates
- Assess regression detection effectiveness

### 10.3 Rollback Plan

**Triggers**:
- CI success rate <95%
- Test execution time >10 minutes
- False positive rate >5%

**Actions**:
1. Disable failing tests in CI
2. Investigate root cause
3. Fix or remove problematic tests
4. Re-enable after validation

---

## 11. Open Questions

1. **Token Estimator Accuracy**: What's acceptable tolerance for token estimation? (Proposal: ±10%)
2. **Live Test Frequency**: Should live integration tests run on every PR or nightly? (Proposal: Nightly for cost/speed)
3. **Failure Threshold**: Should CI block on soft threshold violations or only hard cap? (Proposal: Block on hard cap, warn on soft)
4. **Mock Data Volume**: How many test fixtures needed per endpoint? (Proposal: 3 sizes - small, medium, large)
5. **Metric Collection**: Should we collect production metrics for token usage? (Proposal: Yes, via existing telemetry)

---

## 12. Appendix

### 12.1 Related Documents

- [Token Budget Management](../003-we-need-to/spec.md)
- [Pagination Service](../../src/services/pagination_service.py)
- [Summarization Service](../../src/services/summarization_service.py)
- [API Contract Tests](../../tests/integration/)

### 12.2 Glossary

- **Hard Cap**: Maximum token limit that cannot be exceeded (triggers truncation)
- **Soft Threshold**: Token limit that triggers preview mode (no truncation)
- **Preview Mode**: Summarized response with cursor for full data retrieval
- **Cursor**: Opaque token for pagination navigation
- **Field Projection**: Filtering response to include only specified fields
- **Chunking**: Breaking large responses into smaller logical pieces

### 12.3 References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Claude Context Window Limits](https://docs.anthropic.com/claude/docs/models-overview)
- [Hostaway API Documentation](https://docs.hostaway.com/)
- [Vitest Documentation](https://vitest.dev/)

---

**Document History**:
- 2025-10-16: Initial draft (v1.0)
