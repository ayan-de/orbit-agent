"""
Memory Writer Module

Handles writing to the Orbit Agent memory system.
Saves data as human-readable markdown files with proper formatting.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .structure import (
    ARCHIVE_DIR,
    EPISODIC_DIR,
    IDENTITY_DIR,
    PROCEDURAL_DIR,
    SESSIONS_DIR,
    USER_PROFILE_FILE,
    WORKFLOWS_FILE,
    initialize_memory_structure,
)


# ============================================================================
# Helper Functions
# ============================================================================

def _get_timestamp() -> str:
    """
    Get a formatted timestamp for memory entries.

    Returns:
        ISO 8601 formatted timestamp (e.g., "2026-03-01T14:30:00")
    """
    return datetime.now().isoformat()


def _ensure_structure() -> None:
    """
    Ensure the memory directory structure exists before writing.
    """
    initialize_memory_structure()


# ============================================================================
# Core Memory Writing Functions
# ============================================================================

def write_to_memory(
    content: str,
    memory_type: str,
    filename: str,
    add_timestamp: bool = True,
    mode: str = "w",
) -> Path:
    """
    Write content to a memory file.

    Args:
        content: The content to write
        memory_type: Type of memory ("identity", "episodic", or "procedural")
        filename: Name of the file (without path)
        add_timestamp: Whether to add a timestamp header to the content
        mode: File write mode ("w" for overwrite, "a" for append)

    Returns:
        Path to the written file

    Raises:
        ValueError: If memory_type is invalid
    """
    _ensure_structure()

    # Determine the directory based on memory type
    if memory_type == "identity":
        directory = IDENTITY_DIR
    elif memory_type == "episodic":
        directory = EPISODIC_DIR
    elif memory_type == "procedural":
        directory = PROCEDURAL_DIR
    else:
        raise ValueError(
            f"Invalid memory_type: {memory_type}. "
            "Must be 'identity', 'episodic', or 'procedural'"
        )

    # Construct file path
    file_path = directory / filename

    # Add timestamp header if requested
    if add_timestamp and content:
        timestamp = _get_timestamp()
        timestamp_header = f"\n\n---\n\n## {timestamp}\n\n"
        if mode == "a":
            # Append mode: add header before new content
            content = timestamp_header + content
        elif mode == "w":
            # Write mode: add header after content
            content = content + timestamp_header

    # Write content to file
    with open(file_path, mode, encoding="utf-8") as f:
        f.write(content)

    return file_path


# ============================================================================
# Session Logging Functions
# ============================================================================

def append_to_session(
    session_id: str,
    content: str,
    role: str = "user",
    add_timestamp: bool = True,
) -> Path:
    """
    Append an entry to a session log.

    Args:
        session_id: Unique identifier for the session
        content: The content to append
        role: Role of the message sender ("user" or "assistant")
        add_timestamp: Whether to add a timestamp

    Returns:
        Path to the session file

    Example:
        >>> append_to_session("session-123", "Hello, how are you?", "user")
        Path('/home/user/.orbit/memory/episodic/sessions/session-123.md')
    """
    _ensure_structure()

    # Construct session file path
    session_file = SESSIONS_DIR / f"{session_id}.md"

    # Format the entry
    timestamp = _get_timestamp()
    entry = f"### {role} - {timestamp}\n\n{content}\n\n"

    # Append to session file
    with open(session_file, "a", encoding="utf-8") as f:
        f.write(entry)

    return session_file


def create_new_session(session_id: str, initial_message: Optional[str] = None) -> Path:
    """
    Create a new session log file.

    Args:
        session_id: Unique identifier for the session
        initial_message: Optional initial message to write

    Returns:
        Path to the created session file
    """
    _ensure_structure()

    # Construct session file path
    session_file = SESSIONS_DIR / f"{session_id}.md"

    # Create the session file with header
    timestamp = _get_timestamp()
    header = f"# Session: {session_id}\n\n**Started:** {timestamp}\n\n---\n\n"

    # Write header to file
    with open(session_file, "w", encoding="utf-8") as f:
        f.write(header)

    # Add initial message if provided
    if initial_message:
        append_to_session(session_id, initial_message, role="user")

    return session_file


def list_sessions() -> list[str]:
    """
    List all existing session IDs.

    Returns:
        List of session IDs (filenames without .md extension)
    """
    _ensure_structure()

    sessions = []
    for file_path in SESSIONS_DIR.glob("*.md"):
        session_id = file_path.stem
        sessions.append(session_id)

    return sorted(sessions, reverse=True)


# ============================================================================
# User Profile Functions
# ============================================================================

def update_user_profile(updates: dict[str, str], append: bool = False) -> Path:
    """
    Update the user profile with new information.

    Args:
        updates: Dictionary of key-value pairs to update in the profile
        append: If True, append to existing values; if False, replace

    Returns:
        Path to the user profile file

    Example:
        >>> update_user_profile({"programming_language": "TypeScript"})
        >>> update_user_profile({"preferences": "Prefers dark mode"}, append=True)
    """
    _ensure_structure()

    # Read existing profile
    existing_content = ""
    if USER_PROFILE_FILE.exists():
        with open(USER_PROFILE_FILE, "r", encoding="utf-8") as f:
            existing_content = f.read()

    # Process updates
    new_sections = []
    for key, value in updates.items():
        formatted_key = key.replace("_", " ").title()
        section = f"### {formatted_key}\n\n{value}\n"
        new_sections.append(section)

    # Write updated profile
    with open(USER_PROFILE_FILE, "w", encoding="utf-8") as f:
        # Keep existing content if appending
        if append and existing_content:
            f.write(existing_content)
            f.write("\n\n---\n\n**Updated:** {}\n\n".format(_get_timestamp()))

        # Add new sections
        for section in new_sections:
            f.write(section)

    return USER_PROFILE_FILE


def add_preference(key: str, value: str) -> Path:
    """
    Add or update a user preference.

    Args:
        key: Preference key (e.g., "editor", "language")
        value: Preference value

    Returns:
        Path to the user profile file
    """
    return update_user_profile({"preferences": f"**{key}:** {value}"}, append=True)


# ============================================================================
# Workflow Functions
# ============================================================================

def save_workflow(name: str, description: str, steps: list[str]) -> Path:
    """
    Save a workflow to procedural memory.

    Args:
        name: Name of the workflow
        description: Description of what the workflow does
        steps: List of steps in the workflow

    Returns:
        Path to the workflows file
    """
    _ensure_structure()

    # Format the workflow entry
    timestamp = _get_timestamp()
    workflow_entry = f"""---

## Workflow: {name}

**Description:** {description}

**Created:** {timestamp}

### Steps

"""

    for i, step in enumerate(steps, 1):
        workflow_entry += f"{i}. {step}\n"

    workflow_entry += "\n"

    # Append to workflows file
    with open(WORKFLOWS_FILE, "a", encoding="utf-8") as f:
        f.write(workflow_entry)

    return WORKFLOWS_FILE


# ============================================================================
# Utility Functions
# ============================================================================

def archive_session(session_id: str) -> Path:
    """
    Move a session file to the archive directory.

    Args:
        session_id: The session ID to archive

    Returns:
        Path to the archived file
    """
    _ensure_structure()

    session_file = SESSIONS_DIR / f"{session_id}.md"
    archived_file = ARCHIVE_DIR / f"{session_id}.md"

    # Move file to archive
    if session_file.exists():
        session_file.rename(archived_file)

    return archived_file


def delete_memory_file(file_path: Path) -> bool:
    """
    Delete a memory file.

    Args:
        file_path: Path to the file to delete

    Returns:
        True if file was deleted, False otherwise
    """
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception:
        return False
