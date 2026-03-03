# Memory Management - File-Based Primary Storage

## Overview

This document outlines the complete memory management strategy for Orbit Agent, prioritizing file-based storage with minimal PostgreSQL usage for production deployment.

**Goal:** File-based memory as primary storage, PostgreSQL for authentication and lightweight metadata only.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MEMORY ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  FILE-BASED MEMORY (Primary Storage)                                 │
│  ~/.orbit/memory/                                                        │
│  ├── identity/           - User profiles, preferences, tokens             │
│  ├── procedural/         - Workflows, learned patterns                  │
│  ├── episodic/          - Session logs, conversations, archives         │
│  └── users/             - User-specific indexes and metadata            │
│                                                                     │
│  POSTGRESQL (Lightweight Metadata Only)                                  │
│  - users              - Authentication and user data                       │
│  - session_metadata   - Active session tracking (messages NOT stored)       │
│  - rate_limits       - API rate limiting data                               │
│  - api_keys          - Third-party API key management                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File-Based Memory Structure

### Directory Layout

```
~/.orbit/memory/
├── identity/
│   ├── user_profile.md           # User preferences, personal info
│   ├── user_tokens.json         # Encrypted OAuth tokens (Gmail, Jira, etc.)
│   └── user_settings.json       # Agent configuration per user
│
├── procedural/
│   ├── workflows.md             # Learned workflows and patterns
│   ├── commands.md             # Frequently used shell commands
│   └── snippets.md            # Code snippets and templates
│
├── episodic/
│   ├── sessions/               # Active conversation logs
│   │   ├── {session_id}.md               # Full conversation
│   │   └── {session_id}.summary.json     # Compact summary
│   ├── archive/                 # Compressed/archived old sessions
│   │   ├── {session_id}.md
│   │   └── {session_id}.summary.json
│   ├── checkpoints/              # LangGraph state checkpoints for pause/resume
│   │   └── {thread_id}_{checkpoint_id}.json
│   └── compaction_log.md       # Memory compaction history
│
└── users/
    ├── {user_id}/
    │   ├── session_index.json    # List of user's sessions
    │   ├── preferences.json       # Cached user preferences
    │   └── stats.json           # Usage statistics
    └── global_index.json         # All sessions index (for search)
```

---

## File Specifications

### 1. Identity Files

#### `identity/user_profile.md`

**Purpose:** User preferences, personal information, and agent configuration

**Created:** When user first interacts with agent or explicitly sets preferences

**Updated:** On preference changes

**Format:**
```markdown
# User Profile

**Last Updated:** 2026-03-03T10:30:00Z

---

### Personal Information

**Name:** John Doe
**Email:** john@example.com
**Timezone:** America/New_York

---

### Preferences

**Programming Language:** Python
**Editor:** VS Code
**Code Style:** PEP 8
**Shell:** zsh

---

### Agent Configuration

**Response Style:** concise
**Auto-Confirm Commands:** false
**Tool Safety Level:** 2
**Max Context Tokens:** 100000

---

### Communication Style

**Formality:** casual
**Use Emojis:** true
**Include Examples:** true

---

### Custom Prompts

**System Prompt Override:** You are a coding assistant...
**Response Template:** ...
```

**Usage in code:**
- `reader.read_user_profile()` - Parse and return as dict
- `writer.update_user_profile()` - Update specific sections
- Used by: `memory_loader_node` to inject into LLM context

---

#### `identity/user_tokens.json`

**Purpose:** Encrypted OAuth tokens for third-party integrations

**Created:** When user connects external service (Gmail, Jira, etc.)

**Updated:** On token refresh

**Security:** Encrypted using AES-256 with key from environment

**Format:**
```json
{
  "encryption_version": 1,
  "created_at": "2026-03-01T10:00:00Z",
  "updated_at": "2026-03-03T14:25:00Z",
  "tokens": {
    "gmail": {
      "email_address": "user@gmail.com",
      "access_token": "encrypted_access_token",
      "refresh_token": "encrypted_refresh_token",
      "token_expires_at": "2026-03-03T15:25:00Z",
      "scope": "https://www.googleapis.com/auth/gmail.send",
      "created_at": "2026-03-01T10:00:00Z"
    },
    "jira": {
      "base_url": "https://company.atlassian.net",
      "username": "user@company.com",
      "api_token": "encrypted_api_token",
      "created_at": "2026-02-20T10:00:00Z"
    }
  }
}
```

**Usage in code:**
- `token_store.get_tokens(user_id)` - Retrieve decrypted tokens
- `token_store.store_tokens()` - Store encrypted tokens
- Used by: Gmail tool, Jira tool

---

#### `identity/user_settings.json`

**Purpose:** User-specific agent configuration (not preferences)

**Created:** On user registration

**Updated:** On settings changes

**Format:**
```json
{
  "user_id": "user_123",
  "created_at": "2026-03-01T10:00:00Z",
  "updated_at": "2026-03-03T10:30:00Z",
  "settings": {
    "memory_compaction_enabled": true,
    "auto_compaction_threshold": 0.8,
    "max_sessions_to_keep": 50,
    "session_retention_days": 90,
    "log_level": "info",
    "debug_mode": false
  }
}
```

