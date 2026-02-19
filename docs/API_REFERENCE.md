# Orbit AI Agent API Reference

Complete API documentation for Orbit AI Agent microservice.

---

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently no authentication is required. JWT/API-key authentication will be added in Phase 3.

---

## Agent Endpoints

### POST /agent/invoke

Invoke the Orbit Agent with a user message.

**Request:**
```json
{
  "message": "Which directory am I in?",
  "session_id": "session_123",
  "user_id": "user_456"
}
```

**Response:**
```json
{
  "messages": ["You are in /home/user/projects"],
  "intent": "command",
  "command": "pwd",
  "status": "success"
}
```

### WebSocket /agent/stream

Real-time streaming of agent execution.

**Connect URL:**
```
ws://localhost:8000/ws/api/v1/agent/stream
```

**Send Message:**
```json
{
  "session_id": "session_123",
  "user_id": "user_456",
  "message": "What files are in the current directory?"
}
```

**Events Streamed:**

- `start`: Execution started
- `intent`: Intent classification result
- `plan`: Generated execution plan
- `step`: Current execution step (step, total_steps)
- `tool_result`: Result from tool execution
- `evaluation`: Evaluation outcome with reasoning
- `chunk`: Streaming message content (for streaming effect)
- `complete`: Execution finished
- `error`: Error occurred

**Example Events:**
```json
{"type": "start", "session_id": "session_123", "timestamp": "2024-01-01T00:00:00Z"}
{"type": "intent", "intent": "workflow", "timestamp": "2024-01-01T00:00:01Z"}
{"type": "plan", "plan": {"goal": "...", "steps": [...]}, "timestamp": "2024-01-01T00:00:02Z"}
{"type": "step", "step": 1, "total_steps": 3, "timestamp": "2024-01-01T00:00:03Z"}
{"type": "tool_result", "result": {...}, "timestamp": "2024-01-01T00:00:04Z"}
{"type": "chunk", "content": "Here is", "timestamp": "2024-01-01T00:00:05Z"}
{"type": "chunk", "content": " the result", "timestamp": "2024-01-01T00:00:06Z"}
{"type": "complete", "session_id": "session_123", "timestamp": "2024-01-01T00:00:07Z"}
```

### WebSocket /agent/stream/checkpoint

Streaming with pause/resume support using checkpoints.

**Connect URL:**
```
ws://localhost:8000/ws/api/v1/agent/stream/checkpoint
```

**Send Message:**
```json
{
  "session_id": "session_123",
  "user_id": "user_456",
  "message": "Continue the task",
  "checkpoint_id": "checkpoint_789"
}
```

**Events Streamed:**
- `start`: Execution started (with checkpoint info)
- `state_update`: Full state update
- `complete`: Execution finished
- `error`: Error occurred

---

## Sessions Endpoints

### POST /sessions

Create a new session.

**Request:**
```json
{
  "user_id": "user_123",
  "title": "Project Setup",
  "meta": {
    "project": "orbit-agent",
    "tags": ["setup", "initial"]
  }
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_123",
  "title": "Project Setup",
  "status": "active",
  "meta": {
    "project": "orbit-agent",
    "tags": ["setup", "initial"]
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "message_count": 0
}
```

### GET /sessions

List sessions for a user with optional filters.

**Query Parameters:**
- `user_id` (required): User identifier
- `status_filter` (optional): Filter by status (`active`, `archived`, `deleted`)
- `limit` (optional, default 10): Maximum sessions to return (1-100)
- `offset` (optional, default 0): Pagination offset
- `days` (optional): Only return sessions from last N days (1-365)

**Example Request:**
```
GET /api/v1/sessions?user_id=user_123&status=active&limit=10&days=7
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user_123",
    "title": "Project Setup",
    "status": "active",
    "meta": {},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "message_count": 15
  }
]
```

### GET /sessions/recent

Get recent sessions for a user.

**Query Parameters:**
- `user_id` (required): User identifier
- `limit` (optional, default 10): Maximum sessions to return (1-50)
- `days` (optional, default 7): Days to look back (1-90)

**Example Request:**
```
GET /api/v1/sessions/recent?user_id=user_123&limit=10&days=7
```

### GET /sessions/{session_id}

