"""
LangGraph workflow definition for Orbit AI Agent.

Defines the complete state graph with nodes and conditional edges.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END, START
from src.agent.nodes.classifier import classify_intent
from src.agent.nodes.command_generator import generate_command
from src.agent.nodes.responder import respond
from src.agent.nodes.planner import PlannerNode, Plan
from src.agent.nodes.executor import ExecutorNode
from src.agent.nodes.evaluator import EvaluatorNode
from src.agent.state import AgentState
from src.agent.edges import (
    route_after_classifier,
    route_after_planner,
    route_after_executor,
    route_after_evaluator
)

# Initialize nodes
planner_node = PlannerNode()
executor_node = ExecutorNode()
evaluator_node = EvaluatorNode()


async def planner(state: AgentState) -> Dict[str, Any]:
    """
    Wrapper for planner node to integrate with LangGraph state.

    Args:
        state: Current agent state

    Returns:
        State updates
    """
    plan: Plan = await planner_node.create_plan(state)

    # Update state with plan
    return {
        "plan": plan.to_dict(),
        "current_step": 1,
        "tool_results": [],
        "is_complete": False
    }


async def executor(state: AgentState) -> Dict[str, Any]:
    """
    Wrapper for executor node to integrate with LangGraph state.

    Args:
        state: Current agent state

    Returns:
        State updates
    """
    plan = state.get("plan", {})
    session_id = state.get("session_id", "")
    user_id = state.get("user_id", "")

    # Execute the plan (this will need db_session passed)
    # For now, we'll use a placeholder - actual integration will need db session
    results = await executor_node.execute_plan(
        state=state,
        plan=plan,
        session_id=session_id,
        user_id=user_id,
        db_session=None  # TODO: Pass actual db session
    )

    return {
        "tool_results": results.get("results", []),
        "execution_status": results.get("status", "unknown")
    }


async def evaluator(state: AgentState) -> Dict[str, Any]:
    """
    Wrapper for evaluator node to integrate with LangGraph state.

    Args:
        state: Current agent state

    Returns:
        State updates
    """
    execution_results = state.get("tool_results", [])

    evaluation_result = await evaluator_node.evaluate(
        state=state,
        execution_results=execution_results
    )

    # Update state with evaluation outcome
    return {
        "evaluation_outcome": evaluation_result.get("outcome"),
        "evaluation_reasoning": evaluation_result.get("reasoning"),
        "current_step": evaluation_result.get("current_step", state.get("current_step", 0)),
        "is_complete": evaluation_result.get("outcome") in ["goal_achieved", "fatal_error", "incomplete"]
    }


# Create the workflow
workflow = StateGraph(AgentState)

# Add all nodes
workflow.add_node("classifier", classify_intent)
workflow.add_node("command_generator", generate_command)
workflow.add_node("planner", planner)
workflow.add_node("executor", executor)
workflow.add_node("evaluator", evaluator)
workflow.add_node("responder", respond)

# Define edges

# START → classifier
workflow.add_edge(START, "classifier")

# classifier → [command_generator | planner | responder]
# Based on intent: "command", "workflow", "question", "confirmation", "unknown"
workflow.add_conditional_edges(
    "classifier",
    route_after_classifier,
    {
        "command_generator": "command_generator",
        "planner": "planner",
        "responder": "responder"
    }
)

# command_generator → responder (Phase 1 flow)
workflow.add_edge("command_generator", "responder")

# planner → [executor | responder]
# If plan has steps → executor, otherwise → responder
workflow.add_conditional_edges(
    "planner",
    route_after_planner,
    {
        "executor": "executor",
        "responder": "responder"
    }
)

# executor → evaluator
workflow.add_edge("executor", "evaluator")

# evaluator → [executor | planner | responder]
# Based on evaluation outcome:
# - "continue_execution" → executor (next step)
# - "needs_replanning" → planner (create new plan)
# - "goal_achieved" → responder (done)
# - "fatal_error" → responder (abort)
# - "incomplete" → responder (explain gaps)
workflow.add_conditional_edges(
    "evaluator",
    route_after_evaluator,
    {
        "executor": "executor",
        "planner": "planner",
        "responder": "responder"
    }
)

# responder → END
workflow.add_edge("responder", END)

# Compile the graph
app = workflow.compile()


def get_graph():
    """
    Get the compiled LangGraph application.

    Returns:
        Compiled LangGraph app
    """
    return app


def get_workflow():
    """
    Get the workflow for inspection or visualization.

    Returns:
        StateGraph instance (not compiled)
    """
    return workflow
