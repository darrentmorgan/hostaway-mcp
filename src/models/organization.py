"""Multi-tenant organization models for MCP server.

This module provides Pydantic models for multi-tenant architecture, including
organizations, members, API keys, credentials, subscriptions, usage metrics,
and audit logging.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OrganizationRole(str, Enum):
    """Role enumeration for organization members."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class SubscriptionStatus(str, Enum):
    """Status enumeration for Stripe subscriptions."""

    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"


class Organization(BaseModel):
    """Organization entity representing a tenant (property management company).

    Each organization is a separate tenant with isolated data, its own
    Stripe customer account, and multiple members.
    """

    id: int = Field(
        ...,
        description="Unique organization identifier",
        gt=0,
    )

    name: str = Field(
        ...,
        description="Organization name",
        min_length=1,
        max_length=255,
    )

    owner_user_id: str = Field(
        ...,
        description="UUID of the owner from auth.users",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    )

    stripe_customer_id: str | None = Field(
        None,
        description="Stripe customer ID for billing (format: cus_xxx)",
        pattern=r"^cus_[a-zA-Z0-9]{14,}$",
    )

    created_at: datetime = Field(
        ...,
        description="Timestamp when organization was created (UTC)",
    )

    updated_at: datetime = Field(
        ...,
        description="Timestamp when organization was last updated (UTC)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Acme Property Management",
                "owner_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "stripe_customer_id": "cus_QwvKJnG3c5kHPa",
                "created_at": "2025-10-13T10:30:00Z",
                "updated_at": "2025-10-13T10:30:00Z",
            }
        }
    }


class OrganizationMember(BaseModel):
    """User-organization membership relationship.

    Defines the many-to-many relationship between users and organizations,
    allowing users to belong to multiple organizations with different roles.
    """

    organization_id: int = Field(
        ...,
        description="Organization identifier",
        gt=0,
    )

    user_id: str = Field(
        ...,
        description="UUID of the user from auth.users",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    )

    role: OrganizationRole = Field(
        ...,
        description="User's role within the organization",
    )

    joined_at: datetime = Field(
        ...,
        description="Timestamp when user joined the organization (UTC)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "organization_id": 1,
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "owner",
                "joined_at": "2025-10-13T10:30:00Z",
            }
        }
    }


class APIKey(BaseModel):
    """MCP API key for authentication (hash only, never store actual key).

    API keys are used by AI agents (like Claude Desktop) to authenticate
    with the MCP server. Only the SHA-256 hash is stored in the database.
    """

    id: int = Field(
        ...,
        description="Unique API key identifier",
        gt=0,
    )

    organization_id: int = Field(
        ...,
        description="Organization that owns this API key",
        gt=0,
    )

    key_hash: str = Field(
        ...,
        description="SHA-256 hash of the API key (64 hex characters)",
        min_length=64,
        max_length=64,
        pattern=r"^[a-f0-9]{64}$",
    )

    created_by_user_id: str = Field(
        ...,
        description="UUID of the user who created this API key",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    )

    created_at: datetime = Field(
        ...,
        description="Timestamp when API key was created (UTC)",
    )

    last_used_at: datetime | None = Field(
        None,
        description="Timestamp when API key was last used (UTC)",
    )

    is_active: bool = Field(
        True,
        description="Whether the API key is currently active",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "organization_id": 1,
                "key_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
                "created_by_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-10-13T10:30:00Z",
                "last_used_at": "2025-10-13T11:30:00Z",
                "is_active": True,
            }
        }
    }


class HostawayCredentials(BaseModel):
    """Encrypted Hostaway API credentials for an organization.

    Stores Hostaway account credentials with encryption via Supabase Vault.
    Supports credential validation tracking and historical records.
    """

    id: int = Field(
        ...,
        description="Unique credential identifier",
        gt=0,
    )

    organization_id: int = Field(
        ...,
        description="Organization that owns these credentials",
        gt=0,
    )

    account_id: str = Field(
        ...,
        description="Hostaway account ID",
        min_length=1,
    )

    encrypted_secret_key: str = Field(
        ...,
        description="Encrypted Hostaway secret key (via pgsodium)",
        min_length=1,
    )

    credentials_valid: bool = Field(
        True,
        description="Whether credentials are currently valid (false if 401 received)",
    )

    last_validated_at: datetime | None = Field(
        None,
        description="Timestamp when credentials were last validated (UTC)",
    )

    created_at: datetime = Field(
        ...,
        description="Timestamp when credentials were created (UTC)",
    )

    updated_at: datetime = Field(
        ...,
        description="Timestamp when credentials were last updated (UTC)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "organization_id": 1,
                "account_id": "ACC_12345",
                "encrypted_secret_key": "encrypted_value_here",
                "credentials_valid": True,
                "last_validated_at": "2025-10-13T10:30:00Z",
                "created_at": "2025-10-13T10:30:00Z",
                "updated_at": "2025-10-13T10:30:00Z",
            }
        }
    }


