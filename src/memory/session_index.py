"""
Session Index Module

Provides fast lookups for user sessions without file system scans.
Maintains a JSON index file for quick access to session metadata.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .structure import (
    EPISODIC_DIR,
    SESSIONS_DIR,
    initialize_memory_structure,
)

logger = logging.getLogger("orbit.session_index")

# Session index file path
SESSION_INDEX_FILE = EPISODIC_DIR / "session_index.json"


def _ensure_structure() -> None:
    """Ensure memory directory structure exists."""
    initialize_memory_structure()


def _load_index() -> Dict[str, Any]:
    """
    Load the session index from disk.

    Returns:
        Dictionary containing session index data
    """
    _ensure_structure()

    if SESSION_INDEX_FILE.exists():
        try:
            with open(SESSION_INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load session index: {e}")
            return {"sessions": {}, "users": {}, "total_sessions": 0, "total_messages": 0}

    # Return default empty index
    return {
        "sessions": {},
        "users": {},
        "total_sessions": 0,
        "total_messages": 0,
    }


def _save_index(index: Dict[str, Any]) -> None:
    """
    Save the session index to disk.

    Args:
        index: Dictionary containing session index data
    """
    _ensure_structure()

    try:
        with open(SESSION_INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save session index: {e}")


def update_session_index(
    session_id: str,
    user_id: Optional[str] = None,
    message_count: int = 1,
    last_active: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Update or create a session entry in the index.

    Args:
        session_id: Unique identifier for the session
        user_id: Optional user ID associated with the session
        message_count: Number of messages to add (default: 1)
        last_active: Optional ISO timestamp of last activity
        metadata: Optional additional session metadata

    Returns:
        Updated session index entry
    """
    index = _load_index()

    # Get current timestamp if not provided
    if last_active is None:
        last_active = datetime.now().isoformat()

    # Update or create session entry
    if session_id not in index["sessions"]:
        # New session
        index["sessions"][session_id] = {
            "created_at": last_active,
            "last_active": last_active,
            "message_count": message_count,
            "user_id": user_id,
            "metadata": metadata or {},
        }
        index["total_sessions"] += 1
    else:
        # Update existing session
        index["sessions"][session_id]["last_active"] = last_active
        index["sessions"][session_id]["message_count"] += message_count
        if user_id:
            index["sessions"][session_id]["user_id"] = user_id
        if metadata:
            index["sessions"][session_id]["metadata"].update(metadata)

    # Update user index
    if user_id:
        if user_id not in index["users"]:
            index["users"][user_id] = {
                "total_sessions": 0,
                "total_messages": 0,
                "sessions": [],
            }
        index["users"][user_id]["total_messages"] += message_count
        if session_id not in index["users"][user_id]["sessions"]:
            index["users"][user_id]["sessions"].append(session_id)
            index["users"][user_id]["total_sessions"] += 1

    # Update totals
    index["total_messages"] += message_count

    # Save updated index
    _save_index(index)

    return index["sessions"][session_id]


def get_user_sessions(
    user_id: str,
    limit: int = 10,
    active_only: bool = False,
) -> List[Dict[str, Any]]:
    """
    Retrieve sessions for a specific user from the index.

    Args:
        user_id: The user ID to look up
        limit: Maximum number of sessions to return
        active_only: If True, only return sessions from last 30 days

    Returns:
        List of session dictionaries with metadata
    """
    index = _load_index()

    if user_id not in index["users"]:
        return []

    user_data = index["users"][user_id]
    sessions = []

    # Get session IDs for user
    for session_id in user_data["sessions"][:limit]:
        if session_id in index["sessions"]:
            session = index["sessions"][session_id]

            # Filter by active status if requested
            if active_only:
                try:
                    last_active = datetime.fromisoformat(session["last_active"])
                    days_active = (datetime.now() - last_active).days
                    if days_active > 30:
                        continue
                except Exception:
                    pass

            sessions.append(session)

    return sessions


def get_session_info(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a specific session from the index.

    Args:
        session_id: The session ID to look up

    Returns:
        Session dictionary or None if not found
    """
    index = _load_index()
    return index["sessions"].get(session_id)


def list_all_sessions(limit: int = 20) -> List[Dict[str, Any]]:
    """
    List all sessions from the index, sorted by last_active.

    Args:
        limit: Maximum number of sessions to return

    Returns:
        List of session dictionaries
    """
    index = _load_index()

    # Sort sessions by last_active (most recent first)
    sorted_sessions = sorted(
        index["sessions"].values(),
        key=lambda x: x["last_active"],
        reverse=True,
    )

    return sorted_sessions[:limit]


def delete_session_from_index(session_id: str) -> bool:
    """
    Delete a session entry from the index.

    Args:
        session_id: The session ID to delete

    Returns:
        True if session was deleted, False otherwise
    """
    index = _load_index()

    if session_id not in index["sessions"]:
        return False

    session = index["sessions"][session_id]
    user_id = session.get("user_id")

    # Remove from user index if applicable
    if user_id and user_id in index["users"]:
        user_sessions = index["users"][user_id]["sessions"]
        if session_id in user_sessions:
            user_sessions.remove(session_id)
            index["users"][user_id]["total_sessions"] -= 1
            index["users"][user_id]["total_messages"] -= session["message_count"]

    # Remove session entry
    index["total_sessions"] -= 1
    index["total_messages"] -= session["message_count"]
    del index["sessions"][session_id]

    # Save updated index
    _save_index(index)

    return True


def get_index_stats() -> Dict[str, Any]:
    """
    Get statistics about the session index.

    Returns:
        Dictionary with index statistics
    """
    index = _load_index()

    return {
        "total_sessions": index["total_sessions"],
        "total_messages": index["total_messages"],
        "total_users": len(index["users"]),
        "index_file": str(SESSION_INDEX_FILE),
        "index_exists": SESSION_INDEX_FILE.exists(),
    }
