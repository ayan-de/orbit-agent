"""
Database module for Orbit AI Agent.

Provides database connection, models, repositories, and utilities.
"""

from src.db.base import Base
from src.db.models import (
    Session,
    Message,
    ToolCall,
    AgentState,
    Embedding,
    WorkflowExecution,
    WorkflowStep,
    SessionStatus,
    MessageRole,
    ToolCallStatus,
    WorkflowStatus,
    WorkflowStepStatus,
)
from src.db.repositories.session_repo import SessionRepository
from src.db.engine import engine, async_session, get_db, init_db

__all__ = [
    # Base class
    "Base",
    # Models
    "Session",
    "Message",
    "ToolCall",
    "AgentState",
    "Embedding",
    "WorkflowExecution",
    "WorkflowStep",
    # Enums
    "SessionStatus",
    "MessageRole",
    "ToolCallStatus",
    "WorkflowStatus",
    "WorkflowStepStatus",
    # Repositories
    "SessionRepository",
    # Engine/Session
    "engine",
    "async_session",
    "get_db",
    "init_db",
]