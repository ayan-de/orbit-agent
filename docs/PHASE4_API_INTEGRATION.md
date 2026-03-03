# Phase 4: API and Integration

**Scope**: Update all API endpoints to use file-based memory
**Target**: Complete file-based memory API with proper error handling
**Duration**: 2-3 days
**Last Updated**: 2026-03-03

---

## Overview

This phase focuses on ensuring all APIs use file-based memory correctly:
- Update all endpoints to use file-based storage
- Add memory management endpoints
- Enhance WebSocket streaming with memory context
- Ensure proper error handling for file operations

**Key Goal**: Complete API layer that fully leverages file-based memory.

---

## Phase 4: API Integration (Days 11-13)

**Goal**: Ensure all APIs use file-based storage correctly.

### Day 11: Core API Updates

| Step | Task | File(s) | Status |
|------|------|----------|--------|
| 11.1 | Update SessionResponse schema | `src/api/v1/sessions.py` | ⬜ |
| 11.2 | Add file error handling | `src/api/v1/sessions.py` | ⬜ |
| 11.3 | Update update_session endpoint | `src/api/v1/sessions.py` | ⬜ |
| 11.4 | Update archive_session endpoint | `src/api/v1/sessions.py` | ⬜ |
| 11.5 | Update delete_session endpoint | `src/api/v1/sessions.py` | ⬜ |
| 11.6 | Add session validation | `src/api/v1/sessions.py` | ⬜ |
| 11.7 | Test all session endpoints | `tests/api/test_sessions.py` | ⬜ |

**Details:**

**Task 11.1-11.6: Update sessions.py**

Update all session endpoints to use file-based storage:
- create_session: Write to file + PostgreSQL metadata only
- get_session: Read from file + PostgreSQL metadata
- list_sessions: Use session_index.json for fast lookups
- update_session: Update metadata in PostgreSQL
- archive_session: Move file to archive directory
- delete_session: Delete file + soft/hard delete in metadata

**Task 11.2: Add error handling**

Create error classes for file operations:
- SessionNotFoundError - 404 when session file not found
- SessionFileError - 500 for file read/write failures
- Proper error messages with operation details

---

### Day 12: Memory Management API

| Step | Task | File(s) | Status |
|------|------|----------|--------|
| 12.1 | Create memory router | `src/api/v1/memory.py` | ⬜ |
| 12.2 | Add profile endpoints | `src/api/v1/memory.py` | ⬜ |
| 12.3 | Add workflow endpoints | `src/api/v1/memory.py` | ⬜ |
| 12.4 | Add preferences endpoints | `src/api/v1/memory.py` | ⬜ |
| 12.5 | Add compaction trigger endpoint | `src/api/v1/memory.py` | ⬜ |
| 12.6 | Add session info endpoint | `src/api/v1/memory.py` | ⬜ |
| 12.7 | Test memory API | `tests/api/test_memory.py` | ⬜ |

**Details:**

**Task 12.1-12.6: Create memory API**

Create endpoints for memory management:
- GET /memory/profile - Get user profile
- PUT /memory/profile - Update user profile
- GET /memory/workflows - Get user's workflows
- POST /memory/workflows - Save new workflow
- GET /memory/preferences - Get preferences (with caching)
- PUT /memory/preferences - Update preferences
- POST /memory/compact - Trigger manual compaction
- GET /memory/search - Search across all memory types
- GET /memory/session/{id} - Get session with full context

---

### Day 13: WebSocket Enhancements

| Step | Task | File(s) | Status |
|------|------|----------|--------|
| 13.1 | Add memory context loading events | `src/api/v1/agent.py` | ⬜ |
| 13.2 | Stream compaction progress | `src/api/v1/agent.py` | ⬜ |
| 13.3 | Add checkpoint resume events | `src/api/v1/agent.py` | ⬜ |
| 13.4 | Add error recovery for file ops | `src/api/v1/agent.py` | ⬜ |
| 13.5 | Test WebSocket streaming | `tests/api/test_agent_stream.py` | ⬜ |

**Details:**

**Task 13.1-13.4: Enhance WebSocket**

Add streaming events for memory operations:
- memory_loading - Send when memory context is loading
- memory_loaded - Send with loaded context
- memory_written - Send after session write completes
- compaction_progress - Send during background compaction
- checkpoint_created - Send when checkpoint is saved
- Error recovery for file operation failures

---

## Success Criteria

### Phase 4 is Complete When:

**Core API Updates:**
☐ All session endpoints use file-based storage
☐ Error handling classes implemented
☐ Session validation added
☐ SessionResponse schema updated
☐ File error handling in all endpoints
☐ Session tests pass

**Memory Management API:**
☐ Memory router created
☐ Profile endpoints working
☐ Workflow endpoints working
☐ Preferences endpoints working
☐ Compaction endpoint working
☐ Session info endpoint working
☐ Memory API tests pass

**WebSocket Enhancements:**
☐ Memory context loading events working
☐ Compaction progress streaming
☐ Checkpoint resume events
☐ Error recovery for file operations
☐ WebSocket streaming tests pass

---

## 📊 Total Progress

```
Phase 4: API Integration           ░░░░░   0/20 steps
Day 11: Core API Updates          ░░░░░   0/7 steps
Day 12: Memory Management API    ░░░░░   0/7 steps
Day 13: WebSocket Enhancements    ░░░░░   0/6 steps
────────────────────────────────────────────
Total                              ░░░░░   0/20 steps
```

---

## Next Steps After Phase 4

1. ✅ Review Phase 3 completion
2. ⏭️ Start with Day 11: Core API Updates
3. ⏭️ Implement Day 12: Memory Management API
4. ⏭️ Implement Day 13: WebSocket Enhancements
5. ⏭️ Test all API endpoints
6. ⏭️ Document API changes
7. ⏭️ Move to Phase 5: Future Enhancements

---

**Ready for complete API integration? Let's finish!** 🚀
