"""
Email refinement node - handles email content refinement based on user feedback.
"""
from typing import Dict, Any
from langchain_core.messages import AIMessage

from src.agent.state import AgentState


async def refine_email(state: AgentState) -> Dict[str, Any]:
    """
    Process user's refinement request and update email draft.

    Args:
        state: Current agent state

    Returns:
        State updates for refinement
    """
    # Get refinement request from user's latest message
    messages = state["messages"]
    refinement_request = messages[-1].content if messages else ""

    # Increment iteration
    current_iteration = state.get("email_refinement_iteration", 0)
    new_iteration = current_iteration + 1

    return {
        "email_refinement_iteration": new_iteration
    }
