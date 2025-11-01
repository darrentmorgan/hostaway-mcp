# Tasks: MCP Server Issues Resolution

**Input**: Design documents from `/specs/008-fix-issues-identified/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: Test tasks are included as this is a bug fix feature requiring comprehensive testing per TDD principle IV in constitution.

**Organization**: Tasks are grouped by user story (issue) to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (issue) this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root (existing FastAPI MCP server)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure development environment is ready for implementing fixes

- [ ] T001 Verify Python 3.12+ environment and dependencies (FastAPI 0.100+, fastapi-mcp 0.4+, Pydantic 2.0+)
- [ ] T002 [P] Install Click CLI framework for API key generation script: `uv add click>=8.1.0`
- [ ] T003 [P] Verify Supabase client available for API key script: `supabase-py` already in project
- [ ] T004 [P] Create test fixtures for middleware testing in `tests/conftest.py`
- [ ] T005 Review current middleware execution order in `src/api/main.py` to understand baseline

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core test infrastructure that MUST be complete before ANY issue fix can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create base integration test setup in `tests/integration/conftest.py` with TestClient and mocked authentication
- [ ] T007 [P] Create performance testing utilities in `tests/performance/conftest.py` for measuring middleware overhead
- [ ] T008 [P] Create unit test helpers for rate limit state management in `tests/unit/conftest.py`

**Checkpoint**: Foundation ready - issue fixes can now begin in parallel

---

## Phase 3: User Story 1 - Distinguish Between Authentication Failures and Missing Routes (Priority: P1) 🎯 MVP

**Goal**: Return HTTP 404 for non-existent routes instead of 401, improving API consumer developer experience

**Independent Test**: Make requests to non-existent routes (e.g., `/api/nonexistent`) both with and without authentication headers, verify 404 is returned before authentication is checked

### Tests for User Story 1 (TDD - Write First)

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Integration test for 404 on non-existent routes without auth in `tests/integration/test_404_vs_401_priority.py` - Test `test_nonexistent_route_returns_404()`
- [ ] T010 [P] [US1] Integration test for 404 on non-existent routes with valid auth in `tests/integration/test_404_vs_401_priority.py` - Test `test_nonexistent_route_with_auth_returns_404()`
- [ ] T011 [P] [US1] Integration test that existing routes still return 401 without auth in `tests/integration/test_404_vs_401_priority.py` - Test `test_existing_route_requires_auth()`
- [ ] T012 [P] [US1] Integration test for 405 Method Not Allowed handling in `tests/integration/test_404_vs_401_priority.py` - Test `test_405_method_not_allowed_still_works()`

### Implementation for User Story 1

- [ ] T013 [US1] Add custom 404 exception handler in `src/api/main.py` using `@app.exception_handler(404)` decorator
- [ ] T014 [US1] Implement 404 handler logic to return JSON response with route path and correlation ID in `src/api/main.py`
- [ ] T015 [US1] Ensure 404 handler preserves CORS headers in `src/api/main.py`
- [ ] T016 [US1] Verify all integration tests now PASS after implementation

**Checkpoint**: At this point, User Story 1 should be fully functional - non-existent routes return 404, existing routes still require authentication (401)

---

## Phase 4: User Story 2 - Monitor Rate Limit Status (Priority: P2)

**Goal**: Add industry-standard rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`) to all responses

**Independent Test**: Make authenticated API requests and inspect response headers for accurate rate limit information

### Tests for User Story 2 (TDD - Write First)

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T017 [P] [US2] Unit test for rate limit info calculation in `tests/unit/test_rate_limiter_headers.py` - Test `test_rate_limit_info_calculation()`
- [ ] T018 [P] [US2] Unit test for header format validation in `tests/unit/test_rate_limiter_headers.py` - Test `test_rate_limit_headers_format()`
- [ ] T019 [P] [US2] Integration test for headers present in all responses in `tests/integration/test_rate_limit_headers_e2e.py` - Test `test_rate_limit_headers_present()`
- [ ] T020 [P] [US2] Integration test for remaining count decrement in `tests/integration/test_rate_limit_headers_e2e.py` - Test `test_rate_limit_headers_decrement()`
- [ ] T021 [P] [US2] Integration test for 429 responses with headers in `tests/integration/test_rate_limit_headers_e2e.py` - Test `test_429_includes_rate_limit_headers()`
- [ ] T022 [P] [US2] Performance test ensuring headers don't degrade response times in `tests/performance/test_middleware_performance.py` - Test `test_middleware_performance_no_regression()`

### Implementation for User Story 2

