# Tasks: Automated Overflow-Safety Test Suite

**Feature ID**: 006-overflow-safety-test-suite
**Input**: Design documents from `/specs/006-overflow-safety-test-suite/`
**Prerequisites**: plan.md (4-week TypeScript/Vitest implementation), spec.md (functional requirements), research.md (infrastructure analysis)

**Organization**: Tasks grouped by user story to enable independent implementation and testing

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story this task belongs to (US1, US2, etc.)
- All file paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: TypeScript/Vitest test project initialization

- [ ] T001 [P] Create `test/` directory structure and initialize npm project
  - Create `test/package.json` with dependencies (@modelcontextprotocol/sdk, vitest, nock, typescript, tsx)
  - Create `test/tsconfig.json` for Node.js environment
  - Create `test/.gitignore` for node_modules and coverage

- [ ] T002 [P] Configure Vitest test framework in `test/vitest.config.ts`
  - Set globals: true, environment: 'node'
  - Configure timeout: 30000ms per test, hookTimeout: 10000ms
  - Setup files: `test/setup.ts` for global test initialization

- [ ] T003 [P] Create test utilities directory structure
  - Create `test/utils/` for helpers (mcpClient, tokenEstimator, assertions)
  - Create `test/fixtures/` for mock data (hostaway/, generators/)
  - Create `test/performance/` for benchmark tests
  - Create `test/e2e/` for end-to-end workflows
  - Create `test/live/` for optional live integration tests

**Checkpoint**: Test project structure ready - foundation complete

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core test utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement MCP stdio client wrapper in `test/utils/mcpClient.ts`
  - Spawn MCP server process with configurable env vars
  - Create StdioClientTransport for stdin/stdout communication
  - Implement `callTool<T>()` method with token estimation
  - Implement `listTools()`, `listResources()`, `readResource()` methods
  - Implement graceful `stop()` with process cleanup

- [ ] T005 [P] Port token estimator to TypeScript in `test/utils/tokenEstimator.ts`
  - `estimateTokens(text)` - character count / 4 * 1.2 safety margin
  - `estimateTokensFromObject(obj)` - JSON stringify then estimate
  - `estimateTokensFromList(items)` - estimate from array
  - `checkTokenBudget(text, threshold)` - returns estimated, exceeds, ratio
  - `assertWithinTokenBudget()` - Vitest assertion helper
  - `assertBelowHardCap()` - Hard cap violation assertion

- [ ] T006 [P] Create nock HTTP mocking infrastructure in `test/fixtures/hostaway/setup.ts`
  - `setupHostawayMocks()` - Mock authentication (POST /v1/accessTokens)
  - Mock listings endpoint (GET /v1/listings) with query param support
  - Mock pagination responses (limit, offset, count metadata)
  - `setupLargeFinancialReportMock()` - Mock oversized financial data
  - `setupErrorMocks()` - Mock 500 HTML errors and 429 rate limits

- [ ] T007 [P] Create fixture generators in `test/fixtures/generators/`
  - `properties.ts` - `generateProperties(count)` function
  - `bookings.ts` - `generateBookings(count)` function
  - `financial.ts` - `generateLargeFinancialReport()` function
  - `errors.ts` - `generateLargeHtmlError()` function
  - All generators return realistic, deterministic data

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Pagination Contracts (Priority: P0) 🎯 MVP

**Goal**: Guarantee list_properties and search_bookings pagination works correctly under forced-small caps

**Independent Test**: Run pagination tests with `MCP_DEFAULT_PAGE_SIZE=5` and verify:
- Pages are disjoint (no duplicate IDs)
- nextCursor present when hasMore=true
- Final page has no nextCursor

### Tests for User Story 1

**NOTE**: Tests implement validation logic directly

- [ ] T008 [P] [US1] Create pagination contract tests in `test/hostaway.pagination.test.ts`
  - Test: `list_properties respects limit parameter` (limit=10 returns ≤10 items)
  - Test: `list_properties returns nextCursor when more results available`
  - Test: `list_properties pagination returns disjoint pages`
  - Test: `list_properties final page has no nextCursor`
  - Test: `search_bookings respects pagination` (similar to list_properties)
  - All tests must assert token budget with `assertBelowHardCap(content, 3000)`

### Implementation for User Story 1

- [ ] T009 [US1] Verify pagination service integration
  - Read `src/services/pagination_service.py` to understand cursor contract
  - Ensure MCP tools use `PaginationService.build_response()` correctly
  - Validate cursor encoding/decoding works with nock mocks
  - No code changes needed if already integrated (verification only)

**Checkpoint**: At this point, pagination contracts should be fully validated

---

## Phase 4: User Story 2 - Token Cap Enforcement (Priority: P0)

