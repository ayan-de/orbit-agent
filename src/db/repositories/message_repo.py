"""
Message repository for database operations.

Provides CRUD operations for agent_messages table.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Message, MessageRole, Session
from src.db.base import Base


class MessageRepository:
    """Repository for Message model."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with a database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    # ========================================
    # CRUD Operations
    # ========================================

    async def create(
        self,
        session_id: UUID,
        role: MessageRole,
        content: str,
        meta: Optional[dict] = None
    ) -> Message:
        """
        Create a new message.

        Args:
            session_id: Parent session UUID
            role: Message role (user/assistant/system/tool)
            content: Message content
            meta: Optional metadata dictionary

        Returns:
            Created Message instance
        """
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            meta=meta or {}
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def get_by_id(self, message_id: UUID) -> Optional[Message]:
        """
        Get a message by ID.

        Args:
            message_id: Message UUID

        Returns:
            Message if found, None otherwise
        """
        stmt = select(Message).where(Message.id == message_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_session_id(
        self,
        session_id: UUID,
        role: Optional[MessageRole] = None,
        limit: int = 100,
        offset: int = 0,
        order_desc: bool = True
    ) -> List[Message]:
        """
        Get messages for a session, optionally filtered by role.

        Args:
            session_id: Session UUID
            role: Optional role filter
            limit: Maximum number of results
            offset: Number of results to skip
            order_desc: If True, order by created_at descending

        Returns:
            List of Message instances
        """
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc() if order_desc else Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        if role is not None:
            stmt = stmt.where(Message.role == role)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_messages(
        self,
        session_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """
        Get user messages for a session.

        Args:
            session_id: Session UUID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of user Message instances
        """
        return await self.get_by_session_id(
            session_id=session_id,
            role=MessageRole.USER,
            limit=limit,
            offset=offset
        )

    async def get_assistant_messages(
        self,
        session_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """
        Get assistant messages for a session.

        Args:
            session_id: Session UUID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of assistant Message instances
        """
        return await self.get_by_session_id(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            limit=limit,
            offset=offset
        )

    async def get_conversation(
        self,
        session_id: UUID,
        limit: int = 100
    ) -> List[Message]:
        """
        Get full conversation (user + assistant messages) for a session.

        Args:
            session_id: Session UUID
            limit: Maximum number of results

        Returns:
            List of Message instances ordered chronologically
        """
        stmt = (
            select(Message)
            .where(and_(
                Message.session_id == session_id,
                Message.role.in_([MessageRole.USER, MessageRole.ASSISTANT])
            ))
            .order_by(Message.created_at.asc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_last_user_message(
        self,
        session_id: UUID
    ) -> Optional[Message]:
        """
        Get the last user message for a session.

        Args:
            session_id: Session UUID

        Returns:
            Last user Message if found, None otherwise
        """
        stmt = (
            select(Message)
            .where(and_(
                Message.session_id == session_id,
                Message.role == MessageRole.USER
            ))
            .order_by(Message.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_first_message(
        self,
        session_id: UUID
    ) -> Optional[Message]:
        """
        Get the first message for a session.

        Args:
            session_id: Session UUID

        Returns:
            First Message if found, None otherwise
        """
        stmt = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        message_id: UUID,
        content: Optional[str] = None,
        meta: Optional[dict] = None
    ) -> Optional[Message]:
        """
        Update a message.

        Args:
            message_id: Message UUID
            content: Optional new content
            meta: Optional new metadata

        Returns:
            Updated Message if found, None otherwise
        """
        message = await self.get_by_id(message_id)
        if message is None:
            return None

        if content is not None:
            message.content = content
        if meta is not None:
            message.meta = meta

        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def delete(self, message_id: UUID) -> bool:
        """
        Delete a message by ID.

        Note: Messages are cascade deleted when parent session is deleted.

        Args:
            message_id: Message UUID

        Returns:
            True if deleted, False if not found
        """
        message = await self.get_by_id(message_id)
        if message is None:
            return False

        await self.session.delete(message)
        await self.session.flush()
        return True

    # ========================================
    # Query Operations
    # ========================================

    async def count_by_session_id(
        self,
        session_id: UUID,
        role: Optional[MessageRole] = None
    ) -> int:
        """
        Count messages for a session, optionally filtered by role.

        Args:
            session_id: Session UUID
            role: Optional role filter

        Returns:
            Number of messages
        """
        stmt = select(func.count()).select_from(Message).where(Message.session_id == session_id)
        if role is not None:
            stmt = stmt.where(Message.role == role)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def count_by_session_ids(
        self,
        session_ids: List[UUID]
    ) -> int:
        """
        Count messages across multiple sessions.

        Args:
            session_ids: List of session UUIDs

        Returns:
            Total number of messages
        """
        stmt = select(func.count()).select_from(Message).where(Message.session_id.in_(session_ids))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists(self, message_id: UUID) -> bool:
        """
        Check if a message exists.

        Args:
            message_id: Message UUID

        Returns:
            True if message exists, False otherwise
        """
        return await self.get_by_id(message_id) is not None

    async def search_by_content(
        self,
        user_id: str,
        query: str,
        limit: int = 20
    ) -> List[Message]:
        """
        Search messages by content across user's sessions.

        Args:
            user_id: User identifier
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching Message instances
        """
        # Get user's sessions
        from src.db.repositories.session_repo import SessionRepository

        # Get messages from user's sessions that match query
        search_pattern = f"%{query}%"
        stmt = (
            select(Message)
            .join(Session, Message.session_id == Session.id)
            .where(and_(
                Session.user_id == user_id,
                Message.content.ilike(search_pattern)
            ))
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_messages(
        self,
        limit: int = 50
    ) -> List[Message]:
        """
        Get recent messages across all sessions.

        Args:
            limit: Maximum number of results

        Returns:
            List of recent Message instances
        """
        stmt = (
            select(Message)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all()

    async def get_messages_after_timestamp(
        self,
        session_id: UUID,
        timestamp: datetime
    ) -> List[Message]:
        """
        Get messages created after a specific timestamp.

        Useful for fetching incremental updates.

        Args:
            session_id: Session UUID
            timestamp: Timestamp to filter from

        Returns:
            List of Message instances after the timestamp
        """
        stmt = (
            select(Message)
            .where(and_(
                Message.session_id == session_id,
                Message.created_at > timestamp
            ))
            .order_by(Message.created_at.asc())
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_messages_with_tool_calls(
        self,
        session_id: UUID
    ) -> List[Message]:
        """
        Get messages that have tool calls.

        Useful for understanding which messages triggered tools.

        Args:
            session_id: Session UUID

        Returns:
            List of Message instances with tool calls
        """
        from src.db.models import ToolCall

        stmt = (
            select(Message)
            .join(ToolCall, Message.id == ToolCall.message_id)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
