"""Tests for the custom exception hierarchy, error formatting, and decorator."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from mcp_govt_api.utils.errors import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    format_error,
    handle_api_error,
)

# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class TestExceptionHierarchy(unittest.TestCase):
    """Verify that every custom exception is a subclass of APIError."""

    def test_rate_limit_is_api_error(self):
        self.assertIsInstance(RateLimitError(), APIError)

    def test_timeout_is_api_error(self):
        self.assertIsInstance(TimeoutError(), APIError)

    def test_not_found_is_api_error(self):
        self.assertIsInstance(NotFoundError(), APIError)

    def test_authentication_is_api_error(self):
        self.assertIsInstance(AuthenticationError(), APIError)

    def test_server_error_is_api_error(self):
        self.assertIsInstance(ServerError(), APIError)

    def test_api_error_is_exception(self):
        self.assertIsInstance(APIError(), Exception)

    def test_api_error_attributes(self):
        err = APIError("test", status_code=418, url="http://example.com")
        self.assertEqual(err.status_code, 418)
        self.assertEqual(err.url, "http://example.com")
        self.assertEqual(str(err), "test")

    def test_rate_limit_retry_after(self):
        err = RateLimitError(retry_after=60)
        self.assertEqual(err.retry_after, 60)
        self.assertEqual(err.status_code, 429)

    def test_catch_subclass_with_base(self):
        """Catching APIError should catch all subclasses."""
        for exc_cls in (RateLimitError, TimeoutError, NotFoundError, AuthenticationError, ServerError):
            with self.assertRaises(APIError):
                raise exc_cls()


# ---------------------------------------------------------------------------
# Error formatting
# ---------------------------------------------------------------------------


class TestFormatError(unittest.TestCase):
    """Tests for the format_error helper."""

    def test_format_rate_limit_error(self):
        msg = format_error(RateLimitError())
        self.assertIn("Rate limit", msg)
        self.assertTrue(msg.startswith("Error:"))

    def test_format_timeout_error(self):
        msg = format_error(TimeoutError())
        self.assertIn("timed out", msg)

    def test_format_not_found_error(self):
        msg = format_error(NotFoundError())
        self.assertIn("not found", msg)

    def test_format_authentication_error(self):
        msg = format_error(AuthenticationError())
        self.assertIn("Authentication", msg)

    def test_format_server_error(self):
        msg = format_error(ServerError())
        self.assertIn("Server error", msg)

    def test_format_generic_api_error(self):
        msg = format_error(APIError("something broke"))
        self.assertIn("API error", msg)

    def test_format_with_context(self):
        msg = format_error(NotFoundError(), context="Census API")
        self.assertIn("[Census API]", msg)

    def test_format_non_api_exception(self):
        msg = format_error(ValueError("bad value"))
        self.assertIn("bad value", msg)
        self.assertTrue(msg.startswith("Error:"))

    def test_format_non_api_exception_with_context(self):
        msg = format_error(RuntimeError("oops"), context="test")
        self.assertIn("[test]", msg)
        self.assertIn("oops", msg)


# ---------------------------------------------------------------------------
# Decorator behaviour
# ---------------------------------------------------------------------------


class TestHandleApiErrorDecorator(unittest.IsolatedAsyncioTestCase):
    """Tests for the handle_api_error decorator."""

    async def test_passes_through_on_success(self):
        @handle_api_error
        async def good_tool():
            return "ok"

        result = await good_tool()
        self.assertEqual(result, "ok")

    async def test_catches_api_error(self):
        @handle_api_error
        async def bad_tool():
            raise NotFoundError("gone")

        result = await bad_tool()
        self.assertIn("not found", result)
        self.assertTrue(result.startswith("Error:"))

    async def test_catches_unexpected_exception(self):
        @handle_api_error
        async def bad_tool():
            raise RuntimeError("boom")

        result = await bad_tool()
        self.assertIn("unexpected error", result.lower())
        self.assertIn("boom", result)

    async def test_uses_custom_context(self):
        @handle_api_error(context="My API")
        async def bad_tool():
            raise ServerError("down")

        result = await bad_tool()
        self.assertIn("[My API]", result)

    async def test_decorator_preserves_function_name(self):
        @handle_api_error
        async def my_special_tool():
            return "hi"

        self.assertEqual(my_special_tool.__name__, "my_special_tool")

    async def test_decorator_with_args_preserves_function_name(self):
        @handle_api_error(context="ctx")
        async def my_special_tool():
            return "hi"

        self.assertEqual(my_special_tool.__name__, "my_special_tool")

    async def test_falls_back_to_function_name_as_context(self):
        @handle_api_error
        async def some_tool():
            raise RateLimitError()

        result = await some_tool()
        self.assertIn("[some_tool]", result)


# ---------------------------------------------------------------------------
# Status code -> exception type mapping (via fetch_json)
# ---------------------------------------------------------------------------


class TestFetchJsonErrorMapping(unittest.IsolatedAsyncioTestCase):
    """Verify that fetch_json raises the correct exception type for each status code."""

    def _mock_response(self, status_code: int, text: str = "error body", headers: dict | None = None) -> MagicMock:
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = status_code
        resp.text = text
        resp.headers = headers or {}

        # httpx raises HTTPStatusError from raise_for_status for 4xx/5xx
        http_error = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
        resp.raise_for_status.side_effect = http_error
        return resp

    @patch("mcp_govt_api.utils.http.http_client")
    async def test_401_raises_authentication_error(self, mock_client):
        from mcp_govt_api.utils.http import fetch_json

        mock_client.get = AsyncMock(return_value=self._mock_response(401))

        with self.assertRaises(AuthenticationError) as ctx:
            await fetch_json("https://api.example.com/test", max_retries=0)

        self.assertEqual(ctx.exception.status_code, 401)

    @patch("mcp_govt_api.utils.http.http_client")
    async def test_403_raises_authentication_error(self, mock_client):
        from mcp_govt_api.utils.http import fetch_json

        mock_client.get = AsyncMock(return_value=self._mock_response(403))

        with self.assertRaises(AuthenticationError) as ctx:
            await fetch_json("https://api.example.com/test", max_retries=0)

        self.assertEqual(ctx.exception.status_code, 403)

    @patch("mcp_govt_api.utils.http.http_client")
    async def test_404_raises_not_found_error(self, mock_client):
        from mcp_govt_api.utils.http import fetch_json

        mock_client.get = AsyncMock(return_value=self._mock_response(404))

        with self.assertRaises(NotFoundError):
            await fetch_json("https://api.example.com/missing", max_retries=0)

    @patch("mcp_govt_api.utils.http.http_client")
    async def test_429_raises_rate_limit_error(self, mock_client):
        from mcp_govt_api.utils.http import fetch_json

        mock_client.get = AsyncMock(
            return_value=self._mock_response(429, headers={"Retry-After": "30"})
        )

        with self.assertRaises(RateLimitError) as ctx:
            await fetch_json("https://api.example.com/limit", max_retries=0)

        self.assertEqual(ctx.exception.retry_after, 30)

    @patch("mcp_govt_api.utils.http.http_client")
    async def test_500_raises_server_error(self, mock_client):
        from mcp_govt_api.utils.http import fetch_json

        mock_client.get = AsyncMock(return_value=self._mock_response(500))

        with self.assertRaises(ServerError) as ctx:
            await fetch_json("https://api.example.com/broken", max_retries=0)

        self.assertEqual(ctx.exception.status_code, 500)

    @patch("mcp_govt_api.utils.http.http_client")
    async def test_503_raises_server_error(self, mock_client):
        from mcp_govt_api.utils.http import fetch_json

        mock_client.get = AsyncMock(return_value=self._mock_response(503))

        with self.assertRaises(ServerError) as ctx:
            await fetch_json("https://api.example.com/unavailable", max_retries=0)

        self.assertEqual(ctx.exception.status_code, 503)

    @patch("mcp_govt_api.utils.http.http_client")
    async def test_timeout_raises_timeout_error(self, mock_client):
        from mcp_govt_api.utils.http import fetch_json

        mock_client.get = AsyncMock(side_effect=httpx.ReadTimeout("timed out"))

        with self.assertRaises(TimeoutError):
            await fetch_json("https://api.example.com/slow", max_retries=0)

    @patch("mcp_govt_api.utils.http.http_client")
    async def test_connection_error_raises_api_error(self, mock_client):
        from mcp_govt_api.utils.http import fetch_json

        mock_client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with self.assertRaises(APIError):
            await fetch_json("https://api.example.com/down", max_retries=0)


if __name__ == "__main__":
    unittest.main()
