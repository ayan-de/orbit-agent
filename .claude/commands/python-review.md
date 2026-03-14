# Python Review Command

Comprehensive Python code review.

## Usage

```
/python-review
/python-review src/agent/graph.py  # Review specific file
```

## Review Checklist

### Code Quality
- [ ] Functions < 50 lines
- [ ] Files < 800 lines
- [ ] No deep nesting (>4 levels)
- [ ] Clear naming conventions
- [ ] DRY principle followed

### Type Hints
- [ ] All function parameters typed
- [ ] All return types specified
- [ ] Optional values use `| None`
- [ ] Generic types properly used

### Error Handling
- [ ] All exceptions handled
- [ ] Custom exceptions used
- [ ] Error messages are clear
- [ ] No silent failures

### Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL uses parameterized queries
- [ ] No command injection

### Testing
- [ ] Unit tests exist
- [ ] Edge cases covered
- [ ] Mocks used for external services
- [ ] Coverage ≥ 80%

### Async Patterns
- [ ] Async functions use async/await
- [ ] No blocking calls in async context
- [ ] Proper exception handling in async

## Output Format

```
## Review Summary

**File**: src/agent/graph.py

### Issues Found

#### HIGH
- Line 45: Missing type hint for parameter `state`

#### MEDIUM
- Line 78: Function exceeds 50 lines (62 lines)
- Line 102: Consider using `| None` instead of `Optional`

#### LOW
- Line 15: Consider adding docstring

### Recommendations

1. Add type hints to improve IDE support
2. Extract `process_message` into smaller functions
3. Consider using dataclass for configuration
```
