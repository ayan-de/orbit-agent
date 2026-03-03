# Phase 3: Advanced File-Based Features

**Scope**: Add search, compression, and preferences cache to file-based memory
**Target**: Full-featured file-based memory with smart management
**Duration**: 3-4 days
**Last Updated**: 2026-03-03

---

## Overview

This phase focuses on advanced file-based memory features:
- Implement session search across all session files
- Add LLM-based session compression
- Implement automatic memory compaction
- Add preferences cache for fast access

**Key Features**: Intelligent memory management that keeps storage optimized.

---

## Phase 3: Advanced Features (Days 7-10)

**Goal**: Add search, compression, and caching to file-based memory.

### Day 7: Session Search

| Step | Task | File(s) | Status |
|------|------|----------|--------|
| 7.1 | Create search.py module | `src/memory/search.py` | ⬜ |
| 7.2 | Implement search_sessions | `src/memory/search.py` | ⬜ |
| 7.3 | Implement semantic_search_sessions | `src/memory/search.py` | ⬜ |
| 7.4 | Implement search_workflows | `src/memory/search.py` | ⬜ |
| 7.5 | Add search API endpoints | `src/api/v1/memory.py` | ⬜ |
| 7.6 | Test search functionality | `tests/memory/test_search.py` | ⬜ |

**Details:**

**Task 7.1-7.4: Create search module**

Create new module that provides:
- `search_sessions()` - Keyword matching across session files with snippet extraction
- `semantic_search_sessions()` - Semantic search using embeddings (stub for Phase 5)
- `search_workflows()` - Search workflows by name/description/steps
- `search_all_memory()` - Cross-type search across sessions, workflows, profile

**Task 7.5: Add memory API**

Create REST endpoints:
- `POST /api/v1/memory/search` - Search across all memory types
- Accepts query string and limit parameter
- Returns results grouped by type (sessions, workflows, profile)
- Handles search errors gracefully

---

### Day 8: Session Compression

| Step | Task | File(s) | Status |
|------|------|----------|--------|
| 8.1 | Implement compress_session_file | `src/memory/compression.py` | ⬜ |
| 8.2 | Add [COMPRESSED] marker format | `src/memory/compression.py` | ⬜ |
| 8.3 | Create summary.json format | `src/memory/compression.py` | ⬜ |
| 8.4 | Add compression API endpoint | `src/api/v1/memory.py` | ⬜ |
| 8.5 | Test compression functionality | `tests/memory/test_compression.py` | ⬜ |

**Details:**

**Task 8.1-8.3: Create compression module**

Implement functions that:
- Parse session file to extract messages
- Split messages into old (to compress) and recent (to keep)
- Use LLM to generate concise summary of old messages
- Add [COMPRESSED] marker with summary to session file
- Create/update {session_id}.summary.json with summary and metadata
- Accepts parameters: keep_messages count, max_summary_chars

**Task 8.4: Add compression API**

Create endpoint:
- `POST /api/v1/sessions/{session_id}/compress` - Manual compression
- Accepts keep_messages parameter
- Returns compression result with counts

---

### Day 9: Memory Compaction

| Step | Task | File(s) | Status |
|------|------|----------|--------|
| 9.1 | Enhance auto_compaction | `src/memory/compaction.py` | ⬜ |
| 9.2 | Add file-based threshold check | `src/memory/compaction.py` | ⬜ |
| 9.3 | Integrate with session_writer | `src/agent/nodes/session_writer.py` | ⬜ |
| 9.4 | Add compaction API endpoint | `src/api/v1/memory.py` | ⬜ |
| 9.5 | Test compaction triggers | `tests/memory/test_compaction.py` | ⬜ |

**Details:**

**Task 9.1-9.3: Enhance compaction**