- [ ] T023 [US2] Add `_get_rate_limit_info()` method to `RateLimiterMiddleware` class in `src/api/middleware/rate_limiter.py` to calculate limit, remaining, and reset time
- [ ] T024 [US2] Store rate limit info in `request.state.rate_limit_info` before calling `call_next()` in `src/api/middleware/rate_limiter.py`
- [ ] T025 [US2] Add header logic after response generation in `dispatch()` method in `src/api/middleware/rate_limiter.py` - attach `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- [ ] T026 [US2] Update 429 rate limit exceeded response to include headers in `src/api/middleware/rate_limiter.py`
- [ ] T027 [US2] Add optional `Retry-After` header to 429 responses in `src/api/middleware/rate_limiter.py`
- [ ] T028 [US2] Verify all unit and integration tests now PASS after implementation

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - proper 404s and transparent rate limiting

---

## Phase 5: User Story 3 - Generate Test API Keys Easily (Priority: P3)

**Goal**: Provide documented CLI script for generating test API keys for local development without production database access

**Independent Test**: Follow documentation to generate a test API key, then use that key to make authenticated requests that succeed

### Tests for User Story 3 (TDD - Write First)

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T029 [P] [US3] Unit test for API key format validation in `tests/unit/test_api_key_generation.py` - Test `test_api_key_format()`
- [ ] T030 [P] [US3] Unit test for SHA-256 hash computation in `tests/unit/test_api_key_generation.py` - Test `test_sha256_hash_computation()`
- [ ] T031 [P] [US3] Unit test for Click CLI invocation in `tests/unit/test_api_key_generation.py` - Test `test_generate_key_cli()`
- [ ] T032 [P] [US3] Unit test for Supabase insertion logic (mocked) in `tests/unit/test_api_key_generation.py` - Test `test_database_insertion_mocked()`

### Implementation for User Story 3

- [ ] T033 [P] [US3] Create `src/scripts/` directory if it doesn't exist
- [ ] T034 [US3] Create `src/scripts/generate_api_key.py` with Click CLI framework, `@click.command()` decorator, and options for `--org-id`, `--user-id`, `--supabase-url`, `--supabase-key`
- [ ] T035 [US3] Implement `generate_key()` function in `src/scripts/generate_api_key.py` - Step 1: Generate token using `secrets.token_urlsafe(32)` and format as `mcp_{token}`
- [ ] T036 [US3] Implement SHA-256 hash computation in `src/scripts/generate_api_key.py` - Step 2: `hashlib.sha256(api_key.encode()).hexdigest()`
- [ ] T037 [US3] Implement organization validation in `src/scripts/generate_api_key.py` - Step 3: Query Supabase to verify org exists
- [ ] T038 [US3] Implement API key insertion in `src/scripts/generate_api_key.py` - Step 4: Insert into `api_keys` table with organization_id, key_hash, created_by_user_id, is_active=true
- [ ] T039 [US3] Add user-friendly CLI output with success message, key display, and usage instructions in `src/scripts/generate_api_key.py`
- [ ] T040 [US3] Add error handling for database connection failures, missing organization, and permission errors in `src/scripts/generate_api_key.py`
- [ ] T041 [US3] Create `docs/API_KEY_GENERATION.md` documentation with prerequisites, step-by-step setup, troubleshooting, and examples for both local and remote VPS
- [ ] T042 [US3] Verify all unit tests now PASS after implementation

**Checkpoint**: All user stories should now be independently functional - proper 404s, rate limit headers, and easy API key generation

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and overall code quality

- [ ] T043 [P] Update main README.md with links to new documentation and mention of three fixes
- [ ] T044 [P] Update CHANGELOG.md with entries for all three issues fixed
- [ ] T045 [P] Run `ruff format src/ tests/` to ensure code formatting compliance
- [ ] T046 [P] Run `ruff check src/ tests/ --fix` to fix any linting issues
- [ ] T047 [P] Run `mypy --strict src/` to ensure type checking passes
- [ ] T048 [P] Run full test suite `pytest --cov=src --cov-report=term` and verify >80% coverage maintained
- [ ] T049 [P] Run performance regression tests `pytest tests/performance/ -v` and verify <500ms response times maintained
- [ ] T050 [P] Update quickstart.md with any implementation notes or gotchas discovered during development
- [ ] T051 Commit changes with semantic commit messages: `fix(middleware): return 404 for non-existent routes`, `feat(middleware): add rate limit headers`, `feat(scripts): add API key generation CLI`
- [ ] T052 Run pre-commit hooks to validate all code quality checks
- [ ] T053 Push to branch `008-fix-issues-identified` and create pull request

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3, 4, 5)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed) or sequentially in priority order
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1) - 404 Fix**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2) - Rate Limit Headers**: Can start after Foundational (Phase 2) - Independent of US1 (different file)
- **User Story 3 (P3) - API Key Script**: Can start after Foundational (Phase 2) - Independent of US1/US2 (new script file)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Implementation follows quickstart.md patterns
- Verify all tests PASS before moving to next story
- Each story independently testable at checkpoint

### Parallel Opportunities

#### Phase 1: Setup (All tasks can run in parallel)
- T002, T003, T004 can all run simultaneously (different concerns)

#### Phase 2: Foundational (All tasks can run in parallel)
- T007, T008 can run simultaneously (different test categories)

#### User Story 1 Tests (All can run in parallel - different test functions)
- T009, T010, T011, T012 can all be written simultaneously

#### User Story 2 Tests (All can run in parallel - different test files/functions)
- T017, T018, T019, T020, T021, T022 can all be written simultaneously

#### User Story 3 Tests (All can run in parallel - different test functions)
- T029, T030, T031, T032 can all be written simultaneously

#### User Stories (All three can be worked on in parallel by different developers)
- Once Phase 2 complete, US1, US2, US3 can all proceed in parallel

#### Phase 6: Polish (Most tasks can run in parallel)
- T043, T044, T045, T046, T047, T048, T049, T050 can all run simultaneously

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Integration test for 404 on non-existent routes without auth"
Task: "Integration test for 404 on non-existent routes with valid auth"
Task: "Integration test that existing routes still return 401 without auth"
Task: "Integration test for 405 Method Not Allowed handling"

# After tests written, implement (sequential in same file):
Task: "Add custom 404 exception handler in src/api/main.py"
Task: "Implement 404 handler logic with route path and correlation ID"
Task: "Ensure 404 handler preserves CORS headers"
```

