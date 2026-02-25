"""
Test for Gmail OAuth functionality.
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_oauth_authorization_url_generation():
    """Test OAuth authorization URL generation."""
    print("Testing OAuth authorization URL generation...")

    from src.services.gmail_oauth import get_oauth_authorization_url
    from src.config import settings

    # Test with mock credentials
    original_client_id = settings.GMAIL_CLIENT_ID
    original_secret = settings.GMAIL_CLIENT_SECRET
    settings.GMAIL_CLIENT_ID = "test_client_id.apps.googleusercontent.com"
    settings.GMAIL_CLIENT_SECRET = "test_secret"

    try:
        auth_url = get_oauth_authorization_url(user_id="test_user")

        print(f"  Generated URL: {auth_url}")
        assert "accounts.google.com" in auth_url
        assert "client_id=test_client_id" in auth_url
        assert "state=test_user" in auth_url
        assert "access_type=offline" in auth_url
        # Scope may be URL-encoded differently
        assert "gmail.send" in auth_url

        print(f"  Generated URL: {auth_url[:100]}...")
        print("  ✓ Authorization URL generated successfully!")

    finally:
        # Restore original
        settings.GMAIL_CLIENT_ID = original_client_id
        settings.GMAIL_CLIENT_SECRET = original_secret


def test_oauth_without_credentials():
    """Test OAuth with missing credentials."""
    print("\nTesting OAuth without credentials...")

    from src.services.gmail_oauth import get_oauth_authorization_url
    from src.config import settings

    # Temporarily clear credentials
    original_client_id = settings.GMAIL_CLIENT_ID
    settings.GMAIL_CLIENT_ID = None

    try:
        auth_url = get_oauth_authorization_url(user_id="test_user")
        print("  ✗ Should have raised ValueError!")
        assert False, "Should have raised ValueError"

    except ValueError as e:
        assert "not configured" in str(e).lower()
        print(f"  ✓ Correctly raised error: {str(e)[:50]}...")

    finally:
        # Restore original
        settings.GMAIL_CLIENT_ID = original_client_id


def test_oauth_instructions_exist():
    """Test that OAuth setup instructions exist."""
    print("\nTesting OAuth instructions...")

    from src.services.gmail_oauth import OAUTH_SETUP_INSTRUCTIONS

    assert OAUTH_SETUP_INSTRUCTIONS is not None
    assert len(OAUTH_SETUP_INSTRUCTIONS) > 100
    assert "OAuth 2.0 Setup" in OAUTH_SETUP_INSTRUCTIONS
    assert "GMAIL_CLIENT_ID" in OAUTH_SETUP_INSTRUCTIONS
    assert "GMAIL_CLIENT_SECRET" in OAUTH_SETUP_INSTRUCTIONS

    print("  ✓ OAuth setup instructions exist!")


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Gmail OAuth (Phase 5)")
    print("=" * 50)

    test_oauth_authorization_url_generation()
    test_oauth_without_credentials()
    test_oauth_instructions_exist()

    print("\n" + "=" * 50)
    print("All Phase 5 tests passed! ✓")
    print("=" * 50)
    print("\nOAuth Setup Instructions:")
    # Import and print instructions
    from src.services import gmail_oauth
    print(gmail_oauth.OAUTH_SETUP_INSTRUCTIONS)
