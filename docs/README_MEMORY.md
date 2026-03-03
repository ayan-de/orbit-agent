# Memory Management Implementation - Master Index

**Project**: Orbit Agent Memory Refactoring
**Goal**: File-based memory as primary storage with minimal PostgreSQL
**Total Duration**: 8-10 days (Phases 1-4) + Ongoing (Phase 5)
**Last Updated**: 2026-03-03

---

## Quick Links

| Phase | Document | Duration | Status |
|-------|----------|----------|--------|
| Phase 1 | [PHASE1_MEMORY_FOUNDATION.md](./PHASE1_MEMORY_FOUNDATION.md) | 2-3 days | 🔄 Not Started |
| Phase 2 | [PHASE2_POSTGRESQL_SIMPLIFICATION.md](./PHASE2_POSTGRESQL_SIMPLIFICATION.md) | 2-3 days | 🔄 Not Started |
| Phase 3 | [PHASE3_ADVANCED_FEATURES.md](./PHASE3_ADVANCED_FEATURES.md) | 3-4 days | 🔄 Not Started |
| Phase 4 | [PHASE4_API_INTEGRATION.md](./PHASE4_API_INTEGRATION.md) | 2-3 days | 🔄 Not Started |
| Phase 5 | [PHASE5_FUTURE_ENHANCEMENTS.md](./PHASE5_FUTURE_ENHANCEMENTS.md) | Ongoing | 🔄 Not Started |
| Reference | [MEMORY_MANAGEMENT.md](./MEMORY_MANAGEMENT.md) | - | ✅ Created |

---

## Architecture Overview

### Before Refactoring (Current State)

```
┌─────────────────────────────────────────────────────────────────┐
│                  CURRENT MEMORY ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HEAVY POSTGRESQL                                          │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  agent_messages (stores all messages)             │      │
│  │  agent_tool_calls (tracks tool usage)           │      │
│  │  agent_states (checkpoints for pause/resume)     │      │
│  │  agent_workflow_executions                      │      │
│  └──────────────────────────────────────────────────────────┘      │
│                            ▲                                       │
│                            │                                       │
│  FILE-BASED (Read-Only)                                  │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  identity/user_profile.md (read only)            │      │
│  │  procedural/workflows.md (read only)          │      │
│  │  episodic/sessions/{id}.md (read only)      │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                 │
│  PROBLEM: memory_context loaded but NEVER used!            │
│         - PostgreSQL is primary storage                          │
│         - File system secondary/ignored                         │
│         - Duplicate data in two places                        │
└─────────────────────────────────────────────────────────────────┘
```

### After Refactoring (Target State)

