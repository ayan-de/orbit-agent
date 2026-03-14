---
description: "Comprehensive verification system - build, test, lint, typecheck, security"
globs: ["**/*.py"]
---

# Verification Loop

## Verification Pipeline

Run after ANY code change:

```bash
# Full verification
make verify

# Or individual steps:
black --check src tests
ruff check src tests
mypy src
pytest --cov=src --cov-fail-under=80
```

## Step 1: Format Check

```bash
black --check src tests
```

Fix issues:
```bash
black src tests
```

## Step 2: Lint

```bash
ruff check src tests
```

Fix issues:
```bash
ruff check --fix src tests
```

## Step 3: Type Check

```bash
mypy src --strict
```

Common fixes:
- Add return type hints
- Add parameter type hints
- Use `| None` for optional returns
- Import types from `typing`

## Step 4: Tests with Coverage

```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

## Step 5: Security Scan

```bash
# Check for secrets
grep -r "sk-\|sk-ant-\|api_key.*=" src/ --include="*.py" || echo "No secrets found"

# Check for SQL injection patterns
grep -r "f\".*SELECT\|execute(.*%" src/ --include="*.py" || echo "No SQL injection patterns"
```

## Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

set -e

echo "Running verification..."

# Format
black --check src tests

# Lint
ruff check src tests

# Type check
mypy src

# Tests
pytest tests/ -q --tb=short

echo "All checks passed!"
```

## CI/CD Integration

```yaml
# .github/workflows/verify.yml
name: Verify

on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Format check
        run: black --check src tests

      - name: Lint
        run: ruff check src tests

      - name: Type check
        run: mypy src

      - name: Test with coverage
        run: pytest --cov=src --cov-fail-under=80
```

## Makefile Integration

```makefile
# Makefile
.PHONY: verify format lint typecheck test

verify: format lint typecheck test

format:
	black src tests

lint:
	ruff check --fix src tests

typecheck:
	mypy src

test:
	pytest --cov=src --cov-fail-under=80

dev:
	uvicorn src.main:app --reload --port 8000
```
