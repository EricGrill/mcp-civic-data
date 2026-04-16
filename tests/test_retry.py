"""Tests for HTTP retry logic with exponential backoff."""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx


class TestFetchJsonRetry(unittest.TestCase):
    """Tests for fetch_json retry behavior."""

    def _make_response(self, status_code: int = 200, json_data=None, text: str = ""):
        """Create a mock httpx.Response."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = status_code
        response.text = text
        response.json.return_value = json_data or {}
        response.is_success = 200 <= status_code < 300
        response.headers = {}

        def raise_for_status():
            if status_code >= 400:
                raise httpx.HTTPStatusError(
                    f"HTTP {status_code}",
                    request=MagicMock(spec=httpx.Request),
                    response=response,
                )

        response.raise_for_status = raise_for_status
        return response

    def test_successful_request_no_retry(self):
        """Test that a successful request returns immediately without retrying."""
        from mcp_govt_api.utils.http import fetch_json, http_client

        mock_response = self._make_response(200, {"result": "ok"})

        async def run():
            with patch.object(http_client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response
                result = await fetch_json("https://api.example.com/data")

                self.assertEqual(result, {"result": "ok"})
                self.assertEqual(mock_get.call_count, 1)

        asyncio.run(run())

    def test_retry_on_503_then_success(self):
        """Test retry on HTTP 503 followed by a successful response."""
        from mcp_govt_api.utils.http import fetch_json, http_client

        fail_response = self._make_response(503, text="Service Unavailable")
        success_response = self._make_response(200, {"status": "recovered"})

        async def run():
            with (
                patch.object(http_client, "get", new_callable=AsyncMock) as mock_get,
                patch("mcp_govt_api.utils.http._retry_delay", new_callable=AsyncMock),
            ):
                mock_get.side_effect = [fail_response, success_response]
                result = await fetch_json("https://api.example.com/data")

                self.assertEqual(result, {"status": "recovered"})
                self.assertEqual(mock_get.call_count, 2)

        asyncio.run(run())

    def test_retry_on_timeout_then_success(self):
        """Test retry on connection timeout followed by a successful response."""
        from mcp_govt_api.utils.http import fetch_json, http_client

        success_response = self._make_response(200, {"data": "here"})

        async def run():
            with (
                patch.object(http_client, "get", new_callable=AsyncMock) as mock_get,
                patch("mcp_govt_api.utils.http._retry_delay", new_callable=AsyncMock),
            ):
                mock_get.side_effect = [
                    httpx.ReadTimeout("timed out"),
                    success_response,
                ]
                result = await fetch_json("https://api.example.com/data")

                self.assertEqual(result, {"data": "here"})
                self.assertEqual(mock_get.call_count, 2)

        asyncio.run(run())

    def test_max_retries_exceeded(self):
        """Test that exception is raised after all retries are exhausted."""
        from mcp_govt_api.utils.http import fetch_json, http_client

        fail_response = self._make_response(503, text="Service Unavailable")

        async def run():
            with (
                patch.object(http_client, "get", new_callable=AsyncMock) as mock_get,
                patch("mcp_govt_api.utils.http._retry_delay", new_callable=AsyncMock),
            ):
                mock_get.return_value = fail_response

                with self.assertRaises(Exception) as ctx:
                    await fetch_json(
                        "https://api.example.com/data", max_retries=3
                    )

                self.assertIn("503", str(ctx.exception))
                # 1 initial + 3 retries = 4 total calls
                self.assertEqual(mock_get.call_count, 4)

        asyncio.run(run())

    def test_no_retry_on_404(self):
        """Test that 404 errors are not retried (client error, not transient)."""
        from mcp_govt_api.utils.http import fetch_json, http_client

        fail_response = self._make_response(404, text="Not Found")

        async def run():
            with patch.object(http_client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = fail_response

                with self.assertRaises(Exception) as ctx:
                    await fetch_json("https://api.example.com/missing")

                self.assertIn("404", str(ctx.exception))
                # Should NOT retry -- only 1 call
                self.assertEqual(mock_get.call_count, 1)

        asyncio.run(run())

    def test_retry_on_429_rate_limit(self):
        """Test that HTTP 429 (rate limit) is retried with backoff."""
        from mcp_govt_api.utils.http import fetch_json, http_client

        rate_limit_response = self._make_response(429, text="Too Many Requests")
        success_response = self._make_response(200, {"data": "after_rate_limit"})

        async def run():
            with (
                patch.object(http_client, "get", new_callable=AsyncMock) as mock_get,
                patch(
                    "mcp_govt_api.utils.http._retry_delay", new_callable=AsyncMock
                ) as mock_delay,
            ):
                mock_get.side_effect = [
                    rate_limit_response,
                    rate_limit_response,
                    success_response,
                ]
                result = await fetch_json("https://api.example.com/data")

                self.assertEqual(result, {"data": "after_rate_limit"})
                self.assertEqual(mock_get.call_count, 3)
                # Verify backoff was called twice (attempt 0 and 1)
                self.assertEqual(mock_delay.call_count, 2)

        asyncio.run(run())

    def test_no_retry_on_400(self):
        """Test that 400 Bad Request is not retried."""
        from mcp_govt_api.utils.http import fetch_json, http_client

        fail_response = self._make_response(400, text="Bad Request")

        async def run():
            with patch.object(http_client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = fail_response

                with self.assertRaises(Exception) as ctx:
                    await fetch_json("https://api.example.com/bad")

                self.assertIn("400", str(ctx.exception))
                self.assertEqual(mock_get.call_count, 1)

        asyncio.run(run())

    def test_retry_on_connection_error(self):
        """Test retry on connection error followed by success."""
        from mcp_govt_api.utils.http import fetch_json, http_client

        success_response = self._make_response(200, {"connected": True})

        async def run():
            with (
                patch.object(http_client, "get", new_callable=AsyncMock) as mock_get,
                patch("mcp_govt_api.utils.http._retry_delay", new_callable=AsyncMock),
            ):
                mock_get.side_effect = [
                    httpx.ConnectError("Connection refused"),
                    success_response,
                ]
                result = await fetch_json("https://api.example.com/data")

                self.assertEqual(result, {"connected": True})
                self.assertEqual(mock_get.call_count, 2)

        asyncio.run(run())


class TestFetchWithRetry(unittest.TestCase):
    """Tests for fetch_with_retry (raw response) retry behavior."""

    def _make_response(self, status_code: int = 200, text: str = ""):
        """Create a mock httpx.Response."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = status_code
        response.text = text
        response.is_success = 200 <= status_code < 300
        response.headers = {}

        def raise_for_status():
            if status_code >= 400:
                raise httpx.HTTPStatusError(
                    f"HTTP {status_code}",
                    request=MagicMock(spec=httpx.Request),
                    response=response,
                )

        response.raise_for_status = raise_for_status
        return response

    def test_fetch_with_retry_success(self):
        """Test successful raw response fetch."""
        from mcp_govt_api.utils.http import fetch_with_retry, http_client

        mock_response = self._make_response(200, text="OK")

        async def run():
            with patch.object(
                http_client, "request", new_callable=AsyncMock
            ) as mock_req:
                mock_req.return_value = mock_response
                result = await fetch_with_retry("https://api.example.com/raw")

                self.assertEqual(result.status_code, 200)
                self.assertEqual(mock_req.call_count, 1)

        asyncio.run(run())

    def test_fetch_with_retry_post(self):
        """Test POST request with retry."""
        from mcp_govt_api.utils.http import fetch_with_retry, http_client

        fail_response = self._make_response(502, text="Bad Gateway")
        success_response = self._make_response(200, text="OK")

        async def run():
            with (
                patch.object(
                    http_client, "request", new_callable=AsyncMock
                ) as mock_req,
                patch("mcp_govt_api.utils.http._retry_delay", new_callable=AsyncMock),
            ):
                mock_req.side_effect = [fail_response, success_response]
                result = await fetch_with_retry(
                    "https://api.example.com/post",
                    method="POST",
                    json={"key": "value"},
                )

                self.assertEqual(result.status_code, 200)
                self.assertEqual(mock_req.call_count, 2)
                # Verify POST method was used
                mock_req.assert_called_with(
                    "POST",
                    "https://api.example.com/post",
                    params=None,
                    headers=None,
                    json={"key": "value"},
                )

        asyncio.run(run())


