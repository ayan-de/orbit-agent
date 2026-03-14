# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Orbit AI Agent is a Python microservice that implements an intelligent agent capable of understanding natural language and executing shell commands through a safety-first architecture.

The agent uses **LangGraph** for workflow orchestration, **FastAPI** for REST APIs, and communicates with a separate **NestJS Bridge** service for actual shell command execution on user machines.

---

## Development Commands

```bash
# Install dependencies
make install

# Run development server (hot reload)
make dev

# Run tests
make test

# Format and lint code
make lint

# Run database migrations
make migrate

# Run single test file
pytest tests/path/to/test_file.py

# Run with coverage (80% minimum)
pytest --cov=src --cov-fail-under=80

# Run specific test pattern
pytest -k "classifier" -v

# Type checking
mypy src/ --ignore-missing-imports
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           User's Machine                                 │
│  ┌─────────────┐                                                        │
│  │  Desktop    │                                                        │
│  │  TUI/CLI    │                                                        │
│  └──────┬──────┘                                                        │
└─────────┼───────────────────────────────────────────────────────────────┘
          │ WebSocket
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        NestJS Bridge (:3000)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │  WebSocket   │  │    REST      │  │   Shell      │                   │
│  │  Gateway     │  │    API       │  │   Executor   │                   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                   │
└─────────┼─────────────────┼─────────────────┼───────────────────────────┘
          │                 │                 │
          │ HTTP/SSE        │                 │ Local shell
          ▼                 │                 │
┌─────────────────────────────────────────────────────────────────────────┐
│                        Python Agent (:8000)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │   FastAPI    │  │  LangGraph   │  │   LLM        │                   │
│  │   REST API   │──│   Agent      │──│   Factory    │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
│         │                 │                                             │
│         │                 ▼                                             │
│         │          ┌──────────────┐                                     │
│         │          │   Safety     │                                     │
│         │          │   Layer      │                                     │
│         │          └──────────────┘                                     │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────┐                                                       │
│  │  PostgreSQL  │                                                       │
│  │  (Sessions)  │                                                       │
│  └──────────────┘                                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## LangGraph Workflow

### Current Graph Structure

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│                    CLASSIFIER NODE                       │
│  • Analyzes user message intent                          │
│  • Returns: intent, confidence                           │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│                  ROUTE BY INTENT                         │
│  ┌─────────────────┬─────────────────┬────────────────┐ │
│  │  intent=command │  intent=question│  intent=chat   │ │
│  └────────┬────────┴────────┬────────┴───────┬────────┘ │
└───────────┼─────────────────┼────────────────┼──────────┘
            │                 │                │
            ▼                 ▼                ▼
   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
   │ COMMAND_GEN    │ │   RESPONDER    │ │   RESPONDER    │
   │ NODE           │ │                │ │                │
   │ • LLM gen      │ │ • LLM response │ │ • LLM response │
   │ • Safety check │ │                │ │                │
   └───────┬────────┘ └───────┬────────┘ └───────┬────────┘
           │                  │                  │
           └──────────────────┴──────────────────┘
                              │
                              ▼
                     ┌────────────────┐
                     │   RESPONDER    │
                     │   (Final)      │
                     └───────┬────────┘
                             │
                             ▼
                     ┌─────────────┐
                     │    END      │
                     └─────────────┘
```

### Future: Multi-Step Workflow with HITL

```
                    START
                      │
                      ▼
              ┌───────────────┐
              │ SMART_ROUTER  │ ◄── Dynamic integration loading
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │   PLANNER     │ ◄── LLM creates structured plan
              └───────┬───────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │       ROUTE_EXECUTOR        │
        │  requires_human_approval?   │
        └─────────────┬───────────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
      [auto]    [approval]    [blocked]
         │            │            │
         ▼            ▼            │
    ┌─────────┐ ┌─────────────┐    │
    │EXECUTOR │ │AWAIT_APPROVE│    │
    └────┬────┘ └──────┬──────┘    │
         │       ┌─────┴─────┐     │
         │       ▼           ▼     │
         │   [approved]  [rejected]│
         │       │           │     │
         └───────┴───────────┴─────┘
                      │
                      ▼
              ┌───────────────┐
              │ STEP_COMPLETE │
              │ more steps?   │
              └───────┬───────┘
                      │
              ┌───────┴───────┐
              ▼               ▼
          [continue]       [END]
              │
              └──────► (loop back to PLANNER)
```

---

## Component Structure

```
src/
├── main.py                    # FastAPI app entry point
├── config.py                  # Pydantic Settings (env vars)
│
├── agent/                     # LangGraph Agent Core
│   ├── graph.py              # StateGraph definition
│   ├── state.py              # AgentState TypedDict
│   └── nodes/                # Workflow nodes
│       ├── classifier.py     # Intent classification
│       ├── command_gen.py    # Command generation
│       └── responder.py      # Response formatting
│
├── tools/                     # LangChain Tools
│   ├── shell.py              # Shell execution tool
│   └── base.py               # Base tool class
│
├── bridge/                    # NestJS Bridge Client
│   ├── client.py             # HTTP client
│   └── schemas.py            # Request/Response models
│
├── llm/                       # Multi-LLM Support
│   └── factory.py            # Provider factory
│
├── api/                       # FastAPI Routes
│   ├── router.py             # Main router
│   └── v1/
│       ├── agent.py          # /agent/invoke
│       └── health.py         # /health
│
└── utils/                     # Utilities
    ├── safety.py             # Command safety verification
    └── errors.py             # Custom exceptions
```

