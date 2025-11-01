# API Key Generation Guide

**Last Updated**: 2025-10-28
**Issue**: #008-US3

## Overview

This guide explains how to generate test API keys for local development of the Hostaway MCP Server. The API key generation script allows developers to create valid API keys without requiring access to production databases.

## Prerequisites

Before generating API keys, ensure you have:

1. **Python 3.12+** installed
2. **uv package manager** (recommended) or pip
3. **Supabase instance** running (local or remote)
4. **Environment variables** configured:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_SERVICE_KEY`: Supabase service role key (admin permissions)

### Checking Prerequisites

```bash
# Verify Python version
python --version  # Should be 3.12+

# Verify uv is installed
uv --version

# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY
```

## Quick Start

### 1. Set Environment Variables

Create a `.env` file in the project root (or export in your shell):

```bash
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

**Security Note**: Never commit `.env` files to version control. The `.gitignore` file already excludes them.

### 2. Verify Organization Exists

Before generating a key, ensure your organization exists in the database:

```sql
-- Query Supabase to find organization ID
SELECT id, name FROM organizations WHERE name = 'Your Org Name';
```

### 3. Generate API Key

```bash
# Using uv (recommended)
uv run python -m src.scripts.generate_api_key \
  --org-id 1 \
  --user-id "user-uuid-123"

# Or with optional name
uv run python -m src.scripts.generate_api_key \
  --org-id 1 \
  --user-id "user-uuid-123" \
  --name "Local Development Key"
```

### 4. Save the Generated Key

The script will output:

```
🎉 API KEY GENERATED SUCCESSFULLY
============================================================
API Key:   mcp_xyz123...
Hash:      abc456...
Org ID:    1
Org Name:  Test Organization
Created By: user-uuid-123

⚠️  IMPORTANT: Save this API key securely!
It will not be displayed again.

Usage in requests:
  curl -H 'X-API-Key: mcp_xyz123...' http://localhost:8000/api/listings
============================================================
```

**Copy and save the API key immediately** - it will not be displayed again!

## Detailed Usage

### Command-Line Options

```bash
python -m src.scripts.generate_api_key [OPTIONS]
```

#### Required Options:

| Option | Type | Description |
|--------|------|-------------|
| `--org-id` | Integer | Organization ID to associate the key with |
| `--user-id` | String | User UUID who is creating the key |

#### Optional Options:

| Option | Type | Description |
|--------|------|-------------|
| `--name` | String | Descriptive name for the API key |
| `--supabase-url` | String | Override SUPABASE_URL environment variable |
| `--supabase-key` | String | Override SUPABASE_SERVICE_KEY environment variable |

### Examples

#### Basic Usage

```bash
uv run python -m src.scripts.generate_api_key \
  --org-id 1 \
  --user-id "550e8400-e29b-41d4-a716-446655440000"
```

#### With Custom Name

```bash
uv run python -m src.scripts.generate_api_key \
  --org-id 1 \
  --user-id "550e8400-e29b-41d4-a716-446655440000" \
  --name "Development MacBook Pro"
```

#### With Inline Credentials (Not Recommended)

```bash
uv run python -m src.scripts.generate_api_key \
  --org-id 1 \
  --user-id "550e8400-e29b-41d4-a716-446655440000" \
  --supabase-url "https://your-project.supabase.co" \
  --supabase-key "your-service-key"
```

**Note**: Using inline credentials is not recommended for security reasons. Prefer environment variables or `.env` files.

## Using Generated API Keys

### In API Requests

Include the API key in the `X-API-Key` header:

```bash
# cURL example
curl -H 'X-API-Key: mcp_your_key_here' \
  http://localhost:8000/api/listings

# HTTPie example
http GET localhost:8000/api/listings \
  X-API-Key:mcp_your_key_here
```

### In Python Code

```python
import httpx

api_key = "mcp_your_key_here"
headers = {"X-API-Key": api_key}

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/listings",
        headers=headers
    )
    print(response.json())
```

### In Environment Variables

```bash
# Export for current session
export HOSTAWAY_API_KEY='mcp_your_key_here'

# Use in requests
curl -H "X-API-Key: $HOSTAWAY_API_KEY" http://localhost:8000/api/listings
```

## Setup for Different Environments

### Local Development (Supabase Local)

1. **Start Supabase locally**:
   ```bash
   supabase start
   ```