class TestRetryHelpers(unittest.TestCase):
    """Tests for retry helper functions."""

    def test_is_retryable_timeout(self):
        """Test that timeout errors are retryable."""
        from mcp_govt_api.utils.http import _is_retryable_error

        self.assertTrue(_is_retryable_error(httpx.ReadTimeout("timeout")))
        self.assertTrue(_is_retryable_error(httpx.ConnectTimeout("timeout")))

    def test_is_retryable_server_errors(self):
        """Test that 5xx errors are retryable."""
        from mcp_govt_api.utils.http import _is_retryable_error

        for code in [500, 502, 503, 504]:
            resp = MagicMock(spec=httpx.Response)
            resp.status_code = code
            exc = httpx.HTTPStatusError(
                f"HTTP {code}",
                request=MagicMock(spec=httpx.Request),
                response=resp,
            )
            self.assertTrue(
                _is_retryable_error(exc), f"Expected {code} to be retryable"
            )

    def test_is_not_retryable_client_errors(self):
        """Test that 4xx errors (except 429) are not retryable."""
        from mcp_govt_api.utils.http import _is_retryable_error

        for code in [400, 401, 403, 404, 405, 422]:
            resp = MagicMock(spec=httpx.Response)
            resp.status_code = code
            exc = httpx.HTTPStatusError(
                f"HTTP {code}",
                request=MagicMock(spec=httpx.Request),
                response=resp,
            )
            self.assertFalse(
                _is_retryable_error(exc), f"Expected {code} to NOT be retryable"
            )

    def test_is_retryable_429(self):
        """Test that 429 (rate limit) is retryable."""
        from mcp_govt_api.utils.http import _is_retryable_error

        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 429
        exc = httpx.HTTPStatusError(
            "HTTP 429",
            request=MagicMock(spec=httpx.Request),
            response=resp,
        )
        self.assertTrue(_is_retryable_error(exc))

    def test_is_retryable_connection_error(self):
        """Test that connection errors are retryable."""
        from mcp_govt_api.utils.http import _is_retryable_error

        self.assertTrue(_is_retryable_error(httpx.ConnectError("refused")))
        self.assertTrue(_is_retryable_error(httpx.ReadError("reset")))
        self.assertTrue(_is_retryable_error(httpx.WriteError("broken pipe")))


if __name__ == "__main__":
    unittest.main()
