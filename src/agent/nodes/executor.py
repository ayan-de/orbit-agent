"""
Executor node for LangGraph workflow.

Executes tool calls from planner and handles results.
"""

from typing import Dict, Any, Optional, List
from enum import Enum

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from src.agent.state import AgentState
from src.tools import get_tool_registry
from src.tools.base import OrbitTool, ToolError, ToolCategory
from src.db.models import ToolCall, ToolCallStatus
from src.db.repositories import SessionRepository, MessageRepository, ToolCallRepository
from src.llm.factory import llm_factory


class ExecutionStatus(str, Enum):
    """Status of a single tool execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutorNode:
    """
    Executor node for LangGraph workflow.

    Executes tools from plan and manages execution state.
    """

    def __init__(self, llm_factory=llm_factory):
        """
        Initialize executor node.

        Args:
            llm_factory: Factory function for creating LLM instances
        """
        self.llm_factory = llm_factory

    async def execute_plan(
        self,
        state: AgentState,
        plan: List[Dict[str, Any]],
        session_id: str,
        user_id: str,
        db_session
    ) -> Dict[str, Any]:
        """
        Execute a complete plan.

        Args:
            state: Agent state (will be updated in place)
            plan: Plan with steps to execute
            session_id: Session UUID (as string for now)
            user_id: User identifier
            db_session: Database session

        Returns:
            Updated state with execution results
        """
        registry = get_tool_registry()

        # Get repositories
        session_repo = SessionRepository(db_session)
        tool_call_repo = ToolCallRepository(db_session)

        results = []

        # Execute each step
        for step_data in plan.get("steps", []):
            step_result = await self._execute_step(
                step_data,
                registry,
                state,
                session_id,
                user_id,
                tool_call_repo
            )
            results.append(step_result)

        # Update state with execution summary
        state["execution_results"] = results

        return {
            "status": "completed",
            "results": results
        }

    async def _execute_step(
        self,
        step_data: Dict[str, Any],
        registry: "ToolRegistry",
        state: AgentState,
        session_id: str,
        user_id: str,
        tool_call_repo: ToolCallRepository
    ) -> Dict[str, Any]:
        """
        Execute a single plan step.

        Args:
            step_data: Step data from plan
            registry: Tool registry
            state: Agent state (will be updated in place)
            session_id: Session UUID (as string)
            user_id: User identifier
            tool_call_repo: Tool call repository

        Returns:
            Step execution result
        """
        step_number = step_data.get("step_number")
        description = step_data.get("description")
        tool_name = step_data.get("tool_name")
        arguments = step_data.get("arguments")
        expected_outcome = step_data.get("expected_outcome")

        # Check if user confirmation required
        if step_data.get("requires_confirmation"):
            # This should be handled by the planner before reaching executor
            return {
                "step_number": step_number,
                "status": "skipped",
                "error": "This step requires user confirmation"
            }

        # Get tool instance
        tool = registry.get_tool(tool_name)
        if tool is None:
            return {
                "step_number": step_number,
                "status": "failed",
                "error": f"Tool '{tool_name}' not found in registry"
            }

        # Check if tool requires confirmation for user
        if not tool.is_safe_for_user(user_permission_level=1):
            # This should be handled by planner, but double-check
            return {
                "step_number": step_number,
                "status": "skipped",
                "error": f"Tool '{tool_name}' requires higher permission level"
            }

        # Create tool call record
        db_session_id = await self._get_or_create_session_id(session_id, tool_call_repo)
        tool_call = await tool_call_repo.create(
            session_id=db_session_id,
            tool_name=tool_name,
            inputs=arguments or {}
        )

        # Update status to running
        await tool_call_repo.mark_running(tool_call.id)
        status = ExecutionStatus.RUNNING

        try:
            # Prepare tool input
            tool_input = self._prepare_tool_input(tool, tool_name, arguments)

            # Execute tool
            start_time = self._get_current_time_ms()
            result = await tool.execute(tool_input)

            # Calculate execution time
            end_time = self._get_current_time_ms()
            execution_time_ms = end_time - start_time

            # Update tool call with results
            if isinstance(result, str):
                await tool_call_repo.mark_completed(
                    tool_call.id,
                    outputs={"raw_output": result},
                    execution_time_ms=execution_time_ms
                )
                status = ExecutionStatus.COMPLETED
                output = result
                error_message = None
            else:
                # Handle ToolError
                if isinstance(result, ToolError):
                    await tool_call_repo.mark_failed(
                        tool_call.id,
                        error_message=result.error_message
                    )
                    status = ExecutionStatus.FAILED
                output = None
                error_message = result.error_message if isinstance(result, ToolError) else str(result)
                # Unexpected error type
                if error_message is None:
                    error_message = "Unexpected tool result type"

        except Exception as e:
            status = ExecutionStatus.FAILED
            error_message = str(e)

        finally:
            # Update tool call status in database
            if status == ExecutionStatus.COMPLETED:
                await tool_call_repo.mark_completed(
                    tool_call.id,
                    outputs={"raw_output": output} if output else {},
                    execution_time_ms=execution_time_ms if execution_time_ms else None
                )
            elif status == ExecutionStatus.FAILED:
                await tool_call_repo.mark_failed(
                    tool_call.id,
                    error_message=error_message
                )

        # Format result for return
        result_data = {
            "step_number": step_number,
            "description": description,
            "status": status.value,
            "output": output,
            "error": error_message,
            "execution_time_ms": execution_time_ms if execution_time_ms else None,
            "tool_name": tool_name
        }

        return result_data

    async def _prepare_tool_input(self, tool: OrbitTool, tool_name: str, arguments: Optional[Dict[str, Any]]) -> Any:
        """
        Prepare tool input data.

        Args:
            tool: Tool instance
            tool_name: Name of tool (for logging)
            arguments: Tool arguments (optional)

        Returns:
            Prepared input data for tool
        """
        if arguments is None:
            return {}

        # If tool has an args_schema, validate against it
        if hasattr(tool, 'args_schema') and tool.args_schema:
            from pydantic import ValidationError
            try:
                return tool.args_schema.model_validate(arguments)
            except ValidationError:
                # Validation failed, try with just the arguments
                return arguments

        return arguments

    async def _get_or_create_session_id(self, session_id: str, tool_call_repo) -> str:
        """
        Get database session ID from session string.

        Args:
            session_id: Session ID as string

        Returns:
            Database session UUID
        """
        # Convert string session ID to UUID if needed
        from uuid import UUID

        try:
            return str(UUID(session_id))
        except ValueError:
            # If session_id is not a valid UUID, we have a problem
            # For now, we'll just use it as-is
            return session_id

    def _get_current_time_ms(self) -> int:
        """Get current time in milliseconds."""
        import time
        return int(time.time() * 1000)

    async def _interpret_tool_result(
        self,
        tool: OrbitTool,
        result: str,
        tool_name: str
    ) -> Dict[str, Any]:
        """
        Interpret tool result to determine next action.

        Args:
            tool: Tool instance
            result: Tool output string
            tool_name: Tool name

        Returns:
            Dictionary with interpretation and next action
        """
        # Check if output indicates an error
        if "error" in result.lower() or "failed" in result.lower():
            return {
                "status": "failed",
                "next_action": "abort",
                "message": result
            }

        # Check if output indicates success
        if not result or result.strip() == "":
            return {
                "status": "success",
                "next_action": "continue",
                "message": "Step completed successfully"
            }

        # Default interpretation - continue to next step
        return {
            "status": "success",
            "next_action": "continue",
            "message": "Tool executed"
        }

    async def handle_tool_error(
        self,
        tool_error: ToolError,
        state: AgentState,
        user_permission_level: int = 1
    ) -> Dict[str, Any]:
        """
        Handle tool error and determine if retry is possible.

        Args:
            tool_error: ToolError instance
            state: Agent state (will be updated in place)
            user_permission_level: User permission level (1-10, higher = more access)

        Returns:
            Error handling result
        """
        error_message = tool_error.error_message
        suggested_fix = tool_error.suggested_fix
        retryable = tool_error.retryable

        result = {
            "error": tool_error.error_type,
            "message": error_message,
            "suggested_fix": suggested_fix,
            "retryable": retryable
        }

        # Add error to state for user awareness
        state["last_error"] = result

        return result

    async def validate_tool_availability(
        self,
        tool_name: str,
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Validate if a tool is available and accessible.

        Args:
            tool_name: Name of tool
            state: Agent state

        Returns:
            Validation result
        """
        registry = get_tool_registry()
        tool = registry.get_tool(tool_name)

        if tool is None:
            return {
                "available": False,
                "error": f"Tool '{tool_name}' not found"
            }

        # Check tool environment permissions
        if tool.allowed_environments and "production" in tool.allowed_environments:
            return {
                "available": False,
                "error": f"Tool '{tool_name}' is not available in production environment"
            }

        return {
            "available": True,
            "tool": tool.get_tool_schema(tool_name)
        }

    async def format_tool_response_for_llm(
        self,
        tool_name: str,
        result: str,
        status: str,
        error_message: Optional[str] = None
    ) -> str:
        """
        Format tool execution result for LLM consumption.

        Args:
            tool_name: Name of tool
            result: Tool output
            status: Execution status
            error_message: Optional error message

        Returns:
            Formatted response string
        """
        if status == ExecutionStatus.COMPLETED:
            return f"✓ {tool_name}: {result}"
        elif status == ExecutionStatus.FAILED:
            error_msg = error_message or "Execution failed"
            return f"✗ {tool_name}: {error_msg}"
        elif status == ExecutionStatus.RUNNING:
            return f"⏳ {tool_name}: Executing..."
        elif status == ExecutionStatus.PENDING:
            return f"⏸ {tool_name}: Pending..."
        elif status == ExecutionStatus.SKIPPED:
            return f"⊘ {tool_name}: Skipped"
        else:
            return f"? {tool_name}: {status}"
