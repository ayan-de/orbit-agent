"""
Base tool class for Orbit AI Agent tools.

All tools should inherit from this class to ensure consistency.
"""

from abc import ABC, abstractmethod
from typing import Optional, Type, Dict, Any
from enum import Enum

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class ToolCategory(str, Enum):
    """Categories for organizing tools."""
    SYSTEM = "system"           # Core system operations (shell, files)
    INTEGRATION = "integration"  # External service integrations (Jira, Git, Email)
    WORKFLOW = "workflow"       # Workflow-specific operations
    ANALYSIS = "analysis"        # Data analysis and reporting


class ToolInput(BaseModel):
    """Base class for tool input validation."""

    pass


class ToolOutput(BaseModel):
    """Base class for tool output formatting."""

    pass


class ToolError(BaseModel):
    """Structured error information from tool execution."""

    tool_name: str = Field(..., description="Name of the tool that failed")
    error_type: str = Field(..., description="Type of error (e.g., validation, execution, network)")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    retryable: bool = Field(True, description="Whether the operation can be retried")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix for the error")


class OrbitTool(BaseTool, ABC):
    """
    Base class for all Orbit AI Agent tools.

    All tools should:
    1. Inherit from this class
    2. Implement the required abstract methods
    3. Define proper metadata (name, description, category)
    4. Provide input/output schemas
    5. Handle errors gracefully

    Example:
        ```python
        class MyTool(OrbitTool):
            name: str = "my_tool"
            description: str = "Does something useful"
            category: ToolCategory = ToolCategory.SYSTEM
            args_schema: Type[BaseModel] = MyToolInput

            def _arun(self, input_data: MyToolInput) -> str:
                # Your tool logic here
                return "Result"
        ```
    """

    # Metadata (should be overridden by subclasses)
    category: ToolCategory = ToolCategory.SYSTEM
    danger_level: int = 0  # 0-10, higher means more dangerous
    requires_confirmation: bool = False
    allowed_environments: list[str] = ["dev", "staging", "production"]

    # Validation
    def validate_input(self, input_data: Any) -> tuple[bool, Optional[str]]:
        """
        Validate tool input before execution.

        Can be overridden by subclasses for custom validation.

        Args:
            input_data: Input data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if hasattr(self, 'args_schema') and self.args_schema:
                self.args_schema.model_validate(input_data)
            return True, None
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @abstractmethod
    async def _arun(self, *args: Any, **kwargs: Any) -> str:
        """
        Async execution method (must be implemented by subclasses).

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Tool output as string
        """
        pass

    async def execute(
        self,
        *args: Any,
        **kwargs: Any
    ) -> str | ToolError:
        """
        Execute the tool with validation and error handling.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Tool output as string, or ToolError on failure
        """
        # Extract input data if provided
        input_data = kwargs.get('input_data') if kwargs else None

        # Validate input
        if input_data is not None:
            is_valid, error_message = self.validate_input(input_data)
            if not is_valid:
                return ToolError(
                    tool_name=self.name,
                    error_type="validation",
                    error_message=error_message or "Invalid input",
                    retryable=False
                )

        # Execute tool
        try:
            result = await self._arun(*args, **kwargs)

            # Try to parse result as ToolOutput if possible
            if hasattr(self, 'return_schema') and self.return_schema:
                try:
                    self.return_schema.model_validate_json(result)
                except Exception:
                    pass  # Keep result as string if parsing fails

            return result

        except Exception as e:
            return ToolError(
                tool_name=self.name,
                error_type="execution",
                error_message=str(e),
                retryable=True,
                suggested_fix=self.get_suggested_fix(e)
            )

    def get_suggested_fix(self, error: Exception) -> Optional[str]:
        """
        Get suggested fix for an error (can be overridden).

        Args:
            error: The exception that occurred

        Returns:
            Suggested fix or None
        """
        # Default implementation - can be overridden
        error_str = str(error).lower()

        if "permission denied" in error_str:
            return "Check file permissions or run with elevated privileges"
        elif "not found" in error_str:
            return f"Ensure the required resource exists"
        elif "connection" in error_str or "timeout" in error_str:
            return "Check network connectivity and retry"

        return None

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """
        Get tool metadata for registration.

        Returns:
            Dictionary with tool metadata
        """
        return {
            "name": cls.name if hasattr(cls, 'name') else cls.__name__,
            "description": cls.description if hasattr(cls, 'description') else "",
            "category": cls.category.value if hasattr(cls, 'category') else ToolCategory.SYSTEM.value,
            "danger_level": cls.danger_level if hasattr(cls, 'danger_level') else 0,
            "requires_confirmation": cls.requires_confirmation if hasattr(cls, 'requires_confirmation') else False,
            "allowed_environments": cls.allowed_environments if hasattr(cls, 'allowed_environments') else [],
            "module": cls.__module__,
            "class": cls.__name__,
        }

    @classmethod
    def is_safe_for_user(cls, user_permission_level: int = 1) -> bool:
        """
        Check if tool is safe for user based on danger level.

        Args:
            user_permission_level: User permission level (1-10, higher = more access)

        Returns:
            True if safe, False otherwise
        """
        danger_level = cls.danger_level if hasattr(cls, 'danger_level') else 0
        return danger_level <= user_permission_level

    @classmethod
    def requires_confirmation_for_user(cls, user_permission_level: int = 1) -> bool:
        """
        Check if tool requires user confirmation.

        Args:
            user_permission_level: User permission level

        Returns:
            True if confirmation required
        """
        return cls.requires_confirmation or not cls.is_safe_for_user(user_permission_level)
