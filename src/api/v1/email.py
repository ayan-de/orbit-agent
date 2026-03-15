"""
Email OAuth API Endpoints.

Handles Gmail OAuth token storage and management.
These endpoints are called by the NestJS Bridge during OAuth flow.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional

from src.storage.token_store import get_token_store

router = APIRouter()


# ============================================================================
# Request/Response Schemas
# ============================================================================

class StoreTokensRequest(BaseModel):
    """Request to store OAuth tokens after successful authentication."""
    user_id: str = Field(..., description="User ID from Bridge")
    email_address: str = Field(..., description="User's Gmail address")
    access_token: str = Field(..., description="OAuth access token")
    refresh_token: str = Field(default="", description="OAuth refresh token")
    expires_in: int = Field(default=3600, description="Token expiration in seconds")


class StoreTokensResponse(BaseModel):
    """Response after storing tokens."""
    success: bool
    message: str
    email_address: str


class ConnectionStatusResponse(BaseModel):
    """Response for connection status check."""
    is_connected: bool
    email_address: Optional[str] = None
    provider: Optional[str] = None
    connected_at: Optional[str] = None


class DisconnectRequest(BaseModel):
    """Request to disconnect email integration."""
    user_id: str = Field(..., description="User ID from Bridge")


class DisconnectResponse(BaseModel):
    """Response after disconnecting."""
    success: bool
    message: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/oauth/store-tokens", response_model=StoreTokensResponse)
async def store_tokens(request: StoreTokensRequest):
    """
    Store OAuth tokens after successful Gmail authentication.

    Called by Bridge OAuth callback after user authorizes Gmail access.
    Tokens are encrypted and stored in the token store.
    """
    try:
        token_store = get_token_store()

        # Calculate expiration time
        expires_at = datetime.now() + timedelta(seconds=request.expires_in)

        # Store tokens
        token_store.store_tokens(
            user_id=request.user_id,
            email_address=request.email_address,
            access_token=request.access_token,
            refresh_token=request.refresh_token,
            expires_at=expires_at,
            provider="gmail"
        )

        return StoreTokensResponse(
            success=True,
            message=f"Tokens stored successfully for {request.email_address}",
            email_address=request.email_address
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store tokens: {str(e)}"
        )


@router.get("/status", response_model=ConnectionStatusResponse)
async def get_connection_status(user_id: str):
    """
    Get Gmail connection status for a user.

    Returns whether the user has connected their Gmail account.
    """
    try:
        token_store = get_token_store()
        status = token_store.get_connection_status(user_id, provider="gmail")

        return ConnectionStatusResponse(
            is_connected=status.get("is_connected", False),
            email_address=status.get("email_address"),
            provider=status.get("provider"),
            connected_at=status.get("connected_at")
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get connection status: {str(e)}"
        )


@router.post("/disconnect", response_model=DisconnectResponse)
async def disconnect_email(request: DisconnectRequest):
    """
    Disconnect Gmail integration for a user.

    Removes stored OAuth tokens.
    """
    try:
        token_store = get_token_store()

        # Check if user has tokens
        existing = token_store.get_tokens(request.user_id)
        if not existing:
            return DisconnectResponse(
                success=True,
                message="No Gmail connection found for this user"
            )

        # Delete tokens
        token_store.delete_tokens(request.user_id, provider="gmail")

        return DisconnectResponse(
            success=True,
            message=f"Gmail disconnected for {existing.get('email_address', 'user')}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect email: {str(e)}"
        )


@router.get("/list")
async def list_connections():
    """
    List all email connections (for debugging/admin).

    Returns all stored connections without sensitive tokens.
    """
    try:
        token_store = get_token_store()
        connections = token_store.list_connections()

        return {
            "count": len(connections),
            "connections": connections
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list connections: {str(e)}"
        )
