#!/usr/bin/env python3
"""API Key Generation CLI for Hostaway MCP Server.

Generates test API keys for local development without requiring production database access.
Issue #008-US3: Provide documented CLI script for API key generation.

Usage:
    python -m src.scripts.generate_api_key --org-id 1 --user-id user-uuid-123

Environment Variables:
    SUPABASE_URL: Supabase project URL
    SUPABASE_SERVICE_KEY: Supabase service role key (has admin permissions)
"""

import hashlib
import os
import secrets
import sys

import click

from supabase import Client, create_client


def generate_api_key() -> str:
    """Generate a cryptographically secure API key.

    Returns:
        API key in format: mcp_{base64_urlsafe_token}
    """
    # Generate 32 bytes (256 bits) of cryptographic randomness
    token = secrets.token_urlsafe(32)
    return f"mcp_{token}"


def hash_api_key(api_key: str) -> str:
    """Compute SHA-256 hash of API key for database storage.

    Args:
        api_key: Plain API key

    Returns:
        SHA-256 hash as hexadecimal string
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_supabase_client() -> Client:
    """Create Supabase client from environment variables.

    Returns:
        Configured Supabase client

    Raises:
        ValueError: If required environment variables are missing
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables are required.\n"
            "Set them in your .env file or export them in your shell."
        )

    return create_client(url, key)


@click.command()
@click.option(
    "--org-id",
    type=int,
    required=True,
    help="Organization ID to associate the API key with",
)
@click.option(
    "--user-id",
    type=str,
    required=True,
    help="User UUID who is creating the key",
)
@click.option(
    "--name",
    type=str,
    default=None,
    help="Optional name/description for the API key",
)
@click.option(
    "--supabase-url",
    type=str,
    default=None,
    help="Supabase URL (overrides SUPABASE_URL env var)",
)
@click.option(
    "--supabase-key",
    type=str,
    default=None,
    help="Supabase service key (overrides SUPABASE_SERVICE_KEY env var)",
)
def generate_key(  # noqa: PLR0915
    org_id: int,
    user_id: str,
    name: str | None,
    supabase_url: str | None,
    supabase_key: str | None,
) -> None:
    """Generate a test API key for local development.

    This script creates a new API key and stores it in the Supabase database.
    The key is only displayed once - save it securely!

    Example:
        python -m src.scripts.generate_api_key --org-id 1 --user-id user-123

    Args:
        org_id: Organization ID to associate key with
        user_id: User UUID creating the key
        name: Optional key description
        supabase_url: Optional Supabase URL override
        supabase_key: Optional Supabase key override
    """
    try:
        # Override env vars if provided
        if supabase_url:
            os.environ["SUPABASE_URL"] = supabase_url
        if supabase_key:
            os.environ["SUPABASE_SERVICE_KEY"] = supabase_key

        # Get Supabase client
        try:
            supabase = get_supabase_client()
        except ValueError as e:
            click.echo(f"❌ Error: {e}", err=True)
            sys.exit(1)

        # Step 1: Verify organization exists
        click.echo(f"🔍 Verifying organization {org_id}...")
        try:
            org_response = (
                supabase.table("organizations").select("*").eq("id", org_id).single().execute()
            )

            if not org_response.data:
                click.echo(f"❌ Error: Organization with ID {org_id} not found", err=True)
                sys.exit(1)

            org_name = org_response.data.get("name", "Unknown")
            click.echo(f"✅ Found organization: {org_name}")
        except Exception as e:
            click.echo(f"❌ Error verifying organization: {e}", err=True)
            sys.exit(1)

        # Step 2: Generate API key
        click.echo("\n🔐 Generating API key...")
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)

        # Step 3: Insert into database
        click.echo("💾 Storing API key in database...")
        try:
            key_data = {
                "organization_id": org_id,
                "key_hash": key_hash,
                "created_by_user_id": user_id,
                "is_active": True,
            }

            # Add optional name if provided
            if name:
                key_data["name"] = name

            insert_response = supabase.table("api_keys").insert(key_data).execute()

            if not insert_response.data:
                click.echo("❌ Error: Failed to insert API key into database", err=True)
                sys.exit(1)

            key_id = insert_response.data[0].get("id", "unknown")
            click.echo(f"✅ API key created successfully (ID: {key_id})")
        except Exception as e:
            click.echo(f"❌ Error inserting API key: {e}", err=True)
            sys.exit(1)

        # Step 4: Display the key (only shown once!)
        click.echo("\n" + "=" * 60)
        click.echo("🎉 API KEY GENERATED SUCCESSFULLY")
        click.echo("=" * 60)
        click.echo(f"\nAPI Key:   {api_key}")
        click.echo(f"Hash:      {key_hash}")
        click.echo(f"Org ID:    {org_id}")
        click.echo(f"Org Name:  {org_name}")
        click.echo(f"Created By: {user_id}")
        if name:
            click.echo(f"Name:      {name}")
        click.echo("\n⚠️  IMPORTANT: Save this API key securely!")
        click.echo("It will not be displayed again.\n")
        click.echo("Usage in requests:")
        click.echo(f"  curl -H 'X-API-Key: {api_key}' http://localhost:8000/api/listings")
        click.echo("\nOr in environment variables:")
        click.echo(f"  export HOSTAWAY_API_KEY='{api_key}'")
        click.echo("=" * 60)

    except KeyboardInterrupt:
        click.echo("\n\n❌ Operation cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    generate_key()
