# Tavily Web Search Implementation Guide

**Scope**: AI-powered web search integration using MCP tools
**Target**: Agent can search the web for current information via Tavily MCP server
**Duration**: 4-6 hours
**Last Updated**: 2026-03-02

---

## Overview

This guide focuses on integrating Tavily's AI-powered web search into Orbit Agent using MCP (Model Context Protocol) tools:
- Search the web for information using Tavily MCP server
- Provide citations and sources from search results
- AI-generated answers from Tavily
- News search capabilities
- Domain filtering options

**Implementation Approach**: Using MCP tools instead of direct API client - leveraging the standardized MCP server pattern.

---

## Phase 1: Configuration & Tool Foundation (Day 1)

**Goal**: Configure MCP server connection and create tool foundation.

### Day 1: MCP Configuration

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 1.1 | Get Tavily API key from https://tavily.com/ | - | ✅ |
| 1.2 | Add TAVILY_API_KEY to .env file | `orbit-agent/.env` | ✅ |
| 1.3 | Add Tavily config to Settings class | `orbit-agent/src/config.py` | ✅ |
| 1.4 | Create MCP client manager | `orbit-agent/src/mcp/client.py` | ✅ |
| 1.5 | Implement MCP server connection | `orbit-agent/src/mcp/client.py` | ✅ |
| 1.6 | Add Tavily MCP server config | `orbit-agent/src/mcp/config.py` | ✅ |
| 1.7 | Create WebSearchInput schema | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 1.8 | Create WebSearchTool class | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 1.9 | Set tool metadata (name, description, category) | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 1.10 | Set danger_level to 1 (safe) | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 1.11 | Set requires_confirmation to False | `orbit-agent/src/tools/web/tavily.py` | ✅ |

---

## Phase 2: MCP Tool Implementation (Days 2-3)

**Goal**: Implement Tavily MCP tool integration with proper result formatting.

### Day 2: MCP Tool Core

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 2.1 | Implement _arun method using MCP client | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 2.2 | Call Tavily search tool via MCP | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 2.3 | Add query parameter handling | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 2.4 | Add max_results parameter support | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 2.5 | Add search_depth parameter support | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 2.6 | Add error handling for MCP failures | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 2.7 | Implement format_results method | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 2.8 | Format citations from MCP response | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 2.9 | Format sources from MCP response | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 2.10 | Format AI-generated answer | `orbit-agent/src/tools/web/tavily.py` | ✅ |

### Day 3: Advanced Search & Tests

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 3.1 | Create NewsSearchInput schema | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 3.2 | Create NewsSearchTool class | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 3.3 | Implement news search via MCP | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 3.4 | Add days parameter for news search | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 3.5 | Implement format_news_results method | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 3.6 | Create unit test for web search | `orbit-agent/tests/test_tavily_integration.py` | ✅ |
| 3.7 | Create unit test for news search | `orbit-agent/tests/test_tavily_integration.py` | ✅ |
| 3.8 | Create unit test with domain filtering | `orbit-agent/tests/test_tavily_integration.py` | ✅ |
| 3.9 | Create unit test for MCP connection error | `orbit-agent/tests/test_tavily_integration.py` | ✅ |
| 3.10 | Add include_domains parameter | `orbit-agent/src/tools/web/tavily.py` | ✅ |
| 3.11 | Add exclude_domains parameter | `orbit-agent/src/tools/web/tavily.py` | ✅ |

---

## Phase 3: Integration with Agent (Days 3-4)

**Goal**: Register tool and integrate with agent workflow.

### Day 3: Tool Registration

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 4.1 | Create web module __init__.py | `orbit-agent/src/tools/web/__init__.py` | ⬜ |
| 4.2 | Export WebSearchTool from __init__.py | `orbit-agent/src/tools/web/__init__.py` | ⬜ |
| 4.3 | Export NewsSearchTool from __init__.py | `orbit-agent/src/tools/web/__init__.py` | ⬜ |
| 4.4 | Import WebSearchTool in registry | `orbit-agent/src/tools/registry.py` | ⬜ |
| 4.5 | Register WebSearchTool in get_tool_registry | `orbit-agent/src/tools/registry.py` | ⬜ |
| 4.6 | Register NewsSearchTool in get_tool_registry | `orbit-agent/src/tools/registry.py` | ⬜ |
| 4.7 | Test tool retrieval from registry | `orbit-agent/tests/tools/test_tavily.py` | ⬜ |
| 4.8 | Test tool metadata | `orbit-agent/tests/tools/test_tavily.py` | ⬜ |