---

## State Schema

`AgentState` is the **single source of truth**:

```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph import add_messages

class AgentState(TypedDict):
    # Core conversation (append-only)
    messages: Annotated[list[dict], add_messages]

    # Session context
    session_id: str
    user_id: str | None

    # Classification
    intent: Literal["command", "question", "chat"] | None
    confidence: float | None

    # Planning (future)
    plan: list[dict[str, str]] | None
    current_step: int

    # Execution
    command: str | None
    tool_results: list[dict]

    # HITL (future)
    requires_approval: bool
    approval_prompt: str | None
    approved: bool | None

    # Response
    response: str | None

    # Error handling
    errors: list[str]

    # Metadata
    tokens_used: int
    current_node: str
```

---

## Safety Layer

All shell commands go through `src/utils/safety.py`:

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMMAND SAFETY FLOW                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Empty command?  │──── YES ───► REJECT
                    └────────┬────────┘
                             │ NO
                             ▼
                    ┌─────────────────┐
                    │ Dangerous ops?  │──── YES ───► REJECT
                    │ (&|;< >`$)      │
                    └────────┬────────┘
                             │ NO
                             ▼
                    ┌─────────────────┐
                    │ In whitelist?   │──── YES ───► SAFE
                    │ (ls, pwd, git)  │
                    └────────┬────────┘
                             │ NO
                             ▼
                    ┌─────────────────┐
                    │   LLM Verify    │
                    │ (temp=0)        │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
           [safe]     [confirm]       [dangerous]
              │              │              │
              ▼              ▼              ▼
           EXECUTE    ASK USER        REJECT
```

**Whitelisted Commands**:
- `ls`, `pwd`, `whoami`, `date`
- `git status`, `git log`, `git branch`
- `cat` (no redirections), `head`, `tail`

**Always Rejected**:
- Commands with `&`, `;`, `|`, `>`, `<`, `` ` ``, `$`
- `rm -rf /`, `sudo`, `chmod 777`
- Fork bombs, curl-to-bash patterns

---

## Multi-LLM Provider

```python
from src.llm.factory import llm_factory

# Use default provider (from DEFAULT_LLM_PROVIDER env)
llm = llm_factory(temperature=0)

# Specify provider
llm = llm_factory(
    provider="anthropic",
    model_name="claude-3-opus-20240229",
    temperature=0.7
)

# Streaming
llm = llm_factory(streaming=True)
async for chunk in llm.astream(prompt):
    yield chunk.content
```

| Provider | Default Model | Env Key |
|----------|--------------|---------|
| `openai` | gpt-4-turbo-preview | `OPENAI_API_KEY` |
| `anthropic` | claude-3-opus-20240229 | `ANTHROPIC_API_KEY` |
| `gemini` | gemini-pro | `GOOGLE_API_KEY` |

---

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
DEFAULT_LLM_PROVIDER=openai|anthropic|gemini
BRIDGE_URL=http://localhost:3000
DATABASE_URL=postgresql://user:pass@localhost:5432/orbit

# Optional
BRIDGE_API_KEY=           # Auth for Bridge
PORT=8000                  # API port
DEBUG=true                 # Debug mode
LOG_LEVEL=INFO            # Logging level
```

---

## Testing

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_safety.py       # Safety module
│   ├── test_classifier.py   # Classifier node
│   └── test_llm_factory.py  # LLM factory
├── integration/
│   ├── test_api.py          # API endpoints
│   ├── test_bridge.py       # Bridge client
│   └── test_graph.py        # Full graph
└── e2e/
    └── test_agent_flow.py   # End-to-end
```

```bash
# Run all tests with coverage
pytest --cov=src --cov-fail-under=80

# Run specific markers
pytest -m "not integration"  # Unit tests only
pytest -m "slow"             # Slow tests only

# Single test with verbose
pytest tests/unit/test_safety.py::test_safety_levels -v
```

---

## Code Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files | snake_case | `command_generator.py` |
| Classes | PascalCase | `AgentState` |
| Functions | snake_case | `generate_plan()` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRIES` |
| Private | _underscore | `_internal()` |

**Immutability**: ALWAYS create new objects, never mutate state.

```python
# BAD
state["plan"] = new_plan

# GOOD
new_state = {**state, "plan": new_plan}
```

---

## Future Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Basic classification, command gen, shell tool | Current |
| 2 | Memory system, session persistence | Planned |
| 3 | Multi-step workflows, planning | Planned |
| 4 | External integrations (Jira, Git, VS Code) | Planned |
| 5 | RAG with vector database | Planned |
| 6 | Advanced HITL, approval flows | Planned |
| 7 | Observability, monitoring | Planned |
| 8 | Performance optimization | Planned |

---

## Related Documentation

- `.claude/agents/` - Specialized agent definitions
- `.claude/rules/` - Coding standards and patterns
- `.claude/skills/` - Project-specific skills
- `.claude/hooks/` - Automated checks
- `docs/IMPLEMENTATION_ROADMAP.md` - Detailed roadmap
- `docs/ORBIT_AI_PYTHON_BLUEPRINT.md` - Full blueprint
