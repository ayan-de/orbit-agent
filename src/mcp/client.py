"""
MCP (Model Context Protocol) Client Manager

Manages connections to MCP servers and provides tool execution capabilities.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List

import httpx

from .config import get_all_servers, update_server_from_settings
from src.config import settings

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """Exception raised when MCP client operations fail."""

    pass


class MCPClientManager:
    """
    Manager for MCP server connections and tool execution.

    Handles connection lifecycle, tool discovery, and execution across MCP servers.
    """

    def __init__(self):
        self._connections: Dict[str, Any] = {}
        self._tools: Dict[str, Any] = {}
        self._request_id = 0
        self._http_client: Optional[httpx.AsyncClient] = None

    def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def initialize_servers(self) -> bool:
        """
        Initialize all enabled MCP servers from configuration.

        This ensures that servers are configured and ready before use.

        Returns:
            True if at least one server initialized, False otherwise
        """
        servers = get_all_servers()

        if not servers:
            logger.warning("No MCP servers configured")
            return False

        initialized_count = 0
        for server_name, server_config in servers.items():
            try:
                logger.info(f"Initializing MCP server: {server_name}")
                await self.connect_server(server_name)
                initialized_count += 1
            except Exception as e:
                logger.error(f"Failed to initialize MCP server '{server_name}': {e}")
                # Continue with other servers

        logger.info(f"Initialized {initialized_count}/{len(servers)} MCP servers")
        return initialized_count > 0

    async def shutdown_servers(self):
        """
        Shutdown all MCP server connections.

        Called during application shutdown to clean up connections.
        """
        for server_name in list(self._connections.keys()):
            try:
                await self.disconnect_server(server_name)
                logger.info(f"Shut down MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Error shutting down MCP server '{server_name}': {e}")

        # Close HTTP client
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def connect_server(self, server_name: str) -> bool:
        """
        Connect to an MCP server.

        Args:
            server_name: Name of the server to connect to

        Returns:
            True if connection successful, False otherwise

        Raises:
            MCPClientError: If connection fails
        """
        from .config import get_mcp_server_config

        if server_name in self._connections:
            logger.info(f"MCP server '{server_name}' already connected")
            return True

        config = get_mcp_server_config(server_name)
        if not config:
            raise MCPClientError(f"No configuration found for server: {server_name}")

        if not config.enabled:
            logger.warning(f"MCP server '{server_name}' is disabled")
            return False

        try:
            logger.info(f"Connecting to MCP server '{server_name}' at {config.url}")

            # For HTTP/SSE transport
            client = self._get_http_client()

            # Test connection by sending initialize request
            response = await client.post(
                config.url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "orbit-agent",
                            "version": "1.0.0"
                        }
                    }
                },
                timeout=config.timeout
            )
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                raise MCPClientError(f"Initialize failed: {result['error']}")

            logger.info(f"Successfully connected to MCP server '{server_name}' via HTTP/SSE")

            # Store connection with client
            self._connections[server_name] = {
                "transport": "http",
                "url": config.url,
                "client": client,
                "initialized": True,
                "timeout": config.timeout,
            }

            # Discover tools from the server
            await self._discover_tools(server_name)

            logger.info(f"Successfully connected to MCP server '{server_name}'")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error connecting to MCP server '{server_name}': {e.response.status_code} - {e.response.text}")
            raise MCPClientError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{server_name}': {e}")
            raise MCPClientError(f"Connection failed: {str(e)}")

    async def _send_request(
        self,
        server_name: str,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a JSON-RPC request to an MCP server.

        Args:
            server_name: Name of server
            method: RPC method name
            params: Method parameters

        Returns:
            Response data

        Raises:
            MCPClientError: If request fails
        """
        connection = self._connections.get(server_name)
        if not connection:
            raise MCPClientError(f"Server '{server_name}' not connected")

        client = connection.get("client")
        url = connection.get("url")

        if not client:
            raise MCPClientError(f"No client available for server '{server_name}'")

        self._request_id += 1

        try:
            response = await client.post(
                url,
                json={
                    "jsonrpc": "2.0",
                    "id": self._request_id,
                    "method": method,
                    "params": params or {}
                },
                timeout=connection.get("timeout", 30)
            )
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                raise MCPClientError(f"RPC error: {result['error']}")

            return result.get("result", {})

        except httpx.HTTPStatusError as e:
            raise MCPClientError(f"HTTP error: {e.response.status_code}")
        except Exception as e:
            raise MCPClientError(f"Request error: {str(e)}")

    async def _discover_tools(self, server_name: str):
        """
        Discover available tools from an MCP server.

        Args:
            server_name: Name of the server to discover tools from
        """
        logger.info(f"Discovering tools from MCP server '{server_name}'")

        try:
            # List tools using MCP protocol
            result = await self._send_request(server_name, "tools/list")

            tools = result.get("tools", [])

            for tool in tools:
                tool_key = f"{server_name}.{tool.get('name', 'unknown')}"
                self._tools[tool_key] = {
                    "server": server_name,
                    "tool": tool,
                }

            logger.info(
                f"Discovered {len(tools)} tools from MCP server '{server_name}': "
                f"{[t.get('name', 'unknown') for t in tools]}"
            )

        except Exception as e:
            logger.warning(f"Failed to discover tools from '{server_name}': {e}")
            # Fallback to mock tools if discovery fails
            self._use_fallback_tools(server_name)

    def _use_fallback_tools(self, server_name: str):
        """
        Use fallback tool definitions when MCP discovery fails.

        Args:
            server_name: Name of the server
        """
        logger.warning(f"Using fallback tools for '{server_name}'")

        # Mock tools for Tavily
        if server_name == "tavily":
            tools = [
                {
                    "name": "search",
                    "description": "Search web using Tavily",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "max_results": {"type": "integer", "default": 10},
                            "search_depth": {"type": "string", "default": "basic"},
                            "include_domains": {"type": "array", "items": {"type": "string"}},
                            "exclude_domains": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                {
                    "name": "search_news",
                    "description": "Search for news using Tavily",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "max_results": {"type": "integer", "default": 10},
                            "days": {"type": "integer", "default": 3},
                        },
                    },
                },
            ]

            for tool in tools:
                tool_key = f"{server_name}.{tool['name']}"
                self._tools[tool_key] = {
                    "server": server_name,
                    "tool": tool,
                }

            logger.info(f"Loaded {len(tools)} fallback tools for '{server_name}'")

    async def execute_tool(
        self, server_name: str, tool_name: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a tool on an MCP server.

        Args:
            server_name: Name of server
            tool_name: Name of tool to execute
            **kwargs: Tool parameters

        Returns:
            Tool execution result

        Raises:
            MCPClientError: If execution fails
        """
        tool_key = f"{server_name}.{tool_name}"

        if tool_key not in self._tools:
            raise MCPClientError(f"Tool '{tool_name}' not found on server '{server_name}'")

        if server_name not in self._connections:
            raise MCPClientError(f"Server '{server_name}' not connected")

        logger.info(
            f"Executing tool '{tool_name}' on server '{server_name}' with args: {kwargs}"
        )

        try:
            # Call tool using MCP protocol
            result = await self._send_request(
                server_name,
                f"tools/call",
                {
                    "name": tool_name,
                    "arguments": kwargs
                }
            )

            # Extract content from the result
            content = result.get("content", [])
            if content and isinstance(content, list):
                # First content item is typically the result
                first_content = content[0]
                if isinstance(first_content, dict):
                    result_data = first_content
                else:
                    result_data = {"text": str(first_content)}

                return {
                    "success": True,
                    "data": result_data
                }

            return {
                "success": True,
                "data": result
            }

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise MCPClientError(f"Execution failed: {str(e)}")

    async def disconnect_server(self, server_name: str) -> bool:
        """
        Disconnect from an MCP server.

        Args:
            server_name: Name of the server to disconnect from

        Returns:
            True if disconnection successful
        """
        if server_name not in self._connections:
            logger.warning(f"MCP server '{server_name}' not connected")
            return False

        try:
            logger.info(f"Disconnecting from MCP server '{server_name}'")

            # Clean up connection
            del self._connections[server_name]
            # Remove tools from this server
            self._tools = {
                k: v for k, v in self._tools.items()
                if v.get("server") != server_name
            }

            logger.info(f"Disconnected from MCP server '{server_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to disconnect from server '{server_name}': {e}")
            return False

    def get_available_tools(self, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of available tools.

        Args:
            server_name: Optional server name to filter by

        Returns:
            List of tool definitions
        """
        if server_name:
            return [
                v["tool"]
                for k, v in self._tools.items()
                if v.get("server") == server_name
            ]
        return [v["tool"] for v in self._tools.values()]

    def is_server_connected(self, server_name: str) -> bool:
        """Check if a server is connected."""
        return server_name in self._connections

    def is_server_initialized(self, server_name: str) -> bool:
        """Check if a server is initialized and connected."""
        connection = self._connections.get(server_name)
        return connection is not None and connection.get("initialized", False)


# Global MCP client manager instance
_mcp_client_manager: Optional[MCPClientManager] = None


def get_mcp_client() -> MCPClientManager:
    """
    Get the global MCP client manager instance.

    Returns:
        MCPClientManager instance
    """
    global _mcp_client_manager
    if _mcp_client_manager is None:
        _mcp_client_manager = MCPClientManager()
    return _mcp_client_manager
