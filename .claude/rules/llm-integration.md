# LLM Integration

## Multi-Provider Support

Use `src/llm/factory.py::llm_factory()` for ALL LLM calls:

```python
from src.llm.factory import llm_factory, LLMProvider

# Create LLM instance
llm = llm_factory(
    provider=LLMProvider.OPENAI,  # or ANTHROPIC, GEMINI, GLM
    model="gpt-4o",
    temperature=0.7
)

# Invoke
response = await llm.ainvoke("Your prompt here")
```

## Provider Configuration

Environment variables required:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
DEFAULT_LLM_PROVIDER=openai
```

## Never Hardcode Provider Logic

```python
# BAD: Provider-specific code in nodes
if provider == "openai":
    response = await openai_client.chat(...)
elif provider == "anthropic":
    response = await anthropic_client.messages...

# GOOD: Use factory
llm = llm_factory(provider=settings.default_provider)
response = await llm.ainvoke(prompt)
```

## Token Management

Track token usage in state:

```python
class AgentState(TypedDict):
    # ... other fields
    token_usage: dict[str, int]

# After LLM call
token_usage = {
    "prompt_tokens": response.usage_metadata["input_tokens"],
    "completion_tokens": response.usage_metadata["output_tokens"],
    "total_tokens": response.usage_metadata["total_tokens"]
}
```

## Streaming Responses

```python
async def stream_response(prompt: str):
    llm = llm_factory(streaming=True)
    async for chunk in llm.astream(prompt):
        yield chunk.content
```

## Cost-Aware Model Selection

```python
# Use cheaper models for simple tasks
def get_model_for_task(task_complexity: str) -> str:
    if task_complexity == "simple":
        return "gpt-4o-mini"  # or haiku
    elif task_complexity == "complex":
        return "gpt-4o"  # or sonnet
    else:
        return "o1"  # or opus for reasoning
```

## Testing with Mock LLMs

```python
@pytest.fixture
def mock_llm_factory():
    with patch("src.llm.factory.llm_factory") as mock:
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(return_value="mocked response")
        mock.return_value = mock_llm
        yield mock
```
