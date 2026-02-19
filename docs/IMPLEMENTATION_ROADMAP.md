# 🚀 Orbit AI Agent — Implementation Roadmap

> Status: Phase 2 (In Progress)
> Last Updated: 2026-02-19

---

## All Phases Overview

| # | Phase | Timeline | Goal |
|---|-------|----------|------|
| 1 | **NLP → Shell Command** | Weeks 1-2 | User says "which dir am I in?" → runs `pwd` → responds |
| 2 | **Tools + Memory** | Weeks 3-5 | Multi-step plans, conversation history, PostgreSQL persistence |
| 3 | **Jira + Git + Email** | Weeks 6-9 | External service tools + human-in-the-loop confirmation |
| 4 | **Memory + RAG** | Weeks 10-13 | Long-term memory, project indexing, semantic search (pgvector) |
| 5 | **Autonomous Workflows** | Weeks 14-17 | Full end-to-end workflows, sub-graphs, error recovery |
| 6 | **Testing Suite** | Weeks 18-20 | Comprehensive test coverage (unit, integration, e2e) |
| 7 | **Documentation & CLI** | Weeks 21-22 | Complete docs and developer tooling |
| 8 | **DevOps & CI/CD** | Weeks 23-24 | Automated testing, building, deployment pipeline |

---

## Phase 1: NLP → Shell Command (Weeks 1-2)

**Goal**: User says "which directory am I in?" → agent translates to `pwd` → executes → responds.

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 1 | Get FastAPI server running | `src/main.py` | ✅ |
| 2 | Wire up LLM (OpenAI/Anthropic/Gemini) | `src/llm/factory.py`, `src/llm/openai.py`, `src/llm/anthropic.py`, `src/llm/gemini.py` | ✅ |
| 3 | Build Classifier Node — classify user intent | `src/agent/nodes/classifier.py`, `src/agent/prompts/classifier.py` | ✅ |
| 4 | Build Responder Node — format final response | `src/agent/nodes/responder.py`, `src/agent/prompts/responder.py` | ✅ |
| 5 | Wire minimal LangGraph (classify → respond) | `src/agent/graph.py`, `src/agent/edges.py` | ✅ |
| 6 | Build Bridge Client — HTTP to NestJS Bridge | `src/bridge/client.py`, `src/bridge/schemas.py` | ✅ |
| 7 | Build Shell Tool — NLP to shell command | `src/tools/shell.py`, `src/tools/base.py` | ✅ |
| 8 | Build Safety Classifier — block dangerous cmds | `src/utils/safety.py` | ✅ |
| 9 | Wire `/agent/invoke` endpoint | `src/api/v1/agent.py` | ✅ |

```
User Message
  → POST /api/v1/agent/invoke
    → Classifier (command / question?)
      → [command] → LLM translates to shell cmd
        → Safety check → Shell Tool → Bridge → Desktop → execute
          → Responder → return result
      → [question] → Responder → return answer
```

---

## Phase 2: Tools + Memory (Weeks 3-5)

