# Hostaway MCP Server - Development Guide

Last updated: 2025-10-20

## Project Overview

A production-ready FastAPI-based Model Context Protocol (MCP) server that exposes Hostaway property management operations as AI-callable tools. Enables AI assistants like Claude to interact with Hostaway's property management platform through standardized MCP tools.

## Tech Stack

### Core Technologies
- **Python**: 3.12+
- **Web Framework**: FastAPI 0.100+
- **MCP Integration**: fastapi-mcp 0.4+
- **HTTP Client**: httpx 0.27+ (async)
- **Validation**: Pydantic 2.0+ with pydantic-settings
- **Package Manager**: uv (recommended) or pip

### Infrastructure
- **Containerization**: Docker multi-stage builds
- **Database**: N/A (stateless, all data from Hostaway API)
- **CI/CD**: GitHub Actions
- **Deployment**: Docker Compose (production)

## Project Structure

```
hostaway-mcp/
├── .github/
│   └── workflows/
│       ├── ci-cd.yml              # Main CI/CD pipeline
│       ├── auto-merge.yml         # Auto-merge on passing checks
│       └── deploy-production.yml  # Production deployment
├── src/
│   ├── api/
│   │   ├── main.py               # FastAPI app with MCP integration
│   │   ├── middleware/           # Token-aware, rate limiting middleware
│   │   └── routes/              # API route handlers
│   │       ├── auth.py          # Authentication endpoints
│   │       ├── listings.py      # Property listing endpoints
│   │       ├── bookings.py      # Booking management endpoints
│   │       └── financial.py     # Financial reporting endpoints
│   ├── mcp/
│   │   ├── server.py            # MCP server initialization
│   │   ├── config.py            # Configuration management (pydantic-settings)
│   │   ├── auth.py              # OAuth token management
│   │   └── logging.py           # Structured logging with correlation IDs
│   ├── services/
│   │   ├── hostaway_client.py   # HTTP client with retry logic
│   │   ├── rate_limiter.py      # Token bucket rate limiter
│   │   └── financial_calculator.py  # Financial metrics calculation
│   ├── models/                  # Pydantic v2 models
│   │   ├── auth.py
│   │   ├── listings.py
│   │   ├── bookings.py
│   │   └── financial.py
│   └── utils/                   # Utility functions
│       ├── field_projector.py   # Field projection for large responses
│       └── token_estimator.py   # Token count estimation
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── e2e/                     # End-to-end workflow tests
│   ├── performance/             # Load and stress tests
│   └── mcp/                     # MCP protocol tests
├── docs/
│   └── archive/                 # Archived documentation
├── Dockerfile                   # Multi-stage production build
├── docker-compose.yml           # Development setup
├── docker-compose.prod.yml      # Production setup
├── pyproject.toml              # Project dependencies (hatchling)
├── uv.lock                     # Dependency lock file
└── .pre-commit-config.yaml     # Pre-commit hooks

```

## Key Commands

### Development

```bash
# Install dependencies
uv sync

# Run development server with auto-reload
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Run production server
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing

```bash
# All tests with coverage (requires >80%)
uv run pytest --cov=src --cov-report=term --cov-report=html

# Unit tests only
uv run pytest tests/unit -v

# Integration tests
uv run pytest tests/integration -v

# E2E tests
uv run pytest tests/e2e -v -m e2e

# Performance tests
uv run pytest tests/performance -v -m performance
```

### Code Quality

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run all quality checks
uv run pre-commit run --all-files

# Format code
uv run ruff format src/ tests/

# Lint and fix
uv run ruff check src/ tests/ --fix

# Type check
uv run mypy src/ tests/

# Security scan
uv run bandit -r src/
```

### Docker

```bash
# Build image
docker build -t hostaway-mcp:latest .

# Run with Docker Compose (recommended)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Code Style & Conventions

### Python Standards
- **Style Guide**: PEP 8 (enforced by ruff)
- **Type Hints**: Required for all function signatures (enforced by mypy --strict)
- **Line Length**: 100 characters
- **Import Ordering**: isort style (automated by ruff)

### Code Quality Rules
- **Coverage**: Minimum 80% test coverage (enforced in CI)
- **Linting**: All ruff rules must pass
- **Security**: Bandit scan must pass (no high or medium severity issues)
- **Type Safety**: Mypy strict mode must pass

### Naming Conventions
- **Classes**: PascalCase (e.g., `HostawayClient`, `TokenManager`)
- **Functions/Variables**: snake_case (e.g., `get_listings`, `access_token`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`, `MAX_RETRIES`)
- **Private Members**: Leading underscore (e.g., `_refresh_lock`, `_token_cache`)
- **Type Variables**: PascalCase with T prefix (e.g., `TResponse`, `TModel`)

