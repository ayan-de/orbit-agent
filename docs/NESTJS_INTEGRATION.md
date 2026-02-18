# NestJS Bridge ↔ Python Agent Integration

## Overview

This document explains how the NestJS Bridge integrates with the Python Orbit Agent to enable NLP command translation.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Telegram   │     │   NestJS Bridge   │     │ Python Agent  │
│   User       │────▶│                  │────▶│              │
└─────────────┘     │                  │     │              │
                     │                  │     └──────────────┘
                     │                  │           ▲
                     └──────────────────┘           │
                          │                      │
                          ▼                      │
                      ┌──────────────┐             │
                      │ Desktop TUI  │─────────────┘
                      └──────────────┘
```

## Data Flow

### User Types "what is my current directory?"

1. **Telegram** → NestJS Bridge receives message
2. **NestJS Bridge** → Sends to Python Agent (`/api/v1/agent/invoke`)
3. **Python Agent**:
   - Classifies intent as "command"
   - Translates to shell command: `pwd`
   - Returns response with `command: "pwd"`
4. **NestJS Bridge** → Extracts command from agent response
5. **NestJS Bridge** → Sends `pwd` to Desktop TUI
6. **Desktop TUI** → Executes `pwd` → Returns `/home/user/projects`
7. **NestJS Bridge** → Sends result back to Telegram

### User Types "how do I use git?"

1. **Telegram** → NestJS Bridge receives message
2. **NestJS Bridge** → Sends to Python Agent
3. **Python Agent**:
   - Classifies intent as "question"
   - Generates direct answer
   - Returns response without `command`
4. **NestJS Bridge** → Sends direct answer to Telegram (no TUI execution)

## New Files Created

### NestJS Bridge

1. **`src/application/execution/interfaces/agent-service.interface.ts`**
   - `IAgentService` interface
   - `AgentResponse` DTO
   - `AgentStreamEvent` for future WebSocket streaming

2. **`src/application/execution/agent.service.ts`**
   - `AgentService` implementation
   - Calls Python Agent API at `http://localhost:8000/api/v1/agent/invoke`
   - Extracts shell commands from agent responses
   - Falls back to direct execution if agent is unavailable

### Configuration

3. **`src/config/env.config.ts`** - Added `AGENT_API_URL`
4. **`.env.example`** - Added `AGENT_API_URL=http://localhost:8000`

## Modified Files

### NestJS Bridge

1. **`src/application/execution/execution.module.ts`**
   - Added `AgentService` to providers and exports
   - Imported `IAgentService` interface

2. **`src/application/execution/command-orchestrator.service.ts`**
   - Injected `IAgentService`
   - Modified `executeCommand()` to:
     - Route through agent first
     - Handle `question` intent (direct answer)
     - Handle `command` intent (execute extracted command)
     - Fallback to direct execution

## Configuration

### NestJS Bridge (.env)
```bash
# Orbit Agent API URL
AGENT_API_URL=http://localhost:8000
```

### Python Agent (.env)
```bash
# Bridge URL (for future command execution from agent)
BRIDGE_URL=http://localhost:3000
```

## Testing the Integration

### 1. Start Both Services

```bash
# Terminal 1: Start Python Agent
cd /home/ayande/Projects/bigProject/orbit-agent
source .venv/bin/activate
uvicorn src.main:app --reload

# Terminal 2: Start NestJS Bridge
cd /home/ayande/Projects/bigProject/clawdbotClone/packages/bridge
npm run start:dev
```

### 2. Test via API

```bash
# Test Python Agent directly
curl -X POST http://localhost:8000/api/v1/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "message": "what is my current directory?",
    "session_id": "test-session",
    "user_id": "test-user"
  }'
```

Expected Response:
```json
{
  "messages": ["Running: pwd"],
  "intent": "command",
  "status": "success"
}
```

### 3. Test via Telegram

Send a message to your Telegram bot:
- "what is my current directory?" → Should execute `pwd`
- "list files" → Should execute `ls`
- "how do I use git?" → Should get direct answer

## Agent Response Handling

The AgentService intelligently extracts commands from various response formats:

| Agent Response | Extracted Command |
|---------------|-------------------|
| `pwd` | `pwd` |
| ``pwd`` | `pwd` |
| `Running: pwd` | `pwd` |
| `Execute: ls -la` | `ls -la` |
| `The command is: cat file.txt` | `cat file.txt` |

## Fallback Behavior

If the Python Agent is unavailable:
- NestJS Bridge logs the error
- Falls back to executing the user's message directly
- Sends "❌ Agent unavailable. Executing as direct command." to user
- System continues to function (graceful degradation)

## Future Enhancements

1. **WebSocket Streaming**: Real-time token streaming from agent
2. **Tool Execution**: Agent directly calls bridge for tool execution
3. **Confirmation Flow**: Agent requests confirmation for dangerous commands
4. **Multi-step Workflows**: Agent manages multi-command execution

## Troubleshooting

### Agent Not Responding

Check if Python Agent is running:
```bash
curl http://localhost:8000/health
```

### Bridge Can't Connect to Agent

1. Verify `AGENT_API_URL` in NestJS `.env`
2. Check Python Agent port (default: 8000)
3. Check network connectivity between services

### Command Not Being Executed

Check NestJS logs for:
```
Agent response: intent=command, command=pwd
```

If `command` is null/undefined, the agent response format may have changed.
