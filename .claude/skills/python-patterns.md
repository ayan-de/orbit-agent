---
description: "Pythonic idioms, type hints, and best practices for orbit-agent"
globs: ["**/*.py"]
---

# Python Patterns

## Type Hints (MANDATORY)

Always use type hints for function signatures:

```python
from typing import TypedDict, NotRequired
from collections.abc import Callable, Awaitable

# Good: Full type hints
async def process_message(
    message: str,
    session_id: str,
    options: dict[str, Any] | None = None
) -> ProcessResult:
    ...

# TypedDict for structured dicts
class Message(TypedDict):
    role: str
    content: str
    timestamp: NotRequired[str]
```

## Pydantic for Data Validation

```python
from pydantic import BaseModel, Field, validator

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: str = Field(..., pattern=r"^[\w-]+$")

    @validator("message")
    def sanitize(cls, v: str) -> str:
        return v.strip()

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tokens_used: int
```

## Async Patterns

```python
# Concurrent execution
import asyncio

async def process_concurrent(items: list[str]) -> list[Result]:
    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks)

# With rate limiting
from asyncio import Semaphore

async def process_with_limit(items: list[str], max_concurrent: int = 5) -> list[Result]:
    semaphore = Semaphore(max_concurrent)

    async def limited_process(item: str) -> Result:
        async with semaphore:
            return await process_item(item)

    return await asyncio.gather(*[limited_process(i) for i in items])
```

## Error Handling

```python
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Custom exceptions
class AgentError(Exception):
    """Base exception for agent errors"""

class LLMError(AgentError):
    """LLM-related errors"""

class UnsafeCommandError(AgentError):
    """Command safety violation"""

# Decorator for async error handling
def handle_errors(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AgentError:
            raise  # Re-raise known errors
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            raise AgentError(f"Processing failed: {e}") from e
    return wrapper
```

## Dependency Injection

```python
from dataclasses import dataclass
from typing import Protocol

class LLMProtocol(Protocol):
    async def ainvoke(self, prompt: str) -> str: ...

@dataclass
class AgentServices:
    llm: LLMProtocol
    db: DatabaseRepository
    memory: MemoryStore

class AgentNode:
    def __init__(self, services: AgentServices):
        self.llm = services.llm
        self.db = services.db
        self.memory = services.memory
```

## Configuration with pydantic-settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Required
    openai_api_key: str
    database_url: str

    # Optional with defaults
    log_level: str = "INFO"
    max_retries: int = 3
    default_model: str = "gpt-4o"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()  # Validates at startup
```

## Logging

```python
import structlog

logger = structlog.get_logger()

async def process_message(message: str) -> Result:
    log = logger.bind(message_length=len(message))

    log.info("Processing message")

    try:
        result = await process(message)
        log.info("Message processed", tokens=result.tokens)
        return result
    except Exception as e:
        log.error("Processing failed", error=str(e))
        raise
```
