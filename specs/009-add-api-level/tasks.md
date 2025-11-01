# Tasks: API-Level Response Summarization

**Input**: Design documents from `/specs/009-add-api-level/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-specification.yaml
**Status**: ✅ Complete (Implementation Deployed) | **Deployed**: 2025-10-30 | **PR**: #7

**Tests**: Included (TDD approach from constitution requirement)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Note**: This feature was implemented and deployed to production. Core functionality validated with 17/17 unit tests passing. Integration tests deferred for follow-up refactoring (see PR #7 discussion).

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, SETUP, POLISH)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root (used here)
- Paths use absolute references from repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new infrastructure needed - leveraging existing FastAPI/Pydantic stack

- [ ] T001 [SETUP] Verify existing test infrastructure (pytest, pytest-asyncio, pytest-cov) - no changes needed
- [ ] T002 [P] [SETUP] Review existing `src/models/pagination.py` to understand PageMetadata structure
- [ ] T003 [P] [SETUP] Review existing `src/api/routes/listings.py` to understand current endpoint patterns

**Checkpoint**: Setup complete - all existing patterns understood

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create shared models and extend existing pagination infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [FOUNDATION] Create `src/models/summarized.py` with SummarizedListing and SummarizedBooking Pydantic models (see data-model.md for schemas)
- [ ] T005 [FOUNDATION] Extend `src/models/pagination.py` PageMetadata with optional `note: str | None` field
- [ ] T006 [P] [FOUNDATION] Create unit tests for SummarizedListing model in `tests/unit/models/test_summarized_listing.py`
- [ ] T007 [P] [FOUNDATION] Create unit tests for SummarizedBooking model in `tests/unit/models/test_summarized_booking.py`
- [ ] T008 [FOUNDATION] Run unit tests and verify all model validation passes: `pytest tests/unit/models/test_summarized*.py -v`

**Checkpoint**: Foundation ready - shared models validated, user story implementation can now begin

---

## Phase 3: User Story 1 - API Consumer Requests Compact Property List (Priority: P1) 🎯 MVP

**Goal**: Enable API consumers to request compact property listings with `summary=true` parameter, reducing response size by 80-90%

**Independent Test**: Call `GET /api/listings?summary=true&limit=10` and verify response contains only 6 fields per property (id, name, city, country, bedrooms, status), with metadata.note field present

### Tests for User Story 1

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Create integration test file `tests/integration/test_listings_summary.py` with test_get_listings_with_summary_true()
- [ ] T010 [P] [US1] Add test_get_listings_without_summary_parameter() to verify backward compatibility in same file
- [ ] T011 [P] [US1] Add test_get_listings_response_size_reduction() to verify 80-90% size reduction in same file
- [ ] T012 [US1] Run tests and verify they FAIL (implementation not yet done): `pytest tests/integration/test_listings_summary.py -v`

### Implementation for User Story 1

- [ ] T013 [US1] Modify `src/api/routes/listings.py` get_listings() function: Add `summary: bool = Query(False)` parameter
- [ ] T014 [US1] Add conditional response logic in get_listings(): if summary=true, transform items to List[SummarizedListing]
- [ ] T015 [US1] Add PageMetadata note field when summary=true: "Use GET /api/listings/{id} to see full property details"
- [ ] T016 [US1] Update get_listings() response_model to Union type: `PaginatedResponse[dict] | PaginatedResponse[SummarizedListing]`
- [ ] T017 [US1] Add structured logging when summary=true using existing `src/mcp/logging.py` pattern (INFO level with correlation_id)
- [ ] T018 [US1] Run integration tests and verify they PASS: `pytest tests/integration/test_listings_summary.py -v`
- [ ] T019 [US1] Manually test with curl: `curl "http://localhost:8000/api/listings?summary=true&limit=10" -H "X-API-Key: test_key"`

**Checkpoint**: User Story 1 complete - property listing summarization fully functional and independently testable

---

## Phase 4: User Story 2 - API Consumer Requests Compact Booking List (Priority: P1)

**Goal**: Enable API consumers to request compact booking listings with `summary=true` parameter, excluding nested objects

**Independent Test**: Call `GET /api/reservations?summary=true&limit=10` and verify response contains only 7 fields per booking (id, guestName, checkIn, checkOut, listingId, status, totalPrice) with no nested objects

### Tests for User Story 2

- [ ] T020 [P] [US2] Create integration test file `tests/integration/test_bookings_summary.py` with test_get_bookings_with_summary_true()
- [ ] T021 [P] [US2] Add test_get_bookings_without_summary_parameter() to verify backward compatibility in same file
- [ ] T022 [P] [US2] Add test_bookings_nested_objects_excluded() to verify nested objects removed when summary=true
- [ ] T023 [US2] Run tests and verify they FAIL (implementation not yet done): `pytest tests/integration/test_bookings_summary.py -v`

### Implementation for User Story 2

- [ ] T024 [US2] Identify bookings list endpoint in `src/api/routes/bookings.py` (likely search_bookings or similar)
- [ ] T025 [US2] Modify bookings list function: Add `summary: bool = Query(False)` parameter
- [ ] T026 [US2] Add conditional response logic: if summary=true, transform items to List[SummarizedBooking]
- [ ] T027 [US2] Add PageMetadata note field when summary=true: "Use GET /api/reservations/{id} to see full booking details"
- [ ] T028 [US2] Update response_model to Union type: `PaginatedResponse[dict] | PaginatedResponse[SummarizedBooking]`
- [ ] T029 [US2] Add structured logging when summary=true (INFO level with correlation_id)
- [ ] T030 [US2] Run integration tests and verify they PASS: `pytest tests/integration/test_bookings_summary.py -v`
- [ ] T031 [US2] Manually test with curl: `curl "http://localhost:8000/api/reservations?summary=true&limit=10" -H "X-API-Key: test_key"`

**Checkpoint**: User Stories 1 AND 2 complete - both endpoints support summarization independently

---

## Phase 5: User Story 3 - API Consumer Gets Helpful Guidance (Priority: P2)

**Goal**: Ensure summarized responses include clear guidance on accessing full details

**Independent Test**: Verify all summarized responses include metadata.note field with appropriate endpoint guidance

### Tests for User Story 3

- [ ] T032 [P] [US3] Add test_listings_summary_includes_note() to `tests/integration/test_listings_summary.py`
- [ ] T033 [P] [US3] Add test_bookings_summary_includes_note() to `tests/integration/test_bookings_summary.py`
- [ ] T034 [P] [US3] Add test_note_field_absent_when_summary_false() to both test files to verify note only appears with summary=true
- [ ] T035 [US3] Run tests: `pytest tests/integration/test_*_summary.py::test_*_note -v`

### Implementation for User Story 3

**Note**: Guidance implementation was already included in US1 (T015) and US2 (T027) - this phase validates completeness

- [ ] T036 [US3] Verify note field text in listings endpoint matches spec: "Use GET /api/listings/{id} to see full property details"
- [ ] T037 [US3] Verify note field text in bookings endpoint matches spec: "Use GET /api/reservations/{id} to see full booking details"
- [ ] T038 [US3] Verify note field is absent (null) when summary=false or absent
- [ ] T039 [US3] Run all user story 3 tests and verify PASS: `pytest tests/integration/test_*_summary.py::test_*_note -v`

**Checkpoint**: All user stories (US1, US2, US3) are independently functional

---

## Phase 6: Edge Cases & Detail Endpoint Behavior

**Purpose**: Validate edge case handling per clarifications in spec.md

### Tests for Edge Cases

- [ ] T040 [P] [EDGE] Add test_detail_endpoint_ignores_summary_parameter() to `tests/integration/test_listings_summary.py`
- [ ] T041 [P] [EDGE] Add test_invalid_summary_values_treated_as_false() to test truthy value handling
- [ ] T042 [P] [EDGE] Add test_null_fields_included_in_summary() to verify null handling
- [ ] T043 [EDGE] Run edge case tests: `pytest tests/integration/test_listings_summary.py::test_*_endpoint* -v`

### Implementation for Edge Cases

- [ ] T044 [EDGE] Verify `GET /api/listings/{id}?summary=true` silently ignores parameter (returns full details) - no code changes needed
- [ ] T045 [EDGE] Verify FastAPI boolean Query coercion handles truthy values ("true", "1", "yes" → True) - no code changes needed
- [ ] T046 [EDGE] Verify null fields (city, country) are included in SummarizedListing response (not omitted)
- [ ] T047 [EDGE] Run all edge case tests and verify PASS: `pytest tests/integration/test_listings_summary.py::test_*_endpoint* -v`

### Additional Edge Case Coverage (FR-010, FR-011)

- [ ] T047a [P] [EDGE] Create test file `tests/integration/test_cache_key_differentiation.py` to verify FR-010: cache keys differ for `?summary=true` vs `?summary=false` (same URL base, different query params)
- [ ] T047b [P] [EDGE] Create test file `tests/unit/test_logging_summary_usage.py` to verify FR-011: INFO level logs contain endpoint, organization_id, summary parameter when summary=true
- [ ] T047c [EDGE] Run additional edge case tests: `pytest tests/integration/test_cache_key_differentiation.py tests/unit/test_logging_summary_usage.py -v`

**Checkpoint**: Edge cases validated - feature robust

---

## Phase 7: End-to-End Validation

**Purpose**: Verify complete workflows work end-to-end

- [ ] T048 [P] [E2E] Create E2E test file `tests/e2e/test_summary_workflows.py` with test_browse_then_detail_workflow()
- [ ] T049 [E2E] Add test_summary_with_pagination_workflow() to verify cursor-based pagination with summary=true
- [ ] T050 [E2E] Add test_performance_response_time() to verify <1 second for 10 properties with summary=true
- [ ] T051 [E2E] Run E2E tests: `pytest tests/e2e/test_summary_workflows.py -v`

**Checkpoint**: End-to-end workflows validated

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and documentation

- [ ] T052 [P] [POLISH] Run full test suite and verify >80% coverage: `pytest --cov=src --cov-report=term --cov-report=html`
- [ ] T053 [P] [POLISH] Run type checking with mypy: `mypy src/ --strict`
- [ ] T054 [P] [POLISH] Run linting: `ruff check src/ tests/`
- [ ] T055 [P] [POLISH] Run formatting: `ruff format src/ tests/`
- [ ] T056 [POLISH] Verify OpenAPI docs auto-generated correctly: `curl http://localhost:8000/docs` (check summary parameter visible)
- [ ] T057 [P] [POLISH] Update `README.md` with summary parameter usage examples (add to API section)
- [ ] T058 [P] [POLISH] Add CHANGELOG.md entry for v0.2.0: "feat(api): Add optional summary parameter to list endpoints"
- [ ] T059 [POLISH] Run quickstart.md validation scenarios manually per quickstart guide
- [ ] T060 [POLISH] Final integration test run on all endpoints: `pytest tests/integration/ -v`

