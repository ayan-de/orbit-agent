"""
Email preview node - shows email preview to user.
"""
from typing import Dict, Any
from langchain_core.messages import AIMessage

from src.agent.state import AgentState


async def show_email_preview(state: AgentState) -> Dict[str, Any]:
    """
    Show email preview to user for confirmation.

    Args:
        state: Current agent state

    Returns:
        State updates with preview message
    """
    preview = state.get("email_confirmation_prompt")

    if not preview:
        return {
            "messages": [AIMessage(content="No email draft to preview.")]
        }

    return {
        "messages": [AIMessage(content=preview)],
        "email_needs_confirmation": True
    }
