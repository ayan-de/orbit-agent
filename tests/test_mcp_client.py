"""
Test for MCP (Model Context Protocol) client functionality.
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_mcp_client_manager_initialization():
    """Test MCP client manager initialization."""
    print("Testing MCP client manager initialization...")

    from src.mcp.client import MCPClientManager, get_mcp_client

    # Get global client
    client1 = get_mcp_client()
    client2 = get_mcp_client()

    # Should be the same instance (singleton)
    assert client1 is client2

    print("  ✓ Singleton pattern working correctly")


def test_mcp_client_manager_not_connected():
    """Test that server is not connected initially."""
    print("\nTesting MCP client manager connection state...")

    from src.mcp.client import get_mcp_client

    client = get_mcp_client()

    # Tavily should not be connected initially
    assert not client.is_server_connected("tavily")

    print("  ✓ Server not connected initially")


def test_mcp_client_available_tools_empty():
    """Test that available tools are empty when not connected."""
    print("\nTesting MCP client available tools (disconnected)...")

    from src.mcp.client import get_mcp_client

    client = get_mcp_client()

    # No tools should be available when not connected
    tools = client.get_available_tools("tavily")

    assert tools == [] or len(tools) == 0

    print("  ✓ No tools available when disconnected")


def test_mcp_client_error():
    """Test MCPClientError exception."""
    print("\nTesting MCPClientError exception...")

    from src.mcp.client import MCPClientError

    # Should be able to raise and catch the error
    try:
        raise MCPClientError("Test error message")
    except MCPClientError as e:
        assert str(e) == "Test error message"

    print("  ✓ Error exception test passed!")


def test_mcp_client_get_tools():
    """Test get_tools method."""
    print("\nTesting MCP client get_tools method...")

    from src.mcp.client import get_mcp_client

    client = get_mcp_client()

    # Should return empty list when not initialized
    tools = client.get_tools()
    assert isinstance(tools, list)

    print("  ✓ get_tools returns a list")


def test_mcp_client_get_all_tool_names():
    """Test get_all_tool_names method."""
    print("\nTesting MCP client get_all_tool_names method...")

    from src.mcp.client import get_mcp_client

    client = get_mcp_client()

    # Should return empty list when not initialized
    tool_names = client.get_all_tool_names()
    assert isinstance(tool_names, list)

    print("  ✓ get_all_tool_names returns a list")


def test_mcp_client_execute_tool_not_initialized():
    """Test that execute_tool fails when not initialized."""
    print("\nTesting MCP client execute_tool (not initialized)...")

    import asyncio
    from src.mcp.client import get_mcp_client, MCPClientError

    client = get_mcp_client()

    async def run_test():
        try:
            await client.execute_tool("tavily", "search", query="test")
            assert False, "Should have raised MCPClientError"
        except MCPClientError as e:
            assert "not initialized" in str(e)

    asyncio.run(run_test())

    print("  ✓ execute_tool raises error when not initialized")


if __name__ == "__main__":
    print("=" * 50)
    print("Testing MCP Client (langchain_mcp_adapters)")
    print("=" * 50)

    test_mcp_client_manager_initialization()
    test_mcp_client_manager_not_connected()
    test_mcp_client_available_tools_empty()
    test_mcp_client_error()
    test_mcp_client_get_tools()
    test_mcp_client_get_all_tool_names()
    test_mcp_client_execute_tool_not_initialized()

    print("\n" + "=" * 50)
    print("All MCP client tests passed! ✓")
    print("=" * 50)
