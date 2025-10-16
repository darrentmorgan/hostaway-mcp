# Phase 9: Testing & Quality Assurance Plan

**Status**: Ready for implementation
**Tasks**: T071-T082 (12 tests)
**Test Framework**: pytest, pytest-asyncio, httpx (TestClient)

---

## Overview

This document outlines the comprehensive testing strategy for the multi-tenant Hostaway MCP platform. All tests should be implemented using pytest with async support.

### Test Coverage Goals

- **Backend Unit Tests**: 80%+ coverage for services and dependencies
- **Database Tests**: 100% coverage for RLS policies and RPC functions
- **Integration Tests**: All critical user flows
- **E2E Tests**: Complete onboarding, payment, and sync workflows

---

## Unit Tests (T071-T074)

### T071: Credential Service Tests

**File**: `tests/unit/test_credential_service.py`

**Test Cases**:
```python
import pytest
from unittest.mock import AsyncMock, patch
from src.services.credential_service import check_credential_validity

@pytest.mark.asyncio
async def test_check_credential_validity_success():
    """Test successful credential validation"""
    # Mock httpx response with 200 status
    # Assert valid=True, validated_at is ISO timestamp

@pytest.mark.asyncio
async def test_check_credential_validity_invalid():
    """Test invalid credentials (401 response)"""
    # Mock httpx response with 401 status
    # Assert valid=False, error="Invalid or expired credentials"

@pytest.mark.asyncio
async def test_check_credential_validity_network_error():
    """Test network failure handling"""
    # Mock httpx raising ConnectionError
    # Assert valid=False, error contains exception message

@pytest.mark.asyncio
async def test_check_credential_validity_unexpected_status():
    """Test handling of unexpected HTTP status codes"""
    # Mock httpx response with 503 status
    # Assert valid=False, error contains status code
```

### T072: Stripe Service Tests

**File**: `tests/unit/test_stripe_service.py`

**Test Cases**:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.stripe_service import StripeService

@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    mock = MagicMock()
    mock.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{}]
    return mock

@pytest.mark.asyncio
async def test_create_customer_success(mock_supabase):
    """Test successful Stripe customer creation"""
    with patch('stripe.Customer.create') as mock_create:
        mock_create.return_value = MagicMock(id='cus_test123')
        service = StripeService(supabase=mock_supabase)
        customer_id = await service.create_customer(
            organization_id='org-123',
            email='test@example.com',
            name='Test Org'
        )
        assert customer_id == 'cus_test123'
        # Verify Supabase was updated with customer ID

@pytest.mark.asyncio
async def test_create_customer_stripe_error(mock_supabase):
    """Test Stripe API error handling"""
    with patch('stripe.Customer.create', side_effect=stripe.error.CardError('error', None, None)):
        service = StripeService(supabase=mock_supabase)
        with pytest.raises(CustomerCreationError):
            await service.create_customer('org-123', 'test@example.com')

@pytest.mark.asyncio
async def test_create_subscription_success(mock_supabase):
    """Test successful subscription creation"""
    # Mock stripe.Subscription.create with trial period
    # Verify subscription_id, status, client_secret returned

@pytest.mark.asyncio
async def test_create_billing_portal_session(mock_supabase):
    """Test billing portal session creation"""
    # Mock stripe.billing_portal.Session.create
    # Verify portal URL returned

@pytest.mark.asyncio
async def test_cancel_subscription_at_period_end(mock_supabase):
    """Test subscription cancellation at period end"""
    # Mock stripe.Subscription.modify with cancel_at_period_end=True
    # Verify cancellation details returned
```

### T073: Dependencies Tests

**File**: `tests/unit/test_dependencies.py`

**Test Cases**:
```python
import pytest
from unittest.mock import MagicMock
from src.api.dependencies import get_organization_context, hash_api_key, AuthenticationError, CredentialError

def test_hash_api_key():
    """Test API key hashing with SHA-256"""
    key = "api_test_key_123"
    hashed = hash_api_key(key)
    assert len(hashed) == 64  # SHA-256 produces 64-char hex
    assert hashed == hash_api_key(key)  # Deterministic

@pytest.mark.asyncio
async def test_get_organization_context_success():
    """Test successful organization context retrieval"""
    # Mock Supabase responses for api_keys, hostaway_credentials, RPC decrypt
    # Verify OrganizationContext returned with correct organization_id and credentials

@pytest.mark.asyncio
async def test_get_organization_context_invalid_api_key():
    """Test invalid API key handling"""
    # Mock Supabase returning no data for api_keys query
    # Assert AuthenticationError raised

@pytest.mark.asyncio
async def test_get_organization_context_inactive_api_key():
    """Test inactive API key rejection"""
    # Mock Supabase returning is_active=False
    # Assert AuthenticationError raised