**Goal**: Multi-step plans, conversation memory, tool registry, database persistence.

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 1 | Create DB models (agent_sessions, agent_messages, agent_tool_calls) | `src/db/models.py` | ✅ |
| 2 | Set up Alembic migrations | `alembic.ini`, `migrations/env.py`, `migrations/versions/001_initial_schema.py` | ✅ |
| 3 | Build session repository | `src/db/repositories/session_repo.py` | ✅ |
| 4 | Build message repository | `src/db/repositories/message_repo.py` | ✅ |
| 5 | Build tool call repository | `src/db/repositories/tool_call_repo.py` | ✅ |
| 6 | Build Tool Registry — auto-discover & register tools | `src/tools/registry.py`, `src/tools/base.py` | ✅ |
| 7 | Build File Operations tool | `src/tools/file_ops.py` | ✅ |
| 8 | Build Planner Node — multi-step planning | `src/agent/nodes/planner.py`, `src/agent/prompts/planner.py` | ✅ |
| 9 | Build Executor Node — generic tool executor | `src/agent/nodes/executor.py` | ✅ |
| 10 | Build Evaluator Node — evaluate results, re-plan | `src/agent/nodes/evaluator.py` | ✅ |
| 11 | Wire full StateGraph with conditional edges | `src/agent/graph.py`, `src/agent/edges.py` | ✅ |
| 12 | Build PostgreSQL Checkpointer (pause/resume) | `src/memory/checkpointer.py` | ✅ |
| 13 | Build Conversation Memory service | `src/memory/conversation.py` | ✅ |
| 14 | Add WebSocket streaming endpoint | `src/api/v1/agent.py` (WS `/agent/stream`) | ⬜ |
| 15 | Build Sessions CRUD endpoint | `src/api/v1/sessions.py` | ⬜ |
| 16 | Set up Docker Compose (agent + postgres + redis) | `docker-compose.yml`, `Dockerfile` | ⬜ |

```
User: "create a folder called test, then list its contents"
  → Classifier → intent: "workflow"
    → Planner → plan: [mkdir test, ls test]
      → Executor (step 1) → mkdir test ✅
        → Evaluator → more steps? yes
          → Executor (step 2) → ls test ✅
            → Evaluator → done
              → Responder → return results
```

---

## Phase 3: Jira + Git + Email Tools (Weeks 6-9)

**Goal**: Agent connects to external services. Human-in-the-loop for dangerous actions.

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 1 | Build Jira tool — get tickets, update status | `src/tools/jira.py` | ⬜ |
| 2 | Build Git tool — status, checkout, commit, push | `src/tools/git.py` | ⬜ |
| 3 | Build GitHub tool — list PRs, create PR | `src/tools/github.py` | ⬜ |
| 4 | Build Email tool — send/read emails | `src/tools/email.py` | ⬜ |
| 5 | Build VS Code tool — open project/file | `src/tools/vscode.py` | ⬜ |
| 6 | Build Browser tool — web scraping | `src/tools/browser.py` | ⬜ |
| 6 | Build Human Input Node — pause for confirmation | `src/agent/nodes/human_input.py` | ⬜ |
| 7 | Wire human-in-the-loop edges in graph | `src/agent/graph.py`, `src/agent/edges.py` | ⬜ |
| 8 | Build Auth middleware — JWT/API-key verification | `src/api/middleware/auth.py` | ⬜ |
| 9 | Build Rate Limiting middleware | `src/api/middleware/rate_limit.py` | ⬜ |
| 10 | Build Request/Response logging middleware | `src/api/middleware/logging.py` | ⬜ |
| 11 | Build Tools listing endpoint | `src/api/v1/tools.py` | ⬜ |
| 12 | Add tool-specific env vars (JIRA_TOKEN, etc.) | `src/config.py`, `.env.example` | ⬜ |
| 13 | Register all new tools in registry | `src/tools/registry.py` | ⬜ |

```
User: "check my Jira tickets and push the current branch"
  → Planner → plan: [jira_get_my_tickets, git_push]
    → Executor → jira_get_my_tickets ✅ (3 tickets found)
      → Evaluator → next step is git_push (high risk!)
        → Human Input → "⚠️ Push to main? Confirm."
          → User: "yes"
            → Executor → git_push ✅
              → Responder → return results
```

---

## Phase 4: Memory + RAG (Weeks 10-13)

