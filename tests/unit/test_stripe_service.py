"""Unit tests for src/services/stripe_service.py"""

from unittest.mock import MagicMock, patch

import pytest
import stripe

from src.services.stripe_service import (
    BillingPortalError,
    CustomerCreationError,
    StripeService,
    StripeServiceError,
    SubscriptionError,
)


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client"""
    mock = MagicMock()
    mock.table.return_value = mock
    mock.select.return_value = mock
    mock.update.return_value = mock
    mock.eq.return_value = mock
    mock.single.return_value = mock
    mock.execute.return_value = MagicMock(data={"id": "test-org-id"})
    return mock


@pytest.fixture
def stripe_service(mock_supabase):
    """Create StripeService instance with mocked Supabase"""
    return StripeService(supabase=mock_supabase)


# === Test create_customer ===


@pytest.mark.asyncio
@patch("stripe.Customer.create")
async def test_create_customer_success(mock_stripe_create, stripe_service, mock_supabase):
    """Test successful customer creation"""
    # Arrange
    mock_customer = MagicMock()
    mock_customer.id = "cus_test123"
    mock_stripe_create.return_value = mock_customer

    mock_supabase.execute.return_value = MagicMock(data=[{"id": "org-123"}])

    # Act
    customer_id = await stripe_service.create_customer(
        organization_id="org-123",
        email="test@example.com",
        name="Test Org",
    )

    # Assert
    assert customer_id == "cus_test123"
    mock_stripe_create.assert_called_once_with(
        email="test@example.com",
        name="Test Org",
        metadata={"organization_id": "org-123"},
    )
    mock_supabase.table.assert_called_with("organizations")
    mock_supabase.update.assert_called_with({"stripe_customer_id": "cus_test123"})


@pytest.mark.asyncio
@patch("stripe.Customer.create")
async def test_create_customer_no_name_defaults_to_email(
    mock_stripe_create, stripe_service, mock_supabase
):
    """Test customer creation without name uses email as default"""
    # Arrange
    mock_customer = MagicMock()
    mock_customer.id = "cus_test456"
    mock_stripe_create.return_value = mock_customer

    mock_supabase.execute.return_value = MagicMock(data=[{"id": "org-456"}])

    # Act
    customer_id = await stripe_service.create_customer(
        organization_id="org-456",
        email="user@example.com",
    )

    # Assert
    assert customer_id == "cus_test456"
    mock_stripe_create.assert_called_once_with(
        email="user@example.com",
        name="user@example.com",  # Should default to email
        metadata={"organization_id": "org-456"},
    )


@pytest.mark.asyncio
@patch("stripe.Customer.create")
async def test_create_customer_with_metadata(mock_stripe_create, stripe_service, mock_supabase):
    """Test customer creation with custom metadata"""
    # Arrange
    mock_customer = MagicMock()
    mock_customer.id = "cus_test789"
    mock_stripe_create.return_value = mock_customer

    mock_supabase.execute.return_value = MagicMock(data=[{"id": "org-789"}])

    custom_metadata = {"plan": "enterprise", "referral": "partner"}

    # Act
    customer_id = await stripe_service.create_customer(
        organization_id="org-789",
        email="enterprise@example.com",
        metadata=custom_metadata,
    )

    # Assert
    assert customer_id == "cus_test789"
    # Metadata should include both custom and organization_id
    expected_metadata = {**custom_metadata, "organization_id": "org-789"}
    mock_stripe_create.assert_called_once_with(
        email="enterprise@example.com",
        name="enterprise@example.com",
        metadata=expected_metadata,
    )


@pytest.mark.asyncio
@patch("stripe.Customer.create")
async def test_create_customer_stripe_error(mock_stripe_create, stripe_service):
    """Test Stripe API error during customer creation"""
    # Arrange
    mock_stripe_create.side_effect = stripe.InvalidRequestError(
        message="Invalid email", param="email"
    )

    # Act & Assert
    with pytest.raises(CustomerCreationError) as exc_info:
        await stripe_service.create_customer(
            organization_id="org-error",
            email="invalid-email",
        )

    assert "Stripe API error" in str(exc_info.value)


@pytest.mark.asyncio
@patch("stripe.Customer.create")
async def test_create_customer_database_update_fails(
    mock_stripe_create, stripe_service, mock_supabase
):
    """Test database update failure after customer creation"""
    # Arrange
    mock_customer = MagicMock()
    mock_customer.id = "cus_orphan"
    mock_stripe_create.return_value = mock_customer

    # Simulate database update returning no data (failure)
    mock_supabase.execute.return_value = MagicMock(data=None)

    # Act & Assert
    with pytest.raises(CustomerCreationError) as exc_info:
        await stripe_service.create_customer(
            organization_id="org-fail",
            email="test@example.com",
        )

    assert "Failed to update organization" in str(exc_info.value)


# === Test create_subscription ===


@pytest.mark.asyncio
@patch("stripe.Subscription.create")
async def test_create_subscription_success(mock_subscription_create, stripe_service):
    """Test successful subscription creation"""
    # Arrange
    mock_payment_intent = MagicMock()
    mock_payment_intent.client_secret = "pi_secret_xyz"

    mock_invoice = MagicMock()
    mock_invoice.payment_intent = mock_payment_intent

    mock_subscription = MagicMock()
    mock_subscription.id = "sub_test123"
    mock_subscription.status = "active"
    mock_subscription.latest_invoice = mock_invoice

    mock_subscription_create.return_value = mock_subscription

    # Act
    result = await stripe_service.create_subscription(
        customer_id="cus_test123",
        price_id="price_test456",
        trial_days=14,
    )

    # Assert
    assert result["subscription_id"] == "sub_test123"
    assert result["status"] == "active"
    assert result["client_secret"] == "pi_secret_xyz"

    mock_subscription_create.assert_called_once_with(
        customer="cus_test123",
        items=[{"price": "price_test456"}],
        trial_period_days=14,
        metadata={},
        payment_behavior="default_incomplete",
        payment_settings={"save_default_payment_method": "on_subscription"},
        expand=["latest_invoice.payment_intent"],
    )


@pytest.mark.asyncio
@patch("stripe.Subscription.create")
async def test_create_subscription_with_metadata(mock_subscription_create, stripe_service):
    """Test subscription creation with custom metadata"""
    # Arrange
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_meta"
    mock_subscription.status = "trialing"
    mock_subscription.latest_invoice = None

    mock_subscription_create.return_value = mock_subscription

    custom_metadata = {"source": "dashboard", "campaign": "summer2024"}

    # Act
    result = await stripe_service.create_subscription(
        customer_id="cus_test",
        price_id="price_test",
        metadata=custom_metadata,
    )

    # Assert
    assert result["subscription_id"] == "sub_meta"
    assert result["client_secret"] is None  # No invoice
    mock_subscription_create.assert_called_once()
    call_kwargs = mock_subscription_create.call_args[1]
    assert call_kwargs["metadata"] == custom_metadata


@pytest.mark.asyncio
@patch("stripe.Subscription.create")
async def test_create_subscription_stripe_error(mock_subscription_create, stripe_service):
    """Test Stripe error during subscription creation"""
    # Arrange
    mock_subscription_create.side_effect = stripe.CardError(
        message="Your card was declined",
        param="card",
        code="card_declined",
    )

    # Act & Assert
    with pytest.raises(SubscriptionError) as exc_info:
        await stripe_service.create_subscription(
            customer_id="cus_declined",
            price_id="price_test",
        )

    assert "Stripe API error" in str(exc_info.value)


# === Test create_billing_portal_session ===


@pytest.mark.asyncio
@patch("stripe.billing_portal.Session.create")
async def test_create_billing_portal_session_success(mock_portal_create, stripe_service):
    """Test successful billing portal session creation"""
    # Arrange
    mock_session = MagicMock()
    mock_session.url = "https://billing.stripe.com/session/test"
    mock_portal_create.return_value = mock_session

    # Act
    portal_url = await stripe_service.create_billing_portal_session(
        customer_id="cus_portal",
        return_url="https://app.example.com/settings",
    )

    # Assert
    assert portal_url == "https://billing.stripe.com/session/test"
    mock_portal_create.assert_called_once_with(
        customer="cus_portal",
        return_url="https://app.example.com/settings",
    )


@pytest.mark.asyncio
@patch("stripe.billing_portal.Session.create")
async def test_create_billing_portal_session_stripe_error(mock_portal_create, stripe_service):
    """Test Stripe error during portal session creation"""
    # Arrange
    mock_portal_create.side_effect = stripe.InvalidRequestError(
        message="Customer not found", param="customer"
    )

    # Act & Assert
    with pytest.raises(BillingPortalError) as exc_info:
        await stripe_service.create_billing_portal_session(
            customer_id="cus_notfound",
            return_url="https://app.example.com",
        )

    assert "Stripe API error" in str(exc_info.value)


# === Test get_customer_by_organization ===


@pytest.mark.asyncio
async def test_get_customer_by_organization_success(stripe_service, mock_supabase):
    """Test successful retrieval of customer ID"""
    # Arrange
    mock_supabase.execute.return_value = MagicMock(data={"stripe_customer_id": "cus_org123"})

    # Act
    customer_id = await stripe_service.get_customer_by_organization(organization_id="org-123")

    # Assert
    assert customer_id == "cus_org123"
    mock_supabase.table.assert_called_with("organizations")
    mock_supabase.select.assert_called_with("stripe_customer_id")
    mock_supabase.eq.assert_called_with("id", "org-123")


@pytest.mark.asyncio
async def test_get_customer_by_organization_not_found(stripe_service, mock_supabase):
    """Test when organization has no Stripe customer"""
    # Arrange
    mock_supabase.execute.return_value = MagicMock(data=None)

    # Act
    customer_id = await stripe_service.get_customer_by_organization(
        organization_id="org-nocustomer"
    )

    # Assert
    assert customer_id is None


@pytest.mark.asyncio
async def test_get_customer_by_organization_database_error(stripe_service, mock_supabase):
    """Test database error during customer lookup"""
    # Arrange
    mock_supabase.execute.side_effect = Exception("Database connection failed")

    # Act & Assert
    with pytest.raises(StripeServiceError) as exc_info:
        await stripe_service.get_customer_by_organization(organization_id="org-error")

    assert "Unexpected error" in str(exc_info.value)


# === Test cancel_subscription ===


@pytest.mark.asyncio
@patch("stripe.Subscription.delete")
async def test_cancel_subscription_immediately(mock_subscription_delete, stripe_service):
    """Test immediate subscription cancellation"""
    # Arrange
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_cancel"
    mock_subscription.status = "canceled"
    mock_subscription.canceled_at = 1234567890

    mock_subscription_delete.return_value = mock_subscription

    # Act
    result = await stripe_service.cancel_subscription(
        subscription_id="sub_cancel",
        immediately=True,
    )

    # Assert
    assert result["subscription_id"] == "sub_cancel"
    assert result["status"] == "canceled"
    assert result["canceled_at"] == 1234567890
    mock_subscription_delete.assert_called_once_with("sub_cancel")


@pytest.mark.asyncio
@patch("stripe.Subscription.modify")
async def test_cancel_subscription_at_period_end(mock_subscription_modify, stripe_service):
    """Test subscription cancellation at period end"""
    # Arrange
    mock_subscription = MagicMock()
    mock_subscription.id = "sub_period"
    mock_subscription.status = "active"
    mock_subscription.canceled_at = None

    mock_subscription_modify.return_value = mock_subscription

    # Act
    result = await stripe_service.cancel_subscription(
        subscription_id="sub_period",
        immediately=False,
    )

    # Assert
    assert result["subscription_id"] == "sub_period"
    assert result["status"] == "active"
    assert result["canceled_at"] is None
    mock_subscription_modify.assert_called_once_with(
        "sub_period",
        cancel_at_period_end=True,
    )


@pytest.mark.asyncio
@patch("stripe.Subscription.delete")
async def test_cancel_subscription_stripe_error(mock_subscription_delete, stripe_service):
    """Test Stripe error during cancellation"""
    # Arrange
    mock_subscription_delete.side_effect = stripe.InvalidRequestError(
        message="Subscription not found", param="subscription"
    )

    # Act & Assert
    with pytest.raises(SubscriptionError) as exc_info:
        await stripe_service.cancel_subscription(
            subscription_id="sub_notfound",
            immediately=True,
        )

    assert "Stripe API error" in str(exc_info.value)


# === Test initialization ===


def test_stripe_service_initialization_with_client(mock_supabase):
    """Test StripeService initialization with provided client"""
    service = StripeService(supabase=mock_supabase)
    assert service.supabase is mock_supabase


@patch("src.services.stripe_service.get_supabase_client")
def test_stripe_service_initialization_without_client(mock_get_client):
    """Test StripeService initialization creates singleton client"""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    service = StripeService()

    assert service.supabase is mock_client
    mock_get_client.assert_called_once()
