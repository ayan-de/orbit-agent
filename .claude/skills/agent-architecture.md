---
description: "AI agent patterns for LangGraph-based agent systems"
globs: ["src/agent/**/*.py"]
---

# Agent Architecture Patterns

## Graph Structure

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Classifier │ ──► Route by intent
└──────┬──────┘
       │
       ├─────────────────┬─────────────────┐
       ▼                 ▼                 ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Planner   │   │  Responder  │   │  WebSearch  │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       ▼                 │                 │
┌─────────────┐          │                 │
│  Executor   │          │                 │
└──────┬──────┘          │                 │
       │                 │                 │
       ▼                 ▼                 ▼
┌─────────────────────────────────────────────────┐
│                   Responder                      │
└─────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│    END      │
└─────────────┘
```

## State Design

Single source of truth for graph execution:

```python
from typing import TypedDict, Annotated
from langgraph.graph import add_messages

class AgentState(TypedDict):
    # Core
    messages: Annotated[list[dict], add_messages]
    session_id: str

    # Classification
    intent: str | None
    confidence: float | None

    # Planning
    plan: list[str] | None
    current_step: int

    # Execution
    tool_calls: list[ToolCall]
    results: list[ToolResult]

    # Response
    response: str | None

    # Error handling
    errors: list[str]

    # Metadata
    tokens_used: int
    current_node: str
```

## Node Implementation

```python
from typing import Any

async def planner_node(state: AgentState) -> dict[str, Any]:
    """Generate execution plan from user message."""
    messages = state["messages"]
    last_message = messages[-1]["content"]

    # Use LLM to generate plan
    plan = await generate_plan(last_message)

    return {
        "plan": plan,
        "current_step": 0,
        "current_node": "planner"
    }
```

## Conditional Routing

```python
def route_by_intent(state: AgentState) -> str:
    """Route to appropriate node based on classified intent."""
    intent = state.get("intent")

    if intent == "command":
        return "planner"
    elif intent == "question":
        return "responder"
    elif intent == "web_search":
        return "web_search"
    else:
        return "responder"
```

## Memory Integration

```python
from langgraph.checkpoint.memory import MemorySaver

def create_graph():
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("classifier", classifier_node)
    graph.add_node("planner", planner_node)
    # ...

    # Add edges
    graph.add_conditional_edges("classifier", route_by_intent, {...})

    # Compile with checkpointer
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
```

## Safety Layer

ALL shell commands go through safety check:

```python
async def executor_node(state: AgentState) -> dict[str, Any]:
    """Execute planned commands with safety checks."""
    plan = state.get("plan", [])
    results = []

    for step in plan:
        if step.get("type") == "shell_command":
            # CRITICAL: Always check safety
            safety = is_safe_command(step["command"])

            if safety.level == SafetyLevel.DANGEROUS:
                results.append({
                    "success": False,
                    "error": f"Blocked dangerous command: {step['command']}"
                })
                continue

            if safety.level == SafetyLevel.REQUIRES_CONFIRMATION:
                approved = await request_approval(step["command"])
                if not approved:
                    continue

            result = await execute_shell(step["command"])
            results.append(result)

    return {"results": results, "current_node": "executor"}
```

## Error Recovery

```python
def error_handler_node(state: AgentState) -> dict[str, Any]:
    """Handle errors gracefully."""
    errors = state.get("errors", [])

    if errors:
        # Log all errors
        for error in errors:
            logger.error(f"Agent error: {error}")

        # Generate user-friendly message
        return {
            "response": "I encountered an issue. Let me try a different approach.",
            "errors": []  # Clear errors after handling
        }

    return {}
```
