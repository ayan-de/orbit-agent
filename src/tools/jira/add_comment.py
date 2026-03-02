"""
Add comment to Jira ticket tool.
"""
from typing import Optional

from pydantic import BaseModel, Field

from src.tools.base import OrbitTool, ToolCategory, ToolInput


class AddCommentInput(ToolInput):
    """Input schema for adding a comment to a Jira ticket."""

    user_id: str = Field(..., description="User ID for authentication")
    ticket_key: str = Field(..., description="Jira ticket key (e.g., PROJ-123)")
    comment: str = Field(..., description="Comment text to add")


class AddCommentTool(OrbitTool):
    """
    Add a comment to a Jira ticket.

    Adds a text comment to an existing issue.
    """

    name: str = "jira_add_comment"
    description: str = "Add a comment to a Jira ticket."
    category: ToolCategory = ToolCategory.INTEGRATION
    danger_level: int = 3  # Moderate - modifies external system
    requires_confirmation: bool = False  # Comments are low-risk
    args_schema: type = AddCommentInput

    async def _arun(
        self,
        user_id: str,
        ticket_key: str,
        comment: str
    ) -> str:
        """
        Add comment to Jira ticket.

        Args:
            user_id: User ID for authentication
            ticket_key: Jira ticket key
            comment: Comment text

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
            # Add comment
            result = await client.add_comment(ticket_key, comment)
            comment_id = result.get("id", "unknown")

            return (
                f"✅ Comment added to {ticket_key}.\n"
                f"Comment ID: {comment_id}"
            )

        finally:
            await client.close()
