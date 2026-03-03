# Phase 2: PostgreSQL Simplification

**Scope**: Minimize PostgreSQL usage to authentication and metadata only
**Target**: Remove message storage, checkpoints from PostgreSQL; use only for auth
**Duration**: 2-3 days
**Last Updated**: 2026-03-03

---

## Overview

This phase focuses on simplifying PostgreSQL by removing heavy storage operations:
- Remove message storage (now in file-based sessions)
- Remove checkpoint storage (now in file-based)
- Remove tool call tracking (now in session logs)
- Keep only essential: users, session_metadata, rate_limits, api_keys

**Key Change**: PostgreSQL becomes lightweight metadata layer only.

---

## Phase 2: PostgreSQL Simplification (Days 4-6)

**Goal**: Create minimal PostgreSQL schema and refactor APIs to use file-based storage.

### Day 4: Minimal PostgreSQL Schema

| Step | Task | File(s) | Status |
|------|------|----------|--------|
| 4.1 | Create minimal schema migration | `migrations/002_minimal_schema.sql` | ⬜ |
| 4.2 | Add password_hash to users table | `migrations/002_minimal_schema.sql` | ⬜ |
| 4.3 | Create session_metadata table | `migrations/002_minimal_schema.sql` | ⬜ |
| 4.4 | Create rate_limits table | `migrations/002_minimal_schema.sql` | ⬜ |
| 4.5 | Create api_keys table | `migrations/002_minimal_schema.sql` | ⬜ |
| 4.6 | Drop heavy tables (CASCADE) | `migrations/002_minimal_schema.sql` | ⬜ |
| 4.7 | Run migration | `migrations/` | ⬜ |
| 4.8 | Update models.py | `src/db/models.py` | ⬜ |

**Details:**

**Task 4.1-4.7: Create migration**

Create new migration file that:
- Drops heavy tables: agent_messages, agent_tool_calls, agent_states, agent_workflow_executions, agent_workflow_steps, agent_embeddings
- Updates users table with password_hash, is_active, last_login_at fields
- Creates session_metadata table for lightweight session tracking
- Creates rate_limits table for API rate limiting
- Creates api_keys table for third-party API key management
- Uses proper indexes for fast queries
- Wraps in transaction for atomic execution

**Task 4.8: Update models.py**

- Comment out or remove heavy model classes
- Keep minimal models: User, SessionMetadata, RateLimit, APIKey
- Update relationships to match new schema
- Ensure proper field types and constraints

---

### Day 5: Session API Refactoring

| Step | Task | File(s) | Status |
|------|------|----------|--------|
| 5.1 | Update create_session to write to files | `src/api/v1/sessions.py` | ⬜ |
| 5.2 | Update get_session to read from files | `src/api/v1/sessions.py` | ⬜ |
| 5.3 | Update list_sessions to use session_index | `src/api/v1/sessions.py` | ⬜ |
| 5.4 | Update get_session_messages to read files | `src/api/v1/sessions.py` | ⬜ |
| 5.5 | Update add_message to write to files | `src/api/v1/sessions.py` | ⬜ |
| 5.6 | Remove PostgreSQL message operations | `src/api/v1/sessions.py` | ⬜ |
| 5.7 | Update SessionRepository | `src/db/repositories/session_repo.py` | ⬜ |
| 5.8 | Remove MessageRepository | `src/db/repositories/message_repo.py` | ⬜ |

**Details:**

**Task 5.1-5.8: Refactor sessions.py**

Update all endpoints to use file-based storage:
- create_session: Create file + update PostgreSQL metadata only
- get_session: Read from file + get metadata from PostgreSQL
- list_sessions: Use session_index.json for fast lookups
- get_session_messages: Parse markdown file for messages
- add_message: Append to markdown file
- Remove all ConversationMemory usage
- Update SessionRepository for metadata operations only
- Mark MessageRepository as deprecated or remove

---

### Day 6: Agent Streaming Update

| Step | Task | File(s) | Status |
|------|------|----------|--------|
| 6.1 | Update agent.py to write to files | `src/api/v1/agent.py` | ⬜ |
| 6.2 | Remove ConversationMemory usage | `src/api/v1/agent.py` | ⬜ |
| 6.3 | Add session creation to invoke endpoint | `src/api/v1/agent.py` | ⬜ |
| 6.4 | Add message writing to streaming endpoint | `src/api/v1/agent.py` | ⬜ |
| 6.5 | Simplify or remove ConversationMemory | `src/memory/conversation.py` | ⬜ |

**Details:**

**Task 6.1-6.4: Update agent.py**

Update WebSocket and invoke endpoints:
- Remove get_conversation_memory() usage
- Add create_new_session() call for new sessions
- Use append_to_session() for all message writes
- Write user and assistant messages to files
- Update session_index.json with message counts
- Only update PostgreSQL metadata (message_count, last_message_at)

**Task 6.5: Simplify ConversationMemory**

- Keep only minimal metadata methods if needed
- Or mark entire module as DEPRECATED with docstring
- Add comment pointing to file-based modules

---

## Success Criteria

### Phase 2 is Complete When:

**Minimal PostgreSQL Schema:**
☐ Migration 002_minimal_schema.sql created
☐ agent_messages table dropped
☐ agent_tool_calls table dropped
☐ agent_states table dropped
☐ agent_workflow_executions table dropped
☐ agent_embeddings table dropped
☐ Session metadata table created
☐ Rate limits table created
☐ API keys table created
☐ Migration run successfully
☐ models.py updated to minimal schema

**Session API Refactoring:**
☐ create_session uses file-based storage
☐ get_session reads from files
☐ list_sessions uses session_index
☐ get_session_messages reads from files
☐ add_message writes to files
☐ PostgreSQL message operations removed
☐ SessionRepository updated for metadata only
☐ MessageRepository marked as deprecated

**Agent Streaming Update:**
☐ agent.py writes to file-based storage
☐ ConversationMemory usage removed from streaming
☐ Session creation in invoke endpoint
☐ Message writing in streaming endpoint
☐ ConversationMemory simplified or marked deprecated

**Testing:**
☐ Migration runs without errors
☐ Session API tests pass
☐ Agent streaming tests pass
☐ File-based storage verified
☐ PostgreSQL only stores metadata

---

## 📊 Total Progress

```
Phase 2: PostgreSQL Simplification  ░░░░░░   0/21 steps
Day 4: Minimal Schema             ░░░░░░   0/8 steps
Day 5: Session API Refactoring     ░░░░░░   0/8 steps
Day 6: Agent Streaming Update      ░░░░░░   0/5 steps
────────────────────────────────────────────
Total                              ░░░░░░   0/21 steps
```

---

## Next Steps After Phase 2

1. ✅ Review Phase 1 completion
2. ⏭️ Backup existing PostgreSQL data
3. ⏭️ Start with Day 4: Minimal Schema
4. ⏭️ Implement Day 5: Session API Refactoring
5. ⏭️ Implement Day 6: Agent Streaming Update
6. ⏭️ Test full flow end-to-end
7. ⏭️ Move to Phase 3: Advanced Features

---

**Ready to simplify PostgreSQL? Let's proceed!** 🗄️
