# LangGraph Patterns

## State Management

AgentState is the SINGLE SOURCE OF TRUTH:

```python
from typing import TypedDict, Annotated
from langgraph.graph import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    session_id: str
    plan: list[str] | None
    current_node: str
    errors: list[str]
```

## Node Conventions

Nodes MUST:
1. Accept state as input
2. Return PARTIAL state updates (not full state)
3. Be pure functions (no side effects outside state)

```python
# Good: Node returns partial update
async def planner_node(state: AgentState) -> dict:
    messages = state["messages"]
    plan = await generate_plan(messages)

    return {
        "plan": plan,
        "current_node": "planner"
    }

# BAD: Mutating state directly
async def bad_node(state: AgentState) -> dict:
    state["plan"] = [...]  # NEVER do this
    return state
```

## Edge Functions

Edges determine routing based on state:

```python
def should_continue(state: AgentState) -> str:
    if state.get("errors"):
        return "error_handler"
    if state.get("plan"):
        return "executor"
    return "responder"
```

## Conditional Edges

```python
from langgraph.graph import StateGraph

graph = StateGraph(AgentState)
graph.add_conditional_edges(
    "classifier",
    route_by_type,
    {
        "command": "command_generator",
        "question": "responder",
        "chat": "responder"
    }
)
```

## Checkpointing

Use memory checkpointer for session persistence:

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)

# Resume from checkpoint
config = {"configurable": {"thread_id": session_id}}
result = await app.ainvoke(input, config=config)
```

## Testing Graphs

```python
@pytest.mark.asyncio
async def test_graph_execution():
    app = create_agent_graph()

    initial_state = {
        "messages": [{"role": "user", "content": "test"}],
        "session_id": "test-session"
    }

    result = await app.ainvoke(initial_state)

    assert "messages" in result
    assert len(result["messages"]) > 1  # Should have response
```
