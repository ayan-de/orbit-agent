"""
Memory Loader Node

Loads memory context (user profile, workflows, recent sessions) into the agent state.
This node should run early in the workflow to provide context for LLM decisions.
"""

from typing import Dict, Any

from src.agent.state import AgentState
from src.memory.compaction import (
    auto_compaction,
    check_compaction_needed,
    get_compaction_status,
)
from src.memory.reader import (
    format_profile_for_llm,
    format_workflows_for_llm,
    format_session_for_llm,
    read_recent_sessions,
)
from src.memory.structure import verify_memory_structure


async def load_memory_context(
    state: AgentState,
    profile_enabled: bool = True,
    workflows_enabled: bool = True,
    sessions_enabled: bool = True,
    max_sessions: int = 3,
    session_max_chars: int = 1000,
) -> Dict[str, Any]:
    """
    Load memory context into the agent state.

    This function retrieves and formats memory from the file-based memory system:
    - User profile: Preferences, personal information
    - Workflows: Stored workflows and patterns
    - Recent sessions: Recent conversation history for context

    Args:
        state: Current agent state
        profile_enabled: Whether to include user profile in context
        workflows_enabled: Whether to include workflows in context
        sessions_enabled: Whether to include recent sessions in context
        max_sessions: Maximum number of recent sessions to include
        session_max_chars: Maximum characters per session

    Returns:
        State updates with memory_context field populated

    Example:
        >>> state = {"messages": [...], "intent": "command", ...}
        >>> updates = await load_memory_context(state)
        >>> # updates["memory_context"] contains formatted memory
    """
    # Verify memory structure exists
    structure_valid = verify_memory_structure()

    # Build memory context
    memory_context_parts = []

    # Add user profile if enabled and available
    if profile_enabled:
        try:
            profile_text = format_profile_for_llm()
            if profile_text != "No user profile stored.":
                memory_context_parts.append(profile_text)
        except Exception:
            # Fail gracefully if profile can't be read
            pass

    # Add workflows if enabled and available
    if workflows_enabled:
        try:
            workflows_text = format_workflows_for_llm(limit=5)
            if workflows_text != "No workflows stored.":
                memory_context_parts.append(workflows_text)
        except Exception:
            # Fail gracefully if workflows can't be read
            pass

    # Add recent sessions if enabled and available
    if sessions_enabled:
        try:
            recent_sessions = read_recent_sessions(limit=max_sessions)
            if recent_sessions:
                memory_context_parts.append("\n**Recent Sessions:**\n")
                for session in recent_sessions:
                    session_text = format_session_for_llm(session, max_chars=session_max_chars)
                    memory_context_parts.append(session_text)
        except Exception:
            # Fail gracefully if sessions can't be read
            pass

    # Combine all parts
    memory_context = "\n\n".join(memory_context_parts)

    # Return state updates
    return {
        "memory_context": memory_context,
        "memory_available": structure_valid,
    }


def get_memory_summary(state: AgentState) -> str:
    """
    Get a summary of what memory was loaded for debugging/monitoring.

    Args:
        state: Current agent state

    Returns:
        Summary string of loaded memory
    """
    memory_context = state.get("memory_context", "")

    if not memory_context:
        return "No memory loaded"

    parts = []
    if "User Profile:" in memory_context:
        parts.append("User Profile")
    if "Stored Workflows:" in memory_context:
        parts.append(f"Workflows")
    if "Recent Sessions:" in memory_context:
        session_count = memory_context.count("**Session")
        parts.append(f"{session_count} Sessions")

    return f"Loaded: {', '.join(parts)}"


# ============================================================================
# Compaction Integration
# ============================================================================

async def check_compaction_for_loader(state: AgentState, enable_auto_compaction: bool = False) -> bool:
    """
    Check if memory compaction is needed and optionally trigger it.

    Args:
        state: Current agent state
        enable_auto_compaction: Whether to automatically run compaction

    Returns:
        True if compaction was run, False otherwise
    """
    compaction_status = get_compaction_status()

    if compaction_status["can_compact"]:
        if enable_auto_compaction:
            # Trigger automatic compaction
            compaction_result = await auto_compaction()
            # Log the compaction (could be stored in state or logged)
            return compaction_result.get("compaction_performed", False)

        return True  # Compaction is needed but not triggered

    return False


# Main node function for LangGraph
async def memory_loader_node(
    state: AgentState,
    enable_auto_compaction: bool = False,
) -> Dict[str, Any]:
    """
    Main memory loader node for LangGraph.

    Loads memory context and checks if compaction is needed.

    Args:
        state: Current agent state
        enable_auto_compaction: Whether to automatically run compaction when threshold exceeded

    Returns:
        State updates with memory_context and compaction_needed fields
    """
    # Load memory context
    updates = await load_memory_context(state)

    # Check if compaction is needed and optionally run it
    compaction_needed = await check_compaction_for_loader(state, enable_auto_compaction)
    updates["compaction_needed"] = compaction_needed

    return updates
