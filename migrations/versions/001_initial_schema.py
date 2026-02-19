"""Initial schema - agent_sessions, agent_messages, agent_tool_calls, agent_states, agent_embeddings, agent_workflows

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
    # Create enum types for Orbit Agent (prefixed to avoid conflicts)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE agentsessionstatus AS ENUM ('active', 'archived', 'deleted');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE agentmessagerole AS ENUM ('user', 'assistant', 'system', 'tool');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE agenttoolcallstatus AS ENUM ('pending', 'running', 'completed', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE agentworkflowstatus AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE agentworkflowstepstatus AS ENUM ('pending', 'running', 'completed', 'failed', 'skipped');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Import custom types for SQLAlchemy
    agentsessionstatus = postgresql.ENUM(name='agentsessionstatus', create_type=False)
    agentmessagerole = postgresql.ENUM(name='agentmessagerole', create_type=False)
    agenttoolcallstatus = postgresql.ENUM(name='agenttoolcallstatus', create_type=False)
    agentworkflowstatus = postgresql.ENUM(name='agentworkflowstatus', create_type=False)
    agentworkflowstepstatus = postgresql.ENUM(name='agentworkflowstepstatus', create_type=False)

    # Create agent_sessions table
    op.create_table(
        "agent_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("status", agentsessionstatus, nullable=False, server_default="active"),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index(op.f("ix_agent_sessions_user_id"), "agent_sessions", ["user_id"])
    op.create_index(op.f("ix_agent_sessions_status"), "agent_sessions", ["status"])

    # Create agent_messages table
    op.create_table(
        "agent_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", agentmessagerole, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_agent_messages_session_id"), "agent_messages", ["session_id"])
    op.create_index(op.f("ix_agent_messages_created_at"), "agent_messages", ["created_at"])
    op.create_index("idx_agent_messages_session_created", "agent_messages", ["session_id", "created_at"])

    # Create agent_tool_calls table
    op.create_table(
        "agent_tool_calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_messages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("inputs", postgresql.JSONB(), nullable=False),
        sa.Column("outputs", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("status", agenttoolcallstatus, nullable=False),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index(op.f("ix_agent_tool_calls_session_id"), "agent_tool_calls", ["session_id"])
    op.create_index(op.f("ix_agent_tool_calls_status"), "agent_tool_calls", ["status"])

    # Create agent_states table
    op.create_table(
        "agent_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("thread_id", sa.String(255), nullable=False, unique=True),
        sa.Column("state", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_agent_states_session_id"), "agent_states", ["session_id"])
    op.create_index(op.f("ix_agent_states_thread_id"), "agent_states", ["thread_id"], unique=True)

    # Create agent_embeddings table (without vector column - will be added with pgvector)
    op.create_table(
        "agent_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_agent_embeddings_session_id"), "agent_embeddings", ["session_id"])
    op.create_index("idx_agent_embeddings_entity", "agent_embeddings", ["entity_type", "entity_id"])

    # Create agent_workflow_executions table
    op.create_table(
        "agent_workflow_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workflow_name", sa.String(100), nullable=False),
        sa.Column("status", agentworkflowstatus, nullable=False, server_default="pending"),
        sa.Column("input_data", postgresql.JSONB(), nullable=False),
        sa.Column("output_data", postgresql.JSONB(), nullable=True),
        sa.Column("current_step", sa.Integer(), server_default="0"),
        sa.Column("total_steps", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
    )
    op.create_index(op.f("ix_agent_workflow_executions_session_id"), "agent_workflow_executions", ["session_id"])
    op.create_index(op.f("ix_agent_workflow_executions_status"), "agent_workflow_executions", ["status"])
    op.create_index(op.f("ix_agent_workflow_executions_started_at"), "agent_workflow_executions", ["started_at"])

    # Create agent_workflow_steps table
    op.create_table(
        "agent_workflow_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_execution_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_workflow_executions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_name", sa.String(100), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("status", agentworkflowstepstatus, nullable=False, server_default="pending"),
        sa.Column("input_data", postgresql.JSONB(), nullable=True),
        sa.Column("output_data", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_agent_workflow_steps_execution_order", "agent_workflow_steps", ["workflow_execution_id", "step_order"])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("idx_agent_workflow_steps_execution_order", table_name="agent_workflow_steps")
    op.drop_index(op.f("ix_agent_workflow_executions_started_at"), table_name="agent_workflow_executions")
    op.drop_index(op.f("ix_agent_workflow_executions_status"), table_name="agent_workflow_executions")
    op.drop_index(op.f("ix_agent_workflow_executions_session_id"), table_name="agent_workflow_executions")
    op.drop_index("idx_agent_embeddings_entity", table_name="agent_embeddings")
    op.drop_index(op.f("ix_agent_embeddings_session_id"), table_name="agent_embeddings")
    op.drop_index(op.f("ix_agent_states_thread_id"), table_name="agent_states")
    op.drop_index(op.f("ix_agent_states_session_id"), table_name="agent_states")
    op.drop_index(op.f("ix_agent_tool_calls_status"), table_name="agent_tool_calls")
    op.drop_index(op.f("ix_agent_tool_calls_session_id"), table_name="agent_tool_calls")
    op.drop_index("idx_agent_messages_session_created", table_name="agent_messages")
    op.drop_index(op.f("ix_agent_messages_created_at"), table_name="agent_messages")
    op.drop_index(op.f("ix_agent_messages_session_id"), table_name="agent_messages")
    op.drop_index(op.f("ix_agent_sessions_status"), table_name="agent_sessions")
    op.drop_index(op.f("ix_agent_sessions_user_id"), table_name="agent_sessions")

    # Drop tables in reverse order (due to foreign keys)
    op.drop_table("agent_workflow_steps")
    op.drop_table("agent_workflow_executions")
    op.drop_table("agent_embeddings")
    op.drop_table("agent_states")
    op.drop_table("agent_tool_calls")
    op.drop_table("agent_messages")
    op.drop_table("agent_sessions")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS agentworkflowstepstatus")
    op.execute("DROP TYPE IF EXISTS agentworkflowstatus")
    op.execute("DROP TYPE IF EXISTS agenttoolcallstatus")
    op.execute("DROP TYPE IF EXISTS agentmessagerole")
    op.execute("DROP TYPE IF EXISTS agentsessionstatus")
