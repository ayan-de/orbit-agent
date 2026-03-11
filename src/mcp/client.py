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


# Keys that some LLMs (especially Gemini) don't support in function-calling API
_UNSUPPORTED_SCHEMA_KEYS = frozenset({"additionalProperties", "$schema"})


def sanitize_tool_schema(schema: dict) -> dict:
    """
    Recursively sanitize a tool schema for LLM compatibility.

    Handles issues that cause problems with Gemini, Claude, and OpenAI:
    - Removes null values at any nesting level
    - Simplifies anyOf/oneOf validators to first non-null type
    - Strips unsupported keys ($schema, additionalProperties)
    - Removes properties with None values
    - Handles empty required arrays

    Args:
        schema: Original JSON Schema dict

    Returns:
        Sanitized schema compatible with all major LLMs
    """
    if not isinstance(schema, dict):
        return schema

    sanitized = {}
    for key, value in schema.items():
        # Skip null values - some LLMs don't accept them
        if value is None:
            continue

        # Strip keys unsupported by some LLMs (Gemini in particular)
        if key in _UNSUPPORTED_SCHEMA_KEYS:
            continue

        # Handle anyOf/oneOf: pick the first non-null type definition
        if key in ("anyOf", "oneOf"):
            if isinstance(value, list) and value:
                for item in value:
                    if isinstance(item, dict):
                        # Skip "null" type definitions
                        if item.get("type") == "null":
                            continue
                        # Use the first valid type definition
                        sanitized_item = sanitize_tool_schema(item)
                        if sanitized_item:
                            # Merge the first valid definition into parent
                            for k, v in sanitized_item.items():
                                if k not in sanitized:
                                    sanitized[k] = v
                            break
            continue

        # Recursively sanitize properties
        if key == "properties" and isinstance(value, dict):
            sanitized_props = {}
            for prop_name, prop_value in value.items():
                if prop_value is None:
                    continue
                if isinstance(prop_value, dict):
                    sanitized_prop = sanitize_tool_schema(prop_value)
                    if sanitized_prop:
                        sanitized_props[prop_name] = sanitized_prop
                else:
                    sanitized_props[prop_name] = prop_value
            if sanitized_props:
                sanitized[key] = sanitized_props
            continue

        # Recursively sanitize nested dicts
        if isinstance(value, dict):
            sanitized_value = sanitize_tool_schema(value)
            if sanitized_value:  # Only add if not empty
                sanitized[key] = sanitized_value
            continue

        # Recursively sanitize list items
        if isinstance(value, list):
            sanitized_list = [
                sanitize_tool_schema(item) if isinstance(item, dict) else item
                for item in value
                if item is not None
            ]
            if sanitized_list or key == "required":  # Keep required even if empty
                sanitized[key] = sanitized_list
            continue

        # Keep other values as-is
        sanitized[key] = value

    return sanitized


