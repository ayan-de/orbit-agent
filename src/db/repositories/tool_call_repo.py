"""
Tool call repository for database operations.

Provides CRUD operations for agent_tool_calls table.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ToolCall, ToolCallStatus, Message, Session
from src.db.base import Base


class ToolCallRepository:
    """Repository for ToolCall model."""

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
        tool_name: str,
        inputs: dict,
        message_id: Optional[UUID] = None
    ) -> ToolCall:
        """
        Create a new tool call with PENDING status.

        Args:
            session_id: Parent session UUID
            tool_name: Name of the tool being called
            inputs: Input parameters for the tool
            message_id: Optional related message UUID

        Returns:
            Created ToolCall instance
        """
        tool_call = ToolCall(
            session_id=session_id,
            tool_name=tool_name,
            inputs=inputs,
            status=ToolCallStatus.PENDING,
            message_id=message_id
        )
        self.session.add(tool_call)
        await self.session.flush()
        await self.session.refresh(tool_call)
        return tool_call

    async def get_by_id(self, tool_call_id: UUID) -> Optional[ToolCall]:
        """
        Get a tool call by ID.

        Args:
            tool_call_id: ToolCall UUID

        Returns:
            ToolCall if found, None otherwise
        """
        stmt = select(ToolCall).where(ToolCall.id == tool_call_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_session_id(
        self,
        session_id: UUID,
        status: Optional[ToolCallStatus] = None,
        tool_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ToolCall]:
        """
        Get tool calls for a session, optionally filtered.

        Args:
            session_id: Session UUID
            status: Optional status filter
            tool_name: Optional tool name filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of ToolCall instances
        """
        stmt = (
            select(ToolCall)
            .where(ToolCall.session_id == session_id)
            .order_by(ToolCall.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            stmt = stmt.where(ToolCall.status == status)
        if tool_name is not None:
            stmt = stmt.where(ToolCall.tool_name == tool_name)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_message_id(
        self,
        message_id: UUID
    ) -> List[ToolCall]:
        """
        Get tool calls for a specific message.

        Args:
            message_id: Message UUID

        Returns:
            List of ToolCall instances
        """
        stmt = (
            select(ToolCall)
            .where(ToolCall.message_id == message_id)
            .order_by(ToolCall.created_at.asc())
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        tool_call_id: UUID,
        status: ToolCallStatus,
        outputs: Optional[dict] = None,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[ToolCall]:
        """
        Update tool call status and results.

        Args:
            tool_call_id: ToolCall UUID
            status: New status (PENDING/RUNNING/COMPLETED/FAILED)
            outputs: Optional tool output data
            execution_time_ms: Optional execution duration
            error_message: Optional error message

        Returns:
            Updated ToolCall if found, None otherwise
        """
        tool_call = await self.get_by_id(tool_call_id)
        if tool_call is None:
            return None

        tool_call.status = status
        if outputs is not None:
            tool_call.outputs = outputs
        if execution_time_ms is not None:
            tool_call.execution_time_ms = execution_time_ms
        if error_message is not None:
            tool_call.error_message = error_message

        await self.session.flush()
        await self.session.refresh(tool_call)
        return tool_call

    async def mark_running(self, tool_call_id: UUID) -> Optional[ToolCall]:
        """
        Mark a tool call as RUNNING.

        Args:
            tool_call_id: ToolCall UUID

        Returns:
            Updated ToolCall if found, None otherwise
        """
        return await self.update_status(tool_call_id, ToolCallStatus.RUNNING)

    async def mark_completed(
        self,
        tool_call_id: UUID,
        outputs: dict,
        execution_time_ms: int
    ) -> Optional[ToolCall]:
        """
        Mark a tool call as COMPLETED with results.

        Args:
            tool_call_id: ToolCall UUID
            outputs: Tool output data
            execution_time_ms: Execution duration in milliseconds

        Returns:
            Updated ToolCall if found, None otherwise
        """
        return await self.update_status(
            tool_call_id,
            ToolCallStatus.COMPLETED,
            outputs=outputs,
            execution_time_ms=execution_time_ms
        )

    async def mark_failed(
        self,
        tool_call_id: UUID,
        error_message: str
    ) -> Optional[ToolCall]:
        """
        Mark a tool call as FAILED with error message.

        Args:
            tool_call_id: ToolCall UUID
            error_message: Error description

        Returns:
            Updated ToolCall if found, None otherwise
        """
        return await self.update_status(
            tool_call_id,
            ToolCallStatus.FAILED,
            error_message=error_message
        )

    async def delete(self, tool_call_id: UUID) -> bool:
        """
        Delete a tool call by ID.

        Note: Tool calls are cascade deleted when parent session/message is deleted.

        Args:
            tool_call_id: ToolCall UUID

        Returns:
            True if deleted, False if not found
        """
        tool_call = await self.get_by_id(tool_call_id)
        if tool_call is None:
            return False

        await self.session.delete(tool_call)
        await self.session.flush()
        return True

    # ========================================
    # Query Operations
    # ========================================

    async def count_by_session_id(
        self,
        session_id: UUID,
        status: Optional[ToolCallStatus] = None
    ) -> int:
        """
        Count tool calls for a session, optionally filtered by status.

        Args:
            session_id: Session UUID
            status: Optional status filter

        Returns:
            Number of tool calls
        """
        stmt = select(func.count()).select_from(ToolCall).where(ToolCall.session_id == session_id)
        if status is not None:
            stmt = stmt.where(ToolCall.status == status)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def count_by_tool_name(
        self,
        tool_name: str,
        status: Optional[ToolCallStatus] = None
    ) -> int:
        """
        Count tool calls for a specific tool.

        Args:
            tool_name: Name of the tool
            status: Optional status filter

        Returns:
            Number of tool calls
        """
        stmt = select(func.count()).select_from(ToolCall).where(ToolCall.tool_name == tool_name)
        if status is not None:
            stmt = stmt.where(ToolCall.status == status)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_pending_calls(
        self,
        limit: int = 50
    ) -> List[ToolCall]:
        """
        Get all pending tool calls across all sessions.

        Args:
            limit: Maximum number of results

        Returns:
            List of pending ToolCall instances
        """
        stmt = (
            select(ToolCall)
            .where(ToolCall.status == ToolCallStatus.PENDING)
            .order_by(ToolCall.created_at.asc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_failed_calls(
        self,
        session_id: UUID,
        limit: int = 20
    ) -> List[ToolCall]:
        """
        Get failed tool calls for a session.

        Args:
            session_id: Session UUID
            limit: Maximum number of results

        Returns:
            List of failed ToolCall instances
        """
        return await self.get_by_session_id(
            session_id=session_id,
            status=ToolCallStatus.FAILED,
            limit=limit
        )

    async def get_successful_calls(
        self,
        session_id: UUID,
        limit: int = 20
    ) -> List[ToolCall]:
        """
        Get successful tool calls for a session.

        Args:
            session_id: Session UUID
            limit: Maximum number of results

        Returns:
            List of completed ToolCall instances
        """
        return await self.get_by_session_id(
            session_id=session_id,
            status=ToolCallStatus.COMPLETED,
            limit=limit
        )

    async def get_tool_statistics(
        self,
        session_id: UUID
    ) -> dict:
        """
        Get statistics about tool calls for a session.

        Args:
            session_id: Session UUID

        Returns:
            Dictionary with call counts by status and tool name
        """
        # Count by status
        status_stmt = (
            select(ToolCall.status, func.count())
            .where(ToolCall.session_id == session_id)
            .group_by(ToolCall.status)
        )

        status_result = await self.session.execute(status_stmt)
        status_counts = {row[0]: row[1] for row in status_result}

        # Count by tool name
        tool_stmt = (
            select(ToolCall.tool_name, func.count())
            .where(ToolCall.session_id == session_id)
            .group_by(ToolCall.tool_name)
        )

        tool_result = await self.session.execute(tool_stmt)
        tool_counts = {row[0]: row[1] for row in tool_result}

        return {
            "by_status": status_counts,
            "by_tool": tool_counts,
        }

    async def get_execution_time_stats(
        self,
        session_id: UUID,
        tool_name: Optional[str] = None
    ) -> dict:
        """
        Get execution time statistics for a session.

        Args:
            session_id: Session UUID
            tool_name: Optional tool name filter

        Returns:
            Dictionary with avg, min, max execution times
        """
        stmt = (
            select(func.avg(ToolCall.execution_time_ms), func.min(ToolCall.execution_time_ms), func.max(ToolCall.execution_time_ms))
            .where(and_(
                ToolCall.session_id == session_id,
                ToolCall.status == ToolCallStatus.COMPLETED,
                ToolCall.execution_time_ms.is_not(None)
            ))
        )

        if tool_name is not None:
            stmt = stmt.where(ToolCall.tool_name == tool_name)

        result = await self.session.execute(stmt)
        row = result.one()

        return {
            "avg_ms": row[0],
            "min_ms": row[1],
            "max_ms": row[2],
        }

    async def get_recent_calls(
        self,
        limit: int = 50
    ) -> List[ToolCall]:
        """
        Get recent tool calls across all sessions.

        Args:
            limit: Maximum number of results

        Returns:
            List of recent ToolCall instances
        """
        stmt = (
            select(ToolCall)
            .order_by(ToolCall.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_calls_in_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[ToolCallStatus] = None
    ) -> List[ToolCall]:
        """
        Get tool calls within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            status: Optional status filter

        Returns:
            List of ToolCall instances within range
        """
        stmt = (
            select(ToolCall)
            .where(and_(
                ToolCall.created_at >= start_date,
                ToolCall.created_at <= end_date
            ))
            .order_by(ToolCall.created_at.desc())
        )

        if status is not None:
            stmt = stmt.where(ToolCall.status == status)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_slow_calls(
        self,
        threshold_ms: int = 5000,
        limit: int = 20
    ) -> List[ToolCall]:
        """
        Get slow tool calls (execution time above threshold).

        Args:
            threshold_ms: Execution time threshold in milliseconds
            limit: Maximum number of results

        Returns:
            List of slow ToolCall instances
        """
        stmt = (
            select(ToolCall)
            .where(and_(
                ToolCall.status == ToolCallStatus.COMPLETED,
                ToolCall.execution_time_ms > threshold_ms
            ))
            .order_by(desc(ToolCall.execution_time_ms))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all()

    async def cleanup_old_calls(
        self,
        days: int = 30
    ) -> int:
        """
        Delete old completed/failed tool calls.

        Useful for database cleanup/maintenance.

        Args:
            days: Number of days to keep (default: 30)

        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        stmt = (
            select(ToolCall)
            .where(and_(
                ToolCall.created_at < cutoff_date,
                ToolCall.status.in_([ToolCallStatus.COMPLETED, ToolCallStatus.FAILED])
            ))
        )

        result = await self.session.execute(stmt)
        tool_calls = list(result.scalars().all())

        for tool_call in tool_calls:
            await self.session.delete(tool_call)

        await self.session.flush()
        return len(tool_calls)
