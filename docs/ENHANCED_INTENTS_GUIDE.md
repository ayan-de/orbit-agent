# Enhanced Intent Classification Implementation Guide

**Scope**: Granular intent understanding for each service
**Target**: Agent accurately understands and routes user requests
**Duration**: 1.5-2 weeks
**Last Updated**: 2026-03-01

---

## Overview

Move from generic intents ("command", "question") to domain-specific granular intents:
- **Jira Intents**: List tickets, complete ticket, add comment, daily report
- **Git Intents**: Commit, push, create branch, merge PR, show status
- **File Intents**: Read file, write file, delete file, create directory
- **Web Search Intents**: General search, news search, fact verification
- **Workflow Intents**: Execute workflow, save workflow, list workflows
- **System Intents**: Help, status, configure, reset

**Benefits**:
- More accurate routing to correct tools/agents
- Better understanding of what user wants
- Fewer follow-up questions
- Higher success rate on first attempt

---

## Phase 1: Intent Definitions (Days 1-2)

**Goal**: Define granular intents for each domain.

### Day 1: Jira Intents

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 1.1 | Define JiraIntent enum | `orbit-agent/src/agent/intents/jira_intents.py` | ⬜ |
| 1.2 | Add LIST_TICKETS intent | `orbit-agent/src/agent/intents/jira_intents.py` | ⬜ |
| 1.3 | Add GET_TICKET_DETAILS intent | `orbit-agent/src/agent/intents/jira_intents.py` | ⬜ |
| 1.4 | Add COMPLETE_TICKET intent | `orbit-agent/src/agent/intents/jira_intents.py` | ⬜ |
| 1.5 | Add ADD_COMMENT intent | `orbit-agent/src/agent/intents/jira_intents.py` | ⬜ |
| 1.6 | Add DAILY_SUMMARY intent | `orbit-agent/src/agent/intents/jira_intents.py` | ⬜ |
| 1.7 | Add DAILY_REPORT intent | `orbit-agent/src/agent/intents/jira_intents.py` | ⬜ |
| 1.8 | Add SEARCH_TICKETS intent | `orbit-agent/src/agent/intents/jira_intents.py` | ⬜ |
| 1.9 | Add CREATE_TICKET intent | `orbit-agent/src/agent/intents/jira_intents.py` | ⬜ |
| 1.10 | Add ASSIGN_TICKET intent | `orbit-agent/src/agent/intents/jira_intents.py` | ⬜ |
| 1.11 | Add ticket_key parameter | `orbit-agent/src/agent/intents/jira_intents.py` | ⬜ |
| 1.12 | Add comment parameter | `orbit-agent/src/agent/intents/jira_intents.py` | ⬜ |
| 1.13 | Add query parameter | `orbit-agent/src/agent/intents/jira_intents.py` | ⬜ |

### Day 2: Git Intents

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 2.1 | Define GitIntent enum | `orbit-agent/src/agent/intents/git_intents.py` | ⬜ |
| 2.2 | Add GIT_STATUS intent | `orbit-agent/src/agent/intents/git_intents.py` | ⬜ |
| 2.3 | Add GIT_COMMIT intent | `orbit-agent/src/agent/intents/git_intents.py` | ⬜ |
| 2.4 | Add GIT_PUSH intent | `orbit-agent/src/agent/intents/git_intents.py` | ⬜ |
| 2.5 | Add GIT_PULL intent | `orbit-agent/src/agent/intents/git_intents.py` | ⬜ |
| 2.6 | Add GIT_CREATE_BRANCH intent | `orbit-agent/src/agent/intents/git_intents.py` | ⬜ |
| 2.7 | Add GIT_SWITCH_BRANCH intent | `orbit-agent/src/agent/intents/git_intents.py` | ⬜ |
| 2.8 | Add GIT_DELETE_BRANCH intent | `orbit-agent/src/agent/intents/git_intents.py` | ⬜ |
| 2.9 | Add GIT_MERGE intent | `orbit-agent/src/agent/intents/git_intents.py` | ⬜ |
| 2.10 | Add GIT_CREATE_PR intent | `orbit-agent/src/agent/intents/git_intents.py` | ⬜ |
| 2.11 | Add GIT_SHOW_LOG intent | `orbit-agent/src/agent/intents/git_intents.py` | ⬜ |
| 2.12 | Add branch_name parameter | `orbit-agent/src/agent/intents/git_intents.py` | ⬜ |
| 2.13 | Add commit_message parameter | `orbit-agent/src/agent/intents/git_intents.py` | ⬜ |

