"""
Human Input Node

Handles user confirmation flows for tool execution.
Integrates with LangGraph to pause and wait for user input when needed.
"""

import logging
from typing import Dict, Any, Optional

from src.agent.state import AgentState
from src.tools.permission import (
    can_auto_approve,
    get_permission_prompt,
    needs_confirmation,
    parse_confirmation_response,
    PermissionCheckResult,
)
from src.bridge.orchestrator_client import orchestrator_client
from src.bridge.schemas import ConfirmationType

logger = logging.getLogger("orbit.human_input")


# ============================================================================
# Human Input Node
# ============================================================================

async def human_input_node(
    state: AgentState,
    tool_name: Optional[str] = None,
    tool_danger_level: Optional[int] = None,
    auto_approve: bool = False,
    use_real_confirmation: bool = True,
) -> Dict[str, Any]:
    """
    Human input node for LangGraph - handles user confirmations.

    This node:
    1. Checks if tool execution requires confirmation
    2. Generates user-friendly confirmation prompt
    3. Sends confirmation request to user via Bridge
    4. Waits for user response
    5. Returns approval/denial result

    Args:
        state: Current agent state
        tool_name: Name of tool being executed (optional, taken from state if not provided)
        tool_danger_level: Danger level of tool (optional)
        auto_approve: If True, auto-approve safe tools without asking
        use_real_confirmation: If True, use Bridge for real confirmation (default)

    Returns:
        State updates with:
        - user_confirmation: True/False/None based on user response
        - confirmation_prompt: The prompt shown to user
        - tool_executed: True if tool was executed
    """
    # Get tool details from state or parameters
    if tool_name is None:
        tool_name = state.get("pending_tool_name")

    # If no tool to confirm, pass through
    if not tool_name:
        return {
            "user_confirmation": None,
            "confirmation_prompt": None,
            "tool_executed": False,
        }

    # Get danger level from parameters or state
    if tool_danger_level is None:
        tool_danger_level = state.get("pending_tool_danger_level", 0)

    # Create a mock tool object for permission checking
    class MockTool:
        name: str = tool_name
        danger_level: int = tool_danger_level
        requires_confirmation: bool = tool_danger_level > 2
        category: str = "system"

    tool = MockTool()

    # Get user permission level (default to 1, could be stored in user profile)
    user_permission_level = state.get("user_permission_level", 1)
    environment = state.get("environment", "dev")

    # Check if confirmation is needed
    check_result = needs_confirmation(
        tool,  # type: ignore
        user_permission_level=user_permission_level,
        environment=environment,
    )

    # Auto-approve safe tools if enabled
    if auto_approve and can_auto_approve(
        tool,  # type: ignore
        user_permission_level=user_permission_level,
    ):
        logger.info(f"Auto-approved tool: {tool_name}")
        return {
            "user_confirmation": True,
            "confirmation_prompt": None,
            "tool_executed": False,
            "auto_approved": True,
        }

    # If confirmation required, request from user
    if check_result.requires_confirmation():
        prompt = get_permission_prompt(tool, check_result)  # type: ignore

        # Use real Bridge confirmation if enabled
        if use_real_confirmation:
            return await _request_real_confirmation(
                state=state,
                tool_name=tool_name,
                tool_danger_level=tool_danger_level,
                prompt=prompt,
                check_result=check_result,
            )

        # Fallback: simulated confirmation (for testing/demo)
        return {
            "user_confirmation": None,
            "confirmation_prompt": prompt,
            "tool_executed": False,
            "auto_approved": False,
        }

    # Tool is allowed without confirmation
    return {
        "user_confirmation": True,
        "confirmation_prompt": None,
        "tool_executed": False,
        "auto_approved": True,
    }


async def _request_real_confirmation(
    state: AgentState,
    tool_name: str,
    tool_danger_level: int,
    prompt: str,
    check_result: PermissionCheckResult,
) -> Dict[str, Any]:
    """
    Request real confirmation from user via Bridge.

    Args:
        state: Current agent state
        tool_name: Name of the tool
        tool_danger_level: Danger level of the tool
        prompt: Confirmation prompt text
        check_result: Permission check result

    Returns:
        State updates with confirmation result
    """
    # Determine confirmation type based on tool
    confirmation_type = ConfirmationType.TOOL_EXECUTION
    if "shell" in tool_name.lower() or "command" in tool_name.lower():
        confirmation_type = ConfirmationType.COMMAND_EXECUTION
    elif "file" in tool_name.lower():
        confirmation_type = ConfirmationType.FILE_MODIFICATION

    # Build details for confirmation
    plan = state.get("plan", {})
    current_step = state.get("current_step", 0)
    steps = plan.get("steps", [])
    current_step_info = steps[current_step - 1] if 0 < current_step <= len(steps) else None

    details = {
        "tool_name": tool_name,
        "danger_level": tool_danger_level,
        "reason": check_result.reason,
        "current_step": current_step,
        "step_description": current_step_info.get("description") if current_step_info else None,
        "plan_goal": plan.get("goal"),
    }

    # Add command details if available
    if current_step_info and current_step_info.get("arguments"):
        args = current_step_info.get("arguments", {})
        if "command" in args:
            details["command"] = args["command"]

    try:
        # Request confirmation via Bridge
        response = await orchestrator_client.request_confirmation(
            confirmation_type=confirmation_type,
            title=f"Confirm: {tool_name}",
            message=prompt,
            details=details,
            danger_level=tool_danger_level,
            timeout_seconds=60,
        )

        logger.info(f"Confirmation response for {tool_name}: approved={response.approved}")

        return {
            "user_confirmation": response.approved,
            "confirmation_prompt": prompt,
            "tool_executed": False,
            "auto_approved": False,
            "user_response": response.response,
            "remember_decision": response.remember_decision,
        }

    except Exception as e:
        logger.error(f"Failed to get confirmation: {e}")
        # Default to deny on error
        return {
            "user_confirmation": False,
            "confirmation_prompt": prompt,
            "tool_executed": False,
            "auto_approved": False,
            "user_response": f"Error: {str(e)}",
        }


