"""
Integration Registry for managing MCP tools.

Pre-warms and caches MCP tools at startup for instant access.
"""

import logging
from pathlib import Path
from typing import Optional

from langchain_core.tools import BaseTool

from src.integrations.config import IntegrationConfig, load_integration_configs

logger = logging.getLogger(__name__)


class IntegrationRegistry:
    """
    Singleton registry for managing MCP integration tools.

    Pre-warms tools at startup for fast retrieval during requests.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self._configs: dict[str, IntegrationConfig] = {}
        self._tools_by_integration: dict[str, list[BaseTool]] = {}
        self._all_tools: list[BaseTool] = []
        self._tool_to_integration: dict[str, str] = {}
        self._initialized = False
        self._config_path = config_path

    async def load_all(self, tokens: Optional[dict] = None) -> None:
        """
        Pre-warm all MCP integrations at startup.

        Args:
            tokens: Optional dict of integration_name -> auth_token
        """
        if self._initialized:
            logger.info("Registry already initialized")
            return

        # Load configs from YAML
        self._configs = load_integration_configs(self._config_path)
        logger.info(f"Loaded {len(self._configs)} integration configs")

        # Initialize tool containers for each integration
        for name, config in self._configs.items():
            self._tools_by_integration[name] = []
            for tool_name in config.tool_names:
                self._tool_to_integration[tool_name] = name

        self._initialized = True
        logger.info(f"Integration registry initialized with {len(self._configs)} integrations")

    async def load_missing_servers(self, tokens: dict) -> None:
        """
        Incrementally load servers for newly available tokens.

        Args:
            tokens: Dict of integration_name -> auth_token
        """
        for integration_name, token in tokens.items():
            if integration_name not in self._tools_by_integration:
                logger.info(f"Loading newly available integration: {integration_name}")
                # Would trigger MCP server connection here
                self._tools_by_integration[integration_name] = []

    def get_toolset(self, integrations: list[str]) -> list[BaseTool]:
        """
        Get tools for specified integrations (instant O(1) lookup).

        Args:
            integrations: List of integration names

        Returns:
            List of BaseTool instances for the requested integrations
        """
        tools = []
        for integration in integrations:
            if integration in self._tools_by_integration:
                tools.extend(self._tools_by_integration[integration])
        return tools

    def get_integration_for_tool(self, tool_name: str) -> Optional[str]:
        """
        Reverse lookup: get integration name for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Integration name or None if not found
        """
        return self._tool_to_integration.get(tool_name)

    def get_hints(self, integrations: list[str], hint_type: str) -> str:
        """
        Get planner or executor hints for active integrations.

        Args:
            integrations: List of integration names
            hint_type: Either "planner" or "executor"

        Returns:
            Combined hints string
        """
        hints = []
        hint_attr = f"{hint_type}_hints"

        for name in integrations:
            config = self._configs.get(name)
            if config:
                hint = getattr(config, hint_attr, "")
                if hint:
                    hints.append(f"[{config.display_name}]: {hint}")

        return "\n".join(hints) if hints else ""

    def get_config(self, integration_name: str) -> Optional[IntegrationConfig]:
        """Get configuration for a specific integration."""
        return self._configs.get(integration_name)

    def get_all_configs(self) -> dict[str, IntegrationConfig]:
        """Get all integration configurations."""
        return self._configs.copy()

    def get_integrations_requiring_auth(self, integrations: list[str]) -> list[str]:
        """
        Filter integrations that require authentication.

        Args:
            integrations: List of integration names to check

        Returns:
            List of integration names that require auth
        """
        return [
            name for name in integrations
            if self._configs.get(name, IntegrationConfig(
                name=name, tool_names=[], display_name="",
                icon="", requires_auth=True, mcp_server=None
            )).requires_auth
        ]

    def register_tool(self, integration_name: str, tool: BaseTool) -> None:
        """
        Register a tool for an integration.

        Args:
            integration_name: Name of the integration
            tool: BaseTool instance to register
        """
        if integration_name not in self._tools_by_integration:
            self._tools_by_integration[integration_name] = []

        self._tools_by_integration[integration_name].append(tool)
        self._tool_to_integration[tool.name] = integration_name
        logger.debug(f"Registered tool '{tool.name}' for integration '{integration_name}'")

    def get_tool_names(self, integration_name: str) -> list[str]:
        """Get list of tool names for an integration."""
        config = self._configs.get(integration_name)
        return config.tool_names if config else []

    @property
    def is_initialized(self) -> bool:
        """Check if registry has been initialized."""
        return self._initialized


# Singleton instance
_global_registry: Optional[IntegrationRegistry] = None


async def get_registry(tokens: Optional[dict] = None, config_path: Optional[Path] = None) -> IntegrationRegistry:
    """
    Get or create the global registry instance.

    Args:
        tokens: Optional dict of integration_name -> auth_token
        config_path: Optional path to config file

    Returns:
        IntegrationRegistry singleton
    """
    global _global_registry
    if _global_registry is None or not _global_registry.is_initialized:
        _global_registry = IntegrationRegistry(config_path)
        if tokens is not None:
            await _global_registry.load_all(tokens)
        else:
            await _global_registry.load_all()
    return _global_registry


def reset_registry() -> None:
    """Reset the registry singleton (useful for testing)."""
    global _global_registry
    _global_registry = None
