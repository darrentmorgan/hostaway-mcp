# Python HTTP Mocking Implementation

## Current Status: Partial Implementation

### What Was Built

1. **Mock Infrastructure** (`src/testing/hostaway_mocks.py`)
   - Deterministic mock data generators
   - respx-based HTTP mocking setup
   - Dynamic pagination logic in mock handlers
   - Test mode environment variable detection

2. **Integration Points**
   - FastAPI lifespan detects `HOSTAWAY_TEST_MODE=true`
   - Test client passes environment variable
   - Mock setup is called on app startup

### Technical Challenge

**respx Context Manager Lifecycle**: The core issue is that `respx.mock()` returns a context manager that needs to remain active for the duration of the test. When called in FastAPI's lifespan, the context exits immediately after `setup_hostaway_mocks()` returns, deactivating the mocks.

### Working Solutions (Choose One)

#### Option A: Dependency Injection (Recommended)

Replace the real `HostawayClient` with a mock version during tests:

```python
# src/testing/mock_client.py
class MockHostawayClient(HostawayClient):
    """Mock Hostaway client with deterministic responses."""

    async def get_listings(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Return mock listings."""
        listings = generate_mock_listings(min(limit, 100 - offset), offset)
        return listings

    async def search_bookings(self, limit: int = 100, offset: int = 0, **kwargs) -> list[dict]:
        """Return mock bookings."""
        bookings = generate_mock_bookings(min(limit, 100 - offset), offset)
        return bookings

# In src/api/main.py lifespan
if is_test_mode():
    from src.testing.mock_client import MockHostawayClient
    hostaway_client = MockHostawayClient(config, token_manager, rate_limiter)
else:
    hostaway_client = HostawayClient(config, token_manager, rate_limiter)
```

#### Option B: pytest-httpx

Use pytest fixtures that activate for test duration:

```python
# tests/conftest.py
import pytest
from pytest_httpx import HTTPXMock

@pytest.fixture
def mock_hostaway_api(httpx_mock: HTTPXMock):
    """Mock Hostaway API responses."""

    def listings_callback(request):
        params = dict(request.url.params)
        limit = int(params.get('limit', 50))
        offset = int(params.get('offset', 0))

        listings = generate_mock_listings(limit, offset)
        return {
            "status": "success",
            "result": listings,
            "count": len(listings)
        }

    httpx_mock.add_callback(listings_callback, url__regex=r".*/listings")
    return httpx_mock
```

#### Option C: respx with Persistent Router

Keep the respx router alive for application lifetime:

```python
# src/testing/hostaway_mocks.py
_mock_router: MockRouter | None = None

def setup_hostaway_mocks() -> MockRouter:
    global _mock_router

    if _mock_router is not None:
        return _mock_router

    # Create router that stays active
    _mock_router = respx.mock(assert_all_called=False)
    _mock_router.__enter__()  # Manually enter context

    # Setup routes...

    return _mock_router

def teardown_hostaway_mocks():
    global _mock_router
    if _mock_router is not None:
        _mock_router.__exit__(None, None, None)
        _mock_router = None

# In FastAPI lifespan
if is_test_mode():
    setup_hostaway_mocks()

yield

if is_test_mode():
    teardown_hostaway_mocks()
```

### Recommended Next Steps

1. **Implement Option A** (Dependency Injection)
   - Cleanest separation of concerns
   - No context manager complexity
   - Easy to understand and maintain
   - Works with any test framework

2. **Create MockHostaway Client class**
   - Inherit from `HostawayClient`
   - Override HTTP methods with mock data
   - Use the same data generators already built

3. **Update FastAPI lifespan**
   - Conditional client initialization based on test mode
   - No respx dependency needed

4. **Run tests**
   - Should achieve 10/10 passing
   - Deterministic, fast, reliable

### Code Example

```python
# Complete working example for src/testing/mock_client.py

from typing import Any
from src.services.hostaway_client import HostawayClient
from src.testing.hostaway_mocks import generate_mock_listings, generate_mock_bookings

class MockHostawayClient(HostawayClient):
    """Mock implementation of HostawayClient for testing."""

    TOTAL_LISTINGS = 100
    TOTAL_BOOKINGS = 100

    async def get_listings(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Return deterministic mock listings."""
        actual_limit = min(limit, self.TOTAL_LISTINGS - offset)
        return generate_mock_listings(actual_limit, offset)

    async def search_bookings(
        self,
        listing_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Return deterministic mock bookings."""
        actual_limit = min(limit, self.TOTAL_BOOKINGS - offset)
        return generate_mock_bookings(actual_limit, offset)
```

### Timeline

- **Current**: 4/10 tests passing with real API
- **After Option A**: Expected 10/10 passing (30 min implementation)
- **Total Time Invested**: ~8 hours (test infrastructure + mocking attempt)
- **ROI**: Complete, maintainable test suite for pagination contracts
