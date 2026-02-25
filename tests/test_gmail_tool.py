"""
Test for Gmail tool functionality.
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.gmail.send import SendEmailTool


def test_gmail_tool_metadata():
    """Test Gmail tool metadata."""
    print("Testing Gmail tool metadata...")

    metadata = SendEmailTool.get_metadata()

    print(f"  Name: {metadata['name']}")
    print(f"  Description: {metadata['description']}")
    print(f"  Category: {metadata['category']}")
    print(f"  Danger Level: {metadata['danger_level']}")
    print(f"  Requires Confirmation: {metadata['requires_confirmation']}")

    assert metadata['name'] == 'gmail_send'
    assert metadata['category'] == 'integration'
    assert metadata['danger_level'] == 3
    assert metadata['requires_confirmation'] == True

    print("  ✓ Metadata test passed!")


def test_gmail_tool_in_registry():
    """Test Gmail tool is registered."""
    print("\nTesting Gmail tool registration...")

    from src.tools.registry import get_tool_registry

    registry = get_tool_registry()
    tool = registry.get_tool('gmail_send')

    assert tool is not None, "Gmail tool not found in registry"
    assert tool.name == 'gmail_send'

    print(f"  ✓ Tool registered: {tool.name}")

    # Check metadata from registry
    schema = registry.get_tool_schema('gmail_send')
    assert schema is not None
    print(f"  ✓ Schema available: {schema['name']}")


def test_gmail_message_creation():
    """Test message creation without sending."""
    print("\nTesting Gmail message creation...")

    tool = SendEmailTool()

    # Create a message
    message = tool._create_message(
        from_email="sender@gmail.com",
        to_email="recipient@gmail.com",
        subject="Test Subject",
        body="Test body content",
        cc_emails=["cc1@gmail.com", "cc2@gmail.com"]
    )

    assert message is not None
    assert message['to'] == "recipient@gmail.com"
    assert message['from'] == "sender@gmail.com"
    assert message['subject'] == "Test Subject"
    assert message['cc'] == "cc1@gmail.com, cc2@gmail.com"

    print("  ✓ Message creation test passed!")


def test_message_with_attachment():
    """Test message with attachment."""
    print("\nTesting Gmail message with attachment...")

    tool = SendEmailTool()

    import base64

    # Create a test attachment
    attachment_content = base64.b64encode(b"Test file content").decode()

    message = tool._create_message(
        from_email="sender@gmail.com",
        to_email="recipient@gmail.com",
        subject="Test with Attachment",
        body="Email with attachment",
        attachments=[{
            "filename": "test.txt",
            "content": attachment_content,
            "mimetype": "text/plain"
        }]
    )

    assert message is not None
    # Message should have multipart body with attachment

    print("  ✓ Message with attachment test passed!")


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Gmail Tool (Phase 2)")
    print("=" * 50)

    test_gmail_tool_metadata()
    test_gmail_tool_in_registry()
    test_gmail_message_creation()
    test_message_with_attachment()

    print("\n" + "=" * 50)
    print("All Phase 2 tests passed! ✓")
    print("=" * 50)
