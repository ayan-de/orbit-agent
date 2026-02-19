"""
Sessions API endpoints.

Provides CRUD operations for agent sessions.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Session, SessionStatus, Message, MessageRole
from src.db.repositories import SessionRepository, MessageRepository
from src.memory import get_conversation_memory
from src.db.engine import get_session
from src.config import settings

router = APIRouter()


# ============================================================================
# Request/Response Schemas
# ============================================================================

class SessionCreateRequest:
    """Request schema for creating a session."""
    def __init__(self, user_id: str, title: Optional[str] = None, meta: Optional[dict] = None):
        self.user_id = user_id
        self.title = title
        self.meta = meta or {}


class SessionUpdateRequest:
    """Request schema for updating a session."""
    def __init__(self, title: Optional[str] = None, status: Optional[str] = None):
        self.title = title
        self.status = status


class SessionResponse:
    """Response schema for session."""
    def __init__(
        self,
        id: str,
        user_id: str,
        title: Optional[str],
        status: str,
        meta: dict,
        created_at: str,
        updated_at: str,
        message_count: Optional[int] = None
    ):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.status = status
        self.meta = meta
        self.created_at = created_at
        self.updated_at = updated_at
        self.message_count = message_count


class MessageResponse:
    """Response schema for message."""
    def __init__(
        self,
        id: str,
        session_id: str,
        role: str,
        content: str,
        meta: dict,
        created_at: str
    ):
        self.id = id
        self.session_id = session_id
        self.role = role
        self.content = content
        self.meta = meta
        self.created_at = created_at


# ============================================================================
# CRUD Endpoints
# ============================================================================

@router.post("", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest):
    """
    Create a new session.

    Args:
        request: Session creation data

    Returns:
        Created session
    """
    try:
        memory = await get_conversation_memory()
        session = await memory.create_session(
            user_id=request.user_id,
            title=request.title,
            meta=request.meta
        )

        return SessionResponse(
            id=str(session.id),
            user_id=session.user_id,
            title=session.title,
            status=session.status.value,
            meta=session.meta,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            message_count=0
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """
    Get a session by ID.

    Args:
        session_id: Session UUID

    Returns:
        Session details
    """
    try:
        memory = await get_conversation_memory()
        session = await memory.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )

        # Get message count
        session_db = await memory._get_db_session()
        stmt = select(Message).where(Message.session_id == session.id)
        result = await session_db.execute(stmt)
        messages = result.scalars().all()
        message_count = len(messages)

        return SessionResponse(
            id=str(session.id),
            user_id=session.user_id,
            title=session.title,
            status=session.status.value,
            meta=session.meta,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            message_count=message_count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session: {str(e)}"
        )


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    user_id: str = Query(..., description="User ID to filter sessions"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(10, ge=1, le=100, description="Maximum sessions to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Limit to sessions from last N days")
):
    """
    List sessions for a user.

    Args:
        user_id: User identifier
        status_filter: Optional status filter (active, archived, deleted)
        limit: Maximum sessions to return
        offset: Pagination offset
        days: Only return sessions from last N days

    Returns:
        List of sessions
    """
    try:
        memory = await get_conversation_memory()
        session_db = await memory._get_db_session()

        # Build base query
        stmt = select(Session).where(Session.user_id == user_id)

        # Apply status filter
        if status_filter:
            try:
                status = SessionStatus(status_filter)
                stmt = stmt.where(Session.status == status)
            except ValueError:
                pass  # Invalid status, ignore

        # Apply date filter
        if days:
            since_date = datetime.now(timezone.utc) - timedelta(days=days)
            stmt = stmt.where(Session.created_at >= since_date)

        # Apply ordering and pagination
        stmt = stmt.order_by(Session.updated_at.desc())
        stmt = stmt.limit(limit)
        stmt = stmt.offset(offset)

        result = await session_db.execute(stmt)
        sessions = result.scalars().all()

        # Get message counts for each session
        responses = []
        for session in sessions:
            msg_stmt = select(Message).where(Message.session_id == session.id)
            msg_result = await session_db.execute(msg_stmt)
            messages = msg_result.scalars().all()

            responses.append(SessionResponse(
                id=str(session.id),
                user_id=session.user_id,
                title=session.title,
                status=session.status.value,
                meta=session.meta,
                created_at=session.created_at.isoformat(),
                updated_at=session.updated_at.isoformat(),
                message_count=len(messages)
            ))

        return responses
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/recent", response_model=List[SessionResponse])
async def get_recent_sessions(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(10, ge=1, le=50, description="Maximum sessions to return"),
    days: int = Query(7, ge=1, le=90, description="Days to look back")
):
    """
    Get recent sessions for a user.

    Args:
        user_id: User identifier
        limit: Maximum sessions to return
        days: Days to look back

    Returns:
        List of recent sessions
    """
    try:
        memory = await get_conversation_memory()
        sessions = await memory.get_recent_sessions(
            user_id=user_id,
            limit=limit,
            days=days
        )

        responses = []
        for session in sessions:
            responses.append(SessionResponse(
                id=str(session.id),
                user_id=session.user_id,
                title=session.title,
                status=session.status.value,
                meta=session.meta,
                created_at=session.created_at.isoformat(),
                updated_at=session.updated_at.isoformat()
            ))

        return responses
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recent sessions: {str(e)}"
        )


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, request: SessionUpdateRequest):
    """
    Update a session.

    Args:
        session_id: Session UUID
        request: Session update data

    Returns:
        Updated session
    """
    try:
        memory = await get_conversation_memory()

        # Update title if provided
        if request.title:
            session = await memory.update_session_title(
                session_id=session_id,
                title=request.title
            )
        else:
            session = await memory.get_session(session_id)
            if not session:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session not found: {session_id}"
                )

        # Update status if provided
        if request.status:
            session_db = await memory._get_db_session()
            try:
                status = SessionStatus(request.status)
                stmt = (
                    update(Session)
                    .where(Session.id == session.id)
                    .values(status=status)
                )
                await session_db.execute(stmt)
                await session_db.commit()
                session.status = status
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {request.status}"
                )

        return SessionResponse(
            id=str(session.id),
            user_id=session.user_id,
            title=session.title,
            status=session.status.value,
            meta=session.meta,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update session: {str(e)}"
        )


@router.post("/{session_id}/archive", response_model=SessionResponse)
async def archive_session(session_id: str):
    """
    Archive a session.

    Args:
        session_id: Session UUID

    Returns:
        Archived session
    """
    try:
        memory = await get_conversation_memory()
        session = await memory.archive_session(session_id)

        return SessionResponse(
            id=str(session.id),
            user_id=session.user_id,
            title=session.title,
            status=session.status.value,
            meta=session.meta,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to archive session: {str(e)}"
        )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    soft_delete: bool = Query(True, description="Perform soft delete")
):
    """
    Delete a session.

    Args:
        session_id: Session UUID
        soft_delete: If True, mark as deleted instead of removing

    Returns:
        Success message
    """
    try:
        memory = await get_conversation_memory()
        await memory.delete_session(session_id, soft_delete=soft_delete)

        return {
            "message": "Session deleted successfully",
            "session_id": session_id,
            "soft_delete": soft_delete
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )


# ============================================================================
# Messages Endpoints
# ============================================================================

@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Maximum messages to return"),
    role_filter: Optional[str] = Query(None, description="Filter by message role")
):
    """
    Get messages for a session.

    Args:
        session_id: Session UUID
        limit: Maximum messages to return
        role_filter: Filter by role (user, assistant, system, tool)

    Returns:
        List of messages
    """
    try:
        memory = await get_conversation_memory()

        # Get messages
        messages = await memory.get_conversation_history(
            session_id=session_id,
            limit=limit
        )

        # Apply role filter if specified
        if role_filter:
            try:
                role = MessageRole(role_filter)
                messages = [m for m in messages if m.role == role]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid role: {role_filter}"
                )

        # Convert to response format
        responses = []
        for msg in messages:
            responses.append(MessageResponse(
                id=str(msg.id),
                session_id=str(msg.session_id),
                role=msg.role.value,
                content=msg.content,
                meta=msg.meta,
                created_at=msg.created_at.isoformat()
            ))

        return responses
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get messages: {str(e)}"
        )


@router.post("/{session_id}/messages", response_model=MessageResponse)
async def add_message(
    session_id: str,
    role: str = Query(..., description="Message role (user, assistant, system, tool)"),
    content: str = Query(..., description="Message content"),
    meta: Optional[dict] = Query(None, description="Optional metadata")
):
    """
    Add a message to a session.

    Args:
        session_id: Session UUID
        role: Message role
        content: Message content
        meta: Optional metadata

    Returns:
        Created message
    """
    try:
        memory = await get_conversation_memory()

        # Validate role
        try:
            msg_role = MessageRole(role)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role: {role}"
            )

        message = await memory.add_message(
            session_id=session_id,
            role=msg_role,
            content=content,
            meta=meta
        )

        return MessageResponse(
            id=str(message.id),
            session_id=str(message.session_id),
            role=message.role.value,
            content=message.content,
            meta=message.meta,
            created_at=message.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add message: {str(e)}"
        )


@router.get("/{session_id}/summary")
async def get_session_summary(
    session_id: str,
    max_messages: int = Query(20, ge=5, le=100, description="Maximum messages to summarize")
):
    """
    Get a conversation summary for a session.

    Args:
        session_id: Session UUID
        max_messages: Maximum messages to include in summary

    Returns:
        Conversation summary
    """
    try:
        memory = await get_conversation_memory()
        summary = await memory.summarize_conversation(
            session_id=session_id,
            max_messages=max_messages
        )

        if not summary:
            return {
                "session_id": session_id,
                "summary": None,
                "message": "Unable to generate summary (insufficient messages or error)"
            }

        return {
            "session_id": session_id,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.post("/{session_id}/compress")
async def compress_session(
    session_id: str,
    max_messages: int = Query(20, ge=5, le=100, description="Messages to keep uncompressed")
):
    """
    Compress session by summarizing old messages.

    Replaces old messages with a summary, keeping recent messages intact.

    Args:
        session_id: Session UUID
        max_messages: Maximum messages to keep uncompressed

    Returns:
        Result with new message count
    """
    try:
        memory = await get_conversation_memory()
        messages = await memory.summarize_and_compress(
            session_id=session_id,
            max_messages=max_messages
        )

        return {
            "session_id": session_id,
            "message_count": len(messages),
            "status": "compressed"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compress session: {str(e)}"
        )
