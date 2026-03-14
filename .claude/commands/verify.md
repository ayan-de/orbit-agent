# Verify Command

Run full verification pipeline.

## Usage

```
/verify
/verify --fix     # Auto-fix issues where possible
/verify --quick   # Skip coverage check
```

## Pipeline Steps

1. **Format** - black --check
2. **Lint** - ruff check
3. **Type Check** - mypy
4. **Tests** - pytest with coverage
5. **Security** - Check for secrets and patterns

## Output

```
✓ Format check passed
✓ Lint check passed
✓ Type check passed
✓ Tests passed (coverage: 85%)
✓ Security scan passed

All verification checks passed!
```

## Fix Mode

```
/verify --fix
```

Will automatically:
- Run black to format code
- Run ruff --fix to auto-fix lint issues
- Suggest type hint fixes