### Documentation Standards
- **Docstrings**: Google style for all public functions/classes
- **Comments**: Explain "why" not "what" (code should be self-documenting)
- **Type Hints**: Always use for function signatures and complex data structures

## Configuration

### Environment Variables

**Required**:
- `HOSTAWAY_ACCOUNT_ID` - Hostaway account identifier
- `HOSTAWAY_SECRET_KEY` - Hostaway API secret (stored securely)

**Optional** (with defaults):
- `HOSTAWAY_API_BASE_URL` - Default: `https://api.hostaway.com/v1`
- `RATE_LIMIT_IP` - Default: 15 (per 10 seconds)
- `RATE_LIMIT_ACCOUNT` - Default: 20 (per 10 seconds)
- `MAX_CONCURRENT_REQUESTS` - Default: 10 (CI) / 50 (local dev)
- `TOKEN_REFRESH_THRESHOLD_DAYS` - Default: 7
- `LOG_LEVEL` - Default: INFO

### Configuration Management
- Uses `pydantic-settings` for environment variable loading
- Validates configuration on startup
- Supports `.env` file for local development (ignored in CI)
- Secrets protected with `SecretStr` type

## Architecture Patterns

### Rate Limiting
- **Dual Strategy**: IP-based (15 req/10s) and Account-based (20 req/10s)
- **Concurrency Control**: Max concurrent requests (default: 10)
- **Token Bucket Algorithm**: Smooths traffic spikes

### Connection Pooling
- **Max connections**: 50
- **Keep-alive**: 20 connections for 30 seconds
- **Timeouts**: Connect (5s), Read (30s), Write (10s), Pool (5s)

### Retry Logic
- **Max attempts**: 3 retries (4 total)
- **Backoff**: Exponential (2s → 4s → 8s)
- **Retryable**: Timeout, Network, Connection errors
- **Non-retryable**: 4xx client errors (except 401)

### Token Management
- **OAuth 2.0**: Client Credentials flow
- **Auto-refresh**: 7 days before expiration
- **Thread-safe**: asyncio.Lock for concurrent access
- **401 Handling**: Automatic token invalidation and retry

### Response Optimization
- **Token-Aware Middleware**: Estimates response size, triggers summarization if >4000 tokens
- **Field Projection**: Dynamically reduces response fields for large objects
- **Pagination**: Enforced for list endpoints to prevent large responses

## CI/CD Pipeline

### GitHub Actions Workflows

**CI/CD Pipeline** (`.github/workflows/ci-cd.yml`):
1. **Lint**: Ruff format and lint checks
2. **Type Check**: Mypy --strict validation
3. **Test**: Unit and integration tests
4. **Coverage**: Fails if <80% coverage
5. **Security**: Bandit security scan
6. **Docker Build**: Multi-stage image (main branch only)

**Auto-Merge** (`.github/workflows/auto-merge.yml`):
- Automatically enables auto-merge on PRs when all checks pass
- Only runs for PR events (skips direct pushes to main)
- Uses squash merge strategy
- Deletes branch after merge

### Pre-commit Hooks
- **ruff format**: Code formatting
- **ruff check**: Linting
- **bandit**: Security scanning
- **File checks**: Trailing whitespace, EOF, large files, merge conflicts
- **Secret detection**: AWS credentials, private keys

## Testing Strategy

### Current Coverage
**76.90%** (124 passing tests)

### Test Categories
1. **Unit Tests** (`tests/unit/`):
   - Models, services, utilities
   - Configuration loading
   - Middleware behavior

2. **Integration Tests** (`tests/integration/`):
   - API endpoints
   - Authentication flow
   - Financial calculations

3. **E2E Tests** (`tests/e2e/`):
   - Complete workflows
   - Auth → List → Details → Availability

4. **Performance Tests** (`tests/performance/`):
   - Load testing (100+ concurrent)
   - Rate limiting validation

5. **MCP Tests** (`tests/mcp/`):
   - Tool discovery and schema validation
   - Some tests marked as `xfail` (TDD - awaiting implementation)