---

## Phase 2: File & Web Search Intents (Days 3-4)

**Goal**: Define intents for file operations and web search.

### Day 3: File Intents

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 3.1 | Define FileIntent enum | `orbit-agent/src/agent/intents/file_intents.py` | ⬜ |
| 3.2 | Add FILE_READ intent | `orbit-agent/src/agent/intents/file_intents.py` | ⬜ |
| 3.3 | Add FILE_WRITE intent | `orbit-agent/src/agent/intents/file_intents.py` | ⬜ |
| 3.4 | Add FILE_APPEND intent | `orbit-agent/src/agent/intents/file_intents.py` | ⬜ |
| 3.5 | Add FILE_DELETE intent | `orbit-agent/src/agent/intents/file_intents.py` | ⬜ |
| 3.6 | Add FILE_LIST intent | `orbit-agent/src/agent/intents/file_intents.py` | ⬜ |
| 3.7 | Add FILE_CREATE_DIR intent | `orbit-agent/src/agent/intents/file_intents.py` | ⬜ |
| 3.8 | Add FILE_SEARCH intent | `orbit-agent/src/agent/intents/file_intents.py` | ⬜ |
| 3.9 | Add path parameter | `orbit-agent/src/agent/intents/file_intents.py` | ⬜ |
| 3.10 | Add content parameter | `orbit-agent/src/agent/intents/file_intents.py` | ⬜ |

### Day 4: Web Search Intents

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 4.1 | Define WebSearchIntent enum | `orbit-agent/src/agent/intents/web_intents.py` | ⬜ |
| 4.2 | Add WEB_SEARCH intent | `orbit-agent/src/agent/intents/web_intents.py` | ⬜ |
| 4.3 | Add WEB_SEARCH_NEWS intent | `orbit-agent/src/agent/intents/web_intents.py` | ⬜ |
| 4.4 | Add WEB_VERIFY_FACT intent | `orbit-agent/src/agent/intents/web_intents.py` | ⬜ |
| 4.5 | Add WEB_SEARCH_IMAGES intent | `orbit-agent/src/agent/intents/web_intents.py` | ⬜ |
| 4.6 | Add query parameter | `orbit-agent/src/agent/intents/web_intents.py` | ⬜ |
| 4.7 | Add days parameter (for news) | `orbit-agent/src/agent/intents/web_intents.py` | ⬜ |
| 4.8 | Add domains parameter | `orbit-agent/src/agent/intents/web_intents.py` | ⬜ |

---

## Phase 3: Enhanced Intent Parser (Days 5-7)

**Goal**: Create sophisticated parser that understands all granular intents.

### Day 5: Intent Parser Core

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 5.1 | Create EnhancedIntentParser class | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 5.2 | Import all intent definitions | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 5.3 | Define pattern registry structure | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 5.4 | Add Jira intent patterns | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 5.5 | Add Git intent patterns | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 5.6 | Add File intent patterns | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 5.7 | Add Web Search intent patterns | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 5.8 | Add Workflow intent patterns | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 5.9 | Add System intent patterns | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 5.10 | Add context awareness (previous intents) | `orbit-agent/src/agent/intents/parser.py` | ⬜ |

