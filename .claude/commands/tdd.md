# TDD Command

Enforce test-driven development workflow.

## Usage

```
/tdd "feature description"
```

## Workflow

1. **Analyze** the feature request
2. **Write** failing test first
3. **Implement** minimal code to pass
4. **Refactor** for quality
5. **Verify** 80%+ coverage

## Example

```
/tdd "Add message classification with intent detection"
```

This will:
1. Create test file `tests/test_classifier.py`
2. Write failing tests for classification
3. Implement classifier in `src/classifier.py`
4. Run tests until green
5. Refactor and verify coverage

## Checklist

- [ ] Test file created
- [ ] Test fails (RED)
- [ ] Implementation complete
- [ ] Test passes (GREEN)
- [ ] Code refactored
- [ ] Coverage ≥ 80%