**Goal**: Agent remembers past sessions, knows your projects, semantic search.

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 1 | Build Conversation Summarizer | `src/memory/summary.py` | ⬜ |
| 2 | Set up pgvector extension in PostgreSQL | `migrations/versions/xxx_add_pgvector.py` | ⬜ |
| 3 | Create embeddings table + vector index | `src/db/models.py` (Embedding model) | ⬜ |
| 4 | Build Embedding service — generate & store embeddings | `src/memory/embeddings.py` | ⬜ |
| 5 | Build Project Indexer — index file trees, READMEs | `src/memory/indexer.py` | ⬜ |
| 6 | Build Context Retrieval Node — inject context before LLM | `src/agent/nodes/context_retriever.py` | ⬜ |
| 7 | Wire context retrieval into graph | `src/agent/graph.py` | ⬜ |
| 8 | Auto-summarize long conversations on session end | `src/memory/conversation.py` | ⬜ |
| 9 | Build semantic search endpoint | `src/api/v1/search.py` | ⬜ |
| 10 | Index Jira tickets & emails for RAG | `src/memory/indexer.py` | ⬜ |

```
User: "what was I working on last week?"
  → Context Retriever → searches embeddings for recent activity
    → Found: "auth module refactor", "PROJ-456 bug fix"
      → Responder → "Last week you worked on the auth module
                      refactor and fixed PROJ-456."
```

---

## Phase 5: Autonomous Workflows (Weeks 14-17)

**Goal**: Agent executes full end-to-end workflows automatically.

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 1 | Build Workflow Template system | `src/workflows/templates.py` | ⬜ |
| 2 | Create "Fix Jira Ticket" workflow template | `src/workflows/fix_ticket.py` | ⬜ |
| 3 | Create "Code Review" workflow template | `src/workflows/code_review.py` | ⬜ |
| 4 | Create "Deploy" workflow template | `src/workflows/deploy.py` | ⬜ |
| 5 | Build Sub-graph system — nested LangGraph graphs | `src/agent/subgraphs/`, `src/agent/subgraphs/__init__.py` | ⬜ |
| 6 | Build Error Recovery — auto-retry, rollback, fallback | `src/utils/retry.py`, `src/agent/nodes/error_handler.py` | ⬜ |
| 7 | Build Parallel Tool Execution | `src/agent/nodes/parallel_executor.py` | ⬜ |
| 8 | Build Workflow trigger detection in classifier | `src/agent/nodes/classifier.py` | ⬜ |
| 9 | Build Workflow status tracking & reporting | `src/api/v1/workflows.py` | ⬜ |
| 10 | End-to-end testing for all workflow templates | `tests/e2e/test_full_pipeline.py` | ⬜ |

```
User: "fix PROJ-123 and push"
  → Classifier → intent: "workflow" (fix_ticket template)
    → Jira: read PROJ-123 details
      → Git: checkout fix/PROJ-123
        → LLM: analyze code + apply fix
          → Shell: run tests ✅
            → Git: commit "fix: PROJ-123 resolved"
              → Git: push
                → Jira: update status → "Done"
                  → Responder → "PROJ-123 fixed, pushed, and closed."
```

---

## Phase 6: Testing Suite (Weeks 18-20)

**Goal**: Comprehensive test coverage for reliability and confidence in deployments.

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 1 | Set up pytest configuration with fixtures | `pytest.ini`, `tests/conftest.py` | ⬜ |
| 2 | Mock LLM responses for unit tests | `tests/unit/mocks/mock_llm.py`, `tests/conftest.py` | ⬜ |
| 3 | Write unit tests for all nodes | `tests/unit/test_classifier.py`, `tests/unit/test_planner.py`, `tests/unit/test_executor.py`, `tests/unit/test_evaluator.py` | ⬜ |
| 4 | Write unit tests for tools | `tests/unit/test_tools/test_shell.py`, `tests/unit/test_tools/test_jira.py`, `tests/unit/test_tools/test_git.py` | ⬜ |
| 5 | Write integration tests for agent flows | `tests/integration/test_agent_flow.py` | ⬜ |
| 6 | Write integration tests for API endpoints | `tests/integration/test_api.py` | ⬜ |
| 7 | Write integration tests for database layer | `tests/integration/test_db.py` | ⬜ |
| 8 | Write e2e tests for full pipeline | `tests/e2e/test_full_pipeline.py` | ⬜ |
| 9 | Write tests for error recovery and retry logic | `tests/unit/test_retry.py`, `tests/e2e/test_error_recovery.py` | ⬜ |
| 10 | Set up test database with fixtures | `tests/fixtures/test_db.sql`, `tests/fixtures/seed_data.py` | ⬜ |
| 11 | Configure test coverage reporting | `.coveragerc`, `Makefile` (test-coverage target) | ⬜ |
| 12 | Set up pre-commit hooks (ruff, mypy, tests) | `.pre-commit-config.yaml` | ⬜ |

