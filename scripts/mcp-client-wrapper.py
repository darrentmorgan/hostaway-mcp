#!/usr/bin/env python3
"""
MCP Client Wrapper for Claude Desktop

This script acts as a local MCP server that forwards requests to the remote
Hostaway MCP server via the SSH tunnel (localhost:8000 -> 72.60.233.157:8080).

Usage:
    python3 mcp-client-wrapper.py
"""

import json
import sys
import urllib.error
import urllib.request

API_KEY = "mcp_x64EA0rh4EPmDsi8tVy-xzomCFTV1rApJmQdXGE-j00"
BASE_URL = "http://72.60.233.157:8080"  # Direct access to production server


def make_request(method: str, path: str, data: dict = None):
    """Make HTTP request to remote MCP server."""
    url = f"{BASE_URL}{path}"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    req_data = json.dumps(data).encode() if data else None

    try:
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return {"error": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"error": str(e)}


def main():
    """MCP stdio protocol handler."""
    # Read MCP requests from stdin and write responses to stdout
    for line in sys.stdin:
        try:
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})

            # Route MCP methods to API endpoints
            if method == "tools/list":
                response = make_request("GET", "/mcp/v1/tools")
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                response = make_request("POST", f"/mcp/v1/tools/{tool_name}", tool_args)
            else:
                response = {"error": f"Unknown method: {method}"}

            # Write response
            print(json.dumps(response), flush=True)

        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON"}), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)


if __name__ == "__main__":
    main()
