# Research: Automated Overflow-Safety Test Suite

**Feature ID**: 006-overflow-safety-test-suite
**Date**: 2025-10-16
**Status**: Complete

---

## R001: Existing Test Infrastructure Analysis

### Current Testing Stack

**Test Framework**: pytest 8.4.2+ with plugins
```toml
[dependency-groups]
dev = [
    "pytest>=8.4.2",
    "pytest-asyncio>=1.2.0",   # Async test support
    "pytest-cov>=7.0.0",       # Coverage reporting
    "pytest-mock>=3.12.0",     # Mock utilities
    "respx>=0.21.1",           # HTTP mocking for httpx
]
```

**Test Organization** (`tests/` directory structure):
```
tests/
├── unit/               # Unit tests (fast, isolated)
│   ├── test_token_estimator.py
│   ├── test_dependencies.py
│   ├── test_usage_tracking.py
│   └── ... (14 files)
├── integration/        # Integration tests (slower, real dependencies)
│   ├── test_listings_api.py
│   ├── test_bookings_api.py
│   └── ... (8 files)
├── utils/             # Utility function tests
│   ├── test_cursor_codec.py
│   ├── test_field_projector.py
│   └── test_token_estimator.py
├── services/          # Service layer tests
├── api/               # API route tests
├── mcp/               # MCP-specific tests
├── database/          # Database/RLS tests (SQL)
├── e2e/               # End-to-end tests
└── performance/       # Performance/load tests
```

**Test Configuration** (pyproject.toml):
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # Auto-detect async tests
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = [
    "--strict-markers",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=80",  # 80% coverage requirement
]
markers = [
    "e2e: End-to-end integration tests",
    "performance: Performance and load tests",
    "slow: Slow running tests",
]
```

**Key Findings**:
- ✅ Mature pytest-based infrastructure ready for extension
- ✅ Async test support already configured
- ✅ Coverage requirements enforced (80% minimum)
- ✅ Test categorization with markers
- ⚠️ No dedicated overflow/token-safety tests yet
- ⚠️ HTTP mocking uses `respx` (good for httpx, but need stdio mocking for MCP)

**Recommendation**: Extend existing infrastructure with new `tests/overflow-safety/` directory

---

## R002: Token Estimation Infrastructure

### Existing Implementation

**File**: `src/utils/token_estimator.py` (155 lines, fully implemented)

**Core Algorithm**:
```python
def estimate_tokens(text: str) -> int:
    """Estimate Claude token count from text.

    Uses 4 characters per token heuristic with 20% safety margin.
    """
    char_count = len(text)
    base_estimate = char_count / 4
    safety_margin = base_estimate * 0.20
    return int(base_estimate + safety_margin)
```

**Key Functions Available**:
1. `estimate_tokens(text)` - Basic token estimation from text
2. `estimate_tokens_from_dict(obj)` - Estimate from dictionary (JSON serialization)
3. `estimate_tokens_from_list(items)` - Estimate from list of objects
4. `check_token_budget(text, threshold)` - Check if exceeds budget
5. `estimate_reduction_needed(current, target)` - Calculate reduction needed
6. `calculate_safe_page_size(avg_item_tokens, threshold)` - Calculate safe pagination

**Accuracy Metrics**:
- **Heuristic**: 1 token ≈ 4 characters
- **Safety Margin**: +20% to avoid underestimation
- **Performance**: <20ms per estimation (tested)
- **Target Accuracy**: ±10% acceptable variance

**Test Coverage** (`tests/utils/test_token_estimator.py`):
- ✅ 343 lines of comprehensive tests
- ✅ Edge cases: empty strings, exact boundaries, large text
- ✅ Performance validation (<20ms requirement)
- ✅ Budget checking at various thresholds
- ✅ Page size calculations

**Example Usage**:
```python
# Check if response will exceed threshold
text = json.dumps(large_response)
estimated, exceeds, ratio = check_token_budget(text, threshold=50000)

if exceeds:
    # Activate preview mode
    page_size = calculate_safe_page_size(
        avg_item_tokens=estimated // len(items),
        target_threshold=50000
    )
