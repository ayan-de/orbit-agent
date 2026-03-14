# Test Coverage Command

Analyze and improve test coverage.

## Usage

```
/test-coverage
/test-coverage src/agent/  # Specific directory
/test-coverage --missing   # Show only uncovered lines
```

## Output

```
# Test Coverage Report

## Summary
- Total Coverage: 78%
- Target: 80%
- Gap: 2%

## By Module

| Module | Coverage | Missing |
|--------|----------|---------|
| src/agent/graph.py | 92% | Lines 145-150 |
| src/agent/nodes/planner.py | 85% | Lines 67, 89-92 |
| src/llm/factory.py | 95% | Line 34 |
| src/utils/safety.py | 72% | Lines 45-60, 78-85 |

## Uncovered Areas

### src/utils/safety.py (72%)
Missing tests for:
- `is_safe_command()` edge cases
- Complex command parsing
- LLM verification fallback

### src/agent/nodes/planner.py (85%)
Missing tests for:
- Empty plan handling
- Error recovery paths
- Multi-step plan generation

## Recommendations

1. Add tests for `safety.py` edge cases (PRIORITY: HIGH)
2. Add integration tests for planner error paths
3. Add mock LLM tests for factory error handling
```