**Goal**: Hard cap never exceeded, soft threshold triggers preview mode

**Independent Test**: Run tests with strict caps (`threshold=1000, hardCap=5000`) and verify:
- No response exceeds hard cap
- Large responses trigger preview with meta.summary.kind='preview'

### Tests for User Story 2

- [ ] T010 [P] [US2] Create token cap tests in `test/hostaway.preview-and-caps.test.ts`
  - Test: `get_financial_reports triggers preview for large date range`
  - Test: `get_property_details respects field projection`
  - Test: `never exceeds hard token cap under any scenario` (multiple tools)
  - Test: `soft threshold triggers preview without data loss`
  - All tests validate preview metadata (summary, nextCursor, meta.summary)

### Implementation for User Story 2

- [ ] T011 [US2] Verify preview mode activation logic
  - Read `src/services/summarization_service.py` for preview implementation
  - Ensure `should_summarize()` checks `MCP_OUTPUT_TOKEN_THRESHOLD`
  - Validate `summarize_object()` returns correct meta.summary structure
  - No code changes needed if already implemented (verification only)

**Checkpoint**: At this point, token caps should be enforced across all endpoints

---

## Phase 5: User Story 3 - Error Hygiene (Priority: P0)

**Goal**: All error responses <2KB, no HTML in errors, correlation IDs present

**Independent Test**: Trigger errors (500, 429) and verify:
- Error payload <500 tokens (~2KB)
- No `<!DOCTYPE` or `<html>` in response
- `correlationId` field present

### Tests for User Story 3

- [ ] T012 [P] [US3] Create error hygiene tests in `test/hostaway.errors-and-rate-limit.test.ts`
  - Test: `500 error returns compact JSON (no HTML)`
  - Test: `429 error includes retry guidance` (retryAfterMs field)
  - Test: `all error responses are compact` (<500 tokens)
  - Test: `error messages are actionable` (contains retry/wait/limit keywords)

### Implementation for User Story 3

- [ ] T013 [US3] Verify error transformation logic
  - Check MCP server error handlers strip HTML from Hostaway API errors
  - Ensure errors include correlation IDs (using `generateCorrelationId()` pattern)
  - Validate 429 errors extract Retry-After header
  - Add error hygiene if missing (transform HTML errors to compact JSON)

**Checkpoint**: At this point, all error responses should be compact and actionable

---

## Phase 6: User Story 4 - Resources & Field Projection (Priority: P1)

**Goal**: MCP resources pagination (if exposed) + field projection reduces payload size

**Independent Test**:
- List resources and verify nextCursor pagination
- Get property details with/without field projection and verify size difference

### Tests for User Story 4

- [ ] T014 [P] [US4] Create resources tests in `test/hostaway.resources.test.ts`
  - Test: `resources/list implements cursor pagination` (disjoint pages)
  - Test: `resources/read respects size bounds` (<3000 tokens)

- [ ] T015 [P] [US4] Create field projection tests in `test/hostaway.field-projection.test.ts`
  - Test: `get_booking_details chunks large nested sections`
  - Test: `get_guest_info returns minimal data by default`
  - Test: `get_guest_info with includeHistory returns paginated history`

### Implementation for User Story 4

- [ ] T016 [US4] Verify field projection implementation
  - Read `src/utils/field_projector.py` for ESSENTIAL_FIELDS mapping
  - Ensure `project_fields()` is called for large objects
  - Validate nested collections (lineItems, bookingHistory) are chunked
  - Add field projection if missing

**Checkpoint**: At this point, field projection should reduce payload sizes significantly

---

## Phase 7: User Story 5 - E2E Workflows & Performance (Priority: Integration)

**Goal**: Multi-tool workflows stay within token budget, performance targets met

**Independent Test**:
- Execute property search → availability check → booking flow
- Verify total tokens across conversation <10,000

### Tests for User Story 5

- [ ] T017 [P] [US5] Create E2E workflow tests in `test/e2e/property-search-flow.test.ts`
  - Test: `user searches properties, checks availability, creates booking`
  - Test: `pagination workflow stays within token budget` (10 pages)
  - Track cumulative token usage across all tool calls

- [ ] T018 [P] [US5] Create performance benchmarks in `test/performance/`
  - `token-estimation.bench.ts` - Token estimation <1ms for typical responses
  - `pagination.bench.ts` - First page <100ms, cursor navigation <150ms
  - 10-page pagination <2 seconds

- [ ] T019 [P] [US5] Create optional live integration tests in `test/live/integration.test.ts`
  - Test: `pagination works with real API` (skipIf !process.env.RUN_LIVE_TESTS)
  - Test: `token estimates are accurate within 20%`
  - Use real HOSTAWAY_ACCOUNT_ID and HOSTAWAY_SECRET_KEY from env

