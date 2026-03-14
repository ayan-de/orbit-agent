"""
Rate Limiting Configuration for Orbit Agent

Uses slowapi (FastAPI-limiter) for rate limiting API endpoints.
"""

import logging
from typing import Optional

from fastapi import Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.config import settings

logger = logging.getLogger(__name__)


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting.

    Uses the following in order of preference:
    1. X-Forwarded-For header (first IP)
    2. X-Real-IP header
    3. API key (for service-to-service)
    4. Remote address

    Args:
        request: FastAPI request object

    Returns:
        Client identifier string
    """
    # Check for forwarded headers (behind reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (original client)
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Use API key if available (service-to-service)
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key[:8]}"  # Use first 8 chars for identification

    # Fall back to remote address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=["200/minute"],  # Default: 200 requests per minute
    storage_uri="memory://",  # Use in-memory storage (can be changed to Redis)
)


# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    # Agent endpoints - higher limit for normal use
    "agent_invoke": "60/minute",

    # Health check - very high limit
    "health": "1000/minute",

    # Authentication endpoints - strict limit
    "auth": "10/minute",

    # Webhook endpoints - medium limit
    "webhook": "100/minute",

    # Default for unspecified endpoints
    "default": "200/minute",
}


def get_rate_limit(endpoint_type: str) -> str:
    """
    Get rate limit for an endpoint type.

    Args:
        endpoint_type: Type of endpoint

    Returns:
        Rate limit string (e.g., "60/minute")
    """
    return RATE_LIMITS.get(endpoint_type, RATE_LIMITS["default"])


def setup_rate_limiting(app):
    """
    Setup rate limiting for a FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Add limiter to app state
    app.state.limiter = limiter

    # Add exception handler for rate limit exceeded
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add SlowAPI middleware
    app.add_middleware(SlowAPIMiddleware)

    logger.info("Rate limiting enabled with default limit: 200/minute")


# =============================================================================
# Custom Rate Limit Decorators
# =============================================================================

def rate_limit_agent():
    """Rate limit decorator for agent invoke endpoint."""
    return limiter.limit(RATE_LIMITS["agent_invoke"])


def rate_limit_auth():
    """Rate limit decorator for authentication endpoints."""
    return limiter.limit(RATE_LIMITS["auth"])


def rate_limit_webhook():
    """Rate limit decorator for webhook endpoints."""
    return limiter.limit(RATE_LIMITS["webhook"])


def rate_limit_custom(limit: str):
    """Custom rate limit decorator."""
    return limiter.limit(limit)


# =============================================================================
# Rate Limit Headers
# =============================================================================

class RateLimitHeadersMiddleware:
    """
    Middleware to add rate limit headers to responses.

    Adds:
    - X-RateLimit-Limit: Maximum requests per window
    - X-RateLimit-Remaining: Remaining requests in current window
    - X-RateLimit-Reset: Time when the rate limit resets
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # This is a simplified version - full implementation would
        # need to integrate with the limiter's storage
        await self.app(scope, receive, send)
