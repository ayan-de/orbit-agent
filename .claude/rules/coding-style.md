# Coding Style

## Immutability (CRITICAL)

ALWAYS create new objects, NEVER mutate existing ones:

```python
# WRONG: Mutate in place
data["key"] = value
items.append(item)
result = state.copy()
result["plan"] = new_plan  # Mutation!

# CORRECT: Return new objects
new_data = {**data, "key": value}
new_items = [*items, item]
new_state = {**state, "plan": new_plan}  # Immutable update

# CORRECT: For nested updates
def update_nested(state: dict, path: list[str], value: Any) -> dict:
    """Immutable nested update."""
    if not path:
        return value
    key = path[0]
    return {
        **state,
        key: update_nested(state.get(key, {}), path[1:], value)
    }
```

Rationale: Immutable data prevents hidden side effects, makes debugging easier, and enables safe concurrency.

## File Organization

MANY SMALL FILES > FEW LARGE FILES:
- High cohesion, low coupling
- 200-400 lines typical, 800 max
- Extract utilities from large modules
- Organize by feature/domain, not by type

```
# Good structure
src/
├── agent/
│   ├── graph.py          # Graph definition only
│   ├── state.py          # State schema
│   └── nodes/            # One file per node
│       ├── classifier.py
│       ├── planner.py
│       └── executor.py
├── tools/
│   ├── shell.py          # Shell tool
│   └── base.py           # Base class
└── api/
    └── v1/
        └── agent.py      # Single endpoint file
```

## Import Order

Standard library → Third-party → Local imports:

```python
# Standard library
import asyncio
import logging
from typing import Any, TypedDict

# Third-party
from fastapi import HTTPException
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph

# Local imports (absolute first, then relative)
from src.config import settings
from src.llm.factory import llm_factory
from src.utils.safety import is_safe_command

logger = logging.getLogger(__name__)
```

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files | snake_case | `command_generator.py` |
| Directories | snake_case | `agent/nodes/` |
| Classes | PascalCase | `AgentState`, `CommandResult` |
| Functions | snake_case | `generate_plan()`, `execute_command()` |
| Variables | snake_case | `session_id`, `tool_result` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private | _leading_underscore | `_internal_helper()` |
| TypedDict | PascalCase + "State"/"Config" | `AgentState`, `NodeConfig` |

## Error Handling

ALWAYS handle errors comprehensively with context:

```python
from fastapi import HTTPException
from src.utils.errors import AgentError, LLMError, SafetyError

# Good: Explicit error handling with context
async def process_message(message: str, session_id: str) -> dict:
    try:
        result = await classify_and_execute(message)
    except LLMError as e:
        logger.error(f"[Process] LLM failed for session={session_id}: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable"
        ) from e
    except SafetyError as e:
        logger.warning(f"[Process] Blocked unsafe command: {e.command}")
        raise HTTPException(
            status_code=400,
            detail=f"Command blocked: {e.reason}"
        ) from e
    except Exception as e:
        logger.exception(f"[Process] Unexpected error for session={session_id}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        ) from e

    return result

# Good: Custom exception hierarchy
class AgentError(Exception):
    """Base exception for agent errors."""
    pass

class LLMError(AgentError):
    """LLM provider errors."""
    def __init__(self, message: str, provider: str):
        self.provider = provider
        super().__init__(f"[{provider}] {message}")

class SafetyError(AgentError):
    """Command safety violations."""
    def __init__(self, command: str, reason: str):
        self.command = command
        self.reason = reason
        super().__init__(f"Unsafe command '{command}': {reason}")
```

## Input Validation

ALWAYS validate at system boundaries with Pydantic:

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class MessageRequest(BaseModel):
    """Request schema for agent invocation."""
    content: str = Field(..., min_length=1, max_length=10000)
    session_id: str = Field(..., pattern=r"^[a-zA-Z0-9-]{8,36}$")
    user_id: str | None = Field(default=None)
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def content_not_whitespace(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("content cannot be empty or whitespace only")
        return v.strip()

    model_config = {
        "str_strip_whitespace": True,
        "extra": "forbid"  # Reject unknown fields
    }

# Response schema
class MessageResponse(BaseModel):
    """Response schema for agent invocation."""
    response: str
    intent: Literal["command", "question", "chat"]
    command: str | None = None
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    tokens_used: int = Field(ge=0)
```

## Logging

Structured logging with context prefixes:

```python
import logging

logger = logging.getLogger(__name__)

# Good: Context prefix + structured data
logger.info(f"[Classifier] Classified intent={intent} confidence={confidence:.2f}")
logger.error(f"[Executor] Command failed cmd='{command}' error='{error}'")
logger.debug(f"[State] Updating state node={node} step={step}")

# Bad: Unstructured logging
logger.info("Classified intent")
logger.error(f"Error: {error}")
```

## Code Quality Checklist

Before marking work complete:
- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines)
- [ ] Files are focused (<800 lines)
- [ ] No deep nesting (>4 levels)
- [ ] Proper error handling with context
- [ ] No hardcoded values (use constants or config)
- [ ] No mutation (immutable patterns used)
- [ ] Type hints on all public functions
- [ ] Docstrings on classes and public functions
- [ ] Logging with context prefixes