---

### 2. Procedural Files

#### `procedural/workflows.md`

**Purpose:** Learned workflows, multi-step patterns, reusable procedures

**Created:** When LLM detects a reusable pattern during conversation

**Updated:** On new pattern discovery or explicit workflow saving

**Format:**
```markdown
# Stored Workflows

**Last Updated:** 2026-03-03T14:20:00Z

---

## Workflow: Setup New Python Project

**Description:** Create a new Python project with standard structure, requirements.txt, and README

**Created:** 2026-02-15T10:30:00Z
**Usage Count:** 12
**Last Used:** 2026-03-03T10:15:00Z

### Steps

1. Create project directory with `mkdir project_name && cd project_name`
2. Initialize Python virtual environment with `python -m venv venv`
3. Create main.py with basic application structure
4. Create requirements.txt with common dependencies
5. Create README.md with project description
6. Create .gitignore for Python projects
7. Initialize git repository with `git init`

### Example Invocation

User: "Create a new Python project called myapp"
Agent: Creates structure with: myapp/main.py, myapp/requirements.txt, myapp/README.md

---

## Workflow: Dockerize Application

**Description:** Add Docker support to an existing application

**Created:** 2026-02-20T14:00:00Z
**Usage Count:** 8
**Last Used:** 2026-03-02T16:45:00Z

### Steps

1. Create Dockerfile with appropriate base image
2. Add .dockerignore file
3. Create docker-compose.yml for multi-container setups
4. Add healthcheck to Dockerfile
5. Document docker commands in README

---

## Pattern: Git Commit Standard Format

**Description:** Standardized commit message format

**Created:** 2026-02-10T09:00:00Z

### Template

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- test: Test additions/changes
- chore: Build process or auxiliary tool changes
```
```

**Usage in code:**
- `reader.read_workflows()` - Parse all workflows
- `reader.get_workflow(name)` - Get specific workflow
- `reader.search_workflows(query)` - Search by keywords
- `writer.save_workflow()` - Add new workflow
- Used by: `memory_loader_node` for LLM context

---

#### `procedural/commands.md`

**Purpose:** Frequently used shell commands organized by category

**Created:** When user executes a command multiple times or explicitly saves

**Updated:** On command usage or edits

**Format:**
```markdown
# Frequent Commands

**Last Updated:** 2026-03-03T11:00:00Z

---

## Development

### Python

**Install Dependencies:**
```bash
pip install -r requirements.txt
```

**Run Tests:**
```bash
pytest tests/ -v --cov=src
```

**Format Code:**
```bash
black src/ tests/
```

### Git

**Push with upstream:**
```bash
git push -u origin feature-branch
```

**Interactive Rebase:**
```bash
git rebase -i main
```

---

## Deployment

### Docker

**Build Image:**
```bash
docker build -t myapp:latest .
```

**Run Container:**
```bash
docker run -p 8000:8000 myapp:latest
```

### System

**Check Running Services:**
```bash
systemctl status --all
```

**Restart Service:**
```bash
sudo systemctl restart my-service
```
```

**Usage in code:**
- `reader.get_commands(category)` - Get commands by category
- Used by: Suggested commands feature in future

---

#### `procedural/snippets.md`

**Purpose:** Code snippets, templates, and reusable code blocks

**Created:** When LLM generates useful patterns or user explicitly saves

**Updated:** On new snippets

**Format:**
```markdown
# Code Snippets

**Last Updated:** 2026-03-03T12:00:00Z

---

## Snippet: FastAPI Route with Authentication

**Language:** Python
**Category:** Web Framework
**Tags:** fastapi, authentication, endpoint

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

router = APIRouter()

async def get_current_user(token: str):
    # Validate token and return user
    pass

@router.get("/protected-endpoint")
async def protected_route(
    user: dict = Depends(get_current_user)
):
    return {"message": f"Hello {user['username']}"}
```

**Usage:** Copy and paste for new authenticated endpoints

---

## Snippet: PostgreSQL Connection with Retry

**Language:** Python
**Category:** Database

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

async def get_db_with_retry(
    max_retries: int = 3,
    retry_delay: float = 1.0
):
    for attempt in range(max_retries):
        try:
            engine = create_async_engine(DATABASE_URL)
            return engine
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(retry_delay)
```
```

**Usage in code:**
- `reader.get_snippets(language, tags)` - Get relevant snippets
- `writer.save_snippet()` - Store new snippet
- Used by: Code generation nodes

---

### 3. Episodic Files

#### `episodic/sessions/{session_id}.md`

**Purpose:** Complete conversation log for a session

**Created:** When new session starts (first message)

**Updated:** On every message (appended)

**Format:**
```markdown
# Session: {session_id}

**Started:** 2026-03-03T10:00:00Z
**User ID:** user_123
**Status:** active
**Message Count:** 15

---

### user - 2026-03-03T10:00:00Z

Hello, can you help me set up a new project?

---

### assistant - 2026-03-03T10:00:15Z

Of course! What kind of project would you like to create?

---

### user - 2026-03-03T10:00:30Z

I'd like a FastAPI project with PostgreSQL and Docker support.

