"""Tests for the intelligent response caching system."""

import asyncio
import time
import unittest
from unittest.mock import patch

from mcp_govt_api.utils.cache import ResponseCache


def run(coro):
    """Helper to run an async coroutine in tests."""
    return asyncio.run(coro)


class TestCacheKeyGeneration(unittest.TestCase):
    """Tests for cache key generation."""

    def test_same_url_same_key(self):
        """Same URL produces the same key."""
        key1 = ResponseCache.make_key("https://api.example.com/data")
        key2 = ResponseCache.make_key("https://api.example.com/data")
        self.assertEqual(key1, key2)

    def test_different_url_different_key(self):
        """Different URLs produce different keys."""
        key1 = ResponseCache.make_key("https://api.example.com/a")
        key2 = ResponseCache.make_key("https://api.example.com/b")
        self.assertNotEqual(key1, key2)

    def test_same_params_same_key(self):
        """Same params produce the same key regardless of insertion order."""
        key1 = ResponseCache.make_key(
            "https://api.example.com/data",
            {"b": "2", "a": "1"},
        )
        key2 = ResponseCache.make_key(
            "https://api.example.com/data",
            {"a": "1", "b": "2"},
        )
        self.assertEqual(key1, key2)

    def test_different_params_different_key(self):
        """Different params produce different keys."""
        key1 = ResponseCache.make_key(
            "https://api.example.com/data",
            {"q": "test1"},
        )
        key2 = ResponseCache.make_key(
            "https://api.example.com/data",
            {"q": "test2"},
        )
        self.assertNotEqual(key1, key2)

    def test_none_params_vs_empty(self):
        """None params and no params produce the same key."""
        key1 = ResponseCache.make_key("https://api.example.com/data", None)
        key2 = ResponseCache.make_key("https://api.example.com/data")
        self.assertEqual(key1, key2)

    def test_key_is_hex_digest(self):
        """Key is a valid hex string of expected length (SHA-256 = 64 chars)."""
        key = ResponseCache.make_key("https://example.com")
        self.assertEqual(len(key), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in key))


class TestCacheHitMiss(unittest.TestCase):
    """Tests for cache hit and miss behavior."""

    def test_miss_on_empty_cache(self):
        """Get on an empty cache returns None."""
        cache = ResponseCache()
        result = run(cache.get("nonexistent"))
        self.assertIsNone(result)

    def test_hit_after_set(self):
        """Value is retrievable after set."""
        async def _test():
            cache = ResponseCache()
            await cache.set("key1", {"data": "value"})
            return await cache.get("key1")
        self.assertEqual(run(_test()), {"data": "value"})

    def test_miss_after_clear(self):
        """Clear removes all entries."""
        async def _test():
            cache = ResponseCache()
            await cache.set("key1", "value1")
            await cache.set("key2", "value2")
            await cache.clear()
            return (await cache.get("key1"), await cache.get("key2"))
        r1, r2 = run(_test())
        self.assertIsNone(r1)
        self.assertIsNone(r2)

    def test_overwrite_existing_key(self):
        """Setting the same key overwrites the previous value."""
        async def _test():
            cache = ResponseCache()
            await cache.set("key1", "old")
            await cache.set("key1", "new")
            return await cache.get("key1")
        self.assertEqual(run(_test()), "new")


class TestCacheTTLExpiration(unittest.TestCase):
    """Tests for TTL-based expiration."""

    def test_expired_entry_returns_none(self):
        """Entry past its TTL returns None."""
        async def _test():
            cache = ResponseCache(default_ttl=1)
            await cache.set("key1", "value", ttl=1)
            original = time.monotonic()
            with patch("mcp_govt_api.utils.cache.time.monotonic") as mock_time:
                mock_time.return_value = original + 2
                return await cache.get("key1")
        self.assertIsNone(run(_test()))

    def test_non_expired_entry_returns_value(self):
        """Entry within its TTL returns the value."""
        async def _test():
            cache = ResponseCache(default_ttl=300)
            await cache.set("key1", "value")
            return await cache.get("key1")
        self.assertEqual(run(_test()), "value")

    def test_custom_ttl_per_key(self):
        """Per-key TTL overrides the default."""
        async def _test():
            cache = ResponseCache(default_ttl=300)
            await cache.set("short", "val", ttl=1)
            await cache.set("long", "val", ttl=600)
            original = time.monotonic()
            with patch("mcp_govt_api.utils.cache.time.monotonic") as mock_time:
                mock_time.return_value = original + 2
                return (await cache.get("short"), await cache.get("long"))
        short_val, long_val = run(_test())
        self.assertIsNone(short_val)
        self.assertEqual(long_val, "val")


