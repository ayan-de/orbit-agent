"""
Memory Directory Structure Module

Defines the structure and paths for the Orbit Agent memory system.
Memory is stored as human-readable markdown files in ~/.orbit/memory/
"""

import os
from pathlib import Path
from typing import Final


# ============================================================================
# Base Memory Directory Paths
# ============================================================================

# Base directory for Orbit memory (~/.orbit/)
ORBIT_HOME: Final[Path] = Path.home() / ".orbit"

# Main memory directory (~/.orbit/memory/)
MEMORY_ROOT: Final[Path] = ORBIT_HOME / "memory"


# ============================================================================
# Subdirectory Constants
# ============================================================================

# Identity memory - stores user profile, preferences, and personal info
IDENTITY_DIR: Final[Path] = MEMORY_ROOT / "identity"

# Episodic memory - stores session logs and recent interactions
EPISODIC_DIR: Final[Path] = MEMORY_ROOT / "episodic"

# Procedural memory - stores workflows, patterns, and learned processes
PROCEDURAL_DIR: Final[Path] = MEMORY_ROOT / "procedural"


# ============================================================================
# Specific File Paths
# ============================================================================

# User profile file - stores personal information and preferences
USER_PROFILE_FILE: Final[Path] = IDENTITY_DIR / "user_profile.md"

# Workflows file - stores learned workflows and processes
WORKFLOWS_FILE: Final[Path] = PROCEDURAL_DIR / "workflows.md"

# Sessions directory - stores individual session logs
SESSIONS_DIR: Final[Path] = EPISODIC_DIR / "sessions"

# Archive directory - stores compressed/archived old sessions
ARCHIVE_DIR: Final[Path] = EPISODIC_DIR / "archive"


# ============================================================================
# Directory Structure Definition
# ============================================================================

def initialize_memory_structure() -> None:
    """
    Initialize the complete memory directory structure.

    Creates all required directories if they don't exist:
    - ~/.orbit/
    - ~/.orbit/memory/
    - ~/.orbit/memory/identity/
    - ~/.orbit/memory/identity/user_profile.md
    - ~/.orbit/memory/episodic/
    - ~/.orbit/memory/episodic/sessions/
    - ~/.orbit/memory/episodic/archive/
    - ~/.orbit/memory/procedural/
    - ~/.orbit/memory/procedural/workflows.md
    """
    directories = [
        ORBIT_HOME,
        MEMORY_ROOT,
        IDENTITY_DIR,
        EPISODIC_DIR,
        PROCEDURAL_DIR,
        SESSIONS_DIR,
        ARCHIVE_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    # Create empty markdown files if they don't exist
    files_to_create = [
        USER_PROFILE_FILE,
        WORKFLOWS_FILE,
    ]

    for file_path in files_to_create:
        if not file_path.exists():
            file_path.touch()


def get_memory_paths() -> dict[str, Path]:
    """
    Get a dictionary of all memory paths.

    Returns:
        Dictionary mapping descriptive names to Path objects
    """
    return {
        "orbit_home": ORBIT_HOME,
        "memory_root": MEMORY_ROOT,
        "identity_dir": IDENTITY_DIR,
        "episodic_dir": EPISODIC_DIR,
        "procedural_dir": PROCEDURAL_DIR,
        "user_profile": USER_PROFILE_FILE,
        "workflows": WORKFLOWS_FILE,
        "sessions_dir": SESSIONS_DIR,
        "archive_dir": ARCHIVE_DIR,
    }


def verify_memory_structure() -> bool:
    """
    Verify that the memory directory structure exists and is complete.

    Returns:
        True if all directories and files exist, False otherwise
    """
    required_paths = [
        ORBIT_HOME,
        MEMORY_ROOT,
        IDENTITY_DIR,
        EPISODIC_DIR,
        PROCEDURAL_DIR,
        SESSIONS_DIR,
        ARCHIVE_DIR,
        USER_PROFILE_FILE,
        WORKFLOWS_FILE,
    ]

    return all(path.exists() for path in required_paths)
