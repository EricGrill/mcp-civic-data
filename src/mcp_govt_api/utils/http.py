from typing import Any
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import asyncio
import random

import httpx

from mcp_govt_api.utils.config import config
from mcp_govt_api.utils.errors import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
)

# HTTP status codes that are transient and safe to retry
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_JITTER = 0.5  # seconds

http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(config.timeout),
    follow_redirects=True,
    headers={"User-Agent": "mcp-civic-data/0.1.0"},
)


@asynccontextmanager
async def http_lifespan(_server: Any) -> AsyncIterator[None]:
    """Lifespan context manager that closes the HTTP client on shutdown."""
    try:
        yield None
    finally:
        await http_client.aclose()


def _is_retryable_error(exc: Exception) -> bool:
    """Determine if an exception represents a transient, retryable error."""
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS_CODES
    if isinstance(exc, (httpx.ConnectError, httpx.ReadError, httpx.WriteError)):
        return True
    return False


async def _retry_delay(attempt: int, base_delay: float = DEFAULT_BASE_DELAY) -> None:
    """Sleep with exponential backoff and jitter.

    Delay = base_delay * 2^attempt + random jitter to avoid thundering herd.
    """
    delay = base_delay * (2 ** attempt)
    jitter = random.uniform(0, DEFAULT_MAX_JITTER)
    await asyncio.sleep(delay + jitter)


def _raise_specific_error(last_exception: Exception | None, url: str) -> None:
    """Convert the last caught exception into a specific error type and raise."""
    if isinstance(last_exception, httpx.TimeoutException):
        raise TimeoutError(
            f"Request timed out after {config.timeout}s: {url}",
            url=url,
        ) from last_exception
    elif isinstance(last_exception, httpx.HTTPStatusError):
        status = last_exception.response.status_code
        body = last_exception.response.text[:200]
        if status in (401, 403):
            raise AuthenticationError(
                f"HTTP {status}: {body}", status_code=status, url=url,
            ) from last_exception
        elif status == 404:
            raise NotFoundError(
                f"HTTP 404: {body}", status_code=404, url=url,
            ) from last_exception
        elif status == 429:
            retry_after = last_exception.response.headers.get("Retry-After")
            raise RateLimitError(
                f"HTTP 429: {body}",
                url=url,
                retry_after=int(retry_after) if retry_after and retry_after.isdigit() else None,
            ) from last_exception
        elif 500 <= status < 600:
            raise ServerError(
                f"HTTP {status}: {body}", status_code=status, url=url,
            ) from last_exception
        else:
            raise APIError(
                f"HTTP {status}: {body}", status_code=status, url=url,
            ) from last_exception
    elif isinstance(last_exception, httpx.RequestError):
        raise APIError(f"Request failed: {last_exception}", url=url) from last_exception
    else:
        raise APIError(f"Request failed: {url}", url=url)


async def fetch_json(
    url: str,
    params: dict[str, Any] | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Any:
    """Fetch JSON from a URL with error handling and retry logic.

    Retries on transient errors (HTTP 429/5xx, timeouts, connection errors)
    with exponential backoff and jitter. Does not retry on client errors (4xx
    except 429).

    Args:
        url: The URL to fetch.
        params: Optional query parameters.
        max_retries: Maximum number of retry attempts (default 3).

    Returns:
        Parsed JSON response.

    Raises:
        AuthenticationError: On HTTP 401/403.
        NotFoundError: On HTTP 404.
        RateLimitError: On HTTP 429.
        ServerError: On HTTP 5xx.
        TimeoutError: On request timeout.
        APIError: On other request failures.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = await http_client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as e:
            last_exception = e

            if not _is_retryable_error(e):
                # Non-retryable error, fail immediately
                break

            if attempt < max_retries:
                print(
                    f"[retry] Attempt {attempt + 1}/{max_retries} failed for {url}: "
                    f"{e!r} -- retrying after backoff"
                )
                await _retry_delay(attempt)
            else:
                print(
                    f"[retry] All {max_retries} retries exhausted for {url}: {e!r}"
                )

    # Re-raise the last exception as a specific error type
    _raise_specific_error(last_exception, url)


async def fetch_with_retry(
    url: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    json: dict[str, Any] | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> httpx.Response:
    """Make an HTTP request with retry logic for non-JSON responses.

    This is a retry-capable wrapper around direct http_client usage, for cases
    where callers need the raw httpx.Response (e.g., SEC EDGAR, BLS).

    Args:
        url: The URL to request.
        method: HTTP method (default GET).
        params: Optional query parameters.
        headers: Optional request headers.
        json: Optional JSON body (for POST requests).
        max_retries: Maximum number of retry attempts (default 3).

    Returns:
        The httpx.Response object.

    Raises:
        Exception: After all retries are exhausted, or on non-retryable errors.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = await http_client.request(
                method, url, params=params, headers=headers, json=json
            )
            response.raise_for_status()
            return response
        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as e:
            last_exception = e

            if not _is_retryable_error(e):
                break

            if attempt < max_retries:
                print(
                    f"[retry] Attempt {attempt + 1}/{max_retries} failed for {url}: "
                    f"{e!r} -- retrying after backoff"
                )
                await _retry_delay(attempt)
            else:
                print(
                    f"[retry] All {max_retries} retries exhausted for {url}: {e!r}"
                )

    _raise_specific_error(last_exception, url)
