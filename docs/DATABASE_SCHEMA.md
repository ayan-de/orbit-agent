# Database Schema Documentation

This document describes the database schema for Orbit AI Agent.

## Overview

The database schema is designed to support:
- **Phase 2**: Conversation sessions, messages, tool execution tracking
- **Phase 4**: RAG with vector embeddings
- **Phase 5**: Autonomous workflow execution

All tables use PostgreSQL UUIDs as primary keys and include proper foreign key relationships with cascade deletes where appropriate.

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Sessions                                   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ id (UUID, PK)                                                   │ │
│  │ user_id (VARCHAR)                                               │ │
│  │ title (TEXT)                                                    │ │
│  │ status (ENUM: active, archived, deleted)                       │ │
│  │ metadata (JSONB)                                                │ │
│  │ created_at, updated_at                                         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
         │
         ├──1:N────────────────────────────────────────────────────┐
         │                                                          │
         ↓                                                          ↓
┌────────────────────┐                                    ┌────────────────────┐
│    Messages        │                                    │   Tool Calls       │
│  ┌──────────────┐  │                                    │  ┌──────────────┐  │
│  │ id (PK)      │  │                                    │  │ id (PK)      │  │
│  │ session_id   │──┤                                    │  │ session_id   │──┤
│  │ role (ENUM)  │  │                                    │  │ tool_name    │  │
│  │ content      │  │                                    │  │ status       │  │
│  │ metadata     │  │                                    │  │ inputs       │  │
│  │ created_at   │  │                                    │  │ outputs      │  │
│  └──────────────┘  │                                    │  │ error_message│  │
└────────────────────┘                                    │  └──────────────┘  │
         │                                                └────────────────────┘
         │
         ├──1:N─────────────────────┐
         │                           │
         ↓                           ↓
┌────────────────────┐    ┌────────────────────┐
│   Agent States    │    │   Embeddings       │
│  ┌──────────────┐  │    │  ┌──────────────┐  │
│  │ id (PK)      │  │    │  │ id (PK)      │  │
│  │ session_id   │──┤    │  │ session_id   │──┤
│  │ thread_id    │  │    │  │ entity_type  │  │
│  │ state (JSONB)│  │    │  │ entity_id    │  │
│  │ created_at   │  │    │  │ content      │  │
│  └──────────────┘  │    │  │ embedding    │  │ ← pgvector
└────────────────────┘    │  │ created_at   │  │
                          │  └──────────────┘  │
                          └────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ↓                         ↓                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     Workflow Executions                               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ id (PK)                                                       │ │
│  │ session_id                                                     │ │
│  │ workflow_name                                                  │ │
│  │ status (ENUM)                                                  │ │
│  │ input_data, output_data (JSONB)                               │ │
│  │ current_step, total_steps                                     │ │
│  │ started_at, completed_at                                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
         │
         └──1:N────────────────────────────────────────────────────┐
                                                                │
                                                                ↓
                                                    ┌────────────────────┐
                                                    │  Workflow Steps    │
                                                    │  ┌──────────────┐  │
                                                    │  │ id (PK)      │  │
                                                    │  │ execution_id │──┤
                                                    │  │ step_name    │  │
                                                    │  │ step_order   │  │
                                                    │  │ status       │  │
                                                    │  │ input/output │  │
                                                    │  └──────────────┘  │
                                                    └────────────────────┘
