"""Custom exception hierarchy and error handling utilities for MCP Civic Data.

Provides specific exception types for different API failure modes,
a user-friendly error formatter, and a decorator for consistent
error handling across tool functions.
"""

import functools
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class APIError(Exception):
    """Base exception for all API-related errors.

    Attributes:
        status_code: HTTP status code, if applicable.
        url: The URL that was being requested, if available.
    """

    def __init__(
        self,
        message: str = "An API error occurred",
        *,
        status_code: int | None = None,
        url: str = "",
    ) -> None:
        self.status_code = status_code
        self.url = url
        super().__init__(message)


class RateLimitError(APIError):
    """Raised when the API returns HTTP 429 (Too Many Requests)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again shortly.",
        *,
        status_code: int = 429,
        url: str = "",
        retry_after: int | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, status_code=status_code, url=url)


class TimeoutError(APIError):  # noqa: A001 – intentional shadow of builtins.TimeoutError
    """Raised when a request times out."""

    def __init__(
        self,
        message: str = "The request timed out. The server may be slow or unavailable.",
        *,
        url: str = "",
    ) -> None:
        super().__init__(message, url=url)


class NotFoundError(APIError):
    """Raised when the requested resource is not found (HTTP 404)."""

    def __init__(
        self,
        message: str = "The requested resource was not found.",
        *,
        status_code: int = 404,
        url: str = "",
    ) -> None:
        super().__init__(message, status_code=status_code, url=url)


class AuthenticationError(APIError):
    """Raised for HTTP 401 (Unauthorized) or 403 (Forbidden)."""

    def __init__(
        self,
        message: str = "Authentication failed. Check your API key or credentials.",
        *,
        status_code: int | None = None,
        url: str = "",
    ) -> None:
        super().__init__(message, status_code=status_code, url=url)


class ServerError(APIError):
    """Raised for HTTP 5xx server-side errors."""

    def __init__(
        self,
        message: str = "The API server returned an internal error. Try again later.",
        *,
        status_code: int = 500,
        url: str = "",
    ) -> None:
        super().__init__(message, status_code=status_code, url=url)


# ---------------------------------------------------------------------------
# Error formatting helper
# ---------------------------------------------------------------------------

_ERROR_MESSAGES: dict[type, str] = {
    RateLimitError: "Rate limit exceeded — please wait a moment and retry.",
    TimeoutError: "Request timed out — the server may be slow or unavailable.",
    NotFoundError: "Resource not found — check the request parameters.",
    AuthenticationError: "Authentication failed — verify your API key or credentials.",
    ServerError: "Server error — the remote API is experiencing issues.",
    APIError: "An unexpected API error occurred.",
}


def format_error(error: Exception, context: str = "") -> str:
    """Return a user-friendly error message.

    Args:
        error: The exception that was caught.
        context: Optional context string (e.g. the tool or API name) that
            is prepended to the message for clarity.

    Returns:
        A formatted string suitable for returning from a tool function.
    """
    prefix = f"[{context}] " if context else ""

    for exc_type, template in _ERROR_MESSAGES.items():
        if isinstance(error, exc_type):
            detail = str(error) if str(error) != template else ""
            msg = template
            if detail and detail != msg:
                msg = f"{msg} Details: {detail}"
            return f"Error: {prefix}{msg}"

    # Fallback for non-API exceptions
    return f"Error: {prefix}{error}"


# ---------------------------------------------------------------------------
# Decorator for tool-level error handling
# ---------------------------------------------------------------------------


def handle_api_error(func: Callable[..., Any] | None = None, *, context: str = "") -> Any:
    """Decorator that wraps async tool functions with consistent error handling.

    Can be used with or without arguments::

        @handle_api_error
        async def my_tool(...): ...

        @handle_api_error(context="FDA API")
        async def my_tool(...): ...

    When an :class:`APIError` (or subclass) is raised inside the wrapped
    function, the decorator catches it and returns a user-friendly error
    string via :func:`format_error`.  Unexpected exceptions are also caught
    so that the MCP tool never surfaces a raw traceback.
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await fn(*args, **kwargs)
            except APIError as exc:
                ctx = context or fn.__name__
                logger.warning("API error in %s: %s", ctx, exc)
                return format_error(exc, context=ctx)
            except Exception as exc:
                ctx = context or fn.__name__
                logger.exception("Unexpected error in %s", ctx)
                return f"Error: [{ctx}] An unexpected error occurred: {exc}"

        return wrapper

    # Support both @handle_api_error and @handle_api_error(...)
    if func is not None:
        return decorator(func)
    return decorator
