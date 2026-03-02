"""
MCP Server Configuration

Defines configuration for MCP (Model Context Protocol) servers.
"""

from typing import Dict, Optional, Any
from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    name: str = Field(..., description="Unique name for this MCP server")
    url: str = Field(..., description="URL or connection string for the server")
    transport: str = Field(default="sse", description="Transport protocol: sse, stdio, or http")
    enabled: bool = Field(default=True, description="Whether this server is enabled")
    timeout: int = Field(default=30, description="Connection timeout in seconds")
    env: Optional[Dict[str, str]] = Field(
        default=None, description="Environment variables to pass to the server"
    )
    args: Optional[list[str]] = Field(
        default=None, description="Command-line arguments for stdio transport"
    )


class MCPServersConfig(BaseModel):
    """Configuration for all MCP servers."""

    servers: Dict[str, MCPServerConfig] = Field(
        default_factory=dict, description="Map of server name to config"
    )


def get_default_tavily_config() -> MCPServerConfig:
    """
    Get default Tavily MCP server configuration from environment.

    Returns:
        MCPServerConfig for Tavily
    """
    try:
        from src.config import settings
        api_key = settings.TAVILY_API_KEY or ""
        # Construct URL with API key
        url = f"https://mcp.tavily.com/mcp/?tavilyApiKey={api_key}"
    except Exception:
        # Fallback if settings not available
        url = "https://mcp.tavily.com/mcp/"

    return MCPServerConfig(
        name="tavily",
        url=url,
        transport="http",
        enabled=True,
        timeout=30,
    )


# Default MCP server configurations
DEFAULT_SERVERS: Dict[str, MCPServerConfig] = {
    "tavily": get_default_tavily_config(),
}


def get_mcp_server_config(
    server_name: str, custom_config: Optional[MCPServersConfig] = None
) -> Optional[MCPServerConfig]:
    """
    Get MCP server configuration by name.

    Args:
        server_name: Name of the server to get config for
        custom_config: Custom configuration (uses defaults if not provided)

    Returns:
        MCPServerConfig or None if not found
    """
    servers = custom_config.servers if custom_config else DEFAULT_SERVERS
    return servers.get(server_name)


def get_all_mcp_server_configs(
    custom_config: Optional[MCPServersConfig] = None,
) -> Dict[str, MCPServerConfig]:
    """
    Get all MCP server configurations.

    Args:
        custom_config: Custom configuration (uses defaults if not provided)

    Returns:
        Dictionary of server name to config
    """
    servers = custom_config.servers if custom_config else DEFAULT_SERVERS
    return {name: config for name, config in servers.items() if config.enabled}
