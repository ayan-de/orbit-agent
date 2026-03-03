"""
File-based checkpointer for LangGraph.

Enables pause/resume functionality by storing agent checkpoints as JSON files.
Checkpoints are stored in ~/.orbit/memory/episodic/checkpoints/
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from uuid import uuid4

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata

from .structure import (
    EPISODIC_DIR,
    initialize_memory_structure,
)

logger = logging.getLogger("orbit.file_checkpointer")

# Checkpoints directory
CHECKPOINTS_DIR = EPISODIC_DIR / "checkpoints"


class FileCheckpointSaver(BaseCheckpointSaver):
    """
    File-based checkpointer for LangGraph.

    Stores checkpoints as JSON files for pause/resume functionality.
    Allows resuming conversations from any checkpoint.
    """

    def __init__(self):
        """Initialize file-based checkpointer."""
        super().__init__()
        self._ensure_structure()

    def _ensure_structure(self) -> None:
        """Ensure checkpoints directory exists."""
        initialize_memory_structure()
        CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

    def _get_checkpoint_path(
        self, thread_id: str, checkpoint_id: Optional[str] = None
    ) -> Path:
        """
        Get the file path for a checkpoint.

        Args:
            thread_id: Thread identifier
            checkpoint_id: Optional checkpoint identifier

        Returns:
            Path to checkpoint file
        """
        if checkpoint_id:
            return CHECKPOINTS_DIR / f"{thread_id}_{checkpoint_id}.json"
        return CHECKPOINTS_DIR / f"{thread_id}_latest.json"

    def _serialize_checkpoint(self, checkpoint: Checkpoint) -> Dict[str, Any]:
        """
        Serialize checkpoint for JSON storage.

        Args:
            checkpoint: LangGraph checkpoint

        Returns:
            JSON-serializable checkpoint dictionary
        """
        return {
            "id": checkpoint.get("id", str(uuid4())),
            "channel_values": self._serialize_value(checkpoint.get("channel_values", {})),
            "channel_versions": checkpoint.get("channel_versions", {}),
            "versions_seen": checkpoint.get("versions_seen", {}),
            "pending_sends": checkpoint.get("pending_sends", []),
        }

    def _deserialize_checkpoint(self, data: Dict[str, Any]) -> Checkpoint:
        """
        Deserialize checkpoint from JSON.

        Args:
            data: Serialized checkpoint data

        Returns:
            LangGraph checkpoint
        """
        return {
            "id": data.get("id"),
            "channel_values": self._deserialize_value(data.get("channel_values", {})),
            "channel_versions": data.get("channel_versions", {}),
            "versions_seen": data.get("versions_seen", {}),
            "pending_sends": data.get("pending_sends", []),
        }

    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize a value for JSON storage.

        Handles special types like datetime, UUID, etc.

        Args:
            value: Value to serialize

        Returns:
            JSON-serializable value
        """
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        elif hasattr(value, "isoformat"):  # datetime
            return value.isoformat()
        elif hasattr(value, "__dict__"):  # Pydantic models
            return self._serialize_value(value.__dict__)
        else:
            return value

    def _deserialize_value(self, value: Any) -> Any:
        """
        Deserialize a value from JSON.

        Args:
            value: JSON value

        Returns:
            Deserialized value
        """
        if isinstance(value, dict):
            return {k: self._deserialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._deserialize_value(item) for item in value]
        else:
            return value

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
            "writes": self._serialize_value(metadata.get("writes")),
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
            writes=self._deserialize_value(metadata.get("writes")),
            parents=metadata.get("parents"),
        )

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> RunnableConfig:
        """
        Save checkpoint to file.

        Args:
            config: Runnable configuration
            checkpoint: Checkpoint to save
            metadata: Checkpoint metadata

        Returns:
            Updated configuration with checkpoint ID
        """
        try:
            # Get thread ID from config
            thread_id = config.get("configurable", {}).get("thread_id")
            if not thread_id:
                thread_id = str(uuid4())

            # Get parent checkpoint ID if exists
            parent_checkpoint_id = config.get("configurable", {}).get("checkpoint_id")

            # Generate new checkpoint ID
            checkpoint_id = str(uuid4())

            # Serialize checkpoint and metadata
            checkpoint_data = self._serialize_checkpoint(checkpoint)
            metadata_data = self._serialize_metadata(metadata)

            # Build checkpoint file data
            file_data = {
                "checkpoint_id": checkpoint_id,
                "thread_id": thread_id,
                "parent_checkpoint_id": parent_checkpoint_id,
                "checkpoint": checkpoint_data,
                "metadata": metadata_data,
                "created_at": datetime.now().isoformat(),
            }

            # Write checkpoint to file
            checkpoint_path = self._get_checkpoint_path(thread_id, checkpoint_id)
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(file_data, f, indent=2, default=str)

            # Also write as latest checkpoint
            latest_path = self._get_checkpoint_path(thread_id, None)
            with open(latest_path, "w", encoding="utf-8") as f:
                json.dump(file_data, f, indent=2, default=str)

            logger.debug(f"Saved checkpoint {checkpoint_id} for thread {thread_id}")

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
            logger.error(f"Failed to save checkpoint: {e}")
            raise

    async def aget(
        self,
        config: RunnableConfig,
    ) -> Tuple[Optional[Checkpoint], Optional[CheckpointMetadata]]:
        """
        Get checkpoint from file.

        Args:
            config: Runnable configuration

        Returns:
            Tuple of (checkpoint, metadata) or (None, None)
        """
        try:
            # Get checkpoint ID from config
            checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
            thread_id = config.get("configurable", {}).get("thread_id")

            if not thread_id:
                return None, None

            # Determine which file to read
            if checkpoint_id:
                checkpoint_path = self._get_checkpoint_path(thread_id, checkpoint_id)
            else:
                checkpoint_path = self._get_checkpoint_path(thread_id, None)

            if not checkpoint_path.exists():
                return None, None

            # Read checkpoint from file
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                file_data = json.load(f)

            # Deserialize checkpoint and metadata
            checkpoint_data = file_data.get("checkpoint", {})
            metadata_data = file_data.get("metadata", {})

            checkpoint = self._deserialize_checkpoint(checkpoint_data)
            metadata = self._deserialize_metadata(metadata_data)

            logger.debug(f"Loaded checkpoint {file_data.get('checkpoint_id')} for thread {thread_id}")

            return checkpoint, metadata

        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None, None

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
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            if not thread_id:
                return []

            # List all checkpoint files for this thread
            checkpoint_files = sorted(
                CHECKPOINTS_DIR.glob(f"{thread_id}_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

            # Filter out latest checkpoint (use specific IDs)
            checkpoint_files = [
                f for f in checkpoint_files
                if not f.name.endswith("_latest.json")
            ]

            # Filter by before checkpoint if specified
            if before:
                before_id = before.get("configurable", {}).get("checkpoint_id")
                if before_id:
                    before_path = self._get_checkpoint_path(thread_id, before_id)
                    if before_path.exists():
                        before_time = before_path.stat().st_mtime
                        checkpoint_files = [
                            f for f in checkpoint_files
                            if f.stat().st_mtime < before_time
                        ]

            # Limit results
            checkpoint_files = checkpoint_files[:limit]

            # Load checkpoints
            checkpoints = []
            for checkpoint_path in reversed(checkpoint_files):
                try:
                    with open(checkpoint_path, "r", encoding="utf-8") as f:
                        file_data = json.load(f)

                    checkpoint_data = file_data.get("checkpoint", {})
                    metadata_data = file_data.get("metadata", {})

                    checkpoint = self._deserialize_checkpoint(checkpoint_data)
                    metadata = self._deserialize_metadata(metadata_data)

                    config_data = {
                        "configurable": {
                            "thread_id": file_data.get("thread_id"),
                            "checkpoint_id": file_data.get("checkpoint_id"),
                        }
                    }

                    checkpoints.append((config_data, checkpoint, metadata))

                except Exception as e:
                    logger.error(f"Failed to load checkpoint {checkpoint_path}: {e}")
                    continue

            return checkpoints

        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []

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
            task_id: Task ID for writes
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
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
        thread_id = config.get("configurable", {}).get("thread_id")

        parent_config = None
        if checkpoint_id and thread_id:
            checkpoint_path = self._get_checkpoint_path(thread_id, checkpoint_id)
            if checkpoint_path.exists():
                with open(checkpoint_path, "r", encoding="utf-8") as f:
                    file_data = json.load(f)

                parent_checkpoint_id = file_data.get("parent_checkpoint_id")
                if parent_checkpoint_id:
                    parent_config = {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_id": parent_checkpoint_id,
                        }
                    }

        return checkpoint, parent_config or {}, metadata


# Global checkpointer instance
_file_checkpointer: Optional[FileCheckpointSaver] = None


def get_file_checkpointer() -> FileCheckpointSaver:
    """
    Get or create global file checkpointer instance.

    Returns:
        File-based checkpointer instance
    """
    global _file_checkpointer
    if _file_checkpointer is None:
        _file_checkpointer = FileCheckpointSaver()
    return _file_checkpointer


def reset_file_checkpointer():
    """Reset global file checkpointer instance (for testing)."""
    global _file_checkpointer
    _file_checkpointer = None
