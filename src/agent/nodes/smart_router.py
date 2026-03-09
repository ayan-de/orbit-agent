"""
Smart Router Node for intelligent tool loading.

Runs BEFORE planner to classify request and load needed tools.
"""

import logging
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.agent.state import AgentState
from src.integrations.classifier import get_classifier, ClassificationResult
from src.integrations.registry import get_registry

logger = logging.getLogger(__name__)


def extract_user_request(messages: list[BaseMessage]) -> str:
    """
    Extract the user's request from message history.

    Args:
        messages: List of conversation messages

    Returns:
        User request string
    """
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            content = msg.content
            if isinstance(content, list):
                # Handle multi-part messages
                texts = []
                for part in content:
                    if isinstance(part, dict):
                        texts.append(part.get("text", ""))
                    else:
                        texts.append(str(part))
                return " ".join(texts)
            return str(content)
    return ""


def check_auth_requirements(
    integrations: list[str],
    registry: Any,
    state: AgentState
) -> list[dict]:
    """
    Check if any integrations require authentication.

    Args:
        integrations: List of integration names
        registry: IntegrationRegistry instance
        state: Current agent state

    Returns:
        List of dicts with integration info needing auth
    """
    auth_required = []
    user_tokens = state.get("user_tokens", {})

    for integration_name in integrations:
        config = registry.get_config(integration_name)
        if config and config.requires_auth:
            # Check if user has token for this integration
            has_token = user_tokens.get(integration_name) is not None
            if not has_token:
                auth_required.append({
                    "name": integration_name,
                    "display_name": config.display_name,
                    "icon": config.icon,
                    "mcp_server": config.mcp_server,
                })

    return auth_required


async def smart_router_node(state: AgentState) -> dict:
    """
    Smart router node that runs BEFORE planner.

    Flow:
    1. Extract user request from messages
    2. Classify which integrations are needed
    3. Check auth requirements
    4. Get toolset from registry
    5. Return state update with loaded tools

    Args:
        state: Current agent state

    Returns:
        State update dictionary
    """
    logger.info("Smart router node executing...")

    # 1. Extract user request
    request = extract_user_request(state.get("messages", []))
    if not request:
        logger.warning("No user request found in messages")
        return {
            "loaded_integrations": ["web_search"],
            "total_tool_count": 0,
            "executor_tools": [],
        }

    logger.info(f"Classifying request: {request[:100]}...")

    # 2. Classify request
    classifier = get_classifier()
    result: ClassificationResult = await classifier.classify(request)

    integrations = result.integrations
    logger.info(
        f"Classification result: integrations={integrations}, "
        f"method={result.method}, confidence={result.confidence}"
    )

    # 3. Get registry and check auth
    registry = await get_registry()

    auth_required = check_auth_requirements(integrations, registry, state)
    if auth_required:
        logger.info(f"Auth required for integrations: {[a['name'] for a in auth_required]}")
        return {
            "auth_required_integrations": auth_required,
            "loaded_integrations": integrations,
            "messages": [AIMessage(
                content=f"Please connect the following integrations to proceed: "
                        f"{', '.join(a['display_name'] for a in auth_required)}"
            )],
        }

    # 4. Get tools from registry
    tools = registry.get_toolset(integrations)
    tool_count = len(tools)

    # 5. Get hints for planner/executor
    planner_hints = registry.get_hints(integrations, "planner")
    executor_hints = registry.get_hints(integrations, "executor")

    logger.info(f"Loaded {tool_count} tools for integrations: {integrations}")

    return {
        "loaded_integrations": integrations,
        "total_tool_count": tool_count,
        "executor_tools": tools,
        "planner_hints": planner_hints,
        "executor_hints": executor_hints,
        "classification_method": result.method,
        "classification_confidence": result.confidence,
    }


def route_after_smart_router(state: AgentState) -> str:
    """
    Determine next step after smart router.

    Args:
        state: Current agent state

    Returns:
        Next node name: "planner" or "end"
    """
    # If auth required, end flow and prompt user
    if state.get("auth_required_integrations"):
        return "end"

    # Otherwise, proceed to planner
    return "planner"
