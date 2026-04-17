"""Tests for SEC EDGAR ticker-to-CIK resolution and tool functions."""

import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_govt_api.tools import sec

# Sample data mirroring SEC's company_tickers.json structure
SAMPLE_TICKERS_JSON = {
    "0": {"cik_str": "320193", "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": "789019", "ticker": "MSFT", "title": "Microsoft Corp"},
    "2": {"cik_str": "1018724", "ticker": "AMZN", "title": "Amazon Com Inc"},
    "3": {"cik_str": "1652044", "ticker": "GOOG", "title": "Alphabet Inc."},
    "4": {"cik_str": "1326801", "ticker": "META", "title": "Meta Platforms, Inc."},
}


def _make_response(json_data, status_code=200):
    """Create a mock httpx response."""
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    return resp


class TestPadCik(unittest.TestCase):
    """Tests for the _pad_cik helper."""

    def test_short_cik(self):
        self.assertEqual(sec._pad_cik("320193"), "0000320193")

    def test_already_padded(self):
        self.assertEqual(sec._pad_cik("0000320193"), "0000320193")

    def test_single_digit(self):
        self.assertEqual(sec._pad_cik("1"), "0000000001")

    def test_empty_string(self):
        self.assertEqual(sec._pad_cik(""), "0000000000")


class TestTickerCache(unittest.IsolatedAsyncioTestCase):
    """Tests for the ticker cache loading and resolution."""

    def setUp(self):
        sec._ticker_cache = {}
        sec._ticker_cache_time = 0.0

    @patch("mcp_govt_api.tools.sec.http_client")
    async def test_load_ticker_cache_populates_cache(self, mock_client):
        mock_client.get = AsyncMock(return_value=_make_response(SAMPLE_TICKERS_JSON))

        await sec._load_ticker_cache()

        self.assertIn("AAPL", sec._ticker_cache)
        self.assertEqual(sec._ticker_cache["AAPL"]["cik"], "320193")
        self.assertEqual(sec._ticker_cache["AAPL"]["name"], "Apple Inc.")
        self.assertEqual(len(sec._ticker_cache), 5)

    @patch("mcp_govt_api.tools.sec.http_client")
    async def test_cache_ttl_skips_refetch(self, mock_client):
        """Cache should not refetch if within TTL."""
        mock_client.get = AsyncMock(return_value=_make_response(SAMPLE_TICKERS_JSON))

        await sec._load_ticker_cache()
        self.assertEqual(mock_client.get.call_count, 1)

        # Second call should use cache (no new HTTP request)
        await sec._load_ticker_cache()
        self.assertEqual(mock_client.get.call_count, 1)

    @patch("mcp_govt_api.tools.sec.http_client")
    async def test_cache_expired_refetches(self, mock_client):
        """Cache should refetch after TTL expires."""
        mock_client.get = AsyncMock(return_value=_make_response(SAMPLE_TICKERS_JSON))

        await sec._load_ticker_cache()
        self.assertEqual(mock_client.get.call_count, 1)

        # Simulate cache expiry
        sec._ticker_cache_time = time.monotonic() - sec._CACHE_TTL - 1
        await sec._load_ticker_cache()
        self.assertEqual(mock_client.get.call_count, 2)

    @patch("mcp_govt_api.tools.sec.http_client")
    async def test_resolve_ticker_found(self, mock_client):
        mock_client.get = AsyncMock(return_value=_make_response(SAMPLE_TICKERS_JSON))

        result = await sec._resolve_ticker("AAPL")
        self.assertIsNotNone(result)
        self.assertEqual(result["cik"], "320193")
        self.assertEqual(result["name"], "Apple Inc.")

    @patch("mcp_govt_api.tools.sec.http_client")
    async def test_resolve_ticker_case_insensitive(self, mock_client):
        mock_client.get = AsyncMock(return_value=_make_response(SAMPLE_TICKERS_JSON))

        result = await sec._resolve_ticker("aapl")
        self.assertIsNotNone(result)
        self.assertEqual(result["cik"], "320193")

        result2 = await sec._resolve_ticker("Msft")
        self.assertIsNotNone(result2)
        self.assertEqual(result2["cik"], "789019")

    @patch("mcp_govt_api.tools.sec.http_client")
    async def test_resolve_ticker_not_found(self, mock_client):
        mock_client.get = AsyncMock(return_value=_make_response(SAMPLE_TICKERS_JSON))

        result = await sec._resolve_ticker("ZZZZZ")
        self.assertIsNone(result)


