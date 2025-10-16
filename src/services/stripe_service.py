"""Stripe billing service for subscription and payment management.

Provides Stripe customer creation, subscription management, and billing portal
integration for multi-tenant SaaS billing.
"""

import os
from typing import Any

import stripe

from src.services.supabase_client import SupabaseClientError, get_supabase_client
from supabase import Client

# Initialize Stripe with API key from environment
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")


class StripeServiceError(Exception):
    """Base exception for Stripe service errors."""


class CustomerCreationError(StripeServiceError):
    """Raised when Stripe customer creation fails."""


class SubscriptionError(StripeServiceError):
    """Raised when subscription operations fail."""


class BillingPortalError(StripeServiceError):
    """Raised when billing portal operations fail."""


class StripeService:
    """Service for managing Stripe billing operations.

    Handles customer creation, subscription management, and billing portal
    integration. Works with organizations table to store Stripe customer IDs.

    The billing flow:
    1. Create Stripe customer on organization signup
    2. Store stripe_customer_id in organizations table
    3. Create subscription when user selects a plan
    4. Use billing portal for customer self-service
    """

    def __init__(self, supabase: Client | None = None) -> None:
        """Initialize Stripe service.

        Args:
            supabase: Optional Supabase client (creates singleton if None)
        """
        self.supabase = supabase or get_supabase_client()

    async def create_customer(
        self,
        organization_id: str,
        email: str,
        name: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Create a Stripe customer and link to organization.

        Creates a new Stripe customer and stores the customer ID in the
        organizations table for future billing operations.

        Args:
            organization_id: UUID of the organization
            email: Customer email address
            name: Optional customer name (defaults to email)
            metadata: Optional metadata to attach to customer

        Returns:
            Stripe customer ID (starts with 'cus_')

        Raises:
            CustomerCreationError: If customer creation fails

        Example:
            >>> service = StripeService()
            >>> customer_id = await service.create_customer(
            ...     organization_id="uuid-123",
            ...     email="user@example.com",
            ...     name="Example Organization"
            ... )
            >>> print(customer_id)  # cus_abc123...
        """
        try:
            # Prepare metadata with organization context
            customer_metadata = metadata or {}
            customer_metadata["organization_id"] = organization_id

            # Create Stripe customer
            customer = stripe.Customer.create(
                email=email,
                name=name or email,
                metadata=customer_metadata,
            )

            # Update organization with Stripe customer ID
            update_response = (
                self.supabase.table("organizations")
                .update({"stripe_customer_id": customer.id})
                .eq("id", organization_id)
                .execute()
            )

            if not update_response.data:
                raise CustomerCreationError(
                    f"Failed to update organization {organization_id} with Stripe customer ID"
                )

            return customer.id

        except stripe.StripeError as e:
            raise CustomerCreationError(f"Stripe API error: {e!s}") from e
        except SupabaseClientError as e:
            raise CustomerCreationError(f"Database error: {e!s}") from e
        except Exception as e:
            raise CustomerCreationError(f"Unexpected error: {e!s}") from e

    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int = 14,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a subscription for a customer.

        Creates a new Stripe subscription with optional trial period.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID for the subscription
            trial_days: Number of trial days (default: 14)
            metadata: Optional metadata to attach to subscription

        Returns:
            Dictionary with subscription details

        Raises:
            SubscriptionError: If subscription creation fails

        Example:
            >>> service = StripeService()
            >>> subscription = await service.create_subscription(
            ...     customer_id="cus_abc123",
            ...     price_id="price_xyz789",
            ...     trial_days=14
            ... )
        """
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                trial_period_days=trial_days,
                metadata=metadata or {},
                payment_behavior="default_incomplete",
                payment_settings={"save_default_payment_method": "on_subscription"},
                expand=["latest_invoice.payment_intent"],
            )

            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret
                if subscription.latest_invoice
                else None,
            }

        except stripe.StripeError as e:
            raise SubscriptionError(f"Stripe API error: {e!s}") from e
        except Exception as e:
            raise SubscriptionError(f"Unexpected error: {e!s}") from e

    async def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> str:
        """Create a Stripe billing portal session.

        Generates a URL for customers to manage their subscription, payment
        methods, and view billing history.

        Args:
            customer_id: Stripe customer ID
            return_url: URL to redirect after portal session

        Returns:
            Billing portal session URL

        Raises:
            BillingPortalError: If portal session creation fails

        Example:
            >>> service = StripeService()
            >>> portal_url = await service.create_billing_portal_session(
            ...     customer_id="cus_abc123",
            ...     return_url="https://app.example.com/settings"
            ... )
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )

            return session.url

        except stripe.StripeError as e:
            raise BillingPortalError(f"Stripe API error: {e!s}") from e
        except Exception as e:
            raise BillingPortalError(f"Unexpected error: {e!s}") from e

    async def get_customer_by_organization(
        self,
        organization_id: str,
    ) -> str | None:
        """Get Stripe customer ID for an organization.

        Args:
            organization_id: UUID of the organization

        Returns:
            Stripe customer ID if exists, None otherwise

        Raises:
            StripeServiceError: If database query fails
        """
        try:
            response = (
                self.supabase.table("organizations")
                .select("stripe_customer_id")
                .eq("id", organization_id)
                .single()
                .execute()
            )

            if response.data:
                return response.data.get("stripe_customer_id")

            return None

        except SupabaseClientError as e:
            raise StripeServiceError(f"Database error: {e!s}") from e
        except Exception as e:
            raise StripeServiceError(f"Unexpected error: {e!s}") from e

    async def cancel_subscription(
        self,
        subscription_id: str,
        immediately: bool = False,
    ) -> dict[str, Any]:
        """Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            immediately: If True, cancel immediately. If False, cancel at period end.

        Returns:
            Dictionary with cancellation details

        Raises:
            SubscriptionError: If cancellation fails
        """
        try:
            if immediately:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )

            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "canceled_at": subscription.canceled_at,
            }

        except stripe.StripeError as e:
            raise SubscriptionError(f"Stripe API error: {e!s}") from e
        except Exception as e:
            raise SubscriptionError(f"Unexpected error: {e!s}") from e
