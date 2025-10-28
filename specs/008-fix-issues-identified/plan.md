# Implementation Plan: MCP Server Issues Resolution

**Branch**: `008-fix-issues-identified` | **Date**: 2025-10-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-fix-issues-identified/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This plan addresses three issues identified in the MCP server test report (MCP_SERVER_TEST_REPORT.md):

1. **404 vs 401 Priority**: Fix middleware execution order so non-existent routes return HTTP 404 instead of 401
2. **Rate Limit Headers**: Add industry-standard rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`) to all responses
3. **Test API Key Generation**: Create documented scripts for generating test API keys for local development

**Technical Approach**:
- Adjust FastAPI middleware order to check route existence before authentication
- Enhance rate limiting middleware to expose headers in responses
- Create Python script for API key generation with database insertion
- Add comprehensive tests for all three issues

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: FastAPI 0.100+, fastapi-mcp 0.4+, httpx 0.27+, Pydantic 2.0+, pydantic-settings
**Storage**: Supabase (PostgreSQL) for API key storage, in-memory for rate limit state
**Testing**: pytest, pytest-asyncio, httpx_mock for HTTP mocking
**Target Platform**: Linux server (Docker containers), production VPS deployment
**Project Type**: Single project (FastAPI web server with MCP integration)
**Performance Goals**: Maintain <500ms response times, support 100+ concurrent requests
**Constraints**: Zero performance degradation from middleware changes, backward compatible (no breaking changes)
**Scale/Scope**: Production MCP server with 13 API endpoints, 3 middleware modifications, 1 new script

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. API-First Design ✅ PASS

**Requirement**: Every feature MUST be exposed as a FastAPI endpoint before becoming an MCP tool.

**Assessment**:
- This feature does NOT add new MCP tools - it fixes existing infrastructure
- Changes affect middleware behavior and developer tooling
- No new endpoints or MCP tools are being created
- Existing endpoints remain API-first with proper OpenAPI documentation

**Verdict**: N/A - Infrastructure improvements, not new API features

### II. Type Safety (NON-NEGOTIABLE) ✅ PASS

**Requirement**: All code MUST pass `mypy --strict` without errors.

**Assessment**:
- Middleware modifications will maintain existing type annotations
- Rate limit middleware already has type hints (needs header additions only)
- API key generation script will include full type annotations
- All new code will be validated with `mypy --strict` in CI/CD

**Verdict**: PASS - Will maintain 100% type safety compliance

### III. Security by Default ✅ PASS

**Requirement**: Security is first-class, endpoints MUST require authentication, inputs validated.

**Assessment**:
- **404 vs 401 fix**: Improves security UX without weakening authentication
  - Route existence check happens BEFORE authentication
  - Authentication still required for all protected routes
  - Public routes (/, /health, /docs) remain public
  - No authentication bypass introduced
- **Rate limit headers**: Transparency improves security awareness
  - Headers expose rate limiting, not weaken it
  - No sensitive information leaked in headers
- **API key generation**: Maintains security standards
  - Uses SHA-256 hashing (existing standard)
  - Proper entropy (32+ characters)
  - Follows existing key format `mcp_{base64_token}`

**Verdict**: PASS - Security maintained, UX improved

### IV. Test-Driven Development ✅ PASS

**Requirement**: All code MUST achieve >80% coverage with unit, integration, and E2E tests.

**Assessment**:
- **404 vs 401**: Integration tests for route handling
  - Test non-existent routes return 404 (not 401)
  - Test existing routes still require auth (401 when missing)
  - Test 405 Method Not Allowed still works
- **Rate limit headers**: Unit and integration tests
  - Test headers present in all responses
  - Test header values decrement correctly
  - Test 429 responses include accurate headers
- **API key generation**: Unit tests for script
  - Test key format validation
  - Test SHA-256 hashing
  - Test database insertion (mocked)

**Verdict**: PASS - Comprehensive test plan covers all changes

### V. Async Performance ✅ PASS

**Requirement**: All I/O MUST be async, maintain <500ms response times.

**Assessment**:
- **Middleware changes**: No blocking operations introduced
  - Route existence check is synchronous (fast, no I/O)
  - Rate limit header addition is synchronous (in-memory state)
  - No new database queries or external API calls
- **Performance impact**: Negligible
  - Route check: O(1) lookup in FastAPI's route registry
  - Header addition: O(1) string formatting
  - Expected overhead: <1ms per request
- **Current performance**: 326ms average (test report)
- **Target maintained**: <500ms (95th percentile)

**Verdict**: PASS - Zero performance degradation expected

### Overall Constitution Compliance: ✅ ALL GATES PASSED

No violations. Feature is fully aligned with constitution principles.

## Project Structure

### Documentation (this feature)

```
specs/008-fix-issues-identified/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (in progress)
├── research.md          # Phase 0 output (to be generated)
├── quickstart.md        # Phase 1 output (to be generated)
├── contracts/           # Phase 1 output (N/A - no new API contracts)
├── checklists/
│   └── requirements.md  # Spec quality validation (completed)
└── tasks.md             # Phase 2 output (/speckit.tasks - not yet created)
```

### Source Code (repository root)

**Single Project Structure** - FastAPI MCP Server

```
src/
├── api/
│   ├── main.py                          # FastAPI app - MODIFY (middleware order)
│   ├── middleware/
│   │   ├── mcp_auth_middleware.py       # MODIFY (route existence check)
│   │   └── rate_limiter.py              # MODIFY (add headers)
│   └── routes/
│       ├── auth.py                      # No changes
│       ├── listings.py                  # No changes
│       ├── bookings.py                  # No changes
│       └── financial.py                 # No changes
├── mcp/
│   ├── server.py                        # No changes
│   ├── config.py                        # No changes
│   └── security.py                      # No changes
└── scripts/
    └── generate_api_key.py              # NEW - API key generation script

tests/
├── unit/
│   ├── test_api_key_generation.py       # NEW - Test key script
│   └── test_rate_limiter_headers.py     # NEW - Test header logic
├── integration/
│   ├── test_404_vs_401_priority.py      # NEW - Test route handling
│   └── test_rate_limit_headers_e2e.py   # NEW - Test headers in responses
└── performance/
    └── test_middleware_performance.py   # NEW - Ensure no degradation

docs/
└── API_KEY_GENERATION.md                # NEW - Documentation for key script
```

**Structure Decision**: Single project (existing FastAPI server). Changes are concentrated in:
1. **Middleware layer** (`src/api/middleware/`) - Order adjustment and header additions
2. **Scripts directory** (`src/scripts/`) - New API key generation utility
3. **Tests** - New test files across unit, integration, and performance categories
4. **Documentation** - New guide for API key generation

**Files Modified**: 3 existing files
**Files Created**: 7 new files (1 script, 5 tests, 1 doc)

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**No violations** - Constitution check passed all gates. No complexity justification needed.
