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


def get_default_google_workspace_config() -> MCPServerConfig:
    """
    Get default Google Workspace MCP server configuration from environment.

    Returns:
        MCPServerConfig for Google Workspace
    """
    from src.config import settings

    # Get configuration from settings
    client_id = settings.GOOGLE_OAUTH_CLIENT_ID or ""
    client_secret = settings.GOOGLE_OAUTH_CLIENT_SECRET or ""

    # For local development, use localhost
    # For production, this would be the MCP server URL
    base_uri = settings.WORKSPACE_MCP_BASE_URI or "http://localhost"
    port = settings.WORKSPACE_MCP_PORT or "8000"
    host = settings.WORKSPACE_MCP_HOST or "0.0.0.0"

    url = f"{base_uri}:{host}:{port}/mcp"

    # Prepare environment variables for MCP server
    env_vars = {
        "GOOGLE_OAUTH_CLIENT_ID": client_id,
        "GOOGLE_OAUTH_CLIENT_SECRET": client_secret,
    }

    # Check if OAuth 2.1 external provider mode is enabled
    if settings.MCP_ENABLE_OAUTH21:
        env_vars["MCP_ENABLE_OAUTH21"] = "true"
    if settings.EXTERNAL_OAUTH21_PROVIDER:
        env_vars["EXTERNAL_OAUTH21_PROVIDER"] = "true"
    if settings.OAUTHLIB_INSECURE_TRANSPORT:
        env_vars["OAUTHLIB_INSECURE_TRANSPORT"] = settings.OAUTHLIB_INSECURE_TRANSPORT

    return MCPServerConfig(
        name="google_workspace",
        url=url,
        transport="http",
        enabled=True,
        timeout=30,
        env=env_vars,
    )


# Default MCP server configurations
DEFAULT_SERVERS: Dict[str, MCPServerConfig] = {
    "tavily": get_default_tavily_config(),
    "google_workspace": get_default_google_workspace_config(),
}


def update_server_from_settings(server_name: str, url: str, enabled: bool = True) -> MCPServerConfig:
    """
    Update or add a server configuration from settings.

    Args:
        server_name: Name of the server
        url: Server URL or connection string
        enabled: Whether the server is enabled

    Returns:
        Updated or created server config
    """
    servers = DEFAULT_SERVERS.copy()

    if enabled:
        servers[server_name] = MCPServerConfig(
            name=server_name,
            url=url,
            transport="http" if url.startswith("http") else "sse",
            enabled=enabled,
            timeout=30,
        )
    else:
        # If disabled, remove from defaults
        if server_name in servers:
            del servers[server_name]

    return servers[server_name]


def get_all_servers() -> Dict[str, MCPServerConfig]:
    """
    Get all MCP server configurations, including overrides from settings.

    Returns:
        Dictionary of server name to config
    """
    from src.config import settings

    # Start with defaults
    servers = DEFAULT_SERVERS.copy()

    # Override with settings.MCP_SERVERS if provided
    if settings.MCP_SERVERS:
        for server_name, url in settings.MCP_SERVERS.items():
            if url:  # Only override if URL is provided
                servers[server_name] = MCPServerConfig(
                    name=server_name,
                    url=url,
                    transport="http" if url.startswith("http") else "sse",
                    enabled=True,
                    timeout=settings.MCP_SERVER_TIMEOUT or 30,
                )

    # Return only enabled servers
    return {name: config for name, config in servers.items() if config.enabled}


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