**Checkpoint**: Feature complete, polished, and ready for deployment

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (Phase 5)**: Depends on US1 and US2 completion (validation phase)
- **Edge Cases (Phase 6)**: Depends on US1 completion (validates US1 behavior)
- **E2E (Phase 7)**: Depends on all user stories being complete
- **Polish (Phase 8)**: Depends on all implementation and testing complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Fully independent
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Fully independent (parallel with US1 possible)
- **User Story 3 (P2)**: Requires US1 and US2 complete (validates guidance in both)

### Within Each User Story

1. Tests written FIRST (TDD)
2. Tests run and FAIL
3. Implementation tasks
4. Tests run and PASS
5. Manual validation
6. Story checkpoint

### Parallel Opportunities

#### Within Foundational Phase
- T006 and T007 (unit tests) can run in parallel
- T002 and T003 (setup reviews) can run in parallel

#### User Stories 1 & 2 Can Run in Parallel
- After Foundational complete, Developer A can do US1 (T009-T019) while Developer B does US2 (T020-T031)

#### Within User Story 1
- T009, T010, T011 (tests) can be written in parallel (different test functions)
- Manual testing (T019) only after implementation

#### Within User Story 2
- T020, T021, T022 (tests) can be written in parallel (different test functions)
- T024 (identify endpoint) must complete before other implementation tasks