### Day 4: Agent Integration

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 5.1 | Test web_search tool execution | `orbit-agent/tests/tools/test_tavily.py` | ⬜ |
| 5.2 | Verify results formatting includes citations | `orbit-agent/tests/tools/test_tavily.py` | ⬜ |
| 5.3 | Verify results include sources | `orbit-agent/tests/tools/test_tavily.py` | ⬜ |
| 5.4 | Update system prompt with web search | `orbit-agent/src/agent/prompts/system.md` | ⬜ |
| 5.5 | Document web search capability in prompt | `orbit-agent/src/agent/prompts/system.md` | ⬜ |
| 5.6 | Add usage examples to prompt | `orbit-agent/src/agent/prompts/system.md` | ⬜ |
| 5.7 | Add citation guidelines to prompt | `orbit-agent/src/agent/prompts/system.md` | ⬜ |

---

## Phase 4: MCP Server Setup & Documentation (Days 5-6)

**Goal**: Set up Tavily MCP server and document usage.

### Day 5: MCP Server Setup

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 6.1 | Add mcp_servers config section | `orbit-agent/src/config.py` | ⬜ |
| 6.2 | Configure Tavily MCP server endpoint | `orbit-agent/.env` | ⬜ |
| 6.3 | Add MCP server initialization to main.py | `orbit-agent/src/main.py` | ⬜ |
| 6.4 | Implement MCP tool discovery | `orbit-agent/src/mcp/client.py` | ⬜ |
| 6.5 | Add MCP health check endpoint | `orbit-agent/src/api/v1/health.py` | ⬜ |
| 6.6 | Test MCP server connection | `orbit-agent/tests/mcp/test_client.py` | ⬜ |
| 6.7 | Test MCP tool listing | `orbit-agent/tests/mcp/test_client.py` | ⬜ |
| 6.8 | Test MCP tool execution | `orbit-agent/tests/mcp/test_client.py` | ⬜ |

### Day 6: Documentation

| Step | Task | File(s) | Status |
|------|------|---------|--------|
| 7.1 | Update README.md with web search section | `orbit-agent/README.md` | ⬜ |
| 7.2 | Document Tavily API key setup | `orbit-agent/README.md` | ⬜ |
| 7.3 | Document MCP server configuration | `orbit-agent/docs/MCP_SETUP.md` | ⬜ |
| 7.4 | Update CLAUDE.md with web search | `orbit-agent/CLAUDE.md` | ⬜ |
| 7.5 | Create troubleshooting guide | `orbit-agent/docs/TAVILY_TROUBLESHOOTING.md` | ⬜ |
| 7.6 | Document MCP tool pattern | `orbit-agent/docs/MCP_TOOLS.md` | ⬜ |

---

## Success Criteria

### Web Search Integration is Complete When:

**Configuration:**
☐ Tavily API key configured in .env
☐ MCP server connection configured
☐ Settings class has Tavily fields
☐ Config values are appropriate

**MCP Client:**
☐ MCP client manager implemented
☐ Server connection works
☐ Tool discovery functional
☐ Error handling for connection failures

**Tool Implementation:**
☐ WebSearchTool created and registered
☐ NewsSearchTool created and registered
☐ Input schema has all required fields
☐ _arun method works correctly via MCP
☐ format_results includes citations
☐ format_results includes sources
☐ Tool metadata correct (danger_level: 1)

**Advanced Features:**
☐ Domain filtering supported (include/exclude)
☐ News search implemented
☐ max_results parameter works
☐ search_depth parameter works
☐ days parameter for news works