def sanitize_tool(tool: BaseTool) -> BaseTool:
    """
    Sanitize a tool's schema for LLM compatibility.

    Args:
        tool: LangChain BaseTool instance

    Returns:
        The same tool (schema is validated but tools are immutable)
    """
    try:
        if hasattr(tool, "args_schema") and tool.args_schema:
            # Handle both Pydantic models and plain dicts
            if isinstance(tool.args_schema, dict):
                schema = tool.args_schema
            elif hasattr(tool.args_schema, "model_json_schema"):
                schema = tool.args_schema.model_json_schema()
            else:
                return tool

            sanitized = sanitize_tool_schema(schema)
            if schema != sanitized:
                logger.debug(f"Sanitized schema for tool: {tool.name}")
    except Exception as e:
        logger.warning(f"Could not sanitize tool {tool.name}: {e}")

    return tool


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
            raise MCPClientError(
                "MCP client not initialized. "
                "Ensure MCP servers are enabled and configured."
            )

        # Find the tool by name
        for tool in self._tools:
            if tool.name == tool_name:
                try:
                    logger.info(f"Executing MCP tool '{tool_name}' with args: {kwargs}")
                    result = await tool.ainvoke(kwargs)
                    return result
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"MCP tool '{tool_name}' failed: {error_msg}")

                    # Provide helpful error context
                    if "auth" in error_msg.lower() or "unauthorized" in error_msg.lower():
                        raise MCPClientError(
                            f"Authentication required for '{tool_name}'. "
                            f"Please connect the {server_name} integration."
                        )
                    elif "not found" in error_msg.lower():
                        raise MCPClientError(
                            f"Resource not found in {server_name}: {error_msg}"
                        )
                    elif "timeout" in error_msg.lower():
                        raise MCPClientError(
                            f"Tool '{tool_name}' timed out. "
                            f"The {server_name} server may be slow or unresponsive."
                        )
                    else:
                        raise MCPClientError(
                            f"Tool '{tool_name}' execution failed: {error_msg}"
                        )

        # Tool not found - provide suggestions
        available_tools = [t.name for t in self._tools]
        suggestions = [t for t in available_tools if tool_name.lower() in t.lower()][:3]

        suggestion_text = ""
        if suggestions:
            suggestion_text = f" Did you mean: {', '.join(suggestions)}?"

        raise MCPClientError(
            f"Tool '{tool_name}' not found.{suggestion_text} "
            f"Available MCP tools: {available_tools[:10]}{'...' if len(available_tools) > 10 else ''}"
        )

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
                    "inputSchema": sanitize_tool_schema(t.args_schema.model_json_schema() if t.args_schema else {}),
                }
                for t in self._tools if t.name in tool_names
            ]

        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": sanitize_tool_schema(t.args_schema.model_json_schema() if t.args_schema else {}),
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
                    "inputSchema": sanitize_tool_schema(tool.args_schema.model_json_schema() if tool.args_schema else {}),
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

                    # Sanitize the tool's schema for LLM compatibility
                    sanitize_tool(tool)
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

    # =========================================================================
    # Phase 1: IntegrationRegistry Connection
    # =========================================================================

    # Mapping of MCP server names to integration names (fallback)
    SERVER_TO_INTEGRATION: dict[str, str] = {
        "google_workspace": "gmail",  # Default fallback
        "tavily": "web_search",
    }

    # Mapping of tool name prefixes to integration names
    # Must match integration names in integration_config.yaml
    TOOL_PREFIX_TO_INTEGRATION: dict[str, str] = {
        # Gmail tools
        "gmail": "gmail",
        "search_gmail": "gmail",
        "send_gmail": "gmail",
        "list_gmail": "gmail",
        "get_gmail": "gmail",
        "draft_gmail": "gmail",
        "batch_modify_gmail": "gmail",
        # Google Drive tools
        "drive": "google_drive",
        "search_drive": "google_drive",
        "list_drive": "google_drive",
        "get_drive": "google_drive",
        "create_drive": "google_drive",
        "share_drive": "google_drive",
        "download_drive": "google_drive",
        # Google Docs tools
        "docs": "google_docs",
        "create_doc": "google_docs",
        "get_doc": "google_docs",
        "modify_doc": "google_docs",
        "append_doc": "google_docs",
        "delete_doc": "google_docs",
        # Google Sheets tools
        "sheet": "google_sheets",
        "spreadsheet": "google_sheets",
        "create_spreadsheet": "google_sheets",
        "read_sheet": "google_sheets",
        "modify_sheet": "google_sheets",
        "append_sheet": "google_sheets",
        "clear_sheet": "google_sheets",
        # Google Calendar tools
        "calendar": "google_calendar",
        "event": "google_calendar",
        "list_calendar": "google_calendar",
        "get_event": "google_calendar",
        "create_event": "google_calendar",
        "update_event": "google_calendar",
        "delete_event": "google_calendar",
        # Tavily tools
        "tavily": "web_search",
        "crawl": "web_search",
        "extract": "web_search",
    }

    def get_integration_for_tool(self, tool_name: str) -> str:
        """
        Determine which integration a tool belongs to.

        Args:
            tool_name: Name of the tool

        Returns:
            Integration name (defaults to 'unknown')
        """
        tool_lower = tool_name.lower()

        # Check prefixes
        for prefix, integration in self.TOOL_PREFIX_TO_INTEGRATION.items():
            if tool_lower.startswith(prefix):
                return integration

        return "unknown"

    def register_tools_with_integration_registry(self, registry: Any) -> int:
        """
        Register all loaded MCP tools with the IntegrationRegistry.

        This is the key connection point between MCP tools and the
        integration system used by smart_router and executor.

        Args:
            registry: IntegrationRegistry instance

        Returns:
            Number of tools registered
        """
        if not self._initialized:
            logger.warning("Cannot register tools: MCP client not initialized")
            return 0

        registered_count = 0

        for tool in self._tools:
            # Determine which integration this tool belongs to
            integration_name = self.get_integration_for_tool(tool.name)

            if integration_name == "unknown":
                # Try server mapping as fallback
                server_name = self._get_server_for_tool(tool.name)
                integration_name = self.SERVER_TO_INTEGRATION.get(server_name, "unknown")

            if integration_name != "unknown":
                registry.register_tool(integration_name, tool)
                registered_count += 1
                logger.debug(f"Registered MCP tool '{tool.name}' → integration '{integration_name}'")
            else:
                logger.warning(f"Could not map MCP tool '{tool.name}' to any integration")

        logger.info(f"Registered {registered_count}/{len(self._tools)} MCP tools with IntegrationRegistry")
        return registered_count


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
