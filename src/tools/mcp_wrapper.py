"""
MCP Tool Wrapper for dynamically wrapping MCP server tools.

Converts MCP tool schemas to LangChain BaseTool instances.
"""

import json
import logging
from typing import Any, Optional, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, create_model

logger = logging.getLogger(__name__)


def json_schema_to_pydantic_field(
    name: str,
    schema: dict,
    required: bool = False
) -> tuple[Type, Any]:
    """
    Convert a JSON Schema property to a Pydantic field definition.

    Args:
        name: Field name
        schema: JSON Schema for the field
        required: Whether the field is required

    Returns:
        Tuple of (type, default_value) for create_model
    """
    json_type = schema.get("type", "string")
    description = schema.get("description", "")
    default = ... if required else None

    type_mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    python_type = type_mapping.get(json_type, str)

    # Handle optional types
    if not required:
        python_type = Optional[python_type]

    return (python_type, default)


def build_pydantic_schema_from_mcp(
    tool_name: str,
    mcp_schema: dict
) -> Type[BaseModel]:
    """
    Build a Pydantic model from MCP tool input schema.

    Args:
        tool_name: Name of the tool (used for model name)
        mcp_schema: MCP tool inputSchema

    Returns:
        Pydantic BaseModel class
    """
    properties = mcp_schema.get("properties", {})
    required = mcp_schema.get("required", [])

    fields = {}
    for prop_name, prop_schema in properties.items():
        field_type, default = json_schema_to_pydantic_field(
            prop_name,
            prop_schema,
            prop_name in required
        )
        fields[prop_name] = (field_type, default)

    # Create dynamic model
    model_name = f"{tool_name.title().replace('_', '')}Input"
    return create_model(model_name, **fields)


class MCPToolWrapper(BaseTool):
    """
    Auto-generated LangChain tool from MCP tool schema.

    Wraps MCP server tools as LangChain BaseTool instances
    for seamless integration with the agent.
    """

    server_name: str
    mcp_client: Any  # MCPClientManager (avoid circular import)
    original_schema: dict

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict,
        server_name: str,
        mcp_client: Any,
    ):
        """
        Initialize MCP tool wrapper.

        Args:
            name: Tool name
            description: Tool description
            input_schema: MCP inputSchema (JSON Schema)
            server_name: Name of the MCP server
            mcp_client: MCPClientManager instance
        """
        args_schema = build_pydantic_schema_from_mcp(name, input_schema)

        super().__init__(
            name=name,
            description=description,
            args_schema=args_schema,
        )

        self.server_name = server_name
        self.mcp_client = mcp_client
        self.original_schema = input_schema

    async def _arun(self, **kwargs) -> str:
        """
        Execute the tool asynchronously via MCP client.

        Args:
            **kwargs: Tool arguments

        Returns:
            Tool execution result as string
        """
        try:
            result = await self.mcp_client.execute_tool(
                self.server_name,
                self.name,
                **kwargs
            )
            return self._format_result(result)
        except Exception as e:
            logger.error(f"MCP tool '{self.name}' execution failed: {e}")
            return f"Error executing {self.name}: {str(e)}"

    def _run(self, **kwargs) -> str:
        """
        Synchronous execution (not supported for MCP tools).

        MCP tools require async execution.
        """
        raise NotImplementedError(
            f"MCP tool '{self.name}' only supports async execution. "
            "Use _arun() instead."
        )

    def _format_result(self, result: Any) -> str:
        """
        Format MCP tool result for agent consumption.

        Args:
            result: Raw result from MCP server

        Returns:
            Formatted string result
        """
        if isinstance(result, str):
            return result

        if isinstance(result, dict):
            # Handle MCP response format
            if "content" in result:
                content = result["content"]
                if isinstance(content, list):
                    texts = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            texts.append(item.get("text", ""))
                    return "\n".join(texts)
                return str(content)

            # Return as formatted JSON
            return json.dumps(result, indent=2)

        return str(result)

    @classmethod
    def from_mcp_tool(
        cls,
        server_name: str,
        tool_data: dict,
        mcp_client: Any
    ) -> "MCPToolWrapper":
        """
        Create wrapper from MCP tool discovery response.

        Args:
            server_name: Name of the MCP server
            tool_data: Tool data from tools/list response
            mcp_client: MCPClientManager instance

        Returns:
            MCPToolWrapper instance
        """
        return cls(
            name=tool_data.get("name", "unknown"),
            description=tool_data.get("description", ""),
            input_schema=tool_data.get("inputSchema", {}),
            server_name=server_name,
            mcp_client=mcp_client,
        )


def wrap_mcp_tools(
    server_name: str,
    tools_data: list[dict],
    mcp_client: Any
) -> list[MCPToolWrapper]:
    """
    Wrap multiple MCP tools as LangChain tools.

    Args:
        server_name: Name of the MCP server
        tools_data: List of tool data from tools/list
        mcp_client: MCPClientManager instance

    Returns:
        List of MCPToolWrapper instances
    """
    wrapped = []
    for tool_data in tools_data:
        try:
            wrapper = MCPToolWrapper.from_mcp_tool(
                server_name,
                tool_data,
                mcp_client
            )
            wrapped.append(wrapper)
            logger.debug(f"Wrapped MCP tool: {wrapper.name}")
        except Exception as e:
            logger.warning(f"Failed to wrap MCP tool '{tool_data.get('name')}': {e}")

    return wrapped
