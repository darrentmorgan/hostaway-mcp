-- Add API key to Supabase database
-- Run this in your Hostinger terminal

-- First, get your organization ID (you'll need this)
SELECT id, name FROM organizations LIMIT 5;

-- Replace 'YOUR_ORG_ID_HERE' with the actual UUID from the query above
-- Then run this to insert the API key:

INSERT INTO api_keys (
    key,
    organization_id,
    name,
    is_active,
    created_at
) VALUES (
    'mcp_fbK7dpky8vqkjhn6QLGwAYyiB4Rd4d5',
    'YOUR_ORG_ID_HERE',  -- Replace with your actual org ID
    'Claude Desktop MCP',
    true,
    NOW()
)
ON CONFLICT (key) DO UPDATE SET
    is_active = true,
    updated_at = NOW();

-- Verify it was created
SELECT key, name, is_active, created_at
FROM api_keys
WHERE key = 'mcp_fbK7dpky8vqkjhn6QLGwAYyiB4Rd4d5';
