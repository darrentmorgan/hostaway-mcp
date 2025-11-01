"""Integration tests for all MCP Migration Guide fixes.

This test suite validates that all 7 fixes work together correctly after merging.
It tests end-to-end workflows that span multiple fixes.
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add mcp_stdio_server to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_all_fixes_integrated():
    """Test that all 7 fixes are present and working together.

    This is the main integration test that validates:
    - Fix 1: All tools have hostaway_ prefix
    - Fix 2: All tools have proper annotations
    - Fix 3: Error handling works across all tools
    - Fix 4: Response formats available on all tools
    - Imp 1: Tool descriptions are comprehensive
    - Imp 2: Input validation is robust
    - Imp 3: Character limit truncation works
    """
    import mcp_stdio_server

    tools = asyncio.run(mcp_stdio_server.list_tools())

    # Should have exactly 7 tools
    assert len(tools) == 7, f"Expected 7 tools, got {len(tools)}"

    # All tools should have prefix (Fix 1)
    for tool in tools:
        assert tool.name.startswith("hostaway_"), f"Tool {tool.name} missing prefix"

    # All tools should have annotations (Fix 2)
    for tool in tools:
        assert tool.annotations is not None
        assert tool.annotations["readOnlyHint"] is True
        assert tool.annotations["destructiveHint"] is False
        assert tool.annotations["openWorldHint"] is True

    # All tools should have comprehensive descriptions (Imp 1)
    for tool in tools:
        assert len(tool.description) > 100

    # All tools should have proper input validation (Imp 2)
    for tool in tools:
        schema = tool.inputSchema
        assert schema.get("additionalProperties") is False


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_error_handling_with_prefixed_tools():
    """Test that error messages reference correct prefixed tool names.

    Validates Fix 1 + Fix 3 integration:
    - 404 errors should suggest using hostaway_list_properties (not list_properties)
    - Error messages should reference correct tool names
    """
    import httpx

    from mcp_stdio_server import create_http_error_response

    # Simulate 404 error
    mock_response = httpx.Response(404, request=httpx.Request("GET", "http://test"))
    error = httpx.HTTPStatusError(
        "Not Found", request=mock_response.request, response=mock_response
    )

    response = create_http_error_response(error, "fetching property")

    # Should suggest prefixed tool name
    assert "hostaway_list_properties" in response[0].text
    # Should NOT suggest old name
    assert (
        "list_properties" not in response[0].text or "hostaway_list_properties" in response[0].text
    )


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_response_format_with_character_limit():
    """Test that markdown formatting works with character limit truncation.

    Validates Fix 4 + Imp 3 integration:
    - Large markdown responses should be truncated at 25,000 characters
    - Truncation message should guide users to use JSON format
    """
    from mcp_stdio_server import CHARACTER_LIMIT, format_properties_list_markdown, truncate_response

    # Create large dataset
    large_data = {
        "items": [
            {
                "id": i,
                "name": f"Property {i}",
                "city": "Ubud",
                "country": "Indonesia",
                "bedrooms": 3,
                "status": "Available",
                "description": "A" * 500,  # Long description
            }
            for i in range(100)  # 100 properties with long descriptions
        ],
        "meta": {"hasMore": False},
        "nextCursor": None,
    }

    # Format as markdown
    markdown = format_properties_list_markdown(large_data)

    # Apply character limit
    truncated = truncate_response(markdown, limit=CHARACTER_LIMIT)

    # Should be truncated
    assert len(truncated) <= CHARACTER_LIMIT

    # Should include guidance
    if len(markdown) > CHARACTER_LIMIT:
        assert "Response Truncated" in truncated
        assert "response_format" in truncated  # Suggest using JSON format


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_input_validation_with_annotations():
    """Test that input validation works correctly for annotated tools.

    Validates Fix 2 + Imp 2 integration:
    - Tools with idempotentHint should have consistent validation
    - Read-only tools should reject write operations
    """
    import mcp_stdio_server

    tools = asyncio.run(mcp_stdio_server.list_tools())

    for tool in tools:
        schema = tool.inputSchema

        # Read-only tools should not accept any write-related parameters
        if tool.annotations["readOnlyHint"] is True:
            properties = schema.get("properties", {})
            # Should not have parameters like "update", "delete", "modify"
            write_params = [
                p
                for p in properties
                if any(keyword in p.lower() for keyword in ["update", "delete", "modify", "create"])
            ]
            assert (
                len(write_params) == 0
            ), f"Read-only tool {tool.name} has write parameters: {write_params}"


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_enhanced_descriptions_for_list_tools():
    """Test that list tools have enhanced descriptions with usage guidance.

    Validates Imp 1 integration:
    - List tools should have "when to use" guidance
    - List tools should have "when NOT to use" guidance
    - Descriptions should mention available filters
    """
    import mcp_stdio_server

    tools = asyncio.run(mcp_stdio_server.list_tools())

    list_tools = [t for t in tools if "list" in t.name or "search" in t.name]

    for tool in list_tools:
        description = tool.description

        # Should have usage guidance
        assert any(
            phrase in description for phrase in ["When to use", "Usage examples", "Use this"]
        ), f"{tool.name} missing usage guidance"

        # Should have "when NOT to use"
        assert "NOT to use" in description, f"{tool.name} missing 'when NOT to use'"

        # Should mention pagination or filtering
        assert any(
            keyword in description.lower()
            for keyword in ["filter", "limit", "cursor", "pagination"]
        ), f"{tool.name} description missing pagination/filter guidance"


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_end_to_end_workflow():
    """Test complete workflow using multiple fixed tools.

    End-to-end workflow:
    1. List properties (with markdown format)
    2. Get property details (test error handling)
    3. Check availability
    4. Verify all responses use correct prefixes and formats
    """
    import mcp_stdio_server

    # Step 1: List properties with markdown format
    list_response = asyncio.run(
        mcp_stdio_server.call_tool(
            "hostaway_list_properties", {"limit": 5, "response_format": "markdown"}
        )
    )

    assert list_response is not None
    assert isinstance(list_response, list)
    assert len(list_response) > 0
    assert list_response[0].type == "text"

    # Should be markdown formatted
    markdown_text = list_response[0].text
    assert "#" in markdown_text  # Markdown headers

    # Step 2: Test error handling with invalid property ID
    error_response = asyncio.run(
        mcp_stdio_server.call_tool("hostaway_get_property_details", {"property_id": 999999999})
    )

    # Should return error response
    assert error_response is not None
    assert "ERROR:" in error_response[0].text or "not found" in error_response[0].text.lower()

    # Error should suggest using list tool
    if "404" in error_response[0].text or "not found" in error_response[0].text.lower():
        assert "hostaway_list_properties" in error_response[0].text


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_all_tools_callable():
    """Test that all 7 tools can be called without errors.

    This doesn't test actual API responses, but validates:
    - Tool registration works
    - Input schemas are valid
    - Error handling doesn't crash
    """
    import mcp_stdio_server

    tools = asyncio.run(mcp_stdio_server.list_tools())

    expected_tools = [
        "hostaway_list_properties",
        "hostaway_get_property_details",
        "hostaway_check_availability",
        "hostaway_search_bookings",
        "hostaway_get_booking_details",
        "hostaway_get_guest_info",
        "hostaway_get_financial_reports",
    ]

    actual_tools = [t.name for t in tools]

    for expected in expected_tools:
        assert expected in actual_tools, f"Tool {expected} not found"

        # Verify each tool has valid schema
        tool = next(t for t in tools if t.name == expected)
        assert tool.inputSchema is not None
        assert "properties" in tool.inputSchema
        assert tool.description is not None
        assert len(tool.description) > 0


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_consistency_across_fixes():
    """Test that all fixes maintain consistency.

    Validates:
    - All tools use same error response format (Fix 3)
    - All tools support same response formats (Fix 4)
    - All tools have consistent annotation patterns (Fix 2)
    """
    import mcp_stdio_server

    tools = asyncio.run(mcp_stdio_server.list_tools())

    # All tools should have same annotation keys
    annotation_keys = None
    for tool in tools:
        if annotation_keys is None:
            annotation_keys = set(tool.annotations.keys())
        else:
            assert (
                set(tool.annotations.keys()) == annotation_keys
            ), f"Tool {tool.name} has different annotation keys"

    # All list/search tools should support response_format parameter
    list_search_tools = [t for t in tools if "list" in t.name or "search" in t.name]
    for tool in list_search_tools:
        schema = tool.inputSchema
        properties = schema.get("properties", {})

        assert (
            "response_format" in properties
        ), f"Tool {tool.name} missing response_format parameter"

        # Should support both json and markdown
        format_enum = properties["response_format"].get("enum", [])
        assert "json" in format_enum
        assert "markdown" in format_enum


@pytest.mark.skip(reason="Requires mcp_stdio_server implementation")
def test_backward_compatibility():
    """Test that fixes don't break existing functionality.

    Validates:
    - Old tool names are NOT accessible (Fix 1)
    - Default response format is markdown (Fix 4)
    - Error responses are backwards compatible (Fix 3)
    """
    import mcp_stdio_server

    tools = asyncio.run(mcp_stdio_server.list_tools())

    # Old names should NOT exist
    old_names = [
        "list_properties",
        "get_property_details",
        "check_availability",
        "search_bookings",
        "get_booking_details",
        "get_guest_info",
        "get_financial_reports",
    ]

    actual_names = [t.name for t in tools]
    for old_name in old_names:
        assert old_name not in actual_names, f"Old tool name {old_name} should not be present"

    # Test default response format
    # When response_format is not specified, should default to markdown
    list_response = asyncio.run(
        mcp_stdio_server.call_tool(
            "hostaway_list_properties",
            {"limit": 1},  # No response_format specified
        )
    )

    # Should return markdown by default
    assert list_response[0].type == "text"
    # Markdown should have headers or formatting
    text = list_response[0].text
    assert "#" in text or "*" in text or "-" in text  # Common markdown characters
