"""
Gmail OAuth 2.0 helper for Python side.

This module provides helper functions for OAuth flow that would typically
be handled by the NestJS Bridge. For development/testing, these can be
used directly.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequestMock

from src.config import settings
from src.storage.token_store import get_token_store


def get_oauth_authorization_url(
    user_id: str,
    redirect_uri: Optional[str] = None
) -> str:
    """
    Generate Gmail OAuth 2.0 authorization URL.

    Args:
        user_id: User identifier for state parameter
        redirect_uri: OAuth redirect URI (defaults to config)

    Returns:
        Authorization URL to redirect user to
    """
    if not settings.GMAIL_CLIENT_ID or not settings.GMAIL_CLIENT_SECRET:
        raise ValueError(
            "Gmail OAuth credentials not configured. "
            "Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env"
        )

    # OAuth configuration
    client_config = {
        "installed": {
            "client_id": settings.GMAIL_CLIENT_ID,
            "client_secret": settings.GMAIL_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri or settings.GMAIL_REDIRECT_URI],
        }
    }

    # Create OAuth flow
    flow = InstalledAppFlow.from_client_config(
        client_config,
        scopes=settings.GMAIL_SCOPES
    )

    # Generate authorization URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',  # Get refresh token
        include_granted_scopes='true',
        state=user_id  # Pass user_id for CSRF protection
    )

    return auth_url


async def exchange_code_for_tokens(
    code: str,
    user_id: str,
    redirect_uri: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exchange OAuth authorization code for tokens.

    Args:
        code: Authorization code from OAuth callback
        user_id: User identifier
        redirect_uri: OAuth redirect URI (defaults to config)

    Returns:
        Dict with tokens and user email
    """
    if not settings.GMAIL_CLIENT_ID or not settings.GMAIL_CLIENT_SECRET:
        raise ValueError(
            "Gmail OAuth credentials not configured. "
            "Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env"
        )

    # OAuth configuration
    client_config = {
        "installed": {
            "client_id": settings.GMAIL_CLIENT_ID,
            "client_secret": settings.GMAIL_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri or settings.GMAIL_REDIRECT_URI],
        }
    }

    # Create OAuth flow
    flow = InstalledAppFlow.from_client_config(
        client_config,
        scopes=settings.GMAIL_SCOPES
    )

    # Exchange code for tokens
    flow.fetch_token(code=code)

    # Get credentials
    credentials = flow.credentials

    # Get user email from Gmail API
    try:
        gmail = build("gmail", "v1", credentials=credentials)
        profile = gmail.users().getProfile(userId="me").execute()
        email_address = profile.get("emailAddress")
    except Exception as e:
        # Fallback: use a default or raise error
        print(f"Warning: Could not fetch Gmail profile: {e}")
        email_address = f"user_{user_id}@gmail.com"

    # Calculate expiry time
    if credentials.expiry:
        expires_at = credentials.expiry
    else:
        expires_at = datetime.now() + timedelta(hours=1)

    # Store tokens
    token_store = get_token_store()
    token_store.store_tokens(
        user_id=user_id,
        email_address=email_address,
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        expires_at=expires_at,
        provider="gmail"
    )

    return {
        "success": True,
        "email_address": email_address,
        "expires_at": expires_at.isoformat(),
        "user_id": user_id
    }