Update compaction module to:
- Implement `get_file_based_memory_stats()` - Calculate total file size, session count, etc.
- Replace PostgreSQL-based threshold check with file-based
- Modify `auto_compaction()` to use file-based stats
- Set threshold at 80% of target (e.g., 25KB for 128K tokens)

**Task 9.3: Integrate with session_writer**

Update session_writer_node to:
- Call `get_file_based_memory_stats()` after write
- Check if compaction_needed
- Trigger async background compaction if needed
- Don't block response with compaction

**Task 9.4: Add compaction API**

Create endpoint:
- `POST /api/v1/memory/compact` - Trigger manual compaction
- Accepts threshold parameter
- Returns compaction results

---

### Day 10: Preferences Cache

| Step | Task | File(s) | Status |
|------|------|----------|--------|
| 10.1 | Create preferences.py module | `src/memory/preferences.py` | ⬜ |
| 10.2 | Implement get_user_preferences | `src/memory/preferences.py` | ⬜ |
| 10.3 | Implement update_preference | `src/memory/preferences.py` | ⬜ |
| 10.4 | Add in-memory cache layer | `src/memory/preferences.py` | ⬜ |
| 10.5 | Integrate with memory_loader | `src/agent/nodes/memory_loader.py` | ⬜ |
| 10.6 | Test preferences cache | `tests/memory/test_preferences.py` | ⬜ |

**Details:**

**Task 10.1-10.4: Create preferences module**

Implement caching module that:
- Creates in-memory cache with LRU eviction
- Stores {user_id: {preferences, loaded_at}}
- Sets 5-minute TTL for cache entries
- Provides `get_user_preferences()` with force_refresh option
- Provides `update_preference()` and `update_preferences()` that invalidate cache
- Provides `invalidate_user_cache()` and `invalidate_all_caches()`

**Task 10.5: Integrate with memory_loader**

Update memory_loader_node to:
- Use cached preferences instead of reading file every time
- Pass preferences as part of memory_context
- Format preferences nicely for LLM consumption

---

## Success Criteria

### Phase 3 is Complete When:

**Session Search:**
☐ search.py module created
☐ search_sessions working with keyword matching
☐ semantic_search_sessions stub created (for future)
☐ search_workflows working
☐ search_all_memory working across all types
☐ Memory API endpoints created
☐ Search tests pass

**Session Compression:**
☐ compression.py module created
☐ compress_session_file working with LLM summary
☐ [COMPRESSED] marker added to files
☐ summary.json created alongside session files
☐ Compression API endpoint working
☐ Compression tests pass

**Memory Compaction:**
☐ get_file_based_memory_stats working
☐ auto_compaction uses file-based stats
☐ Compaction triggers after threshold
☐ Compaction API endpoint working
☐ Compaction tests pass
☐ Integration with session_writer working

**Preferences Cache:**
☐ preferences.py module created
☐ get_user_preferences working with cache
☐ update_preference writes to user_profile.md
☐ In-memory cache layer working (5 min TTL)
☐ Integrated with memory_loader
☐ Preferences tests pass

---

## 📊 Total Progress

```
Phase 3: Advanced Features        ░░░░░░   0/26 steps
Day 7: Session Search              ░░░░░░   0/6 steps
Day 8: Session Compression          ░░░░░░   0/5 steps
Day 9: Memory Compaction          ░░░░░░   0/5 steps
Day 10: Preferences Cache          ░░░░░░   0/6 steps
────────────────────────────────────────────
Total                              ░░░░░░   0/26 steps
```

---

## Next Steps After Phase 3

1. ✅ Review Phase 2 completion
2. ⏭️ Start with Day 7: Session Search
3. ⏭️ Implement Day 8: Session Compression
4. ⏭️ Implement Day 9: Memory Compaction
5. ⏭️ Implement Day 10: Preferences Cache
6. ⏭️ Test all advanced features end-to-end
7. ⏭️ Move to Phase 4: API Integration

---

**Ready to add advanced features? Let's enhance memory!** 🔍
