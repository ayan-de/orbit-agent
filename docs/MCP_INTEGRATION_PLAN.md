# MCP Tool Integration Implementation Plan

## Overview

**Problem:** Orbit-agent has a fragmented tool system where MCP tools are not integrated with the main ToolRegistry. Tools require manual wrapper classes, and there's no dynamic loading or intelligent routing.

**Solution:** Implement chat-automation patterns to create a unified, production-ready MCP tool integration system with:
- YAML-based integration definitions
- Intelligent request classification (regex + LLM fallback)
- Pre-warmed tool registry for performance
- Dynamic tool loading from MCP servers

**Outcome:** Zero-code tool additions, 5-15s faster requests, unified tool interface, production-ready architecture.

---

## Phase 1: Integration Configuration System (Priority: HIGH)

**Goal:** Define integration configurations in YAML for declarative tool management.

**Files to Create:**
- `src/integrations/config.py` - Configuration dataclass with pattern matching helpers
- `src/integrations/integration_config.yaml` - YAML definitions for all integrations
- `src/integrations/__init__.py` - Package exports

**Key Components:**
- `IntegrationConfig` dataclass with fields for tool names, display info, auth requirements, regex patterns, keywords, and hints
- YAML loader function to parse integration definitions
- Pattern and keyword matching methods for classification

**Integrations Defined:**
- Web Search (Tavily)
- Gmail, Google Docs, Google Sheets, Google Calendar, Google Drive
- Notion
- GitHub
- Slack
- File Operations (native)
- Shell (native)

---

## Phase 2: Integration Registry (Priority: HIGH)

**Goal:** Create a singleton registry to pre-warm and cache MCP tools at startup.

**Files to Create:**
- `src/integrations/registry.py` - IntegrationRegistry class

**Key Components:**
- Singleton pattern with global registry instance
- Pre-warming of all MCP integrations at startup for instant access
- Tool-to-integration reverse mapping
- Filtered toolset retrieval by integration name
- Planner/executor hints aggregation

**Methods:**
- `load_all()` - Pre-warm all integrations at startup
- `load_missing_servers()` - Incrementally load servers for new tokens
- `get_toolset()` - Instant filtered tool retrieval
- `get_integration_for_tool()` - Reverse lookup
- `get_hints()` - Get planner/executor hints for active integrations

---

## Phase 3: Integration Classifier (Priority: HIGH)

**Goal:** Intelligently classify which integrations a request needs using regex + LLM fallback.

**Files to Create:**
- `src/integrations/classifier.py` - IntegrationClassifier class

**Key Components:**
- `IntegrationIndex` - Metadata for fast classification
- `ClassificationResult` - Result with integrations, scores, method, and confidence
- `IntegrationClassifier` - Main classifier with tiered approach

**Classification Flow:**
1. **Phase 1: Regex patterns** - Fast pattern matching (confidence > 0.8 returns immediately)
2. **Phase 2: LLM classification** - Gemini Flash fallback for ambiguous requests
3. **Phase 3: Fallback** - Default to web_search with low confidence

**Why Gemini Flash:** Fast and cheap for classification tasks

---

## Phase 4: Smart Router Node (Priority: HIGH)

**Goal:** Insert a routing node before planner to classify and load needed tools.

**Files to Create/Modify:**
- `src/agent/nodes/smart_router.py` - NEW smart router node
- `src/agent/graph.py` - MODIFY to add smart_router before planner
- `src/agent/edges.py` - MODIFY for new routing logic

**Smart Router Flow:**
1. Extract user request from messages
2. Classify which integrations are needed
3. Check auth requirements for needed integrations
4. Get toolset from registry (instant lookup)
5. Bind tools to executor LLM
6. Return state update with loaded tools

**Graph Integration:**
```
START → smart_router → [planner | END (if auth required)]
                    → planner → executor → evaluator → [executor | responder]
```

---

## Phase 5: Enhanced MCP Client (Priority: MEDIUM)

**Goal:** Enhance MCP client with stdio transport, auto-registration, and retry logic.

**Files to Modify:**
- `src/mcp/client.py`

