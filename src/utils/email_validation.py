"""
Email validation utilities.
"""
import re
from email_validator import validate_email, EmailNotValidError
from typing import Tuple, Optional

from ..config import settings


def validate_recipient(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an email address.

    Args:
        email: Email address to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not email:
        return False, "Email address is required"

    try:
        # Validate email format and domain
        info = validate_email(email, check_deliverability=False)
        return True, None
    except EmailNotValidError as e:
        return False, f"Invalid email address: {str(e)}"


def validate_attachment(file_size: int, content_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an attachment file.

    Args:
        file_size: File size in bytes
        content_type: MIME type of the file

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    # Check file size
    max_size = settings.EMAIL_MAX_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        return False, f"File too large (max {settings.EMAIL_MAX_SIZE_MB}MB)"

    # Check file type
    allowed_types = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'text/plain',
        'text/csv',
    ]

    if content_type not in allowed_types:
        return False, f"File type '{content_type}' not allowed. Allowed types: {', '.join(allowed_types)}"

    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove any path separators
    filename = filename.replace('/', '').replace('\\', '')

    # Remove any null bytes
    filename = filename.replace('\x00', '')

    # Keep only safe characters
    # Allow: alphanumeric, underscores, hyphens, spaces, dots, parentheses
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\s\.()]', '_', filename)

    # Limit length
    max_length = 255
    if len(sanitized) > max_length:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = name[:max_length - len(ext) - 1] + '.' + ext if ext else name[:max_length]

    return sanitized


def extract_email_addresses(text: str) -> list[str]:
    """
    Extract email addresses from text using regex.

    Args:
        text: Text to search

    Returns:
        List of found email addresses
    """
    # Common email regex pattern
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(pattern, text, re.IGNORECASE)
