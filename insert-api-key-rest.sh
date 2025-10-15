#!/bin/bash
# Insert API key using Supabase REST API

SUPABASE_URL="https://khodniyhethjyomscyjw.supabase.co"
SERVICE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtob2RuaXloZXRoanlvbXNjeWp3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDE5MDA4MCwiZXhwIjoyMDY5NzY2MDgwfQ.58Llsii1gzL9mael0FIVavN90D_K0LNuI4p1v8lscQg"
API_KEY_HASH="603056d3f247194b36e533c06d2cc7c81b5fa288e9bc9bfa29f45c0d5b01ad46"

echo "=== Step 1: Getting organization ID ==="
ORG_RESPONSE=$(curl -s "${SUPABASE_URL}/rest/v1/organizations?select=id,name&limit=1" \
  -H "apikey: ${SERVICE_KEY}" \
  -H "Authorization: Bearer ${SERVICE_KEY}")

echo "$ORG_RESPONSE" | python3 -m json.tool

ORG_ID=$(echo "$ORG_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '')")

if [ -z "$ORG_ID" ]; then
    echo "ERROR: No organization found in database!"
    echo "You need to create an organization first via the dashboard:"
    echo "https://dashboard-iota-eight-75.vercel.app/dashboard"
    exit 1
fi

echo "Found organization ID: $ORG_ID"
echo ""

echo "=== Step 2: Inserting API key ==="
INSERT_RESPONSE=$(curl -s -X POST "${SUPABASE_URL}/rest/v1/api_keys" \
  -H "apikey: ${SERVICE_KEY}" \
  -H "Authorization: Bearer ${SERVICE_KEY}" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation" \
  -d "{
    \"key_hash\": \"${API_KEY_HASH}\",
    \"organization_id\": \"${ORG_ID}\",
    \"name\": \"Claude Desktop MCP\",
    \"is_active\": true
  }")

echo "$INSERT_RESPONSE" | python3 -m json.tool
echo ""

echo "=== Step 3: Verifying API key ==="
VERIFY_RESPONSE=$(curl -s "${SUPABASE_URL}/rest/v1/api_keys?key_hash=eq.${API_KEY_HASH}&select=id,key_hash,name,is_active,created_at" \
  -H "apikey: ${SERVICE_KEY}" \
  -H "Authorization: Bearer ${SERVICE_KEY}")

echo "$VERIFY_RESPONSE" | python3 -m json.tool

echo ""
echo "=== API key setup complete ==="
