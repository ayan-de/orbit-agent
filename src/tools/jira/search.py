"""
Search Jira tickets tool.
"""
from typing import Optional

from pydantic import BaseModel, Field

from src.tools.base import OrbitTool, ToolCategory, ToolInput


class SearchTicketsInput(ToolInput):
    """Input schema for searching Jira tickets."""

    user_id: str = Field(..., description="User ID for authentication")
    query: str = Field(..., description="Search query or JQL string")
    project_key: Optional[str] = Field(
        default=None,
        description="Filter by project key (e.g., 'PROJ')"
    )
    limit: int = Field(
        default=20,
        description="Maximum number of results"
    )


class SearchTicketsTool(OrbitTool):
    """
    Search Jira tickets by query.

    Performs a JQL-based search for tickets matching criteria.
    """

    name: str = "jira_search_tickets"
    description: str = "Search Jira tickets by query text or JQL. Supports filtering by project."
    category: ToolCategory = ToolCategory.INTEGRATION
    danger_level: int = 1  # Read-only, safe
    requires_confirmation: bool = False
    args_schema: type = SearchTicketsInput

    async def _arun(
        self,
        user_id: str,
        query: str,
        project_key: Optional[str] = None,
        limit: int = 20
    ) -> str:
        """
        Search Jira tickets.

        Args:
            user_id: User ID for authentication
            query: Search query or JQL
            project_key: Filter by project
            limit: Maximum results

        Returns:
            Formatted search results
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
            # Build JQL query
            # If query looks like natural language, search in summary and description
            # If it looks like JQL (contains operators), use as-is
            jql_operators = ["=", "!=", ">", "<", ">=", "<=", "~", "!~", "in", "not in", "and", "or", "is", "was"]
            is_jql = any(op in query.lower() for op in jql_operators)

            if is_jql:
                jql = query
            else:
                # Natural language search
                jql_parts = [f'summary ~ "{query}" or description ~ "{query}"']

                if project_key:
                    jql_parts.append(f'project = "{project_key}"')

                jql = " AND ".join(jql_parts)

            # Search for issues
            result = await client.search_issues(jql, max_results=limit)

            # Format output
            issues = result.get("issues", [])

            if not issues:
                return f"🔍 No tickets found matching: '{query}'"

            output_lines = [
                f"🔍 Found {len(issues)} ticket(s) for '{query}':\n"
            ]

            for issue in issues:
                key = issue.get("key")
                fields = issue.get("fields", {})

                summary = fields.get("summary", "No summary")
                status_name = fields.get("status", {}).get("name", "Unknown")
                priority_name = fields.get("priority", {}).get("name", "None")
                assignee = fields.get("assignee", {}).get("displayName", "Unassigned")

                output_lines.append(
                    f"📌 {key}: {summary}\n"
                    f"   Status: {status_name} | Priority: {priority_name} | Assignee: {assignee}"
                )

            return "\n".join(output_lines)

        finally:
            await client.close()