2. **Get local credentials**:
   ```bash
   supabase status
   # Copy the service_role key
   ```

3. **Set environment variables**:
   ```bash
   export SUPABASE_URL="http://localhost:54321"
   export SUPABASE_SERVICE_KEY="your-local-service-key"
   ```

4. **Generate key**:
   ```bash
   uv run python -m src.scripts.generate_api_key --org-id 1 --user-id "test-user"
   ```

### Remote VPS (Production Supabase)

1. **Get Supabase credentials** from your project dashboard

2. **SSH into your VPS**:
   ```bash
   ssh user@your-vps.com
   ```

3. **Set environment variables**:
   ```bash
   export SUPABASE_URL="https://your-project.supabase.co"
   export SUPABASE_SERVICE_KEY="your-service-role-key"
   ```

4. **Generate key**:
   ```bash
   cd /path/to/hostaway-mcp
   uv run python -m src.scripts.generate_api_key --org-id 1 --user-id "admin-uuid"
   ```

### CI/CD Environment

For automated testing, add API keys to your CI/CD secrets:

```yaml
# GitHub Actions example
env:
  SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
  SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}

steps:
  - name: Generate Test API Key
    run: |
      uv run python -m src.scripts.generate_api_key \
        --org-id 1 \
        --user-id "ci-test-user"
```

## Troubleshooting

### Error: "SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables are required"

**Cause**: Environment variables not set.

**Solution**:
```bash
# Check if variables are set
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY

# Set them if missing
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="your-service-key"
```

### Error: "Organization with ID X not found"

**Cause**: The specified organization doesn't exist in the database.

**Solution**:
1. Check existing organizations:
   ```sql
   SELECT id, name FROM organizations;
   ```
2. Use a valid organization ID or create one first

### Error: "Error inserting API key"

**Cause**: Database permissions issue or invalid user UUID.

**Solution**:
1. Verify Supabase service key has admin permissions
2. Check user UUID format (must be valid UUID v4)
3. Ensure `api_keys` table exists with correct schema

### Permission Denied When Running Script

**Cause**: Script is not executable.

**Solution**:
```bash
# Make script executable (optional)
chmod +x src/scripts/generate_api_key.py

# Or always use python -m
uv run python -m src.scripts.generate_api_key --help
```

### ImportError: No module named 'click'

**Cause**: Dependencies not installed.

**Solution**:
```bash
# Install dependencies
uv sync

# Or with pip
pip install click supabase
```

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** instead of hardcoding keys
3. **Rotate keys regularly** in production
4. **Limit key permissions** to required scopes only
5. **Store keys securely** using a password manager or secrets vault
6. **Delete unused keys** from the database
7. **Monitor key usage** via audit logs

## Database Schema

The script inserts API keys into the `api_keys` table with this structure:

```sql
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id INTEGER NOT NULL REFERENCES organizations(id),
  key_hash TEXT NOT NULL UNIQUE,
  name TEXT,
  created_by_user_id UUID NOT NULL REFERENCES auth.users(id),
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_used_at TIMESTAMPTZ
);
```

**Note**: Only the SHA-256 hash is stored, never the plain key.

## Advanced Usage

### Programmatic Key Generation

You can import the functions directly in Python code:

```python
from src.scripts.generate_api_key import generate_api_key, hash_api_key

# Generate a key
api_key = generate_api_key()
print(f"Generated: {api_key}")

# Compute hash
key_hash = hash_api_key(api_key)
print(f"Hash: {key_hash}")
```

### Batch Key Generation

To generate multiple keys for testing:

```bash
#!/bin/bash
# generate_test_keys.sh

ORG_ID=1
USER_ID="test-user-uuid"

for i in {1..5}; do
  echo "Generating key $i..."
  uv run python -m src.scripts.generate_api_key \
    --org-id $ORG_ID \
    --user-id $USER_ID \
    --name "Test Key $i"
  echo "---"
done
```

## Support

For issues or questions:

1. Check the [main README](../README.md) for project setup
2. Review [CLAUDE.md](../CLAUDE.md) for development guidelines
3. Create an issue on GitHub with the `api-key` label

## Related Documentation

- [MCP Server Setup](../README.md#setup)
- [Authentication Guide](./AUTHENTICATION.md)
- [API Reference](./API_REFERENCE.md)
- [Supabase Configuration](./SUPABASE_SETUP.md)