### Day 6: Pattern Matching

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 6.1 | Implement match_pattern method | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 6.2 | Add fuzzy matching support | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 6.3 | Add intent confidence scoring | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 6.4 | Add parameter extraction (ticket_key, branch) | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 6.5 | Add intent disambiguation | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 6.6 | Create unit tests for parser | `orbit-agent/tests/agent/intents/test_parser.py` | ⬜ |
| 6.7 | Test all intent pattern matches | `orbit-agent/tests/agent/intents/test_parser.py` | ⬜ |
| 6.8 | Test parameter extraction | `orbit-agent/tests/agent/intents/test_parser.py` | ⬜ |
| 6.9 | Test fuzzy matching | `orbit-agent/tests/agent/intents/test_parser.py` | ⬜ |
| 6.10 | Test intent disambiguation | `orbit-agent/tests/agent/intents/test_parser.py` | ⬜ |

### Day 7: Context & Conversation

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 7.1 | Add conversation history tracking | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 7.2 | Implement multi-turn intent resolution | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 7.3 | Add follow-up question detection | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 7.4 | Add intent persistence across turns | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 7.5 | Add clarification prompts | `orbit-agent/src/agent/intents/parser.py` | ⬜ |
| 7.6 | Create integration tests | `orbit-agent/tests/agent/intents/test_integration.py` | ⬜ |
| 7.7 | Test conversation flows | `orbit-agent/tests/agent/intents/test_integration.py` | ⬜ |
| 7.8 | Test multi-turn scenarios | `orbit-agent/tests/agent/intents/test_integration.py` | ⬜ |

---

## Phase 4: Enhanced Classifier Node (Days 8-9)

**Goal**: Replace simple classifier with enhanced intent understanding.

### Day 8: Classifier Node

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 8.1 | Create EnhancedClassifier node | `orbit-agent/src/agent/nodes/enhanced_classifier.py` | ⬜ |
| 8.2 | Integrate EnhancedIntentParser | `orbit-agent/src/agent/nodes/enhanced_classifier.py` | ⬜ |
| 8.3 | Implement classify_intent method | `orbit-agent/src/agent/nodes/enhanced_classifier.py` | ⬜ |
| 8.4 | Add intent result to state | `orbit-agent/src/agent/nodes/enhanced_classifier.py` | ⬜ |
| 8.5 | Add extracted parameters to state | `orbit-agent/src/agent/nodes/enhanced_classifier.py` | ⬜ |
| 8.6 | Add confidence score to state | `orbit-agent/src/agent/nodes/enhanced_classifier.py` | ⬜ |
| 8.7 | Create unit tests for classifier | `orbit-agent/tests/agent/test_enhanced_classifier.py` | ⬜ |

### Day 9: Graph Integration

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 9.1 | Update AgentState with enhanced intent fields | `orbit-agent/src/agent/state.py` | ⬜ |
| 9.2 | Add detected_intent field | `orbit-agent/src/agent/state.py` | ⬜ |
| 9.3 | Add intent_parameters field | `orbit-agent/src/agent/state.py` | ⬜ |
| 9.4 | Add intent_confidence field | `orbit-agent/src/agent/state.py` | ⬜ |
| 9.5 | Replace classifier with enhanced_classifier | `orbit-agent/src/agent/graph.py` | ⬜ |
| 9.6 | Update graph edges for granular intents | `orbit-agent/src/agent/graph.py` | ⬜ |
| 9.7 | Add routing based on intent type | `orbit-agent/src/agent/graph.py` | ⬜ |
| 9.8 | Add conditional edges for each domain | `orbit-agent/src/agent/graph.py` | ⬜ |
| 9.9 | Test full workflow | `orbit-agent/tests/agent/test_enhanced_classifier.py` | ⬜ |
| 9.10 | Test all intent types | `orbit-agent/tests/agent/test_enhanced_classifier.py` | ⬜ |

---

