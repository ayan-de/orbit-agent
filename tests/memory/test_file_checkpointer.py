"""
Unit tests for FileCheckpointSaver.

Tests checkpoint save/load functionality for file-based persistence.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from uuid import uuid4

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata

from src.memory.file_checkpointer import (
    FileCheckpointSaver,
    get_file_checkpointer,
    reset_file_checkpointer,
)


@pytest.fixture
def checkpointer():
    """
    Fixture that provides a fresh FileCheckpointSaver instance for each test.
    Also cleans up test checkpoints to avoid cross-test pollution.
    """
    reset_file_checkpointer()

    # Clean up any existing test checkpoints
    from src.memory.file_checkpointer import CHECKPOINTS_DIR
    import shutil
    if CHECKPOINTS_DIR.exists():
        for f in CHECKPOINTS_DIR.glob("test_thread*.json"):
            f.unlink()
        for f in CHECKPOINTS_DIR.glob("test_complex_thread*.json"):
            f.unlink()

    return FileCheckpointSaver()


@pytest.fixture
def sample_checkpoint():
    """
    Fixture providing a sample checkpoint for testing.
    """
    return {
        "id": str(uuid4()),
        "channel_values": {
            "messages": [{"role": "user", "content": "Hello"}],
            "intent": "command",
            "tool_results": [],
        },
        "channel_versions": {"messages": 1},
        "versions_seen": {},
        "pending_sends": [],
    }


@pytest.fixture
def sample_metadata():
    """
    Fixture providing sample checkpoint metadata for testing.
    """
    return CheckpointMetadata(
        source="test",
        step=1,
        writes={},
        parents=[],
    )


class TestFileCheckpointSaverSave:
    """Tests for save_checkpoint functionality."""

    @pytest.mark.asyncio
    async def test_save_checkpoint_creates_file(
        self, checkpointer, sample_checkpoint, sample_metadata
    ):
        """Test that saving a checkpoint creates a file."""
        config = RunnableConfig(
            configurable={"thread_id": "test_thread", "checkpoint_id": str(uuid4())}
        )

        await checkpointer.aput(config, sample_checkpoint, sample_metadata)

        # Check that file was created
        checkpoint_file = checkpointer._get_checkpoint_path("test_thread")
        assert checkpoint_file.exists()

    @pytest.mark.asyncio
    async def test_save_checkpoint_creates_latest_file(
        self, checkpointer, sample_checkpoint, sample_metadata
    ):
        """Test that saving a checkpoint creates a _latest.json file."""
        config = RunnableConfig(
            configurable={"thread_id": "test_thread", "checkpoint_id": str(uuid4())}
        )

        await checkpointer.aput(config, sample_checkpoint, sample_metadata)

        # Check that latest file was created
        latest_file = checkpointer._get_checkpoint_path("test_thread", None)
        assert latest_file.exists()
        assert "_latest.json" in str(latest_file)

    @pytest.mark.asyncio
    async def test_save_checkpoint_updates_config(
        self, checkpointer, sample_checkpoint, sample_metadata
    ):
        """Test that saving a checkpoint updates the config with checkpoint ID."""
        config = RunnableConfig(
            configurable={"thread_id": "test_thread", "checkpoint_id": str(uuid4())}
        )

        new_config = await checkpointer.aput(config, sample_checkpoint, sample_metadata)

        # Check that new checkpoint ID is in config
        new_checkpoint_id = new_config.get("configurable", {}).get("checkpoint_id")
        assert new_checkpoint_id is not None
        assert new_checkpoint_id != config.get("configurable", {}).get("checkpoint_id")


class TestFileCheckpointSaverLoad:
    """Tests for load_checkpoint functionality."""

    @pytest.mark.asyncio
    async def test_load_checkpoint_by_id(
        self, checkpointer, sample_checkpoint, sample_metadata
    ):
        """Test loading a checkpoint by ID."""
        config = RunnableConfig(
            configurable={"thread_id": "test_thread", "checkpoint_id": str(uuid4())}
        )

        # Save checkpoint
        new_config = await checkpointer.aput(config, sample_checkpoint, sample_metadata)

        # Load checkpoint by ID
        loaded_checkpoint, loaded_metadata = await checkpointer.aget(new_config)

        assert loaded_checkpoint is not None
        assert loaded_metadata is not None

    @pytest.mark.asyncio
    async def test_load_checkpoint_latest(
        self, checkpointer, sample_checkpoint, sample_metadata
    ):
        """Test loading the latest checkpoint."""
        config = RunnableConfig(configurable={"thread_id": "test_thread"})

        # Save checkpoint
        await checkpointer.aput(config, sample_checkpoint, sample_metadata)

        # Load latest checkpoint (no checkpoint_id in config)
        loaded_checkpoint, loaded_metadata = await checkpointer.aget(config)

        assert loaded_checkpoint is not None
        assert loaded_metadata is not None

    @pytest.mark.asyncio
    async def test_load_checkpoint_nonexistent_returns_none(
        self, checkpointer, sample_checkpoint, sample_metadata
    ):
        """Test that loading a nonexistent checkpoint returns None."""
        config = RunnableConfig(
            configurable={
                "thread_id": "nonexistent_thread",
                "checkpoint_id": str(uuid4()),
            }
        )

        loaded_checkpoint, loaded_metadata = await checkpointer.aget(config)

        assert loaded_checkpoint is None
        assert loaded_metadata is None


class TestFileCheckpointSaverList:
    """Tests for list_checkpoints functionality."""

    @pytest.mark.asyncio
    async def test_list_checkpoints_returns_history(
        self, checkpointer, sample_checkpoint, sample_metadata
    ):
        """Test listing checkpoints returns checkpoint history."""
        config = RunnableConfig(configurable={"thread_id": "test_thread"})

        # Save multiple checkpoints
        for i in range(3):
            await checkpointer.aput(config, sample_checkpoint, sample_metadata)

        # List checkpoints
        checkpoints = await checkpointer.alist(config, limit=10)

        assert len(checkpoints) == 3

    @pytest.mark.asyncio
    async def test_list_checkpoints_respects_limit(
        self, checkpointer, sample_checkpoint, sample_metadata
    ):
        """Test that listing checkpoints respects the limit parameter."""
        config = RunnableConfig(configurable={"thread_id": "test_thread"})

        # Save multiple checkpoints
        for i in range(5):
            await checkpointer.aput(config, sample_checkpoint, sample_metadata)

        # List checkpoints with limit of 3
        checkpoints = await checkpointer.alist(config, limit=3)

        assert len(checkpoints) == 3

    @pytest.mark.asyncio
    async def test_list_checkpoints_empty_returns_empty(
        self, checkpointer
    ):
        """Test listing checkpoints with no saved checkpoints returns empty list."""
        config = RunnableConfig(configurable={"thread_id": "test_thread"})

        checkpoints = await checkpointer.alist(config)

        assert len(checkpoints) == 0


class TestFileCheckpointSaverRoundTrip:
    """Tests for save/load round-trip integrity."""

    @pytest.mark.asyncio
    async def test_round_trip_preserves_data(
        self, checkpointer, sample_checkpoint, sample_metadata
    ):
        """Test that saving and loading preserves checkpoint data."""
        config = RunnableConfig(configurable={"thread_id": "test_thread"})

        # Save checkpoint
        new_config = await checkpointer.aput(config, sample_checkpoint, sample_metadata)

        # Load checkpoint
        loaded_checkpoint, loaded_metadata = await checkpointer.aget(new_config)

        # Check channel values
        assert loaded_checkpoint["channel_values"] == sample_checkpoint["channel_values"]
        assert loaded_checkpoint["channel_versions"] == sample_checkpoint["channel_versions"]
        assert loaded_checkpoint["versions_seen"] == sample_checkpoint["versions_seen"]
        assert loaded_checkpoint["pending_sends"] == sample_checkpoint["pending_sends"]

        # Check metadata
        assert loaded_metadata["source"] == sample_metadata["source"]
        assert loaded_metadata["step"] == sample_metadata["step"]
        assert loaded_metadata["parents"] == sample_metadata["parents"]

    @pytest.mark.asyncio
    async def test_round_trip_preserves_complex_data(
        self, checkpointer
    ):
        """Test that complex nested data structures are preserved."""
        complex_checkpoint = {
            "id": str(uuid4()),
            "channel_values": {
                "nested": {
                    "deep": {
                        "values": [1, 2, 3],
                        "strings": ["a", "b", "c"],
                    }
                },
                "messages": [
                    {"role": "user", "content": "First"},
                    {"role": "assistant", "content": "Response"},
                    {"role": "user", "content": "Second"},
                ],
            },
            "channel_versions": {"messages": 3, "nested": 1},
            "versions_seen": {},
            "pending_sends": [],
        }

        complex_metadata = CheckpointMetadata(
            source="test_complex",
            step=5,
            writes={"nested": {"new_value": "test"}},
            parents=["parent_1", "parent_2"],
        )

        config = RunnableConfig(configurable={"thread_id": "test_complex_thread"})

        # Save and load
        new_config = await checkpointer.aput(config, complex_checkpoint, complex_metadata)
        loaded_checkpoint, loaded_metadata = await checkpointer.aget(new_config)

        # Verify nested structure
        assert loaded_checkpoint["channel_values"]["nested"]["deep"]["values"] == [1, 2, 3]
        assert len(loaded_checkpoint["channel_values"]["messages"]) == 3

        # Verify complex metadata
        assert loaded_metadata["source"] == "test_complex"
        assert loaded_metadata["writes"]["nested"]["new_value"] == "test"


class TestGlobalCheckpointer:
    """Tests for global checkpointer instance."""

    def test_get_file_checkpointer_returns_same_instance(self):
        """Test that get_file_checkpointer returns the same instance."""
        reset_file_checkpointer()

        checkpointer1 = get_file_checkpointer()
        checkpointer2 = get_file_checkpointer()

        assert checkpointer1 is checkpointer2

    def test_reset_file_checkpointer_clears_instance(self):
        """Test that reset_file_checkpointer clears the global instance."""
        reset_file_checkpointer()

        checkpointer1 = get_file_checkpointer()
        reset_file_checkpointer()

        checkpointer2 = get_file_checkpointer()

        assert checkpointer1 is not checkpointer2
