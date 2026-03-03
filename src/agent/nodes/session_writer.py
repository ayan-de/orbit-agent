"""
Session Writer Node

Persists conversations to file-based memory and updates session index.
This node should run after responder to save the conversation.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from src.agent.state import AgentState
from src.memory.writer import append_to_session, create_new_session
from src.memory.session_index import update_session_index

logger = logging.getLogger("orbit.session_writer")


async def session_writer_node(state: AgentState) -> Dict[str, Any]:
    """
    Write conversation messages to session file and update session index.

    This node:
    - Extracts session_id, user_id, messages from state
    - Writes each message to session file using append_to_session()
    - Skips system/tool messages (internal only)
    - Updates user session index with message count
    - Returns confirmation of write with error handling

    Args:
        state: Current agent state with messages, session_id, user_id

    Returns:
        State updates with session_write_success field
    """
    # Extract session information
    session_id = state.get("session_id")
    user_id = state.get("user_id")
    messages = state.get("messages", [])

    if not messages:
        logger.warning("No messages to write to session")
        return {"session_write_success": False, "session_write_error": "No messages"}

    if not session_id:
        logger.warning("No session_id in state, skipping session write")
        return {"session_write_success": False, "session_write_error": "No session_id"}

    try:
        # Check if session file exists, create if not
        from pathlib import Path
        from src.memory.structure import SESSIONS_DIR

        session_file = SESSIONS_DIR / f"{session_id}.md"

        if not session_file.exists():
            # Create new session file with first user message
            first_user_message = None
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    first_user_message = msg.content
                    break

            create_new_session(session_id, first_user_message)
            logger.info(f"Created new session: {session_id}")
        else:
            logger.info(f"Appending to existing session: {session_id}")

        # Write all new messages (skip system and tool messages)
        messages_written = 0
        for msg in messages:
            # Skip system messages (internal only)
            if isinstance(msg, SystemMessage):
                continue

            # Skip tool messages (internal only)
            if isinstance(msg, ToolMessage):
                continue

            # Write user messages
            if isinstance(msg, HumanMessage):
                content = _extract_message_content(msg)
                if content:
                    append_to_session(session_id, content, role="user", add_timestamp=False)
                    messages_written += 1

            # Write assistant messages
            elif isinstance(msg, AIMessage):
                # Only write the final response, not intermediate reasoning
                # Check if this is the last assistant message (the one we just generated)
                if messages.index(msg) == len(messages) - 1:
                    content = _extract_message_content(msg)
                    if content:
                        append_to_session(session_id, content, role="assistant", add_timestamp=False)
                        messages_written += 1

        # Update session index
        update_session_index(
            session_id=session_id,
            user_id=user_id,
            message_count=messages_written,
            last_active=datetime.now().isoformat(),
        )

        logger.info(f"Wrote {messages_written} messages to session {session_id}")

        return {
            "session_write_success": True,
            "messages_written": messages_written,
            "session_file": str(session_file),
        }

    except Exception as e:
        logger.error(f"Failed to write session: {e}")
        return {
            "session_write_success": False,
            "session_write_error": str(e),
        }


def _extract_message_content(message) -> Optional[str]:
    """
    Extract text content from a message.

    Handles both simple string content and list-based content (e.g., from Gemini).

    Args:
        message: A LangChain message object

    Returns:
        String content or None
    """
    content = message.content

    # Handle string content
    if isinstance(content, str):
        return content

    # Handle list content (e.g., from Gemini)
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict):
                text_parts.append(part.get("text", ""))
            elif isinstance(part, str):
                text_parts.append(part)
        return "\n".join(text_parts) if text_parts else None

    return None
