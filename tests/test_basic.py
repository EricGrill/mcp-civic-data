"""Basic import tests for MCP Civic Data."""

import asyncio
import unittest


class TestHTTPUtils(unittest.TestCase):
    """Tests for HTTP utility functions."""

    def test_import(self):
        """Test that http module can be imported."""
        from mcp_govt_api.utils import http

        self.assertIsNotNone(http)


class TestHTTPClientLifecycle(unittest.TestCase):
    """Tests for HTTP client lifecycle management."""

    def test_http_lifespan_closes_client(self):
        """Test that http_lifespan context manager closes the HTTP client."""
        from mcp_govt_api.utils.http import http_client, http_lifespan

        async def run():
            # Client should start open
            assert not http_client.is_closed

            async with http_lifespan(None):
                # Client should still be open during lifespan
                assert not http_client.is_closed

            # Client should be closed after lifespan exits
            assert http_client.is_closed

        asyncio.run(run())

    def test_server_has_lifespan_configured(self):
        """Test that the MCP server is configured with the HTTP lifespan."""
        from mcp_govt_api.server import mcp
        from mcp_govt_api.utils.http import http_lifespan

        self.assertEqual(mcp.settings.lifespan, http_lifespan)


class TestConfig(unittest.TestCase):
    """Tests for configuration module."""

    def test_import(self):
        """Test that config module can be imported."""
        from mcp_govt_api.utils import config

        self.assertIsNotNone(config)


class TestServer(unittest.TestCase):
    """Tests for MCP server."""

    def test_import(self):
        """Test that server module can be imported."""
        from mcp_govt_api import server

        self.assertIsNotNone(server)


if __name__ == "__main__":
    unittest.main()
