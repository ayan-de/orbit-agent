# 📧 Email Tool Feature Design

> Status: Planning Phase
> Last Updated: 2026-02-22

---

## Table of Contents

1. [Overview](#overview)
2. [Use Cases](#use-cases)
3. [Architecture](#architecture)
4. [Database Schema](#database-schema)
5. [API Design](#api-design)
6. [LangGraph Integration](#langgraph-integration)
7. [Authentication Flow](#authentication-flow)
8. [Human-in-the-Loop Pattern](#human-in-the-loop-pattern)
9. [Security Considerations](#security-considerations)
10. [Technology Stack](#technology-stack)
11. [Implementation Roadmap](#implementation-roadmap)
12. [MCP/RAG Assessment](#mcprag-assessment)

---

## Overview

The Email Tool enables users to compose, preview, and send emails through natural language. It features:

- **Gmail OAuth 2.0 integration** for secure authentication
- **Human-in-the-loop confirmation** - preview before sending
- **Multi-step refinement** - modify email content before final send
- **File attachments** - support for uploaded files
- **Connected services UI** - show Gmail connection status in Next.js profile
- **Content generation** - can generate email content from other tools (Jira, web search, etc.)

---

## Use Cases

### 1. Simple Direct Email
```
User: "email 'Happy birthday' to sakil@gmail.com"
→ Draft: From: deayan252@gmail.com, To: sakil@gmail.com, Body: "Happy birthday"
→ Preview shown to user
→ User: "yes send it"
→ Email sent
```

### 2. Email with Attachment
```
User: "email 'Here is the report' to sakil@gmail.com with this file [uploads report.pdf]"
→ Draft: From: deayan252@gmail.com, To: sakil@gmail.com, Body: "Here is the report"
→ Attachment: report.pdf
→ Preview shown to user
→ User: "yes send it"
→ Email sent
```

### 3. Generated Content Email (Multi-Source)
```
User: "fetch my jira tickets, summarize them, and email the summary to manager@gmail.com"
→ Agent: Fetches Jira tickets → Generates summary → Drafts email
→ Preview shown to user with Jira summary content
→ User: "yes send it"
→ Email sent
```

### 4. Content with Refinement
```
User: "list top 10 cars and mail it to sakil@gmail.com"
→ Agent: Lists cars → Drafts email with 10 cars
→ Preview shown to user
→ User: "instead of 10 cars make it 20 cars"
→ Agent: Regenerates list with 20 cars → Shows new preview
→ User: "yes send it"
→ Email sent
```

### 5. Manual Drafting
```
User: "email 'I'll be out tomorrow' to my boss"
→ Agent: "Who is your boss?"
→ User: "boss@company.com"
→ Draft: From: deayan252@gmail.com, To: boss@company.com, Body: "I'll be out tomorrow"
→ Preview shown
→ User: "yes send it"
→ Email sent
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
│  - Stores tokens securely                                            │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Python Agent (FastAPI)                          │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Agent Layer (LangGraph)                                        │ │
│  │  ┌────────────┐ ┌─────────────┐ ┌─────────────┐                │ │
│  │  │Classifier  │ │EmailDrafter │ │EmailPreview │                │ │
│  │  └────────────┘ └─────────────┘ └─────────────┘                │ │
│  │  ┌────────────┐ ┌─────────────┐ ┌─────────────┐                │ │
│  │  │EmailSender │ │HumanInput   │ │Refinement   │                │ │
│  │  └────────────┘ └─────────────┘ └─────────────┘                │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Tools Layer (LangChain)                                       │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │ │
│  │  │GmailTool     │  │JiraTool      │  │BrowserTool   │         │ │
│  │  │- list_emails │  │- get_tickets │  │- web_search  │         │ │
│  │  │- draft_email │  │- get_details │  │- scrape      │         │ │
│  │  │- send_email  │  └──────────────┘  └──────────────┘         │ │
│  │  │- attachments │                                            │ │
│  │  └──────────────┘                                            │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  API Layer                                                      │ │
│  │  - POST /api/v1/email/draft                                     │ │
│  │  - POST /api/v1/email/send                                      │ │
│  │  - GET  /api/v1/email/status                                    │ │
│  │  - POST /api/v1/email/refine                                    │ │
│  │  - GET  /api/v1/email/sent                                      │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          PostgreSQL Database                        │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  user_email_connections                                         │ │
│  │  - id, user_id, email_address                                   │ │
│  │  - access_token, refresh_token                                  │ │
│  │  - token_expiry, is_connected                                   │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  email_drafts                                                   │ │
│  │  - id, session_id, user_id                                      │ │
│  │  - to_address, subject, body                                    │ │
│  │  - attachments (JSONB), status (draft/sent)                    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  sent_emails                                                    │ │
│  │  - id, user_id, to_address, subject                            │ │
│  │  - body, attachments, sent_at                                  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Gmail API                                    │
│  - OAuth 2.0 Authentication                                          │
│  - Gmail API for sending emails                                    │
│  - Attachment handling                                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### 1. user_email_connections

```sql
CREATE TABLE user_email_connections (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    email_address VARCHAR(255) NOT NULL UNIQUE,
    provider VARCHAR(50) NOT NULL DEFAULT 'gmail', -- gmail, outlook, etc.

    -- OAuth tokens (encrypted)
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_expires_at TIMESTAMP NOT NULL,

    -- Connection status
    is_connected BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    disconnected_at TIMESTAMP NULL,

    -- Indexes
    UNIQUE(user_id, email_address)
);

CREATE INDEX idx_user_email_connections_user_id ON user_email_connections(user_id);
CREATE INDEX idx_user_email_connections_is_connected ON user_email_connections(is_connected);
```

### 2. email_drafts

```sql
CREATE TABLE email_drafts (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,

    -- Email fields
    from_email VARCHAR(255) NOT NULL,
    to_email VARCHAR(255) NOT NULL,
    cc_email VARCHAR(255)[] DEFAULT '{}', -- Array for multiple CC recipients
    bcc_email VARCHAR(255)[] DEFAULT '{}', -- Array for multiple BCC recipients
    subject TEXT,
    body TEXT NOT NULL,

    -- Attachments (stored as JSONB array)
    attachments JSONB DEFAULT '[]'::jsonb,
    -- Format: [{"file_id": "uuid", "filename": "report.pdf", "size": 12345, "mimetype": "application/pdf"}]

    -- Draft state
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, previewed, sent, cancelled
    iteration INTEGER NOT NULL DEFAULT 0, -- Track refinement iterations

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    -- Can store: {"source": "jira", "jira_tickets": ["PROJ-123", "PROJ-456"]}

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    previewed_at TIMESTAMP NULL,
    sent_at TIMESTAMP NULL,

    -- Indexes
    INDEX idx_email_drafts_session_id (session_id),
    INDEX idx_email_drafts_user_id (user_id),
    INDEX idx_email_drafts_status (status)
);
```

### 3. sent_emails

```sql
CREATE TABLE sent_emails (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    draft_id INTEGER REFERENCES email_drafts(id),

    -- Email fields
    from_email VARCHAR(255) NOT NULL,
    to_email VARCHAR(255) NOT NULL,
    cc_email VARCHAR(255)[],
    bcc_email VARCHAR(255)[],
    subject TEXT,
    body TEXT NOT NULL,

    -- Attachments
    attachments JSONB DEFAULT '[]'::jsonb,

    -- Gmail metadata
    gmail_message_id VARCHAR(255), -- Returned by Gmail API
    gmail_thread_id VARCHAR(255),

    -- Timestamps
    sent_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Indexes
    INDEX idx_sent_emails_user_id (user_id),
    INDEX idx_sent_emails_sent_at (sent_at)
);
```

---

## API Design

### 1. Email Connection Management

#### `GET /api/v1/email/status`
Get user's email connection status.

**Response:**
```json
{
  "is_connected": true,
  "email_address": "deayan252@gmail.com",
  "provider": "gmail",
  "connected_at": "2026-02-20T10:30:00Z"
}
```

#### `POST /api/v1/email/disconnect`
Disconnect email service.

**Request:**
```json
{}
```

**Response:**
```json
{
  "success": true,
  "message": "Email service disconnected"
}
```

### 2. Email Drafting & Sending

#### `POST /api/v1/email/draft`
Create or update an email draft.

**Request:**
```json
{
  "session_id": "session-123",
  "to_email": "sakil@gmail.com",
  "subject": "Happy Birthday!",
  "body": "Happy birthday! Hope you have a great day.",
  "attachments": [
    {
      "file_id": "uuid-123",
      "filename": "card.pdf",
      "mimetype": "application/pdf"
    }
  ],
  "metadata": {
    "source": "direct",
    "iteration": 0
  }
}
```

**Response:**
```json
{
  "draft_id": 456,
  "status": "draft",
  "preview_url": "/api/v1/email/draft/456/preview"
}
```

#### `GET /api/v1/email/draft/{id}`
Get email draft details.

**Response:**
```json
{
  "id": 456,
  "from_email": "deayan252@gmail.com",
  "to_email": "sakil@gmail.com",
  "subject": "Happy Birthday!",
  "body": "Happy birthday! Hope you have a great day.",
  "attachments": [
    {
      "file_id": "uuid-123",
      "filename": "card.pdf",
      "size": 12345,
      "mimetype": "application/pdf"
    }
  ],
  "status": "previewed",
  "iteration": 0,
  "created_at": "2026-02-22T10:00:00Z",
  "metadata": {}
}
```

#### `POST /api/v1/email/send`
Send a drafted email.

**Request:**
```json
{
  "draft_id": 456
}
```

**Response:**
```json
{
  "success": true,
  "sent_email_id": 789,
  "gmail_message_id": "123abc456def",
  "sent_at": "2026-02-22T10:05:00Z"
}
```

#### `POST /api/v1/email/refine`
Refine an email draft (multi-step refinement).

**Request:**
```json
{
  "draft_id": 456,
  "refinement_request": "instead of 10 cars make it 20 cars"
}
```

**Response:**
```json
{
  "draft_id": 456,
  "iteration": 1,
  "body": "Here are the top 20 cars:\n1. ...\n2. ...\n...\n20. ..."
}
```

### 3. Email History

#### `GET /api/v1/email/sent`
Get user's sent emails with pagination.

**Query Parameters:**
- `page`: Page number (default 1)
- `limit`: Items per page (default 20)

**Response:**
```json
{
  "emails": [
    {
      "id": 789,
      "to_email": "sakil@gmail.com",
      "subject": "Happy Birthday!",
      "sent_at": "2026-02-22T10:05:00Z",
      "has_attachments": true
    }
  ],
  "total": 45,
  "page": 1,
  "limit": 20
}
```

---

## LangGraph Integration

### Email-Specific Nodes

#### 1. `EmailIntentNode`
Determines if user request is email-related.

**File:** `src/agent/nodes/email_intent.py`

```python
async def email_intent_node(state: AgentState) -> AgentState:
    """Classify if request involves email sending."""
    # Prompt LLM to check if request involves email
    # Returns intent: "email_send", "email_read", or "other"
```

#### 2. `EmailDrafterNode`
Creates email draft based on user request.

**File:** `src/agent/nodes/email_drafter.py`

```python
async def email_drafter_node(state: AgentState) -> AgentState:
    """
    Drafts email from natural language request.

    Handles:
    - Direct email: "email 'Happy birthday' to sakil@gmail.com"
    - Generated content: "list top 10 cars and mail to sakil@gmail.com"
    - Multi-source: "fetch jira tickets and email summary to manager@gmail.com"
    """
    # 1. Extract email components (to, subject, body)
    # 2. Execute other tools if needed (jira, browser)
    # 3. Generate email content
    # 4. Store draft in database
    # 5. Return draft_id to state
```

#### 3. `EmailPreviewNode`
Shows email preview to user.

**File:** `src/agent/nodes/email_preview.py`

```python
async def email_preview_node(state: AgentState) -> AgentState:
    """
    Retrieves and formats email preview.

    Displays:
    - From: user_email
    - To: recipient_email
    - Subject: ...
    - Body: ...
    - Attachments: [list]
    """
    # Fetch draft from database
    # Format preview message
    # Set state.needs_confirmation = True
    # Set state.confirmation_prompt = formatted_preview
```

#### 4. `EmailSenderNode`
Sends the email via Gmail API.

**File:** `src/agent/nodes/email_sender.py`

```python
async def email_sender_node(state: AgentState) -> AgentState:
    """
    Sends the email draft via Gmail API.

    Steps:
    1. Fetch draft from database
    2. Get user's access token
    3. Call Gmail API to send
    4. Store sent email record
    5. Update draft status
    """
    # Use GmailTool.send_email()
    # Log to sent_emails table
```

#### 5. `EmailRefinementNode`
Handles email content refinement.

**File:** `src/agent/nodes/email_refinement.py`

```python
async def email_refinement_node(state: AgentState) -> AgentState:
    """
    Refines email draft based on user feedback.

    Examples:
    - "make it shorter"
    - "add more details about X"
    - "change the tone to more professional"
    - "instead of 10 cars make it 20 cars"
    """
    # 1. Parse refinement request
    # 2. Use LLM to modify email content
    # 3. Update draft in database
    # 4. Return to preview state
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

    # Email-specific fields
    email_draft_id: int | None
    email_needs_confirmation: bool
    email_refinement_iteration: int
    email_confirmation_prompt: str | None
    email_attachments: list[dict]
```

### Email Workflow Graph

```
START
  ↓
[Classifier]
  ↓
[intent == "email_send"]
  ↓
[EmailDrafter] ──→ [EmailPreview]
                    ↓
              [needs_confirmation?]
               ↙           ↘
           [user: "yes"]   [user: modify]
               ↓               ↓
          [EmailSender]    [EmailRefinement]
               ↓               ↓
          [Responder] ←─────┘
               ↓
             END
```

---

## Authentication Flow

### OAuth 2.0 Flow with Next.js

#### Step 1: User clicks "Connect Gmail" in Next.js UI

**Next.js Component:**
```typescript
// components/EmailConnection.tsx
<button onClick={connectGmail}>
  {isConnected ? (
    <span>Gmail ✓</span>
  ) : (
    <span>Connect Gmail</span>
  )}
</button>

async function connectGmail() {
  // Redirect to NestJS Bridge OAuth endpoint
  window.location.href = `${API_BASE}/auth/gmail/authorize`;
}
```

#### Step 2: NestJS Bridge handles OAuth flow

**NestJS Controller:**
```typescript
// auth/gmail.controller.ts
@Controller('auth/gmail')
export class GmailController {
  @Get('authorize')
  async authorize(@Res() res: Response) {
    // Generate OAuth URL with scopes
    const authUrl = oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: ['https://www.googleapis.com/auth/gmail.send'],
      state: generateState(), // For CSRF protection
    });
    res.redirect(authUrl);
  }

  @Get('callback')
  async callback(@Query('code') code: string, @Query('state') state: string) {
    // 1. Exchange code for tokens
    const { tokens } = await oauth2Client.getToken(code);

    // 2. Get user email from Gmail API
    const gmail = google.gmail({ version: 'v1', auth: oauth2Client });
    const profile = await gmail.users.getProfile({ userId: 'me' });

    // 3. Store tokens in Python Agent database
    await agentService.storeEmailTokens({
      user_id: session.user_id,
      email_address: profile.data.emailAddress,
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token,
      expires_at: tokens.expiry_date,
    });

    // 4. Redirect back to Next.js
    res.redirect(`${FRONTEND_URL}/profile?email=connected`);
  }
}
```

#### Step 3: Store tokens in Python Agent database

**Python Repository:**
```python
# src/db/repositories/email_connection_repo.py
class EmailConnectionRepository:
    async def store_tokens(
        self,
        user_id: str,
        email_address: str,
        access_token: str,
        refresh_token: str,
        expires_at: datetime
    ):
        # Encrypt tokens before storing
        encrypted_access = encrypt_token(access_token)
        encrypted_refresh = encrypt_token(refresh_token)

        await self.db.execute(
            """INSERT INTO user_email_connections
               (user_id, email_address, access_token, refresh_token, token_expires_at, is_connected)
               VALUES ($1, $2, $3, $4, $5, true)
               ON CONFLICT (user_id, email_address)
               DO UPDATE SET
                 access_token = $3,
                 refresh_token = $4,
                 token_expires_at = $5,
                 is_connected = true,
                 updated_at = NOW()
            """,
            user_id, email_address, encrypted_access, encrypted_refresh, expires_at
        )
```

#### Step 4: Disconnect flow

**Python API:**
```python
# src/api/v1/email.py
@router.post("/disconnect")
async def disconnect_email(user_id: str = Depends(get_current_user)):
    # 1. Mark as disconnected
    await email_repo.set_disconnected(user_id)

    # 2. Optionally delete tokens (for security)
    # await email_repo.delete_tokens(user_id)

    return {"success": True, "message": "Email service disconnected"}
```

---

## Human-in-the-Loop Pattern

### Multi-Step Email Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  User: "list top 10 cars and mail it to sakil@gmail.com"               │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  Agent: BrowserTool.web_search("top 10 cars")                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  Agent: EmailDrafterNode                                                │
│          → Creates draft with car list                                  │
│          → Draft ID: 123                                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  Agent: EmailPreviewNode                                                │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  📧 Email Preview                                                  │ │
│  │  ───────────────────────────────────────────────────────────────  │ │
│  │  From: deayan252@gmail.com                                         │ │
│  │  To:   sakil@gmail.com                                             │ │
│  │  Subject: Top 10 Cars                                             │ │
│  │                                                                   │ │
│  │  Here are the top 10 cars:                                        │ │
│  │  1. Tesla Model S                                                  │ │
│  │  2. BMW M3                                                         │ │
│  │  3. Mercedes AMG GT                                                │ │
│  │  ...                                                               │ │
│  │  10. Porsche 911                                                   │ │
│  │                                                                   │ │
│  │  Send this email?                                                 │ │
│  │  • Reply "yes" to send                                            │ │
│  │  • Reply "make it [n] cars" to change                             │ │
│  │  • Reply "cancel" to cancel                                       │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  User: "instead of 10 cars make it 20 cars"                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  Agent: EmailRefinementNode                                            │
│          → Re-queries browser with 20 cars                             │
│          → Updates draft (iteration: 1)                                │
│          → Shows new preview                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  User: "yes send it"                                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  Agent: EmailSenderNode                                                │
│          → Gets user's access token                                     │
│          → Calls Gmail API to send                                     │
│          → Stores sent email record                                    │
│          → Returns: "Email sent successfully!"                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### State Machine for Email Confirmation

```python
# src/agent/edges.py

def email_confirmation_router(state: AgentState) -> str:
    """
    Route based on user's confirmation decision.

    States:
    - "email_send": User confirmed, proceed to send
    - "email_refine": User wants to modify, go to refinement
    - "email_cancel": User cancelled, go to responder
    - "email_preview": Still in preview (no user response yet)
    """
    user_response = state.get("user_confirmation")

    if user_response == "yes" or user_response == "send":
        return "email_send"
    elif user_response == "no" or user_response == "cancel":
        return "email_cancel"
    elif user_response:  # Any other response is a refinement
        return "email_refine"
    else:
        return "email_preview"
```

---

## Security Considerations

### 1. Token Storage & Encryption

**Requirement:** Store OAuth tokens encrypted at rest.

**Implementation:**
```python
# src/utils/encryption.py
from cryptography.fernet import Fernet

class TokenEncryption:
    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key.encode())

    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()

# Usage
encryption = TokenEncryption(settings.ENCRYPTION_KEY)
encrypted_token = encryption.encrypt(access_token)
```

### 2. Token Refresh

**Requirement:** Automatically refresh expired tokens.

**Implementation:**
```python
# src/utils/gmail_token_manager.py

class GmailTokenManager:
    async def get_valid_token(self, user_id: str) -> str:
        conn = await email_repo.get_connection(user_id)

        # Check if token needs refresh
        if conn.token_expires_at <= datetime.now() + timedelta(minutes=5):
            # Refresh the token
            new_token = await self._refresh_token(conn.refresh_token)

            # Update in database
            await email_repo.update_access_token(user_id, new_token)

            return new_token

        return conn.access_token

    async def _refresh_token(self, refresh_token: str) -> str:
        # Call Gmail OAuth endpoint to refresh
        # ...
```

### 3. Rate Limiting

**Requirement:** Prevent email abuse.

**Implementation:**
```python
# src/api/middleware/rate_limit.py

@router.post("/send", dependencies=[Depends(rate_limiter)])
async def send_email(
    draft_id: int,
    user_id: str = Depends(get_current_user)
):
    # Check: max 10 emails per hour per user
    if await rate_limiter.is_exceeded(user_id, limit=10, window=3600):
        raise HTTPException(429, "Too many emails. Please wait.")

    # Proceed to send...
```

### 4. Email Validation

**Requirement:** Validate email addresses and attachments.

**Implementation:**
```python
# src/utils/email_validation.py

import re
from email_validator import validate_email

def validate_recipient(email: str) -> bool:
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def validate_attachment(file: UploadFile) -> tuple[bool, str]:
    """Validate file size and type."""
    MAX_SIZE = 25 * 1024 * 1024  # 25MB
    ALLOWED_TYPES = [
        'application/pdf',
        'image/jpeg',
        'image/png',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]

    if file.size > MAX_SIZE:
        return False, "File too large (max 25MB)"

    if file.content_type not in ALLOWED_TYPES:
        return False, "File type not allowed"

    return True, ""
```

### 5. Permission Scopes

**Gmail OAuth Scopes:**
- `https://www.googleapis.com/auth/gmail.send` - Send emails only (recommended)
- `https://www.googleapis.com/auth/gmail.readonly` - Read emails (optional, for fetching history)
- `https://www.googleapis.com/auth/gmail.compose` - Draft emails (if needed)

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Email API** | Gmail API via `google-api-python-client` | Send emails, handle attachments |
| **OAuth 2.0** | `google-auth-oauthlib` | Gmail authentication flow |
| **HTTP Client** | `httpx` | Async HTTP requests to Gmail API |
| **Email Construction** | `email.mime` | Build MIME messages with attachments |
| **Token Encryption** | `cryptography` | Encrypt OAuth tokens at rest |
| **Rate Limiting** | `slowapi` | API rate limiting |
| **Email Validation** | `email-validator` | Validate email addresses |
| **File Handling** | `python-multipart` | Handle file uploads |
| **Database** | PostgreSQL + asyncpg | Store tokens, drafts, sent emails |
| **LLM** | OpenAI/Anthropic via LangChain | Generate/refine email content |
| **Workflow** | LangGraph | Email workflow orchestration |

### Dependencies to Add

```txt
# requirements.txt additions
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.0.0
google-auth>=2.20.0
cryptography>=41.0.0
email-validator>=2.0.0
slowapi>=0.1.9
```

---

## Implementation Roadmap

### Phase 1: Core Email Infrastructure (3-4 days)

| Step | Task | File(s) |
|------|------|---------|
| 1 | Create database models and migrations | `src/db/models.py`, `migrations/versions/xxx_add_email_tables.py` |
| 2 | Build email connection repository | `src/db/repositories/email_connection_repo.py` |
| 3 | Build email draft repository | `src/db/repositories/email_draft_repo.py` |
| 4 | Build sent emails repository | `src/db/repositories/sent_email_repo.py` |
| 5 | Set up token encryption utility | `src/utils/encryption.py` |
| 6 | Set up Gmail OAuth client | `src/services/gmail_oauth.py` |
| 7 | Build token refresh manager | `src/utils/gmail_token_manager.py` |
| 8 | Build email validation utilities | `src/utils/email_validation.py` |

### Phase 2: Gmail API Tool (2-3 days)

| Step | Task | File(s) |
|------|------|---------|
| 1 | Build base Gmail tool class | `src/tools/gmail/base.py` |
| 2 | Implement `send_email` tool | `src/tools/gmail/send.py` |
| 3 | Implement `draft_email` tool | `src/tools/gmail/draft.py` |
| 4 | Implement `list_sent_emails` tool | `src/tools/gmail/list.py` |
| 5 | Implement attachment handling | `src/tools/gmail/attachments.py` |
| 6 | Register Gmail tool in registry | `src/tools/registry.py` |
| 7 | Add environment variables | `src/config.py`, `.env.example` |

### Phase 3: LangGraph Email Nodes (2-3 days)

| Step | Task | File(s) |
|------|------|---------|
| 1 | Build EmailIntentNode | `src/agent/nodes/email_intent.py` |
| 2 | Build EmailDrafterNode | `src/agent/nodes/email_drafter.py` |
| 3 | Build EmailPreviewNode | `src/agent/nodes/email_preview.py` |
| 4 | Build EmailSenderNode | `src/agent/nodes/email_sender.py` |
| 5 | Build EmailRefinementNode | `src/agent/nodes/email_refinement.py` |
| 6 | Update AgentState with email fields | `src/agent/state.py` |
| 7 | Build email confirmation router | `src/agent/edges.py` |
| 8 | Wire email workflow into main graph | `src/agent/graph.py` |

### Phase 4: API Endpoints (2 days)

| Step | Task | File(s) |
|------|------|---------|
| 1 | Build email connection status endpoint | `src/api/v1/email.py` (GET /status) |
| 2 | Build email disconnect endpoint | `src/api/v1/email.py` (POST /disconnect) |
| 3 | Build email draft endpoint | `src/api/v1/email.py` (POST /draft) |
| 4 | Build email preview endpoint | `src/api/v1/email.py` (GET /draft/{id}) |
| 5 | Build email send endpoint | `src/api/v1/email.py` (POST /send) |
| 6 | Build email refine endpoint | `src/api/v1/email.py` (POST /refine) |
| 7 | Build sent emails list endpoint | `src/api/v1/email.py` (GET /sent) |
| 8 | Add rate limiting to email endpoints | `src/api/middleware/rate_limit.py` |

### Phase 5: OAuth Integration (2-3 days)

| Step | Task | File(s) |
|------|------|---------|
| 1 | Set up Gmail OAuth credentials | Google Cloud Console |
| 2 | Build OAuth authorize endpoint (NestJS) | `nest/src/auth/gmail.controller.ts` |
| 3 | Build OAuth callback endpoint (NestJS) | `nest/src/auth/gmail.controller.ts` |
| 4 | Build token storage API (NestJS → Python) | `nest/src/services/email-connection.service.ts` |
| 5 | Build email connection service | `src/services/email_connection.py` |
| 6 | Build disconnect flow | `src/services/email_connection.py` |
| 7 | Test full OAuth flow end-to-end | Manual testing |

### Phase 6: Testing & Refinement (2-3 days)

| Step | Task | File(s) |
|------|------|---------|
| 1 | Write unit tests for Gmail tools | `tests/unit/test_tools/test_gmail.py` |
| 2 | Write unit tests for email nodes | `tests/unit/test_nodes/test_email_nodes.py` |
| 3 | Write integration tests for email flow | `tests/integration/test_email_flow.py` |
| 4 | Test with Gmail sandbox account | Manual testing |
| 5 | Test attachment handling | Manual testing |
| 6 | Test token refresh flow | Manual testing |
| 7 | Test refinement workflow | Manual testing |

### Phase 7: UI Integration (Frontend)

| Step | Task | File(s) |
|------|------|---------|
| 1 | Build EmailConnection component | `components/EmailConnection.tsx` |
| 2 | Add email connection status to profile | `app/profile/page.tsx` |
| 3 | Build email preview component | `components/EmailPreview.tsx` |
| 4 | Add attachment upload UI | `components/AttachmentUpload.tsx` |
| 5 | Connect WebSocket for real-time updates | `hooks/useEmailStream.ts` |

---

## MCP/RAG Assessment

### Do We Need MCP (Model Context Protocol)?

**Answer: No, MCP is not needed for this feature.**

**Reasoning:**
- MCP is useful for standardizing tool access across different AI agents
- Our custom LangChain tools already provide this functionality
- Gmail API is well-documented and stable
- We don't need external tool discovery or standardization at this point

**When MCP Might Be Useful (Future):**
- If we want to make our email tools available to other AI systems
- If we adopt a multi-agent architecture where different services need tool access
- If we participate in a broader ecosystem of MCP-compatible tools

### Do We Need RAG (Retrieval-Augmented Generation)?

**Answer: No, RAG is not needed for the email feature itself.**

**Reasoning:**
- Email drafting is primarily generation-based, not retrieval-based
- We generate email content from user requests and tool outputs
- We don't need semantic search over past emails (initially)

**When RAG Might Be Useful (Future):**
- If we want "search my past emails" functionality
- If we want to provide context from previous emails when drafting new ones
- If we want to build an "email assistant" that can suggest replies based on history

### What We DO Need

| Component | Purpose |
|-----------|---------|
| **LangChain Tools** | Standard interface for Gmail API operations |
| **LangGraph** | Workflow orchestration with human-in-the-loop |
| **LLM Generation** | Email content creation and refinement |
| **PostgreSQL** | Token storage, drafts, sent email history |
| **Gmail API** | Actual email sending |
| **OAuth 2.0** | User authentication and token management |

---

## Summary

This email feature will provide:

1. **Secure Authentication** - Gmail OAuth 2.0 with encrypted token storage
2. **Natural Language Emailing** - "email 'Happy birthday' to sakil@gmail.com"
3. **Content Generation** - "fetch jira tickets and email summary"
4. **Human-in-the-Loop** - Preview before sending, multi-step refinement
5. **Attachments** - Support for file uploads
6. **Connected Services UI** - Show Gmail connection status in profile
7. **Email History** - Track sent emails
8. **Rate Limiting** - Prevent abuse
9. **Token Refresh** - Automatic token management

**Total Estimated Time:** 14-18 days for full implementation
**Key Files:** 30+ new/modified files
**New Database Tables:** 3 (user_email_connections, email_drafts, sent_emails)
