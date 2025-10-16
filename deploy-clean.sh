#!/bin/bash
# Secure Deployment Script Template

set -e

# Load environment variables from secure location
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: .env file not found"
    echo "Please create .env from .env.example"
    exit 1
fi

# Verify required environment variables
required_vars=(
    "SUPABASE_URL"
    "SUPABASE_SERVICE_KEY"
    "MCP_API_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set"
        exit 1
    fi
done

echo "Environment variables loaded successfully"
# Add your deployment commands here
