"""Intelligent in-memory TTL cache for API responses.

Provides LRU eviction, per-key TTL, and thread-safe async access.
"""

import asyncio
import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CacheEntry:
    """A single cached value with expiration metadata."""

    value: Any
    expires_at: float
    created_at: float = field(default_factory=time.monotonic)

    @property
    def is_expired(self) -> bool:
        return time.monotonic() >= self.expires_at


class ResponseCache:
    """In-memory TTL cache with LRU eviction for API responses.

    Features:
        - Configurable max size with LRU eviction
        - Per-key TTL with a configurable default
        - Thread-safe via asyncio.Lock
        - Hit/miss statistics tracking
        - Cache key generation from URL + sorted params

    Usage:
        cache = ResponseCache(max_size=256, default_ttl=300)
        key = cache.make_key("https://api.example.com/data", {"q": "test"})

        cached = await cache.get(key)
        if cached is None:
            result = await fetch_from_api(...)
            await cache.set(key, result)
    """

    def __init__(
        self,
        max_size: int = 256,
        default_ttl: int = 300,
    ) -> None:
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    @staticmethod
    def make_key(url: str, params: dict[str, Any] | None = None) -> str:
        """Generate a deterministic cache key from URL and sorted params.

        Args:
            url: The request URL.
            params: Optional query parameters dict.

        Returns:
            A hex digest string suitable as a cache key.
        """
        key_parts: dict[str, Any] = {"url": url}
        if params:
            key_parts["params"] = dict(sorted(params.items()))
        raw = json.dumps(key_parts, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache.

        Returns None on miss or expiration. Counts hits and misses.
        Moves hit entries to the end (most-recently-used).

        Args:
            key: Cache key (from make_key).

        Returns:
            The cached value, or None if not found / expired.
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None
            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Store a value in the cache.

        Evicts the least-recently-used entry if max_size is exceeded.

        Args:
            key: Cache key (from make_key).
            value: The value to cache.
            ttl: Time-to-live in seconds. Uses default_ttl if None.
        """
        effective_ttl = ttl if ttl is not None else self._default_ttl
        async with self._lock:
            # Remove existing entry if present (to update position)
            if key in self._cache:
                del self._cache[key]

            # Evict LRU entries if at capacity
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)

            self._cache[key] = CacheEntry(
                value=value,
                expires_at=time.monotonic() + effective_ttl,
            )

    async def clear(self) -> None:
        """Remove all entries from the cache."""
        async with self._lock:
            self._cache.clear()

    async def stats(self) -> dict[str, Any]:
        """Return cache statistics.

        Returns:
            Dict with hits, misses, hit_rate, size, and max_size.
        """
        async with self._lock:
            total = self._hits + self._misses
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": (self._hits / total * 100) if total > 0 else 0.0,
                "size": len(self._cache),
                "max_size": self._max_size,
            }

    async def reset_stats(self) -> None:
        """Reset hit/miss counters."""
        async with self._lock:
            self._hits = 0
            self._misses = 0


# Module-level singleton used by fetch_json
response_cache = ResponseCache()