## Phase 5: Domain-Specific Routers (Days 10-11)

**Goal**: Create specialized routers for each domain.

### Day 10: Router Services

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 10.1 | Create JiraRouter service | `orbit-agent/src/agent/routers/jira_router.py` | ⬜ |
| 10.2 | Create GitRouter service | `orbit-agent/src/agent/routers/git_router.py` | ⬜ |
| 10.3 | Create FileRouter service | `orbit-agent/src/agent/routers/file_router.py` | ⬜ |
| 10.4 | Create WebSearchRouter service | `orbit-agent/src/agent/routers/web_router.py` | ⬜ |
| 10.5 | Create WorkflowRouter service | `orbit-agent/src/agent/routers/workflow_router.py` | ⬜ |
| 10.6 | Create SystemRouter service | `orbit-agent/src/agent/routers/system_router.py` | ⬜ |
| 10.7 | Add execute_intent method to each router | `orbit-agent/src/agent/routers/*.py` | ⬜ |
| 10.8 | Add routing logic | `orbit-agent/src/agent/routers/*.py` | ⬜ |
| 10.9 | Create unit tests for routers | `orbit-agent/tests/agent/routers/test_*.py` | ⬜ |
| 10.10 | Test all routers | `orbit-agent/tests/agent/routers/test_*.py` | ⬜ |

### Day 11: Router Orchestration

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 11.1 | Create RouterOrchestrator service | `orbit-agent/src/agent/routers/orchestrator.py` | ⬜ |
| 11.2 | Implement route_to_domain method | `orbit-agent/src/agent/routers/orchestrator.py` | ⬜ |
| 11.3 | Add router discovery | `orbit-agent/src/agent/routers/orchestrator.py` | ⬜ |
| 11.4 | Add fallback routing | `orbit-agent/src/agent/routers/orchestrator.py` | ⬜ |
| 11.5 | Add router caching | `orbit-agent/src/agent/routers/orchestrator.py` | ⬜ |
| 11.6 | Create integration tests | `orbit-agent/tests/agent/routers/test_orchestrator.py` | ⬜ |
| 11.7 | Test cross-domain routing | `orbit-agent/tests/agent/routers/test_orchestrator.py` | ⬜ |
| 11.8 | Test fallback behavior | `orbit-agent/tests/agent/routers/test_orchestrator.py` | ⬜ |

---

## Phase 6: Testing & Documentation (Days 12-13)

**Goal**: Ensure enhanced intents work correctly.

### Day 12: Testing

| Step | Task | Status |
|------|------|--------|
| 12.1 | Test all Jira intent patterns | ⬜ |
| 12.2 | Test all Git intent patterns | ⬜ |
| 12.3 | Test all File intent patterns | ⬜ |
| 12.4 | Test all Web Search intent patterns | ⬜ |
| 12.5 | Test parameter extraction | ⬜ |
| 12.6 | Test fuzzy matching | ⬜ |
| 12.7 | Test multi-turn conversations | ⬜ |
| 12.8 | Test intent disambiguation | ⬜ |
| 12.9 | Test router orchestration | ⬜ |
| 12.10 | Test all unit tests pass | ⬜ |

### Day 13: Documentation

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 13.1 | Document all intent types | `orbit-agent/docs/INTENTS_REFERENCE.md` | ⬜ |
| 13.2 | Create pattern examples | `orbit-agent/docs/INTENT_PATTERNS.md` | ⬜ |
| 13.3 | Update CLAUDE.md with intents info | `orbit-agent/CLAUDE.md` | ⬜ |
| 13.4 | Update README with intent capabilities | `orbit-agent/README.md` | ⬜ |
| 13.5 | Create troubleshooting guide | `orbit-agent/docs/INTENTS_TROUBLESHOOTING.md` | ⬜ |
| 13.6 | Add examples to docs | `orbit-agent/docs/INTENT_EXAMPLES.md` | ⬜ |
| 13.7 | Document confidence scoring | `orbit-agent/docs/INTENTS_CONFIDENCE.md` | ⬜ |
| 13.8 | Document parameter extraction | `orbit-agent/docs/INTENTS_PARAMETERS.md` | ⬜ |

