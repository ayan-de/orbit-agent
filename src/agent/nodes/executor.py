"""
Executor node for LangGraph workflow.

Executes tool calls from planner and handles results.
"""

import logging
import time
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from enum import Enum

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.agent.state import AgentState
from src.tools import get_tool_registry
from src.tools.base import OrbitTool, ToolError, ToolCategory
from src.db.repositories import SessionRepository, MessageRepository, ToolCallRepository
from src.llm.factory import llm_factory

if TYPE_CHECKING:
    from src.tools.registry import ToolRegistry

logger = logging.getLogger("orbit.executor")


class ExecutionStatus(str, Enum):
    """Status of a single tool execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutorNode:
    """Executor node for LangGraph workflow."""

    def __init__(self, llm_factory=llm_factory):
        self.llm_factory = llm_factory

    async def execute_plan(
        self,
        state: AgentState,
        plan: Dict[str, Any],
        session_id: str,
        user_id: str,
        db_session,
    ) -> Dict[str, Any]:
        """Execute a complete plan."""
        registry = get_tool_registry()
        tool_call_repo = ToolCallRepository(db_session) if db_session else None

        results = list(state.get("tool_results", []))
        current_step = state.get("current_step", 1)
        steps = plan.get("steps", [])

        logger.info(f"Execute plan: step {current_step} of {len(steps)}")

        if not steps or current_step < 1 or current_step > len(steps):
            logger.warning(
                f"Invalid step configuration: steps={len(steps)}, current={current_step}"
            )
            return {"status": "completed", "results": results}

        step_data = steps[current_step - 1]
        logger.info(f"Step data: {step_data}")

        step_result = await self._execute_step(
            step_data=step_data,
            registry=registry,
            state=state,
            session_id=session_id,
            user_id=user_id,
            tool_call_repo=tool_call_repo,
        )
        results.append(step_result)

        logger.info(f"Step {current_step} result: {step_result.get('status')}")

        return {"status": "completed", "results": results}

    async def _execute_step(
        self,
        step_data: Dict[str, Any],
        registry: "ToolRegistry",
        state: AgentState,
        session_id: str,
        user_id: str,
        tool_call_repo: Optional[ToolCallRepository],
    ) -> Dict[str, Any]:
        """Execute a single plan step."""
        step_number = step_data.get("step_number", 0)
        description = step_data.get("description", "")
        tool_name = step_data.get("tool_name")
        arguments = step_data.get("arguments") or {}

        logger.info(f"Executing step {step_number}: {description}")
        logger.info(f"Tool: {tool_name}, Args: {arguments}")

        if not tool_name:
            logger.error(f"No tool_name for step {step_number}")
            return {
                "step_number": step_number,
                "description": description,
                "status": "failed",
                "error": "No tool specified for this step",
                "output": None,
                "tool_name": None,
            }

        tool = registry.get_tool(tool_name)
        if tool is None:
            available = registry.get_tool_names()
            logger.error(f"Tool '{tool_name}' not found. Available: {available}")
            return {
                "step_number": step_number,
                "description": description,
                "status": "failed",
                "error": f"Tool '{tool_name}' not found. Available tools: {available}",
                "output": None,
                "tool_name": tool_name,
            }

        status = ExecutionStatus.RUNNING
        output = None
        error_message = None
        execution_time_ms = None

        try:
            tool_input = await self._prepare_tool_input(tool, tool_name, arguments)

            start_time = self._get_current_time_ms()
            logger.info(f"Executing tool: {tool_name} with input: {tool_input}")

            result = await tool.execute(tool_input)

            execution_time_ms = self._get_current_time_ms() - start_time
            logger.info(f"Tool execution time: {execution_time_ms}ms")

            if isinstance(result, str):
                status = ExecutionStatus.COMPLETED
                output = result
                logger.info(
                    f"Tool succeeded: {output[:200]}..."
                    if len(output) > 200
                    else f"Tool succeeded: {output}"
                )
            elif isinstance(result, ToolError):
                status = ExecutionStatus.FAILED
                error_message = result.error_message
                logger.error(f"Tool error: {error_message}")
            else:
                status = ExecutionStatus.COMPLETED
                output = str(result)

        except Exception as e:
            status = ExecutionStatus.FAILED
            error_message = str(e)
            logger.exception(f"Tool execution failed: {e}")

        return {
            "step_number": step_number,
            "description": description,
            "status": status.value,
            "output": output,
            "error": error_message,
            "execution_time_ms": execution_time_ms,
            "tool_name": tool_name,
        }

    async def _prepare_tool_input(
        self, tool: OrbitTool, tool_name: str, arguments: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare tool input data."""
        if arguments is None:
            return {}

        if hasattr(tool, "args_schema") and tool.args_schema:
            from pydantic import ValidationError

            try:
                validated = tool.args_schema.model_validate(arguments)
                return validated.model_dump()
            except ValidationError:
                return arguments

        return arguments

        return arguments

    def _get_current_time_ms(self) -> int:
        """Get current time in milliseconds."""
        return int(time.time() * 1000)
