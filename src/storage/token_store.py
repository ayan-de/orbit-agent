"""
File-based token storage for Gmail OAuth tokens.
Stores encrypted tokens in a JSON file for persistent access.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from ..config import settings
from ..utils.encryption import TokenEncryption, get_encryption_key


class TokenStore:
    """
    Manages persistent storage of OAuth tokens in an encrypted JSON file.

    Data structure:
    {
        "user_id": {
            "email_address": "user@gmail.com",
            "access_token": "encrypted_access_token",
            "refresh_token": "encrypted_refresh_token",
            "token_expires_at": "2024-02-26T10:30:00Z",
            "provider": "gmail",
            "created_at": "2024-02-20T10:30:00Z",
            "updated_at": "2024-02-20T10:30:00Z"
        },
        "jira": {
            "base_url": "https://your-domain.atlassian.net",
            "email": "user@example.com",
            "api_token": "encrypted_api_token",
            "username": "user@example.com",
            "provider": "jira",
            "created_at": "2024-02-20T10:30:00Z",
            "updated_at": "2024-02-20T10:30:00Z"
        }
    }
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize token store.

        Args:
            storage_path: Path to JSON storage file. Defaults to data/tokens.json
        """
        self.storage_path = Path(storage_path or "data/tokens.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.encryption = TokenEncryption(get_encryption_key())
        self._tokens: Dict[str, Any] = self._load_tokens()

    def _load_tokens(self) -> Dict[str, Any]:
        """Load tokens from storage file."""
        if not self.storage_path.exists():
            return {}

        try:
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading tokens: {e}")
            return {}

    def _save_tokens(self) -> None:
        """Save tokens to storage file."""
        try:
            with open(self.storage_path, "w") as f:
                json.dump(self._tokens, f, indent=2, default=str)
        except IOError as e:
            print(f"Error saving tokens: {e}")
            raise

    def store_tokens(
        self,
        user_id: str,
        email_address: str,
        access_token: str,
        refresh_token: str,
        expires_at: datetime,
        provider: str = "gmail"
    ) -> None:
        """
        Store OAuth tokens for a user.

        Args:
            user_id: User identifier
            email_address: User's email address
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_at: Token expiration datetime
            provider: OAuth provider (default: "gmail")
        """
        now = datetime.now()

        self._tokens[user_id] = {
            "email_address": email_address,
            "access_token": self.encryption.encrypt(access_token),
            "refresh_token": self.encryption.encrypt(refresh_token),
            "token_expires_at": expires_at.isoformat(),
            "provider": provider,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }

        self._save_tokens()

    def get_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve tokens for a user.

        Args:
            user_id: User identifier

        Returns:
            Dict with token data (decrypted), or None if not found
        """
        if user_id not in self._tokens:
            return None

        data = self._tokens[user_id].copy()

        try:
            return {
                "user_id": user_id,
                "email_address": data["email_address"],
                "access_token": self.encryption.decrypt(data["access_token"]),
                "refresh_token": self.encryption.decrypt(data["refresh_token"]),
                "token_expires_at": datetime.fromisoformat(data["token_expires_at"]),
                "provider": data.get("provider", "gmail"),
                "created_at": datetime.fromisoformat(data["created_at"]),
                "updated_at": datetime.fromisoformat(data["updated_at"])
            }
        except Exception as e:
            print(f"Error decrypting tokens for user {user_id}: {e}")
            return None

    def update_access_token(self, user_id: str, access_token: str, expires_at: datetime) -> None:
        """
        Update access token after refresh.

        Args:
            user_id: User identifier
            access_token: New access token
            expires_at: New expiration datetime
        """
        if user_id not in self._tokens:
            return

        self._tokens[user_id]["access_token"] = self.encryption.encrypt(access_token)
        self._tokens[user_id]["token_expires_at"] = expires_at.isoformat()
        self._tokens[user_id]["updated_at"] = datetime.now().isoformat()

        self._save_tokens()

    def delete_tokens(self, user_id: str, provider: str = "gmail") -> None:
        """
        Delete tokens for a user (disconnect).

        Args:
            user_id: User identifier
            provider: Provider to disconnect (gmail, jira, or "all" for all)
        """
        if user_id not in self._tokens:
            return

        if provider == "all":
            del self._tokens[user_id]
        elif provider == "jira" and "jira" in self._tokens[user_id]:
            del self._tokens[user_id]["jira"]
            # If no providers left, delete user entry
            if not self._tokens[user_id]:
                del self._tokens[user_id]
        elif provider == "gmail":
            # Remove the main email tokens
            del self._tokens[user_id]

        self._save_tokens()

    def get_connection_status(self, user_id: str, provider: str = "gmail") -> Dict[str, Any]:
        """
        Check if a user has a connected account for a specific provider.

        Args:
            user_id: User identifier
            provider: Provider name (gmail, jira)

        Returns:
            Dict with connection status
        """
        if user_id not in self._tokens:
            return {
                "is_connected": False,
                "email_address": None,
                "provider": None,
                "base_url": None,
                "username": None
            }

        data = self._tokens[user_id]

        # Check for Jira provider
        if provider == "jira" and "jira" in data:
            jira_data = data["jira"]
            return {
                "is_connected": True,
                "email_address": jira_data.get("email"),
                "base_url": jira_data.get("base_url"),
                "username": jira_data.get("username"),
                "provider": "jira",
                "connected_at": jira_data.get("created_at")
            }

        # Default to Gmail (email)
        return {
            "is_connected": True,
            "email_address": data["email_address"],
            "provider": data.get("provider", "gmail"),
            "connected_at": data["created_at"]
        }

    def list_connections(self) -> Dict[str, Dict[str, Any]]:
        """
        List all email connections (for admin/debugging).

        Returns:
            Dict of user_id -> connection info (without sensitive tokens)
        """
        result = {}
        for user_id, data in self._tokens.items():
            result[user_id] = {
                "email_address": data["email_address"],
                "provider": data.get("provider", "gmail"),
                "created_at": data["created_at"],
                "updated_at": data["updated_at"]
            }
        return result


# Global instance
_token_store: Optional[TokenStore] = None


def get_token_store() -> TokenStore:
    """
    Get the global token store instance.

    Returns:
        TokenStore instance
    """
    global _token_store
    if _token_store is None:
        _token_store = TokenStore()
    return _token_store
