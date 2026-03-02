"""
Tavily Web Search Tools via MCP

Provides web search capabilities using Tavily API through MCP (Model Context Protocol).
"""

import logging
from typing import Optional, List

from pydantic import BaseModel, Field

from src.tools.base import OrbitTool, ToolCategory

logger = logging.getLogger(__name__)


class WebSearchInput(BaseModel):
    """Input schema for web search tool."""

    query: str = Field(..., description="The search query to search for")
    max_results: int = Field(
        default=10, ge=1, le=50, description="Maximum number of results to return"
    )
    search_depth: str = Field(
        default="basic",
        description="Search depth: 'basic' or 'advanced'",
    )
    include_domains: Optional[List[str]] = Field(
        default=None,
        description="List of domains to include in search results",
    )
    exclude_domains: Optional[List[str]] = Field(
        default=None,
        description="List of domains to exclude from search results",
    )


class NewsSearchInput(BaseModel):
    """Input schema for news search tool."""

    query: str = Field(..., description="The news search query")
    max_results: int = Field(
        default=10, ge=1, le=50, description="Maximum number of results to return"
    )
    days: int = Field(
        default=3,
        ge=1,
        le=30,
        description="Number of days to search back for news",
    )


class WebSearchTool(OrbitTool):
    """
    Web search tool using Tavily via MCP.

    Searches the web for information and returns results with citations.
    """

    name: str = "web_search"
    description: str = (
        "Search the web for current information using Tavily. "
        "Returns results with citations and sources. "
        "Use this when you need up-to-date information or facts not in your training data. "
        "Supports domain filtering and search depth options."
    )
    category: ToolCategory = ToolCategory.INTEGRATION
    args_schema: type[BaseModel] = WebSearchInput
    danger_level: int = 1  # SAFE - read-only web search
    requires_confirmation: bool = False

    async def _arun(self, query: str, max_results: int = 10, search_depth: str = "basic",
                   include_domains: Optional[List[str]] = None,
                   exclude_domains: Optional[List[str]] = None) -> str:
        """
        Execute web search via MCP Tavily server.

        Args:
            query: Search query
            max_results: Maximum number of results
            search_depth: Search depth ('basic' or 'advanced')
            include_domains: Domains to include
            exclude_domains: Domains to exclude

        Returns:
            Formatted search results with citations
        """
        from src.mcp.client import get_mcp_client

        try:
            # Get MCP client
            self.mcp_client = get_mcp_client()

            # Ensure Tavily server is connected
            if not self.mcp_client.is_server_connected("tavily"):
                logger.info("Connecting to Tavily MCP server...")
                await self.mcp_client.connect_server("tavily")

            # Build tool parameters
            tool_params = {
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth,
            }

            if include_domains:
                tool_params["include_domains"] = include_domains
            if exclude_domains:
                tool_params["exclude_domains"] = exclude_domains

            # Execute tool via MCP
            result = await self.mcp_client.execute_tool(
                server_name="tavily",
                tool_name="search",
                **tool_params
            )

            # Format results
            return self._format_results(result, query)

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return f"Web search error: {str(e)}"

    def _format_results(self, result: dict, query: str) -> str:
        """
        Format search results with citations and sources.

        Args:
            result: Raw result from MCP tool
            query: Original search query

        Returns:
            Formatted results string
        """
        if not result or not result.get("success"):
            return f"No results found for query: {query}"

        data = result.get("data", {})
        answer = data.get("answer", "")
        sources = data.get("sources", [])

        # Build formatted response
        formatted = f"**Search Results for: {query}**\n\n"

        if answer:
            formatted += f"**Answer:**\n{answer}\n\n"

        if sources:
            formatted += "**Sources:**\n"
            for i, source in enumerate(sources, 1):
                title = source.get("title", "Untitled")
                url = source.get("url", "")
                formatted += f"{i}. {title}\n   {url}\n"

        return formatted


class NewsSearchTool(OrbitTool):
    """
    News search tool using Tavily via MCP.

    Searches for recent news articles.
    """

    name: str = "news_search"
    description: str = (
        "Search for recent news using Tavily. "
        "Returns news articles from the past few days. "
        "Use this when you need recent news or current events. "
        "Adjust the 'days' parameter to search further back."
    )
    category: ToolCategory = ToolCategory.INTEGRATION
    args_schema: type[BaseModel] = NewsSearchInput
    danger_level: int = 1  # SAFE - read-only news search
    requires_confirmation: bool = False

    async def _arun(self, query: str, max_results: int = 10, days: int = 3) -> str:
        """
        Execute news search via MCP Tavily server.

        Args:
            query: Search query
            max_results: Maximum number of results
            days: Number of days to search back

        Returns:
            Formatted news results
        """
        from src.mcp.client import get_mcp_client

        try:
            # Get MCP client
            self.mcp_client = get_mcp_client()

            # Ensure Tavily server is connected
            if not self.mcp_client.is_server_connected("tavily"):
                logger.info("Connecting to Tavily MCP server...")
                await self.mcp_client.connect_server("tavily")

            # Build tool parameters
            tool_params = {
                "query": query,
                "max_results": max_results,
                "days": days,
            }

            # Execute tool via MCP
            result = await self.mcp_client.execute_tool(
                server_name="tavily",
                tool_name="search_news",
                **tool_params
            )

            # Format results
            return self._format_news_results(result, query, days)

        except Exception as e:
            logger.error(f"News search failed: {e}")
            return f"News search error: {str(e)}"

    def _format_news_results(self, result: dict, query: str, days: int) -> str:
        """
        Format news search results.

        Args:
            result: Raw result from MCP tool
            query: Original search query
            days: Days parameter used

        Returns:
            Formatted news results string
        """
        if not result or not result.get("success"):
            return f"No news found for query: {query}"

        data = result.get("data", {})
        answer = data.get("answer", "")
        sources = data.get("sources", [])

        # Build formatted response
        formatted = f"**News Results (past {days} days) for: {query}**\n\n"

        if answer:
            formatted += f"**Summary:**\n{answer}\n\n"

        if sources:
            formatted += "**Articles:**\n"
            for i, source in enumerate(sources, 1):
                title = source.get("title", "Untitled")
                url = source.get("url", "")
                pub_date = source.get("published_date", "")
                formatted += f"{i}. {title}"
                if pub_date:
                    formatted += f" ({pub_date})"
                formatted += f"\n   {url}\n"

        return formatted
