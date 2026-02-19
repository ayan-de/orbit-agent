# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Orbit AI Agent is a Python microservice that implements an intelligent agent capable of understanding natural language and executing shell commands through a safety-first architecture. The project is currently in **Phase 1** of implementation (9/93 steps completed).

The agent uses LangGraph for workflow orchestration, FastAPI for REST APIs, and communicates with a separate NestJS Bridge service for actual shell command execution on user machines.

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

# Run with coverage
pytest --cov=src tests/
```

## Architecture

### High-Level Flow

1. User sends message → NestJS Bridge → Python Agent (FastAPI)
2. LangGraph agent processes intent through node workflow
3. Tools (shell, etc.) execute via NestJS Bridge
4. Results returned through Bridge → User

### Component Structure

**`src/main.py`**: FastAPI application entry point with CORS middleware and health endpoints

**`src/agent/`**: LangGraph agent core
- `graph.py`: StateGraph workflow definition with nodes (`classifier`, `command_generator`, `responder`)
- `state.py`: TypedDict-based state schema (`AgentState`) - includes messages, intent, command, plan, tool_results, session metadata
- `nodes/`: Individual workflow nodes - each is a function that receives and returns `AgentState`
  - `classifier.py`: Determines if user wants command execution or simple response
  - `command_generator.py`: Translates natural language to shell commands using LLM
  - `responder.py`: Formats final responses

**`src/tools/`**: LangChain tool implementations
- `shell.py`: Shell execution tool via NestJS Bridge, with integrated safety verification
- `base.py`: Base tool class (planned)

**`src/bridge/`**: NestJS Bridge integration
- `client.py`: HTTP client for communicating with Bridge service (`execute_command`, `list_files`, `read_file`)
- `schemas.py`: Pydantic models for Bridge requests/responses

**`src/llm/`**: Multi-LLM provider support via factory pattern
- `factory.py`: `llm_factory(provider, model_name, temperature)` - creates LangChain ChatOpenAI/ChatAnthropic/ChatGoogle instances
- Providers: `openai` (GPT-4 Turbo), `anthropic` (Claude 3 Opus), `gemini` (Flash)
- Default provider configured via `DEFAULT_LLM_PROVIDER` env var

**`src/utils/safety.py`**: Two-tier safety verification
1. **Whitelist**: Simple commands (`ls`, `pwd`, `git status`, etc.) bypass LLM check
2. **LLM Verification**: Complex commands analyzed by LLM with `temperature=0` for deterministic safety decisions
- Rejects commands containing dangerous operators: `&`, `;`, `|`, `>`, `<`, `` ` ``, `$`

**`src/api/`**: FastAPI routes
- `router.py`: Main API router aggregating v1 endpoints
- `v1/agent.py`: `POST /agent/invoke` endpoint - invokes LangGraph agent
- `v1/health.py`: Health check endpoints

**`src/config.py`**: Pydantic Settings - all environment variables (PORT, DEBUG, API keys, DATABASE_URL, BRIDGE_URL, etc.)

### LangGraph Workflow Pattern

The agent follows a stateful graph pattern:

```
START → classifier (classify intent)
         ↓
    [conditional edges based on intent]
    ↓                    ↓
command_generator   responder
    ↓                    ↓
    └────────→ responder → END
```

- State is passed between nodes as a dictionary conforming to `AgentState`
- Conditional routing uses `add_conditional_edges` with routing functions
- Messages use LangChain's `add_messages` reducer for append-only semantics

### Safety-First Design

All shell commands go through `src/utils/safety.py::is_safe_command()` before execution:
1. Reject empty commands
2. Check whitelist for safe prefixes (no dangerous operators)
3. LLM analysis for everything else
4. Return `(is_safe: bool, reason: str)` tuple

### Async-First Architecture

- FastAPI endpoints are async
- LLM calls use `.ainvoke()` methods
- Bridge client uses `httpx.AsyncClient`
- Tool execution uses `_arun()` async methods

### Bridge Architecture Pattern

The Python API is separated from desktop execution concerns:
- Python handles LLM, planning, orchestration
- NestJS Bridge handles actual shell execution on user's machine
- Communication via HTTP with Bearer token authentication

### Configuration Pattern

All settings defined in `src/config.py` as Pydantic `BaseSettings`:
- Reads from `.env` file automatically
- Type-hinted fields with defaults
- `extra="ignore"` for forward compatibility

### State Machine Design

`AgentState` in `src/agent/state.py` is the single source of truth for agent execution:
- `messages`: Append-only conversation history with LangChain `add_messages` reducer
- `intent`: Literal type for type-safe intent values
- `plan`/`current_step`: For multi-step workflow support (planned)
- `needs_confirmation`/`confirmation_prompt`: For user confirmation flows (planned)
- `session_id`/`user_id`: For conversation persistence (planned)

### Multi-LLM Provider Pattern

Use `src/llm/factory.py::llm_factory()` to create LLM instances:
```python
from src.llm.factory import llm_factory

# Use default provider from config
llm = llm_factory(temperature=0)

# Specify provider
llm = llm_factory(provider="openai", model_name="gpt-4-turbo-preview", temperature=0.7)
```

## Environment Variables

Required variables (set in `.env`):
- `OPENAI_API_KEY`: For OpenAI provider
- `ANTHROPIC_API_KEY`: For Anthropic provider
- `GOOGLE_API_KEY`: For Gemini provider
- `DEFAULT_LLM_PROVIDER`: One of `openai`, `anthropic`, `gemini`
- `BRIDGE_URL`: URL of NestJS Bridge service
- `BRIDGE_API_KEY`: Authentication for Bridge (optional)
- `DATABASE_URL`: PostgreSQL connection string

Optional:
- `PORT`: API server port (default 8000)
- `DEBUG`: Enable debug mode (default True)

## Testing

Test structure is planned but not yet implemented:
```
tests/
├── unit/          # Unit tests for individual components
├── integration/   # Integration tests for multi-component flows
└── e2e/          # End-to-end tests
```

Tests use pytest framework with async support.

## Future Expansion (Planned)

The codebase is designed for expansion across 8 phases:
- Phase 1: Basic intent classification, command generation, shell tool (current)
- Phase 2: Memory system, session persistence
- Phase 3: Multi-step workflows, planning
- Phase 4: External tool integrations (Jira, Git, VS Code, etc.)
- Phase 5: RAG with vector database
- Phase 6: Advanced workflows, approval flows
- Phase 7: Observability, monitoring, logging
- Phase 8: Performance optimization, caching

See `docs/IMPLEMENTATION_ROADMAP.md` and `docs/ORBIT_AI_PYTHON_BLUEPRINT.md` for detailed plans.
