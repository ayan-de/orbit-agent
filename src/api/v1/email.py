"""
Email API endpoints for Gmail OAuth and email management.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from src.storage.token_store import get_token_store
from src.tools.gmail.send import SendEmailTool
from src.config import settings
from src.services.gmail_oauth import (
    get_oauth_authorization_url,
    exchange_code_for_tokens,
    refresh_access_token
)


router = APIRouter(prefix="/email", tags=["Email"])


# ============================================================================
# Schemas
# ============================================================================

class EmailConnectionStatus(BaseModel):
    """Email connection status response."""
    is_connected: bool
    email_address: Optional[str] = None
    provider: Optional[str] = None
    connected_at: Optional[str] = None


class EmailDraft(BaseModel):
    """Email draft."""
    to_email: str
    subject: str = ""
    body: str
    cc_emails: Optional[List[str]] = None
    attachments: Optional[List[dict]] = None


class SendEmailRequest(BaseModel):
    """Send email request."""
    user_id: str
    to_email: str
    subject: str
    body: str
    cc_emails: Optional[List[str]] = None
    attachments: Optional[List[dict]] = None


class SendEmailResponse(BaseModel):
    """Send email response."""
    success: bool
    message: str
    sent_email_id: Optional[str] = None
    sent_at: Optional[str] = None


class RefineEmailRequest(BaseModel):
    """Refine email request."""
    draft_id: Optional[int] = None
    refinement_request: str


class SentEmail(BaseModel):
    """Sent email record."""
    to_email: str
    subject: str
    sent_at: str
    has_attachments: bool = False


class SentEmailsResponse(BaseModel):
    """Sent emails list response."""
    emails: List[SentEmail]
    total: int
    page: int
    limit: int


# ============================================================================
# Email Connection Management
# ============================================================================

@router.get("/status", response_model=EmailConnectionStatus)
async def get_email_status(user_id: str = "user") -> None:
    """
    Get user's email connection status.

    Args:
        user_id: User identifier (query parameter)

    Returns:
        Connection status with email address and provider
    """
    token_store = get_token_store()
    status = token_store.get_connection_status(user_id)

    return EmailConnectionStatus(**status)


@router.post("/disconnect")
async def disconnect_email(user_id: str = "user") -> None:
    """
    Disconnect email service.

    Args:
        user_id: User identifier (query parameter)

    Returns:
        Success message
    """
    token_store = get_token_store()
    token_store.delete_tokens(user_id)

    return {"success": True, "message": "Email service disconnected"}


# ============================================================================
# Email Drafting & Sending
# ============================================================================

@router.post("/draft", response_model=dict)
async def create_email_draft(draft: EmailDraft) -> None:
    """
    Create or update an email draft.

    Note: In this simplified implementation, drafts are stored in AgentState
    during the LangGraph workflow. This endpoint is provided for API
    compatibility but primarily serves as a placeholder for frontend integration.

    Args:
        draft: Email draft data

    Returns:
        Draft status
    """
    # In the full implementation, this would store to database
    # For now, drafts are stored in AgentState (session-scoped)
    return {
        "status": "draft",
        "message": "Draft created (stored in session)",
        "note": "Drafts are stored in AgentState for the current session"
    }


@router.get("/draft/{draft_id}", response_model=dict)
async def get_email_draft(draft_id: int) -> None:
    """
    Get email draft details.

    Note: Drafts are session-scoped in AgentState.

    Args:
        draft_id: Draft ID

    Returns:
        Draft details
    """
    # In full implementation, fetch from database
    # For now, return placeholder
    return {
        "id": draft_id,
        "status": "draft",
        "message": "Draft is stored in current session"
    }


@router.post("/send", response_model=SendEmailResponse)
async def send_email(request: SendEmailRequest) -> None:
    """
    Send a drafted email via Gmail API.

    Args:
        request: Send email request

    Returns:
        Send result with Gmail message ID
    """
    # Check if user is connected
    token_store = get_token_store()
    connection_status = token_store.get_connection_status(request.user_id)

    if not connection_status["is_connected"]:
        raise HTTPException(
            status_code=401,
            detail="Gmail not connected. Please connect your Gmail account first."
        )

    # Validate email
    from src.utils.email_validation import validate_recipient
    is_valid, error = validate_recipient(request.to_email)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Create Gmail tool
    gmail_tool = SendEmailTool()

    try:
        # Send email
        result = await gmail_tool._arun(
            user_id=request.user_id,
            to_email=request.to_email,
            subject=request.subject,
            body=request.body,
            cc_emails=request.cc_emails,
            attachments=request.attachments
        )

        # Extract message ID
        message_id = None
        if "Message ID:" in result:
            message_id = result.split("Message ID: ")[1]

        return SendEmailResponse(
            success=True,
            message=result,
            sent_email_id=message_id,
            sent_at=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/refine", response_model=dict)
async def refine_email(request: RefineEmailRequest) -> None:
    """
    Refine an email draft.

    Note: In the LangGraph workflow, refinement is handled by the
    email_refinement node. This endpoint is for API compatibility.

    Args:
        request: Refine request

    Returns:
        Refinement result
    """
    # In the LangGraph workflow, refinement happens via user messages
    # This endpoint provides a way to trigger refinement via API
    return {
        "status": "refined",
        "refinement_request": request.refinement_request,
        "message": "Email refinement request processed"
    }


# ============================================================================
# Email History
# ============================================================================

@router.get("/sent", response_model=SentEmailsResponse)
async def get_sent_emails(
    user_id: str = "user",
    page: int = 1,
    limit: int = 20
) -> None:
    """
    Get user's sent emails with pagination.

    Args:
        user_id: User identifier
        page: Page number (default 1)
        limit: Items per page (default 20)

    Returns:
        List of sent emails with pagination info
    """
    # Read from log file if exists
    from pathlib import Path
    import json

    log_file = Path("data/sent_emails.log")
    emails = []

    if log_file.exists():
        try:
            with open(log_file, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            if entry.get("user_id") == user_id:
                                emails.append(SentEmail(
                                    to_email=entry.get("to_email", ""),
                                    subject=entry.get("subject", ""),
                                    sent_at=entry.get("sent_at", ""),
                                    has_attachments=False  # Not tracked in log
                                ))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Error reading sent emails: {e}")

    # Pagination
    total = len(emails)
    start = (page - 1) * limit
    end = start + limit
    paginated_emails = emails[start:end]

    return SentEmailsResponse(
        emails=paginated_emails,
        total=total,
        page=page,
        limit=limit
    )


# ============================================================================
# OAuth Helper Endpoints (for development/testing)
# ============================================================================

@router.get("/oauth/authorize")
async def get_authorization_url(
    user_id: str = Query(..., description="User identifier for state"),
    redirect_uri: Optional[str] = Query(None, description="OAuth redirect URI")
) -> dict:
    """
    Generate Gmail OAuth 2.0 authorization URL.

    For development/testing. In production, use NestJS Bridge OAuth flow.

    Args:
        user_id: User identifier for state parameter
        redirect_uri: OAuth redirect URI (optional)

    Returns:
        Authorization URL to redirect user to
    """
    try:
        auth_url = get_oauth_authorization_url(
            user_id=user_id,
            redirect_uri=redirect_uri
        )
        return {
            "success": True,
            "authorization_url": auth_url,
            "user_id": user_id
        }
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oauth/callback")
async def oauth_callback(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="State parameter (user_id)"),
    redirect_uri: Optional[str] = Query(None, description="OAuth redirect URI")
) -> dict:
    """
    Exchange OAuth authorization code for tokens.

    For development/testing. In production, NestJS Bridge handles this.

    Args:
        code: Authorization code from Google
        state: User ID from state parameter
        redirect_uri: OAuth redirect URI (optional)

    Returns:
        Token storage result
    """
    try:
        result = await exchange_code_for_tokens(
            code=code,
            user_id=state,
            redirect_uri=redirect_uri
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OAuth callback failed: {str(e)}"
        )


@router.post("/oauth/refresh")
async def refresh_tokens(
    user_id: str = Query(..., description="User identifier")
) -> dict:
    """
    Refresh expired access token.

    Args:
        user_id: User identifier

    Returns:
        New access token and expiry
    """
    try:
        result = await refresh_access_token(user_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/oauth/store-tokens")
async def store_oauth_tokens(request: dict) -> dict:
    """
    Store OAuth tokens (for development/testing).

    This endpoint allows manually storing OAuth tokens for testing purposes.
    In production, this would be handled by the NestJS Bridge OAuth flow.

    Args:
        request: JSON body with tokens

    Returns:
        Storage result
    """
    from datetime import datetime, timedelta

    user_id = request.get("user_id")
    email_address = request.get("email_address")
    access_token = request.get("access_token")
    refresh_token = request.get("refresh_token")
    expires_in = request.get("expires_in", 3600)

    expires_at = datetime.now() + timedelta(seconds=expires_in)

    token_store = get_token_store()
    token_store.store_tokens(
        user_id=user_id,
        email_address=email_address,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        provider="gmail"
    )

    return {
        "success": True,
        "message": "Tokens stored successfully",
        "email_address": email_address,
        "expires_at": expires_at.isoformat()
    }