Get a session by ID.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_123",
  "title": "Project Setup",
  "status": "active",
  "meta": {},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "message_count": 15
}
```

### PATCH /sessions/{session_id}

Update a session (title or status).

**Request:**
```json
{
  "title": "Updated Title",
  "status": "archived"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_123",
  "title": "Updated Title",
  "status": "archived",
  "meta": {},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### POST /sessions/{session_id}/archive

Archive a session (mark status as `archived`).

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_123",
  "title": "Project Setup",
  "status": "archived",
  "meta": {},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### DELETE /sessions/{session_id}

Delete a session.

**Query Parameters:**
- `soft_delete` (optional, default true): Mark as deleted instead of removing

**Response:**
```json
{
  "message": "Session deleted successfully",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "soft_delete": true
}
```

---

## Messages Endpoints

### GET /sessions/{session_id}/messages

Get messages for a session.

**Query Parameters:**
- `limit` (optional): Maximum messages to return (1-1000)
- `role_filter` (optional): Filter by role (`user`, `assistant`, `system`, `tool`)

**Example Request:**
```
GET /api/v1/sessions/{session_id}/messages?limit=50&role_filter=user
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "role": "user",
    "content": "Which directory am I in?",
    "meta": {},
    "created_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "role": "assistant",
    "content": "You are in /home/user/projects",
    "meta": {},
    "created_at": "2024-01-01T00:00:01Z"
  }
]
```

### POST /sessions/{session_id}/messages

Add a message to a session.

**Query Parameters:**
- `role` (required): Message role (`user`, `assistant`, `system`, `tool`)
- `content` (required): Message content
- `meta` (optional): Optional metadata as JSON

**Example Request:**
```
POST /api/v1/sessions/{session_id}/messages?role=user&content=Hello world&meta={"source":"api"}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "user",
  "content": "Hello world",
  "meta": {
    "source": "api"
  },
  "created_at": "2024-01-01T00:00:02Z"
}
```

### GET /sessions/{session_id}/summary

Get a conversation summary for a session.

**Query Parameters:**
- `max_messages` (optional, default 20): Maximum messages to include in summary (5-100)

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "summary": "The user worked on setting up a new Orbit Agent project. They initialized the database, created the basic agent structure, and tested the shell command execution. The user encountered an error with enum type conflicts which was resolved by prefixing enum types."
}
```

### POST /sessions/{session_id}/compress

Compress session by summarizing old messages.
Keeps recent messages intact and replaces old messages with a summary.

**Query Parameters:**
- `max_messages` (optional, default 20): Maximum messages to keep uncompressed (5-100)

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_count": 5,
  "status": "compressed"
}
```

---

## Health Endpoints

### GET /

Root health check.

**Response:**
```json
{
  "service": "Orbit AI Agent",
  "version": "0.1.0",
  "status": "running"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "llm_provider": "openai"
}
```

---

## WebSocket Message Flow

### Basic Streaming Flow

```
Client                              Server
  |                                    |
  |------ Connect ----------------------->|
  |                                    |
  |------ Send Message -------------->|
  |                                    |
  |<----- Event: "start" ------------|
  |<----- Event: "intent" -----------|
  |<----- Event: "plan" ------------|
  |<----- Event: "step" (1/n) -------|
  |<----- Event: "tool_result" ------|
  |<----- Event: "step" (2/n) -------|
  |<----- Event: "evaluation" --------|
  |<----- Event: "chunk" x N -------|
  |<----- Event: "complete" ---------|
  |                                    |
  |------ Close ----------------------->|
```

### Checkpoint Resume Flow

```
Client                              Server
  |                                    |
  |------ Connect ----------------------->|
  |                                    |
  |------ Send Message + ID --------->|
  |                                    |
  |<----- Event: "start" ------------|
  |<----- Event: "state_update" -----|
  |<----- Event: "state_update" -----|
  |<----- Event: "state_update" -----|
  |<----- Event: "complete" ---------|
  |                                    |
  |------ Close ----------------------->|
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message here"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Successful request
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## WebSocket Client Example

### JavaScript

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/api/v1/agent/stream');

ws.onopen = () => {
  console.log('Connected to agent');

  // Send initial message
  ws.send(JSON.stringify({
    session_id: 'session_123',
    user_id: 'user_456',
    message: 'What files are in the current directory?'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'start':
      console.log('Execution started:', data.session_id);
      break;
    case 'intent':
      console.log('Intent:', data.intent);
      break;
    case 'plan':
      console.log('Plan:', data.plan);
      break;
    case 'step':
      console.log(`Step ${data.step}/${data.total_steps}`);
      break;
    case 'tool_result':
      console.log('Tool result:', data.result);
      break;
    case 'evaluation':
      console.log('Evaluation:', data.outcome);
      break;
    case 'chunk':
      // Append streaming content
      appendToChat(data.content);
      break;
    case 'complete':
      console.log('Execution complete');
      break;
    case 'error':
      console.error('Error:', data.error);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
};
```

### Python

```python
import asyncio
import websockets
import json

async def stream_agent():
    uri = "ws://localhost:8000/ws/api/v1/agent/stream"

    async with websockets.connect(uri) as websocket:
        # Send message
        message = {
            "session_id": "session_123",
            "user_id": "user_456",
            "message": "What files are in the current directory?"
        }
        await websocket.send(json.dumps(message))

        # Receive events
        async for event in websocket:
            data = json.loads(event)

            if data["type"] == "start":
                print(f"Started: {data['session_id']}")
            elif data["type"] == "intent":
                print(f"Intent: {data['intent']}")
            elif data["type"] == "chunk":
                print(f"Chunk: {data['content']}", end="", flush=True)
            elif data["type"] == "complete":
                print("\nComplete!")
            elif data["type"] == "error":
                print(f"Error: {data['error']}")

asyncio.run(stream_agent())
```

---

## Rate Limiting

Rate limiting is not yet implemented. It will be added in Phase 3.

---

## Version

Current API Version: `0.1.0`

See [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) for planned features.