---

### assistant - 2026-03-03T10:01:00Z

I'll help you set that up. Let me create the project structure.

[Tool Execution: shell_exec]
Command: mkdir -p fastapi-project/{src,tests}
Output: Directory created successfully

---

### user - 2026-03-03T10:02:00Z

Great, can you also add a requirements.txt?

---

### assistant - 2026-03-03T10:02:15Z

Sure! Here's a requirements.txt for a FastAPI project:

[Content: requirements.txt]
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
...

---

### tool - 2026-03-03T10:03:00Z

File created: fastapi-project/requirements.txt

---

### user - 2026-03-03T10:03:30Z

Perfect, thanks!

---

### assistant - 2026-03-03T10:03:45Z

You're welcome! Your FastAPI project is ready. Would you like me to add any specific features or configurations?

---

### system - 2026-03-03T10:05:00Z

[COMPRESSED] Previous 10 messages replaced with summary:
User requested help setting up a FastAPI project with PostgreSQL and Docker. Assistant created project structure, added requirements.txt with FastAPI, Uvicorn, SQLAlchemy, and Psycopg2 dependencies. Project ready at fastapi-project/ directory.
```

**Usage in code:**
- `writer.append_to_session()` - Add new message
- `reader.read_session()` - Load session content
- Used by: Session resumption, search, compaction

---

#### `episodic/sessions/{session_id}.summary.json`

**Purpose:** Compact summary for quick session loading

**Created:** After session exceeds threshold or on compaction

**Updated:** On compaction or significant changes

**Format:**
```json
{
  "session_id": "sess_abc123",
  "user_id": "user_123",
  "title": "FastAPI Project Setup",
  "status": "active",
  "created_at": "2026-03-03T10:00:00Z",
  "updated_at": "2026-03-03T10:05:00Z",
  "message_count": 15,
  "compressed_count": 10,
  "metadata": {
    "intents_detected": ["command", "question"],
    "tools_used": ["shell_exec"],
    "total_duration_ms": 345000
  },
  "summary": {
    "user_goal": "Set up a new FastAPI project with PostgreSQL and Docker",
    "outcome": "Project structure created with requirements.txt, ready for development",
    "key_topics": ["FastAPI", "PostgreSQL", "Docker", "project setup"],
    "facts_learned": [
      "User prefers FastAPI framework",
      "User needs Docker support",
      "User wants PostgreSQL database"
    ]
  }
}
```

**Usage in code:**
- Fast lookup without parsing full markdown
- Used by: Session list API, search

---

#### `episodic/checkpoints/{thread_id}_{checkpoint_id}.json`

**Purpose:** LangGraph state checkpoint for pause/resume functionality

**Created:** On each significant agent state change

**Updated:** On checkpoint creation

**Format:**
```json
{
  "checkpoint_id": "ckpt_abc123",
  "thread_id": "thread_xyz789",
  "session_id": "sess_abc123",
  "created_at": "2026-03-03T10:05:00Z",
  "parent_checkpoint_id": null,
  "node": "responder",
  "state": {
    "messages": [
      {
        "role": "user",
        "content": "Hello, can you help me?"
      },
      {
        "role": "assistant",
        "content": "Of course! What would you like help with?"
      }
    ],
    "intent": "question",
    "plan": {},
    "current_step": 0,
    "tool_results": [],
    "is_complete": false,
    "session_id": "sess_abc123",
    "user_id": "user_123"
  }
}
```

**Usage in code:**
- `checkpointer.save_checkpoint()` - Store checkpoint
- `checkpointer.load_checkpoint()` - Restore from checkpoint
- Used by: LangGraph pause/resume

---

#### `episodic/compaction_log.md`

**Purpose:** History of memory compaction operations

**Created:** On first compaction

**Updated:** On each compaction

**Format:**
```markdown
# Memory Compaction Log

---

## Compaction #1

**Timestamp:** 2026-03-03T14:00:00Z
**Trigger:** Manual
**Reason:** Memory size exceeded 80% threshold

### Before
- Total characters: 256,000
- Estimated tokens: 64,000
- Session count: 25
- Workflow count: 8

### Actions Performed
- **Facts Extracted:** 15 facts from recent sessions
- **Workflows Created:** 2 new workflows
- **Sessions Archived:** 10 old sessions moved to archive
- **Sessions Compressed:** 5 sessions summarized

### Results
- Total characters: 128,000
- Estimated tokens: 32,000
- Reduction: 50%
- Duration: 2.5 seconds

### Details
- Extracted user preference for FastAPI framework
- Created "FastAPI Project Setup" workflow
- Archived sessions older than 30 days

---

## Compaction #2

**Timestamp:** 2026-03-05T10:00:00Z
**Trigger:** Auto
**Reason:** Scheduled weekly compaction

