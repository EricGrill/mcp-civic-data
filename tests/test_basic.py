"""Basic import tests for MCP Civic Data."""

import unittest


class TestHTTPUtils(unittest.TestCase):
    """Tests for HTTP utility functions."""

    def test_import(self):
        """Test that http module can be imported."""
        from mcp_govt_api.utils import http

        self.assertIsNotNone(http)


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
