"""
Web Search Tools Module

Provides tools for searching the web using Tavily via MCP (Model Context Protocol).
"""

from .tavily import WebSearchTool, NewsSearchTool, WebSearchInput, NewsSearchInput

__all__ = [
    "WebSearchTool",
    "NewsSearchTool",
    "WebSearchInput",
    "NewsSearchInput",
]
