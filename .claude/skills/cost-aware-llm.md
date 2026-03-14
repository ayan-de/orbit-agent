---
description: "LLM cost optimization patterns - model routing, budget tracking, token efficiency"
globs: ["**/*.py"]
---

# Cost-Aware LLM Pipeline

## Model Selection Strategy

Route to appropriate model based on task complexity:

```python
from enum import Enum
from dataclasses import dataclass

class TaskComplexity(Enum):
    SIMPLE = "simple"      # Classification, short responses
    MODERATE = "moderate"  # Planning, summarization
    COMPLEX = "complex"    # Reasoning, code generation
    CRITICAL = "critical"  # Security decisions, complex reasoning

@dataclass
class ModelConfig:
    provider: str
    model: str
    max_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float

MODEL_ROUTING = {
    TaskComplexity.SIMPLE: ModelConfig(
        provider="openai",
        model="gpt-4o-mini",
        max_tokens=1000,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006
    ),
    TaskComplexity.MODERATE: ModelConfig(
        provider="openai",
        model="gpt-4o",
        max_tokens=4000,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015
    ),
    TaskComplexity.COMPLEX: ModelConfig(
        provider="anthropic",
        model="claude-sonnet-4-6-20250514",
        max_tokens=8000,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015
    ),
    TaskComplexity.CRITICAL: ModelConfig(
        provider="anthropic",
        model="claude-opus-4-6-20250514",
        max_tokens=16000,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075
    )
}

def get_model_for_complexity(complexity: TaskComplexity) -> ModelConfig:
    return MODEL_ROUTING[complexity]
```

## Budget Tracking

```python
from typing import TypedDict

class TokenUsage(TypedDict):
    input_tokens: int
    output_tokens: int
    cost_usd: float

class BudgetTracker:
    def __init__(self, max_budget_usd: float = 1.0):
        self.max_budget = max_budget_usd
        self.spent = 0.0
        self.usage_history: list[TokenUsage] = []

    async def track_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        model: ModelConfig
    ) -> TokenUsage:
        cost = (
            (input_tokens / 1000) * model.cost_per_1k_input +
            (output_tokens / 1000) * model.cost_per_1k_output
        )

        if self.spent + cost > self.max_budget:
            raise BudgetExceededError(
                f"Budget exceeded: ${self.spent:.4f} + ${cost:.4f} > ${self.max_budget:.4f}"
            )

        usage: TokenUsage = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost
        }

        self.usage_history.append(usage)
        self.spent += cost

        return usage

    def get_summary(self) -> dict:
        return {
            "total_spent_usd": self.spent,
            "budget_remaining_usd": self.max_budget - self.spent,
            "total_requests": len(self.usage_history),
            "total_input_tokens": sum(u["input_tokens"] for u in self.usage_history),
            "total_output_tokens": sum(u["output_tokens"] for u in self.usage_history)
        }
```

## Token Optimization

```python
def estimate_tokens(text: str) -> int:
    """Rough token estimation: ~4 chars per token for English."""
    return len(text) // 4

def truncate_to_budget(text: str, max_tokens: int) -> str:
    """Truncate text to fit within token budget."""
    estimated = estimate_tokens(text)
    if estimated <= max_tokens:
        return text

    # Truncate to approximate token limit
    char_limit = max_tokens * 4
    return text[:char_limit - 100] + "\n...[truncated]"

def compact_messages(messages: list[dict], max_tokens: int) -> list[dict]:
    """Compact message history to fit token budget."""
    total = sum(estimate_tokens(m.get("content", "")) for m in messages)

    if total <= max_tokens:
        return messages

    # Keep first and last messages, summarize middle
    if len(messages) <= 2:
        return messages

    first = messages[0]
    last = messages[-1]
    middle = messages[1:-1]

    # Summarize middle messages
    summary = summarize_messages(middle)

    return [
        first,
        {"role": "system", "content": f"[Previous context: {summary}]"},
        last
    ]
```

## Streaming for Cost Visibility

```python
from typing import AsyncGenerator

async def stream_with_tracking(
    prompt: str,
    model: ModelConfig,
    budget: BudgetTracker
) -> AsyncGenerator[str, None]:
    """Stream response while tracking token usage."""
    llm = llm_factory(provider=model.provider, model=model.model)

    input_tokens = estimate_tokens(prompt)
    output_tokens = 0

    async for chunk in llm.astream(prompt):
        output_tokens += estimate_tokens(chunk)
        yield chunk

    # Track after completion
    await budget.track_usage(input_tokens, output_tokens, model)
```
