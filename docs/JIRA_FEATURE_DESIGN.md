# 🎫 Jira Tool Feature Design

> Status: Planning Phase
> Last Updated: 2026-02-27

---

## Table of Contents

1. [Overview](#overview)
2. [Use Cases](#use-cases)
3. [Architecture](#architecture)
4. [Database Schema](#database-schema)
5. [API Design](#api-design)
6. [LangGraph Integration](#langgraph-integration)
7. [Authentication Flow](#authentication-flow)
8. [Autonomous Workflows](#autonomous-workflows)
9. [Security Considerations](#security-considerations)
10. [Technology Stack](#technology-stack)
11. [Implementation Roadmap](#implementation-roadmap)
12. [MCP/RAG Assessment](#mcprag-assessment)

---

## Overview

The Jira Tool enables users to interact with their Jira tickets through natural language. It features:

- **Jira OAuth 2.0 / API Token integration** for secure authentication
- **Ticket querying** - list, search, and filter tickets
- **Ticket operations** - update status, add comments, transition workflows
- **Daily summaries** - automated summaries of assigned tickets and completed work
- **Autonomous notifications** - proactive alerts about new ticket assignments
- **Connected services UI** - show Jira connection status in Next.js profile
- **Cross-tool integration** - Jira data can be used in emails, reports, etc.

**Design Philosophy**: Keep the database lightweight. Store only essential connection information and cache tickets temporarily. Most data should be fetched directly from Jira API when needed.

---

## Use Cases

### 1. List Assigned Tickets
```
User: "show me my tickets"
→ Agent: Fetches tickets assigned to user from Jira
→ Response: Lists 5 tickets:
  - TDX-300: Fix login bug (In Progress, High priority)
  - TDX-201: Update API docs (To Do, Medium)
  - TDX-145: Add dark mode (Done, Low)
  ...
```

### 2. Summary of Today's Tickets
```
User: "what's my summary for today?"
→ Agent: Fetches all tickets assigned to user
→ LLM generates comprehensive summary:

  Today's Work Summary:
  =====================
  In Progress (3):
  - TDX-300: Fix login bug on mobile devices
    Description: Users reporting login failures on iOS Safari
    Priority: High, Due: 2026-02-28

  - TDX-205: Implement user profile caching
    Description: Cache user data to reduce API calls
    Priority: Medium, Due: 2026-03-01

  - TDX-198: Refactor authentication middleware
    Description: Simplify auth flow and add logging
    Priority: Low, Due: 2026-03-05

  Backlog (7):
  - TDX-201: Update API documentation
  - TDX-187: Add unit tests for email service
  ...
```

### 3. Daily Task Completion Summary
```
User: "i finished my ticket TDX-300, TDX-201"
→ Agent:
  1. Fetches details for TDX-300 and TDX-201
  2. Generates work summary:
     Today's Completed Tasks:
     ======================
     ✅ TDX-300: Fix login bug on mobile devices
        - Fixed authentication token handling
        - Added mobile device detection
        - Tested on iOS Safari and Chrome
        - Status moved to "Done"

     ✅ TDX-201: Update API documentation
        - Updated 15 endpoint docs
        - Added request/response examples
        - Fixed typos in authentication section
        - Status moved to "Done"

  3. Offers to send summary via email
  → "Would you like me to email this summary to your manager?"
```

### 4. Update Ticket Status
```
User: "move TDX-300 to done and add comment 'fixed the mobile issue'"
→ Agent: Updates TDX-300 status to "Done"
→ Adds comment: "fixed the mobile issue"
→ Response: "TDX-300 moved to Done. Comment added."
```

### 5. Search Tickets by Keywords
```
User: "find all tickets related to authentication"
→ Agent: Searches Jira for tickets with "authentication" in summary/description
→ Response: Found 8 tickets:
  - TDX-300: Fix login bug (In Progress)
  - TDX-198: Refactor authentication middleware (To Do)
  - TDX-156: Add OAuth2 support (Backlog)
  ...
```

### 6. Create New Ticket
```
User: "create a ticket: 'Add dark mode to dashboard', priority: high, assign to me"
→ Agent: Creates ticket in Jira
→ Response: "Created TDX-310: Add dark mode to dashboard (High priority, assigned to you)"
```

### 7. Get Ticket Details
```
User: "tell me about ticket TDX-300"
→ Agent: Fetches full ticket details
→ Response:
  TDX-300: Fix login bug on mobile devices
  ========================================
  Status: In Progress
  Priority: High
  Assignee: You
  Reporter: John Smith
  Created: 2026-02-20
  Due: 2026-02-28

  Description:
  Users are reporting login failures when using Safari on iOS devices.
  The issue appears to be related to token handling in mobile browsers.

  Steps to reproduce:
  1. Open app in Safari on iOS
  2. Enter credentials
  3. Click login
  4. Error: "Authentication failed"

  Comments (3):
  - Sarah (2 days ago): Can reproduce on iPhone 12
  - Mike (1 day ago): Works fine on Android Chrome
  - You (5 hours ago): Investigating token storage
```

### 8. Autonomous Notification (Future)
```
[Background webhook triggers]
New Jira webhook received: Ticket TDX-320 assigned to you by Alice
→ Agent: Proactive notification

  New Ticket Assignment Alert
  ===========================
  You were assigned ticket TDX-320 by Alice

  TDX-320: Implement search functionality
  ======================================
  Status: To Do
  Priority: High
  Due: 2026-03-02

  Description:
  Add search bar to dashboard with filters for:
  - Date range
  - Category
  - Status

  This ticket blocks TDX-340 (Dashboard release)
  =====================
  View ticket: https://jira.example.com/browse/TDX-320
```

### 9. Cross-Tool Integration - Email Report
```
User: "summarize my tickets and email it to manager@company.com"
→ Agent:
  1. Fetches user's tickets from Jira
  2. Generates summary
  3. Creates email draft with summary
  4. Shows preview
→ User: "yes send it"
→ Email sent with Jira summary
```

### 10. Filter Tickets by Status
```
User: "show me all tickets in backlog"
→ Agent: Fetches tickets with status "Backlog"
→ Response: Found 12 tickets in Backlog:
  - TDX-187: Add unit tests (Low)
  - TDX-175: Performance optimization (Medium)
  ...
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Next.js Frontend                           │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Profile Page                                                   │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │ │
│  │  │Telegram  │  │  Gmail   │  │   Jira   │                      │ │
│  │  │  ✓       │  │  ✓       │  │  ✗       │                      │ │
│  │  │[Connect] │  │[Connect] │  │[Connect] │                      │ │
│  │  └──────────┘  └──────────┘  └──────────┘                      │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
└──────────────────────────────┼───────────────────────────────────────┘
                               │ HTTP/WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         NestJS Bridge Service                        │
│  - Handles OAuth redirect callbacks                                  │
│  - Manages user sessions                                             │
│  - Receives Jira webhooks                                            │
│  - Stores tokens securely                                            │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Python Agent (FastAPI)                          │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Agent Layer (LangGraph)                                        │ │
│  │  ┌────────────┐ ┌─────────────┐ ┌─────────────┐                │ │
│  │  │Classifier  │ │JiraQuerier  │ │JiraSummarizer│               │ │
│  │  └────────────┘ └─────────────┘ └─────────────┘                │ │
│  │  ┌────────────┐ ┌─────────────┐ ┌─────────────┐                │ │
│  │  │JiraUpdater │ │TicketCreate │ │Notification  │                │ │
│  │  └────────────┘ └─────────────┘ └─────────────┘                │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Tools Layer (LangChain)                                       │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │JiraTool      │  │GmailTool     │  │BrowserTool   │         │ │
│  │  │- list_tickets│  │- send_email  │  │- web_search  │         │ │
│  │  │- get_ticket  │  │- draft_email │  │- scrape      │         │ │
│  │  │- update_ticket│              │  └──────────────┘         │ │
│  │  │- create_ticket│              │                            │ │
│  │  │- add_comment  │              │                            │ │
│  │  │- search       │              │                            │ │
│  │  └──────────────┘              │                            │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  API Layer                                                      │ │
│  │  - POST /api/v1/jira/draft                                      │ │
│  │  - GET  /api/v1/jira/status                                     │ │
│  │  - GET  /api/v1/jira/tickets                                    │ │
│  │  - POST /api/v1/jira/webhook                                   │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          PostgreSQL Database                        │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  user_jira_connections                                          │ │
│  │  - id, user_id, jira_url                                       │ │
│  │  - access_token, user_email                                    │ │
│  │  - is_connected                                                │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  jira_ticket_cache (lightweight cache)                         │ │
│  │  - id, user_id, ticket_key, ticket_data                        │ │
│  │  - cached_at, expires_at                                       │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Jira API                                     │
│  - Jira Cloud API or Jira Server API                                │
│  - OAuth 2.0 / API Token authentication                             │
│  - REST API for all ticket operations                               │
│  - Webhook support for autonomous notifications                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Design Principle: Keep It Simple

The Jira integration follows a lightweight database design:
- Store only connection information
- Use minimal caching (tickets expire quickly)
- Rely on Jira API as source of truth

### 1. user_jira_connections

```sql
CREATE TABLE user_jira_connections (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    jira_url VARCHAR(500) NOT NULL,  -- e.g., https://company.atlassian.net
    jira_email VARCHAR(255) NOT NULL,

    -- Authentication
    auth_type VARCHAR(20) NOT NULL DEFAULT 'api_token', -- 'api_token' or 'oauth'
    access_token TEXT NOT NULL,  -- API token or OAuth access token
    refresh_token TEXT NULL,     -- OAuth refresh token only
    token_expires_at TIMESTAMP NULL, -- OAuth expiry only

    -- Connection status
    is_connected BOOLEAN NOT NULL DEFAULT true,
    last_synced_at TIMESTAMP NULL,

    -- Metadata
    display_name VARCHAR(255) NULL,  -- User's Jira display name
    avatar_url VARCHAR(500) NULL,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    disconnected_at TIMESTAMP NULL,

    -- Indexes
    UNIQUE(user_id, jira_url)
);

CREATE INDEX idx_user_jira_connections_user_id ON user_jira_connections(user_id);
CREATE INDEX idx_user_jira_connections_is_connected ON user_jira_connections(is_connected);
```

### 2. jira_ticket_cache (Optional - for performance)

```sql
CREATE TABLE jira_ticket_cache (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    jira_url VARCHAR(500) NOT NULL,
    ticket_key VARCHAR(50) NOT NULL,  -- e.g., "TDX-300"

    -- Ticket data (as JSON for flexibility)
    ticket_data JSONB NOT NULL,
    -- Format: {
    --   "key": "TDX-300",
    --   "summary": "Fix login bug",
    --   "description": "...",
    --   "status": "In Progress",
    --   "priority": "High",
    --   "assignee": {"displayName": "John Doe", "email": "john@example.com"},
    --   "reporter": {"displayName": "Alice Smith"},
    --   "created": "2026-02-20T10:00:00Z",
    --   "updated": "2026-02-27T14:30:00Z",
    --   "due": "2026-02-28",
    --   "labels": ["bug", "mobile"]
    -- }

    -- Cache management
    cached_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL DEFAULT NOW() + INTERVAL '15 minutes',

    -- Indexes
    UNIQUE(user_id, jira_url, ticket_key),
    INDEX idx_jira_ticket_cache_user_id ON jira_ticket_cache(user_id),
    INDEX idx_jira_ticket_cache_expires_at ON jira_ticket_cache(expires_at)
);
```

### 3. daily_summaries (Optional - for historical tracking)

```sql
CREATE TABLE daily_summaries (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    summary_date DATE NOT NULL,

    -- Summary data
    assigned_tickets INTEGER NOT NULL DEFAULT 0,
    completed_tickets INTEGER NOT NULL DEFAULT 0,
    in_progress_tickets INTEGER NOT NULL DEFAULT 0,

    -- LLM-generated summary text
    summary_text TEXT NOT NULL,

    -- Ticket keys for reference
    ticket_keys VARCHAR(50)[] DEFAULT '{}',

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Indexes
    UNIQUE(user_id, summary_date),
    INDEX idx_daily_summaries_user_id ON daily_summaries(user_id),
    INDEX idx_daily_summaries_date ON daily_summaries(summary_date DESC)
);
```

---

## API Design

### 1. Jira Connection Management

#### `GET /api/v1/jira/status`
Get user's Jira connection status.

**Response:**
```json
{
  "is_connected": true,
  "jira_url": "https://company.atlassian.net",
  "jira_email": "user@company.com",
  "display_name": "John Doe",
  "avatar_url": "https://avatar-url...",
  "connected_at": "2026-02-20T10:30:00Z",
  "last_synced_at": "2026-02-27T14:00:00Z"
}
```

#### `POST /api/v1/jira/connect`
Connect to Jira with API token.

**Request:**
```json
{
  "jira_url": "https://company.atlassian.net",
  "jira_email": "user@company.com",
  "api_token": "abcd1234..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Jira connected successfully",
  "display_name": "John Doe"
}
```

#### `POST /api/v1/jira/disconnect`
Disconnect Jira service.

**Request:**
```json
{}
```

**Response:**
```json
{
  "success": true,
  "message": "Jira service disconnected"
}
```

### 2. Ticket Operations

#### `GET /api/v1/jira/tickets`
Get tickets assigned to user.

**Query Parameters:**
- `status`: Filter by status (optional)
- `limit`: Number of tickets to return (default 20)
- `force_refresh`: Skip cache and fetch fresh data (default false)

**Response:**
```json
{
  "tickets": [
    {
      "key": "TDX-300",
      "summary": "Fix login bug on mobile devices",
      "description": "Users are reporting login failures...",
      "status": "In Progress",
      "priority": "High",
      "assignee": {"displayName": "John Doe", "email": "john@example.com"},
      "reporter": {"displayName": "Alice Smith"},
      "created": "2026-02-20T10:00:00Z",
      "updated": "2026-02-27T14:30:00Z",
      "due": "2026-02-28"
    },
    {
      "key": "TDX-201",
      "summary": "Update API documentation",
      "status": "To Do",
      "priority": "Medium"
    }
  ],
  "total": 15,
  "cached": false
}
```

#### `GET /api/v1/jira/tickets/{key}`
Get detailed ticket information.

**Response:**
```json
{
  "key": "TDX-300",
  "summary": "Fix login bug on mobile devices",
  "description": "Users are reporting login failures when using Safari on iOS devices...",
  "status": {
    "name": "In Progress",
    "category": "IN_PROGRESS"
  },
  "priority": {
    "name": "High",
    "id": 3
  },
  "assignee": {
    "displayName": "John Doe",
    "email": "john@example.com",
    "accountId": "5b10ac8d82"
  },
  "reporter": {
    "displayName": "Alice Smith",
    "accountId": "5b10ac8d83"
  },
  "created": "2026-02-20T10:00:00Z",
  "updated": "2026-02-27T14:30:00Z",
  "due": "2026-02-28",
  "labels": ["bug", "mobile"],
  "components": ["Authentication"],
  "url": "https://company.atlassian.net/browse/TDX-300",
  "comments": [
    {
      "id": "12345",
      "author": {"displayName": "Sarah Johnson"},
      "body": "Can reproduce on iPhone 12",
      "created": "2026-02-25T10:00:00Z"
    }
  ]
}
```

#### `POST /api/v1/jira/tickets`
Create a new ticket.

**Request:**
```json
{
  "project_key": "TDX",
  "summary": "Add dark mode to dashboard",
  "description": "Implement dark mode theme...",
  "issue_type": "Task",
  "priority": "High",
  "assignee": "user@company.com"
}
```

**Response:**
```json
{
  "success": true,
  "ticket": {
    "key": "TDX-310",
    "summary": "Add dark mode to dashboard",
    "status": "To Do",
    "url": "https://company.atlassian.net/browse/TDX-310"
  }
}
```

#### `PATCH /api/v1/jira/tickets/{key}`
Update a ticket (status, assignee, etc.).

**Request:**
```json
{
  "status": "Done",
  "comment": "Fixed the mobile issue"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Ticket TDX-300 updated",
  "ticket": {
    "key": "TDX-300",
    "status": "Done"
  }
}
```

### 3. Summary & Search Operations

#### `GET /api/v1/jira/summary/daily`
Get daily summary of user's tickets.

**Query Parameters:**
- `date`: Date in YYYY-MM-DD format (default today)

**Response:**
```json
{
  "date": "2026-02-27",
  "summary": "Today's Work Summary:\n\nIn Progress (3):\n- TDX-300: Fix login bug...",
  "assigned_tickets": 15,
  "completed_today": 2,
  "in_progress": 3,
  "in_backlog": 7,
  "tickets": {
    "in_progress": [
      {
        "key": "TDX-300",
        "summary": "Fix login bug",
        "priority": "High"
      }
    ],
    "backlog": [
      {
        "key": "TDX-201",
        "summary": "Update API docs"
      }
    ]
  }
}
```

#### `GET /api/v1/jita/search`
Search tickets.

**Query Parameters:**
- `jql`: JQL query (e.g., `status = "In Progress" AND assignee = currentUser()`)
- `fields`: Comma-separated fields to return (default: key,summary,status,priority)

**Response:**
```json
{
  "tickets": [
    {
      "key": "TDX-300",
      "summary": "Fix login bug",
      "status": "In Progress",
      "priority": "High"
    }
  ],
  "total": 5,
  "jql": "status = \"In Progress\" AND assignee = currentUser()"
}
```

### 4. Webhook (for Autonomous Notifications)

#### `POST /api/v1/jira/webhook`
Receive Jira webhook events.

**Request Body (Jira webhook payload):**
```json
{
  "webhookEvent": "jira:issue_created",
  "timestamp": 1677480000000,
  "issue": {
    "key": "TDX-320",
    "fields": {
      "summary": "Implement search functionality",
      "assignee": {"accountId": "5b10ac8d82"},
      "reporter": {"displayName": "Alice Smith"},
      "status": {"name": "To Do"}
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Webhook received and processed"
}
```

---

## LangGraph Integration

### Jira-Specific Nodes

#### 1. `JiraIntentNode`
Determines if user request is Jira-related.

**File:** `src/agent/nodes/jira_intent.py`

```python
async def jira_intent_node(state: AgentState) -> AgentState:
    """Classify if request involves Jira operations."""
    # Prompt LLM to check if request involves Jira
    # Returns intent: "jira_list", "jira_summary", "jira_update", "jira_create", or "other"
```

#### 2. `JiraQuerierNode`
Fetches Jira tickets based on user request.

**File:** `src/agent/nodes/jira_querier.py`

```python
async def jira_querier_node(state: AgentState) -> AgentState:
    """
    Fetches tickets from Jira based on query parameters.

    Handles:
    - "show me my tickets"
    - "list all tickets in backlog"
    - "find tickets related to X"
    """
    # 1. Parse query parameters (status, assignee, keywords)
    # 2. Call JiraTool.list_tickets() or JiraTool.search()
    # 3. Store tickets in state
    # 4. Return ticket count
```

#### 3. `JiraSummarizerNode`
Generates natural language summaries from ticket data.

**File:** `src/agent/nodes/jira_summarizer.py`

```python
async def jira_summarizer_node(state: AgentState) -> AgentState:
    """
    Generates summaries from Jira ticket data.

    Handles:
    - "what's my summary for today?"
    - "summarize my tickets"
    - "i finished my ticket TDX-300, TDX-201"
    """
    # 1. Fetch relevant tickets from Jira
    # 2. Use LLM to generate natural language summary
    # 3. Structure summary by status/priority
    # 4. Optionally store in daily_summaries table
    # 5. Return formatted summary
```

#### 4. `JiraUpdaterNode`
Updates Jira tickets (status, comments).

**File:** `src/agent/nodes/jira_updater.py`

```python
async def jira_updater_node(state: AgentState) -> AgentState:
    """
    Updates Jira tickets based on user request.

    Handles:
    - "move TDX-300 to done"
    - "add comment 'fixed it' to TDX-300"
    - "i finished my ticket TDX-300" (updates status + generates summary)
    """
    # 1. Parse update request (ticket keys, status, comment)
    # 2. Call JiraTool.update_ticket() for each ticket
    # 3. Optionally trigger JiraSummarizerNode for completion summary
    # 4. Return update results
```

#### 5. `JiraCreatorNode`
Creates new Jira tickets.

**File:** `src/agent/nodes/jira_creator.py`

```python
async def jira_creator_node(state: AgentState) -> AgentState:
    """
    Creates new Jira tickets.

    Handles:
    - "create a ticket: 'Add dark mode', priority: high"
    - "file a bug for login issue"
    """
    # 1. Parse ticket details (summary, description, type, priority)
    # 2. Use LLM to fill in missing details
    # 3. Call JiraTool.create_ticket()
    # 4. Return new ticket key
```

#### 6. `JiraNotificationNode` (Future)
Handles autonomous notifications from webhooks.

**File:** `src/agent/nodes/jira_notification.py`

```python
async def jira_notification_node(state: AgentState) -> AgentState:
    """
    Processes Jira webhook notifications.

    Handles:
    - New ticket assignments
    - Ticket status changes
    - Comment mentions
    """
    # 1. Parse webhook payload
    # 2. Generate notification message
    # 3. Send via WebSocket to user
    # 4. Optionally trigger follow-up actions
```

### Updated State Schema

**File:** `src/agent/state.py`

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Existing fields
    messages: Annotated[list, add_messages]
    intent: str
    plan: list[str]
    current_step: int
    tool_results: dict
    session_id: str
    user_id: str

    # Email-specific fields (from email integration)
    email_draft_id: int | None
    email_needs_confirmation: bool
    email_refinement_iteration: int
    email_confirmation_prompt: str | None
    email_attachments: list[dict]

    # Jira-specific fields
    jira_tickets: list[dict]
    jira_ticket_keys: list[str]
    jira_summary: str | None
    jira_needs_confirmation: bool
    jira_confirmation_prompt: str | None
```

### Jira Workflow Graph

```
START
  ↓
[Classifier]
  ↓
[intent == "jira_*"]
  ↓
    ┌────────────────────────────┐
    │                            │
    ↓                            ↓
[JiraQuerier]               [JiraCreator]
    │                            │
    ↓                            ↓
[JiraSummarizer] ────────────→ [Responder]
    │                            │
    ↓                            ↓
[JiraUpdater]                [Responder]
    │                            │
    ↓                            ↓
[Responder]                   END
    ↓
  END
```

### Cross-Tool Workflow Example

```
START
  ↓
[Classifier] → intent: "jira_summary_email"
  ↓
[JiraQuerier] → fetch user's tickets
  ↓
[JiraSummarizer] → generate summary
  ↓
[EmailDrafter] → draft email with summary
  ↓
[EmailPreview] → show preview
  ↓
[User: "yes"]
  ↓
[EmailSender] → send email
  ↓
[Responder] → "Email sent successfully!"
  ↓
END
```

---

## Authentication Flow

### Option A: API Token (Simpler - Recommended for MVP)

#### Step 1: User generates API token in Jira

```
1. User logs in to Jira
2. Goes to Account Settings → Security → API Tokens
3. Creates new token: "Orbit AI Agent"
4. Copies token: "abcd1234..."
```

#### Step 2: User connects Jira via Next.js UI

**Next.js Component:**
```typescript
// components/JiraConnection.tsx
<form onSubmit={connectJira}>
  <input
    type="text"
    placeholder="Jira URL (e.g., https://company.atlassian.net)"
    value={jiraUrl}
    onChange={(e) => setJiraUrl(e.target.value)}
  />
  <input
    type="email"
    placeholder="Jira Email"
    value={jiraEmail}
    onChange={(e) => setJiraEmail(e.target.value)}
  />
  <input
    type="password"
    placeholder="API Token"
    value={apiToken}
    onChange={(e) => setApiToken(e.target.value)}
  />
  <button type="submit">Connect Jira</button>
</form>

async function connectJira(e) {
  e.preventDefault();
  const response = await fetch(`${API_BASE}/api/v1/jira/connect`, {
    method: 'POST',
    body: JSON.stringify({
      jira_url: jiraUrl,
      jira_email: jiraEmail,
      api_token: apiToken
    })
  });
  // Handle response...
}
```

#### Step 3: Python API validates and stores credentials

**Python Controller:**
```python
# src/api/v1/jira.py
@router.post("/connect")
async def connect_jira(
    request: JiraConnectRequest,
    user_id: str = Depends(get_current_user)
):
    # 1. Validate credentials by calling Jira API
    jira_client = JiraClient(request.jira_url, request.jira_email, request.api_token)
    user_info = await jira_client.get_current_user()

    # 2. Store encrypted credentials
    encrypted_token = encrypt_token(request.api_token)
    await jira_repo.store_connection(
        user_id=user_id,
        jira_url=request.jira_url,
        jira_email=request.jira_email,
        api_token=encrypted_token,
        display_name=user_info.displayName
    )

    return {"success": True, "display_name": user_info.displayName}
```

### Option B: OAuth 2.0 (More Secure - Recommended for Production)

Similar to Gmail OAuth flow:
1. User clicks "Connect Jira"
2. Redirect to Jira OAuth authorize endpoint
3. User approves
4. Jira redirects to NestJS Bridge with auth code
5. Exchange code for access token
6. Store encrypted tokens in database

---

## Autonomous Workflows

### Jira Webhook Integration

Jira supports webhooks that send events to your application when tickets change.

#### Setup Webhook in Jira

```bash
# Via Jira API
POST /rest/webhooks/1.0/webhook
{
  "name": "Orbit AI Agent",
  "url": "https://your-api.com/api/v1/jira/webhook",
  "events": [
    "jira:issue_created",
    "jira:issue_updated",
    "comment_created"
  ],
  "jqlFilter": "assignee = currentUser()"
}
```

#### Process Webhook in Python

**NestJS Bridge → Python Agent flow:**
```python
# src/api/v1/jira.py
@router.post("/webhook")
async def jira_webhook(webhook_data: dict):
    """
    Receive Jira webhook events.

    Events handled:
    - jira:issue_created → New ticket assigned
    - jira:issue_updated → Ticket status changed
    - comment_created → User mentioned
    """
    event_type = webhook_data.get("webhookEvent")

    if event_type == "jira:issue_created":
        await handle_new_ticket_assignment(webhook_data)
    elif event_type == "jira:issue_updated":
        await handle_ticket_update(webhook_data)
    elif event_type == "comment_created":
        await handle_comment_mention(webhook_data)

    return {"success": True}

async def handle_new_ticket_assignment(webhook_data: dict):
    """Handle new ticket assigned to user."""
    issue = webhook_data.get("issue", {})
    fields = issue.get("fields", {})

    # Generate notification
    notification = f"""
    New Ticket Assignment Alert
    =========================
    You were assigned {issue.get('key')} by {fields.get('reporter', {}).get('displayName', 'Unknown')}

    {fields.get('summary')}
    """

    # Send via WebSocket to user
    await websocket_manager.send_to_user(user_id, notification)
```

### Proactive Use Cases

#### 1. New Ticket Notification
```
[Webhook received]
→ Notification sent to user:
  "You were assigned TDX-320 by Alice"
→ User can say: "tell me more about TDX-320"
→ Agent fetches and displays full ticket details
```

#### 2. Ticket Status Change Notification
```
[Webhook: TDX-300 status changed to Done]
→ Notification:
  "TDX-300 has been moved to Done by Alice"
→ User: "update my daily summary"
→ Agent regenerates summary with completed ticket
```

#### 3. Comment Mention Notification
```
[Webhook: Alice commented on TDX-300]
→ Notification:
  "Alice mentioned you in a comment on TDX-300:
   'Can you review the fix?'"
→ User: "add comment: 'Will review tomorrow'"
→ Agent adds comment to ticket
```

---

## Security Considerations

### 1. Token Storage & Encryption

**Requirement:** Store Jira API tokens encrypted at rest.

**Implementation:**
```python
# src/utils/encryption.py (reuse from email integration)
from cryptography.fernet import Fernet

class TokenEncryption:
    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key.encode())

    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()
```

### 2. Webhook Validation

**Requirement:** Validate Jira webhook signatures.

**Implementation:**
```python
# src/utils/jira_webhook_validator.py

def verify_webhook_signature(
    payload: str,
    signature: str,
    secret: str
) -> bool:
    """Verify webhook signature from Jira."""
    # HMAC verification
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### 3. Rate Limiting

**Requirement:** Respect Jira API rate limits.

**Implementation:**
```python
# src/tools/jira/rate_limiter.py

from slowapi import Limiter

limiter = Limiter(key_func=lambda: "jira_api")

@limiter.limit("100/minute")  # Jira Cloud rate limit
async def call_jira_api(endpoint: str):
    """Call Jira API with rate limiting."""
    # ...
```

### 4. Permission Scopes

**Jira OAuth Scopes:**
- `read:jira-work` - Read tickets (required)
- `write:jira-work` - Create/update tickets (required for write operations)
- `manage:jira-project` - Project management (optional)

### 5. User Authorization

**Requirement:** Users should only access their own tickets.

**Implementation:**
```python
# src/api/v1/jira.py

@router.get("/tickets")
async def get_tickets(
    force_refresh: bool = False,
    user_id: str = Depends(get_current_user)
):
    # Always filter by authenticated user
    conn = await jira_repo.get_connection(user_id)
    if not conn:
        raise HTTPException(401, "Jira not connected")

    # Get user's Jira email from connection
    jira_email = conn.jira_email

    # Fetch tickets assigned to this user only
    tickets = await jira_tool.list_tickets(
        assignee=jira_email,
        force_refresh=force_refresh
    )

    return {"tickets": tickets}
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Jira API** | Jira REST API via `httpx` | Ticket operations, authentication |
| **OAuth 2.0** | `requests-oauthlib` (if using OAuth) | Jira authentication flow |
| **HTTP Client** | `httpx` | Async HTTP requests to Jira API |
| **Token Encryption** | `cryptography` | Encrypt API tokens at rest |
| **Rate Limiting** | `slowapi` | Respect Jira API rate limits |
| **Database** | PostgreSQL + asyncpg | Store connections, light cache |
| **LLM** | OpenAI/Anthropic via LangChain | Summarize tickets, generate content |
| **Workflow** | LangGraph | Jira workflow orchestration |
| **Webhooks** | FastAPI + NestJS Bridge | Autonomous notifications |

### Dependencies to Add

```txt
# requirements.txt additions
requests-oauthlib>=1.3.1
slowapi>=0.1.9
```

---

## Implementation Roadmap

### Phase 1: Core Jira Infrastructure (2-3 days)

| Step | Task | File(s) |
|------|------|---------|
| 1 | Create database models and migrations | `src/db/models.py`, `migrations/versions/xxx_add_jira_tables.py` |
| 2 | Build Jira connection repository | `src/db/repositories/jira_connection_repo.py` |
| 3 | Build ticket cache repository (optional) | `src/db/repositories/jira_ticket_cache_repo.py` |
| 4 | Set up token encryption (reuse from email) | `src/utils/encryption.py` |
| 5 | Set up Jira API client | `src/services/jira_client.py` |
| 6 | Build rate limiter | `src/tools/jira/rate_limiter.py` |
| 7 | Add environment variables | `src/config.py`, `.env.example` |

### Phase 2: Jira API Tool (2-3 days)

| Step | Task | File(s) |
|------|------|---------|
| 1 | Build base Jira tool class | `src/tools/jira/base.py` |
| 2 | Implement `list_tickets` tool | `src/tools/jira/list.py` |
| 3 | Implement `get_ticket` tool | `src/tools/jira/get.py` |
| 4 | Implement `search_tickets` tool | `src/tools/jira/search.py` |
| 5 | Implement `update_ticket` tool | `src/tools/jira/update.py` |
| 6 | Implement `create_ticket` tool | `src/tools/jira/create.py` |
| 7 | Implement `add_comment` tool | `src/tools/jira/comment.py` |
| 8 | Register Jira tool in registry | `src/tools/registry.py` |

### Phase 3: LangGraph Jira Nodes (2-3 days)

| Step | Task | File(s) |
|------|------|---------|
| 1 | Build JiraIntentNode | `src/agent/nodes/jira_intent.py` |
| 2 | Build JiraQuerierNode | `src/agent/nodes/jira_querier.py` |
| 3 | Build JiraSummarizerNode | `src/agent/nodes/jira_summarizer.py` |
| 4 | Build JiraUpdaterNode | `src/agent/nodes/jira_updater.py` |
| 5 | Build JiraCreatorNode | `src/agent/nodes/jira_creator.py` |
| 6 | Update AgentState with Jira fields | `src/agent/state.py` |
| 7 | Build Jira workflow edges | `src/agent/edges.py` |
| 8 | Wire Jira workflow into main graph | `src/agent/graph.py` |

### Phase 4: API Endpoints (2 days)

| Step | Task | File(s) |
|------|------|---------|
| 1 | Build Jira connection status endpoint | `src/api/v1/jira.py` (GET /status) |
| 2 | Build Jira connect endpoint | `src/api/v1/jira.py` (POST /connect) |
| 3 | Build Jira disconnect endpoint | `src/api/v1/jira.py` (POST /disconnect) |
| 4 | Build list tickets endpoint | `src/api/v1/jira.py` (GET /tickets) |
| 5 | Build get ticket endpoint | `src/api/v1/jira.py` (GET /tickets/{key}) |
| 6 | Build create ticket endpoint | `src/api/v1/jira.py` (POST /tickets) |
| 7 | Build update ticket endpoint | `src/api/v1/jira.py` (PATCH /tickets/{key}) |
| 8 | Build daily summary endpoint | `src/api/v1/jira.py` (GET /summary/daily) |
| 9 | Build search endpoint | `src/api/v1/jira.py` (GET /search) |

### Phase 5: UI Integration (Frontend)

| Step | Task | File(s) |
|------|------|---------|
| 1 | Build JiraConnection component | `components/JiraConnection.tsx` |
| 2 | Add Jira connection status to profile | `app/profile/page.tsx` |
| 3 | Build ticket list component | `components/TicketList.tsx` |
| 4 | Build ticket details component | `components/TicketDetails.tsx` |
| 5 | Add WebSocket support for notifications | `hooks/useJiraStream.ts` |

### Phase 6: Testing & Refinement (2-3 days)

| Step | Task | File(s) |
|------|------|---------|
| 1 | Write unit tests for Jira tools | `tests/unit/test_tools/test_jira.py` |
| 2 | Write unit tests for Jira nodes | `tests/unit/test_nodes/test_jira_nodes.py` |
| 3 | Write integration tests for Jira flow | `tests/integration/test_jira_flow.py` |
| 4 | Test with sample Jira instance | Manual testing |
| 5 | Test summary generation | Manual testing |
| 6 | Test cross-tool integration (Jira + Email) | Manual testing |

### Phase 7: Autonomous Workflows (Future - Optional)

| Step | Task | File(s) |
|------|------|---------|
| 1 | Build webhook receiver endpoint | `src/api/v1/jira.py` (POST /webhook) |
| 2 | Build webhook validation utility | `src/utils/jira_webhook_validator.py` |
| 3 | Build JiraNotificationNode | `src/agent/nodes/jira_notification.py` |
| 4 | Set up Jira webhook configuration | Jira UI or API |
| 5 | Build WebSocket notification service | `src/services/websocket_manager.py` |
| 6 | Test webhook flows | Manual testing |

---

## MCP/RAG Assessment

### Do We Need MCP (Model Context Protocol)?

**Answer: NO, MCP is not needed for this feature.**

**Reasoning:**
- MCP is useful for standardizing tool access across different AI agents
- Our custom LangChain tools already provide this functionality
- Jira API is well-documented and stable
- We don't need external tool discovery or standardization at this point
- The single-service pattern (one agent, one toolset) works well for Jira

**When MCP Might Be Useful (Future):**
- If we want to make our Jira tools available to other AI systems
- If we adopt a multi-agent architecture where different services need tool access
- If we participate in a broader ecosystem of MCP-compatible tools
- If we need to dynamically discover and use third-party Jira tools

### Do We Need RAG (Retrieval-Augmented Generation)?

**Answer: NO, RAG is not needed for the initial Jira feature.**

**Reasoning:**
- Jira operations are primarily query/transactional, not retrieval-based
- We fetch tickets directly from Jira API when needed
- We don't need semantic search over past tickets initially
- Ticket data is structured, not free-form text that needs vector search

**When RAG Might Be Useful (Future):**
- If we want "search my past tickets by meaning" (semantic search)
- If we want to find similar tickets based on description similarity
- If we want to provide context from related tickets when creating new ones
- If we want to build a "ticket assistant" that suggests similar issues

### What We DO Need

| Component | Purpose |
|-----------|---------|
| **LangChain Tools** | Standard interface for Jira API operations |
| **LangGraph** | Workflow orchestration with cross-tool integration |
| **LLM Generation** | Summarize tickets, generate descriptions, create notifications |
| **PostgreSQL** | Connection storage, lightweight ticket cache |
| **Jira REST API** | All ticket operations |
| **API Token / OAuth** | User authentication |
| **Webhooks** (optional) | Autonomous notifications |
| **HTTP Client (httpx)** | Async API calls |
| **Rate Limiting** | Respect Jira API limits |

---

## Additional Use Cases & Future Enhancements

### Advanced Use Cases

#### 1. Sprint Planning Assistance
```
User: "help me plan my sprint"
→ Agent:
  - Fetches user's assigned tickets
  - Estimates complexity based on description
  - Suggests sprint allocation:
    "Based on your 12 assigned tickets, I recommend:
    - 3 High priority (estimated 8 story points)
    - 4 Medium priority (estimated 6 story points)
    - 2 Low priority (estimated 3 story points)

    Total: 17 story points"
```

#### 2. Blocker Identification
```
User: "are any of my tickets blocked?"
→ Agent:
  - Analyzes ticket dependencies
  - Checks for unresolved blockers
  - Returns:
    "Found 2 blocked tickets:
    - TDX-340: Blocked by TDX-300 (login fix)
    - TDX-355: Blocked by TDX-201 (API docs)"
```

#### 3. Workload Visualization
```
User: "show my workload for this week"
→ Agent:
  - Fetches tickets due this week
  - Groups by priority
  - Returns:
    "This Week's Workload:
    ===================
    Due: Feb 28 (3 tickets)
    - TDX-300: Fix login bug [High]
    - TDX-215: Review PRs [Medium]
    - TDX-198: Auth refactor [Low]

    Due: Mar 1 (2 tickets)
    - TDX-205: User profile caching [Medium]
    - TDX-210: Update changelog [Low]"
```

#### 4. Automated Daily Standup Report
```
User: "generate my standup report"
→ Agent:
  - Fetches tickets updated yesterday
  - Generates standup format:
    "**Yesterday**
    - Worked on TDX-300 (login bug fix)
    - Fixed authentication token handling

    **Today**
    - Continue testing TDX-300 on mobile devices
    - Start TDX-201 (API docs update)

    **Blockers**
    - Need access to iOS device for testing"

  - Offers to email to team
```

#### 5. Time Tracking Integration (Future)
```
User: "log 4 hours on TDX-300"
→ Agent:
  - Calls Jira time tracking API
  - Adds worklog entry
  - Response: "Logged 4 hours on TDX-300"
```

### Cross-Tool Workflows

#### 1. Jira + Email + Calendar
```
User: "schedule a meeting with the TDX-300 assignees tomorrow at 2pm"
→ Agent:
  1. Fetches TDX-300 details
  2. Gets assignee emails
  3. Creates calendar invite
  4. Sends email confirmation
```

#### 2. Jira + GitHub Integration
```
User: "create a PR for TDX-300"
→ Agent:
  1. Fetches TDX-300 details
  2. Creates PR with ticket summary as description
  3. Adds "Closes TDX-300" to PR
  4. Updates ticket status to "In Review"
```

#### 3. Jira + Web Search
```
User: "research solutions for TDX-300 and add to comments"
→ Agent:
  1. Fetches TDX-300 (login bug on iOS)
  2. Web searches "Safari iOS login token issues"
  3. Summarizes findings
  4. Adds comment to TDX-300 with research
```

---

## Summary

This Jira feature will provide:

1. **Secure Authentication** - API token / OAuth with encrypted storage
2. **Natural Language Ticket Queries** - "show me my tickets", "find bugs"
3. **Ticket Operations** - Create, update, comment on tickets
4. **AI-Powered Summaries** - Daily summaries, completion reports
5. **Autonomous Notifications** - Webhook-driven alerts (optional)
6. **Cross-Tool Integration** - Use Jira data in emails, reports, etc.
7. **Connected Services UI** - Show Jira connection status in profile
8. **Lightweight Database** - Minimal storage, Jira API as source of truth
9. **Rate Limiting** - Respect Jira API limits
10. **Future-Ready** - Hooks for advanced workflows, time tracking, etc.

**Total Estimated Time:**
- Core functionality (Phases 1-6): **10-13 days**
- Autonomous workflows (Phase 7): +3-5 days

**Key Files:** 25+ new/modified files
**New Database Tables:** 2-3 (user_jira_connections, optional cache/summaries)

---

## Next Steps

1. **Review this plan** with the team
2. **Decide on authentication method**: API Token (MVP) vs OAuth (production)
3. **Set up Jira test instance** for development
4. **Start Phase 1**: Core Jira infrastructure
5. **Iterate and refine** based on user feedback
