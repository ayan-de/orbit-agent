"""
Authentication Middleware for Orbit Agent

Supports multiple authentication methods:
- API Key authentication (for service-to-service)
- JWT authentication (for user sessions)
"""

import logging
import os
from typing import Optional, Callable

from fastapi import Request, Response, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# =============================================================================
# Configuration
# =============================================================================

def get_jwt_secret() -> str:
    """Get JWT secret from settings or environment."""
    secret = settings.ENCRYPTION_KEY or os.getenv("JWT_SECRET")
    if not secret:
        raise ConfigurationError(
            "JWT secret not configured. Set ENCRYPTION_KEY or JWT_SECRET environment variable.",
            config_key="ENCRYPTION_KEY",
        )
    return secret


def get_api_keys() -> list[str]:
    """Get valid API keys from settings."""
    keys = []

    # Add Bridge API key if configured
    if settings.BRIDGE_API_KEY:
        keys.append(settings.BRIDGE_API_KEY)

    # Add additional keys from environment
    additional_keys = os.getenv("ORBIT_API_KEYS", "")
    if additional_keys:
        keys.extend([k.strip() for k in additional_keys.split(",") if k.strip()])

    return keys


# =============================================================================
# Token Validation
# =============================================================================

def validate_jwt_token(token: str) -> Optional[dict]:
    """
    Validate a JWT token and return payload.

    Args:
        token: JWT token string

    Returns:
        Token payload dict if valid, None otherwise
    """
    try:
        import jwt

        secret = get_jwt_secret()
        payload = jwt.decode(token, secret, algorithms=["HS256"])

        # Basic validation
        if not payload.get("sub"):
            logger.warning("JWT token missing 'sub' claim")
            return None

        return payload

    except jwt.ExpiredSignatureError:
        logger.info("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"JWT validation error: {e}")
        return None


def validate_api_key(api_key: str) -> bool:
    """
    Validate an API key.

    Args:
        api_key: API key string

    Returns:
        True if valid, False otherwise
    """
    valid_keys = get_api_keys()
    return api_key in valid_keys


# =============================================================================
# Authentication Dependencies
# =============================================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_header),
) -> Optional[dict]:
    """
    FastAPI dependency for authentication.

    Tries API key first, then JWT bearer token.

    Args:
        credentials: Bearer token credentials
        api_key: API key from header

    Returns:
        User info dict if authenticated, None otherwise

    Raises:
        HTTPException: If authentication fails
    """
    # Try API key first
    if api_key:
        if validate_api_key(api_key):
            return {
                "type": "api_key",
                "source": "service",
            }
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Try JWT bearer token
    if credentials:
        payload = validate_jwt_token(credentials.credentials)
        if payload:
            return {
                "type": "jwt",
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "permissions": payload.get("permissions", []),
            }
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # No authentication provided
    raise HTTPException(status_code=401, detail="Authentication required")


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_header),
) -> Optional[dict]:
    """
    FastAPI dependency for optional authentication.

    Returns user info if authenticated, None otherwise.
    Does not raise exception if not authenticated.
    """
    # Try API key first
    if api_key and validate_api_key(api_key):
        return {"type": "api_key", "source": "service"}

    # Try JWT bearer token
    if credentials:
        payload = validate_jwt_token(credentials.credentials)
        if payload:
            return {
                "type": "jwt",
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "permissions": payload.get("permissions", []),
            }

    return None


# =============================================================================
# Middleware
# =============================================================================

# Paths that don't require authentication
PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for FastAPI.

    Validates API key or JWT token on incoming requests.
    """

    def __init__(self, app, public_paths: Optional[set] = None):
        super().__init__(app)
        self.public_paths = public_paths or PUBLIC_PATHS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip auth for public paths
        if request.url.path in self.public_paths:
            return await call_next(request)

        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            if validate_api_key(api_key):
                # Add auth info to request state
                request.state.user = {"type": "api_key", "source": "service"}
                return await call_next(request)
            else:
                logger.warning(f"Invalid API key from {request.client.host if request.client else 'unknown'}")
                return JSONResponse(
                    status_code=401,
                    content={"error": "AUTH_ERROR", "message": "Invalid API key"},
                )

        # Check for Bearer token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = validate_jwt_token(token)
            if payload:
                request.state.user = {
                    "type": "jwt",
                    "user_id": payload.get("sub"),
                    "email": payload.get("email"),
                    "permissions": payload.get("permissions", []),
                }
                return await call_next(request)
            else:
                return JSONResponse(
                    status_code=401,
                    content={"error": "AUTH_ERROR", "message": "Invalid or expired token"},
                )

        # No authentication provided
        return JSONResponse(
            status_code=401,
            content={"error": "AUTH_ERROR", "message": "Authentication required"},
        )


# =============================================================================
# Helper for Response
# =============================================================================

from fastapi.responses import JSONResponse


# =============================================================================
# Permission Checking
# =============================================================================

def require_permission(permission: str):
    """
    Dependency factory that requires a specific permission.

    Usage:
        @router.get("/admin")
        async def admin_endpoint(user = Depends(require_permission("admin"))):
            ...
    """
    async def check_permission(user: dict = Depends(get_current_user)) -> dict:
        if user.get("type") == "api_key":
            # API keys have all permissions
            return user

        user_permissions = user.get("permissions", [])
        if permission not in user_permissions and "admin" not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission} required"
            )
        return user

    return check_permission


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency that requires admin permission."""
    if user.get("type") == "api_key":
        return user

    if "admin" not in user.get("permissions", []):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
