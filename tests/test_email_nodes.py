"""
Test for email nodes functionality.
"""
import os
import sys
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage, AIMessage
from src.agent.nodes.email_intent import classify_email_intent
from src.agent.nodes.email_drafter import draft_email
from src.agent.nodes.email_preview import show_email_preview


async def test_email_intent_fallback():
    """Test email intent fallback extraction (no LLM required)."""
    print("Testing email intent fallback...")

    from src.agent.nodes.email_intent import _extract_email_fallback

    result = _extract_email_fallback("email 'Test message' to test@example.com")

    assert result.get('email_to') == "test@example.com"
    assert result.get('email_body') == "Test message"

    print("  ✓ Email intent fallback passed!")


async def test_email_intent_extraction():
    """Test email intent extraction (skipped - requires API key)."""
    print("\nTesting email intent extraction...")
    print("  ⚠ Skipped (requires GOOGLE_API_KEY)")


def test_email_preview_formatting():
    """Test email preview formatting."""
    print("\nTesting email preview formatting...")

    from src.agent.nodes.email_drafter import _format_email_preview

    preview = _format_email_preview(
        from_email="sender@gmail.com",
        to_email="recipient@gmail.com",
        subject="Test Subject",
        body="Test body content",
        cc=None,
        iteration=0
    )

    assert "From: sender@gmail.com" in preview
    assert "To: recipient@gmail.com" in preview
    assert "Subject: Test Subject" in preview
    assert "Test body content" in preview
    assert "'yes' to send this email" in preview

    print("  ✓ Email preview formatting passed!")


def test_email_graph_has_nodes():
    """Test that email nodes are in the graph."""
    print("\nTesting email graph nodes...")

    from src.agent.graph import get_workflow

    workflow = get_workflow()
    nodes = list(workflow.nodes.keys())

    print(f"  Graph nodes: {nodes}")

    assert "email_drafter" in nodes
    assert "email_preview" in nodes
    assert "email_sender" in nodes
    assert "email_refinement" in nodes

    print("  ✓ Email nodes in graph!")


def test_edges_include_email_routing():
    """Test that edges include email routing."""
    print("\nTesting email routing edges...")

    from src.agent.edges import route_after_classifier, route_after_email_preview

    # Test classifier routing for email
    state = {"intent": "email"}
    route = route_after_classifier(state)
    assert route == "email_drafter"
    print(f"  ✓ Email intent routes to email_drafter")

    # Test preview routing for confirmation
    state_with_yes = {
        "messages": [AIMessage(content="yes")]
    }
    route = route_after_email_preview(state_with_yes)
    assert route == "email_sender"
    print(f"  ✓ 'yes' routes to email_sender")

    # Test preview routing for refinement
    state_with_refine = {
        "messages": [AIMessage(content="make it shorter")]
    }
    route = route_after_email_preview(state_with_refine)
    assert route == "email_refinement"
    print(f"  ✓ Refinement request routes to email_refinement")


async def test_email_intent_fallback():
    """Test email intent fallback extraction."""
    print("\nTesting email intent fallback...")

    from src.agent.nodes.email_intent import _extract_email_fallback

    result = _extract_email_fallback("email 'Test message' to test@example.com")

    assert result.get('email_to') == "test@example.com"
    assert result.get('email_body') == "Test message"

    print("  ✓ Email intent fallback passed!")


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Email Nodes (Phase 3)")
    print("=" * 50)

    asyncio.run(test_email_intent_fallback())
    asyncio.run(test_email_intent_extraction())
    test_email_preview_formatting()
    test_email_graph_has_nodes()
    test_edges_include_email_routing()

    print("\n" + "=" * 50)
    print("All Phase 3 tests passed! ✓")
    print("=" * 50)