```

**Limitations**:
- Character-based estimation (not actual tokenization)
- Assumes uniform token distribution
- No special handling for code/JSON structure
- 20% margin may be conservative for some content

**Key Finding**: Token estimator is production-ready and performant. Can be used directly for overflow testing without modification.

---

## R003: Pagination Service Infrastructure

### Current Implementation

**File**: `src/services/pagination_service.py` (242 lines, fully implemented)

**Architecture**:
```python
class PaginationService:
    def __init__(
        self,
        secret: str,
        default_page_size: int = 50,
        max_page_size: int = 200,
    ):
        self.cursor_storage = get_cursor_storage()

    def create_cursor(self, offset, order_by=None, filters=None) -> str:
        """Create HMAC-signed pagination cursor"""

    def parse_cursor(self, cursor: str) -> dict:
        """Validate and decode cursor"""

    def build_response(self, items, total_count, params) -> PaginatedResponse:
        """Build response with nextCursor and metadata"""
```

**Response Schema** (`src/models/pagination.py`):
```python
class PageMetadata(BaseModel):
    totalCount: int
    pageSize: int
    hasMore: bool

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    nextCursor: str | None
    meta: PageMetadata
```

**Cursor Implementation**:
- **Encoding**: Base64-encoded JSON with HMAC signature
- **Storage**: In-memory cursor storage service
- **Validation**: HMAC verification prevents tampering
- **Expiration**: Configurable TTL (default: 1 hour)

**Integration Pattern**:
```python
# In endpoint handler
pagination_service = get_pagination_service(secret="...")
response = await pagination_service.paginate_query(
    query_func=fetch_listings,
    params=PaginationParams(cursor=request_cursor, limit=50),
    total_count=total_listings,
    order_by="created_desc"
)
# Returns: PaginatedResponse[Listing]
```

**Test Coverage**:
- ✅ Cursor encoding/decoding (`tests/utils/test_cursor_codec.py`)
- ✅ Cursor storage (`tests/services/test_cursor_storage.py`)
- ✅ Pagination scenarios in integration tests
- ⚠️ Missing: Boundary tests (empty results, single page, exact threshold)

**Key Finding**: Pagination infrastructure is complete and contract-ready. Need to add overflow-specific validation tests.

---

## R004: Summarization Service Infrastructure

### Current Implementation

**File**: `src/services/summarization_service.py` (201 lines)

**Capabilities**:
```python
class SummarizationService:
    def summarize_object(self, obj, obj_type, endpoint) -> SummaryResponse:
        """Summarize using field projection"""

    def should_summarize(self, obj, token_threshold=4000) -> tuple[bool, int]:
        """Determine if summarization needed"""

    def calculate_reduction(self, original, summary) -> SummarizationResult:
        """Calculate metrics (field count, token reduction)"""

    def summarize_list(self, items, obj_type) -> list[dict]:
        """Project fields for list of objects"""
```

**Field Projection** (`src/utils/field_projector.py`):
```python
ESSENTIAL_FIELDS = {
    "booking": ["id", "status", "guestName", "checkIn", "checkOut", "totalPrice"],
    "listing": ["id", "name", "address", "city", "capacity", "basePrice"],
    "guest": ["id", "firstName", "lastName", "email"],
    # ... etc
}

def project_fields(obj: dict, fields: list[str]) -> dict:
    """Extract only specified fields from object"""
```

**Response Schema** (`src/models/summarization.py`):
```python
class SummaryMetadata(BaseModel):
    kind: str  # "preview"
    totalFields: int
    projectedFields: list[str]
    detailsAvailable: DetailsFetchInfo

class SummaryResponse(BaseModel):
    summary: dict[str, Any]  # Projected object
    meta: SummaryMetadata
```

**Example Workflow**:
```python
# Check if object needs summarization
should_summarize, tokens = service.should_summarize(
    large_booking,
    token_threshold=4000
)

if should_summarize:
    # Return preview with metadata
    response = service.summarize_object(
        obj=large_booking,
        obj_type="booking",
        endpoint="/api/v1/bookings/{id}"
    )
    # response.summary contains essential fields only
    # response.meta indicates full details available
```

**Test Coverage**:
- ✅ Field projection logic (`tests/utils/test_field_projector.py`)
- ⚠️ Missing: Integration tests for summarization service
- ⚠️ Missing: Token reduction validation

**Key Finding**: Summarization infrastructure exists but needs integration testing and overflow validation.

---

## R005: HTTP Mocking Patterns

### Current Approach

**Library**: `respx` for httpx-based APIs

**Example Pattern** (from `tests/integration/test_listings_api.py`):
```python
import httpx
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_listing_response() -> dict:
    """Create mock Hostaway listing response."""
    return {
        "id": 12345,
        "name": "Cozy Downtown Apartment",
        # ... full mock object
    }

