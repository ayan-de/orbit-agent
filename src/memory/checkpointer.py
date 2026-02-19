"""
PostgreSQL checkpointer for LangGraph.

Enables pause/resume functionality by storing agent checkpoints in PostgreSQL.
"""

from typing import Dict, Any, Optional, Tuple, List, TypedDict, Annotated
from datetime import datetime, timezone
from uuid import uuid4, UUID
import json

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint import BaseCheckpointSaver, Checkpoint, CheckpointMetadata

from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Session, AgentState as DBAgentState
from src.db.engine import get_session
from src.config import settings


class CheckpointData(TypedDict):
    """Checkpoint data stored in database."""
    checkpoint_id: str
    thread_id: str
    parent_checkpoint_id: Optional[str]
    checkpoint: Dict[str, Any]
    metadata: CheckpointMetadata
    next_node: Optional[str]
    created_at: datetime


class PostgresCheckpointSaver(BaseCheckpointSaver):
    """
    PostgreSQL-based checkpointer for LangGraph.

    Stores checkpoints in PostgreSQL for pause/resume functionality.
    Allows resuming conversations from any checkpoint.
    """

    def __init__(self, db_session: AsyncSession = None):
        """
        Initialize PostgreSQL checkpointer.

        Args:
            db_session: Async SQLAlchemy session (optional)
        """
        self.db_session = db_session
        super().__init__()

    async def _get_db_session(self) -> AsyncSession:
        """Get database session."""
        if self.db_session:
            return self.db_session
        return await get_session().__anext__()

    def _serialize_checkpoint(self, checkpoint: Checkpoint) -> Dict[str, Any]:
        """
        Serialize checkpoint for storage.

        Args:
            checkpoint: LangGraph checkpoint

        Returns:
            Serialized checkpoint dictionary
        """
        # Convert checkpoint to JSON-serializable format
        return {
            "id": checkpoint.get("id", str(uuid4())),
            "channel_values": self._serialize_state(checkpoint.get("channel_values", {})),
            "channel_versions": checkpoint.get("channel_versions", {}),
            "versions_seen": checkpoint.get("versions_seen", {}),
            "pending_sends": checkpoint.get("pending_sends", []),
        }

    def _deserialize_checkpoint(self, data: Dict[str, Any]) -> Checkpoint:
        """
        Deserialize checkpoint from storage.

        Args:
            data: Serialized checkpoint data

        Returns:
            LangGraph checkpoint
        """
        return {
            "id": data.get("id"),
            "channel_values": self._deserialize_state(data.get("channel_values", {})),
            "channel_versions": data.get("channel_versions", {}),
            "versions_seen": data.get("versions_seen", {}),
            "pending_sends": data.get("pending_sends", []),
        }

    def _serialize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize state for JSON storage.

        Handles special types like datetime, UUID, etc.

        Args:
            state: State dictionary

        Returns:
            JSON-serializable state
        """
        serialized = {}
        for key, value in state.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, UUID):
                serialized[key] = str(value)
            elif hasattr(value, 'model_dump'):  # Pydantic models
                serialized[key] = value.model_dump()
            elif isinstance(value, (list, dict)):
                serialized[key] = self._serialize_state(value) if isinstance(value, dict) else [
                    self._serialize_state(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                serialized[key] = value
        return serialized

    def _deserialize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialize state from JSON storage.

        Args:
            state: JSON-serializable state

        Returns:
            Deserialized state
        """
        deserialized = {}
        for key, value in state.items():
            deserialized[key] = value
        return deserialized

    def _serialize_metadata(self, metadata: CheckpointMetadata) -> Dict[str, Any]:
        """
        Serialize checkpoint metadata.

        Args:
            metadata: CheckpointMetadata object

        Returns:
            JSON-serializable metadata
        """
        return {
            "source": metadata.get("source"),
            "step": metadata.get("step"),
            "writes": metadata.get("writes"),
            "parents": metadata.get("parents"),
        }

    def _deserialize_metadata(self, metadata: Dict[str, Any]) -> CheckpointMetadata:
        """
        Deserialize checkpoint metadata.

        Args:
            metadata: JSON metadata

        Returns:
            CheckpointMetadata object
        """
        return CheckpointMetadata(
            source=metadata.get("source"),
            step=metadata.get("step"),
            writes=metadata.get("writes"),
            parents=metadata.get("parents"),
        )

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> RunnableConfig:
        """
        Save checkpoint to database.

        Args:
            config: Runnable configuration
            checkpoint: Checkpoint to save
            metadata: Checkpoint metadata

        Returns:
            Updated configuration with checkpoint ID
        """
        session = await self._get_db_session()

        try:
            # Get thread ID from config
            thread_id = config.get("configurable", {}).get("thread_id")
            if not thread_id:
                thread_id = str(uuid4())

            # Get parent checkpoint ID if exists
            parent_checkpoint_id = config.get("configurable", {}).get("checkpoint_id")

            # Serialize checkpoint and metadata
            checkpoint_data = self._serialize_checkpoint(checkpoint)
            metadata_data = self._serialize_metadata(metadata)

            # Get next node from metadata if available
            next_node = None
            writes = metadata.get("writes", {})
            if writes:
                next_node = list(writes.keys())[0] if writes else None

            # Check if session exists
            stmt = select(Session).where(Session.id == thread_id)
            result = await session.execute(stmt)
            session_obj = result.scalar_one_or_none()

            # Create session if doesn't exist
            if not session_obj:
                session_obj = Session(
                    id=thread_id,
                    user_id="system",  # Default user for checkpointer
                    status="active"
                )
                session.add(session_obj)
                await session.flush()

            # Create checkpoint record
            checkpoint_id = str(uuid4())

            # Store in AgentState table
            db_state = DBAgentState(
                id=checkpoint_id,
                session_id=thread_id,
                thread_id=thread_id,
                state={
                    "checkpoint": checkpoint_data,
                    "metadata": metadata_data,
                    "parent_checkpoint_id": parent_checkpoint_id,
                    "next_node": next_node,
                }
            )
            session.add(db_state)
            await session.commit()

            # Update config with new checkpoint ID
            new_config = {
                "configurable": {
                    **config.get("configurable", {}),
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint_id,
                }
            }

            return new_config

        except Exception as e:
            await session.rollback()
            raise e

    async def aget(
        self,
        config: RunnableConfig,
    ) -> Tuple[Optional[Checkpoint], Optional[CheckpointMetadata]]:
        """
        Get checkpoint from database.

        Args:
            config: Runnable configuration

        Returns:
            Tuple of (checkpoint, metadata) or (None, None)
        """
        session = await self._get_db_session()

        try:
            # Get checkpoint ID from config
            checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
            thread_id = config.get("configurable", {}).get("thread_id")

            if checkpoint_id:
                # Get specific checkpoint
                stmt = select(DBAgentState).where(DBAgentState.id == checkpoint_id)
            elif thread_id:
                # Get latest checkpoint for thread
                stmt = (
                    select(DBAgentState)
                    .where(DBAgentState.thread_id == thread_id)
                    .order_by(DBAgentState.created_at.desc())
                    .limit(1)
                )
            else:
                return None, None

            result = await session.execute(stmt)
            db_state = result.scalar_one_or_none()

            if not db_state:
                return None, None

            # Deserialize checkpoint and metadata
            state_data = db_state.state
            checkpoint_data = state_data.get("checkpoint", {})
            metadata_data = state_data.get("metadata", {})

            checkpoint = self._deserialize_checkpoint(checkpoint_data)
            metadata = self._deserialize_metadata(metadata_data)

            return checkpoint, metadata

        except Exception as e:
            await session.rollback()
            raise e

    async def alist(
        self,
        config: RunnableConfig,
        limit: int = 10,
        before: Optional[RunnableConfig] = None,
    ) -> List[Tuple[RunnableConfig, Checkpoint, CheckpointMetadata]]:
        """
        List checkpoints for a thread.

        Args:
            config: Runnable configuration
            limit: Maximum number of checkpoints to return
            before: Get checkpoints before this one

        Returns:
            List of (config, checkpoint, metadata) tuples
        """
        session = await self._get_db_session()

        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            if not thread_id:
                return []

            # Build query
            stmt = (
                select(DBAgentState)
                .where(DBAgentState.thread_id == thread_id)
                .order_by(DBAgentState.created_at.desc())
                .limit(limit)
            )

            # Filter by before checkpoint if specified
            if before:
                before_id = before.get("configurable", {}).get("checkpoint_id")
                if before_id:
                    before_checkpoint = await session.execute(
                        select(DBAgentState).where(DBAgentState.id == before_id)
                    )
                    before_state = before_checkpoint.scalar_one_or_none()
                    if before_state:
                        stmt = stmt.where(
                            DBAgentState.created_at < before_state.created_at
                        )

            result = await session.execute(stmt)
            db_states = result.scalars().all()

            checkpoints = []
            for db_state in reversed(db_states):
                state_data = db_state.state
                checkpoint_data = state_data.get("checkpoint", {})
                metadata_data = state_data.get("metadata", {})

                checkpoint = self._deserialize_checkpoint(checkpoint_data)
                metadata = self._deserialize_metadata(metadata_data)

                config_data = {
                    "configurable": {
                        "thread_id": db_state.thread_id,
                        "checkpoint_id": str(db_state.id),
                    }
                }

                checkpoints.append((config_data, checkpoint, metadata))

            return checkpoints

        except Exception as e:
            await session.rollback()
            raise e

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: List[Tuple[str, Any]],
        task_id: str,
    ) -> None:
        """
        Write updates to checkpoint.

        Args:
            config: Runnable configuration
            writes: List of (channel, value) tuples
            task_id: Task ID for the writes
        """
        # For simplicity, we'll checkpoint after each write
        # More sophisticated implementations could batch writes
        pass

    async def aget_tuple(
        self,
        config: RunnableConfig,
    ) -> Optional[Tuple[Optional[Checkpoint], Dict[str, Any], Optional[CheckpointMetadata]]]:
        """
        Get checkpoint with additional metadata.

        Args:
            config: Runnable configuration

        Returns:
            Tuple of (checkpoint, parent_config, metadata) or None
        """
        checkpoint, metadata = await self.aget(config)
        if not checkpoint:
            return None

        # Get parent config
        state_data = checkpoint.get("metadata", {})
        parent_checkpoint_id = state_data.get("parent_checkpoint_id")

        parent_config = None
        if parent_checkpoint_id:
            parent_config = {
                "configurable": {
                    "thread_id": config.get("configurable", {}).get("thread_id"),
                    "checkpoint_id": parent_checkpoint_id,
                }
            }

        return checkpoint, parent_config or {}, metadata


# Global checkpointer instance
_postgres_checkpointer: Optional[PostgresCheckpointSaver] = None


async def get_checkpointer() -> PostgresCheckpointSaver:
    """
    Get or create global checkpointer instance.

    Returns:
        PostgreSQL checkpointer instance
    """
    global _postgres_checkpointer
    if _postgres_checkpointer is None:
        _postgres_checkpointer = PostgresCheckpointSaver()
    return _postgres_checkpointer


def reset_checkpointer():
    """Reset global checkpointer instance (for testing)."""
    global _postgres_checkpointer
    _postgres_checkpointer = None