async def process_user_confirmation(
    state: AgentState,
    user_response: str,
) -> Dict[str, Any]:
    """
    Process user's confirmation response.

    Args:
        state: Current agent state
        user_response: User's response to confirmation prompt

    Returns:
        State updates with confirmation result
    """
    # Parse the response
    approved = parse_confirmation_response(user_response)

    # Update state with result
    return {
        "user_confirmation": approved,
        "confirmation_processed": True,
        "user_response": user_response,
    }


# ============================================================================
# Confirmation State Management
# ============================================================================

def needs_confirmation_in_state(state: AgentState) -> bool:
    """
    Check if current state needs user confirmation.

    Args:
        state: Current agent state

    Returns:
        True if confirmation is pending, False otherwise
    """
    return (
        state.get("confirmation_prompt") is not None
        and state.get("user_confirmation") is None
    )


def is_confirmed(state: AgentState) -> bool:
    """
    Check if user has approved the pending action.

    Args:
        state: Current agent state

    Returns:
        True if approved, False otherwise
    """
    return state.get("user_confirmation") is True


def is_denied(state: AgentState) -> bool:
    """
    Check if user has denied the pending action.

    Args:
        state: Current agent state

    Returns:
        True if denied, False otherwise
    """
    return state.get("user_confirmation") is False


def get_confirmation_message(state: AgentState) -> Optional[str]:
    """
    Get the confirmation message to show user.

    Args:
        state: Current agent state

    Returns:
        Confirmation prompt string or None
    """
    return state.get("confirmation_prompt")


def clear_confirmation_state(state: AgentState) -> Dict[str, Any]:
    """
    Clear confirmation-related fields from state.

    Args:
        state: Current agent state

    Returns:
        State updates with confirmation fields cleared
    """
    return {
        "user_confirmation": None,
        "confirmation_prompt": None,
        "confirmation_processed": False,
        "user_response": None,
        "pending_tool_name": None,
        "pending_tool_danger_level": None,
    }


# ============================================================================
# Tool Execution Helpers
# ============================================================================

def set_pending_tool(
    state: AgentState,
    tool_name: str,
    danger_level: int,
) -> Dict[str, Any]:
    """
    Set a tool as pending confirmation.

    Args:
        state: Current agent state
        tool_name: Name of tool to execute
        danger_level: Danger level of tool

    Returns:
        State updates with pending tool information
    """
    return {
        "pending_tool_name": tool_name,
        "pending_tool_danger_level": danger_level,
        "user_confirmation": None,  # Reset confirmation
        "confirmation_processed": False,
    }


async def route_after_confirmation(state: AgentState) -> str:
    """
    Determine next step after user confirmation.

    Args:
        state: Current agent state

    Returns:
        Next node name ("execute_tool" or "responder")
    """
    # If no confirmation needed or approved, execute tool
    if is_confirmed(state) or not needs_confirmation_in_state(state):
        return "executor"

    # If denied, respond to user
    if is_denied(state):
        return "responder"

    # Still awaiting confirmation - stay in human_input node
    return "human_input"


# ============================================================================
# Logging and Debugging
# ============================================================================

def log_confirmation_event(
    tool_name: str,
    danger_level: int,
    approved: bool,
    auto_approved: bool,
) -> str:
    """
    Generate a log message for confirmation events.

    Args:
        tool_name: Name of tool
        danger_level: Danger level of tool
        approved: Whether user approved
        auto_approved: Whether auto-approved

    Returns:
        Log message string
    """
    status = "APPROVED" if approved else "DENIED"

    if auto_approved:
        status = "AUTO-APPROVED"

    return f"[CONFIRMATION] Tool: {tool_name} | Danger: {danger_level} | Status: {status}"
