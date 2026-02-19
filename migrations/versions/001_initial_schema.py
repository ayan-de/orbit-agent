"""Initial schema - sessions, messages, tool_calls, agent_states, embeddings, workflows

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    session_status = sa.Enum(
        "active",
        "archived",
        "deleted",
        name="sessionstatus",
        create_type=True
    )
    session_status.create(op.get_bind())
    op.execute("CREATE TYPE sessionstatus AS ENUM ('active', 'archived', 'deleted')")

    message_role = sa.Enum(
        "user",
        "assistant",
        "system",
        "tool",
        name="messagerole",
        create_type=True
    )
    op.execute("CREATE TYPE messagerole AS ENUM ('user', 'assistant', 'system', 'tool')")

    tool_call_status = sa.Enum(
        "pending",
        "running",
        "completed",
        "failed",
        name="toolcallstatus",
        create_type=True
    )
    op.execute("CREATE TYPE toolcallstatus AS ENUM ('pending', 'running', 'completed', 'failed')")

    workflow_status = sa.Enum(
        "pending",
        "running",
        "completed",
        "failed",
        "cancelled",
        name="workflowstatus",
        create_type=True
    )
    op.execute("CREATE TYPE workflowstatus AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled')")

    workflow_step_status = sa.Enum(
        "pending",
        "running",
        "completed",
        "failed",
        "skipped",
        name="workflowstepstatus",
        create_type=True
    )
    op.execute("CREATE TYPE workflowstepstatus AS ENUM ('pending', 'running', 'completed', 'failed', 'skipped')")

    # Create sessions table
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "archived", "deleted", name="sessionstatus"),
            nullable=False,
            server_default="active"
        ),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"])
    op.create_index(op.f("ix_sessions_status"), "sessions", ["status"])

    # Create messages table
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False
        ),
        sa.Column(
            "role",
            sa.Enum("user", "assistant", "system", "tool", name="messagerole"),
            nullable=False
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_messages_session_id"), "messages", ["session_id"])
    op.create_index(op.f("ix_messages_created_at"), "messages", ["created_at"])
    op.create_index("idx_messages_session_created", "messages", ["session_id", "created_at"])

    # Create tool_calls table
    op.create_table(
        "tool_calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("messages.id", ondelete="SET NULL"),
            nullable=True
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False
        ),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("inputs", postgresql.JSONB(), nullable=False),
        sa.Column("outputs", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", name="toolcallstatus"),
            nullable=False
        ),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index(op.f("ix_tool_calls_session_id"), "tool_calls", ["session_id"])
    op.create_index(op.f("ix_tool_calls_status"), "tool_calls", ["status"])

    # Create agent_states table
    op.create_table(
        "agent_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False
        ),
        sa.Column("thread_id", sa.String(255), nullable=False, unique=True),
        sa.Column("state", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_agent_states_session_id"), "agent_states", ["session_id"])
    op.create_index(op.f("ix_agent_states_thread_id"), "agent_states", ["thread_id"], unique=True)

    # Create embeddings table (without vector column - will be added with pgvector)
    op.create_table(
        "embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="SET NULL"),
            nullable=True
        ),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_embeddings_session_id"), "embeddings", ["session_id"])
    op.create_index("idx_embeddings_entity", "embeddings", ["entity_type", "entity_id"])

    # Create workflow_executions table
    op.create_table(
        "workflow_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False
        ),
        sa.Column("workflow_name", sa.String(100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", "cancelled", name="workflowstatus"),
            nullable=False,
            server_default="pending"
        ),
        sa.Column("input_data", postgresql.JSONB(), nullable=False),
        sa.Column("output_data", postgresql.JSONB(), nullable=True),
        sa.Column("current_step", sa.Integer(), server_default="0"),
        sa.Column("total_steps", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
    )
    op.create_index(op.f("ix_workflow_executions_session_id"), "workflow_executions", ["session_id"])
    op.create_index(op.f("ix_workflow_executions_status"), "workflow_executions", ["status"])
    op.create_index(op.f("ix_workflow_executions_started_at"), "workflow_executions", ["started_at"])

    # Create workflow_steps table
    op.create_table(
        "workflow_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workflow_execution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_executions.id", ondelete="CASCADE"),
            nullable=False
        ),
        sa.Column("step_name", sa.String(100), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", "skipped", name="workflowstepstatus"),
            nullable=False,
            server_default="pending"
        ),
        sa.Column("input_data", postgresql.JSONB(), nullable=True),
        sa.Column("output_data", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_workflow_steps_execution_order", "workflow_steps", ["workflow_execution_id", "step_order"])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("idx_workflow_steps_execution_order", table_name="workflow_steps")
    op.drop_index(op.f("ix_workflow_executions_started_at"), table_name="workflow_executions")
    op.drop_index(op.f("ix_workflow_executions_status"), table_name="workflow_executions")
    op.drop_index(op.f("ix_workflow_executions_session_id"), table_name="workflow_executions")
    op.drop_index("idx_embeddings_entity", table_name="embeddings")
    op.drop_index(op.f("ix_embeddings_session_id"), table_name="embeddings")
    op.drop_index(op.f("ix_agent_states_thread_id"), table_name="agent_states")
    op.drop_index(op.f("ix_agent_states_session_id"), table_name="agent_states")
    op.drop_index(op.f("ix_tool_calls_status"), table_name="tool_calls")
    op.drop_index(op.f("ix_tool_calls_session_id"), table_name="tool_calls")
    op.drop_index("idx_messages_session_created", table_name="messages")
    op.drop_index(op.f("ix_messages_created_at"), table_name="messages")
    op.drop_index(op.f("ix_messages_session_id"), table_name="messages")
    op.drop_index(op.f("ix_sessions_status"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_user_id"), table_name="sessions")

    # Drop tables in reverse order (due to foreign keys)
    op.drop_table("workflow_steps")
    op.drop_table("workflow_executions")
    op.drop_table("embeddings")
    op.drop_table("agent_states")
    op.drop_table("tool_calls")
    op.drop_table("messages")
    op.drop_table("sessions")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS workflowstepstatus")
    op.execute("DROP TYPE IF EXISTS workflowstatus")
    op.execute("DROP TYPE IF EXISTS toolcallstatus")
    op.execute("DROP TYPE IF EXISTS messagerole")
    op.execute("DROP TYPE IF EXISTS sessionstatus")