```

---

## Table Definitions

### Sessions

Stores top-level conversation sessions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `user_id` | VARCHAR(255) | NOT NULL, INDEXED | User identifier |
| `title` | TEXT | NULLABLE | Optional session title |
| `status` | ENUM | NOT NULL, DEFAULT 'active' | Session status |
| `metadata` | JSONB | DEFAULT `{}` | Additional session data |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | AUTO UPDATE | Last update timestamp |

**Indexes**: `idx_sessions_user_id`, `idx_sessions_status`

**Relationships**:
- One-to-many with `messages`, `tool_calls`, `agent_states`, `embeddings`, `workflow_executions`

---

### Messages

Stores individual messages in a conversation.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `session_id` | UUID | FK → sessions, NOT NULL, INDEXED | Parent session |
| `role` | ENUM | NOT NULL | Message role (user/assistant/system/tool) |
| `content` | TEXT | NOT NULL | Message content |
| `metadata` | JSONB | DEFAULT `{}` | Additional message data |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW(), INDEXED | Creation timestamp |

**Indexes**: `idx_messages_session_id`, `idx_messages_created_at`, `idx_messages_session_created`

**Relationships**:
- Many-to-one with `sessions`
- One-to-many with `tool_calls`

---

### Tool Calls

Tracks tool execution and results.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `message_id` | UUID | FK → messages, NULLABLE | Related message |
| `session_id` | UUID | FK → sessions, NOT NULL, INDEXED | Parent session |
| `tool_name` | VARCHAR(100) | NOT NULL | Name of the tool |
| `inputs` | JSONB | NOT NULL | Tool input parameters |
| `outputs` | JSONB | NULLABLE | Tool output results |
| `error_message` | TEXT | NULLABLE | Error message if failed |
| `status` | ENUM | NOT NULL, INDEXED | Execution status |
| `execution_time_ms` | INTEGER | NULLABLE | Execution duration |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | AUTO UPDATE | Last update timestamp |

**Indexes**: `idx_tool_calls_session_id`, `idx_tool_calls_status`

**Relationships**:
- Many-to-one with `sessions`
- Many-to-one with `messages`

---

### Agent States

Stores agent state for pause/resume functionality (LangGraph checkpointing).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `session_id` | UUID | FK → sessions, NOT NULL, INDEXED | Parent session |
| `thread_id` | VARCHAR(255) | NOT NULL, UNIQUE, INDEXED | Thread identifier |
| `state` | JSONB | NOT NULL | Complete agent state |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |

**Indexes**: `idx_agent_states_session_id`, `ix_agent_states_thread_id` (unique)

**Relationships**:
- Many-to-one with `sessions`

---

### Embeddings

Stores text embeddings for semantic search (RAG).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `session_id` | UUID | FK → sessions, NULLABLE, INDEXED | Parent session |
| `entity_type` | VARCHAR(50) | NOT NULL | Type of entity (message/file/etc) |
| `entity_id` | VARCHAR(255) | NULLABLE | Entity identifier |
| `content` | TEXT | NOT NULL | Original text content |
| `metadata` | JSONB | DEFAULT `{}` | Additional embedding data |
| `embedding` | vector(1536) | NULLABLE | Vector embedding (pgvector) |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |

**Indexes**:
- `idx_embeddings_session_id`
- `idx_embeddings_entity` (composite: entity_type, entity_id)
- `idx_embeddings_hnsw` (HNSW index on embedding column)
- `idx_embeddings_metadata` (GIN index on metadata)

**Note**: The `embedding` column and HNSW index are added in migration `002_add_pgvector` (Phase 4).

---

### Workflow Executions

Tracks autonomous workflow execution.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `session_id` | UUID | FK → sessions, NOT NULL, INDEXED | Parent session |
| `workflow_name` | VARCHAR(100) | NOT NULL | Name of the workflow |
| `status` | ENUM | NOT NULL, DEFAULT 'pending', INDEXED | Execution status |
| `input_data` | JSONB | NOT NULL | Workflow input |
| `output_data` | JSONB | NULLABLE | Workflow output |
| `current_step` | INTEGER | DEFAULT 0 | Current step number |
| `total_steps` | INTEGER | NULLABLE | Total number of steps |
| `error_message` | TEXT | NULLABLE | Error message if failed |
| `started_at` | TIMESTAMPTZ | DEFAULT NOW(), INDEXED | Start timestamp |
| `completed_at` | TIMESTAMPTZ | NULLABLE | Completion timestamp |
| `metadata` | JSONB | DEFAULT `{}` | Additional workflow data |

**Indexes**: `idx_workflow_executions_session_id`, `idx_workflow_executions_status`, `idx_workflow_executions_started_at`

**Relationships**:
- Many-to-one with `sessions`
- One-to-many with `workflow_steps`

---

### Workflow Steps

Represents individual steps in a workflow execution.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Unique identifier |
| `workflow_execution_id` | UUID | FK → workflow_executions, NOT NULL | Parent workflow |
| `step_name` | VARCHAR(100) | NOT NULL | Name of the step |
| `step_order` | INTEGER | NOT NULL | Step execution order |
| `status` | ENUM | NOT NULL, DEFAULT 'pending' | Step status |
| `input_data` | JSONB | NULLABLE | Step input |
| `output_data` | JSONB | NULLABLE | Step output |
| `error_message` | TEXT | NULLABLE | Error message if failed |
| `execution_time_ms` | INTEGER | NULLABLE | Execution duration |
| `started_at` | TIMESTAMPTZ | NULLABLE | Start timestamp |
| `completed_at` | TIMESTAMPTZ | NULLABLE | Completion timestamp |

**Indexes**: `idx_workflow_steps_execution_order` (composite: workflow_execution_id, step_order)

**Relationships**:
- Many-to-one with `workflow_executions`

---

## Enum Types

| Enum Name | Values |
|-----------|--------|
| `sessionstatus` | `active`, `archived`, `deleted` |
| `messagerole` | `user`, `assistant`, `system`, `tool` |
| `toolcallstatus` | `pending`, `running`, `completed`, `failed` |
| `workflowstatus` | `pending`, `running`, `completed`, `failed`, `cancelled` |
| `workflowstepstatus` | `pending`, `running`, `completed`, `failed`, `skipped` |

---

## Migration History

| Migration ID | Description | Phase |
|-------------|-------------|-------|
| `001_initial_schema` | Initial schema with all tables and relationships | Phase 2 |
| `002_add_pgvector` | Add pgvector extension and vector column for RAG | Phase 4 |

---

## Running Migrations

```bash
# Create a new migration
alembic revision -m "description of changes"