...
```

**Usage in code:**
- Audit trail of memory operations
- Used by: Debugging, monitoring

---

### 4. User Files

#### `users/{user_id}/session_index.json`

**Purpose:** Fast lookup of user's sessions without scanning all files

**Created:** When user first creates a session

**Updated:** On session creation, archive, deletion

**Format:**
```json
{
  "user_id": "user_123",
  "last_updated": "2026-03-03T10:30:00Z",
  "sessions": {
    "active": [
      {
        "session_id": "sess_abc123",
        "title": "FastAPI Project Setup",
        "created_at": "2026-03-03T10:00:00Z",
        "updated_at": "2026-03-03T10:05:00Z",
        "message_count": 15,
        "status": "active"
      },
      {
        "session_id": "sess_def456",
        "title": "Debug Code Issue",
        "created_at": "2026-03-02T14:00:00Z",
        "updated_at": "2026-03-03T09:00:00Z",
        "message_count": 8,
        "status": "active"
      }
    ],
    "archived": [
      {
        "session_id": "sess_ghi789",
        "title": "Old Project Help",
        "created_at": "2026-02-01T10:00:00Z",
        "archived_at": "2026-03-01T00:00:00Z",
        "reason": "age_based",
        "message_count": 25
      }
    ]
  },
  "stats": {
    "total_sessions": 15,
    "active_sessions": 2,
    "archived_sessions": 13,
    "total_messages": 345
  }
}
```

**Usage in code:**
- Fast session listing without file system scan
- Used by: `GET /sessions` API endpoint

---

#### `users/{user_id}/preferences.json`

**Purpose:** Cached user preferences for quick access

**Created:** On user first interaction

**Updated:** On preference changes

**Format:**
```json
{
  "user_id": "user_123",
  "last_updated": "2026-03-03T10:30:00Z",
  "preferences": {
    "programming_language": "Python",
    "editor": "VS Code",
    "shell": "zsh",
    "timezone": "America/New_York",
    "response_style": "concise",
    "formality": "casual",
    "include_examples": true,
    "auto_confirm_commands": false,
    "tool_safety_level": 2,
    "max_context_tokens": 100000
  }
}
```

**Usage in code:**
- Quick access to user preferences
- Used by: `memory_loader_node`, all LLM prompts

---

#### `users/{user_id}/stats.json`

**Purpose:** Usage statistics and analytics

**Created:** On user first interaction

**Updated:** Periodically or on session completion

**Format:**
```json
{
  "user_id": "user_123",
  "first_seen": "2026-02-01T10:00:00Z",
  "last_active": "2026-03-03T10:30:00Z",
  "stats": {
    "total_sessions": 45,
    "total_messages": 856,
    "total_tool_calls": 234,
    "total_workflow_runs": 67,
    "most_used_intents": {
      "command": 156,
      "question": 89,
      "workflow": 45,
      "email": 12
    },
    "most_used_tools": {
      "shell_exec": 123,
      "file_ops": 45,
      "web_search": 34,
      "gmail_send": 12
    },
    "average_session_duration_ms": 245000,
    "total_agent_time_ms": 11025000
  }
}
```

**Usage in code:**
- Analytics and usage insights
- Used by: Optional dashboard/monitoring

---

#### `users/global_index.json`

**Purpose:** Global index of all sessions for search across users (admin/debugging)

**Created:** When first session is created

**Updated:** On session creation, deletion

**Format:**
```json
{
  "last_updated": "2026-03-03T10:30:00Z",
  "total_sessions": 1234,
  "total_users": 45,
  "sessions": [
    {
      "session_id": "sess_abc123",
      "user_id": "user_123",
      "title": "FastAPI Project Setup",
      "created_at": "2026-03-03T10:00:00Z",
      "status": "active"
    }
  ]
}
```

**Usage in code:**
- Cross-user search, admin functions
- Used by: Admin API (optional)

---

## PostgreSQL Usage (Minimal)

### Schema

#### Table: `users`

**Purpose:** User authentication and core metadata

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP WITH TIME ZONE,

    INDEX idx_users_email (email),
    INDEX idx_users_username (username)
);
```

**Usage:**
- User registration/login
- User metadata (NOT preferences - those are in files)
- Authentication tokens

---

#### Table: `session_metadata`

**Purpose:** Lightweight session tracking (no messages stored here)

```sql
CREATE TABLE session_metadata (
    session_id VARCHAR(100) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    status VARCHAR(50) NOT NULL, -- active, archived, deleted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE,

    INDEX idx_sessions_user (user_id),
    INDEX idx_sessions_status (status),
    INDEX idx_sessions_updated (updated_at DESC)
);
```

**Usage:**
- Fast session listing (complements file-based index)
- Session status tracking
- Cross-user session queries

---

#### Table: `rate_limits`

**Purpose:** API rate limiting and quotas

```sql
CREATE TABLE rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL, -- api, email, etc.
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    request_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE (user_id, resource_type, window_start),
    INDEX idx_ratelimits_user (user_id, window_start)
);
```

**Usage:**
- Rate limiting enforcement
- Prevent abuse

---

#### Table: `api_keys`

