"""
Test for MCP (Model Context Protocol) client functionality.
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_mcp_config_default_servers():
    """Test default MCP server configuration."""
    print("Testing default MCP server configuration...")

    from src.mcp.config import DEFAULT_SERVERS, get_mcp_server_config

    # Check that tavily server is configured
    tavily_config = get_mcp_server_config("tavily")

    assert tavily_config is not None, "Tavily server config not found"
    assert tavily_config.name == "tavily"
    assert tavily_config.transport == "http"
    assert tavily_config.enabled == True

    print(f"  ✓ Tavily server configured: {tavily_config.url}")


def test_mcp_config_custom_servers():
    """Test custom MCP server configuration."""
    print("\nTesting custom MCP server configuration...")

    from src.mcp.config import MCPServersConfig, MCPServerConfig, get_mcp_server_config

    # Create custom config
    custom_config = MCPServersConfig(
        servers={
            "test_server": MCPServerConfig(
                name="test_server",
                url="sse://test-server",
                transport="sse",
                enabled=True,
                timeout=30
            )
        }
    )

    test_server = get_mcp_server_config("test_server", custom_config)

    assert test_server is not None
    assert test_server.name == "test_server"
    assert test_server.url == "sse://test-server"

    print("  ✓ Custom server config test passed!")


def test_mcp_config_get_all():
    """Test getting all enabled MCP servers."""
    print("\nTesting get all MCP server configs...")

    from src.mcp.config import get_all_mcp_server_configs

    all_servers = get_all_mcp_server_configs()

    # Should include tavily
    assert "tavily" in all_servers
    assert all_servers["tavily"].enabled == True

    print(f"  ✓ Found {len(all_servers)} enabled server(s)")


def test_mcp_client_manager_initialization():
    """Test MCP client manager initialization."""
    print("\nTesting MCP client manager initialization...")

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


def test_mcp_server_config_validation():
    """Test MCPServerConfig validation."""
    print("\nTesting MCPServerConfig validation...")

    from src.mcp.config import MCPServerConfig

    # Valid config
    config = MCPServerConfig(
        name="test",
        url="sse://test",
        transport="sse",
        enabled=True,
        timeout=30
    )

    assert config.name == "test"
    assert config.url == "sse://test"
    assert config.transport == "sse"
    assert config.enabled == True
    assert config.timeout == 30

    print("  ✓ Config validation test passed!")


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


if __name__ == "__main__":
    print("=" * 50)
    print("Testing MCP Client (Phase 1)")
    print("=" * 50)

    test_mcp_config_default_servers()
    test_mcp_config_custom_servers()
    test_mcp_config_get_all()
    test_mcp_client_manager_initialization()
    test_mcp_client_manager_not_connected()
    test_mcp_client_available_tools_empty()
    test_mcp_server_config_validation()
    test_mcp_client_error()

    print("\n" + "=" * 50)
    print("All MCP client tests passed! ✓")
    print("=" * 50)
