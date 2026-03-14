# Security Guidelines

## Mandatory Security Checks

Before ANY commit:
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries via SQLAlchemy)
- [ ] No shell injection in command execution
- [ ] Error messages don't leak sensitive data

## Secret Management

- NEVER hardcode secrets in source code
- ALWAYS use environment variables via pydantic-settings
- Validate that required secrets are present at startup
- Rotate any secrets that may have been exposed

```python
# Good: Load from environment
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    anthropic_api_key: str
    database_url: str

    class Config:
        env_file = ".env"

settings = Settings()  # Fails fast if missing
```

## Command Safety (CRITICAL for orbit-agent)

ALL shell commands MUST go through `src/utils/safety.py::is_safe_command()`:

```python
from src.utils.safety import is_safe_command, SafetyLevel

async def execute_command(command: str) -> CommandResult:
    safety = is_safe_command(command)

    if safety.level == SafetyLevel.DANGEROUS:
        raise UnsafeCommandError(f"Blocked dangerous command: {command}")

    if safety.level == SafetyLevel.REQUIRES_CONFIRMATION:
        # Must get user approval via bridge
        approved = await request_user_approval(command)
        if not approved:
            raise CommandRejectedError(command)

    # Only then execute
    return await run_command(command)
```

## API Security

```python
# Always validate input
from fastapi import HTTPException

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    if len(request.content) > MAX_MESSAGE_LENGTH:
        raise HTTPException(400, "Message too long")

    if contains_injection(request.content):
        raise HTTPException(400, "Invalid input")
```

## Security Response Protocol

If security issue found:
1. STOP immediately
2. Document the vulnerability
3. Fix CRITICAL issues before continuing
4. Rotate any exposed secrets
5. Review entire codebase for similar issues
