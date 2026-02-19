"""
Conditional edge functions for LangGraph workflow.

Determines routing between nodes based on agent state.
"""

from typing import Literal
from src.agent.state import AgentState


def route_after_classifier(state: AgentState) -> Literal["command_generator", "planner", "responder"]:
    """
    Route after classifier based on intent.

    - "question" → responder (simple Q&A)
    - "workflow" → planner (multi-step task)
    - "command" → command_generator (single shell command, Phase 1 flow)
    - "confirmation" → responder (user confirmed action)
    - "unknown" → responder (fallback)
    """
    intent = state.get("intent", "unknown")

    if intent == "question":
        return "responder"
    elif intent == "workflow":
        return "planner"
    elif intent == "command":
        return "command_generator"
    elif intent == "confirmation":
        return "responder"
    else:
        # Unknown or unexpected intent
        return "responder"


def route_after_planner(state: AgentState) -> Literal["executor", "responder"]:
    """
    Route after planner based on plan.

    - Plan has steps → executor
    - Plan is empty or failed → responder
    """
    plan = state.get("plan", {})
    steps = plan.get("steps", [])

    if steps:
        return "executor"
    else:
        return "responder"


def route_after_executor(state: AgentState) -> Literal["evaluator"]:
    """
    Route after executor.

    Always go to evaluator for result analysis.
    """
    return "evaluator"


def route_after_evaluator(state: AgentState) -> Literal["executor", "planner", "responder"]:
    """
    Route after evaluator based on evaluation outcome.

    The evaluator should set evaluation_outcome in state.
    Possible outcomes:
    - "continue_execution" → executor (next step)
    - "needs_replanning" → planner (create new plan)
    - "goal_achieved" → responder (done)
    - "fatal_error" → responder (abort)
    - "incomplete" → responder (explain gaps)
    """
    evaluation_outcome = state.get("evaluation_outcome", "unknown")

    if evaluation_outcome == "continue_execution":
        return "executor"
    elif evaluation_outcome == "needs_replanning":
        return "planner"
    elif evaluation_outcome in ["goal_achieved", "fatal_error", "incomplete"]:
        return "responder"
    else:
        # Unknown outcome, default to responder
        return "responder"


def should_continue_execution(state: AgentState) -> bool:
    """
    Determine if execution should continue to next step.

    Args:
        state: Agent state

    Returns:
        True if should continue, False otherwise
    """
    evaluation_outcome = state.get("evaluation_outcome")
    return evaluation_outcome == "continue_execution"


def should_replan(state: AgentState) -> bool:
    """
    Determine if re-planning is needed.

    Args:
        state: Agent state

    Returns:
        True if re-planning needed, False otherwise
    """
    evaluation_outcome = state.get("evaluation_outcome")
    return evaluation_outcome == "needs_replanning"


def should_respond(state: AgentState) -> bool:
    """
    Determine if should respond to user.

    Args:
        state: Agent state

    Returns:
        True if should respond, False otherwise
    """
    evaluation_outcome = state.get("evaluation_outcome")
    return evaluation_outcome in ["goal_achieved", "fatal_error", "incomplete"]