### Test Best Practices
- **Mock external dependencies**: Use `httpx_mock` for HTTP calls
- **Patch environment-dependent config**: Test flexibility for CI vs local
- **Test middleware behavior**: Patch during test execution, not app setup
- **Mark long tests**: Use `@pytest.mark.performance` for slow tests
- **Expected failures**: Use `@pytest.mark.xfail` for TDD tests

## Security

### Implemented Measures
- ✅ OAuth 2.0 authentication with automatic token refresh
- ✅ Environment-based credentials (no hardcoded secrets)
- ✅ Pydantic input validation
- ✅ Rate limiting (prevent API abuse)
- ✅ Audit logging with correlation IDs
- ✅ CORS configuration
- ✅ Non-root Docker user
- ✅ Bandit security scanning in CI
- ✅ Secret detection in pre-commit hooks

### Security Best Practices
- **Never commit secrets**: Use `.env` files (gitignored)
- **Use SecretStr**: For sensitive configuration values
- **Validate all inputs**: Use Pydantic models
- **Log security events**: With correlation IDs for tracing
- **Run security scans**: Before committing (pre-commit hooks)

## Logging & Debugging

### Structured Logging
- **Format**: JSON with correlation IDs
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Correlation IDs**: Generated per request (or from `X-Correlation-ID` header)
- **Fields**: timestamp, level, message, correlation_id, context

### Debugging Tips
```bash
# View logs in JSON format
tail -f logs/app.log | jq

# Trace specific request
grep "correlation_id_here" logs/app.log | jq

# Filter by level
jq 'select(.level == "ERROR")' logs/app.log
```

## Recent Changes
- 010-we-need-to: Added Python 3.12+ (existing project requirement), Bash 4.0+ for worktree orchestration
- 008-fix-issues-identified: Added Python 3.12+ + FastAPI 0.100+, fastapi-mcp 0.4+, httpx 0.27+, Pydantic 2.0+, pydantic-settings

### 2025-10-20
- Fixed auto-merge workflow to only run on PR events (not direct pushes)

### 2025-10-19

### 2025-10-12

## Production Status

✅ **Production Ready**

**Completed Phases**:
- ✅ Phase 1: Setup and Infrastructure
- ✅ Phase 2: Foundational Components
- ✅ Phase 3: Authentication (User Story 1)
- ✅ Phase 4: Property Listings (User Story 2)
- ✅ Phase 5: Booking Management (User Story 3)
- ⏭️ Phase 6: Guest Communication (User Story 4) - *Skipped (requires test environment)*
- ✅ Phase 7: Financial Reporting (User Story 5)
- ✅ Phase 8: Polish & Production Readiness

**Next Steps**:
- Deploy to staging environment for end-to-end validation
- Monitor production metrics and performance
- Iterate based on user feedback

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Verify `HOSTAWAY_ACCOUNT_ID` and `HOSTAWAY_SECRET_KEY` in `.env`
- Check token expiration (auto-refreshes 7 days before expiry)

**Rate Limit Exceeded**
- Reduce request frequency
- Adjust `RATE_LIMIT_IP` and `RATE_LIMIT_ACCOUNT` if needed
- Check concurrent request count

**Connection Timeout**
- Check internet connection
- Verify `HOSTAWAY_API_BASE_URL` is correct
- Increase timeout values if needed

**Test Failures in CI**
- Check for environment-dependent values (e.g., .env file vs code defaults)
- Ensure tests are flexible for both CI and local environments
- Review middleware patching (must be active during test execution)

**Docker Build Failures**
- Verify .dockerignore doesn't exclude required files (e.g., README.md)
- Check multi-stage build dependencies
- Ensure uv.lock is committed (required for reproducible builds)

## Resources

- [FastAPI-MCP Documentation](https://fastapi-mcp.tadata.com/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Hostaway API Docs](https://docs.hostaway.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
- [uv Package Manager](https://docs.astral.sh/uv/)

## Contributing

1. Follow spec-driven development workflow
2. Write tests for all new features (maintain >80% coverage)
3. Run pre-commit hooks before committing
4. Update documentation (README.md, CLAUDE.md)
5. Follow security best practices
6. Use structured logging with correlation IDs
7. Create meaningful commit messages (conventional commits style)

---

**Project Status**: ✅ Production Ready | **Test Coverage**: 76.90% | **CI/CD**: Passing
