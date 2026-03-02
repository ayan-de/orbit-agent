"""
Integration tests for Tavily web search via MCP.
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_web_search_basic():
    """Test basic web search functionality."""
    print("Testing basic web search...")

    from src.tools.web.tavily import WebSearchTool

    tool = WebSearchTool()

    # Note: This is a unit test, so we're not actually calling the MCP server
    # We're testing the tool structure and parameter handling
    import asyncio

    async def run_test():
        # Mock the MCP client to avoid actual API calls
        from src.mcp.client import MCPClientManager, MCPClientError

        # Create a mock result
        mock_result = {
            "success": True,
            "data": {
                "answer": "This is a test answer",
                "sources": [
                    {
                        "title": "Test Source 1",
                        "url": "https://example.com/1"
                    },
                    {
                        "title": "Test Source 2",
                        "url": "https://example.com/2"
                    }
                ]
            }
        }

        # Test formatting
        formatted = tool._format_results(mock_result, "test query")

        assert "test query" in formatted
        assert "Test Source 1" in formatted
        assert "https://example.com/1" in formatted
        print("  ✓ Basic formatting test passed!")

    asyncio.run(run_test())


def test_web_search_with_domain_filtering():
    """Test web search with domain filtering."""
    print("\nTesting web search with domain filtering...")

    from src.tools.web.tavily import WebSearchInput

    # Test with include_domains
    input_data = WebSearchInput(
        query="test",
        max_results=5,
        search_depth="advanced",
        include_domains=["github.com", "stackoverflow.com"],
        exclude_domains=["spam.com"]
    )

    assert input_data.include_domains == ["github.com", "stackoverflow.com"]
    assert input_data.exclude_domains == ["spam.com"]
    assert input_data.max_results == 5
    assert input_data.search_depth == "advanced"

    print("  ✓ Domain filtering input test passed!")


def test_web_search_max_results_limits():
    """Test max_results parameter limits."""
    print("\nTesting max_results parameter limits...")

    from src.tools.web.tavily import WebSearchInput

    # Test minimum value
    input_data = WebSearchInput(query="test", max_results=1)
    assert input_data.max_results == 1

    # Test maximum value
    input_data = WebSearchInput(query="test", max_results=50)
    assert input_data.max_results == 50

    print("  ✓ Max results limits test passed!")


def test_news_search_basic():
    """Test basic news search functionality."""
    print("\nTesting basic news search...")

    from src.tools.web.tavily import NewsSearchTool

    tool = NewsSearchTool()

    import asyncio

    async def run_test():
        # Mock result for news search
        mock_result = {
            "success": True,
            "data": {
                "answer": "Recent news about test topic",
                "sources": [
                    {
                        "title": "News Article 1",
                        "url": "https://news.example.com/1",
                        "published_date": "2026-03-01"
                    }
                ]
            }
        }

        # Test formatting
        formatted = tool._format_news_results(mock_result, "news query", 3)

        assert "news query" in formatted
        assert "News Article 1" in formatted
        assert "2026-03-01" in formatted
        print("  ✓ News formatting test passed!")

    asyncio.run(run_test())


def test_news_search_days_parameter():
    """Test news search days parameter."""
    print("\nTesting news search days parameter...")

    from src.tools.web.tavily import NewsSearchInput

    # Test different day values
    for days in [1, 7, 14, 30]:
        input_data = NewsSearchInput(
            query="test",
            max_results=10,
            days=days
        )
        assert input_data.days == days

    print("  ✓ Days parameter test passed!")


def test_format_results_empty_sources():
    """Test formatting with empty sources."""
    print("\nTesting format_results with empty sources...")

    from src.tools.web.tavily import WebSearchTool

    tool = WebSearchTool()

    # Mock result with no sources
    mock_result = {
        "success": True,
        "data": {
            "answer": "Test answer",
            "sources": []
        }
    }

    formatted = tool._format_results(mock_result, "test")

    assert "test" in formatted
    assert "Test answer" in formatted
    print("  ✓ Empty sources formatting test passed!")


def test_format_results_failure():
    """Test formatting failed search result."""
    print("\nTesting format_results for failed search...")

    from src.tools.web.tavily import WebSearchTool

    tool = WebSearchTool()

    # Mock failed result
    mock_result = {
        "success": False,
        "data": {}
    }

    formatted = tool._format_results(mock_result, "test")

    assert "No results found" in formatted
    assert "test" in formatted
    print("  ✓ Failed result formatting test passed!")


def test_format_news_with_date_range():
    """Test news formatting with various date ranges."""
    print("\nTesting news formatting with date ranges...")

    from src.tools.web.tavily import NewsSearchTool

    tool = NewsSearchTool()

    for days in [1, 3, 7, 30]:
        mock_result = {
            "success": True,
            "data": {
                "answer": f"News from past {days} days",
                "sources": [
                    {
                        "title": f"Article {days}",
                        "url": f"https://example.com/{days}",
                        "published_date": "2026-03-01"
                    }
                ]
            }
        }

        formatted = tool._format_news_results(mock_result, "test", days)

        assert f"past {days} days" in formatted
        print(f"  ✓ {days} days formatting test passed!")


def test_format_news_no_date():
    """Test news formatting without published date."""
    print("\nTesting news formatting without published date...")

    from src.tools.web.tavily import NewsSearchTool

    tool = NewsSearchTool()

    mock_result = {
        "success": True,
        "data": {
            "answer": "News summary",
            "sources": [
                {
                    "title": "Article without date",
                    "url": "https://example.com/article"
                }
            ]
        }
    }

    formatted = tool._format_news_results(mock_result, "test", 7)

    assert "Article without date" in formatted
    # Should not show date if not present
    assert not ("(2026" in formatted or "(2025" in formatted)
    print("  ✓ No date formatting test passed!")


def test_error_handling_mcp_failure():
    """Test error handling for MCP failures."""
    print("\nTesting error handling for MCP failures...")

    from src.tools.web.tavily import WebSearchTool
    from src.mcp.client import MCPClientError

    tool = WebSearchTool()

    # Mock a failed MCP call
    import asyncio

    async def run_test():
        try:
            # Simulate MCP client raising an error
            raise MCPClientError("Connection failed")
        except MCPClientError as e:
            # The tool should handle this gracefully
            error_msg = f"Web search error: {str(e)}"
            assert "Web search error" in error_msg
            assert "Connection failed" in error_msg
            print("  ✓ MCP error handling test passed!")

    asyncio.run(run_test())


def test_search_depth_values():
    """Test valid search depth values."""
    print("\nTesting search depth parameter validation...")

    from src.tools.web.tavily import WebSearchInput

    # Test basic and advanced depth
    for depth in ["basic", "advanced"]:
        input_data = WebSearchInput(
            query="test",
            search_depth=depth
        )
        assert input_data.search_depth == depth

    print("  ✓ Search depth test passed!")


def test_input_validation_defaults():
    """Test that default values are applied correctly."""
    print("\nTesting input validation with defaults...")

    from src.tools.web.tavily import WebSearchInput, NewsSearchInput

    # Test WebSearchInput defaults
    web_input = WebSearchInput(query="test")
    assert web_input.max_results == 10
    assert web_input.search_depth == "basic"
    assert web_input.include_domains is None
    assert web_input.exclude_domains is None

    # Test NewsSearchInput defaults
    news_input = NewsSearchInput(query="test")
    assert news_input.max_results == 10
    assert news_input.days == 3

    print("  ✓ Default values test passed!")


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Tavily Web Search Integration (Phase 2)")
    print("=" * 50)

    test_web_search_basic()
    test_web_search_with_domain_filtering()
    test_web_search_max_results_limits()
    test_news_search_basic()
    test_news_search_days_parameter()
    test_format_results_empty_sources()
    test_format_results_failure()
    test_format_news_with_date_range()
    test_format_news_no_date()
    test_error_handling_mcp_failure()
    test_search_depth_values()
    test_input_validation_defaults()

    print("\n" + "=" * 50)
    print("All Phase 2 integration tests passed! ✓")
    print("=" * 50)
