<!--
Sync Impact Report
==================
Version Change: Initial → 1.0.0
Creation Date: 2025-10-12

Principles Defined:
- I. API-First Design (new)
- II. Type Safety (NON-NEGOTIABLE) (new)
- III. Security by Default (new)
- IV. Test-Driven Development (new)
- V. Async Performance (new)

Sections Added:
- Technology Standards (new)
- Development Workflow (new)
- Governance (new)

Templates Status:
✅ plan-template.md - Aligned with constitution principles
✅ spec-template.md - Aligned with requirements and scope
✅ tasks-template.md - Aligned with task categorization
✅ checklist-template.md - Aligned with quality gates
✅ agent-file-template.md - No changes needed

Follow-up Actions:
- None - all templates compatible with constitution v1.0.0
-->

# Hostaway MCP Server Constitution

## Core Principles

### I. API-First Design

Every feature MUST be exposed as a FastAPI endpoint before becoming an MCP tool. FastAPI-MCP automatically converts endpoints to MCP tools through OpenAPI schema introspection.

**Requirements:**
- All endpoints MUST have explicit `operation_id` (no auto-generated IDs)
- All endpoints MUST use Pydantic models for request/response
- All endpoints MUST have comprehensive docstrings (used as tool descriptions)
- All endpoints MUST specify `response_model` for output schema generation
- All endpoints MUST use FastAPI tags for logical grouping

**Rationale:** API-first ensures that MCP tools are well-structured, documented, and maintainable. OpenAPI serves as the single source of truth for both REST API and MCP tool definitions.

### II. Type Safety (NON-NEGOTIABLE)

Type safety is mandatory at every layer: models, endpoints, services, and configurations. All code MUST pass static type checking before merge.

**Requirements:**
- All functions and methods MUST have type annotations
- All Pydantic models MUST use strict validation (`Field` with constraints)
- All configuration MUST use `pydantic-settings` with type validation
- All code MUST pass `mypy --strict` without errors
- All API responses MUST be serializable and type-validated

**Enforcement:**
- Pre-commit hook runs `mypy --strict`
- CI/CD pipeline fails on type checking errors
- Pull requests require type check approval

**Rationale:** Type safety prevents runtime errors, improves code readability, enables better IDE support, and ensures contract compliance between components.

### III. Security by Default

Security is a first-class requirement, not an afterthought. Every endpoint, configuration, and data flow MUST be secure by design.

**Requirements:**
- All MCP tools MUST require authentication (API key or OAuth2)
- All user inputs MUST be validated with Pydantic Field constraints
- All sensitive data MUST be stored in environment variables (never in code)
- All API requests MUST implement rate limiting
- All tool invocations MUST be audit logged with user context
- All production deployments MUST use HTTPS
- All error messages MUST NOT leak sensitive information

**Security Layers:**
1. **Authentication:** FastAPI security dependencies (`Depends()`)
2. **Input Validation:** Pydantic models with `Field()` constraints
3. **Rate Limiting:** Per-key request throttling
4. **Audit Logging:** Structured logs for all MCP tool calls
5. **Secret Management:** Environment-based configuration only

**Rationale:** Security breaches can compromise guest data, booking information, and property management operations. Defense-in-depth ensures multiple security layers.

### IV. Test-Driven Development

Testing is mandatory at all levels: unit, integration, and end-to-end. All code MUST achieve >80% coverage before merge.

**Requirements:**
- **Unit Tests:** All services, models, and utilities MUST have unit tests
- **Integration Tests:** All FastAPI endpoints MUST have integration tests
- **MCP Tests:** All tools MUST be tested via MCP protocol
- **E2E Tests:** Critical workflows MUST have end-to-end tests
- **Coverage:** Minimum 80% line coverage, 70% branch coverage
- **Test Isolation:** All tests MUST use mocks for external dependencies

**Test Categories:**
1. **Unit:** Pydantic models, utility functions, business logic
2. **Integration:** FastAPI endpoint responses, authentication flows
3. **MCP Protocol:** Tool discovery, tool invocation, schema validation
4. **E2E:** Complete user workflows (search → book → message)
5. **Load:** Performance under concurrent requests

**Enforcement:**
- `pytest --cov=src --cov-fail-under=80`
- CI/CD fails if coverage drops below threshold
- Pull requests require test approval

**Rationale:** TDD catches bugs early, ensures regression safety, documents expected behavior, and enables confident refactoring.

### V. Async Performance

All I/O operations MUST be asynchronous. Blocking calls are prohibited in request handlers.

**Requirements:**
- All endpoint functions MUST be `async def`
- All external API calls MUST use `httpx.AsyncClient` or `aiohttp`
- All database operations MUST use async drivers
- All file I/O MUST use `aiofiles`
- Connection pooling MUST be implemented for all HTTP clients
- Response caching MUST be implemented for expensive operations

**Performance Targets:**
- API response time: <500ms (95th percentile)
- MCP tool invocation: <1s total (including Hostaway API)
- Concurrent requests: 100+ simultaneous
- Memory efficiency: <100MB per worker

