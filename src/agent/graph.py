"""
LangGraph workflow definition for Orbit AI Agent.

Defines complete state graph with nodes and conditional edges.

ARCHITECTURE NOTE - INTERNAL ROUTING:
This graph implements INTERNAL ROUTING system for agent.

There are TWO distinct routing systems in Orbit architecture:

1. EXTERNAL ROUTING (TypeScript MessageRouterService):
   - Routes: External Chat Platforms → Bridge → Agent
   - Scope: Routing messages FROM platforms TO agent system
   - Pattern: Strategy Pattern for platform adapters
   - File: packages/bridge/src/application/adapters/message-router.service.ts

2. INTERNAL ROUTING (this - Python LangGraph):
   - Routes: Agent Intent Classification → Workflow Nodes
   - Scope: Routing WITHIN agent state machine
   - Pattern: LangGraph conditional edges
   - File: this file (graph.py)

ROUTING BOUNDARY:
- External Router: ENDS at Python Agent (hands off to agent)
- Internal Router: STARTS at Python Agent (takes over from external router)

FLOW:
User/Chat → MessageRouterService (EXTERNAL) → Python Agent → LangGraph (INTERNAL)

INTERNAL ROUTING RESPONSIBILITIES (this graph):
- Classify user intent (command, question, workflow, email, web_search)
- Route to appropriate node based on intent
- Execute plans if needed (planner → executor → evaluator cycle)
- Generate responses via responder node
- Handle email workflow (intent → drafter → preview → sender/refinement)
- Execute web searches (web_search_node) with proper formatting

EXTERNAL ROUTING DOES NOT:
- Decide agent intent (that's classifier node's job)
- Plan multi-step workflows (that's planner node's job)
- Execute tools (that's executor node's job)
"""
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END, START

from src.agent.nodes.classifier import classify_intent
from src.agent.nodes.command_generator import generate_command
from src.agent.nodes.responder import respond
from src.agent.nodes.planner import PlannerNode, Plan
from src.agent.nodes.executor import ExecutorNode
from src.agent.nodes.evaluator import EvaluatorNode
from src.agent.nodes.email_intent import classify_email_intent
from src.agent.nodes.email_drafter import draft_email
from src.agent.nodes.email_preview import show_email_preview
from src.agent.nodes.email_sender import send_email
from src.agent.nodes.email_refinement import refine_email
from src.agent.nodes.memory_loader import memory_loader_node
from src.agent.nodes.session_writer import session_writer_node
from src.agent.nodes.human_input import (
    human_input_node,
    route_after_confirmation,
)
from src.agent.nodes.web_search import web_search_node
from src.agent.state import AgentState
from src.agent.edges import (
    route_after_classifier,
    route_after_planner,
    route_after_executor,
    route_after_evaluator,
    route_after_email_drafter,
    route_after_email_preview,
    route_after_web_search,
)
from src.memory import get_checkpointer

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
workflow.add_node("memory_loader", memory_loader_node)
workflow.add_node("classifier", classify_intent)
workflow.add_node("session_writer", session_writer_node)
workflow.add_node("command_generator", generate_command)
workflow.add_node("planner", planner)
workflow.add_node("executor", executor)
workflow.add_node("evaluator", evaluator)
workflow.add_node("responder", respond)
workflow.add_node("human_input", human_input_node)
workflow.add_node("web_search", web_search_node)
# Email nodes
workflow.add_node("email_intent", classify_email_intent)
workflow.add_node("email_drafter", draft_email)
workflow.add_node("email_preview", show_email_preview)
workflow.add_node("email_sender", send_email)
workflow.add_node("email_refinement", refine_email)

# Define edges
# START → memory_loader → classifier
workflow.add_edge(START, "memory_loader")
workflow.add_edge("memory_loader", "classifier")

# classifier → [command_generator | planner | email_intent | web_search | responder]
# Based on intent: "command", "workflow", "email", "web_search", "question", "confirmation", "unknown"
workflow.add_conditional_edges(
    "classifier",
    route_after_classifier,
    {
        "command_generator": "command_generator",
        "planner": "planner",
        "email_intent": "email_intent",
        "web_search": "web_search",
        "responder": "responder"
    }
)

# email_intent → email_drafter (after extracting email components from user message)
workflow.add_edge("email_intent", "email_drafter")

# command_generator → responder (Phase 1 flow)
workflow.add_edge("command_generator", "responder")

# planner → [human_input | responder]
# If plan has steps → human_input (for confirmation), otherwise → responder
workflow.add_conditional_edges(
    "planner",
    route_after_planner,
    {
        "human_input": "human_input",
        "responder": "responder"
    }
)

# human_input → [executor | responder]
# Based on user confirmation: approved → executor, denied → responder
workflow.add_conditional_edges(
    "human_input",
    route_after_confirmation,
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

# email_drafter → [email_preview | END]
# If draft was created (email_needs_confirmation=True) → preview, otherwise → END (error message preserved)
workflow.add_conditional_edges(
    "email_drafter",
    route_after_email_drafter,
    {
        "email_preview": "email_preview",
        "end": END
    }
)

# web_search → responder
workflow.add_edge("web_search", "responder")

# email_preview → [email_sender | email_refinement | responder]
# Based on user confirmation: "yes" to send, "cancel" to abort, otherwise refine
workflow.add_conditional_edges(
    "email_preview",
    route_after_email_preview,
    {
        "email_sender": "email_sender",
        "email_refinement": "email_refinement",
        "responder": "responder"
    }
)

# email_refinement → email_drafter
workflow.add_edge("email_refinement", "email_drafter")

# email_sender → responder (show success message)
workflow.add_edge("email_sender", "responder")

# responder → session_writer → END
workflow.add_edge("responder", "session_writer")
workflow.add_edge("session_writer", END)

# Compile graph (checkpointer attached at runtime)
app = workflow.compile(checkpointer=None)


def get_graph():
    """
    Get the compiled LangGraph application.

    Returns:
        Compiled LangGraph app
    """
    return app


async def get_compiled_graph(with_checkpointer: bool = True):
    """
    Get a compiled graph with optional checkpointer.

    Args:
        with_checkpointer: Whether to use PostgreSQL checkpointer

    Returns:
        Compiled LangGraph app
    """
    checkpointer = None
    if with_checkpointer:
        checkpointer = await get_checkpointer()
    return workflow.compile(checkpointer=checkpointer)


def get_workflow():
    """
    Get the workflow for inspection or visualization.

    Returns:
        StateGraph instance (not compiled)
    """
    return workflow
