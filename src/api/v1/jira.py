"""
Jira API endpoints for Jira authentication and connection management.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional

from src.storage.token_store import get_token_store
from src.config import settings


router = APIRouter(prefix="/jira", tags=["Jira"])


# ============================================================================
# Schemas
# ============================================================================

class JiraConnectionStatus(BaseModel):
    """Jira connection status response."""
    is_connected: bool
    base_url: Optional[str] = None
    username: Optional[str] = None
    provider: Optional[str] = None
    connected_at: Optional[str] = None


class StoreJiraTokensRequest(BaseModel):
    """Store Jira tokens request."""
    user_id: str
    base_url: str
    email: str
    api_token: str
    username: Optional[str] = None


# ============================================================================
# Jira Connection Management
# ============================================================================

@router.get("/status", response_model=JiraConnectionStatus)
async def get_jira_status(user_id: str = "user") -> None:
    """
    Get user's Jira connection status.

    Args:
        user_id: User identifier (query parameter)

    Returns:
        Connection status with Jira URL and username
    """
    token_store = get_token_store()
    status = token_store.get_connection_status(user_id)

    # Check if user has Jira tokens
    tokens = token_store.get_tokens(user_id)
    if tokens and tokens.get("provider") == "jira":
        status.is_connected = True
        status.provider = "jira"
        status.base_url = tokens.get("base_url")
        status.username = tokens.get("username")
        status.connected_at = tokens.get("created_at")

    return JiraConnectionStatus(**status)


@router.post("/disconnect")
async def disconnect_jira(user_id: str = "user") -> None:
    """
    Disconnect Jira service.

    Args:
        user_id: User identifier (query parameter)

    Returns:
        Success message
    """
    token_store = get_token_store()
    token_store.delete_tokens(user_id, provider="jira")

    return {"success": True, "message": "Jira service disconnected"}


# ============================================================================
# Jira OAuth Helper Endpoints (for development/testing)
# ============================================================================

@router.post("/oauth/store-tokens")
async def store_jira_tokens(request: StoreJiraTokensRequest) -> dict:
    """
    Store Jira API tokens (for development/testing).

    This endpoint allows manually storing Jira tokens for testing purposes.
    In production, this would be handled by the NestJS Bridge OAuth flow.

    Args:
        request: JSON body with tokens

    Returns:
        Storage result
    """
    from datetime import datetime, timedelta

    token_store = get_token_store()

    # Jira API tokens don't expire (but we can store an expiry)
    # Default to 1 year from now
    expires_at = datetime.now() + timedelta(days=365)

    # Store in token store (this will need to be extended to support Jira)
    # For now, we'll use the generic token storage structure
    # The token store will need to be updated to support Jira provider

    try:
        # Update token store to support Jira
        # For now, storing in a compatible format
        tokens = {
            "base_url": request.base_url,
            "email": request.email,
            "api_token": request.api_token,
            "username": request.username or request.email,
            "provider": "jira",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Store in token store (requires updating token store to support Jira)
        # For now, we'll use a simple approach
        if user_id not in token_store._tokens:
            token_store._tokens[user_id] = {}
        token_store._tokens[user_id]["jira"] = tokens
        token_store._save_tokens()

        return {
            "success": True,
            "message": "Jira tokens stored successfully",
            "base_url": request.base_url,
            "username": request.username or request.email,
            "expires_at": expires_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store Jira tokens: {str(e)}"
        )


@router.get("/oauth/authorize")
async def get_jira_authorize_url(
    user_id: str = Query(..., description="User identifier for state"),
    redirect_uri: Optional[str] = Query(None, description="OAuth redirect URI")
) -> dict:
    """
    Generate Jira OAuth 1.0a/2.0 authorization URL.

    For development/testing. In production, use NestJS Bridge OAuth flow.

    Args:
        user_id: User identifier for state parameter
        redirect_uri: OAuth redirect URI (optional)

    Returns:
        Authorization URL to redirect user to
    """
    try:
        # Jira OAuth 1.0a URL structure:
        # https://auth.atlassian.com/authorize?client_id={client_id}&response_type=code&state={state}
        # This would need Jira OAuth client ID to work
        # For now, return a placeholder message

        return {
            "success": True,
            "message": "Jira OAuth requires client_id configuration",
            "note": "Jira OAuth not fully implemented in Python Agent",
            "user_id": user_id
        }
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
