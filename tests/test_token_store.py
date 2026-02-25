"""
Simple test for token storage functionality.
"""
import os
import sys
import tempfile
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.token_store import TokenStore
from src.utils.encryption import TokenEncryption


def test_encryption():
    """Test basic encryption/decryption."""
    print("Testing encryption...")

    enc = TokenEncryption()
    original = "my_secret_token_12345"

    encrypted = enc.encrypt(original)
    print(f"  Encrypted: {encrypted}")

    decrypted = enc.decrypt(encrypted)
    print(f"  Decrypted: {decrypted}")

    assert original == decrypted, "Decryption failed!"
    print("  ✓ Encryption test passed!")


def test_token_store():
    """Test token storage operations."""
    print("\nTesting token store...")

    # Use temp file for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = f"{tmpdir}/test_tokens.json"
        store = TokenStore(storage_path)

        user_id = "test_user_123"
        email = "test@gmail.com"

        # Store tokens
        print("  Storing tokens...")
        store.store_tokens(
            user_id=user_id,
            email_address=email,
            access_token="access_token_123",
            refresh_token="refresh_token_456",
            expires_at=datetime.now() + timedelta(hours=1),
            provider="gmail"
        )

        # Get tokens
        print("  Retrieving tokens...")
        tokens = store.get_tokens(user_id)
        assert tokens is not None, "Failed to retrieve tokens"
        assert tokens["email_address"] == email
        assert tokens["access_token"] == "access_token_123"
        assert tokens["refresh_token"] == "refresh_token_456"
        print(f"  ✓ Retrieved: {tokens['email_address']}")

        # Check connection status
        print("  Checking connection status...")
        status = store.get_connection_status(user_id)
        assert status["is_connected"] == True
        assert status["email_address"] == email
        print(f"  ✓ Connected: {status}")

        # Delete tokens
        print("  Deleting tokens...")
        store.delete_tokens(user_id)
        tokens = store.get_tokens(user_id)
        assert tokens is None, "Tokens should be None after deletion"

        status = store.get_connection_status(user_id)
        assert status["is_connected"] == False
        print("  ✓ Tokens deleted!")

        print("  ✓ Token store test passed!")


def test_email_validation():
    """Test email validation."""
    print("\nTesting email validation...")

    from src.utils.email_validation import validate_recipient, validate_attachment

    # Valid email
    is_valid, error = validate_recipient("test@gmail.com")
    assert is_valid == True, "Valid email should pass"
    print("  ✓ Valid email passed")

    # Invalid email
    is_valid, error = validate_recipient("not-an-email")
    assert is_valid == False, "Invalid email should fail"
    print(f"  ✓ Invalid email rejected: {error}")

    # Valid attachment (small PDF)
    is_valid, error = validate_attachment(1024 * 1024, "application/pdf")  # 1MB
    assert is_valid == True, "Valid attachment should pass"
    print("  ✓ Valid attachment passed")

    # Too large attachment
    is_valid, error = validate_attachment(100 * 1024 * 1024, "application/pdf")  # 100MB
    assert is_valid == False, "Too large attachment should fail"
    print(f"  ✓ Large attachment rejected: {error}")

    print("  ✓ Email validation test passed!")


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Email Infrastructure (Phase 1)")
    print("=" * 50)

    test_encryption()
    test_token_store()
    test_email_validation()

    print("\n" + "=" * 50)
    print("All Phase 1 tests passed! ✓")
    print("=" * 50)