@pytest.mark.asyncio
async def test_get_organization_context_missing_credentials():
    """Test missing Hostaway credentials"""
    # Mock api_keys success, but hostaway_credentials returns no data
    # Assert CredentialError raised

@pytest.mark.asyncio
async def test_get_organization_context_invalid_credentials():
    """Test invalid Hostaway credentials (credentials_valid=false)"""
    # Mock hostaway_credentials with credentials_valid=False
    # Assert CredentialError with re-authentication message

@pytest.mark.asyncio
async def test_get_organization_context_decryption_failure():
    """Test credential decryption failure"""
    # Mock RPC decrypt_hostaway_credential returning no data
    # Assert CredentialError raised

@pytest.mark.asyncio
async def test_get_organization_context_updates_last_used():
    """Test API key last_used_at timestamp update"""
    # Mock successful flow, verify update_api_key_last_used RPC called
```

### T074: Usage Tracking Middleware Tests

**File**: `tests/unit/test_usage_tracking_middleware.py`

**Test Cases**:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request
from src.api.middleware.usage_tracking import UsageTrackingMiddleware

@pytest.mark.asyncio
async def test_usage_tracking_middleware_tracks_api_requests():
    """Test middleware tracks /api/* requests"""
    # Mock Request with url.path=/api/listings
    # Mock request.state.organization_id
    # Verify increment_usage_metrics RPC called with correct params

@pytest.mark.asyncio
async def test_usage_tracking_middleware_skips_non_api_routes():
    """Test middleware skips non-/api routes"""
    # Mock Request with url.path=/health
    # Verify RPC not called

@pytest.mark.asyncio
async def test_usage_tracking_middleware_handles_missing_org_id():
    """Test middleware handles missing organization_id gracefully"""
    # Mock Request without organization_id in state
    # Verify RPC not called, request continues

@pytest.mark.asyncio
async def test_usage_tracking_middleware_handles_rpc_failure():
    """Test middleware doesn't fail request on tracking error"""
    # Mock RPC raising exception
    # Verify request still completes successfully

def test_extract_tool_name():
    """Test tool name extraction from API paths"""
    middleware = UsageTrackingMiddleware(app=None)
    assert middleware._extract_tool_name("/api/listings") == "listings"
    assert middleware._extract_tool_name("/api/bookings/123") == "bookings"
    assert middleware._extract_tool_name("/api/analytics/financial") == "analytics"
```

---

## Database Tests (T075-T076)

### T075: RLS Policy Tests

**File**: `tests/database/test_rls_policies.py`

**Test Cases**:
```python
import pytest
from supabase import create_client
from src.config import settings

@pytest.fixture
def supabase_user_a():
    """Supabase client authenticated as User A"""
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    # Sign in as test user A
    return client

@pytest.fixture
def supabase_user_b():
    """Supabase client authenticated as User B"""
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    # Sign in as test user B
    return client

def test_rls_organizations_isolation(supabase_user_a, supabase_user_b):
    """Test User A cannot access User B's organization"""
    # Create org for User A
    # Try to query it as User B
    # Assert access denied or empty results

def test_rls_hostaway_credentials_isolation(supabase_user_a, supabase_user_b):
    """Test User A cannot see User B's Hostaway credentials"""
    # Insert credentials for User A's org
    # Query as User B
    # Assert empty results

def test_rls_api_keys_isolation(supabase_user_a, supabase_user_b):
    """Test User A cannot see User B's API keys"""
    # Create API key for User A's org
    # Query as User B
    # Assert empty results

def test_rls_usage_metrics_isolation(supabase_user_a, supabase_user_b):
    """Test User A cannot see User B's usage metrics"""
    # Insert usage metrics for User A's org
    # Query as User B
    # Assert empty results

def test_rls_subscriptions_isolation(supabase_user_a, supabase_user_b):
    """Test User A cannot access User B's subscription"""
    # Create subscription for User A's org
    # Query as User B
    # Assert access denied
```

### T076: RPC Function Tests

**File**: `tests/database/test_rpc_functions.py`

**Test Cases**:
```python
import pytest
from src.services.supabase_client import get_supabase_client

def test_rpc_increment_usage_metrics():
    """Test increment_usage_metrics RPC function"""
    supabase = get_supabase_client()
    org_id = "test-org-123"
    tool_name = "listings"

    # Call RPC multiple times
    for _ in range(3):
        result = supabase.rpc('increment_usage_metrics', {
            'p_organization_id': org_id,
            'p_tool_name': tool_name
        }).execute()

    # Verify total_api_requests incremented by 3
    # Verify unique_tools_used contains 'listings'
    # Verify month_year set correctly

def test_rpc_update_api_key_last_used():
    """Test update_api_key_last_used RPC function"""
    supabase = get_supabase_client()

    # Create test API key
    # Call RPC to update last_used_at
    # Verify timestamp updated

def test_rpc_decrypt_hostaway_credential():
    """Test decrypt_hostaway_credential RPC function"""
    supabase = get_supabase_client()

    # Encrypt a test secret using Vault
    # Call RPC to decrypt
    # Verify decrypted value matches original

def test_rpc_sync_stripe_subscription():
    """Test sync_stripe_subscription RPC function (if exists)"""
    # Test subscription sync between Stripe and database
    # Verify listing count updated from Stripe subscription quantity
```

