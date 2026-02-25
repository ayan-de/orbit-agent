"""
Token encryption utility using Fernet symmetric encryption.
"""
import os
from cryptography.fernet import Fernet
from typing import Optional


class TokenEncryption:
    """Encrypts and decrypts sensitive tokens using Fernet."""

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption with a key.

        Args:
            encryption_key: Base64-encoded encryption key. If None, generates a new key.
        """
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            self.cipher = Fernet.generate_key()
            self.cipher = Fernet(self.cipher)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext.

        Args:
            plaintext: Text to encrypt

        Returns:
            Encrypted string (Base64 encoded)
        """
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext.

        Args:
            ciphertext: Encrypted string to decrypt

        Returns:
            Decrypted plaintext

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        return self.cipher.decrypt(ciphertext.encode()).decode()

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key.

        Returns:
            Base64-encoded encryption key
        """
        return Fernet.generate_key().decode()


def get_encryption_key(env_key: str = "ENCRYPTION_KEY") -> str:
    """
    Get encryption key from .env file, environment, or generate and persist a new one.

    Args:
        env_key: Environment variable name to check for existing key

    Returns:
        Encryption key
    """
    # 1. Try os environment first
    key = os.getenv(env_key)
    if key:
        return key

    # 2. Try reading directly from .env file
    try:
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{env_key}=") and not line.startswith("#"):
                        key = line.split("=", 1)[1].strip()
                        if key:
                            # Also set in current process env for subsequent calls
                            os.environ[env_key] = key
                            return key
    except Exception as e:
        print(f"Warning: Could not read .env file: {e}")

    # 3. Generate a new key and persist it
    key = TokenEncryption.generate_key()
    print(f"⚠️  No {env_key} found. Generated and saving new encryption key.")

    # Auto-persist to .env file so it's reused across restarts
    try:
        env_path = os.path.join(os.getcwd(), ".env")
        with open(env_path, "a") as f:
            f.write(f"\n# Auto-generated encryption key for token storage\n")
            f.write(f"{env_key}={key}\n")
        print(f"✓ Encryption key saved to {env_path}")
    except Exception as e:
        print(f"⚠️  Could not save encryption key to .env: {e}")
        print(f"   Manually set {env_key}={key} in your .env to avoid data loss on restart.")

    # Also set in current process env
    os.environ[env_key] = key
    return key
