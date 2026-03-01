"""
Memory Reader Module

Handles reading from the Orbit Agent memory system.
Loads data from markdown files and provides structured access to memory.
"""

import re
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
    verify_memory_structure,
)


# ============================================================================
# Core Memory Reading Functions
# ============================================================================

def read_memory_file(file_path: Path) -> Optional[str]:
    """
    Read the contents of a memory file.

    Args:
        file_path: Path to the memory file

    Returns:
        File contents as string, or None if file doesn't exist

    Example:
        >>> from .structure import USER_PROFILE_FILE
        >>> content = read_memory_file(USER_PROFILE_FILE)
    """
    if not file_path.exists():
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def read_memory_by_type(
    memory_type: str,
    filename: str,
) -> Optional[str]:
    """
    Read a memory file by type and filename.

    Args:
        memory_type: Type of memory ("identity", "episodic", or "procedural")
        filename: Name of the file (without path)

    Returns:
        File contents as string, or None if file doesn't exist

    Raises:
        ValueError: If memory_type is invalid
    """
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

    file_path = directory / filename
    return read_memory_file(file_path)


# ============================================================================
# User Profile Functions
# ============================================================================

def read_user_profile() -> dict[str, str]:
    """
    Read and parse the user profile.

    Returns:
        Dictionary of profile keys and their values

    Example:
        >>> profile = read_user_profile()
        >>> profile.get("programming_language")
        "TypeScript"
    """
    content = read_memory_file(USER_PROFILE_FILE)
    if not content:
        return {}

    profile = {}

    # Parse sections (### Key\n\nvalue)
    sections = re.split(r"\n### ", content)
    for section in sections:
        if not section.strip():
            continue

        # Split key and content
        lines = section.split("\n", 1)
        if len(lines) >= 2:
            key = lines[0].strip().lower().replace(" ", "_")
            value = lines[1].strip()
            profile[key] = value

    return profile


def get_user_preference(key: str) -> Optional[str]:
    """
    Get a specific user preference.

    Args:
        key: Preference key to look up

    Returns:
        Preference value or None if not found
    """
    profile = read_user_profile()
    return profile.get(key)


# ============================================================================
# Workflow Functions
# ============================================================================

def read_workflows() -> list[dict]:
    """
    Read all workflows from procedural memory.

    Returns:
        List of workflow dictionaries, each containing:
        - name: Workflow name
        - description: Workflow description
        - created: Creation timestamp
        - steps: List of step descriptions

    Example:
        >>> workflows = read_workflows()
        >>> for w in workflows:
        ...     print(f"{w['name']}: {w['description']}")
    """
    content = read_memory_file(WORKFLOWS_FILE)
    if not content:
        return []

    workflows = []

    # Split by workflow separators
    workflow_blocks = re.split(r"\n---\n", content)

    for block in workflow_blocks:
        if not block.strip() or "## Workflow:" not in block:
            continue

        workflow = {}

        # Extract name
        name_match = re.search(r"## Workflow:\s*(.+)", block)
        if name_match:
            workflow["name"] = name_match.group(1).strip()

        # Extract description
        desc_match = re.search(r"\*\*Description:\*\*\s*(.+)", block)
        if desc_match:
            workflow["description"] = desc_match.group(1).strip()

        # Extract creation timestamp
        created_match = re.search(r"\*\*Created:\*\*\s*(.+)", block)
        if created_match:
            workflow["created"] = created_match.group(1).strip()

        # Extract steps
        steps_section = re.search(r"### Steps\n\n(.+)", block, re.DOTALL)
        if steps_section:
            steps_text = steps_section.group(1)
            # Parse numbered steps
            steps = re.findall(r"^\d+\.\s*(.+)$", steps_text, re.MULTILINE)
            workflow["steps"] = steps
        else:
            workflow["steps"] = []

        workflows.append(workflow)

    return workflows


def get_workflow(name: str) -> Optional[dict]:
    """
    Get a specific workflow by name.

    Args:
        name: Workflow name to look up

    Returns:
        Workflow dictionary or None if not found
    """
    workflows = read_workflows()
    for workflow in workflows:
        if workflow.get("name", "").lower() == name.lower():
            return workflow
    return None


def search_workflows(query: str) -> list[dict]:
    """
    Search workflows by name or description.

    Args:
        query: Search query string

    Returns:
        List of matching workflow dictionaries
    """
    workflows = read_workflows()
    query_lower = query.lower()

    return [
        w
        for w in workflows
        if query_lower in w.get("name", "").lower()
        or query_lower in w.get("description", "").lower()
    ]


# ============================================================================
# Session Functions
# ============================================================================

def read_session(session_id: str) -> Optional[str]:
    """
    Read the contents of a session file.

    Args:
        session_id: Session ID to read

    Returns:
        Session contents as string, or None if session doesn't exist
    """
    session_file = SESSIONS_DIR / f"{session_id}.md"
    return read_memory_file(session_file)


def read_recent_sessions(limit: int = 10) -> list[dict]:
    """
    Read the most recent sessions.

    Args:
        limit: Maximum number of sessions to return

    Returns:
        List of session dictionaries, each containing:
        - id: Session ID
        - content: Session content
        - modified_time: Last modification time

    Example:
        >>> recent = read_recent_sessions(5)
        >>> for session in recent:
        ...     print(f"{session['id']}: {len(session['content'])} chars")
    """
    if not SESSIONS_DIR.exists():
        return []

    sessions = []

    # Get all session files
    for session_file in SESSIONS_DIR.glob("*.md"):
        content = read_memory_file(session_file)
        if content:
            sessions.append({
                "id": session_file.stem,
                "content": content,
                "modified_time": datetime.fromtimestamp(
                    session_file.stat().st_mtime
                ),
            })

    # Sort by modification time (newest first)
    sessions.sort(key=lambda x: x["modified_time"], reverse=True)

    # Return limited results
    return sessions[:limit]


