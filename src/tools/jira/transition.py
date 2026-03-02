"""
Transition Jira ticket tool.
"""
from typing import Optional

from pydantic import BaseModel, Field

from src.tools.base import OrbitTool, ToolCategory, ToolInput


class TransitionTicketInput(ToolInput):
    """Input schema for transitioning a Jira ticket."""

    user_id: str = Field(..., description="User ID for authentication")
    ticket_key: str = Field(..., description="Jira ticket key (e.g., PROJ-123)")
    status: str = Field(..., description="Target status (e.g., 'Done', 'In Progress', 'To Do')")


class TransitionTicketTool(OrbitTool):
    """
    Transition a Jira ticket to a new status.

    Changes the workflow status of a ticket.
    """

    name: str = "jira_transition_ticket"
    description: "Transition a Jira ticket to a new status (e.g., mark as Done, move to In Progress)."
    category: ToolCategory = ToolCategory.INTEGRATION
    danger_level: int = 4  # Moderate - modifies external system
    requires_confirmation: bool = True  # Always confirm before changing status
    args_schema: type = TransitionTicketInput

    async def _arun(
        self,
        user_id: str,
        ticket_key: str,
        status: str
    ) -> str:
        """
        Transition Jira ticket to new status.

        Args:
            user_id: User ID for authentication
            ticket_key: Jira ticket key
            status: Target status name

        Returns:
            Success message
        """
        from src.tools.jira.client import JiraClient
        from src.storage.token_store import get_token_store

        # Get Jira credentials from token store
        token_store = get_token_store()
        tokens = token_store.get_tokens(user_id)

        if not tokens or "jira" not in tokens:
            raise Exception(
                "No Jira connection found. Please connect your Jira account first."
            )

        jira_config = tokens["jira"]

        # Create Jira client
        client = JiraClient(
            base_url=jira_config["base_url"],
            email=jira_config["email"],
            api_token=jira_config["api_token"]
        )

        try:
            # Get available transitions
            transitions = await client.get_transitions(ticket_key)

            # Find transition matching target status
            matching_transition = None
            for transition in transitions:
                to_status = transition.get("to", {}).get("name", "")
                if to_status.lower() == status.lower():
                    matching_transition = transition
                    break

            if not matching_transition:
                # List available transitions
                available = ", ".join([
                    t.get("to", {}).get("name", "Unknown")
                    for t in transitions
                ])
                return (
                    f"❌ Cannot transition {ticket_key} to '{status}'.\n"
                    f"Available transitions: {available}"
                )

            # Execute transition
            transition_id = matching_transition["id"]
            await client.transition_issue(ticket_key, transition_id)

            # Get updated issue to confirm new status
            issue = await client.get_issue(ticket_key)
            new_status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")

            return (
                f"✅ Successfully transitioned {ticket_key} to '{new_status}'.\n"
                f"Status change confirmed."
            )

        finally:
            await client.close()
