---
description: "Test-driven development workflow for Python projects"
globs: ["**/*.py"]
---

# TDD Workflow

## RED → GREEN → REFACTOR

### Step 1: Write Test First (RED)

Before implementing ANY feature:

```python
# tests/test_new_feature.py
import pytest
from src.module import new_function

@pytest.mark.asyncio
async def test_new_function_returns_expected_result():
    # Arrange
    input_data = "test input"

    # Act
    result = await new_function(input_data)

    # Assert
    assert result == "expected output"
```

Run test - it MUST FAIL:
```bash
pytest tests/test_new_feature.py -v
```

### Step 2: Minimal Implementation (GREEN)

Write ONLY enough code to pass:

```python
# src/module.py
async def new_function(input_data: str) -> str:
    return "expected output"
```

Run test - it MUST PASS:
```bash
pytest tests/test_new_feature.py -v
```

### Step 3: Refactor (IMPROVE)

Improve code while keeping tests green:
- Extract functions
- Add type hints
- Handle edge cases
- Optimize performance

### Step 4: Verify Coverage

```bash
pytest --cov=src --cov-report=term-missing
```

Target: 80%+ coverage

## Test Patterns

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Mocking External Services

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mock():
    with patch("src.llm.factory.llm_factory") as mock:
        mock.return_value.ainvoke = AsyncMock(return_value="mocked")
        result = await function_using_llm()
        assert result == "expected"
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "greeting"),
    ("goodbye", "farewell"),
    ("thanks", "gratitude"),
])
async def test_classifier(input, expected):
    result = await classify(input)
    assert result == expected
```

## Coverage Gates

Pre-commit hook should verify:
```bash
#!/bin/bash
coverage run -m pytest
coverage report --fail-under=80
```