**Additions:**
1. **stdio transport support** - Connect to local MCP servers via subprocess
2. **Tool auto-registration** - Discover tools from MCP servers and wrap as OrbitTool instances
3. **Retry with exponential backoff** - Handle transient failures gracefully

**Benefits:**
- Support for local MCP servers (like Notion, GitHub CLIs)
- Automatic tool discovery without manual wrappers
- More resilient tool execution

---

## Phase 6: MCP Tool Wrapper (Priority: MEDIUM)

**Goal:** Create dynamic tool wrapper that converts MCP tool schemas to OrbitTool instances.

**Files to Create:**
- `src/tools/mcp_wrapper.py` - MCPToolWrapper class

**Key Components:**
- Auto-generated OrbitTool from MCP tool JSON Schema
- Dynamic Pydantic model creation from input schema
- Server name and MCP client references
- Result formatting

**Benefits:**
- Zero-code tool additions - just add to YAML
- Automatic schema validation
- Consistent tool interface across all MCP tools

---

## Phase 7: State Updates (Priority: MEDIUM)

**Goal:** Add integration tracking fields to agent state.

**Files to Modify:**
- `src/agent/state.py`

**New Fields:**
- `loaded_integrations` - List of active integration names
- `auth_required_integrations` - Integrations needing authentication
- `total_tool_count` - Number of tools loaded for current request
- `executor_tools` - Dynamically bound tools for executor

---

## File Structure After Implementation

```
orbit-agent/src/
├── integrations/
│   ├── __init__.py
│   ├── config.py              # IntegrationConfig dataclass
│   ├── integration_config.yaml # YAML definitions
│   ├── registry.py            # IntegrationRegistry singleton
│   └── classifier.py          # IntegrationClassifier
├── tools/
│   ├── base.py               # OrbitTool (unchanged)
│   ├── registry.py           # ToolRegistry (enhanced)
│   ├── mcp_wrapper.py        # MCPToolWrapper (NEW)
│   ├── shell.py              # Native tool (unchanged)
│   └── file_ops.py           # Native tools (unchanged)
├── mcp/
│   ├── client.py             # Enhanced with stdio + auto-registration
│   └── config.py             # MCP server config (unchanged)
├── agent/
│   ├── graph.py              # Updated with smart_router
│   ├── edges.py              # Updated routing
│   ├── state.py              # New integration fields
│   └── nodes/
│       ├── smart_router.py   # NEW
│       ├── planner.py        # Enhanced with hints
│       └── executor.py       # Enhanced with dynamic tools
```

---

## Verification Plan

### Unit Tests
- Test integration config loading from YAML
- Test classifier regex and LLM classification
- Test registry tool loading and retrieval

### Integration Tests
- Test MCP tool loading and execution
- Test full workflow with smart router

### Manual Testing
- Start agent and test classification for various requests
- Verify web_search returns correct integrations
- Verify auth check for Gmail requests

---

## Migration Steps

1. **Keep existing tools working** - Don't break shell, file_ops, web_search
2. **Add new integration system** - Create parallel to existing registry
3. **Migrate Tavily** - Move from hardcoded wrapper to YAML config
4. **Add smart router** - Insert before planner in graph
5. **Test thoroughly** - Verify all existing functionality works
6. **Add new integrations** - Gmail, Notion, etc. via YAML

---

## Critical Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `src/integrations/__init__.py` | Create | Package init |
| `src/integrations/config.py` | Create | IntegrationConfig dataclass |
| `src/integrations/integration_config.yaml` | Create | Integration definitions |
| `src/integrations/registry.py` | Create | IntegrationRegistry singleton |
| `src/integrations/classifier.py` | Create | IntegrationClassifier |
| `src/agent/nodes/smart_router.py` | Create | Smart router node |
| `src/tools/mcp_wrapper.py` | Create | MCPToolWrapper class |
| `src/agent/graph.py` | Modify | Add smart_router node |
| `src/agent/edges.py` | Modify | Add routing logic |
| `src/agent/state.py` | Modify | Add integration fields |
| `src/mcp/client.py` | Modify | Add stdio + auto-registration |
| `src/tools/registry.py` | Modify | Add MCP tool integration |