async def refresh_access_token(user_id: str) -> Dict[str, Any]:
    """
    Refresh expired access token using refresh token.

    Args:
        user_id: User identifier

    Returns:
        Dict with new access token and expiry
    """
    token_store = get_token_store()
    tokens = token_store.get_tokens(user_id)

    if not tokens:
        raise ValueError(f"No tokens found for user {user_id}")

    if not tokens.get("refresh_token"):
        raise ValueError("No refresh token available")

    # Create credentials from stored refresh token
    credentials = Credentials(
        token=None,  # Will be refreshed
        refresh_token=tokens["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GMAIL_CLIENT_ID,
        client_secret=settings.GMAIL_CLIENT_SECRET,
        scopes=settings.GMAIL_SCOPES,
        expiry=None
    )

    # Refresh the token
    from google.auth.transport.requests import Request
    credentials.refresh(Request())

    # Update token store with new access token
    token_store.update_access_token(
        user_id=user_id,
        access_token=credentials.token,
        expires_at=credentials.expiry or datetime.now() + timedelta(hours=1)
    )

    return {
        "success": True,
        "access_token": credentials.token,
        "expires_at": (credentials.expiry or datetime.now() + timedelta(hours=1)).isoformat()
    }


def get_gmail_credentials(user_id: str) -> Optional[Credentials]:
    """
    Get Gmail credentials for a user, refreshing if needed.

    Args:
        user_id: User identifier

    Returns:
        Credentials object or None if not connected
    """
    token_store = get_token_store()
    tokens = token_store.get_tokens(user_id)

    if not tokens:
        return None

    # Check if token needs refresh (expires within 5 minutes)
    now = datetime.now()
    expires_at = tokens.get("token_expires_at", now)
    needs_refresh = expires_at <= now + timedelta(minutes=5)

    if needs_refresh:
        # Token needs refresh - attempt automatic refresh
        try:
            from google.auth.transport.requests import Request

            creds = Credentials(
                token=None,
                refresh_token=tokens["refresh_token"],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GMAIL_CLIENT_ID,
                client_secret=settings.GMAIL_CLIENT_SECRET,
                scopes=settings.GMAIL_SCOPES,
            )
            creds.refresh(Request())

            # Update token store with new access token
            new_expires_at = creds.expiry or (now + timedelta(hours=1))
            token_store.update_access_token(
                user_id=user_id,
                access_token=creds.token,
                expires_at=new_expires_at,
            )

            return creds
        except Exception as e:
            print(f"Token refresh failed for user {user_id}: {e}")
            return None

    # Create credentials
    return Credentials(
        token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GMAIL_CLIENT_ID,
        client_secret=settings.GMAIL_CLIENT_SECRET,
        scopes=settings.GMAIL_SCOPES,
        expiry=tokens.get("token_expires_at")
    )


def disconnect_oauth(user_id: str) -> bool:
    """
    Disconnect OAuth for a user.

    Args:
        user_id: User identifier

    Returns:
        True if disconnected, False otherwise
    """
    try:
        token_store = get_token_store()
        token_store.delete_tokens(user_id)
        return True
    except Exception as e:
        print(f"Error disconnecting OAuth: {e}")
        return False


# ============================================================================
# OAuth Setup Instructions
# ============================================================================

OAUTH_SETUP_INSTRUCTIONS = """
## Gmail OAuth 2.0 Setup Instructions

### 1. Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Create a new project or select existing one
3. Navigate to: APIs & Services → Credentials

### 2. Configure OAuth Consent Screen

1. Click "OAuth consent screen"
2. Fill in:
   - App name: "Orbit AI Agent"
   - User support email: your email
   - Developer contact: your email
3. Add Scopes:
   - https://www.googleapis.com/auth/gmail.send
4. Save

### 3. Create OAuth 2.0 Client ID

1. Click "Create Credentials" → "OAuth client ID"
2. Application type: "Web application"
3. Name: "Orbit AI Agent"
4. Authorized redirect URIs:
   - http://localhost:3001/auth/gmail/callback (development)
   - Your production callback URL
5. Copy Client ID and Client Secret

### 4. Configure Environment Variables

Add to your `.env` file:

```
GMAIL_CLIENT_ID=your-client-id-here
GMAIL_CLIENT_SECRET=your-client-secret-here
GMAIL_REDIRECT_URI=http://localhost:3001/auth/gmail/callback
GMAIL_SCOPES=["https://www.googleapis.com/auth/gmail.send"]
```

### 5. OAuth Flow

#### Development (Direct Python)

```python
from src.services.gmail_oauth import get_oauth_authorization_url, exchange_code_for_tokens

# Get authorization URL
auth_url = get_oauth_authorization_url(user_id="user123")
print(f"Visit: {auth_url}")

# After user authorizes, get code from callback
# Then exchange for tokens:
result = await exchange_code_for_tokens(code="auth_code_here", user_id="user123")
```

#### Production (via NestJS Bridge)

1. User clicks "Connect Gmail" in frontend
2. Frontend redirects to NestJS: `/auth/gmail/authorize`
3. NestJS generates auth URL and redirects to Google
4. User authorizes on Google
5. Google redirects back to NestJS callback with code
6. NestJS exchanges code for tokens
7. NestJS calls Python API: `/api/v1/email/oauth/store-tokens`

### Testing OAuth

Use the development endpoint to manually store tokens:

```bash
curl -X POST http://localhost:8000/api/v1/email/oauth/store-tokens \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "test_user",
    "email_address": "your@gmail.com",
    "access_token": "ya29.a0...",
    "refresh_token": "1//0g...",
    "expires_in": 3600
  }'
```

### Important Notes

1. **Scopes**: We only request `gmail.send` scope for security
2. **Refresh Tokens**: Set `access_type=offline` to get refresh tokens
3. **State Parameter**: Pass user_id for CSRF protection
4. **Token Storage**: Tokens are encrypted and stored in `data/tokens.json`
5. **Token Refresh**: Implement refresh before expiry (check 5 minutes before)
"""
