# Phase 1: File-Based Memory Foundation

**Scope**: Make file-based memory primary storage with LLM context injection
**Target**: Memory context injected into all LLM prompts, session persistence to files
**Duration**: 2-3 days
**Last Updated**: 2026-03-03

---

## Overview

This phase focuses on making file-based memory primary storage by:
- Injecting memory context into all LLM prompts (currently loaded but unused)
- Creating session writer node to persist conversations to files
- Implementing file-based checkpointer for LangGraph pause/resume
- Creating user session index for fast lookups without file system scans

**Key Insight**: Currently `memory_context` is populated by `memory_loader_node` but never used in any LLM prompt. This is a critical gap to fix.

---

## Phase 1: File-Based Foundation (Days 1-3)

**Goal**: Enable file-based memory as primary storage with proper LLM integration.

### Day 1: Memory Context Injection

| Step | Task | File(s) | Status |
|------|------|----------|--------|
| 1.1 | Add memory_context to classifier prompt | `src/agent/prompts/classifier.py` | ⬜ |
| 1.2 | Add memory_context to planner prompt | `src/agent/prompts/planner.py` | ⬜ |
| 1.3 | Add memory_context to responder prompt | `src/agent/prompts/responder.py` | ⬜ |
| 1.4 | Update classifier node to pass memory_context | `src/agent/nodes/classifier.py` | ⬜ |
| 1.5 | Update planner node to pass memory_context | `src/agent/nodes/planner.py` | ⬜ |
| 1.6 | Update responder node to pass memory_context | `src/agent/nodes/responder.py` | ⬜ |

**Details:**

**Task 1.1-1.3: Update Prompts**

Add `memory_context` variable to all LLM prompt templates with a Memory Context section that provides:
- User preferences from profile
- Learned workflows
- Recent session context
- Usage instructions for the LLM

**Task 1.4-1.6: Update Node Invocations**

Pass `memory_context` from state to LLM chains in all three nodes:
- Extract memory_context from state using `state.get("memory_context", "")`
- Pass as variable to LLM chain invoke
- Maintain existing logic for other parameters

---

### Day 2: Session Writer Node

| Step | Task | File(s) | Status |
|------|------|----------|--------|
| 2.1 | Create session_writer node | `src/agent/nodes/session_writer.py` | ⬜ |
| 2.2 | Implement write conversation to file | `src/agent/nodes/session_writer.py` | ⬜ |
| 2.3 | Implement update session index | `src/agent/nodes/session_writer.py` | ⬜ |
| 2.4 | Add session_writer to graph | `src/agent/graph.py` | ⬜ |
| 2.5 | Connect responder → session_writer | `src/agent/graph.py` | ⬜ |

**Details:**

**Task 2.1: Create session_writer.py**

Create new LangGraph node that:
- Extracts session_id, user_id, messages from state
- Writes each message to session file using append_to_session()
- Skips system/tool messages (internal only)
- Updates user session index with message count
- Returns confirmation of write with error handling

**Task 2.3: Create session_index.py**

Create new module that provides:
- `update_session_index()` - Updates or creates session entry in JSON index
- `get_user_sessions()` - Retrieves sessions from index for fast listing
- Manages active/archived session lists
- Updates statistics (total_sessions, total_messages)

**Task 2.4-2.5: Integrate into graph**

- Add session_writer node to workflow
- Connect responder → session_writer → END
- Ensure all paths that reach responder also reach session_writer

---

### Day 3: File-Based Checkpointer

| Step | Task | File(s) | Status |
|------|------|----------|--------|
| 3.1 | Create file checkpointer class | `src/memory/file_checkpointer.py` | ⬜ |
| 3.2 | Implement save_checkpoint method | `src/memory/file_checkpointer.py` | ⬜ |
| 3.3 | Implement load_checkpoint method | `src/memory/file_checkpointer.py` | ⬜ |
| 3.4 | Implement list_checkpoints method | `src/memory/file_checkpointer.py` | ⬜ |
| 3.5 | Update graph to use file checkpointer | `src/agent/graph.py` | ⬜ |
| 3.6 | Test checkpoint save/load | `tests/memory/test_file_checkpointer.py` | ⬜ |

**Details:**

**Task 3.1: Create file_checkpointer.py**

Implement FileCheckpointer class that:
- Inherits from BaseCheckpointSaver
- Stores checkpoints as JSON files in `episodic/checkpoints/`
- Handles LangGraph checkpoint serialization/deserialization
- Manages checkpoint metadata (thread_id, parent_checkpoint)
- Implements all required async methods: aput, aget, alist, aput_writes

**Task 3.5: Update graph**

- Remove PostgreSQL checkpointer import
- Import get_file_checkpointer() from new module
- Update get_compiled_graph() to use file checkpointer
- Ensure backward compatibility with checkpoint configuration

---

## Success Criteria

### Phase 1 is Complete When:

**Memory Context Injection:**
☐ memory_context added to classifier prompt
☐ memory_context added to planner prompt
☐ memory_context added to responder prompt
☐ classifier node passes memory_context to LLM
☐ planner node passes memory_context to LLM
☐ responder node passes memory_context to LLM

**Session Writer Node:**
☐ session_writer.py created with write to file functionality
☐ session_index.py created for fast lookups
☐ session_writer node integrated into graph
☐ responder → session_writer → END flow working
☐ Session files created in episodic/sessions/

**File Checkpointer:**
☐ FileCheckpointer class implements BaseCheckpointSaver
☐ save_checkpoint writes to episodic/checkpoints/
☐ load_checkpoint reads from episodic/checkpoints/
☐ list_checkpoints returns checkpoint history
☐ Graph uses file checkpointer instead of PostgreSQL
☐ Checkpoint save/load tested and working

**Testing:**
☐ Unit tests for memory context injection pass
☐ Unit tests for session writer pass
☐ Unit tests for session index pass
☐ Unit tests for file checkpointer pass
☐ Integration test: full conversation flow works

---

## 📊 Total Progress

```
Phase 1: File-Based Foundation   ░░░░░░   0/20 steps
Day 1: Memory Context Injection  ░░░░░░   0/6 steps
Day 2: Session Writer Node        ░░░░░░   0/5 steps
Day 3: File Checkpointer          ░░░░░░   0/6 steps
────────────────────────────────────────────
Total                              ░░░░░░   0/20 steps
```

---

## Next Steps After Phase 1

1. ✅ Review and approve Phase 1 plan
2. ⏭️ Start with Day 1: Memory Context Injection
3. ⏭️ Implement Day 2: Session Writer Node
4. ⏭️ Implement Day 3: File Checkpointer
5. ⏭️ Test end-to-end file-based memory flow
6. ⏭️ Move to Phase 2: PostgreSQL Simplification

---

**Ready to make file-based memory primary storage? Let's begin!** 🚀