---

## Phase 7: Documentation & CLI Tools (Weeks 21-22)

**Goal**: Complete documentation for users and developers, useful CLI tools.

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 1 | Write API documentation (OpenAPI/Swagger) | Auto-generated via FastAPI, customize descriptions | ⬜ |
| 2 | Write Developer Setup Guide | `docs/DEVELOPER_SETUP.md` | ⬜ |
| 3 | Write Deployment Guide | `docs/DEPLOYMENT.md` | ⬜ |
| 4 | Write Tool Development Guide | `docs/TOOL_DEVELOPMENT.md` | ⬜ |
| 5 | Write Workflow Template Guide | `docs/WORKFLOW_TEMPLATES.md` | ⬜ |
| 6 | Write Troubleshooting Guide | `docs/TROUBLESHOOTING.md` | ⬜ |
| 7 | Update README with quick start and architecture | `README.md` | ⬜ |
| 8 | Build CLI tool for testing agent without API | `scripts/run_agent_cli.py` | ⬜ |
| 9 | Build database seed script for development | `scripts/seed_db.py` | ⬜ |
| 10 | Build database reset/clean script | `scripts/reset_db.py` | ⬜ |
| 11 | Build migration management script helpers | `Makefile` (migrate, rollback, upgrade targets) | ⬜ |

---

## Phase 8: DevOps & CI/CD (Weeks 23-24)

**Goal**: Automated testing, building, and deployment pipeline.

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 1 | Set up GitHub Actions workflow for CI | `.github/workflows/ci.yml` | ⬜ |
| 2 | Configure automated testing on PRs | `.github/workflows/ci.yml` | ⬜ |
| 3 | Configure automated linting and type checking | `.github/workflows/ci.yml` | ⬜ |
| 4 | Set up GitHub Actions workflow for CD | `.github/workflows/cd.yml` | ⬜ |
| 5 | Configure Docker multi-stage build | `Dockerfile` (production optimized) | ⬜ |
| 6 | Configure Kubernetes/Helm charts (optional) | `k8s/`, `helm/orbit-agent/` | ⬜ |
| 7 | Set up secrets management | `.env.example`, documentation | ⬜ |
| 8 | Configure production health checks | `src/api/v1/health.py` (enhanced) | ⬜ |
| 9 | Set up monitoring and logging (Prometheus/Grafana) | `src/utils/monitoring.py`, docker-compose.yml | ⬜ |
| 10 | Configure backup strategy for PostgreSQL | docker-compose.yml, backup scripts | ⬜ |
| 11 | Set up deployment to production environment | Documentation + scripts | ⬜ |

---

## 📊 Total Progress

\`\`\`
Phase 1  █████████████   9/9   NLP → Shell
Phase 2  █████████░░░   8/16  Tools + Memory
Phase 3  ░░░░░░░░░   0/14  Jira, Git, Email
Phase 4  ░░░░░░░░░   0/10  Memory + RAG
Phase 5  ░░░░░░░░   0/10  Autonomous Workflows
Phase 6  ░░░░░░░░   0/12  Testing Suite
Phase 7  ░░░░░░░░   0/11  Documentation & CLI
Phase 8  ░░░░░░░░   0/11  DevOps & CI/CD
─────────────────────────────
Total    ███░░░░░░   17/93  steps
\`\`\`
