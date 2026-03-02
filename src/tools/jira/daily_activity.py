"""
Get Jira daily activity tool.
"""
from typing import Optional
from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from src.tools.base import OrbitTool, ToolCategory, ToolInput


class DailyActivityInput(ToolInput):
    """Input schema for getting Jira daily activity."""

    user_id: str = Field(..., description="User ID for authentication")
    username: Optional[str] = Field(
        default=None,
        description="Jira username (defaults to stored username)"
    )
    days: int = Field(
        default=1,
        description="Number of days to look back (default: 1)"
    )


class DailyActivityTool(OrbitTool):
    """
    Get user's Jira activity for the specified time period.

    Summarizes tickets worked on, updated, or commented on.
    """

    name: str = "jira_daily_activity"
    description: str = "Get a summary of user's Jira activity (tickets worked on) for a time period."
    category: ToolCategory = ToolCategory.INTEGRATION
    danger_level: int = 1  # Read-only, safe
    requires_confirmation: bool = False
    args_schema: type = DailyActivityInput

    async def _arun(
        self,
        user_id: str,
        username: Optional[str] = None,
        days: int = 1
    ) -> str:
        """
        Get Jira daily activity.

        Args:
            user_id: User ID for authentication
            username: Jira username
            days: Number of days to look back

        Returns:
            Formatted activity summary
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
            # Calculate date range
            since = datetime.now() - timedelta(days=days)

            # Get user activity
            issues = await client.get_user_activity(jira_username, since)

            if not issues:
                return f"📊 No Jira activity found for the last {days} day(s)."

            # Group by status
            by_status = {}
            for issue in issues:
                fields = issue.get("fields", {})
                status = fields.get("status", {}).get("name", "Unknown")
                by_status.setdefault(status, []).append(issue)

            # Format output
            date_str = since.strftime("%B %d, %Y") if days > 1 else "today"
            output_lines = [
                f"📊 Jira Activity Summary (last {days} day(s))\n",
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"Total tickets worked on: {len(issues)}\n",
            ]

            for status, status_issues in by_status.items():
                output_lines.append(f"📌 {status}: {len(status_issues)} ticket(s)")
                for issue in status_issues:
                    key = issue.get("key")
                    summary = issue.get("fields", {}).get("summary", "No summary")
                    output_lines.append(f"   • {key}: {summary}")

            return "\n".join(output_lines)

        finally:
            await client.close()
