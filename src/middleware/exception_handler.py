"""
Exception Handler Middleware for FastAPI

Catches custom Orbit exceptions and converts them to proper HTTP responses.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.exceptions import OrbitError

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that catches OrbitError exceptions and converts them to JSON responses.

    This ensures consistent error response format across the API.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except OrbitError as exc:
            # Log the error
            logger.error(
                f"OrbitError: {exc.error_code} - {exc.message}",
                extra={"details": exc.details}
            )

            # Return JSON response
            return JSONResponse(
                status_code=exc.http_status,
                content=exc.to_dict(),
            )
        except Exception as exc:
            # Log unexpected errors
            logger.exception(f"Unexpected error: {exc}")

            # Return generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {},
                },
            )


def register_exception_handlers(app):
    """
    Register exception handlers with a FastAPI app.

    This is an alternative to using middleware, providing more
    fine-grained control over exception handling.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(OrbitError)
    async def orbit_error_handler(request: Request, exc: OrbitError):
        logger.error(
            f"OrbitError: {exc.error_code} - {exc.message}",
            extra={"details": exc.details, "path": request.url.path}
        )
        return JSONResponse(
            status_code=exc.http_status,
            content=exc.to_dict(),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception at {request.url.path}: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            },
        )