**Anti-Patterns (Prohibited):**
- ❌ `requests` library (use `httpx.AsyncClient`)
- ❌ `time.sleep()` (use `asyncio.sleep()`)
- ❌ Blocking file operations (use `aiofiles`)
- ❌ Synchronous database queries (use async drivers)

**Rationale:** Async I/O enables high concurrency with low resource usage, critical for handling multiple AI agent requests simultaneously.

## Technology Standards

### Required Stack
- **Python:** 3.12+ (latest stable)
- **Framework:** FastAPI 0.100+
- **MCP Integration:** fastapi-mcp 0.4+
- **HTTP Client:** httpx (async)
- **Validation:** Pydantic 2.0+
- **Configuration:** pydantic-settings
- **Testing:** pytest + pytest-asyncio
- **Linting:** ruff
- **Type Checking:** mypy --strict
- **Package Manager:** uv (preferred) or pip

### Prohibited Libraries
- ❌ `requests` (synchronous, use `httpx`)
- ❌ `flask` (use FastAPI)
- ❌ `django` (use FastAPI)
- ❌ Any library without type stubs or `py.typed`

### Code Quality Standards
- **Formatting:** `ruff format` (enforced by pre-commit)
- **Linting:** `ruff check` (zero violations required)
- **Type Checking:** `mypy --strict` (zero errors required)
- **Import Sorting:** `ruff` with `isort` profile
- **Line Length:** 100 characters (not hard limit, readability first)
- **Docstrings:** Required for all public functions, classes, modules

## Development Workflow

### Branch Strategy
- **main:** Production-ready code only
- **develop:** Integration branch (not used - direct to main with feature branches)
- **feature/*:** Feature development branches
- **fix/*:** Bug fix branches
- **hotfix/*:** Emergency production fixes

### Pull Request Requirements
1. **Code Quality:**
   - ✅ All tests pass (`pytest`)
   - ✅ Coverage >80% (`pytest --cov`)
   - ✅ Type checking passes (`mypy --strict`)
   - ✅ Linting passes (`ruff check`)
   - ✅ Formatting applied (`ruff format`)

2. **Documentation:**
   - ✅ Docstrings for new functions
   - ✅ README updated if API changed
   - ✅ CHANGELOG.md entry added
   - ✅ OpenAPI docs auto-generated

3. **Security:**
   - ✅ No secrets in code
   - ✅ Input validation present
   - ✅ Authentication enforced
   - ✅ Security review approved (for auth/data changes)

4. **Testing:**
   - ✅ Unit tests for new code
   - ✅ Integration tests for new endpoints
   - ✅ MCP tests for new tools
   - ✅ E2E tests for new workflows (if critical)

### Spec-Kit Integration
All features MUST follow the Spec-Kit workflow:

1. **Constitution Check:** Verify alignment with principles
2. **Specification:** Define requirements and API contracts
3. **Planning:** Create technical implementation plan
4. **Task Generation:** Break down into actionable tasks
5. **Implementation:** Execute with AI assistance
6. **Validation:** Run analysis and checklist verification

### Commit Message Format
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:** feat, fix, docs, style, refactor, test, chore
**Scopes:** api, mcp, auth, listings, bookings, guests, config, tests

**Examples:**
- `feat(listings): add get_listing MCP tool`
- `fix(auth): prevent API key bypass vulnerability`
- `test(bookings): add E2E workflow tests`

## Governance

### Amendment Procedure
1. **Proposal:** Document proposed change with rationale
2. **Review:** Discuss impact on existing code and templates
3. **Approval:** Requires maintainer approval
4. **Implementation:** Update constitution and propagate changes
5. **Migration:** Update all affected code to comply
6. **Documentation:** Update dependent templates and guides

### Version Policy
- **MAJOR (x.0.0):** Breaking changes to principles or governance
- **MINOR (0.x.0):** New principles or significant expansions
- **PATCH (0.0.x):** Clarifications, wording improvements, typo fixes

### Compliance Review
- **Frequency:** Every Sprint (weekly during active development)
- **Scope:** All merged PRs, production deployments
- **Action:** Non-compliant code MUST be fixed immediately
- **Exception Process:** Requires maintainer approval with documented technical debt

### Constitution Supremacy
This constitution supersedes all other development practices, guidelines, and preferences. When in doubt, the constitution is the final authority.

**Conflict Resolution:**
1. Constitution principle applies
2. If ambiguous, defer to security and type safety
3. If still unclear, consult maintainer

### Runtime Development Guidance
For agent-specific development guidance, see:
- `.claude/CLAUDE.md` - Claude Code configuration
- `docs/FASTAPI_MCP_GUIDE.md` - FastAPI-MCP integration
- `docs/IMPLEMENTATION_ROADMAP.md` - Project roadmap

---

**Version**: 1.0.0 | **Ratified**: 2025-10-12 | **Last Amended**: 2025-10-12