---

## Integration Tests (T077-T079)

### T077: Multi-Tenant Isolation Test

**File**: `tests/integration/test_multi_tenant_isolation.py`

**Test Cases**:
```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_organization_a_cannot_access_organization_b_listings(client):
    """Test Org A API key cannot access Org B's listings"""
    # Create Org A with Hostaway account X
    # Create Org B with Hostaway account Y
    # Generate API key for Org A
    # Try to GET /api/listings with Org A key
    # Verify only Org A's listings returned (not Org B's)

def test_api_key_from_org_a_fails_for_org_b_resources(client):
    """Test API key scoping"""
    # Create API key for Org A
    # Create listing for Org B
    # Try to GET /api/listings/{org_b_listing_id} with Org A key
    # Assert 404 or 403

def test_financial_summary_scoped_to_organization(client):
    """Test financial analytics only include org's own data"""
    # Create bookings for Org A and Org B
    # GET /api/analytics/financial with Org A key
    # Verify only Org A bookings in summary

def test_usage_metrics_scoped_to_organization(client):
    """Test usage metrics isolation"""
    # Track API requests for Org A and Org B
    # Query usage_metrics with Org A context
    # Verify only Org A metrics returned
```

### T078: API Key Lifecycle Test

**File**: `tests/integration/test_api_key_lifecycle.py`

**Test Cases**:
```python
import pytest
from fastapi.testclient import TestClient

def test_api_key_creation_and_validation(client):
    """Test complete API key lifecycle"""
    # Create organization and user
    # Generate API key via dashboard endpoint
    # Verify key returned (starts with 'hwmc_')
    # Use key in X-API-Key header
    # Verify request succeeds

def test_api_key_hashing_for_security(client):
    """Test API keys are hashed in database"""
    # Create API key
    # Query api_keys table
    # Verify key_hash is SHA-256 hex (64 chars)
    # Verify original key not stored

def test_api_key_deactivation(client):
    """Test deactivating API key"""
    # Create and use API key
    # Deactivate key (set is_active=false)
    # Try to use deactivated key
    # Assert 401 Unauthorized

def test_api_key_last_used_timestamp(client):
    """Test last_used_at timestamp updates"""
    # Create API key
    # Make API request
    # Verify last_used_at updated
    # Wait 1 second, make another request
    # Verify timestamp updated again
```

### T079: Billing Flow Test

**File**: `tests/integration/test_billing_flow.py`

**Test Cases**:
```python
import pytest
from unittest.mock import patch

def test_stripe_customer_creation_on_signup(client):
    """Test Stripe customer created when organization signs up"""
    # Create organization
    # Verify stripe_customer_id set in organizations table
    # Verify customer exists in Stripe

def test_subscription_creation_flow(client):
    """Test subscription creation"""
    # Create organization with Stripe customer
    # Create subscription with 10 listings quantity
    # Verify subscriptions table updated
    # Verify current_quantity = 10

def test_subscription_quantity_update_on_listing_change(client):
    """Test subscription updates when listing count changes"""
    # Create subscription with 5 listings
    # User adds 3 more listings in Hostaway
    # Trigger sync (via webhook or cron)
    # Verify subscription quantity updated to 8
    # Verify Stripe subscription updated

def test_invoice_generation_on_billing_cycle(client):
    """Test invoice created at billing cycle"""
    # Mock Stripe webhook: invoice.paid
    # Verify invoice recorded in invoices table
    # Verify listing_count, amount, period captured
```

---

## E2E Tests (T080-T082)

### T080: Complete Onboarding Flow

**File**: `tests/e2e/test_onboarding_flow.py`