#### Within Polish Phase
- T052, T053, T054, T055, T057, T058 can all run in parallel (different tools/files)

---

## Parallel Example: User Story 1

```bash
# Launch all test creation for User Story 1 together:
Task: "Create integration test file tests/integration/test_listings_summary.py with test_get_listings_with_summary_true()"
Task: "Add test_get_listings_without_summary_parameter() to verify backward compatibility in same file"
Task: "Add test_get_listings_response_size_reduction() to verify 80-90% size reduction in same file"

# After tests written, run them to verify FAIL:
pytest tests/integration/test_listings_summary.py -v

# Then implement in sequence:
# T013 → T014 → T015 → T016 → T017 (sequential in same file)

# Then verify tests PASS:
pytest tests/integration/test_listings_summary.py -v
```

---

## Parallel Example: User Stories 1 & 2 Together

```bash
# Developer A works on US1:
# T009-T012 (write tests) → T013-T017 (implement) → T018 (verify)

# Developer B works on US2 (in parallel):
# T020-T023 (write tests) → T024-T029 (implement) → T030 (verify)

# Both stories complete independently, then merge together
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T008) - **CRITICAL BLOCKER**
3. Complete Phase 3: User Story 1 (T009-T019)
4. **STOP and VALIDATE**: Test User Story 1 independently with curl and pytest
5. Deploy/demo if ready (property listing summarization works!)

**Result**: API consumers can request compact property listings with 80-90% size reduction

### Incremental Delivery

1. **Foundation** (Phase 1+2): Setup + Models ready
2. **MVP** (Phase 3): User Story 1 → Property summarization works → Deploy/Demo
3. **Enhancement** (Phase 4): User Story 2 → Booking summarization works → Deploy/Demo
4. **Polish** (Phase 5): User Story 3 → Guidance validated → Deploy/Demo
5. **Hardening** (Phase 6+7): Edge cases + E2E → Production-ready
6. Each increment adds value without breaking previous functionality

### Parallel Team Strategy

With 2 developers after Foundational phase completes:

1. **Team completes Setup + Foundational together** (T001-T008)
2. **Once Foundational done**:
   - Developer A: User Story 1 (T009-T019) - Property summarization
   - Developer B: User Story 2 (T020-T031) - Booking summarization
3. **Both stories merge** → User Story 3 validation (T032-T039)
4. **Team finishes together**: Edge cases → E2E → Polish

---

## Success Metrics

### Test Coverage
- **Target**: >80% overall coverage (constitution requirement)
- **Unit Tests**: 100% coverage for Pydantic models (SummarizedListing, SummarizedBooking)
- **Integration Tests**: >80% coverage for modified route handlers
- **E2E Tests**: Critical workflows (browse → detail, pagination)

### Response Size Validation
- **Target**: 80-90% reduction for summarized responses
- **Measurement**: T011 (test_get_listings_response_size_reduction)
- **Example**: 150KB full → 15KB summarized (90% reduction)

### Response Time Validation
- **Target**: <1 second for 10 properties with summary=true
- **Measurement**: T050 (test_performance_response_time)
- **Baseline**: 500-700ms expected

### Backward Compatibility
- **Target**: 100% compatibility (all existing tests pass)
- **Measurement**: T010, T021 (test without summary parameter)
- **Validation**: Run existing test suite: `pytest tests/integration/ -k "not summary"`

---

## Notes

- **[P]** tasks = different files or independent concerns, no dependencies
- **[Story]** label maps task to specific user story (US1, US2, US3, SETUP, FOUNDATION, EDGE, E2E, POLISH)
- Each user story should be independently completable and testable
- **TDD Workflow**: Write tests → Verify FAIL → Implement → Verify PASS
- Commit after each task or logical group (e.g., all tests for a story)
- Stop at any checkpoint to validate story independently
- **Avoid**: Same file conflicts between parallel tasks, cross-story dependencies
- **Type Safety**: All code must pass `mypy --strict` (enforced in T053)
- **Constitution**: Follows all 5 core principles (validated in plan.md)

---

## Deployment Checklist

After all tasks complete:

- [ ] All tests pass: `pytest --cov=src --cov-fail-under=80`
- [ ] Type checking passes: `mypy src/ --strict`
- [ ] Linting passes: `ruff check src/ tests/`
- [ ] OpenAPI docs updated: `/docs` endpoint shows summary parameter
- [ ] README.md updated with examples
- [ ] CHANGELOG.md entry added
- [ ] Manual validation with curl completed
- [ ] Backward compatibility verified (existing tests pass)
- [ ] Ready for deployment to VPS (72.60.233.157:8080)

---

**Total Tasks**: 63
**Foundational Tasks**: 8 (T001-T008) - BLOCKING
**User Story 1 Tasks**: 11 (T009-T019) - MVP
**User Story 2 Tasks**: 12 (T020-T031)
**User Story 3 Tasks**: 8 (T032-T039)
**Edge Case Tasks**: 11 (T040-T047c) - includes FR-010/FR-011 coverage
**E2E Tasks**: 4 (T048-T051)
**Polish Tasks**: 9 (T052-T060)

**Parallel Opportunities**: 22 tasks marked [P] (includes T047a, T047b)
**Estimated Time**: 4-6 hours (following TDD workflow)
**MVP Scope**: Phases 1-3 (T001-T019) = ~2 hours
