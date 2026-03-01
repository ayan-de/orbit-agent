from typing import TypedDict, Annotated, Literal, List, Dict, Any, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """The complete state of an Orbit agent execution."""

    # Conversation messages (LLM + tool results) — append-only via reducer
    messages: Annotated[List[BaseMessage], add_messages]

    # Current classification of user intent
    intent: Literal["command", "question", "workflow", "confirmation", "email", "unknown"]

    # Email-specific fields
    email_draft_id: Optional[int]
    email_to: Optional[str]
    email_subject: Optional[str]
    email_body: Optional[str]
    email_cc: Optional[List[str]]
    email_attachments: Optional[List[Dict[str, Any]]]
    email_needs_confirmation: bool
    email_confirmation_prompt: Optional[str]
    email_refinement_iteration: int
    email_sent_message_id: Optional[str]
    # Content generation flags (set by email_intent when email needs data from external sources)
    needs_content_generation: bool
    content_source: Optional[str]

    # Generated shell command (populated by command_generator)
    command: str

    # Multi-step plan (dict with steps, goal, etc.)
    plan: Dict[str, Any]
    current_step: int

    # Tool execution results
    tool_results: List[Dict[str, Any]]

    # Control flow
    needs_confirmation: bool
    confirmation_prompt: Optional[str]
    is_complete: bool
    evaluation_outcome: Optional[
        Literal[
            "goal_achieved",
            "continue_execution",
            "needs_replanning",
            "fatal_error",
            "incomplete",
        ]
    ]

    # Metadata
    session_id: str
    user_id: str
    iteration_count: int

    # Memory context (populated by memory_loader node)
    memory_context: str
    memory_available: bool
    compaction_needed: bool
