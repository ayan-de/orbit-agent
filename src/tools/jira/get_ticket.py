"""
Get Jira ticket details tool.
"""
from typing import Optional

from pydantic import BaseModel, Field

from src.tools.base import OrbitTool, ToolCategory, ToolInput


class GetTicketDetailsInput(ToolInput):
    """Input schema for getting Jira ticket details."""

    user_id: str = Field(..., description="User ID for authentication")
    ticket_key: str = Field(..., description="Jira ticket key (e.g., PROJ-123)")


class GetTicketDetailsTool(OrbitTool):
    """
    Get detailed information about a Jira ticket.

    Retrieves comprehensive ticket information including status, assignee, comments, etc.
    """

    name: str = "jira_get_ticket"
    description: "Get detailed information about a specific Jira ticket by key."
    category: ToolCategory = ToolCategory.INTEGRATION
    danger_level: int = 1  # Read-only, safe
    requires_confirmation: bool = False
    args_schema: type = GetTicketDetailsInput

    async def _arun(
        self,
        user_id: str,
        ticket_key: str
    ) -> str:
        """
        Get Jira ticket details.

        Args:
            user_id: User ID for authentication
            ticket_key: Jira ticket key

        Returns:
            Formatted ticket details
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
            # Get issue details
            issue = await client.get_issue(ticket_key)
            fields = issue.get("fields", {})

            # Extract fields
            summary = fields.get("summary", "No summary")
            description = fields.get("description", "").replace("*", "").replace("_", "")
            status = fields.get("status", {}).get("name", "Unknown")
            priority = fields.get("priority", {}).get("name", "None")
            issue_type = fields.get("issuetype", {}).get("name", "Unknown")
            assignee = fields.get("assignee", {})
            reporter = fields.get("reporter", {})
            created = fields.get("created", "")[:10] if fields.get("created") else ""
            updated = fields.get("updated", "")[:10] if fields.get("updated") else ""

            # Get recent comments
            comments = await client.get_comments(ticket_key, limit=3)

            # Format output
            output_lines = [
                f"📌 {ticket_key}: {summary}\n",
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"Status: {status}",
                f"Priority: {priority}",
                f"Type: {issue_type}",
                f"Reporter: {reporter.get('displayName', reporter.get('name', 'Unknown'))}",
                f"Assignee: {assignee.get('displayName', assignee.get('name', 'Unassigned'))}",
                f"Created: {created}",
                f"Updated: {updated}",
                "",
                "📝 Description:",
                description[:500] + "..." if len(description) > 500 else description,
            ]

            if comments:
                output_lines.extend([
                    "",
                    f"💬 Recent Comments ({len(comments)}):"
                ])
                for comment in comments[:3]:
                    author = comment.get("author", {}).get("displayName", "Unknown")
                    body = comment.get("body") or {}
                    text = body.get("content", comment.get("body", ""))
                    created = comment.get("created", "")[:10] if comment.get("created") else ""
                    output_lines.extend([
                        f"  • {author} ({created}):",
                        f"    {text[:200]}..." if len(text) > 200 else f"    {text}"
                    ])

            return "\n".join(output_lines)

        finally:
            await client.close()
