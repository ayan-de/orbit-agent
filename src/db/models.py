"""
Database models for Orbit AI Agent.

This module defines all SQLAlchemy ORM models for the application.
"""

from datetime import datetime
from typing import Optional, List, Any
from uuid import uuid4

from sqlalchemy import (
    String, Text, Integer, DateTime, JSON, ForeignKey, Index, func, Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from src.db.base import Base


# Enums for status fields
class SessionStatus(str, SQLEnum):
    """Status for sessions."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MessageRole(str, SQLEnum):
    """Role for messages."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ToolCallStatus(str, SQLEnum):
    """Status for tool calls."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStatus(str, SQLEnum):
    """Status for workflow executions."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepStatus(str, SQLEnum):
    """Status for workflow steps."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ============================================================================
# Session Models
# ============================================================================

class Session(Base):
    """
    Represents a conversation session.

    A session contains multiple messages and tracks the overall state
    of a conversation between a user and the agent.
    """
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus),
        default=SessionStatus.ACTIVE,
        nullable=False,
        index=True
    )
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at.asc()"
    )
    tool_calls: Mapped[List["ToolCall"]] = relationship(
        "ToolCall",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    agent_states: Mapped[List["AgentState"]] = relationship(
        "AgentState",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    embeddings: Mapped[List["Embedding"]] = relationship(
        "Embedding",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    workflow_executions: Mapped[List["WorkflowExecution"]] = relationship(
        "WorkflowExecution",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, status={self.status.value})>"


# ============================================================================
# Message Models
# ============================================================================

class Message(Base):
    """
    Represents a single message in a conversation.

    Messages can be from the user, assistant, system, or tool outputs.
    """
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[MessageRole] = mapped_column(
        SQLEnum(MessageRole),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="messages")
    tool_calls: Mapped[List["ToolCall"]] = relationship(
        "ToolCall",
        back_populates="message",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_messages_session_created", "session_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role.value}, session_id={self.session_id})>"


# ============================================================================
# Tool Call Models
# ============================================================================

class ToolCall(Base):
    """
    Represents the execution of a tool.

    Tracks tool name, inputs, outputs, status, and execution time.
    """
    __tablename__ = "tool_calls"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True
    )
    session_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    inputs: Mapped[dict] = mapped_column(JSONB, nullable=False)
    outputs: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ToolCallStatus] = mapped_column(
        SQLEnum(ToolCallStatus),
        nullable=False,
        index=True
    )
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="tool_calls")
    message: Mapped[Optional["Message"]] = relationship("Message", back_populates="tool_calls")

    def __repr__(self) -> str:
        return f"<ToolCall(id={self.id}, tool_name={self.tool_name}, status={self.status.value})>"


# ============================================================================
# Agent State Models (for Checkpointing)
# ============================================================================

class AgentState(Base):
    """
    Stores agent state for pause/resume functionality.

    Used by LangGraph checkpointer to save/restore workflow state.
    """
    __tablename__ = "agent_states"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    thread_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    state: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="agent_states")

    def __repr__(self) -> str:
        return f"<AgentState(id={self.id}, thread_id={self.thread_id})>"


# ============================================================================
# Embedding Models (for RAG)
# ============================================================================

class Embedding(Base):
    """
    Stores text embeddings for semantic search.

    Used for RAG (Retrieval-Augmented Generation) to find relevant
    context based on vector similarity.
    """
    __tablename__ = "embeddings"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    # embedding column will be added in a separate migration with pgvector extension
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    session: Mapped[Optional["Session"]] = relationship("Session", back_populates="embeddings")

    # Indexes (HNSW index for vector search added in pgvector migration)
    __table_args__ = (
        Index("idx_embeddings_entity", "entity_type", "entity_id"),
        Index("idx_embeddings_session", "session_id"),
    )

    def __repr__(self) -> str:
        return f"<Embedding(id={self.id}, entity_type={self.entity_type})>"


# ============================================================================
# Workflow Execution Models (for Autonomous Workflows)
# ============================================================================

class WorkflowExecution(Base):
    """
    Represents an autonomous workflow execution.

    Tracks the execution of multi-step workflows including status,
    current step, and results.
    """
    __tablename__ = "workflow_executions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    workflow_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[WorkflowStatus] = mapped_column(
        SQLEnum(WorkflowStatus),
        default=WorkflowStatus.PENDING,
        nullable=False,
        index=True
    )
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    total_steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="workflow_executions")
    steps: Mapped[List["WorkflowStep"]] = relationship(
        "WorkflowStep",
        back_populates="workflow_execution",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.step_order.asc()"
    )

    def __repr__(self) -> str:
        return f"<WorkflowExecution(id={self.id}, workflow_name={self.workflow_name}, status={self.status.value})>"


class WorkflowStep(Base):
    """
    Represents a single step in a workflow execution.

    Each step tracks its own status, inputs, outputs, and execution time.
    """
    __tablename__ = "workflow_steps"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_execution_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False
    )
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[WorkflowStepStatus] = mapped_column(
        SQLEnum(WorkflowStepStatus),
        default=WorkflowStepStatus.PENDING,
        nullable=False
    )
    input_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    workflow_execution: Mapped["WorkflowExecution"] = relationship("WorkflowExecution", back_populates="steps")

    # Indexes
    __table_args__ = (
        Index("idx_workflow_steps_execution_order", "workflow_execution_id", "step_order"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowStep(id={self.id}, step_name={self.step_name}, status={self.status.value})>"