# Run all pending migrations
make migrate
# or
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```

---

## Common Query Patterns

### Get all messages for a session with tool calls

```sql
SELECT
    m.*,
    tc.tool_name,
    tc.status as tool_status
FROM messages m
LEFT JOIN tool_calls tc ON m.id = tc.message_id
WHERE m.session_id = $1
ORDER BY m.created_at ASC;
```

### Get recent tool calls with execution time

```sql
SELECT
    tc.*,
    s.user_id
FROM tool_calls tc
JOIN sessions s ON tc.session_id = s.id
WHERE tc.created_at > NOW() - INTERVAL '24 hours'
ORDER BY tc.created_at DESC
LIMIT 100;
```

### Vector similarity search (Phase 4+)

```sql
-- Find similar embeddings with metadata filtering
SELECT
    e.id,
    e.entity_type,
    e.entity_id,
    e.content,
    1 - (e.embedding <=> $1) as similarity
FROM embeddings e
WHERE
    e.embedding <=> $1 < 0.3  -- Cosine distance threshold
    AND e.session_id = $2
    AND e.created_at > NOW() - INTERVAL '7 days'
ORDER BY e.embedding <=> $1
LIMIT 10;
```

### Get workflow execution status with steps

```sql
SELECT
    we.*,
    COUNT(ws.id) as total_steps,
    COUNT(ws.id) FILTER (WHERE ws.status = 'completed') as completed_steps
FROM workflow_executions we
LEFT JOIN workflow_steps ws ON we.id = ws.workflow_execution_id
WHERE we.session_id = $1
GROUP BY we.id
ORDER BY we.started_at DESC;
```

---

## Performance Considerations

### Indexes
- All foreign keys are indexed
- Timestamp columns used for filtering are indexed
- Vector column has HNSW index for fast similarity search
- JSONB columns have GIN indexes where appropriate

### Cascade Behavior
- Deleting a `session` cascades to all related messages, tool calls, agent states, and workflow executions
- Deleting a `message` sets `tool_calls.message_id` to NULL (SET NULL)
- Deleting `embeddings` does not cascade (session_id is nullable)

### Connection Pooling
Use PgBouncer in production for efficient connection pooling:

```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
```
