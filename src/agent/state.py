from typing import TypedDict, Annotated, Literal, List, Dict, Any, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """The complete state of an Orbit agent execution."""
    # Conversation messages (LLM + tool results) — append-only via reducer
    messages: Annotated[List[BaseMessage], add_messages]

    # Current classification of user intent
    intent: Literal["command", "question", "workflow", "confirmation", "unknown"]

    # Generated shell command (populated by command_generator)
    command: str

    # Multi-step plan (list of planned actions)
    plan: List[Dict[str, Any]]
    current_step: int

    # Tool execution results
    tool_results: List[Dict[str, Any]]

    # Control flow
    needs_confirmation: bool
    confirmation_prompt: Optional[str]
    is_complete: bool
    evaluation_outcome: Optional[Literal["goal_achieved", "continue_execution", "needs_replanning", "fatal_error", "incomplete"]]

    # Metadata
    session_id: str
    user_id: str
    iteration_count: int