**Purpose:** Third-party API key management (encrypted)

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service VARCHAR(50) NOT NULL, -- openai, anthropic, tavily
    encrypted_key TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,

    INDEX idx_apikeys_user (user_id),
    INDEX idx_apikeys_service (service)
);
```

**Usage:**
- Store user's API keys for LLM providers
- Manage third-party integrations

---

### Removed Tables (Previously Used)

| Table | Why Removed | Alternative |
|--------|-------------|--------------|
| `agent_messages` | Messages now in files | `episodic/sessions/{id}.md` |
| `agent_tool_calls` | Tool tracking in session files | Session metadata |
| `agent_states` | Checkpoints now in files | `episodic/checkpoints/{id}.json` |
| `agent_embeddings` | Future RAG will use files | File-based vector store |
| `agent_workflow_executions` | Workflow tracking in files | Session logs |

---

## Implementation Phases

### Phase 1: File-Based Memory Foundation

**Status:** ✅ Partially Implemented
**Duration:** 2-3 days

#### Tasks

1.1 **Enhance Memory Injection into Prompts**

**What:** Add `memory_context` to all LLM prompts

**Files to modify:**
- `src/agent/prompts/classifier.py`
- `src/agent/prompts/planner.py`
- `src/agent/prompts/responder.py`

**Changes:**
```python
# Add memory_context variable to prompts
CLASSIFIER_SYSTEM_PROMPT = """... Memory Context: {memory_context} ..."""
PLANNER_SYSTEM_PROMPT = """... Memory Context: {memory_context} ..."""
RESPONDER_SYSTEM_PROMPT = """... Memory Context: {memory_context} ..."""

# Update node invocations to pass memory_context
async def classify_intent(state: AgentState):
    memory_context = state.get("memory_context", "")
    return {"intent": intent}

async def respond(state: AgentState):
    memory_context = state.get("memory_context", "")
    response = await chain.ainvoke({
        "messages": messages,
        "intent": intent,
        "tool_results": str(tool_results),
        "memory_context": memory_context  # NEW
    })
```

---

1.2 **Create Session Writer Node**

**What:** New LangGraph node to write conversations to files

**New file:** `src/agent/nodes/session_writer.py`

**Functionality:**
```python
async def session_writer_node(state: AgentState):
    """
    Write conversation to file-based memory after agent completes.
    """
    session_id = state["session_id"]
    user_id = state["user_id"]
    messages = state["messages"]

    # Update session file
    for msg in messages:
        writer.append_to_session(
            session_id=session_id,
            content=msg.content,
            role=msg.type,
            add_timestamp=True
        )

    # Update user index
    session_index = update_session_index(user_id, session_id)

    return {
        "session_written": True,
        "session_index_updated": True
    }
```

**Integration in graph:**
```python
# graph.py
workflow.add_node("session_writer", session_writer_node)
workflow.add_edge("responder", "session_writer")
workflow.add_edge("session_writer", END)
```

---

1.3 **Implement File-Based Checkpointer**

**What:** Replace PostgreSQL checkpointer with file-based

**New file:** `src/memory/file_checkpointer.py`

**Functionality:**
```python
class FileCheckpointer:
    """File-based checkpoint storage for LangGraph pause/resume."""

    async def save_checkpoint(
        thread_id: str,
        checkpoint_id: str,
        state: dict
    ):
        # Save to episodic/checkpoints/{thread_id}_{checkpoint_id}.json
        pass

    async def load_checkpoint(
        thread_id: str,
        checkpoint_id: str
    ) -> dict:
        # Load from episodic/checkpoints/{thread_id}_{checkpoint_id}.json
        pass

    async def list_checkpoints(
        thread_id: str
    ) -> list:
        # List all checkpoints for a thread
        pass
```

---

1.4 **Create User Session Index**

**What:** Fast session lookup without file system scan

**New file:** `src/memory/session_index.py`

**Functionality:**
```python
async def update_session_index(
    user_id: str,
    session_id: str,
    title: str = None,
    status: str = "active"
):
    """
    Update user's session index file.
    """
    index_file = USERS_DIR / user_id / "session_index.json"
    # Load, update, save
    pass

async def get_user_sessions(
    user_id: str,
    status: str = None
) -> list:
    """
    Get sessions from index.
    """
    pass
```

---

#### Acceptance Criteria

- [ ] `memory_context` is used in classifier, planner, responder prompts
- [ ] New conversations are written to `{session_id}.md`
- [ ] Checkpoints saved to `episodic/checkpoints/`
- [ ] Session index created and updated
- [ ] All existing unit tests pass

---

### Phase 2: PostgreSQL Simplification

**Status:** 🔄 Not Started
**Duration:** 2-3 days

#### Tasks

2.1 **Create Minimal PostgreSQL Schema**

**What:** New simplified schema for authentication only

**New migration:** `migrations/002_minimal_schema.sql`

```sql
-- Keep only necessary tables
DROP TABLE IF EXISTS agent_messages CASCADE;
DROP TABLE IF EXISTS agent_tool_calls CASCADE;
DROP TABLE IF EXISTS agent_states CASCADE;
DROP TABLE IF EXISTS agent_workflow_executions CASCADE;

-- Keep users table (auth)
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;

-- Create session_metadata table (lightweight)
CREATE TABLE IF NOT EXISTS session_metadata (...);

-- Create rate_limits table
CREATE TABLE IF NOT EXISTS rate_limits (...);

-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (...);
```

---

2.2 **Refactor Session API**

**What:** Update `src/api/v1/sessions.py` to use file-based storage

**Changes:**
```python
# Remove PostgreSQL message storage
# OLD:
# await memory.add_message(...)