class TestGetCompanyFilings(unittest.IsolatedAsyncioTestCase):
    """Tests for the get_company_filings tool."""

    def setUp(self):
        sec._ticker_cache = {}
        sec._ticker_cache_time = 0.0

    async def test_no_args_returns_error(self):
        result = await sec.get_company_filings()
        self.assertIn("Error", result)

    @patch("mcp_govt_api.tools.sec.http_client")
    async def test_ticker_resolves_to_filings(self, mock_client):
        """Providing a ticker should resolve CIK and return filings."""
        submissions_data = {
            "name": "Apple Inc.",
            "cik": "320193",
            "filings": {
                "recent": {
                    "form": ["10-K", "10-Q"],
                    "filingDate": ["2024-11-01", "2024-08-02"],
                    "primaryDocDescription": ["Annual Report", "Quarterly Report"],
                    "accessionNumber": [
                        "0000320193-24-000001",
                        "0000320193-24-000002",
                    ],
                }
            },
        }

        async def mock_get(url, **kwargs):
            if "company_tickers" in url:
                return _make_response(SAMPLE_TICKERS_JSON)
            return _make_response(submissions_data)

        mock_client.get = AsyncMock(side_effect=mock_get)

        result = await sec.get_company_filings(ticker="AAPL")
        self.assertIn("Apple Inc.", result)
        self.assertIn("10-K", result)
        self.assertNotIn("please use the CIK number", result)

    @patch("mcp_govt_api.tools.sec.http_client")
    async def test_ticker_not_found_returns_error(self, mock_client):
        mock_client.get = AsyncMock(return_value=_make_response(SAMPLE_TICKERS_JSON))

        result = await sec.get_company_filings(ticker="ZZZZZ")
        self.assertIn("not found", result)
        self.assertIn("ZZZZZ", result)


class TestSearchCompany(unittest.IsolatedAsyncioTestCase):
    """Tests for the search_company tool."""

    def setUp(self):
        sec._ticker_cache = {}
        sec._ticker_cache_time = 0.0

    async def test_no_args_returns_error(self):
        result = await sec.search_company()
        self.assertIn("Error", result)

    @patch("mcp_govt_api.tools.sec.http_client")
    async def test_search_by_ticker_found(self, mock_client):
        mock_client.get = AsyncMock(return_value=_make_response(SAMPLE_TICKERS_JSON))

        result = await sec.search_company(ticker="MSFT")
        self.assertIn("Microsoft Corp", result)
        self.assertIn("789019", result)
        self.assertIn("Company Found", result)

    @patch("mcp_govt_api.tools.sec.http_client")
    async def test_search_by_ticker_not_found(self, mock_client):
        mock_client.get = AsyncMock(return_value=_make_response(SAMPLE_TICKERS_JSON))

        result = await sec.search_company(ticker="ZZZZZ")
        self.assertIn("not found", result)

    @patch("mcp_govt_api.tools.sec.http_client")
    async def test_search_by_name_found(self, mock_client):
        mock_client.get = AsyncMock(return_value=_make_response(SAMPLE_TICKERS_JSON))

        result = await sec.search_company(name="Apple")
        self.assertIn("Apple Inc.", result)
        self.assertIn("320193", result)
        self.assertIn("AAPL", result)

    @patch("mcp_govt_api.tools.sec.http_client")
    async def test_search_by_name_case_insensitive(self, mock_client):
        mock_client.get = AsyncMock(return_value=_make_response(SAMPLE_TICKERS_JSON))

        result = await sec.search_company(name="amazon")
        self.assertIn("Amazon", result)
        self.assertIn("AMZN", result)

    @patch("mcp_govt_api.tools.sec.http_client")
    async def test_search_by_name_not_found(self, mock_client):
        mock_client.get = AsyncMock(return_value=_make_response(SAMPLE_TICKERS_JSON))

        result = await sec.search_company(name="Nonexistent Corp XYZ")
        self.assertIn("No results found", result)


if __name__ == "__main__":
    unittest.main()