def list_sessions() -> list[str]:
    """
    List all session IDs.

    Returns:
        List of session IDs (sorted newest first)
    """
    if not SESSIONS_DIR.exists():
        return []

    sessions = []

    for session_file in SESSIONS_DIR.glob("*.md"):
        sessions.append(session_file.stem)

    # Sort by modification time
    sessions.sort(
        key=lambda sid: (SESSIONS_DIR / f"{sid}.md").stat().st_mtime,
        reverse=True,
    )

    return sessions


def get_session_info(session_id: str) -> Optional[dict]:
    """
    Get metadata about a session.

    Args:
        session_id: Session ID to query

    Returns:
        Dictionary with session metadata or None if not found
    """
    session_file = SESSIONS_DIR / f"{session_id}.md"

    if not session_file.exists():
        return None

    content = read_memory_file(session_file)
    if not content:
        return None

    # Extract start time from header
    start_time_match = re.search(r"\*\*Started:\*\*\s*(.+)", content)

    stats = {
        "id": session_id,
        "path": str(session_file),
        "created": datetime.fromtimestamp(session_file.stat().st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(session_file.stat().st_mtime).isoformat(),
        "size_bytes": session_file.stat().st_size,
        "size_chars": len(content),
    }

    if start_time_match:
        stats["started"] = start_time_match.group(1).strip()

    # Count messages
    user_messages = len(re.findall(r"\n### user", content))
    assistant_messages = len(re.findall(r"\n### assistant", content))
    stats["message_count"] = user_messages + assistant_messages
    stats["user_message_count"] = user_messages
    stats["assistant_message_count"] = assistant_messages

    return stats


# ============================================================================
# Search and Query Functions
# ============================================================================

def search_sessions(query: str, limit: int = 5) -> list[dict]:
    """
    Search sessions for a specific query.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of matching session dictionaries with snippet
    """
    recent = read_recent_sessions(limit * 2)  # Get more to filter
    query_lower = query.lower()

    results = []

    for session in recent:
        content_lower = session["content"].lower()

        if query_lower in content_lower:
            # Find a snippet containing the query
            idx = content_lower.find(query_lower)
            start = max(0, idx - 50)
            end = min(len(session["content"]), idx + len(query) + 50)
            snippet = session["content"][start:end]

            session["snippet"] = snippet
            results.append(session)

            if len(results) >= limit:
                break

    return results


def search_all_memory(query: str) -> dict[str, list]:
    """
    Search across all memory types for a query.

    Args:
        query: Search query string

    Returns:
        Dictionary with results from each memory type:
        - profile: Matching profile entries
        - workflows: Matching workflow dictionaries
        - sessions: Matching session dictionaries
    """
    results = {
        "profile": [],
        "workflows": search_workflows(query),
        "sessions": search_sessions(query, limit=5),
    }

    # Search profile
    profile = read_user_profile()
    for key, value in profile.items():
        if query.lower() in value.lower():
            results["profile"].append({"key": key, "value": value})

    return results


# ============================================================================
# Utility Functions
# ============================================================================

def get_memory_stats() -> dict:
    """
    Get statistics about the memory system.

    Returns:
        Dictionary with memory statistics
    """
    stats = {
        "structure_valid": verify_memory_structure(),
        "total_size_bytes": 0,
        "file_count": 0,
        "session_count": 0,
        "workflow_count": 0,
        "profile_exists": USER_PROFILE_FILE.exists(),
    }

    # Calculate total size
    for directory in [IDENTITY_DIR, EPISODIC_DIR, PROCEDURAL_DIR]:
        if directory.exists():
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    stats["total_size_bytes"] += file_path.stat().st_size
                    stats["file_count"] += 1

    # Count sessions
    if SESSIONS_DIR.exists():
        stats["session_count"] = len(list(SESSIONS_DIR.glob("*.md")))

    # Count workflows
    workflows = read_workflows()
    stats["workflow_count"] = len(workflows)

    return stats


def format_session_for_llm(session: dict, max_chars: int = 2000) -> str:
    """
    Format a session for inclusion in an LLM prompt.

    Args:
        session: Session dictionary
        max_chars: Maximum characters to include

    Returns:
        Formatted session string
    """
    content = session.get("content", "")

    if len(content) <= max_chars:
        return f"**Session {session['id']}:**\n{content}"

    # Truncate with ellipsis
    return f"**Session {session['id']} (truncated):**\n{content[:max_chars]}..."


def format_workflows_for_llm(limit: int = 5) -> str:
    """
    Format workflows for inclusion in an LLM prompt.

    Args:
        limit: Maximum number of workflows to include

    Returns:
        Formatted workflows string
    """
    workflows = read_workflows()[:limit]

    if not workflows:
        return "No workflows stored."

    result = "Stored Workflows:\n\n"

    for workflow in workflows:
        result += f"**{workflow['name']}:** {workflow['description']}\n"
        result += f"Steps: {', '.join(workflow['steps'][:3])}"
        if len(workflow["steps"]) > 3:
            result += f" ({len(workflow['steps']) - 3} more steps)"
        result += "\n\n"

    return result


def format_profile_for_llm() -> str:
    """
    Format user profile for inclusion in an LLM prompt.

    Returns:
        Formatted profile string
    """
    profile = read_user_profile()

    if not profile:
        return "No user profile stored."

    result = "User Profile:\n\n"

    for key, value in profile.items():
        result += f"**{key.replace('_', ' ').title()}:** {value}\n"

    return result