# NEW:
from src.memory.writer import append_to_session
from src.memory.session_index import update_session_index

async def add_message(session_id: str, role: str, content: str):
    await append_to_session(session_id, content, role)
    # Only update PostgreSQL metadata table
    await session_repo.update_metadata(session_id, {
        "last_message_at": datetime.now()
    })
```

---

2.3 **Update Agent Streaming**

**What:** Change `src/api/v1/agent.py` to use file-based storage

**Changes:**
```python
# agent.py:274-292
# OLD:
# memory = await get_conversation_memory()
# await memory.add_message(...)

# NEW:
from src.memory.writer import append_to_session
from src.memory.session_index import update_session_index

# Save to file, not PostgreSQL
await append_to_session(session_id, message, "user")
await append_to_session(session_id, assistant_response, "assistant")
```

---

2.4 **Simplify or Remove ConversationMemory**

**What:** Reduce `src/memory/conversation.py` to minimal functionality

**Options:**
- Option A: Keep only user/session metadata methods
- Option B: Remove entirely, use file-based directly

**Recommended:** Option A - Keep for backward compatibility with minimal methods

---

#### Acceptance Criteria

- [ ] PostgreSQL schema migrated to minimal
- [ ] Session API uses file-based storage
- [ ] Agent streaming saves to files
- [ ] ConversationMemory simplified or removed
- [ ] All API tests pass

---

### Phase 3: Advanced File-Based Features

**Status:** ⏸ Not Started
**Duration:** 3-4 days

#### Tasks

3.1 **Implement Session Search**

**What:** Add search across all session files

**New file:** `src/memory/search.py`

**Functionality:**
```python
async def search_sessions(
    user_id: str,
    query: str,
    limit: int = 10
) -> list:
    """
    Search session files for query.
    Uses file system scan with content matching.
    """
    pass

async def semantic_search_sessions(
    user_id: str,
    query: str,
    limit: int = 10
) -> list:
    """
    Semantic search using embeddings (future Phase 5).
    """
    pass
```

---

3.2 **Implement Session Summarization**

**What:** LLM-based session compression for file-based storage

**Changes to:** `src/memory/compaction.py`

**Enhancements:**
```python
async def compress_session_file(
    session_id: str,
    keep_messages: int = 20
):
    """
    Compress session file by replacing old messages with summary.

    Updates:
    - {session_id}.md - Adds [COMPRESSED] marker
    - {session_id}.summary.json - Updates summary
    """
    pass
```

---

3.3 **Implement Memory Compaction**

**What:** Automatic memory cleanup when size exceeds threshold

**Already implemented:** `src/memory/compaction.py`

**Integration needed:**
```python
# Add to session_writer_node
async def session_writer_node(state: AgentState):
    # ... write session ...

    # Check compaction after write
    if check_compaction_needed():
        await auto_compaction()

    return state
```

---

3.4 **Add User Preferences Cache**

**What:** Fast access to user preferences from `preferences.json`

**New file:** `src/memory/preferences.py`

**Functionality:**
```python
async def get_user_preferences(user_id: str) -> dict:
    """
    Get user preferences from cache file.
    """
    pass

async def update_preference(
    user_id: str,
    key: str,
    value: any
):
    """
    Update single preference in cache.
    """
    pass
```

---

#### Acceptance Criteria

- [ ] Session search working
- [ ] Session compression working
- [ ] Auto-compaction triggered after threshold
- [ ] Preferences cache functional
- [ ] Integration tests pass

---

### Phase 4: API and Integration

**Status:** ⏸ Not Started
**Duration:** 2-3 days

#### Tasks

4.1 **Update All API Endpoints**

**Files:** All files in `src/api/v1/`

**Changes:**
- Ensure file-based storage used
- Update response models
- Add error handling for file operations

---

4.2 **Add Memory Management Endpoints**

**New file:** `src/api/v1/memory.py`

**Endpoints:**
```python
@router.get("/profile")
async def get_user_profile(user_id: str):
    """Get user profile from file."""
    pass

@router.put("/profile")
async def update_user_profile(user_id: str, updates: dict):
    """Update user profile."""
    pass

@router.get("/workflows")
async def get_workflows(user_id: str):
    """Get user's workflows."""
    pass

@router.post("/workflows")
async def save_workflow(user_id: str, workflow: dict):
    """Save new workflow."""
    pass

@router.post("/compact")
async def trigger_compaction(user_id: str):
    """Trigger manual memory compaction."""
    pass
