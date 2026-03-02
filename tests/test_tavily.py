"""
Test for Tavily web search tool functionality.
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_web_search_tool_metadata():
    """Test WebSearchTool metadata."""
    print("Testing WebSearchTool metadata...")

    from src.tools.web.tavily import WebSearchTool

    metadata = WebSearchTool.get_metadata()

    print(f"  Name: {metadata['name']}")
    print(f"  Description: {metadata['description']}")
    print(f"  Category: {metadata['category']}")
    print(f"  Danger Level: {metadata['danger_level']}")
    print(f"  Requires Confirmation: {metadata['requires_confirmation']}")

    assert metadata['name'] == 'web_search'
    assert metadata['category'] == 'integration'
    assert metadata['danger_level'] == 1
    assert metadata['requires_confirmation'] == False

    print("  ✓ Metadata test passed!")


def test_news_search_tool_metadata():
    """Test NewsSearchTool metadata."""
    print("\nTesting NewsSearchTool metadata...")

    from src.tools.web.tavily import NewsSearchTool

    metadata = NewsSearchTool.get_metadata()

    print(f"  Name: {metadata['name']}")
    print(f"  Description: {metadata['description']}")
    print(f"  Category: {metadata['category']}")
    print(f"  Danger Level: {metadata['danger_level']}")
    print(f"  Requires Confirmation: {metadata['requires_confirmation']}")

    assert metadata['name'] == 'news_search'
    assert metadata['category'] == 'integration'
    assert metadata['danger_level'] == 1
    assert metadata['requires_confirmation'] == False

    print("  ✓ Metadata test passed!")


def test_web_search_tool_in_registry():
    """Test WebSearchTool is registered."""
    print("\nTesting WebSearchTool registration...")

    from src.tools.registry import get_tool_registry

    registry = get_tool_registry()
    tool = registry.get_tool('web_search')

    assert tool is not None, "WebSearchTool not found in registry"
    assert tool.name == 'web_search'

    print(f"  ✓ Tool registered: {tool.name}")

    # Check metadata from registry
    schema = registry.get_tool_schema('web_search')
    assert schema is not None
    print(f"  ✓ Schema available: {schema['name']}")


def test_news_search_tool_in_registry():
    """Test NewsSearchTool is registered."""
    print("\nTesting NewsSearchTool registration...")

    from src.tools.registry import get_tool_registry

    registry = get_tool_registry()
    tool = registry.get_tool('news_search')

    assert tool is not None, "NewsSearchTool not found in registry"
    assert tool.name == 'news_search'

    print(f"  ✓ Tool registered: {tool.name}")

    # Check metadata from registry
    schema = registry.get_tool_schema('news_search')
    assert schema is not None
    print(f"  ✓ Schema available: {schema['name']}")


def test_web_search_input_validation():
    """Test WebSearchInput schema validation."""
    print("\nTesting WebSearchInput validation...")

    from src.tools.web.tavily import WebSearchInput

    # Valid input
    input_data = WebSearchInput(
        query="test query",
        max_results=10,
        search_depth="basic"
    )

    assert input_data.query == "test query"
    assert input_data.max_results == 10
    assert input_data.search_depth == "basic"

    print("  ✓ Valid input test passed!")

    # Test with domain filters
    input_data = WebSearchInput(
        query="test",
        include_domains=["example.com", "test.com"],
        exclude_domains=["spam.com"]
    )

    assert input_data.include_domains == ["example.com", "test.com"]
    assert input_data.exclude_domains == ["spam.com"]

    print("  ✓ Domain filtering test passed!")


def test_news_search_input_validation():
    """Test NewsSearchInput schema validation."""
    print("\nTesting NewsSearchInput validation...")

    from src.tools.web.tavily import NewsSearchInput

    # Valid input
    input_data = NewsSearchInput(
        query="news query",
        max_results=10,
        days=7
    )

    assert input_data.query == "news query"
    assert input_data.max_results == 10
    assert input_data.days == 7

    print("  ✓ Valid input test passed!")


def test_tool_safety_levels():
    """Test that tools have appropriate safety levels."""
    print("\nTesting tool safety levels...")

    from src.tools.web.tavily import WebSearchTool, NewsSearchTool

    # Both tools should be safe (danger_level <= 2)
    metadata_web = WebSearchTool.get_metadata()
    metadata_news = NewsSearchTool.get_metadata()

    assert metadata_web['danger_level'] <= 2, "WebSearchTool should be safe"
    assert metadata_news['danger_level'] <= 2, "NewsSearchTool should be safe"

    # Neither should require confirmation
    assert metadata_web['requires_confirmation'] == False
    assert metadata_news['requires_confirmation'] == False

    # Test is_safe_for_user method
    assert WebSearchTool.is_safe_for_user(user_permission_level=1)
    assert NewsSearchTool.is_safe_for_user(user_permission_level=1)

    print("  ✓ Safety level test passed!")


def test_tool_categories():
    """Test that tools are categorized correctly."""
    print("\nTesting tool categories...")

    from src.tools.web.tavily import WebSearchTool, NewsSearchTool

    metadata_web = WebSearchTool.get_metadata()
    metadata_news = NewsSearchTool.get_metadata()

    assert metadata_web['category'] == "integration"
    assert metadata_news['category'] == "integration"

    print("  ✓ Category test passed!")


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Tavily Web Search Tools (Phase 1-2)")
    print("=" * 50)

    test_web_search_tool_metadata()
    test_news_search_tool_metadata()
    test_web_search_tool_in_registry()
    test_news_search_tool_in_registry()
    test_web_search_input_validation()
    test_news_search_input_validation()
    test_tool_safety_levels()
    test_tool_categories()

    print("\n" + "=" * 50)
    print("All tests passed! ✓")
    print("=" * 50)