class Subscription(BaseModel):
    """Stripe subscription for billing per organization.

    Tracks the subscription status, billing periods, and listing quantity
    for usage-based billing. Synchronized via Stripe webhooks.
    """

    id: int = Field(
        ...,
        description="Unique subscription identifier",
        gt=0,
    )

    organization_id: int = Field(
        ...,
        description="Organization that owns this subscription",
        gt=0,
    )

    stripe_subscription_id: str = Field(
        ...,
        description="Stripe subscription ID (format: sub_xxx)",
        pattern=r"^sub_[a-zA-Z0-9]{14,}$",
    )

    stripe_customer_id: str = Field(
        ...,
        description="Stripe customer ID (denormalized for webhook processing)",
        pattern=r"^cus_[a-zA-Z0-9]{14,}$",
    )

    current_quantity: int = Field(
        0,
        description="Current active listing count for billing",
        ge=0,
    )

    status: SubscriptionStatus = Field(
        ...,
        description="Current subscription status",
    )

    billing_period_start: datetime = Field(
        ...,
        description="Start of current billing period (UTC)",
    )

    billing_period_end: datetime = Field(
        ...,
        description="End of current billing period (UTC)",
    )

    created_at: datetime = Field(
        ...,
        description="Timestamp when subscription was created (UTC)",
    )

    updated_at: datetime = Field(
        ...,
        description="Timestamp when subscription was last updated (UTC)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "organization_id": 1,
                "stripe_subscription_id": "sub_1NzYwKJnG3c5kH",
                "stripe_customer_id": "cus_QwvKJnG3c5kHPa",
                "current_quantity": 25,
                "status": "active",
                "billing_period_start": "2025-10-01T00:00:00Z",
                "billing_period_end": "2025-11-01T00:00:00Z",
                "created_at": "2025-10-13T10:30:00Z",
                "updated_at": "2025-10-13T10:30:00Z",
            }
        }
    }


class UsageMetrics(BaseModel):
    """Monthly aggregated API usage statistics per organization.

    Tracks API request counts and unique tool usage for billing and
    analytics purposes. Updated asynchronously on each MCP tool invocation.
    """

    id: int = Field(
        ...,
        description="Unique metrics identifier",
        gt=0,
    )

    organization_id: int = Field(
        ...,
        description="Organization these metrics belong to",
        gt=0,
    )

    month_year: str = Field(
        ...,
        description="Month and year for this metrics period (format: YYYY-MM)",
        pattern=r"^\d{4}-\d{2}$",
    )

    total_api_requests: int = Field(
        0,
        description="Total API requests made in this period",
        ge=0,
    )

    unique_tools_used: list[str] = Field(
        default_factory=list,
        description="List of unique MCP tool names used",
    )

    listing_count_snapshot: int = Field(
        0,
        description="Snapshot of active listing count for this month",
        ge=0,
    )

    created_at: datetime = Field(
        ...,
        description="Timestamp when metrics record was created (UTC)",
    )

    updated_at: datetime = Field(
        ...,
        description="Timestamp when metrics were last updated (UTC)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "organization_id": 1,
                "month_year": "2025-10",
                "total_api_requests": 1250,
                "unique_tools_used": ["get_properties", "create_listing", "get_reservations"],
                "listing_count_snapshot": 25,
                "created_at": "2025-10-01T00:00:00Z",
                "updated_at": "2025-10-13T10:30:00Z",
            }
        }
    }


class AuditLog(BaseModel):
    """MCP tool invocation audit log for compliance and debugging.

    Records every MCP tool invocation with request parameters, response status,
    and error messages. Used for compliance, debugging, and usage analytics.
    """

    id: int = Field(
        ...,
        description="Unique audit log identifier",
        gt=0,
    )

    organization_id: int = Field(
        ...,
        description="Organization that made this request",
        gt=0,
    )

    user_id: str | None = Field(
        None,
        description="UUID of user if user-initiated (null for API key usage)",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    )

    tool_name: str = Field(
        ...,
        description="Name of the MCP tool invoked",
        min_length=1,
    )

    request_params: dict | None = Field(
        None,
        description="Tool invocation parameters (JSONB)",
    )

    response_status: int = Field(
        ...,
        description="HTTP response status code",
        ge=100,
        lt=600,
    )

    error_message: str | None = Field(
        None,
        description="Error message if response_status >= 400",
    )

    created_at: datetime = Field(
        ...,
        description="Timestamp when the tool was invoked (UTC)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "organization_id": 1,
                "user_id": None,
                "tool_name": "get_properties",
                "request_params": {"limit": 10, "offset": 0},
                "response_status": 200,
                "error_message": None,
                "created_at": "2025-10-13T10:30:00Z",
            }
        }
    }
