"""
MCP Client using langchain_mcp_adapters.

Provides a wrapper around MultiServerMCPClient with backward-compatible interface
for the orbit-agent.
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Optional

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.config import settings

logger = logging.getLogger(__name__)

_BLOCKED_TOOLS = {"start_google_auth"}
GOOGLE_MCP_CREDENTIALS_DIR = Path(
    os.getenv("GOOGLE_MCP_CREDENTIALS_DIR", settings.GOOGLE_MCP_CREDENTIALS_DIR)
)


class MCPClientError(Exception):
    """Exception raised when MCP client operations fail."""

    pass


def _sanitize_tool_schema(schema: dict) -> dict:
    """
    Sanitize tool schema to remove unsupported JSON Schema features.

    LangChain/Pydantic may not support all JSON Schema features, so we
    clean up the schema to ensure compatibility.

    Args:
        schema: Original tool schema

    Returns:
        Sanitized schema
    """
    if not isinstance(schema, dict):
        return schema

    sanitized = {}
    for key, value in schema.items():
        if key == "$schema":
            # Remove $schema directive
            continue
        elif key == "additionalProperties":
            # Convert boolean to appropriate form or remove
            if isinstance(value, bool):
                sanitized[key] = value
            else:
                sanitized[key] = True
        elif key == "properties" and isinstance(value, dict):
            # Recursively sanitize properties
            sanitized[key] = {
                k: _sanitize_tool_schema(v) for k, v in value.items()
            }
        elif key == "items" and isinstance(value, dict):
            # Sanitize items schema
            sanitized[key] = _sanitize_tool_schema(value)
        elif key == "default":
            # Keep defaults as-is
            sanitized[key] = value
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_tool_schema(value)
        elif isinstance(value, list):
            sanitized[key] = [
                _sanitize_tool_schema(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


class MCPClientManager:
    """
    Wrapper around MultiServerMCPClient with backward-compatible interface.

    Provides the same interface as the original MCPClientManager but uses
    langchain_mcp_adapters for actual MCP communication.
    """

    def __init__(self):
        self._client: Optional[MultiServerMCPClient] = None
        self._tools: list[BaseTool] = []
        self._initialized = False
        self._tools_by_server: dict[str, list[str]] = {}

    async def initialize_servers(self) -> bool:
        """
        Initialize MCP servers and discover tools.

        Returns:
            True if at least one server initialized successfully, False otherwise
        """
        try:
            servers = self._build_server_configs()

            if not servers:
                logger.warning("No MCP servers configured")
                return False

            self._client = self._create_client(servers)
            self._tools = await self._load_tools_with_retry()
            self._initialized = True

            # Build tools index by server
            self._tools_by_server = {}
            for tool in self._tools:
                # Try to determine server from tool name prefix or metadata
                server_name = self._get_server_for_tool(tool.name)
                if server_name not in self._tools_by_server:
                    self._tools_by_server[server_name] = []
                self._tools_by_server[server_name].append(tool.name)

            logger.info(f"Loaded {len(self._tools)} MCP tools from {len(servers)} servers")
            return True

        except Exception as e:
            logger.error(f"MCP initialization failed: {e}")
            return False

    async def shutdown_servers(self) -> None:
        """Cleanup MCP servers and release resources."""
        self._client = None
        self._tools = []
        self._initialized = False
        self._tools_by_server = {}
        logger.info("MCP servers shut down")

    async def execute_tool(self, server_name: str, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool via MCP.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to execute
            **kwargs: Tool arguments

        Returns:
            Tool execution result

        Raises:
            MCPClientError: If execution fails
        """
        if not self._initialized or not self._client:
            raise MCPClientError("MCP client not initialized")

        # Find the tool by name
        for tool in self._tools:
            if tool.name == tool_name:
                try:
                    logger.info(f"Executing MCP tool '{tool_name}' with args: {kwargs}")
                    result = await tool.ainvoke(kwargs)
                    return result
                except Exception as e:
                    logger.error(f"Tool execution failed: {e}")
                    raise MCPClientError(f"Tool execution failed: {e}")

        raise MCPClientError(f"Tool '{tool_name}' not found")

    def get_tools(self) -> list[BaseTool]:
        """Get all loaded LangChain tools."""
        return self._tools

    def get_available_tools(self, server_name: Optional[str] = None) -> list[dict]:
        """
        Get list of available tools.

        Args:
            server_name: Optional server name to filter by

        Returns:
            List of tool definitions in MCP format
        """
        if server_name:
            tool_names = self._tools_by_server.get(server_name, [])
            return [
                {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": _sanitize_tool_schema(t.args_schema.model_json_schema() if t.args_schema else {}),
                }
                for t in self._tools if t.name in tool_names
            ]

        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": _sanitize_tool_schema(t.args_schema.model_json_schema() if t.args_schema else {}),
            }
            for t in self._tools
        ]

    def is_server_connected(self, server_name: str) -> bool:
        """Check if a server is connected."""
        return self._initialized and server_name in self._tools_by_server

    def is_server_initialized(self, server_name: str) -> bool:
        """Check if a server is initialized and connected."""
        return self.is_server_connected(server_name)

    def get_all_tool_names(self) -> list[str]:
        """Get all registered tool names."""
        return [t.name for t in self._tools]

    def get_tool_info(self, server_name: str, tool_name: str) -> Optional[dict]:
        """Get detailed information about a specific tool."""
        for tool in self._tools:
            if tool.name == tool_name:
                return {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": _sanitize_tool_schema(tool.args_schema.model_json_schema() if tool.args_schema else {}),
                }
        return None

    def _build_server_configs(self) -> dict:
        """Build server configurations from settings."""
        servers = {}

        # Google Workspace MCP
        if settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET:
            GOOGLE_MCP_CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

            workspace_env = os.environ.copy()
            workspace_env.update({
                "GOOGLE_CLIENT_ID": settings.GOOGLE_OAUTH_CLIENT_ID,
                "GOOGLE_CLIENT_SECRET": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                "GOOGLE_MCP_CREDENTIALS_DIR": str(GOOGLE_MCP_CREDENTIALS_DIR),
            })

            # Tools to enable
            ws_tools = ["--single-user", "--tools", "gmail", "drive", "calendar", "docs", "sheets"]

            # Check if workspace-mcp is installed globally
            if shutil.which("workspace-mcp"):
                ws_cmd, ws_args = "workspace-mcp", ws_tools
            else:
                # Use uv tool run as fallback
                ws_cmd, ws_args = "uv", ["tool", "run", "workspace-mcp@1.11.1"] + ws_tools

            servers["google_workspace"] = {
                "transport": "stdio",
                "command": ws_cmd,
                "args": ws_args,
                "env": workspace_env,
                "cwd": "/tmp",
            }

        # Tavily MCP
        if settings.TAVILY_API_KEY:
            tavily_env = os.environ.copy()
            tavily_env["TAVILY_API_KEY"] = settings.TAVILY_API_KEY

            # Check if tavily-mcp is installed globally
            if shutil.which("tavily-mcp"):
                t_cmd, t_args = "tavily-mcp", []
            else:
                # Use npx as fallback
                t_cmd, t_args = "npx", ["-y", "tavily-mcp@0.2.17"]

            servers["tavily"] = {
                "transport": "stdio",
                "command": t_cmd,
                "args": t_args,
                "env": tavily_env,
            }

        return servers

    def _create_client(self, servers: dict) -> MultiServerMCPClient:
        """Create MultiServerMCPClient with given server configs."""
        return MultiServerMCPClient(servers)

    async def _load_tools_with_retry(
        self,
        retries: int = 3,
        base_delay: float = 1.0
    ) -> list[BaseTool]:
        """
        Load tools from MCP servers with retry logic.

        Args:
            retries: Number of retry attempts
            base_delay: Base delay for exponential backoff

        Returns:
            List of LangChain tools

        Raises:
            MCPClientError: If all retries fail
        """
        last_error = None

        for attempt in range(retries):
            try:
                # Get tools from MultiServerMCPClient
                tools = self._client.get_tools()

                # Filter out blocked tools and sanitize schemas
                filtered_tools = []
                for tool in tools:
                    if tool.name in _BLOCKED_TOOLS:
                        logger.info(f"Skipping blocked tool: {tool.name}")
                        continue

                    # Sanitize the tool's args_schema if present
                    if hasattr(tool, 'args_schema') and tool.args_schema:
                        try:
                            schema = tool.args_schema.model_json_schema()
                            sanitized = _sanitize_tool_schema(schema)
                            # The schema is read-only, but we've validated it works
                            logger.debug(f"Tool '{tool.name}' schema validated")
                        except Exception as e:
                            logger.warning(f"Could not validate schema for tool '{tool.name}': {e}")

                    filtered_tools.append(tool)

                return filtered_tools

            except Exception as e:
                last_error = e
                if attempt < retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Tool loading attempt {attempt + 1} failed, "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)

        raise MCPClientError(
            f"Tool loading failed after {retries} attempts: {last_error}"
        )

    def _get_server_for_tool(self, tool_name: str) -> str:
        """
        Determine which server a tool belongs to.

        Args:
            tool_name: Name of the tool

        Returns:
            Server name (defaults to 'unknown')
        """
        # Common tool prefixes that indicate their server
        if any(prefix in tool_name.lower() for prefix in ["gmail", "drive", "calendar", "docs", "sheets", "google"]):
            return "google_workspace"
        if any(prefix in tool_name.lower() for prefix in ["tavily", "search", "crawl", "extract"]):
            return "tavily"

        return "unknown"

    async def get_wrapped_tools(self, server_name: str) -> list:
        """
        Get tools from a server wrapped as MCPToolWrapper instances.

        Args:
            server_name: Name of the server

        Returns:
            List of MCPToolWrapper instances
        """
        from src.tools.mcp_wrapper import wrap_mcp_tools

        tools_data = self.get_available_tools(server_name)
        return wrap_mcp_tools(server_name, tools_data, self)


# Global MCP client manager instance
_mcp_client_manager: Optional[MCPClientManager] = None


def get_mcp_client() -> MCPClientManager:
    """
    Get the global MCP client manager instance.

    Returns:
        MCPClientManager singleton instance
    """
    global _mcp_client_manager
    if _mcp_client_manager is None:
        _mcp_client_manager = MCPClientManager()
    return _mcp_client_manager
