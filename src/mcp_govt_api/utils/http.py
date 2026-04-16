from typing import Any
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import httpx

from mcp_govt_api.utils.config import config
from mcp_govt_api.utils.cache import response_cache

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


async def fetch_json(
    url: str,
    params: dict[str, Any] | None = None,
    cache_ttl: int | None = None,
) -> Any:
    """Fetch JSON from a URL with error handling and optional caching.

    Args:
        url: The URL to fetch.
        params: Optional query parameters.
        cache_ttl: Cache time-to-live in seconds. Set to 0 to skip caching.
            When None (default), caching is not used (backwards compatible).
            Tools opt in by passing a positive value.

    Returns:
        Parsed JSON response.
    """
    use_cache = (
        config.cache_enabled
        and cache_ttl is not None
        and cache_ttl > 0
    )

    if use_cache:
        cache_key = response_cache.make_key(url, params)
        cached = await response_cache.get(cache_key)
        if cached is not None:
            return cached

    try:
        response = await http_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except httpx.TimeoutException as e:
        raise Exception(f"Request timed out after {config.timeout}s: {url}") from e
    except httpx.HTTPStatusError as e:
        raise Exception(f"HTTP {e.response.status_code}: {e.response.text[:200]}") from e
    except httpx.RequestError as e:
        raise Exception(f"Request failed: {e}") from e

    if use_cache:
        await response_cache.set(cache_key, data, ttl=cache_ttl)

    return data