**Test Cases**:
```python
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_complete_user_onboarding():
    """Test full onboarding flow from signup to MCP usage"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Step 1: Sign up
        await page.goto('http://localhost:3000/signup')
        await page.fill('input[name="email"]', 'test@example.com')
        await page.fill('input[name="password"]', 'SecurePass123!')
        await page.click('button[type="submit"]')

        # Step 2: Verify email (mock or use test email service)
        # Click verification link

        # Step 3: Connect Hostaway account
        await page.goto('http://localhost:3000/settings')
        await page.fill('input[name="account_id"]', 'TEST_ACCOUNT')
        await page.fill('input[name="secret_key"]', 'TEST_SECRET')
        await page.click('button:has-text("Save Credentials")')
        await page.wait_for_selector('text=Connection successful')

        # Step 4: Start Stripe subscription
        await page.goto('http://localhost:3000/billing')
        await page.click('button:has-text("Start Subscription")')
        # Fill Stripe checkout form
        await page.frame_locator('iframe').fill('input[name="cardNumber"]', '4242424242424242')
        await page.frame_locator('iframe').fill('input[name="cardExpiry"]', '12/34')
        await page.frame_locator('iframe').fill('input[name="cardCvc"]', '123')
        await page.click('button:has-text("Subscribe")')
        await page.wait_for_selector('text=Subscription active')

        # Step 5: Generate API key
        await page.goto('http://localhost:3000/api-keys')
        await page.click('button:has-text("Create API Key")')
        await page.fill('input[name="name"]', 'Test Key')
        await page.click('button:has-text("Create")')
        api_key = await page.locator('code').text_content()

        # Step 6: Test MCP endpoint
        # Make HTTP request to /mcp with X-API-Key header
        # Verify tools returned

        await browser.close()
```

### T081: Payment Failure Handling

**File**: `tests/e2e/test_payment_failure.py`

**Test Cases**:
```python
@pytest.mark.asyncio
async def test_payment_failure_subscription_suspended():
    """Test subscription suspension on payment failure"""
    # Create organization with active subscription
    # Mock Stripe webhook: invoice.payment_failed
    # Verify subscription status = suspended
    # Verify API requests fail with 403 "Subscription suspended"
    # Verify dashboard shows payment failure notice

@pytest.mark.asyncio
async def test_payment_retry_reactivates_subscription():
    """Test subscription reactivation after successful payment retry"""
    # Suspend subscription due to payment failure
    # Mock Stripe webhook: invoice.paid
    # Verify subscription status = active
    # Verify API requests work again
```

### T082: Listing Sync Test

**File**: `tests/e2e/test_listing_sync.py`

**Test Cases**:
```python
@pytest.mark.asyncio
async def test_listing_count_syncs_to_stripe():
    """Test listing count syncs from Hostaway to Stripe"""
    # Create organization with 5 listings in Hostaway
    # Create Stripe subscription
    # Verify subscription quantity = 5
    # Add 3 listings in Hostaway
    # Trigger sync (webhook or cron)
    # Verify Stripe subscription quantity updated to 8
    # Verify next invoice prorated for additional listings

@pytest.mark.asyncio
async def test_listing_deletion_updates_subscription():
    """Test subscription quantity decreases when listings deleted"""
    # Create subscription with 10 listings
    # Delete 3 listings in Hostaway
    # Trigger sync
    # Verify Stripe subscription quantity = 7
    # Verify billing reflects reduced quantity
```

---

## Running Tests

### Setup

```bash
# Install test dependencies
uv pip install pytest pytest-asyncio pytest-cov httpx playwright

# Setup test database (use separate Supabase project or local)
export SUPABASE_URL=http://localhost:54321
export SUPABASE_ANON_KEY=test_anon_key
export SUPABASE_SERVICE_ROLE_KEY=test_service_key

# Run migrations on test database
supabase db reset --db-url postgresql://postgres:postgres@localhost:54321/postgres
```

### Run All Tests

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test categories
pytest tests/unit/                    # Unit tests only
pytest tests/database/                # Database tests only
pytest tests/integration/             # Integration tests only
pytest tests/e2e/                     # E2E tests only

# Run with verbose output
pytest -vv

# Run single test file
pytest tests/unit/test_dependencies.py

# Run single test function
pytest tests/unit/test_dependencies.py::test_hash_api_key
```

### Coverage Goals

- **Overall**: 80%+
- **Services**: 90%+
- **API Routes**: 85%+
- **Middleware**: 90%+
- **Dependencies**: 95%+

---

## CI/CD Integration

Add to `.github/workflows/test.yml`:

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: supabase/postgres
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 54321:5432

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -r requirements.txt
          uv pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        run: pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## Next Steps

1. Implement T071-T074 (Unit tests) - **Priority: High**
2. Implement T075-T076 (Database tests) - **Priority: High**
3. Implement T077-T079 (Integration tests) - **Priority: Medium**
4. Implement T080-T082 (E2E tests) - **Priority: Medium**
5. Setup CI/CD pipeline with automated testing
6. Generate coverage reports and identify gaps
7. Add performance benchmarks for critical paths

---

**Estimated Implementation Time**: 16-20 hours
**Dependencies**: Local Supabase running, Stripe test mode configured, Playwright installed
