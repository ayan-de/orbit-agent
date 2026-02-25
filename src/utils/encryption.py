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
    Get encryption key from environment or generate a new one.

    Args:
        env_key: Environment variable name to check for existing key

    Returns:
        Encryption key
    """
    key = os.getenv(env_key)
    if not key:
        # Generate a new key for development
        key = TokenEncryption.generate_key()
        # In production, you'd want to persist this key securely
        print(f"Generated new encryption key: {key}")
        print(f"Set {env_key}={key} in your .env file to reuse this key.")
    return key