class TestCacheLRUEviction(unittest.TestCase):
    """Tests for LRU eviction when max_size is reached."""

    def test_evicts_lru_when_full(self):
        """Oldest entry is evicted when cache exceeds max_size."""
        async def _test():
            cache = ResponseCache(max_size=2, default_ttl=300)
            await cache.set("key1", "val1")
            await cache.set("key2", "val2")
            await cache.set("key3", "val3")
            return (
                await cache.get("key1"),
                await cache.get("key2"),
                await cache.get("key3"),
            )
        r1, r2, r3 = run(_test())
        self.assertIsNone(r1)
        self.assertEqual(r2, "val2")
        self.assertEqual(r3, "val3")

    def test_access_refreshes_lru_position(self):
        """Accessing an entry moves it to most-recently-used."""
        async def _test():
            cache = ResponseCache(max_size=2, default_ttl=300)
            await cache.set("key1", "val1")
            await cache.set("key2", "val2")
            # Access key1 to move it to MRU
            await cache.get("key1")
            # Now adding key3 should evict key2 (LRU), not key1
            await cache.set("key3", "val3")
            return (
                await cache.get("key1"),
                await cache.get("key2"),
                await cache.get("key3"),
            )
        r1, r2, r3 = run(_test())
        self.assertEqual(r1, "val1")
        self.assertIsNone(r2)
        self.assertEqual(r3, "val3")

    def test_max_size_respected(self):
        """Cache never exceeds max_size."""
        async def _test():
            cache = ResponseCache(max_size=3, default_ttl=300)
            for i in range(10):
                await cache.set(f"key{i}", f"val{i}")
            return await cache.stats()
        stats = run(_test())
        self.assertLessEqual(stats["size"], 3)


class TestCacheStats(unittest.TestCase):
    """Tests for cache statistics tracking."""

    def test_initial_stats(self):
        """Fresh cache has zero hits and misses."""
        cache = ResponseCache()
        stats = run(cache.stats())
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)
        self.assertEqual(stats["hit_rate"], 0.0)
        self.assertEqual(stats["size"], 0)

    def test_miss_increments_counter(self):
        """Cache miss increments the miss counter."""
        async def _test():
            cache = ResponseCache()
            await cache.get("missing")
            return await cache.stats()
        stats = run(_test())
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hits"], 0)

    def test_hit_increments_counter(self):
        """Cache hit increments the hit counter."""
        async def _test():
            cache = ResponseCache()
            await cache.set("key1", "value")
            await cache.get("key1")
            return await cache.stats()
        stats = run(_test())
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 0)

    def test_hit_rate_calculation(self):
        """Hit rate is calculated correctly."""
        async def _test():
            cache = ResponseCache()
            await cache.set("key1", "value")
            await cache.get("key1")     # hit
            await cache.get("key1")     # hit
            await cache.get("missing")  # miss
            return await cache.stats()
        stats = run(_test())
        self.assertAlmostEqual(stats["hit_rate"], 66.67, places=1)

    def test_reset_stats(self):
        """Reset clears hit/miss counters."""
        async def _test():
            cache = ResponseCache()
            await cache.set("key1", "value")
            await cache.get("key1")
            await cache.get("missing")
            await cache.reset_stats()
            return await cache.stats()
        stats = run(_test())
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)

    def test_stats_includes_size(self):
        """Stats report current cache size and max_size."""
        async def _test():
            cache = ResponseCache(max_size=100)
            await cache.set("a", 1)
            await cache.set("b", 2)
            return await cache.stats()
        stats = run(_test())
        self.assertEqual(stats["size"], 2)
        self.assertEqual(stats["max_size"], 100)


if __name__ == "__main__":
    unittest.main()
