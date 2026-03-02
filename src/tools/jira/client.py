"""
Jira API client for Orbit AI Agent.

Handles authentication and API calls to Jira.
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta


class JiraClient:
    """
    Jira API client using API token authentication.

    Supports Jira Cloud and Jira Data Center/Server.
    """

    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
        timeout: int = 30
    ):
        """
        Initialize Jira client.

        Args:
            base_url: Jira instance URL (e.g., https://your-domain.atlassian.net)
            email: User email for authentication
            api_token: Jira API token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.timeout = timeout

        # Create HTTP client with basic auth
        auth = (email, api_token)
        self.client = httpx.AsyncClient(
            auth=auth,
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )

    async def search_issues(
        self,
        jql: str,
        fields: Optional[List[str]] = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        Search for issues using JQL.

        Args:
            jql: JQL query string
            fields: List of fields to return (None for default)
            max_results: Maximum number of results

        Returns:
            Jira API response with issues
        """
        if fields is None:
            fields = [
                "id", "key", "summary", "status", "priority",
                "assignee", "reporter", "created", "updated",
                "description", "issuetype", "project"
            ]

        params = {
            "jql": jql,
            "fields": ",".join(fields),
            "maxResults": max_results
        }

        response = await self.client.get(
            f"{self.base_url}/rest/api/3/search",
            params=params
        )
        response.raise_for_status()
        return response.json()

    async def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Get issue details by key.

        Args:
            issue_key: Issue key (e.g., PROJ-123)

        Returns:
            Issue details
        """
        response = await self.client.get(
            f"{self.base_url}/rest/api/3/issue/{issue_key}"
        )
        response.raise_for_status()
        return response.json()

    async def get_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get available transitions for an issue.

        Args:
            issue_key: Issue key

        Returns:
            List of available transitions
        """
        response = await self.client.get(
            f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
        )
        response.raise_for_status()
        data = response.json()
        return data.get("transitions", [])

    async def transition_issue(
        self,
        issue_key: str,
        transition_id: str
    ) -> Dict[str, Any]:
        """
        Transition an issue to a new status.

        Args:
            issue_key: Issue key
            transition_id: Transition ID (from get_transitions)

        Returns:
            Response data
        """
        response = await self.client.post(
            f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions",
            json={"transition": {"id": transition_id}}
        )
        response.raise_for_status()
        return response.json()

    async def add_comment(
        self,
        issue_key: str,
        body: str
    ) -> Dict[str, Any]:
        """
        Add a comment to an issue.

        Args:
            issue_key: Issue key
            body: Comment body (supports markdown/ADF)

        Returns:
            Created comment data
        """
        response = await self.client.post(
            f"{self.base_url}/rest/api/3/issue/{issue_key}/comment",
            json={"body": {"type": "text", "text": body}}
        )
        response.raise_for_status()
        return response.json()

    async def get_comments(
        self,
        issue_key: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get comments for an issue.

        Args:
            issue_key: Issue key
            limit: Maximum number of comments

        Returns:
            List of comments
        """
        response = await self.client.get(
            f"{self.base_url}/rest/api/3/issue/{issue_key}/comment",
            params={"maxResults": limit}
        )
        response.raise_for_status()
        data = response.json()
        return data.get("comments", [])

    async def create_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str = "Task",
        description: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new issue.

        Args:
            project_key: Project key
            summary: Issue summary/title
            issue_type: Issue type name (Task, Bug, Story, etc.)
            description: Issue description
            priority: Priority name
            assignee: Assignee email

        Returns:
            Created issue data
        """
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type}
        }

        if description:
            fields["description"] = {"type": "text", "text": description}

        if priority:
            fields["priority"] = {"name": priority}

        if assignee:
            fields["assignee"] = {"name": assignee}

        response = await self.client.post(
            f"{self.base_url}/rest/api/3/issue",
            json={"fields": fields}
        )
        response.raise_for_status()
        return response.json()

    async def get_user_activity(
        self,
        username: str,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user activity (issues worked on).

        Args:
            username: Jira username
            since: Start date for activity (defaults to 24h ago)

        Returns:
            List of activity items
        """
        if since is None:
            since = datetime.now() - timedelta(days=1)

        since_str = since.strftime("%Y-%m-%d %H:%M")

        # Search for issues where user is assignee and updated recently
        jql = f'assignee = "{username}" AND updated >= "{since_str}"'
        response = await self.search_issues(jql)

        issues = response.get("issues", [])
        return issues

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def _build_url(self, path: str) -> str:
        """Build full URL from path."""
        return f"{self.base_url}{path}"
