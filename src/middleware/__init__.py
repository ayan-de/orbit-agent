"""
Orbit Agent Middleware Package

Provides middleware components for the FastAPI application.
"""

from src.middleware.exception_handler import (
    ExceptionHandlerMiddleware,
    register_exception_handlers,
)
from src.middleware.auth import (
    AuthMiddleware,
    get_current_user,
    get_optional_user,
    require_permission,
    require_admin,
)
from src.middleware.rate_limit import (
    limiter,
    setup_rate_limiting,
    rate_limit_agent,
    rate_limit_auth,
    rate_limit_webhook,
    rate_limit_custom,
)

__all__ = [
    # Exception handling
    "ExceptionHandlerMiddleware",
    "register_exception_handlers",
    # Authentication
    "AuthMiddleware",
    "get_current_user",
    "get_optional_user",
    "require_permission",
    "require_admin",
    # Rate limiting
    "limiter",
    "setup_rate_limiting",
    "rate_limit_agent",
    "rate_limit_auth",
    "rate_limit_webhook",
    "rate_limit_custom",
]