## Parallel Example: All User Stories (Multi-Developer Team)

```bash
# Once Phase 2 complete, launch all three user stories in parallel:

# Developer A works on User Story 1 (P1):
Tasks T009-T016: 404 vs 401 fix

# Developer B works on User Story 2 (P2):
Tasks T017-T028: Rate limit headers

# Developer C works on User Story 3 (P3):
Tasks T029-T042: API key generation script

# All three stories complete independently and can be tested/deployed separately
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup → Development environment ready
2. Complete Phase 2: Foundational → Test infrastructure ready (CRITICAL)
3. Complete Phase 3: User Story 1 → 404 fix working
4. **STOP and VALIDATE**: Test User Story 1 independently using quickstart.md
5. Deploy/demo if ready - this alone provides significant value

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP: Proper 404 responses!)
3. Add User Story 2 → Test independently → Deploy/Demo (Rate limit transparency!)
4. Add User Story 3 → Test independently → Deploy/Demo (Easy key generation!)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy (Recommended)

With three developers:

1. **All devs**: Complete Phase 1 (Setup) together - 30 minutes
2. **All devs**: Complete Phase 2 (Foundational) together - 1 hour
3. **Once Foundational done**:
   - Developer A: User Story 1 (T009-T016) - 2 hours
   - Developer B: User Story 2 (T017-T028) - 3 hours
   - Developer C: User Story 3 (T029-T042) - 3 hours
4. **All devs**: Phase 6 (Polish) together - 1 hour
5. **Total time**: ~5 hours vs ~10 hours sequential

### Sequential Strategy (Single Developer)

1. Phase 1: Setup - 30 minutes
2. Phase 2: Foundational - 1 hour
3. Phase 3: User Story 1 - 2 hours
4. Phase 4: User Story 2 - 3 hours
5. Phase 5: User Story 3 - 3 hours
6. Phase 6: Polish - 1 hour
7. **Total time**: ~10.5 hours

---

## Task Metrics

**Total Tasks**: 53
- Setup: 5 tasks
- Foundational: 3 tasks
- User Story 1 (P1): 8 tasks (4 tests + 4 implementation)
- User Story 2 (P2): 12 tasks (6 tests + 6 implementation)
- User Story 3 (P3): 14 tasks (4 tests + 10 implementation)
- Polish: 11 tasks

**Parallelizable Tasks**: 35 marked with [P]
- Parallel efficiency: 66% of tasks can run concurrently
- Single developer: ~10.5 hours
- Three developers (parallel): ~5 hours (52% time savings)

**Test Tasks**: 14 (26% of total) - Comprehensive TDD coverage

**Independent Test Criteria**:
- US1: Non-existent routes return 404, existing routes require auth
- US2: All responses include accurate rate limit headers
- US3: Generated API keys work for authenticated requests

**Suggested MVP**: User Story 1 only (8 tasks after foundation) - Delivers most critical developer experience fix in ~2 hours

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable (follows spec requirement)
- Tests are written FIRST (TDD) per constitution principle IV
- Verify tests FAIL before implementing, PASS after implementation
- Commit after each user story checkpoint for incremental delivery
- Stop at any checkpoint to validate story independently
- Follow quickstart.md for detailed implementation patterns
- All file paths are exact, ready for LLM execution
- Middleware changes tested for zero performance regression (<500ms maintained)
