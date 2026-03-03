"""
Web Search Node

Executes web search queries using Tavily via MCP.
"""

from typing import Dict, Any

from src.agent.state import AgentState
from src.tools.web.tavily import WebSearchTool, NewsSearchTool
from src.agent.prompts.web_search import (
    WEB_SEARCH_SYSTEM_PROMPT,
    web_search_prompt_template,
)


async def web_search_node(state: AgentState) -> Dict[str, Any]:
    """
    Execute web search based on user query.

    This node:
    1. Identifies user's search intent (web search vs news search)
    2. Executes appropriate Tavily tool via MCP
    3. Formats and returns results with citations

    Args:
        state: Current agent state

    Returns:
        State updates with search results
    """
    messages = state.get("messages", [])
    if not messages:
        return {
            "error": "No messages to search",
            "tool_results": [],
        }

    # Get latest user message
    user_message = messages[-1].content

    # Determine search type: news search vs general web search
    # Check for news-related keywords
    news_keywords = ["news", "recent", "happening", "latest", "today's", "today",
                     "breaking", "headlines", "yesterday", "this week", "past week"]
    is_news_query = any(kw in user_message.lower() for kw in news_keywords)

    try:
        web_search_tool = NewsSearchTool() if is_news_query else WebSearchTool()

        # Extract query parameters from user message
        query = user_message

        # Execute search
        result = await web_search_tool._arun(
            query=query,
            max_results=10,
            days=3 if is_news_query else None,
            search_depth="basic"
        )

        # Return formatted result
        return {
            "tool_results": [{
                "tool": "news_search" if is_news_query else "web_search",
                "result": result,
                "query": query
            }],
            "current_step": 0,
        }

    except Exception as e:
        return {
            "error": f"Web search failed: {str(e)}",
            "tool_results": [],
        }


async def general_web_search_node(state: AgentState) -> Dict[str, Any]:
    """
    Execute general web search (non-news).

    Args:
        state: Current agent state

    Returns:
        State updates with search results
    """
    messages = state.get("messages", [])
    if not messages:
        return {
            "error": "No messages to search",
            "tool_results": [],
        }

    user_message = messages[-1].content

    try:
        tool = WebSearchTool()

        result = await tool._arun(
            query=user_message,
            max_results=10,
            search_depth="basic"
        )

        return {
            "tool_results": [{
                "tool": "web_search",
                "result": result,
                "query": user_message
            }],
            "current_step": 0,
        }

    except Exception as e:
        return {
            "error": f"Web search failed: {str(e)}",
            "tool_results": [],
        }