```

---

4.3 **WebSocket Streaming Updates**

**File:** `src/api/v1/agent.py`

**Enhancements:**
- Stream memory context loading status
- Stream compaction progress
- Add checkpoint resumption

---

#### Acceptance Criteria

- [ ] All endpoints use file-based storage
- [ ] Memory management API working
- [ ] WebSocket streaming enhanced
- [ ] API integration tests pass

---

### Phase 5: Future Enhancements

**Status:** ⏸ Not Started
**Duration:** Ongoing

#### Tasks

5.1 **File-Based Vector Store**

**What:** Implement RAG using file-based embeddings

**Approach:**
- Use `sentence-transformers` for embeddings
- Store embeddings in JSON files
- Implement ANN search using faiss or similar

---

5.2 **Distributed File Storage**

**What:** Support for S3/Cloud storage for multi-instance deployment

**Approach:**
- Abstract file operations
- S3 backend option
- Cache layer for performance

---

5.3 **Memory Visualization**

**What:** Web UI to browse memory, search, manage

**Approach:**
- Read-only view of memory files
- Search interface
- Session viewer

---

## What's Already Implemented

### ✅ Fully Implemented

| Component | File | Status |
|-----------|------|--------|
| File directory structure | `src/memory/structure.py` | ✅ Complete |
| User profile read/write | `src/reader.py`, `writer.py` | ✅ Complete |
| Workflow read/write | `src/reader.py`, `writer.py` | ✅ Complete |
| Session logging | `src/writer.py` | ✅ Complete |
| Session reading | `src/reader.py` | ✅ Complete |
| Memory compaction | `src/memory/compaction.py` | ✅ Complete |
| Token storage (file-based) | `src/storage/token_store.py` | ✅ Complete |

### 🔄 Partially Implemented

| Component | File | Gap |
|-----------|------|-----|
| Memory context loading | `src/agent/nodes/memory_loader.py` | Loads context but NOT used in prompts |
| User session index | - | Not implemented, needs creation |
| File-based checkpointer | - | Not implemented, uses PostgreSQL |
| Memory search | `src/memory/reader.py` | Has `search_sessions()` but needs enhancement |

### ❌ Not Implemented

| Component | File | Phase |
|-----------|------|-------|
| Memory context in prompts | - | Phase 1.1 |
| Session writer node | - | Phase 1.2 |
| File-based checkpointer | - | Phase 1.3 |
| User session index | - | Phase 1.4 |
| Minimal PostgreSQL schema | - | Phase 2.1 |
| Session API refactoring | `src/api/v1/sessions.py` | Phase 2.2 |
| Agent streaming update | `src/api/v1/agent.py` | Phase 2.3 |
| Session search | - | Phase 3.1 |
| Session compression | - | Phase 3.2 |
| Preferences cache | - | Phase 3.4 |
| Memory management API | - | Phase 4.2 |

---

## Data Flow Diagrams

### Current Flow (Before Refactoring)

```
User Message
    ↓
POST /agent/invoke
    ↓
[Classifier] → [Planner] → [Executor] → [Responder]
    ↓
[Save to PostgreSQL]  ← agent.py:274-292
    ↓
[NOT saved to files]
    ↓
Response
```

### Target Flow (After Refactoring)

```
User Message
    ↓
POST /agent/invoke
    ↓
[Memory Loader] → Reads: profile, workflows, recent sessions
    ↓
[Classifier (with memory_context)] → [Planner (with memory_context)]
    → [Executor] → [Responder (with memory_context)]
    ↓
[Session Writer] → Writes: {session_id}.md
    ↓
[Update Session Index] → users/{user_id}/session_index.json
    ↓
[Check Compaction] → If needed, run auto_compaction()
    ↓
[Update PostgreSQL Metadata] → Only: session_metadata table
    ↓