@pytest.mark.asyncio
async def test_get_listings_success(test_config, mock_listing_response):
    """Test successful retrieval."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "success",
        "result": [mock_listing_response],
        "count": 1,
    }
    mock_client.get = AsyncMock(return_value=mock_response)

    # Use mocked client in test
    # client = HostawayClient(config=test_config, http_client=mock_client)
```

**Strengths**:
- ✅ Detailed control over responses
- ✅ Can simulate pagination, errors, edge cases
- ✅ Fast execution (no network calls)
- ✅ Deterministic test outcomes

**Limitations**:
- ⚠️ HTTP-focused (doesn't mock stdio for MCP server)
- ⚠️ Verbose fixture setup
- ⚠️ No centralized mock server for reuse

**Alternative Approaches**:

**Option 1**: MSW (Mock Service Worker) - TypeScript-based
```typescript
import { setupServer } from 'msw/node'
import { rest } from 'msw'

const server = setupServer(
  rest.get('https://api.hostaway.com/v1/listings', (req, res, ctx) => {
    const limit = req.url.searchParams.get('limit') || '50'
    return res(ctx.json({
      result: generateProperties(parseInt(limit)),
      count: 500
    }))
  })
)
```

**Option 2**: Centralized Mock Fixtures
```python
# tests/fixtures/hostaway_api.py
class MockHostawayAPI:
    """Centralized mock for Hostaway API responses"""

    def get_listings(self, limit=50, offset=0):
        return {
            "result": self._generate_properties(limit),
            "count": 500,
            "limit": limit,
            "offset": offset
        }
```

**Recommendation**: Create centralized mock fixtures in `tests/fixtures/` for overflow tests

---

## R006: MCP Server Testing Patterns

### Current MCP Tests

**File**: `tests/mcp/test_tool_discovery.py` (186 lines)

**Testing Approach**:
```python
@pytest.mark.asyncio
async def test_list_tools():
    """Test MCP server tool discovery"""
    # Tests that tools are properly registered
    # Validates tool schemas and descriptions
```

**Challenges for Overflow Testing**:
1. **stdio Communication**: MCP server uses stdio, not HTTP
2. **Server Lifecycle**: Need to start/stop server per test
3. **Tool Invocation**: Must simulate MCP client calling tools
4. **Response Validation**: Check both schema AND size

**Proposed Approach**:

**Option 1**: Mock MCP Server Responses
```python
class MockMCPServer:
    """Mock MCP server for testing without stdio"""

    async def call_tool(self, tool_name, arguments):
        # Directly call internal handlers
        handler = get_tool_handler(tool_name)
        result = await handler(arguments)
        return result
```

**Option 2**: Real MCP Client via stdio
```python
import subprocess
import json

class MCPTestClient:
    """Real MCP client for integration testing"""

    def __init__(self):
        self.process = subprocess.Popen(
            ['python', '-m', 'src.mcp.server'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    async def call_tool(self, tool_name, arguments):
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        }
        self.process.stdin.write(json.dumps(request).encode())
        response = json.loads(self.process.stdout.readline())
        return response
```

**Recommendation**: Use Option 1 (mock) for unit tests, Option 2 (real) for integration tests

---

## R007: Error Response Testing

### Current Error Handling

**No Standardized Error Format Found**

**Existing Patterns**:
```python
# In various route handlers
try:
    result = await hostaway_client.get(endpoint)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        # Rate limit handling
        return {"error": "rate_limit", "retryAfter": ...}
    elif e.response.status_code == 500:
        # Server error
        return {"error": "server_error", "message": ...}
```

**Problem**: No guarantee error responses are compact

**Example of Oversized Error** (from spec):
```html
<!-- 500 error from Hostaway API -->
<!DOCTYPE html>
<html>
<head><title>500 Internal Server Error</title></head>
<body>
<h1>500 Internal Server Error</h1>
<pre>
... 10-50KB of stack trace ...
</pre>
</body>
</html>
```

**Desired Error Format**:
```json
{
  "error": {
    "code": "internal_server_error",
    "message": "Failed to fetch listings",
    "correlationId": "abc123xyz789",
    "timestamp": "2025-10-16T13:00:00Z"
  }
}
```

**Requirements**:
- **Size**: <2KB per error
- **No HTML**: Only JSON responses
- **Correlation ID**: For debugging
- **Actionable**: Clear next steps for client

**Test Strategy**:
1. Mock 500/429 errors with large HTML bodies
2. Validate transformed responses are compact JSON
3. Check all required fields present
4. Measure token count of error responses

---

## R008: Token Cap Configuration

### Current Environment Variables

**Existing Config** (`src/mcp/config.py`):
```python
class HostawayConfig(BaseSettings):
    HOSTAWAY_ACCOUNT_ID: str
    HOSTAWAY_SECRET_KEY: str
    HOSTAWAY_API_BASE_URL: str = "https://api.hostaway.com/v1"
    # ... other configs
```

**Missing**:
- `MCP_OUTPUT_TOKEN_THRESHOLD` (soft cap for preview)
- `MCP_HARD_OUTPUT_TOKEN_CAP` (absolute maximum)
- `MCP_DEFAULT_PAGE_SIZE` (default pagination limit)

**Proposed Configuration**:
```python
class MCPConfig(BaseSettings):
    # Existing Hostaway config...

    # Token management
    MCP_OUTPUT_TOKEN_THRESHOLD: int = 50000  # Soft cap (triggers preview)
    MCP_HARD_OUTPUT_TOKEN_CAP: int = 100000  # Hard cap (triggers truncation)

    # Pagination defaults
    MCP_DEFAULT_PAGE_SIZE: int = 50
    MCP_MAX_PAGE_SIZE: int = 200

    # Summarization
    MCP_ENABLE_AUTO_SUMMARIZATION: bool = True
    MCP_PREVIEW_FIELD_LIMIT: int = 10  # Max fields in preview
```

**Test Configuration Override**:
```python
@pytest.fixture
def small_token_caps(monkeypatch):
    """Override caps for testing overflow scenarios"""
    monkeypatch.setenv("MCP_OUTPUT_TOKEN_THRESHOLD", "1000")
    monkeypatch.setenv("MCP_HARD_OUTPUT_TOKEN_CAP", "5000")
    monkeypatch.setenv("MCP_DEFAULT_PAGE_SIZE", "10")
```

---

## R009: Test Data Fixtures

### Fixture Requirements

**Need Fixtures At Multiple Scales**:

1. **Small** (for happy path tests)
   - 10 properties, 10 bookings
   - Fits well under threshold
   - Fast to generate

2. **Medium** (for pagination tests)
   - 100 properties, 100 bookings
   - Requires pagination
   - Tests cursor navigation

3. **Large** (for overflow tests)
   - 1000+ properties
   - Exceeds soft threshold
   - Forces preview mode

**Proposed Structure**:
```
tests/fixtures/
├── properties/
│   ├── small-set.json (10 items, ~5KB)
│   ├── medium-set.json (100 items, ~50KB)
│   └── large-set.json (1000 items, ~500KB)
├── bookings/
│   ├── minimal.json (1 booking, core fields only)
│   ├── detailed.json (1 booking, all fields)
│   └── collection.json (50 bookings)
├── errors/
│   ├── 500-html.html (large HTML error body)
│   ├── 500-compact.json (desired compact format)
│   ├── 429-rate-limit.json (with retryAfter)
│   └── 400-validation.json (with validation details)
└── generators/
    ├── __init__.py
    ├── properties.py (generateProperties function)
    ├── bookings.py (generateBookings function)
    └── errors.py (generateError function)
```

**Generator Example**:
```python
# tests/fixtures/generators/properties.py
def generate_properties(count: int) -> list[dict]:
    """Generate realistic property data"""
    return [
        {
            "id": i,
            "name": f"Property {i}",
            "address": f"{i} Main Street",
            "city": random.choice(CITIES),
            "capacity": random.randint(2, 12),
            "basePrice": random.uniform(50, 500),
            # ... realistic data
        }
        for i in range(count)
    ]
```

---

## R010: CI Integration Patterns

### Existing CI Workflows

**File**: `.github/workflows/ci.yml` (excerpt):
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest --cov
```

**Current Test Execution**:
- Runs on every PR and push
- Python 3.12 only
- Coverage enforced (80%)
- No timeout limits

**Proposed Enhancements for Overflow Tests**:

```yaml
jobs:
  overflow-safety-tests:
    name: Overflow Safety Tests
    runs-on: ubuntu-latest
    timeout-minutes: 10  # 5 min target + buffer

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run overflow safety tests
        run: |
          pytest tests/overflow-safety/ \
            --cov=src \
            --cov-fail-under=95 \
            -v \
            --tb=short
        env:
          MCP_OUTPUT_TOKEN_THRESHOLD: "1000"  # Tiny caps for testing
          MCP_HARD_OUTPUT_TOKEN_CAP: "5000"

      - name: Check for flakes
        if: failure()
        run: |
          # Re-run failed tests to check for flakes
          pytest tests/overflow-safety/ --lf --count=5
```

**Performance Monitoring**:
```yaml
- name: Check test duration
  run: |
    pytest tests/overflow-safety/ \
      --durations=10 \
      --tb=no
```

---

## R011: Comparable Systems Analysis

### Similar Pagination Testing (Research)

**LangChain Document Loaders**:
- Tests pagination with various document sources
- Validates chunk sizes don't exceed token limits
- Uses tiktoken for accurate token counting

**OpenAI API Client Libraries**:
- Test automatic chunking of large inputs
- Validate streaming responses stay within limits
- Mock API responses at various sizes

**Anthropic SDK**:
- Tests context window management
- Validates message truncation strategies
- Checks token counting accuracy

**Key Patterns Identified**:

1. **Tiered Testing Approach**:
   - Unit tests: Fast, mocked, tiny data
   - Integration tests: Slower, larger data, real pagination
   - E2E tests: Full stack, realistic payloads

2. **Token Budget Validation**:
   - Always check estimated vs actual (when possible)
   - Test at boundaries: threshold-1, threshold, threshold+1
   - Validate truncation doesn't break JSON

3. **Fixture Management**:
   - Generate fixtures programmatically
   - Cache generated fixtures for speed
   - Version fixtures to detect schema drift

4. **Error Injection**:
   - Simulate oversized responses
   - Test partial failures (some pages succeed, some fail)
   - Validate retry/recovery mechanisms

---

## R012: Performance Benchmarking

### Current Performance Tests

**File**: `tests/performance/` (exists but limited coverage)

**No Existing Overflow-Specific Benchmarks**

**Proposed Benchmarks**:

```python
import pytest
import time

class TestOverflowPerformance:
    """Performance tests for overflow safety"""

    @pytest.mark.performance
    def test_pagination_performance_100_pages(self):
        """Pagination with 100 pages should complete in <2s"""
        start = time.time()

        # Simulate paginating through 100 pages
        for i in range(100):
            cursor = create_cursor(offset=i*50)
            page = get_page(cursor)
            assert len(page.items) <= 50

        duration = time.time() - start
        assert duration < 2.0, f"Took {duration}s, expected <2s"

    @pytest.mark.performance
    def test_token_estimation_performance_large_payload(self):
        """Token estimation on 500KB payload should be <50ms"""
        large_response = generate_properties(1000)  # ~500KB

        start = time.time()
        tokens = estimate_tokens_from_list(large_response)
        duration = (time.time() - start) * 1000  # Convert to ms

        assert duration < 50, f"Took {duration}ms, expected <50ms"

    @pytest.mark.performance
    def test_preview_generation_performance(self):
        """Preview generation should be <100ms"""
        large_booking = generate_large_booking()

        start = time.time()
        preview = summarization_service.summarize_object(
            large_booking,
            obj_type="booking",
            endpoint="/api/v1/bookings/{id}"
        )
        duration = (time.time() - start) * 1000

        assert duration < 100, f"Took {duration}ms, expected <100ms"
```

**CI Performance Tracking**:
- Store benchmark results in GitHub artifacts
- Compare against baseline (detect regressions)
- Fail CI if performance degrades >20%

---

## R013: Open Questions & Unknowns

### Questions Requiring Decisions

**Q1: Test Framework Language**
- **Option A**: Python (pytest) - Matches existing infrastructure
  - ✅ Consistent with current stack
  - ✅ Direct access to services
  - ❌ No native stdio mocking

- **Option B**: TypeScript (Vitest) - Better for MCP stdio testing
  - ✅ Native stdio handling
  - ✅ MSW for HTTP mocking
  - ❌ Additional stack to maintain

**Recommendation**: Python for unit tests, consider TypeScript for E2E

**Q2: Live vs Mock Testing**
- **Live API Tests**: Expensive, slow, rate-limited
- **Mock API Tests**: Fast, deterministic, but may miss real issues

**Recommendation**: Mock by default, live tests nightly

**Q3: Token Estimation Accuracy**
- **Current**: ±10% tolerance
- **Question**: Is this acceptable for production?

**Recommendation**: Validate against real Claude API in E2E tests

**Q4: Cursor Storage**
- **Current**: In-memory (lost on restart)
- **Question**: Need persistent storage for tests?

**Recommendation**: In-memory fine for tests, document limitation

**Q5: Error Response Size Threshold**
- **Proposed**: <2KB per error
- **Question**: Is this sufficient for debugging?

**Recommendation**: Yes, with correlation IDs for detailed logs

---

## Summary & Recommendations

### Key Findings

**Strengths**:
1. ✅ **Token Estimation**: Production-ready, well-tested, performant
2. ✅ **Pagination**: Complete implementation with cursor-based navigation
3. ✅ **Summarization**: Field projection infrastructure in place
4. ✅ **Test Infrastructure**: Mature pytest setup with async support
5. ✅ **Coverage**: 80% minimum enforced, comprehensive test organization

**Gaps**:
1. ⚠️ **No Overflow Tests**: No tests specifically for token cap enforcement
2. ⚠️ **Error Hygiene**: No validation of error response sizes
3. ⚠️ **MCP stdio Testing**: Limited patterns for testing stdio communication
4. ⚠️ **Fixture Library**: No centralized mock data generators
5. ⚠️ **Performance Baselines**: No overflow-specific performance benchmarks

### Implementation Strategy

**Phase 1: Foundation** (Week 1)
- Create `tests/overflow-safety/` directory structure
- Build centralized fixture generators
- Implement mock MCP server wrapper
- Add token cap configuration variables

**Phase 2: Core Tests** (Week 2)
- Pagination validation tests (all endpoints)
- Token threshold enforcement tests
- Error hygiene validation tests
- Preview mode activation tests

**Phase 3: Integration** (Week 3)
- End-to-end overflow scenarios
- Performance benchmarks
- Live API integration tests (optional)
- Flake detection and mitigation

**Phase 4: CI & Docs** (Week 4)
- GitHub Actions workflow
- Test documentation and runbook
- Failure troubleshooting guide
- Metrics dashboard (optional)

### Technology Decisions

**Test Framework**: Python (pytest) + AsyncMock
**HTTP Mocking**: respx + centralized fixtures
**MCP Testing**: Mock server wrapper (not real stdio)
**Fixtures**: Programmatic generators in `tests/fixtures/`
**CI Integration**: GitHub Actions with timeout enforcement

### Success Metrics

**Coverage**:
- ✅ 100% of high-volume endpoints tested
- ✅ All pagination paths exercised
- ✅ All error scenarios covered

**Performance**:
- ✅ Test suite <5 minutes in CI
- ✅ Individual tests <10 seconds
- ✅ Flake rate <1%

**Quality**:
- ✅ 0 hard cap violations
- ✅ ≥95% of endpoints return paginated/summarized results
- ✅ All error responses <2KB

---

## References

### Internal Documentation
- [Token Estimator](../../src/utils/token_estimator.py)
- [Pagination Service](../../src/services/pagination_service.py)
- [Summarization Service](../../src/services/summarization_service.py)
- [Existing Integration Tests](../../tests/integration/)

### External Resources
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [respx HTTP Mocking](https://lundberg.github.io/respx/)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Claude Token Limits](https://docs.anthropic.com/claude/docs/models-overview)

### Similar Systems
- [LangChain Document Loader Tests](https://github.com/langchain-ai/langchain/tree/master/libs/langchain/tests/unit_tests/document_loaders)
- [OpenAI Python SDK Tests](https://github.com/openai/openai-python/tree/main/tests)
- [Anthropic SDK Tests](https://github.com/anthropics/anthropic-sdk-python/tree/main/tests)

---

**Research Complete**: 2025-10-16
**Next Steps**: Create `plan.md` with detailed implementation tasks
