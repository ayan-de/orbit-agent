"""
Tool registry for Orbit AI Agent.

Provides auto-discovery and registration of tools.
"""

import inspect
from typing import Dict, List, Type, Optional, Any, Callable
from pathlib import Path

from src.tools.base import OrbitTool
from src.tools.shell import ShellTool


class ToolRegistry:
    """
    Registry for managing all available tools.

    Provides auto-discovery of tools and methods to retrieve tools by name, category, etc.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._tools: Dict[str, Type[OrbitTool]] = {}
        self._tool_instances: Dict[str, OrbitTool] = {}

    def register_tool(self, tool_class: Type[OrbitTool]) -> None:
        """
        Register a tool class.

        Args:
            tool_class: Tool class (not instance)
        """
        # Create instance to get metadata
        tool_instance = tool_class()
        metadata = tool_class.get_metadata()

        self._tools[metadata["name"]] = tool_class
        self._tool_instances[metadata["name"]] = tool_instance

    def register_tools(self, tool_classes: List[Type[OrbitTool]]) -> None:
        """
        Register multiple tool classes.

        Args:
            tool_classes: List of tool classes
        """
        for tool_class in tool_classes:
            self.register_tool(tool_class)

    def get_tool(self, tool_name: str) -> Optional[OrbitTool]:
        """
        Get a tool instance by name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool instance if found, None otherwise
        """
        return self._tool_instances.get(tool_name)

    def get_all_tools(self) -> Dict[str, Type[OrbitTool]]:
        """
        Get all registered tool classes.

        Returns:
            Dictionary mapping tool names to tool classes
        """
        return self._tools.copy()

    def get_all_instances(self) -> Dict[str, OrbitTool]:
        """
        Get all tool instances.

        Returns:
            Dictionary mapping tool names to tool instances
        """
        return self._tool_instances.copy()

    def get_tools_by_category(self, category: str) -> List[str]:
        """
        Get all tool names in a category.

        Args:
            category: Category to filter by (SYSTEM, INTEGRATION, WORKFLOW, ANALYSIS)

        Returns:
            List of tool names in the category
        """
        return [
            name for name, tool_class in self._tools.items()
            if tool_class.get_metadata().get("category") == category
        ]

    def get_safe_tools_for_user(
        self,
        user_permission_level: int = 1
    ) -> Dict[str, OrbitTool]:
        """
        Get tools that are safe for a user based on their permission level.

        Args:
            user_permission_level: User permission level (1-10, higher = more access)

        Returns:
            Dictionary of tool names to safe tool instances
        """
        safe_tools = {}
        for name, tool_instance in self._tool_instances.items():
            if tool_instance.is_safe_for_user(user_permission_level):
                safe_tools[name] = tool_instance
        return safe_tools

    def get_tools_requiring_confirmation(
        self,
        user_permission_level: int = 1
    ) -> Dict[str, OrbitTool]:
        """
        Get tools that require user confirmation.

        Args:
            user_permission_level: User permission level

        Returns:
            Dictionary of tool names to tool instances
        """
        confirmation_tools = {}
        for name, tool_instance in self._tool_instances.items():
            if tool_instance.requires_confirmation_for_user(user_permission_level):
                confirmation_tools[name] = tool_instance
        return confirmation_tools

    def get_tool_names(self) -> List[str]:
        """
        Get all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def tool_exists(self, tool_name: str) -> bool:
        """
        Check if a tool is registered.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool exists, False otherwise
        """
        return tool_name in self._tools

    def auto_discover_tools(
        self,
        package_name: str = "src.tools",
        base_class: Type[OrbitTool] = OrbitTool
    ) -> int:
        """
        Auto-discover tools in a package.

        Scans the package for classes that inherit from base_class.

        Args:
            package_name: Package to scan (e.g., "src.tools")
            base_class: Base class to look for (e.g., OrbitTool)

        Returns:
            Number of tools discovered and registered
        """
        # Import the package
        try:
            package = __import__(package_name)
        except ImportError:
            return 0

        discovered_count = 0

        # Scan all modules in the package
        for _, module_name in inspect.getmembers(package):
            # Skip private modules and __init__
            if module_name.startswith("_") or module_name == "__init__":
                continue

            # Get the module
            module = getattr(package, module_name)

            # Skip if it's not a module (e.g., package-level attributes)
            if not inspect.ismodule(module):
                continue

            # Find all classes in the module
            for _, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, base_class):
                    # Skip the base class itself
                    if obj is base_class:
                        continue

                    # Skip classes defined in other modules
                    if obj.__module__ != module.__name__:
                        continue

                    # Register the tool
                    try:
                        self.register_tool(obj)
                        discovered_count += 1
                    except Exception as e:
                        # Log error but continue discovering other tools
                        print(f"Warning: Failed to register tool {obj.__name__}: {e}")

        return discovered_count

    def search_tools(self, query: str) -> List[str]:
        """
        Search tools by name or description.

        Args:
            query: Search query string

        Returns:
            List of matching tool names
        """
        query_lower = query.lower()
        matches = []

        for name, tool_class in self._tools.items():
            metadata = tool_class.get_metadata()
            # Search in tool name
            if query_lower in name.lower():
                matches.append(name)
                continue

            # Search in description
            description = metadata.get("description", "").lower()
            if query_lower in description:
                matches.append(name)
                continue

        return list(set(matches))  # Remove duplicates

    def format_tools_for_llm(
        self,
        tools: Optional[List[str]] = None
    ) -> List[str]:
        """
        Format tools as a string description for LLM.

        Useful for providing tools to the LLM so it can choose which to use.

        Args:
            tools: Optional list of tool names (defaults to all)

        Returns:
            List of formatted tool descriptions
        """
        if tools is None:
            tools = self.get_tool_names()

        formatted = []
        for tool_name in tools:
            tool_instance = self.get_tool(tool_name)
            if tool_instance is None:
                continue

            metadata = tool_instance.get_metadata()
            formatted.append(
                f"- {metadata['name']}: {metadata['description']}"
            )

        return formatted

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the schema for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool schema dictionary or None if tool not found
        """
        tool_class = self._tools.get(tool_name)
        if tool_class is None:
            return None

        metadata = tool_class.get_metadata()
        schema = {
            "name": metadata["name"],
            "description": metadata["description"],
            "category": metadata.get("category"),
            "danger_level": metadata.get("danger_level", 0),
            "requires_confirmation": metadata.get("requires_confirmation", False),
            "allowed_environments": metadata.get("allowed_environments", []),
            "module": metadata.get("module"),
            "class": metadata.get("class"),
        }

        # Add input/output schema if available
        if hasattr(tool_class, 'args_schema') and tool_class.args_schema:
            schema["input_schema"] = tool_class.args_schema.model_json_schema()
        if hasattr(tool_class, 'return_schema') and tool_class.return_schema:
            schema["output_schema"] = tool_class.return_schema.model_json_schema()

        return schema

    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Get schemas for all registered tools.

        Returns:
            Dictionary mapping tool names to tool schemas
        """
        schemas = {}
        for tool_name in self.get_tool_names():
            schema = self.get_tool_schema(tool_name)
            if schema:
                schemas[tool_name] = schema
        return schemas


# Singleton registry instance
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the singleton tool registry instance.

    Creates and initializes the registry on first call.

    Returns:
        ToolRegistry instance
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = ToolRegistry()
        # Auto-discover and register built-in tools
        _global_registry.auto_discover_tools()
        # Register ShellTool explicitly
        _global_registry.register_tool(ShellTool)

    return _global_registry


def reset_registry() -> ToolRegistry:
    """
    Reset the registry (useful for testing).

    Returns:
        New ToolRegistry instance
    """
    global _global_registry
    _global_registry = None
    return get_tool_registry()
