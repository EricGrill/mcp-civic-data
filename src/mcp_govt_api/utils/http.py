from typing import Any
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import httpx

from mcp_govt_api.utils.config import config

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


async def fetch_json(url: str, params: dict[str, Any] | None = None) -> Any:
    """Fetch JSON from a URL with error handling."""
    try:
        response = await http_client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException as e:
        raise Exception(f"Request timed out after {config.timeout}s: {url}") from e
    except httpx.HTTPStatusError as e:
        raise Exception(f"HTTP {e.response.status_code}: {e.response.text[:200]}") from e
    except httpx.RequestError as e:
        raise Exception(f"Request failed: {e}") from e
