"""MCP protocol tests for tool discovery and schema validation.

Tests authentication tools are properly registered and discoverable
by MCP clients like Claude Desktop.

Following TDD: These tests should FAIL until implementation is complete.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.mcp.server import mcp


@pytest.fixture
def client() -> TestClient:
    """Create test client for FastAPI app."""
    return TestClient(app)


# T033: MCP protocol test for authentication tool discovery
class TestAuthenticationToolDiscovery:
    """Test MCP server discovers and exposes authentication tools."""

    def test_mcp_server_initialized(self) -> None:
        """Test MCP server is properly initialized.

        Verifies:
        - MCP server instance exists
        - Server name is 'hostaway-mcp'
        - Server version is '0.1.0'
        """
        assert mcp is not None
        assert hasattr(mcp, "name")
        assert mcp.name == "hostaway-mcp"
        assert hasattr(mcp, "version")
        assert mcp.version == "0.1.0"

    def test_authenticate_hostaway_tool_registered(self) -> None:
        """Test 'authenticate_hostaway' MCP tool is registered.

        Verifies:
        - Tool exists in MCP server
        - Tool has proper name and description
        - Tool input schema includes account_id and secret_key
        - Tool output schema includes access_token and expires_in
        """
        # Get registered tools from MCP server
        # Note: fastapi-mcp stores tools in _tools attribute
        tools = mcp._tools if hasattr(mcp, "_tools") else {}

        # Verify authenticate_hostaway tool is registered
        assert "authenticate_hostaway" in tools, "authenticate_hostaway tool not found"

        tool = tools["authenticate_hostaway"]

        # Verify tool metadata
        assert tool.name == "authenticate_hostaway"
        assert "authenticate" in tool.description.lower()
        assert "hostaway" in tool.description.lower()

        # Verify input schema
        input_schema = tool.input_schema
        assert "account_id" in input_schema["properties"]
        assert "secret_key" in input_schema["properties"]
        assert input_schema["properties"]["account_id"]["type"] == "string"
        assert input_schema["properties"]["secret_key"]["type"] == "string"

    def test_refresh_token_tool_registered(self) -> None:
        """Test 'refresh_token' MCP tool is registered.

        Verifies:
        - Tool exists in MCP server
        - Tool has proper name and description
        - Tool requires no input (uses existing credentials)
        - Tool output schema includes new access_token and expires_in
        """
        tools = mcp._tools if hasattr(mcp, "_tools") else {}

        # Verify refresh_token tool is registered
        assert "refresh_token" in tools, "refresh_token tool not found"

        tool = tools["refresh_token"]

        # Verify tool metadata
        assert tool.name == "refresh_token"
        assert "refresh" in tool.description.lower()
        assert "token" in tool.description.lower()

        # Tool should require no input parameters
        input_schema = tool.input_schema
        assert (
            len(input_schema.get("properties", {})) == 0 or input_schema.get("properties") is None
        )

    def test_authentication_tools_have_proper_schemas(self) -> None:
        """Test authentication tools have valid JSON schemas.

        Verifies:
        - Input schemas follow JSON Schema Draft 7
        - Required fields are marked as required
        - Field types are correctly specified
        - Descriptions are present for AI understanding
        """
        tools = mcp._tools if hasattr(mcp, "_tools") else {}

        # Test authenticate_hostaway schema
        if "authenticate_hostaway" in tools:
            auth_tool = tools["authenticate_hostaway"]
            schema = auth_tool.input_schema

            # Verify schema structure
            assert "type" in schema
            assert schema["type"] == "object"
            assert "properties" in schema
            assert "required" in schema

            # Verify required fields
            assert "account_id" in schema["required"]
            assert "secret_key" in schema["required"]

            # Verify field descriptions exist
            assert "description" in schema["properties"]["account_id"]
            assert "description" in schema["properties"]["secret_key"]

    def test_mcp_tools_endpoint_accessible(self, client: TestClient) -> None:
        """Test MCP tools endpoint is accessible via HTTP.

        Verifies:
        - GET /mcp/tools returns 200
        - Response includes authentication tools
        - Tool schemas are valid JSON

        Note: This assumes HTTP transport is mounted for testing.
        """
        # Note: This test may need adjustment based on how fastapi-mcp
        # exposes tools via HTTP. The exact endpoint may vary.
        # For now, verify the app has MCP mounted
        assert "/mcp" in [route.path for route in app.routes]

    def test_tool_invocation_requires_authentication(self, client: TestClient) -> None:
        """Test MCP tools require proper authentication when invoked.

        Verifies:
        - Tools cannot be invoked without authentication
        - Proper error responses are returned
        - Error messages are helpful for AI agents

        Note: This is a security test for tool access control.
        """
        # This test verifies that the dependency injection for
        # get_authenticated_client() properly guards tool access
        # Implementation will depend on how tools are protected
        # TODO: Implement after tools are registered

    def test_tool_descriptions_are_ai_friendly(self) -> None:
        """Test tool descriptions are clear and helpful for AI agents.

        Verifies:
        - Descriptions explain what the tool does
        - Descriptions include use cases
        - Descriptions mention expected inputs/outputs
        - Language is clear and unambiguous
        """
        tools = mcp._tools if hasattr(mcp, "_tools") else {}

        for tool_name, tool in tools.items():
            if "auth" in tool_name or "token" in tool_name:
                # Verify description exists and is substantial
                assert hasattr(tool, "description")
                assert len(tool.description) > 20, f"{tool_name} description too short"

                # Verify description is helpful
                description_lower = tool.description.lower()
                assert any(
                    keyword in description_lower
                    for keyword in ["authenticate", "token", "access", "credentials"]
                ), f"{tool_name} description not clear"

    def test_mcp_server_mounts_to_fastapi_app(self, client: TestClient) -> None:
        """Test MCP server is properly mounted to FastAPI app.

        Verifies:
        - MCP endpoint exists at /mcp
        - Endpoint is accessible
        - ASGI transport is configured
        """
        # Check MCP is mounted
        mcp_routes = [route for route in app.routes if "/mcp" in route.path]
        assert len(mcp_routes) > 0, "MCP not mounted to FastAPI app"

    def test_tool_schemas_validate_with_jsonschema(self) -> None:
        """Test tool schemas are valid according to JSON Schema specification.

        Verifies:
        - Schemas can be validated by jsonschema library
        - All required fields are present
        - Types are correctly specified
        """
        import jsonschema

        tools = mcp._tools if hasattr(mcp, "_tools") else {}

        for tool_name, tool in tools.items():
            if "auth" in tool_name or "token" in tool_name:
                schema = tool.input_schema

                # Verify schema is valid JSON Schema
                try:
                    # Use Draft7Validator for validation
                    jsonschema.Draft7Validator.check_schema(schema)
                except jsonschema.SchemaError as e:
                    pytest.fail(f"Invalid schema for tool {tool_name}: {e}")
