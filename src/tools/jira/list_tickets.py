"""
List Jira tickets tool.
"""
from typing import Optional, List

from pydantic import BaseModel, Field

from src.tools.base import OrbitTool, ToolCategory, ToolInput
from src.config import settings


class ListTicketsInput(ToolInput):
    """Input schema for listing Jira tickets."""

    user_id: str = Field(..., description="User ID for authentication")
    username: Optional[str] = Field(
        default=None,
        description="Jira username (defaults to user's email)"
    )
    status: Optional[str] = Field(
        default=None,
        description="Filter by status (e.g., 'In Progress', 'Done')"
    )
    project_key: Optional[str] = Field(
        default=None,
        description="Filter by project key (e.g., 'PROJ')"
    )
    limit: int = Field(
        default=20,
        description="Maximum number of tickets to return"
    )


class ListTicketsTool(OrbitTool):
    """
    List assigned Jira tickets for a user.

    Retrieves tickets assigned to the user with optional filters.
    """

    name: str = "jira_list_tickets"
    description: str = "List Jira tickets assigned to the user. Supports filtering by status, project, and limiting results."
    category: ToolCategory = ToolCategory.INTEGRATION
    danger_level: int = 1  # Read-only, safe
    requires_confirmation: bool = False
    args_schema: type = ListTicketsInput

    async def _arun(
        self,
        user_id: str,
        username: Optional[str] = None,
        status: Optional[str] = None,
        project_key: Optional[str] = None,
        limit: int = 20
    ) -> str:
        """
        List Jira tickets for the user.

        Args:
            user_id: User ID for authentication
            username: Jira username (defaults to email)
            status: Filter by status
            project_key: Filter by project
            limit: Maximum tickets to return

        Returns:
            Formatted list of tickets
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
        jira_username = username or jira_config.get("username")

        # Create Jira client
        client = JiraClient(
            base_url=jira_config["base_url"],
            email=jira_config["email"],
            api_token=jira_config["api_token"]
        )

        try:
            # Build JQL query
            jql_parts = [f'assignee = "{jira_username}"']

            if status:
                jql_parts.append(f'status = "{status}"')

            if project_key:
                jql_parts.append(f'project = "{project_key}"')

            jql = " AND ".join(jql_parts)

            # Search for issues
            result = await client.search_issues(jql, max_results=limit)

            # Format output
            issues = result.get("issues", [])

            if not issues:
                return "No tickets found matching your criteria."

            # Build formatted response
            output_lines = [f"Found {len(issues)} ticket(s):\n"]

            for issue in issues:
                key = issue.get("key")
                fields = issue.get("fields", {})

                summary = fields.get("summary", "No summary")
                status_name = fields.get("status", {}).get("name", "Unknown")
                priority_name = fields.get("priority", {}).get("name", "None")
                issue_type = fields.get("issuetype", {}).get("name", "Unknown")
                updated = fields.get("updated", "")

                output_lines.append(
                    f"📌 {key}: {summary}\n"
                    f"   Status: {status_name} | Priority: {priority_name} | Type: {issue_type}"
                )

            return "\n".join(output_lines)

        finally:
            await client.close()