### Implementation for User Story 5

- [ ] T020 [US5] Validate E2E token budget tracking
  - Ensure cumulative token tracking works across multiple tool calls
  - No implementation needed (tests validate existing behavior)

**Checkpoint**: At this point, E2E workflows should demonstrate conversation-level safety

---

## Phase 8: User Story 6 - CI/CD Integration & Documentation (Priority: Delivery)

**Goal**: Tests run in CI on every PR, clear failure reporting, comprehensive documentation

**Independent Test**:
- Push PR with intentional overflow
- Verify CI fails with clear message
- Fix overflow and verify CI passes

### CI/CD Implementation for User Story 6

- [ ] T021 [P] [US6] Create PR gate workflow in `.github/workflows/overflow-safety-pr.yml`
  - Run on pull_request to main/develop branches
  - Setup Node.js 20 + Python 3.12
  - Install test dependencies (npm ci in test/)
  - Run tests with strict caps (threshold=1000, hardCap=5000)
  - Upload test results as artifacts
  - Comment PR with results if failure
  - Check for flakes with --rerun-failures=3

- [ ] T022 [P] [US6] Create nightly live tests workflow in `.github/workflows/overflow-safety-nightly.yml`
  - Schedule: cron '0 2 * * *' (2 AM daily)
  - Run live integration tests with RUN_LIVE_TESTS=true
  - Use HOSTAWAY_SANDBOX credentials from secrets
  - Publish metrics as artifacts

### Documentation for User Story 6

- [ ] T023 [P] [US6] Create test README in `test/README.md`
  - Quick start guide (prerequisites, installation, running tests)
  - Test categories (pagination, preview, errors, E2E)
  - Configuration (environment variables table)
  - Adding new tests (step-by-step guide)
  - Troubleshooting (MCP server issues, timeouts, flakes)
  - CI integration (PR gate, nightly workflow)

- [ ] T024 [P] [US6] Create failure runbook in `test/RUNBOOK.md`
  - Quick diagnosis (identify failure type from logs)
  - Failure modes & fixes:
    - Hard cap violation (add pagination/preview)
    - Preview not activating (adjust threshold, fix estimation)
    - Pagination broken (verify cursor logic)
    - Error response too large (strip HTML)
  - Performance issues (parallel execution, optimize slow tests)
  - Flaky tests (add retries, fix timing, clean mocks)
  - Escalation (collect diagnostics, create GitHub issue)

### Final Validation for User Story 6

- [ ] T025 [US6] Run full regression testing
  - Execute all tests with default caps (threshold=50000, hardCap=100000)
  - Execute all tests with strict caps (threshold=1000, hardCap=5000)
  - Execute performance benchmarks
  - Verify flake rate <1% (run suite 10 times)

- [ ] T026 [US6] Validate CI pipeline end-to-end
  - Create test PR with intentional overflow
  - Verify CI fails with clear message
  - Fix overflow and verify CI passes
  - Verify test results uploaded as artifacts

**Checkpoint**: At this point, overflow-safety tests should be production-ready

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational completion
  - US1-US4 can proceed in parallel (if staffed)
  - US5 (E2E) should wait for US1-US4 completion for realistic tests
  - US6 (CI/CD) can start anytime after Foundational
- **Polish**: Not needed (tests are complete after US6)

### User Story Dependencies

- **US1 (Pagination)**: Can start after Foundational - No dependencies
- **US2 (Token Caps)**: Can start after Foundational - No dependencies
- **US3 (Error Hygiene)**: Can start after Foundational - No dependencies
- **US4 (Field Projection)**: Can start after Foundational - No dependencies
- **US5 (E2E)**: Should wait for US1-US4 for realistic scenarios (but can start after Foundational)
- **US6 (CI/CD)**: Can start after Foundational - No dependencies

### Within Each User Story

- Tests first (validate existing behavior or guide implementation)
- Implementation/verification second
- Story complete and independently testable before moving to next

### Parallel Opportunities

**Setup Phase**: All T001-T003 can run in parallel (different files)

**Foundational Phase**: All T004-T007 can run in parallel (different files)

**User Stories Phase**: ALL user stories can start in parallel once Foundational is complete:
- Developer A: US1 (T008-T009) - Pagination contracts
- Developer B: US2 (T010-T011) - Token caps
- Developer C: US3 (T012-T013) - Error hygiene
- Developer D: US4 (T014-T016) - Field projection
- Developer E: US5 (T017-T020) - E2E & performance
- Developer F: US6 (T021-T026) - CI/CD & docs