---

## Success Criteria

### Enhanced Intents System is Complete When:

**Intent Definitions:**
☐ All domain intents defined (Jira, Git, File, Web)
☐ Granular intents for each domain
☐ Parameters defined for each intent type
☐ Intent enums compile

**Parser:**
☐ EnhancedIntentParser created
☐ All patterns registered
☐ Fuzzy matching works
☐ Parameter extraction works
☐ Confidence scoring works
☐ Multi-turn support works

**Classifier Node:**
☐ EnhancedClassifier node created
☐ Integrates with parser
☐ Returns intent and parameters
☐ Confidence score tracked
☐ Node integrates with graph

**Routers:**
☐ Domain-specific routers created
☐ execute_intent implemented
☐ Orchestrator coordinates routers
☐ Fallback routing works
☐ Caching implemented

**Testing:**
☐ All intent patterns tested
☐ Parameter extraction tested
☐ Multi-turn conversations tested
☐ Router orchestration tested
☐ All unit tests pass

**Documentation:**
☐ All intents documented
☐ Patterns documented with examples
☐ CLAUDE.md updated
☐ README updated
☐ Troubleshooting guide created

---

## 📊 Total Progress

```
Phase 1: Intent Definitions      ░░░░░░░   0/26 steps
Phase 2: File & Web Intents  ░░░░░░░   0/18 steps
Phase 3: Enhanced Parser      ░░░░░░░   0/20 steps
Phase 4: Classifier Node       ░░░░░░░   0/10 steps
Phase 5: Domain Routers        ░░░░░░░   0/17 steps
Phase 6: Testing & Docs        ░░░░░░░   0/18 steps
────────────────────────────────────────────
Total                             ░░░░░░░   0/109 steps
```

---

## Example Intents

### Jira Domain:
```
"what tickets do I have?" → LIST_TICKETS
"show me ticket TDX-300" → GET_TICKET_DETAILS (key: TDX-300)
"I finished TDX-300" → COMPLETE_TICKET (key: TDX-300)
"add note to TDX-300: fixed in prod" → ADD_COMMENT (key: TDX-300, comment)
"what did I work on today?" → DAILY_SUMMARY
"generate my daily report" → DAILY_REPORT
```

### Git Domain:
```
"show git status" → GIT_STATUS
"commit changes" → GIT_COMMIT
"push to main" → GIT_PUSH
"create branch feature-xyz" → GIT_CREATE_BRANCH
"show me the recent commits" → GIT_SHOW_LOG
```

### File Domain:
```
"read package.json" → FILE_READ (path: package.json)
"create utils folder" → FILE_CREATE_DIR (path: utils)
"delete temp.py" → FILE_DELETE (path: temp.py)
"list files in src" → FILE_LIST (path: src)
```

### Web Search Domain:
```
"search for python asyncio" → WEB_SEARCH
"what's the latest AI news?" → WEB_SEARCH_NEWS
"is it true that Earth is flat?" → WEB_VERIFY_FACT
```

---

## Next Steps After Enhanced Intents

1. ✅ Review this plan and approve
2. ⏭️ Start with Phase 1: Intent Definitions
3. ⏭️ Implement Phase 2: File & Web Intents
4. ⏭️ Implement Phase 3: Enhanced Parser
5. ⏭️ Implement Phase 4: Classifier Node
6. ⏭️ Implement Phase 5: Domain Routers
7. ⏭️ Implement Phase 6: Testing & Documentation
8. ⏭️ Test end-to-end
9. ⏭️ Deploy to environment

---

**Ready to build enhanced intent system? Let's go!** 🎯
