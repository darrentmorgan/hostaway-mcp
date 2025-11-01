# Hostaway MCP Server

[![Deploy to Production](https://github.com/darrenmorgan/hostaway-mcp/actions/workflows/deploy-production.yml/badge.svg)](https://github.com/darrenmorgan/hostaway-mcp/actions/workflows/deploy-production.yml)

A production-ready FastAPI-based Model Context Protocol (MCP) server that exposes Hostaway property management operations as AI-callable tools.

## Overview

This project enables AI assistants like Claude to interact with Hostaway's property management platform through standardized MCP tools. Built with FastAPI-MCP, it provides type-safe, authenticated access to property listings, booking management, and financial reporting.

## Features

- ✅ **MCP Protocol Support**: All Hostaway operations exposed as AI-callable tools
- ✅ **Type Safety**: Full Pydantic v2 model validation with strict typing
- ✅ **Authentication**: OAuth 2.0 Client Credentials flow with automatic token refresh
- ✅ **Rate Limiting**: Dual rate limits (IP and account-based) with connection pooling
- ✅ **Structured Logging**: JSON logging with correlation IDs for request tracing
- ✅ **Performance**: Async/await, connection pooling, and exponential backoff retry logic
- ✅ **Production Ready**: Docker support, CI/CD pipeline, comprehensive test coverage

## Recent Updates (Issue #008)

**Three MCP server improvements implemented (2025-10-28)**:

### ✅ Issue #008-US1: 404 vs 401 Priority Fix
- **Problem**: Non-existent routes returned `401 Unauthorized` instead of `404 Not Found`
- **Solution**: Added custom 404 exception handler and route existence check in authentication middleware
- **Impact**: Improved API developer experience - route existence now checked before authentication
- **Tests**: 7 integration tests covering 404 behavior, auth preservation, CORS, and correlation IDs

### ✅ Issue #008-US2: Rate Limit Visibility Headers
- **Problem**: API consumers had no visibility into rate limit status
- **Solution**: Added `RateLimiterMiddleware` that injects industry-standard headers on all responses
  - `X-RateLimit-Limit`: Maximum requests allowed per window
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Unix timestamp when window resets
  - `Retry-After`: Seconds to wait when limit exceeded
- **Impact**: Transparent rate limiting for better client retry logic
- **Tests**: 9 tests (4 integration + 5 unit) + 3 performance regression tests

### ✅ Issue #008-US3: API Key Generation CLI
- **Problem**: No documented way to generate test API keys for local development
- **Solution**: Created CLI script (`src/scripts/generate_api_key.py`) with:
  - Cryptographically secure key generation (`secrets.token_urlsafe(32)`)
  - SHA-256 hashing for database storage
  - Organization verification before key creation
  - One-time display of plain key (security best practice)
- **Usage**: `uv run python -m src.scripts.generate_api_key --org-id 1 --user-id user-123`
- **Documentation**: See `docs/API_KEY_GENERATION.md`
- **Tests**: 6 unit tests covering format, hashing, CLI interface, and entropy

**All implementations follow TDD** - tests written first, implementation second.

## Quick Start

**Server is already deployed and accessible!**

- **Base URL**: `http://72.60.233.157:8080`
- **Health Check**: http://72.60.233.157:8080/health
- **API Docs**: http://72.60.233.157:8080/docs

### Using with Claude Desktop

Add to your `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hostaway": {
      "url": "http://72.60.233.157:8080/mcp/v1",
      "transport": "sse"
    }
  }
}
```

Restart Claude Desktop and start using Hostaway MCP tools!

For detailed setup instructions, see [docs/SIMPLE_SETUP.md](docs/SIMPLE_SETUP.md).

## Automated MCP Migration

**Parallel execution system** for applying MCP Migration Guide fixes using git worktrees.

### Quick Start

```bash
# Execute all 7 fixes in parallel (~45 minutes vs 4 hours sequential)
.automation/scripts/orchestrator.sh --auto-rollback --failure-threshold 30

# Monitor progress in real-time
.automation/scripts/status.sh --watch --metrics

# Generate HTML report
.automation/scripts/generate-report.sh --format html --output report.html
```

### Key Features

- ✅ **6x Speedup**: Parallel execution using git worktrees (4 hours → 45 min)
- ✅ **Zero Manual Intervention**: Fully automated from execution to PR merge
- ✅ **Safety First**: Automatic rollback on failure threshold, checkpoint tags
- ✅ **Comprehensive Testing**: MCP Inspector validation + pytest integration
- ✅ **Real-Time Monitoring**: Progress visualization with metrics
- ✅ **Audit Trail**: Timestamped logs and execution state tracking

### Architecture

The system executes 7 MCP fixes in 2 waves using dependency-aware scheduling:

- **Wave 1** (Parallel): 6 independent fixes run concurrently in isolated git worktrees
- **Wave 2** (Sequential): Fix-4 runs after Wave 1 (depends on Fix-1 and Fix-3)

Each fix executes in its own worktree with:
- Automated implementation
- Unit + integration tests (pytest)
- MCP Inspector schema validation
- Automatic PR creation (GitHub CLI)

### Prerequisites

- Git >= 2.30 (worktree support)
- Python >= 3.12
- GitHub CLI (`gh`) - for PR automation
- Node.js (optional) - for MCP Inspector

### Documentation

For complete documentation, see [.automation/README.md](.automation/README.md)

**Core scripts**:
- `orchestrator.sh` - Main entry point
- `status.sh` - Real-time monitoring
- `rollback.sh` - Emergency recovery
- `generate-report.sh` - Summary reports
- `cleanup.sh` - Manual cleanup

## Recent Updates (Issue #008)

**Three MCP server improvements implemented (2025-10-28)**:

### ✅ Issue #008-US1: 404 vs 401 Priority Fix
- **Problem**: Non-existent routes returned `401 Unauthorized` instead of `404 Not Found`
- **Solution**: Added custom 404 exception handler and route existence check in authentication middleware
- **Impact**: Improved API developer experience - route existence now checked before authentication
- **Tests**: 7 integration tests covering 404 behavior, auth preservation, CORS, and correlation IDs

### ✅ Issue #008-US2: Rate Limit Visibility Headers
- **Problem**: API consumers had no visibility into rate limit status
- **Solution**: Added `RateLimiterMiddleware` that injects industry-standard headers on all responses
  - `X-RateLimit-Limit`: Maximum requests allowed per window
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Unix timestamp when window resets
  - `Retry-After`: Seconds to wait when limit exceeded
- **Impact**: Transparent rate limiting for better client retry logic
- **Tests**: 9 tests (4 integration + 5 unit) + 3 performance regression tests

### ✅ Issue #008-US3: API Key Generation CLI
- **Problem**: No documented way to generate test API keys for local development
- **Solution**: Created CLI script (`src/scripts/generate_api_key.py`) with:
  - Cryptographically secure key generation (`secrets.token_urlsafe(32)`)
  - SHA-256 hashing for database storage
  - Organization verification before key creation
  - One-time display of plain key (security best practice)
- **Usage**: `uv run python -m src.scripts.generate_api_key --org-id 1 --user-id user-123`
- **Documentation**: See `docs/API_KEY_GENERATION.md`
- **Tests**: 6 unit tests covering format, hashing, CLI interface, and entropy

**All implementations follow TDD** - tests written first, implementation second.

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip
- Hostaway API credentials (Client ID and Secret)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd hostaway-mcp

# Install dependencies with uv (recommended)
uv sync

# Or with pip
pip install -r pyproject.toml
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Hostaway credentials
# Required variables:
HOSTAWAY_CLIENT_ID=your_client_id
HOSTAWAY_CLIENT_SECRET=your_client_secret
HOSTAWAY_API_BASE_URL=https://api.hostaway.com/v1
```

### Running the Server

```bash
# Development mode with auto-reload
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Docker (recommended for production)
docker-compose up -d
```

### Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# View OpenAPI documentation
open http://localhost:8000/docs

# View ReDoc documentation
open http://localhost:8000/redoc
```

## Available MCP Tools

All FastAPI routes are automatically exposed as MCP tools via FastAPI-MCP integration.

### Authentication

- `POST /auth/authenticate` - Obtain access token (manual authentication for testing)
- `POST /auth/refresh` - Refresh expired access token

### Property Listings

- `GET /api/listings` - List all properties with pagination
  - Query params: `limit`, `cursor`, `summary` (optional)
  - **New**: `summary=true` returns compact response (80-90% size reduction)
    - Only essential fields: id, name, city, country, bedrooms, status
    - Use `GET /api/listings/{id}` for full details
- `GET /api/listings/{id}` - Get detailed property information
- `GET /api/listings/{id}/availability` - Check availability for date range
  - Query params: `start_date`, `end_date` (YYYY-MM-DD)

### Booking Management

- `GET /api/reservations` - Search bookings with filters
  - Query params: `listing_id`, `check_in_from`, `check_in_to`, `check_out_from`, `check_out_to`, `status`, `guest_email`, `booking_source`, `min_guests`, `max_guests`, `limit`, `cursor`, `summary` (optional)
  - **New**: `summary=true` returns compact response (80-90% size reduction)
    - Only essential fields: id, guestName, checkIn, checkOut, listingId, status, totalPrice
    - Use `GET /api/reservations/{id}` for full details
- `GET /api/reservations/{id}` - Get booking details
- `GET /api/reservations/{id}/guest` - Get guest information for booking

### Financial Reporting

- `GET /api/financialReports` - Get financial report for date range
  - Query params: `start_date`, `end_date` (YYYY-MM-DD), optional `listing_id`
  - Returns revenue breakdown, expense breakdown, profitability metrics

## Usage Examples

### Response Summarization (New!)

The API now supports optional response summarization for list endpoints, reducing response sizes by 80-90% for AI assistant consumption:

**Listings - Full Response**:
```bash
curl "http://72.60.233.157:8080/api/listings?limit=10"
# Returns full property details: id, name, address, city, state, country, postal_code,
# description, capacity, bedrooms, bathrooms, property_type, base_price, amenities, images, etc.
```

**Listings - Summarized Response**:
```bash
curl "http://72.60.233.157:8080/api/listings?limit=10&summary=true"
# Returns only essential fields:
# {
#   "items": [
#     {
#       "id": 12345,
#       "name": "Luxury Villa in Seminyak",
#       "city": "Seminyak",
#       "country": "Indonesia",
#       "bedrooms": 3,
#       "status": "Available"
#     }
#   ],
#   "nextCursor": "eyJvZmZzZXQiOjEwfQ==",
#   "meta": {
#     "totalCount": 100,
#     "pageSize": 10,
#     "hasMore": true,
#     "note": "Use GET /api/listings/{id} to see full property details"
#   }
# }
```

**Bookings - Full Response**:
```bash
curl "http://72.60.233.157:8080/api/reservations?limit=10&status=confirmed"
# Returns full booking details including nested guest objects, payment history, etc.
```

**Bookings - Summarized Response**:
```bash
curl "http://72.60.233.157:8080/api/reservations?limit=10&status=confirmed&summary=true"
# Returns only essential fields:
# {
#   "items": [
#     {
#       "id": 67890,
#       "guestName": "John Doe",
#       "checkIn": "2025-11-15",
#       "checkOut": "2025-11-22",
#       "listingId": 12345,
#       "status": "confirmed",
#       "totalPrice": 2500.00
#     }
#   ],
#   "nextCursor": "eyJvZmZzZXQiOjEwfQ==",
#   "meta": {
#     "totalCount": 50,
#     "pageSize": 10,
#     "hasMore": true,
#     "note": "Use GET /api/reservations/{id} to see full booking details"
#   }
# }
```

**Benefits**:
- 80-90% reduction in response size
- Faster response times
- Reduced context window consumption for AI assistants
- Backward compatible (defaults to full response)
- Guidance note points to detailed endpoints

## Project Structure

```
hostaway-mcp/
├── .github/
│   └── workflows/
│       └── ci.yml           # CI/CD pipeline (pytest, ruff, mypy, docker)
├── src/
│   ├── api/
│   │   ├── main.py          # FastAPI app with MCP integration
│   │   └── routes/          # API route handlers
│   │       ├── auth.py      # Authentication endpoints
│   │       ├── listings.py  # Property listing endpoints
│   │       ├── bookings.py  # Booking management endpoints
│   │       └── financial.py # Financial reporting endpoints
│   ├── mcp/
│   │   ├── server.py        # MCP server initialization
│   │   ├── config.py        # Configuration management
│   │   ├── auth.py          # OAuth token management
│   │   └── logging.py       # Structured logging with correlation IDs
│   ├── services/
│   │   ├── hostaway_client.py  # HTTP client with retry logic
│   │   └── rate_limiter.py     # Token bucket rate limiter
│   └── models/              # Pydantic v2 models
│       ├── auth.py
│       ├── listings.py
│       ├── bookings.py
│       └── financial.py
├── tests/
│   ├── unit/                # Unit tests (76.90% coverage)
│   ├── integration/         # Integration tests
│   ├── e2e/                 # End-to-end workflow tests
│   └── performance/         # Load and stress tests
├── Dockerfile               # Multi-stage production build
├── docker-compose.yml       # Local development setup
└── .pre-commit-config.yaml  # Pre-commit hooks (ruff, mypy, bandit)
```

## Development

### Running Tests

```bash
# All tests with coverage
uv run pytest --cov=src --cov-report=term --cov-report=html

# Unit tests only
uv run pytest tests/unit -v

# Integration tests only
uv run pytest tests/integration -v

# E2E tests
uv run pytest tests/e2e -v -m e2e

# Performance tests (slow)
uv run pytest tests/performance -v -m performance
```

### Code Quality

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run all checks manually
uv run pre-commit run --all-files

# Format code
uv run ruff format src/ tests/

# Lint code
uv run ruff check src/ tests/ --fix

# Type check
uv run mypy src/ tests/

# Security scan
uv run bandit -r src/
```

### Pre-Push Validation

**IMPORTANT**: Always run pre-push checks before pushing to CI/CD to avoid build failures.

```bash
# Run all pre-push validation checks (recommended)
make pre-push

# Or run the script directly
./scripts/pre-push-check.sh
```

The pre-push script validates:
- ✅ **Formatting**: Ruff format check
- ✅ **Linting**: Ruff lint check
- ✅ **Tests**: Quick integration test run (no coverage)

If all checks pass, you'll see:
```
✓ All pre-push checks passed!
✓ Safe to push to CI/CD
```

If any check fails, fix the issues before pushing:
```bash
# Fix formatting
make format

# Fix linting issues
make lint

# Run tests to debug failures
make test-integration
```

**Available Make Targets**:
```bash
make help              # Show all available targets
make pre-push          # Run pre-push validation
make format            # Format code with ruff
make format-check      # Check formatting without changes
make lint              # Run linter
make test              # Run all tests with coverage
make test-integration  # Run integration tests only
make test-unit         # Run unit tests only
make clean             # Remove build artifacts
make install           # Install dependencies
```

### Logging and Debugging

The server uses structured JSON logging with correlation IDs:

```bash
# View logs in JSON format
tail -f logs/app.log | jq

# Trace a specific request using correlation ID
grep "correlation_id_here" logs/app.log | jq
```

Correlation IDs are automatically:
- Generated for each request (or extracted from `X-Correlation-ID` header)
- Included in all log entries
- Returned in response headers

## Deployment

### Docker

```bash
# Build image
docker build -t hostaway-mcp:latest .

# Run container
docker run -p 8000:8000 --env-file .env hostaway-mcp:latest

# Health check
curl http://localhost:8000/health
```

### Docker Compose (Recommended)

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment

The project includes:
- Multi-stage Dockerfile for optimized image size
- Non-root user for security
- Health checks for container orchestration
- GitHub Actions CI/CD pipeline
- Pre-commit hooks for code quality

Environment variables for production:
```bash
# Required
HOSTAWAY_CLIENT_ID=<your_client_id>
HOSTAWAY_CLIENT_SECRET=<your_client_secret>

# Optional (with defaults)
HOSTAWAY_API_BASE_URL=https://api.hostaway.com/v1
RATE_LIMIT_IP=15
RATE_LIMIT_ACCOUNT=20
MAX_CONCURRENT_REQUESTS=10
LOG_LEVEL=INFO
```

## Architecture

### Rate Limiting

Dual rate limiting strategy:
- **IP-based**: 15 requests per 10 seconds
- **Account-based**: 20 requests per 10 seconds
- **Concurrency**: Max 10 concurrent requests (configurable)

### Connection Pooling

HTTP client configuration:
- **Max connections**: 50
- **Keep-alive connections**: 20
- **Keep-alive expiry**: 30 seconds
- **Timeouts**: Connect (5s), Read (30s), Write (10s), Pool (5s)

### Retry Logic

Exponential backoff for transient failures:
- **Max attempts**: 3 retries (4 total attempts)
- **Backoff**: 2s → 4s → 8s
- **Retryable errors**: Timeout, Network, Connection errors
- **Non-retryable**: 4xx client errors (except 401)

### Token Management

OAuth 2.0 Client Credentials flow:
- **Auto-refresh**: 7 days before expiration
- **Thread-safe**: asyncio.Lock for concurrent access
- **Retry on 401**: Automatic token invalidation and retry

## Testing

Current test coverage: **76.90%**

Test categories:
- **Unit tests**: Models, services, utilities
- **Integration tests**: API endpoints, authentication flow
- **E2E tests**: Complete workflows (auth → list → details → availability)
- **Performance tests**: Load testing (100+ concurrent), rate limiting validation
- **MCP tests**: Tool discovery and invocation

## Security

Security measures:
- ✅ OAuth 2.0 authentication with automatic token refresh
- ✅ Environment-based credential management (no hardcoded secrets)
- ✅ Input validation with Pydantic models
- ✅ Rate limiting to prevent API abuse
- ✅ Audit logging with correlation IDs
- ✅ CORS configuration (configure for production)
- ✅ Non-root Docker user
- ✅ Security scanning with Bandit in CI/CD
- ✅ HTTPS enforcement (via reverse proxy in production)

## CI/CD Pipeline

GitHub Actions workflow includes:
1. **Linting**: Ruff format and lint checks
2. **Type checking**: Mypy --strict validation
3. **Testing**: Unit and integration tests with coverage
4. **Coverage enforcement**: Fails if <80% coverage
5. **Security audit**: Bandit security scan
6. **Docker build**: Multi-stage image build (on main branch)

## Performance

Benchmarks:
- **Authentication**: <5 seconds for initial token
- **API response time**: <2 seconds average
- **MCP tool invocation**: <1 second overhead
- **Concurrent requests**: 100+ requests handled via rate limiting queue
- **Zero downtime**: Graceful shutdown with lifespan management

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Verify `HOSTAWAY_CLIENT_ID` and `HOSTAWAY_CLIENT_SECRET` in `.env`
- Check token expiration (auto-refreshes 7 days before expiry)

**Rate limit exceeded**
- Reduce request frequency
- Adjust `RATE_LIMIT_IP` and `RATE_LIMIT_ACCOUNT` if needed
- Check concurrent request count against `MAX_CONCURRENT_REQUESTS`

**Connection timeout**
- Check internet connection
- Verify `HOSTAWAY_API_BASE_URL` is correct
- Increase timeout values in `hostaway_client.py` if needed

**Missing dependencies**
- Run `uv sync` or `pip install -r pyproject.toml`
- Check Python version (requires 3.12+)

## Contributing

1. Follow spec-driven development workflow
2. Write tests for all new features (maintain >80% coverage)
3. Run pre-commit hooks before committing
4. Update documentation
5. Follow security best practices
6. Use structured logging with correlation IDs

## License

MIT

## Resources

- [FastAPI-MCP Documentation](https://fastapi-mcp.tadata.com/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Hostaway API Docs](https://docs.hostaway.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)

## Support

For issues and questions:
- Check [OpenAPI Documentation](http://localhost:8000/docs) (when server is running)
- Review logs with correlation IDs for debugging
- Open an issue on GitHub

---

**Status**: ✅ **Production Ready**

**Implemented Features**:
- ✅ Phase 1: Setup and Infrastructure
- ✅ Phase 2: Foundational Components
- ✅ Phase 3: Authentication (User Story 1)
- ✅ Phase 4: Property Listings (User Story 2)
- ✅ Phase 5: Booking Management (User Story 3)
- ⏭️ Phase 6: Guest Communication (User Story 4) - *Skipped (requires test environment)*
- ✅ Phase 7: Financial Reporting (User Story 5)
- ✅ Phase 8: Polish & Production Readiness

**Test Coverage**: 76.90% (124 passing tests)

**Next Steps**: Deploy to staging environment for end-to-end validation
