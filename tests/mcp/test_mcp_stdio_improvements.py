"""Tests for MCP Migration Guide improvements.

This test suite validates all 7 fixes from the MCP Migration Guide.
Each test can run independently to verify a specific fix.
"""

import sys
from pathlib import Path

import pytest

# Add mcp_stdio_server to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_fix_1_service_prefixes():
    """Fix 1: Verify all 7 tools have 'hostaway_' prefix.

    Expected tool names:
    - hostaway_list_properties
    - hostaway_get_property_details
    - hostaway_check_availability
    - hostaway_search_bookings
    - hostaway_get_booking_details
    - hostaway_get_guest_info
    - hostaway_get_financial_reports
    """
    import asyncio

    import mcp_stdio_server

    tools = asyncio.run(mcp_stdio_server.list_tools())

    expected_names = [
        "hostaway_list_properties",
        "hostaway_get_property_details",
        "hostaway_check_availability",
        "hostaway_search_bookings",
        "hostaway_get_booking_details",
        "hostaway_get_guest_info",
        "hostaway_get_financial_reports",
    ]

    actual_names = [tool.name for tool in tools]

    for expected in expected_names:
        assert expected in actual_names, f"Tool {expected} not found"

    # Verify old names are NOT present
    old_names = [
        "list_properties",
        "get_property_details",
        "check_availability",
        "search_bookings",
        "get_booking_details",
        "get_guest_info",
        "get_financial_reports",
    ]

    for old_name in old_names:
        assert old_name not in actual_names, f"Old tool name {old_name} should not be present"


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_fix_2_tool_annotations():
    """Fix 2: Verify annotations present on all tools.

    Expected annotations:
    - readOnlyHint: True (all tools are read-only)
    - destructiveHint: False (no tools modify/delete data)
    - idempotentHint: True (except financial reports)
    - openWorldHint: True (all interact with external API)
    """
    import asyncio

    import mcp_stdio_server

    tools = asyncio.run(mcp_stdio_server.list_tools())

    required_annotations = ["readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"]

    for tool in tools:
        # Verify annotations exist
        assert tool.annotations is not None, f"Tool {tool.name} missing annotations"

        for annotation in required_annotations:
            assert annotation in tool.annotations, f"Tool {tool.name} missing {annotation}"

        # Verify read-only
        assert tool.annotations["readOnlyHint"] is True, f"{tool.name} should be read-only"
        assert (
            tool.annotations["destructiveHint"] is False
        ), f"{tool.name} should not be destructive"

        # Verify open-world
        assert tool.annotations["openWorldHint"] is True, f"{tool.name} should be open-world"

        # Financial reports are not idempotent (data may update)
        if tool.name == "hostaway_get_financial_reports":
            assert tool.annotations["idempotentHint"] is False
        else:
            assert tool.annotations["idempotentHint"] is True


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_fix_3_error_messages():
    """Fix 3: Test actionable error responses.

    Expected error handling:
    - 401: Authentication guidance
    - 403: Permission guidance
    - 404: Suggests using list tools to find valid IDs
    - 429: Rate limit guidance with retry advice
    - 500+: Server error guidance
    - Timeout: Suggests reducing limit parameter
    """
    import httpx

    from mcp_stdio_server import create_error_response, create_http_error_response

    # Test generic error response
    response = create_error_response("Test error")
    assert len(response) == 1
    assert response[0].type == "text"
    assert "ERROR:" in response[0].text

    # Test 401 error
    mock_response = httpx.Response(401, request=httpx.Request("GET", "http://test"))
    error = httpx.HTTPStatusError(
        "Unauthorized", request=mock_response.request, response=mock_response
    )
    response = create_http_error_response(error, "testing")

    assert "Authentication failed" in response[0].text
    assert "REMOTE_MCP_API_KEY" in response[0].text

    # Test 404 error
    mock_response = httpx.Response(404, request=httpx.Request("GET", "http://test"))
    error = httpx.HTTPStatusError(
        "Not Found", request=mock_response.request, response=mock_response
    )
    response = create_http_error_response(error, "fetching property")

    assert "Resource not found" in response[0].text
    assert "hostaway_list_properties" in response[0].text  # Actionable suggestion

    # Test 429 rate limit
    mock_response = httpx.Response(429, request=httpx.Request("GET", "http://test"))
    error = httpx.HTTPStatusError(
        "Too Many Requests", request=mock_response.request, response=mock_response
    )
    response = create_http_error_response(error, "listing")

    assert "Rate limit exceeded" in response[0].text
    assert "10 seconds" in response[0].text  # Specific guidance

    # Test timeout
    error = httpx.TimeoutException("Timeout")
    response = create_http_error_response(error, "fetching data")

    assert "timeout" in response[0].text.lower()
    assert "30 seconds" in response[0].text


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_fix_4_markdown_formatting():
    """Fix 4: Test JSON and Markdown response formats.

    Expected:
    - response_format parameter accepts "json" or "markdown"
    - Default is "markdown"
    - Markdown output is human-readable
    - JSON output is valid JSON
    """
    from mcp_stdio_server import (
        format_properties_list_markdown,
        format_property_markdown,
    )

    # Test single property formatting
    property_data = {
        "id": 12345,
        "name": "Test Villa",
        "city": "Ubud",
        "country": "Indonesia",
        "bedrooms": 3,
        "status": "Available",
    }

    markdown = format_property_markdown(property_data)
    assert "Test Villa" in markdown
    assert "12345" in markdown
    assert "Ubud, Indonesia" in markdown
    assert "### " in markdown  # Markdown header

    # Test properties list formatting
    data = {"items": [property_data], "meta": {"hasMore": True}, "nextCursor": "abc123"}

    markdown = format_properties_list_markdown(data)
    assert "# Properties" in markdown
    assert "Test Villa" in markdown
    assert "More results available" in markdown
    assert "abc123" in markdown


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_imp_1_tool_descriptions():
    """Improvement 1: Verify enhanced tool descriptions.

    Expected:
    - Descriptions longer than 100 characters
    - Contains "When to use" or "Usage examples"
    - Contains "When NOT to use" for list/search tools
    - Includes performance info
    """
    import asyncio

    import mcp_stdio_server

    tools = asyncio.run(mcp_stdio_server.list_tools())

    for tool in tools:
        description = tool.description

        # Should be comprehensive
        assert len(description) > 100, f"{tool.name} description too short"

        # Should contain usage guidance
        assert any(
            phrase in description
            for phrase in ["When to use", "Usage examples", "Examples:", "Use this"]
        ), f"{tool.name} missing usage guidance"

        # List/search tools should have "when NOT to use"
        if "list" in tool.name or "search" in tool.name:
            assert "NOT to use" in description, f"{tool.name} missing 'when NOT to use'"


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_imp_2_input_validation():
    """Improvement 2: Test input validation constraints.

    Expected:
    - Numeric fields have min/max constraints
    - Date fields have pattern validation
    - Schemas include examples
    - additionalProperties set to False
    """
    import asyncio

    import mcp_stdio_server

    tools = asyncio.run(mcp_stdio_server.list_tools())

    for tool in tools:
        schema = tool.inputSchema
        properties = schema.get("properties", {})

        # Check numeric constraints
        for prop_name, prop_schema in properties.items():
            if prop_schema.get("type") == "integer":
                assert "minimum" in prop_schema, f"{tool.name}.{prop_name} missing minimum"

                if prop_name == "limit":
                    assert "maximum" in prop_schema, f"{tool.name}.limit missing maximum"

        # Check for examples
        has_examples = any("examples" in prop for prop in properties.values())
        assert has_examples, f"{tool.name} has no examples in schema"

        # Check additionalProperties
        assert (
            schema.get("additionalProperties") is False
        ), f"{tool.name} should reject additional properties"


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_imp_3_character_limit():
    """Improvement 3: Test CHARACTER_LIMIT truncation.

    Expected:
    - CHARACTER_LIMIT constant set to 25000
    - truncate_response() function exists
    - Truncation includes helpful guidance
    - Response under limit is not truncated
    """
    from mcp_stdio_server import CHARACTER_LIMIT, truncate_response

    # Verify constant
    assert CHARACTER_LIMIT == 25000

    # Test under limit
    short_text = "Short response"
    result = truncate_response(short_text, limit=1000)
    assert result == short_text
    assert "Truncated" not in result

    # Test over limit
    long_text = "x" * 30000
    result = truncate_response(long_text, limit=25000)

    assert len(result) <= 25000
    assert "Response Truncated" in result
    assert "Reduce the `limit` parameter" in result
    assert "Add filters" in result
    assert "cursor pagination" in result
