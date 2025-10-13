"""Supabase client singleton for multi-tenant database operations.

Provides a singleton Supabase client configured with service role key for
backend operations including RLS policy enforcement, Vault encryption, and
organization-scoped data access.
"""

import os
from functools import lru_cache
from typing import Any

from supabase import Client, create_client


class SupabaseClientError(Exception):
    """Base exception for Supabase client errors."""


class MissingEnvironmentVariableError(SupabaseClientError):
    """Raised when required environment variables are not set."""


@lru_cache
def get_supabase_client() -> Client:
    """Get singleton Supabase client with service role key.

    This client uses the service role key which bypasses RLS policies,
    allowing backend services to perform administrative operations.
    Use with caution - always enforce organization-scoping in application logic.

    Returns:
        Configured Supabase client instance

    Raises:
        MissingEnvironmentVariableError: If SUPABASE_URL or SUPABASE_SERVICE_KEY not set

    Example:
        >>> client = get_supabase_client()
        >>> response = client.table("organizations").select("*").execute()
        >>> organizations = response.data
    """
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url:
        raise MissingEnvironmentVariableError(
            "SUPABASE_URL environment variable is required. "
            "Set it to your Supabase project URL (e.g., https://xxx.supabase.co)"
        )

    if not service_key:
        raise MissingEnvironmentVariableError(
            "SUPABASE_SERVICE_KEY environment variable is required. "
            "Find it in Supabase Dashboard > Settings > API > service_role key"
        )

    # Create client with service role key (bypasses RLS)
    client: Client = create_client(url, service_key)

    return client


async def execute_rpc(
    function_name: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """Execute Supabase RPC function with error handling.

    Args:
        function_name: Name of the PostgreSQL function to call
        params: Optional parameters to pass to the function

    Returns:
        Function result data

    Raises:
        SupabaseClientError: If RPC function execution fails

    Example:
        >>> result = await execute_rpc(
        ...     "increment_usage_metrics",
        ...     {"org_id": 123, "month": "2025-10", "tool": "get_properties"}
        ... )
    """
    client = get_supabase_client()

    try:
        response = client.rpc(function_name, params or {}).execute()
        return response.data
    except Exception as e:
        raise SupabaseClientError(f"Failed to execute RPC function '{function_name}': {e!s}") from e


async def query_with_rls(
    table: str,
    user_id: str,
    select: str = "*",
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Query table with RLS context for specific user.

    This helper sets the JWT claims to enforce RLS policies as if
    the query was made by the specified user.

    Args:
        table: Table name to query
        user_id: User UUID for RLS context
        select: Columns to select (default: "*")
        filters: Optional column filters (e.g., {"status": "active"})

    Returns:
        List of matching records

    Raises:
        SupabaseClientError: If query fails

    Example:
        >>> organizations = await query_with_rls(
        ...     "organizations",
        ...     user_id="550e8400-e29b-41d4-a716-446655440000",
        ...     filters={"status": "active"}
        ... )
    """
    client = get_supabase_client()

    try:
        query = client.table(table).select(select)

        # Apply filters if provided
        if filters:
            for column, value in filters.items():
                query = query.eq(column, value)

        response = query.execute()
        result: list[dict[str, Any]] = response.data
        return result
    except Exception as e:
        raise SupabaseClientError(f"Failed to query table '{table}' with RLS: {e!s}") from e