**Testing:**
☐ Unit tests pass
☐ MCP client tests pass
☐ Tool retrieval from registry works
☐ Error cases handled (MCP disconnect)

**Agent Integration:**
☐ Tools registered in agent
☐ System prompt updated
☐ Usage examples provided
☐ Citation guidelines documented

**Documentation:**
☐ README updated
☐ CLAUDE.md updated
☐ MCP setup documented
☐ Troubleshooting guide created
☐ MCP tool pattern documented

---

## 📊 Total Progress

```
Phase 1: Configuration & Foundation    ██████████  11/11 steps
Phase 2: MCP Tool Implementation       ██████████  21/21 steps
Phase 3: Agent Integration             ░░░░░░░   0/15 steps
Phase 4: MCP Server Setup & Docs       ░░░░░░░   0/14 steps
────────────────────────────────────────────
Total                                  ███████░░   32/61 steps
```

---

## File Structure

```
orbit-agent/
├── src/
│   ├── config.py                      # Add Tavily MCP config
│   ├── main.py                        # Initialize MCP server
│   ├── mcp/                           # NEW - MCP client module
│   │   ├── __init__.py
│   │   ├── client.py                  # MCP client manager
│   │   └── config.py                  # MCP server configurations
│   ├── tools/
│   │   ├── web/                       # NEW - Web search tools
│   │   │   ├── __init__.py
│   │   │   └── tavily.py              # Tavily search tools via MCP
│   │   └── registry.py                # Register web search tools
│   └── agent/
│       └── prompts/
│           └── system.md              # Update with web search docs
├── tests/
│   ├── tools/
│   │   └── test_tavily.py             # Tavily tool tests
│   └── mcp/                           # NEW - MCP tests
│       ├── __init__.py
│       └── test_client.py             # MCP client tests
├── docs/
│   ├── MCP_SETUP.md                   # NEW - MCP server setup guide
│   ├── MCP_TOOLS.md                   # NEW - MCP tool pattern docs
│   └── TAVILY_TROUBLESHOOTING.md      # Troubleshooting guide
└── .env                               # Add TAVILY_API_KEY
```

---

## MCP Tool Pattern

### Overview

This project uses MCP (Model Context Protocol) tools to integrate external services. Instead of implementing direct API clients, tools connect to MCP servers that provide standardized interfaces.

### Benefits

- **Standardization**: Consistent tool interface across all integrations
- **Community**: Use pre-built MCP servers (Tavily MCP server available)
- **Extensibility**: Easy to add new MCP servers
- **Maintenance**: Less code to maintain (leverages MCP server implementations)

### Pattern

1. **MCP Client** (`src/mcp/client.py`): Manages connections to MCP servers
2. **Tool Wrapper** (`src/tools/web/tavily.py`): LangChain tool that calls MCP
3. **Configuration** (`src/config.py`, `.env`): MCP server endpoints and credentials

### Adding New MCP Tools

1. Configure MCP server in `.env`
2. Add config to `src/mcp/config.py`
3. Create tool wrapper in `src/tools/`
4. Register in `src/tools/registry.py`

---

## Future Enhancements

After core features are complete, consider adding:

1. **Search Caching** - Cache results for common queries
2. **Result Reranking** - Reorder results by relevance
3. **Multi-Query** - Search multiple terms and combine
4. **Image Search** - Include visual search results
5. **Video Search** - Search YouTube and video platforms
6. **Local Results** - Combine with file search
7. **Query Suggestions** - Suggest related queries
8. **Custom MCP Server** - Wrap internal tools as MCP server

---

## Next Steps

1. ✅ Get Tavily API key from https://tavily.com/
2. ✅ Phase 1: Configuration & Tool Foundation (COMPLETED)
3. ✅ Phase 2: MCP Tool Implementation (COMPLETED)
4. ⏭️ Implement Phase 3: Agent Integration
5. ⏭️ Implement Phase 4: MCP Server Setup & Documentation
6. ⏭️ Test end-to-end
7. ⏭️ Deploy to environment

---

**Ready to build Tavily web search with MCP? Let's go!** 🔍
