"""
Test for email API endpoints.
"""
import os
import sys
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from src.main import app
from src.storage.token_store import get_token_store


def test_email_status_not_connected():
    """Test email status when not connected."""
    print("Testing email status (not connected)...")

    client = TestClient(app)
    response = client.get("/api/v1/email/status?user_id=test_user")

    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.text}")

    assert response.status_code == 200
    data = response.json()
    assert data["is_connected"] == False
    assert data["email_address"] is None

    print("  ✓ Status endpoint works when not connected!")


def test_email_status_with_connection():
    """Test email status when connected."""
    print("\nTesting email status (connected)...")

    from datetime import datetime, timedelta

    # Store test tokens
    token_store = get_token_store()
    token_store.store_tokens(
        user_id="test_user",
        email_address="test@gmail.com",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        expires_at=datetime.now() + timedelta(hours=1)
    )

    client = TestClient(app)
    response = client.get("/api/v1/email/status?user_id=test_user")

    assert response.status_code == 200
    data = response.json()
    assert data["is_connected"] == True
    assert data["email_address"] == "test@gmail.com"
    assert data["provider"] == "gmail"

    # Cleanup
    token_store.delete_tokens("test_user")

    print("  ✓ Status endpoint works when connected!")


def test_email_disconnect():
    """Test email disconnect."""
    print("\nTesting email disconnect...")

    from datetime import datetime, timedelta

    # Store test tokens first
    token_store = get_token_store()
    token_store.store_tokens(
        user_id="test_user_disconnect",
        email_address="disconnect@gmail.com",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        expires_at=datetime.now() + timedelta(hours=1)
    )

    client = TestClient(app)
    response = client.post("/api/v1/email/disconnect?user_id=test_user_disconnect")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True

    # Verify disconnected
    status = token_store.get_connection_status("test_user_disconnect")
    assert status["is_connected"] == False

    print("  ✓ Disconnect endpoint works!")


def test_send_email_not_connected():
    """Test send email when not connected."""
    print("\nTesting send email (not connected)...")

    client = TestClient(app)
    response = client.post("/api/v1/email/send", json={
        "user_id": "not_connected_user",
        "to_email": "recipient@gmail.com",
        "subject": "Test",
        "body": "Test body"
    })

    assert response.status_code == 401
    data = response.json()
    assert "not connected" in data["detail"].lower()

    print("  ✓ Send endpoint requires connection!")


def test_send_email_invalid_email():
    """Test send email with invalid email."""
    print("\nTesting send email (invalid email)...")

    from datetime import datetime, timedelta

    # First connect a user
    token_store = get_token_store()
    token_store.store_tokens(
        user_id="test_invalid_email_user",
        email_address="test@gmail.com",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        expires_at=datetime.now() + timedelta(hours=1)
    )

    client = TestClient(app)
    response = client.post("/api/v1/email/send", json={
        "user_id": "test_invalid_email_user",
        "to_email": "invalid-email",
        "subject": "Test",
        "body": "Test body"
    })

    print(f"  Status: {response.status_code}")

    # The email validator may have different error messages, so just check status
    assert response.status_code == 400
    data = response.json()
    # Just check we got an error detail
    assert "detail" in data

    # Cleanup
    token_store.delete_tokens("test_invalid_email_user")

    print("  ✓ Send endpoint validates email!")


def test_get_sent_emails():
    """Test get sent emails endpoint."""
    print("\nTesting get sent emails...")

    client = TestClient(app)
    response = client.get("/api/v1/email/sent?user_id=test_user&page=1&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert "emails" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data

    print("  ✓ Sent emails endpoint works!")


def test_oauth_store_tokens():
    """Test OAuth token storage endpoint."""
    print("\nTesting OAuth token storage...")

    client = TestClient(app)
    response = client.post("/api/v1/email/oauth/store-tokens", json={
        "user_id": "test_oauth_user",
        "email_address": "oauth@gmail.com",
        "access_token": "oauth_access_token",
        "refresh_token": "oauth_refresh_token",
        "expires_in": 3600
    })

    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.text}")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["email_address"] == "oauth@gmail.com"

    # Cleanup
    token_store = get_token_store()
    token_store.delete_tokens("test_oauth_user")

    print("  ✓ OAuth token storage endpoint works!")


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Email API (Phase 4)")
    print("=" * 50)

    test_email_status_not_connected()
    test_email_status_with_connection()
    test_email_disconnect()
    test_send_email_not_connected()
    test_send_email_invalid_email()
    test_get_sent_emails()
    test_oauth_store_tokens()

    print("\n" + "=" * 50)
    print("All Phase 4 tests passed! ✓")
    print("=" * 50)
