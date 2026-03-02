"""
Create Jira ticket tool.
"""
from typing import Optional

from pydantic import BaseModel, Field

from src.tools.base import OrbitTool, ToolCategory, ToolInput


class CreateTicketInput(ToolInput):
    """Input schema for creating a Jira ticket."""

    user_id: str = Field(..., description="User ID for authentication")
    project_key: str = Field(..., description="Project key (e.g., 'PROJ')")
    summary: str = Field(..., description="Ticket summary/title")
    description: Optional[str] = Field(
        default=None,
        description="Ticket description"
    )
    issue_type: str = Field(
        default="Task",
        description="Issue type (Task, Bug, Story, Epic, etc.)"
    )
    priority: Optional[str] = Field(
        default=None,
        description="Priority (High, Medium, Low, etc.)"
    )
    assignee: Optional[str] = Field(
        default=None,
        description="Assignee username"
    )


class CreateTicketTool(OrbitTool):
    """
    Create a new Jira ticket.

    Creates a new issue in the specified project.
    """

    name: str = "jira_create_ticket"
    description: "Create a new Jira ticket in a project."
    category: ToolCategory = ToolCategory.INTEGRATION
    danger_level: int = 4  # Moderate - modifies external system
    requires_confirmation: bool = True  # Always confirm before creating
    args_schema: type = CreateTicketInput

    async def _arun(
        self,
        user_id: str,
        project_key: str,
        summary: str,
        description: Optional[str] = None,
        issue_type: str = "Task",
        priority: Optional[str] = None,
        assignee: Optional[str] = None
    ) -> str:
        """
        Create Jira ticket.

        Args:
            user_id: User ID for authentication
            project_key: Project key
            summary: Ticket summary
            description: Ticket description
            issue_type: Issue type
            priority: Priority
            assignee: Assignee

        Returns:
            Success message with ticket key
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
            # Create issue
            result = await client.create_issue(
                project_key=project_key,
                summary=summary,
                issue_type=issue_type,
                description=description,
                priority=priority,
                assignee=assignee
            )

            key = result.get("key")
            id = result.get("id")

            return (
                f"✅ Ticket created successfully!\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Key: {key}\n"
                f"ID: {id}\n"
                f"Project: {project_key}\n"
                f"Summary: {summary}\n"
                f"Type: {issue_type}"
            )

        finally:
            await client.close()