**Within User Stories**:
- US1: T008 (tests) can run alone, T009 (verification) sequential
- US2: T010 (tests) can run alone, T011 (verification) sequential
- US3: T012 (tests) can run alone, T013 (verification) sequential
- US4: T014 + T015 (tests) can run in parallel, T016 (verification) sequential
- US5: T017 + T018 + T019 (all tests) can run in parallel, T020 (verification) sequential
- US6: T021 + T022 (workflows) can run in parallel, T023 + T024 (docs) can run in parallel, T025-T026 (validation) sequential

---

## Parallel Example: Foundational Phase (Maximum Parallelization)

```bash
# Launch all foundational tasks simultaneously (4 developers):
Developer A: T004 - "Implement MCP stdio client wrapper in test/utils/mcpClient.ts"
Developer B: T005 - "Port token estimator to TypeScript in test/utils/tokenEstimator.ts"
Developer C: T006 - "Create nock HTTP mocking infrastructure in test/fixtures/hostaway/setup.ts"
Developer D: T007 - "Create fixture generators in test/fixtures/generators/"

# All tasks write to different files, no conflicts
```

## Parallel Example: User Stories Phase (6 developers)

```bash
# After Foundational complete, launch all user stories in parallel:
Developer A: US1 - Pagination contracts (T008-T009)
Developer B: US2 - Token caps (T010-T011)
Developer C: US3 - Error hygiene (T012-T013)
Developer D: US4 - Field projection (T014-T016)
Developer E: US5 - E2E workflows (T017-T020)
Developer F: US6 - CI/CD (T021-T026)

# Each story independently testable
# No cross-story dependencies
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003) - ~1 day
2. Complete Phase 2: Foundational (T004-T007) - ~2-3 days
3. Complete Phase 3: US1 Pagination (T008-T009) - ~1 day
4. **STOP and VALIDATE**: Run pagination tests with strict caps
5. If passing: MVP complete! (Pagination safety guaranteed)

**Total MVP Time**: ~5 days (1 developer)

### Incremental Delivery

1. **Week 1**: Setup + Foundational → Foundation ready
2. **Week 2**: US1 (Pagination) → Test → Deploy (MVP!)
3. **Week 2**: US2 (Token Caps) → Test → Deploy
4. **Week 2**: US3 (Error Hygiene) → Test → Deploy
5. **Week 3**: US4 (Field Projection) → Test → Deploy
6. **Week 3**: US5 (E2E Workflows) → Test → Validate
7. **Week 4**: US6 (CI/CD) → Test → Production-ready

Each story adds safety without breaking previous validation.

### Parallel Team Strategy

With 6 developers (optimal):

1. **Day 1-2**: Team completes Setup + Foundational together
2. **Day 3-10**: Once Foundational is done:
   - Developer A: US1 (Pagination)
   - Developer B: US2 (Token Caps)
   - Developer C: US3 (Error Hygiene)
   - Developer D: US4 (Field Projection)
   - Developer E: US5 (E2E Workflows)
   - Developer F: US6 (CI/CD)
3. **Day 11-20**: Stories complete independently, integrate, and validate

**Total Time (6 developers)**: ~2-3 weeks (vs 4 weeks for 1 developer)

---

## Success Metrics

### Coverage Targets (from spec.md)

- ✅ 100% of high-volume endpoints tested (list_properties, search_bookings, get_financial_reports)
- ✅ All pagination paths exercised (first page, middle page, last page, empty results)
- ✅ All error scenarios covered (500, 429, 400)
- ✅ Token cap boundaries tested (at threshold, over threshold, at hard cap)

### Performance Targets (from spec.md)

- ✅ Test suite <5 minutes in CI
- ✅ Individual tests <10 seconds
- ✅ Flake rate <1% (verified over 10 runs)
- ✅ Token estimation <1ms per operation
- ✅ Pagination overhead <150ms per page

### Quality Targets (from spec.md)

- ✅ 0 hard cap violations across all endpoints
- ✅ ≥95% of endpoints return paginated/summarized results under forced-small caps
- ✅ All error responses <2KB (~500 tokens)
- ✅ All tests deterministic and repeatable

---

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability
- **Tests are validation**: No separate test implementation tasks (tests ARE the implementation)
- **Verification only**: Most tasks verify existing infrastructure works correctly (minimal code changes)
- **Commit frequency**: After each task or logical group
- **Checkpoint validation**: Stop after each user story to validate independently
- **Avoid**: Cross-story dependencies, same-file conflicts, vague tasks

---

**Task Generation Complete**: 2025-10-16
**Total Tasks**: 26 tasks across 8 phases
**Estimated Duration**: 4 weeks (1 developer) or 2-3 weeks (6 developers in parallel)
**MVP Tasks**: 10 tasks (Setup + Foundational + US1)
**MVP Duration**: ~5 days (1 developer)
