"""
Session repository for database operations.

Provides CRUD operations for agent_sessions table.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Session, SessionStatus
from src.db.base import Base


class SessionRepository:
    """Repository for Session model."""

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
        user_id: str,
        title: Optional[str] = None,
        meta: Optional[dict] = None
    ) -> Session:
        """
        Create a new session.

        Args:
            user_id: User identifier
            title: Optional session title
            meta: Optional metadata dictionary

        Returns:
            Created Session instance
        """
        session = Session(
            user_id=user_id,
            title=title,
            status=SessionStatus.ACTIVE,
            meta=meta or {}
        )
        self.session.add(session)
        await self.session.flush()
        await self.session.refresh(session)
        return session

    async def get_by_id(self, session_id: UUID) -> Optional[Session]:
        """
        Get a session by ID.

        Args:
            session_id: Session UUID

        Returns:
            Session if found, None otherwise
        """
        stmt = select(Session).where(Session.id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: str,
        status: Optional[SessionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Session]:
        """
        Get sessions for a user, optionally filtered by status.

        Args:
            user_id: User identifier
            status: Optional status filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of Session instances
        """
        stmt = (
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            stmt = stmt.where(Session.status == status)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_sessions(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Session]:
        """
        Get active sessions for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of results

        Returns:
            List of active Session instances
        """
        return await self.get_by_user_id(
            user_id=user_id,
            status=SessionStatus.ACTIVE,
            limit=limit
        )

    async def update(
        self,
        session_id: UUID,
        title: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        meta: Optional[dict] = None
    ) -> Optional[Session]:
        """
        Update a session.

        Args:
            session_id: Session UUID
            title: Optional new title
            status: Optional new status
            meta: Optional new metadata

        Returns:
            Updated Session if found, None otherwise
        """
        session = await self.get_by_id(session_id)
        if session is None:
            return None

        if title is not None:
            session.title = title
        if status is not None:
            session.status = status
        if meta is not None:
            session.meta = meta

        await self.session.flush()
        await self.session.refresh(session)
        return session

    async def delete(self, session_id: UUID) -> bool:
        """
        Delete a session by ID.

        Args:
            session_id: Session UUID

        Returns:
            True if deleted, False if not found
        """
        session = await self.get_by_id(session_id)
        if session is None:
            return False

        await self.session.delete(session)
        await self.session.flush()
        return True

    async def soft_delete(self, session_id: UUID) -> Optional[Session]:
        """
        Soft delete a session by marking as deleted.

        Args:
            session_id: Session UUID

        Returns:
            Updated Session if found, None otherwise
        """
        return await self.update(
            session_id=session_id,
            status=SessionStatus.DELETED
        )

    async def archive(self, session_id: UUID) -> Optional[Session]:
        """
        Archive a session by marking as archived.

        Args:
            session_id: Session UUID

        Returns:
            Updated Session if found, None otherwise
        """
        return await self.update(
            session_id=session_id,
            status=SessionStatus.ARCHIVED
        )

    # ========================================
    # Query Operations
    # ========================================

    async def count_by_user_id(
        self,
        user_id: str,
        status: Optional[SessionStatus] = None
    ) -> int:
        """
        Count sessions for a user, optionally filtered by status.

        Args:
            user_id: User identifier
            status: Optional status filter

        Returns:
            Number of sessions
        """
        stmt = select(func.count()).select_from(Session).where(Session.user_id == user_id)
        if status is not None:
            stmt = stmt.where(Session.status == status)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists(self, session_id: UUID) -> bool:
        """
        Check if a session exists.

        Args:
            session_id: Session UUID

        Returns:
            True if session exists, False otherwise
        """
        return await self.get_by_id(session_id) is not None

    async def search_by_title(
        self,
        user_id: str,
        query: str,
        limit: int = 20
    ) -> List[Session]:
        """
        Search sessions by title.

        Args:
            user_id: User identifier
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching Session instances
        """
        search_pattern = f"%{query}%"
        stmt = (
            select(Session)
            .where(and_(
                Session.user_id == user_id,
                Session.title.ilike(search_pattern)
            ))
            .order_by(Session.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_sessions(
        self,
        limit: int = 50
    ) -> List[Session]:
        """
        Get recent sessions across all users.

        Args:
            limit: Maximum number of results

        Returns:
            List of recent Session instances
        """
        stmt = (
            select(Session)
            .where(Session.status == SessionStatus.ACTIVE)
            .order_by(Session.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
