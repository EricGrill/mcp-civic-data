from typing import Any
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import logging

import httpx

from mcp_govt_api.utils.config import config

logger = logging.getLogger(__name__)

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
        logger.warning("Request timed out after %ds: %s", config.timeout, url)
        raise Exception(f"Request timed out after {config.timeout}s: {url}") from e
    except httpx.HTTPStatusError as e:
        logger.error(
            "HTTP %d error for %s: %s",
            e.response.status_code,
            url,
            e.response.text[:200],
        )
        raise Exception(f"HTTP {e.response.status_code}: {e.response.text[:200]}") from e
    except httpx.RequestError as e:
        logger.error("Request failed for %s: %s", url, e)
        raise Exception(f"Request failed: {e}") from e