Response
```

---

## File Creation/Update Triggers

### Identity Files

| File | Created | Updated | Trigger |
|------|---------|---------|----------|
| `user_profile.md` | First interaction | Preference change | `writer.update_user_profile()` |
| `user_tokens.json` | First OAuth connection | Token refresh | `token_store.store_tokens()` |
| `user_settings.json` | Registration | Settings change | New endpoint |

### Procedural Files

| File | Created | Updated | Trigger |
|------|---------|---------|----------|
| `workflows.md` | First workflow | New pattern detected | `writer.save_workflow()` |
| `commands.md` | First command usage | New frequent command | LLM pattern detection |
| `snippets.md` | First snippet | New snippet | LLM generation or explicit save |

### Episodic Files

| File | Created | Updated | Trigger |
|------|---------|---------|----------|
| `{session_id}.md` | First message | Every message | `writer.append_to_session()` |
| `{session_id}.summary.json` | Session > 20 msgs | Compression | `compaction.py` |
| `{thread_id}_{ckpt_id}.json` | State change | Checkpoint | `file_checkpointer.py` |
| `compaction_log.md` | First compaction | Every compaction | `auto_compaction()` |

### User Files

| File | Created | Updated | Trigger |
|------|---------|---------|----------|
| `session_index.json` | First session | Every session | `update_session_index()` |
| `preferences.json` | First interaction | Preference change | `preferences.py` |
| `stats.json` | First interaction | Periodically | Background task |

---

## Migration Strategy

### From PostgreSQL to File-Based

1. **Backup existing PostgreSQL data**
   ```bash
   pg_dump orbit_db > backup_$(date +%Y%m%d).sql
   ```

2. **Export messages to files**
   - Script to read from `agent_messages` table
   - Write to `episodic/sessions/{session_id}.md`
   - Create `{session_id}.summary.json`

3. **Export workflows**
   - If any workflows stored in PostgreSQL, export to `procedural/workflows.md`

4. **Update schema** (Phase 2.1)
   - Drop old tables
   - Create minimal tables

5. **Switch application**
   - Deploy new code
   - Verify file-based operations

6. **Monitor and rollback if needed**

---

## Performance Considerations

### File-Based Memory Optimizations

| Concern | Solution |
|----------|-----------|
| **File I/O Performance** | - Lazy loading of session files<br>- Keep index files in memory<br>- Use async file operations |
| **Directory Scan Performance** | - Session index for fast lookups<br>- Limit directory scans to user's sessions |
| **Memory Usage** | - Stream large files<br>- Implement LRU cache for frequently accessed files |
| **Concurrent Access** | - File locking mechanism<br>- SQLite for concurrent index updates |

### When to Cache

- **In-memory cache:**
  - User preferences (frequently accessed)
  - Session index (load on startup, refresh periodically)
  - Workflows (frequently used patterns)

- **No cache (read from file):**
  - Full session logs (large, infrequent)
  - Archived sessions (rarely accessed)
  - Compaction logs (rarely accessed)

---

## Security Considerations

### File Permissions

```bash
# Memory directory structure
~/.orbit/
├── memory/              # drwx------ (700) - Owner only
│   ├── identity/        # drwx------ (700)
│   ├── procedural/      # drwx------ (700)
│   ├── episodic/       # drwx------ (700)
│   └── users/          # drwx------ (700)
│       └── {user_id}/   # drwx------ (700)
```

### Token Encryption

- All tokens encrypted at rest using AES-256
- Encryption key from environment variable
- Never log decrypted tokens

### Sensitive Data in Files

- Avoid storing:
  - API keys in plain text
  - Passwords
  - PII without encryption

- Store encrypted:
  - OAuth tokens
  - API keys (if necessary)

---

## Monitoring and Observability

### Metrics to Track

| Metric | Source | Purpose |
|--------|---------|----------|
| File I/O latency | Application logging | Detect performance issues |
| Memory size | `get_memory_usage_stats()` | Trigger compaction |
| Session file count | Session index | Track growth |
| Compaction frequency | Compaction log | Optimize thresholds |
| Cache hit rate | Application | Tune caching strategy |

### Logging

```python
# File-based operations should log:
logger.info(f"Session written: {session_id}, size: {size} bytes")
logger.warning(f"Compaction triggered: {reason}")
logger.error(f"Failed to write session: {error}")

# PostgreSQL operations:
logger.info(f"User authenticated: {user_id}")
logger.info(f"Session metadata updated: {session_id}")
```

---

## Testing Strategy

### Unit Tests

```python
# tests/memory/test_writer.py
def test_append_to_session():
    session_id = "test_session"
    await writer.append_to_session(session_id, "test", "user")
    assert (SESSIONS_DIR / f"{session_id}.md").exists()

def test_update_user_profile():
    await writer.update_user_profile({"language": "Python"})
    profile = reader.read_user_profile()
    assert profile["language"] == "Python"
```

### Integration Tests

```python
# tests/integration/test_memory_flow.py
async def test_full_conversation_flow():
    # 1. User sends message
    response = await client.post("/agent/invoke", {...})

    # 2. Check file created
    assert (SESSIONS_DIR / "session_id.md").exists()

    # 3. Check index updated
    index = await get_session_index(user_id)
    assert "session_id" in index["sessions"]["active"]

    # 4. Check compaction
    if response["compaction_needed"]:
        assert len(os.listdir(ARCHIVE_DIR)) > 0
```

### Performance Tests

```python
# tests/performance/test_file_operations.py
async def test_concurrent_session_writes():
    # 100 concurrent writes
    tasks = [writer.append_to_session(...) for _ in range(100)]
    await asyncio.gather(*tasks)
    # Verify no corruption
```

---

## Rollback Plan

### If Issues Arise

1. **Immediate rollback:**
   - Deploy previous PostgreSQL-heavy version
   - File-based memory as backup reference

2. **Data recovery:**
   - PostgreSQL backup still available
   - File-based files remain intact

3. **Switch strategy:**
   - Hybird approach for transition
   - Gradual migration of data

---

## Summary

### Key Changes

1. **Primary Storage:** File-based (`~/.orbit/memory/`)
2. **PostgreSQL:** Authentication and metadata only
3. **Memory Injection:** All LLM prompts receive `memory_context`
4. **Session Management:** File logs + JSON index
5. **Checkpointing:** File-based JSON
6. **Compaction:** LLM-powered, automatic

### Benefits

- ✅ Simpler deployment (no heavy PostgreSQL)
- ✅ Easier debugging (human-readable files)
- ✅ Better scaling (file storage cheap)
- ✅ Portability (migrate memory by copying files)
- ✅ Offline capability (files work without DB)

### Risks

- ⚠️ File I/O performance vs PostgreSQL
- ⚠️ Concurrent access handling
- ⚠️ Directory management at scale
- ⚠️ Backup/restore complexity

---

## Next Steps

1. Review this document with team
2. Prioritize phases based on timeline
3. Start Phase 1 (Foundation)
4. Create implementation tasks in project tracker
5. Set timeline and milestones
6. Begin implementation
