from typing import TypedDict, Annotated, Literal, List, Dict, Any, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """The complete state of an Orbit agent execution."""

    # Conversation messages (LLM + tool results) — append-only via reducer
    messages: Annotated[List[BaseMessage], add_messages]

    # Current classification of user intent
    intent: Literal["command", "question", "workflow", "confirmation", "search", "unknown"]

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

    # Human input / tool confirmation fields
    user_confirmation: Optional[bool]  # True=approved, False=denied, None=pending
    confirmation_processed: bool
    user_response: Optional[str]
    pending_tool_name: Optional[str]
    pending_tool_danger_level: Optional[int]
    auto_approved: bool

    # Metadata
    session_id: str
    user_id: str
    iteration_count: int

    # Memory context (populated by memory_loader node)
    memory_context: str
    memory_available: bool
    compaction_needed: bool

    # Environment and permissions
    environment: Literal["dev", "staging", "production"]
    user_permission_level: int
