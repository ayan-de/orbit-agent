"""
MCP (Model Context Protocol) Client Manager

Manages connections to MCP servers and provides tool execution capabilities.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

import httpx

from .config import MCPServerConfig, get_mcp_server_config

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

    async def close(self):
        """Close all connections and HTTP client."""
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
        from src.config import settings

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

            # For SSE transport (Server-Sent Events) or HTTP endpoint
            if config.transport == "sse" or config.url.startswith("http"):
                connection = await self._connect_http(config)
            # For stdio transport (command-line)
            elif config.transport == "stdio":
                connection = await self._connect_stdio(config)
            else:
                raise MCPClientError(f"Unsupported transport: {config.transport}")

            self._connections[server_name] = connection

            # Discover tools from the server
            await self._discover_tools(server_name)

            logger.info(f"Successfully connected to MCP server '{server_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{server_name}': {e}")
            raise MCPClientError(f"Connection failed: {str(e)}")

    async def _connect_http(self, config: MCPServerConfig) -> Dict[str, Any]:
        """
        Connect to MCP server using HTTP/SSE transport.

        For Tavily, we use the SSE endpoint with the API key.

        Args:
            config: Server configuration

        Returns:
            Connection object
        """
        client = self._get_http_client()

        # Use the URL directly (for Tavily, it includes the API key)
        url = config.url

        # Test connection by sending a ping/initialize request
        try:
            response = await client.post(
                url,
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

            logger.info(f"Successfully connected to MCP server via HTTP/SSE")

            return {
                "transport": "http",
                "url": url,
                "client": client,
                "initialized": True
            }

        except httpx.HTTPStatusError as e:
            raise MCPClientError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise MCPClientError(f"Connection error: {str(e)}")

    async def _connect_stdio(self, config: MCPServerConfig) -> Dict[str, Any]:
        """
        Connect to MCP server using stdio transport.

        Args:
            config: Server configuration

        Returns:
            Connection object
        """
        # Note: This is a placeholder implementation
        # In production, spawn the subprocess and communicate via stdio
        logger.debug(f"Simulating stdio connection to {config.url}")
        return {"transport": "stdio", "url": config.url}

    async def _send_request(
        self,
        server_name: str,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a JSON-RPC request to an MCP server.

        Args:
            server_name: Name of the server
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
            tools = []

            if server_name == "tavily":
                tools = [
                    {
                        "name": "search",
                        "description": "Search the web using Tavily",
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

            logger.info(f"Using fallback tools for '{server_name}'")

    async def execute_tool(
        self, server_name: str, tool_name: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a tool on an MCP server.

        Args:
            server_name: Name of the server
            tool_name: Name of the tool to execute
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
            # Call the tool using MCP protocol
            result = await self._send_request(
                server_name,
                f"tools/call",
                {
                    "name": tool_name,
                    "arguments": kwargs
                }
            )

            # Extract the content from the result
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
                k: v for k, v in self._tools.items() if v["server"] != server_name
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
                if v["server"] == server_name
            ]
        return [v["tool"] for v in self._tools.values()]

    def is_server_connected(self, server_name: str) -> bool:
        """Check if a server is connected."""
        return server_name in self._connections


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