```
┌─────────────────────────────────────────────────────────────────┐
│                  NEW MEMORY ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MINIMAL POSTGRESQL                                        │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  users (authentication only)                       │      │
│  │  session_metadata (lightweight metadata)        │      │
│  │  rate_limits (API rate limiting)                │      │
│  │  api_keys (encrypted third-party keys)         │      │
│  └──────────────────────────────────────────────────────────┘      │
│                            ▲                                       │
│                            │                                       │
│  FILE-BASED (Primary Storage)                             │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  identity/                                            │      │
│  │    ├── user_profile.md (read/write)       │      │
│  │    ├── user_tokens.json (encrypted)       │      │
│  │    └── user_settings.json                    │      │
│  │                                                      │      │
│  │  procedural/                                          │      │
│  │    ├── workflows.md (read/write)          │      │
│  │    ├── commands.md (read/write)            │      │
│  │    └── snippets.md (read/write)           │      │
│  │                                                      │      │
│  │  episodic/                                           │      │
│  │    ├── sessions/{id}.md (read/write)    │      │
│  │    ├── sessions/{id}.summary.json          │      │
│  │    ├── checkpoints/{id}.json             │      │
│  │    ├── archive/ (old sessions)           │      │
│  │    └── compaction_log.md                 │      │
│  │                                                      │      │
│  └── users/{user_id}/                                   │      │
│      ├── session_index.json (fast lookup)   │      │
│      ├── preferences.json (cached)        │      │
│      └── stats.json (analytics)             │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                 │
│  ✅ FIXED: memory_context used in all LLM prompts!   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase Summaries

### Phase 1: File-Based Foundation

**Focus**: Make file-based memory primary by fixing critical gap

**Key Deliverables:**
- Inject memory_context into classifier, planner, responder prompts
- Create session_writer node to persist conversations
- Implement file-based checkpointer for LangGraph
- Create user session index for fast lookups

**Critical Fix:**
- Currently memory_context is loaded but **never used** in any prompt
- This is the #1 issue preventing file-based memory from working

**Files Modified/Created:**
- `src/agent/prompts/classifier.py` - Add memory_context
- `src/agent/prompts/planner.py` - Add memory_context
- `src/agent/prompts/responder.py` - Add memory_context
- `src/agent/nodes/classifier.py` - Pass memory_context
- `src/agent/nodes/planner.py` - Pass memory_context
- `src/agent/nodes/responder.py` - Pass memory_context
- `src/agent/nodes/session_writer.py` - NEW
- `src/memory/session_index.py` - NEW
- `src/memory/file_checkpointer.py` - NEW

**Duration**: 2-3 days
**Steps**: 20

---

### Phase 2: PostgreSQL Simplification

**Focus**: Remove heavy storage from PostgreSQL, keep only auth/metadata

**Key Deliverables:**
- Create minimal schema migration
- Drop heavy tables (messages, tool_calls, states, workflows)
- Create session_metadata table (lightweight only)
- Create rate_limits table
- Create api_keys table
- Refactor session API to use file-based storage
- Update agent streaming to write to files
- Simplify ConversationMemory or mark deprecated

**Changes:**
| Table | Before | After |
|-------|--------|-------|
| `agent_messages` | Stores all messages | DROPPED |
| `agent_tool_calls` | Tracks tool usage | DROPPED |
| `agent_states` | Checkpoints | DROPPED |
| `agent_workflow_executions` | Workflow tracking | DROPPED |
| `session_metadata` | Doesn't exist | CREATED (metadata only) |
| `rate_limits` | Doesn't exist | CREATED |
| `api_keys` | Doesn't exist | CREATED |

**Files Modified/Created:**
- `migrations/002_minimal_schema.sql` - NEW
- `src/db/models.py` - Minimal models only
- `src/api/v1/sessions.py` - Use file-based storage
- `src/api/v1/agent.py` - Write to files
- `src/memory/conversation.py` - Simplify or deprecate

**Duration**: 2-3 days
**Steps**: 21

---

### Phase 3: Advanced Features

**Focus**: Add search, compression, and caching to file-based memory

**Key Deliverables:**
- Implement session search with keyword matching
- Add LLM-based session compression
- Implement automatic memory compaction
- Add preferences cache with in-memory layer
- Create memory management API endpoints

**New Features:**
- `search_sessions()` - Keyword search across sessions
- `semantic_search_sessions()` - Vector search (Phase 5)
- `compress_session_file()` - Replace old messages with summary
- `auto_compaction()` - Triggered when memory exceeds threshold
- `get_user_preferences()` - Cached preferences (5 min TTL)
- Memory API (`/api/v1/memory/*`) - Search, profile, workflows, compress

**Files Modified/Created:**
- `src/memory/search.py` - NEW
- `src/memory/compression.py` - NEW (enhance existing)
- `src/memory/preferences.py` - NEW
- `src/api/v1/memory.py` - NEW
- `tests/memory/test_search.py` - NEW
- `tests/memory/test_compression.py` - NEW
- `tests/memory/test_preferences.py` - NEW

**Duration**: 3-4 days
**Steps**: 26

---

### Phase 4: API Integration

**Focus**: Ensure all APIs use file-based memory correctly

**Key Deliverables:**
- Update all session endpoints to use file-based storage
- Add error handling classes
- Create memory management endpoints
- Enhance WebSocket streaming with memory context
- Test all API endpoints

**API Endpoints:**

**Sessions API** (`/api/v1/sessions`):
- `POST /sessions` - Create (writes to file)
- `GET /sessions/{id}` - Get (reads from file)
- `GET /sessions` - List (uses session_index)
- `PATCH /sessions/{id}` - Update (PostgreSQL metadata)
- `DELETE /sessions/{id}` - Delete (file + metadata)
- `GET /sessions/{id}/messages` - Get (reads from file)
- `POST /sessions/{id}/messages` - Add (writes to file)
- `POST /sessions/{id}/archive` - Archive (move file)

**Memory API** (`/api/v1/memory`):
- `GET /memory/profile` - Get user profile
- `PUT /memory/profile` - Update user profile
- `GET /memory/workflows` - Get workflows
- `POST /memory/workflows` - Save workflow
- `GET /memory/preferences` - Get preferences (cached)
- `PUT /memory/preferences` - Update preferences
- `POST /memory/compact` - Trigger compaction
- `POST /memory/search` - Search across memory

**WebSocket** (`/ws/api/v1/agent/stream`):
- Send memory loading events
- Stream compaction progress
- Add checkpoint resume events

**Files Modified/Created:**
- `src/api/v1/sessions.py` - Complete refactor
- `src/api/v1/memory.py` - NEW
- `src/api/v1/agent.py` - WebSocket enhancements
- `tests/api/test_sessions.py` - NEW
- `tests/api/test_memory.py` - NEW
- `tests/api/test_agent_stream.py` - NEW

**Duration**: 2-3 days
**Steps**: 20

---

### Phase 5: Future Enhancements

**Focus**: Advanced features for production-scale deployment

**Key Deliverables:**
- File-based vector store with semantic search
- Distributed storage abstraction (file + S3)
- Memory visualization dashboard
- Advanced caching strategies

**Parts:**

**Part 1: Vector Store**
- Install sentence-transformers
- Create embeddings module
- Generate and store embeddings in JSON files
- Implement vector search with cosine similarity
- Integration with search_sessions

**Part 2: Distributed Storage**
- Create storage abstraction (Backend interface)
- Implement FileStorageBackend
- Implement S3StorageBackend
- Add storage configuration
- Migration utility

**Part 3: Memory Dashboard**
- Dashboard API specification
- Session viewer UI
- Profile editor UI
- Workflow manager UI
- Memory stats UI

**Part 4: Advanced Caching**
- LRU cache implementation
- Session file cache
- Workflow cache
- Cache warming on startup
- Cache invalidation strategy

**Files Modified/Created:**
- `src/memory/embeddings.py` - NEW
- `src/storage/abstract.py` - NEW
- `src/storage/file_backend.py` - NEW
- `src/storage/s3_backend.py` - NEW
- `src/utils/lru_cache.py` - NEW
- `docs/MEMORY_DASHBOARD_API.md` - NEW

**Duration**: Ongoing
**Steps**: 24

---

## Overall Progress

```
┌─────────────────────────────────────────────────────────────────┐
│                   TOTAL IMPLEMENTATION PROGRESS              │
├─────────────────────────────────────────────────────────────────┤
│                                                             │
│  PHASE 1: File-Based Foundation  ░░░░░░   0/20  │
│  PHASE 2: PostgreSQL Simplif.   ░░░░░░   0/21  │
│  PHASE 3: Advanced Features       ░░░░░░   0/26  │
│  PHASE 4: API Integration        ░░░░░░   0/20  │
│  PHASE 5: Future Enhancements   ░░░░░░   0/24  │
│                                                             │
│  ────────────────────────────────────────────────────────── │
│                                                             │
│  CORE (Phases 1-4)             ░░░░░░   0/87  │
│  ────────────────────────────────────────────────────────── │
│                                                             │
│  PRODUCTION READY               ░░░░░░   0/87  │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure Summary

### Directory Layout After Implementation

```
~/.orbit/memory/
├── identity/
│   ├── user_profile.md              # User preferences (read/write)
│   ├── user_tokens.json            # Encrypted OAuth tokens
│   └── user_settings.json          # Agent configuration
│
├── procedural/
│   ├── workflows.md               # Learned workflows (read/write)
│   ├── commands.md                 # Frequent commands (read/write)
│   └── snippets.md                # Code templates (read/write)
│
├── episodic/
│   ├── sessions/
│   │   ├── {session_id}.md          # Full conversation (read/write)
│   │   └── {session_id}.summary.json  # Compact summary
│   ├── archive/                   # Old compressed sessions
│   ├── checkpoints/
│   │   └── {thread_id}_{ckpt_id}.json  # LangGraph checkpoints
│   └── compaction_log.md           # Memory management history
│
└── users/
    ├── {user_id}/
    │   ├── session_index.json        # Fast session lookup
    │   ├── preferences.json         # Cached preferences
    │   └── stats.json                # Usage analytics
    └── global_index.json           # Cross-user search index
```

### PostgreSQL Schema After Implementation

```
Tables (Minimal):
├── users                           # Authentication only
│   ├── id, email, password_hash
│   ├── is_active, last_login_at
│   └── created_at, updated_at
│
├── session_metadata               # Lightweight metadata
│   ├── session_id, user_id
│   ├── title, status
│   ├── created_at, updated_at
│   ├── last_message_at, message_count
│
├── rate_limits                    # API rate limiting
│   ├── user_id, resource_type
│   ├── window_start, request_count
│
└── api_keys                       # Third-party API keys (encrypted)
    ├── user_id, service
    ├── encrypted_key, key_name
    └── is_active, created_at, updated_at

Removed Tables:
├── agent_messages               # Now in sessions/{id}.md
├── agent_tool_calls              # Not needed
├── agent_states                 # Now in checkpoints/{id}.json
├── agent_workflow_executions    # Not needed
├── agent_workflow_steps         # Not needed
└── agent_embeddings              # Future (file-based)
```

---

## Migration Plan

### Pre-Migration Checklist

- [ ] Backup existing PostgreSQL database
- [ ] Verify backup file size is reasonable
- [ ] Test restore on staging database
- [ ] Document current PostgreSQL schema
- [ ] Identify any data that must be preserved

### Migration Steps

1. **Export Messages to Files**
   - Write script to read from `agent_messages` table
   - Write each session to `episodic/sessions/{id}.md`
   - Create `{id}.summary.json` for each session
   - Update session indexes

2. **Export Workflows** (if any in PostgreSQL)
   - Read from any workflow tables
   - Append to `procedural/workflows.md`

3. **Apply Minimal Schema**
   - Run migration 002_minimal_schema.sql
   - Verify tables dropped correctly
   - Verify new tables created

4. **Update Application**
   - Deploy new code (Phase 1-4)
   - Test file-based memory operations
   - Verify PostgreSQL only stores metadata

5. **Verification**
   - Test conversation creation and flow
   - Test session loading from files
   - Test search across sessions
   - Verify PostgreSQL metadata updates
   - Monitor for errors in logs

### Rollback Plan

If issues arise during migration:

1. **Immediate Actions**
   - Stop application
   - Restore PostgreSQL from backup
   - Revert code changes (git rollback)
   - Verify data integrity

2. **Investigate Issues**
   - Review error logs
   - Identify root cause
   - Fix issues

3. **Retry Migration**
   - Address specific issues
   - Plan modified migration approach
   - Test on staging first

---

## Testing Strategy

### Unit Tests

Test individual components in isolation

### Integration Tests

Test full conversation flows end-to-end

### Performance Tests

Test file I/O performance and cache effectiveness

---

## Monitoring & Metrics

### Key Metrics to Track

| Metric | Source | Purpose |
|--------|---------|---------|
| File write latency | Application logs | Detect I/O bottlenecks |
| File read latency | Application logs | Detect read performance |
| Session creation rate | Application logs | Monitor usage |
| Compression frequency | Compaction log | Optimize thresholds |
| Cache hit rate | Cache stats | Tune cache size/TTL |
| Memory size (total bytes) | get_memory_stats() | Trigger compaction |
| PostgreSQL query time | Database logs | Verify minimal DB usage |
| Search query time | Application logs | Optimize search |

---

## Success Criteria

### Production Readiness Checklist

**Phase 1: File-Based Foundation**
- [ ] memory_context in all LLM prompts
- [ ] session_writer node integrated
- [ ] File checkpointer working
- [ ] Session index created and updated
- [ ] All unit tests pass
- [ ] Integration tests pass

**Phase 2: PostgreSQL Simplification**
- [ ] Minimal schema applied
- [ ] Session API uses file-based storage
- [ ] Agent streaming writes to files
- [ ] ConversationMemory simplified
- [ ] Migration runs without errors
- [ ] All API tests pass

**Phase 3: Advanced Features**
- [ ] Session search working
- [ ] Session compression working
- [ ] Auto-compaction triggers correctly
- [ ] Preferences cache effective
- [ ] Memory API working
- [ ] All feature tests pass

**Phase 4: API Integration**
- [ ] All endpoints use file-based storage
- [ ] Error handling complete
- [ ] WebSocket streaming enhanced
- [ ] All API tests pass
- [ ] Documentation updated

**Overall Production**
- [ ] File-based memory is primary storage
- [ ] PostgreSQL minimal (auth/metadata only)
- [ ] All phases tested and working
- [ ] Migration completed successfully
- [ ] Monitoring and metrics in place
- [ ] Documentation complete

---

## Risk Assessment

### High Priority Risks

| Risk | Impact | Mitigation |
|------|----------|------------|
| File I/O performance | High | Implement caching, use async operations |
| Concurrent file corruption | Medium | Use file locking, test heavily |
| Data loss during migration | Critical | Full backup before migration |
| Incomplete migration | Medium | Test on staging, have rollback plan |
| Cache staleness | Low | Short TTL (5 min), invalidate on updates |

### Medium Priority Risks

| Risk | Impact | Mitigation |
|------|----------|------------|
| Search performance at scale | Medium | Vector search (Phase 5), pagination |
| Memory bloat | Medium | Auto-compaction, archive old sessions |
| Disk space exhaustion | Medium | Monitoring, size limits |
| File system permissions | Low | Proper permissions (700), validation |

### Low Priority Risks

| Risk | Impact | Mitigation |
|------|----------|------------|
| Token overflow in file names | Low | Use UUID for session IDs |
| Large file reads slow | Low | Lazy loading, chunking for UI |
| Manual file corruption | Low | Git ignore memory/ backups |

---

## Deployment Checklist

### Pre-Deployment

- [ ] All phases implemented and tested
- [ ] Code review completed
- [ ] Database backup created
- [ ] Migration plan documented
- [ ] Rollback plan tested
- [ ] Monitoring configured
- [ ] Documentation updated
- [ ] Environment variables set
- [ ] Staging tested and verified

### Deployment Steps

1. **Staging Deployment**
   - [ ] Deploy code to staging
   - [ ] Run database migration
   - [ ] Verify file structure created
   - [ ] Run integration tests
   - [ ] Monitor for errors (30 min)
   - [ ] Get sign-off

2. **Production Deployment**
   - [ ] Create final production backup
   - [ ] Deploy code to production
   - [ ] Run database migration
   - [ ] Verify file permissions
   - [ ] Smoke test key features
   - [ ] Monitor for errors
   - [ ] Validate data integrity

3. **Post-Deployment**
   - [ ] Monitor error rates for 24 hours
   - [ ] Check performance metrics
   - [ ] Validate file-based operations
   - [ ] Verify PostgreSQL minimal usage
   - [ ] Update runbooks if needed

---

## Support & Troubleshooting

### Common Issues

**Issue**: Session not found
**Solution**: Check session_index.json, verify session file exists

**Issue**: Memory not loading
**Solution**: Check file permissions (~/.orbit/memory should be 700), verify structure exists

**Issue**: Compaction not triggering
**Solution**: Check threshold calculation, verify get_file_based_memory_stats() working

**Issue**: PostgreSQL queries still heavy
**Solution**: Verify ConversationMemory not being called, check migration applied

**Issue**: Cache not working
**Solution**: Check TTL expiration, verify invalidate_user_cache() called on updates

**Issue**: File write errors
**Solution**: Check disk space, verify directory permissions, check for concurrent writes

### Debugging Commands

Check memory structure, size, PostgreSQL state, session index, compaction log, and file permissions.

---

## Glossary

| Term | Definition |
|-------|------------|
| **File-based memory** | Primary storage in `~/.orbit/memory/` files |
| **Minimal PostgreSQL** | Authentication and metadata only |
| **Memory context** | User profile, workflows, sessions formatted for LLM |
| **Session index** | Fast JSON index of user's sessions |
| **File checkpointer** | LangGraph pause/resume using JSON files |
| **Compaction** | LLM-based memory consolidation to prevent bloat |
| **Vector search** | Semantic search using embeddings (Phase 5) |
| **LRU cache** | Least Recently Used cache with TTL |
| **TTL** | Time To Live - cache expiration |

---

## References

- [MEMORY_MANAGEMENT.md](./MEMORY_MANAGEMENT.md) - Complete memory documentation
- [PHASE1_MEMORY_FOUNDATION.md](./PHASE1_MEMORY_FOUNDATION.md) - Phase 1 detailed guide
- [PHASE2_POSTGRESQL_SIMPLIFICATION.md](./PHASE2_POSTGRESQL_SIMPLIFICATION.md) - Phase 2 detailed guide
- [PHASE3_ADVANCED_FEATURES.md](./PHASE3_ADVANCED_FEATURES.md) - Phase 3 detailed guide
- [PHASE4_API_INTEGRATION.md](./PHASE4_API_INTEGRATION.md) - Phase 4 detailed guide
- [PHASE5_FUTURE_ENHANCEMENTS.md](./PHASE5_FUTURE_ENHANCEMENTS.md) - Phase 5 detailed guide

---

## Contact & Support

For questions about memory implementation:
1. Review phase-specific documentation
2. Check glossary for terminology
3. Review common issues and solutions
4. Verify environment configuration
5. Check monitoring and logs

---

**Ready to implement file-based memory? Follow the phases in order!** 🚀
