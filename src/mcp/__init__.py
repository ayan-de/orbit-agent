"""
MCP (Model Context Protocol) Client Module

This module provides client functionality for connecting to and interacting with MCP servers.
MCP servers provide standardized tool interfaces for external services.
"""

from .client import MCPClientManager, get_mcp_client
from .config import MCPServerConfig, get_mcp_server_config

__all__ = [
    "MCPClientManager",
    "get_mcp_client",
    "MCPServerConfig",
    "get_mcp_server_config",
]
