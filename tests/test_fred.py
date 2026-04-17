import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.fred import (
    get_fred_series,
    get_fred_series_info,
    search_fred_series,
)


class FredToolTests(unittest.IsolatedAsyncioTestCase):
    @patch("mcp_govt_api.tools.fred.config")
    @patch(
        "mcp_govt_api.tools.fred.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_search_fred_series_returns_results(self, mock_fetch, mock_config):
        mock_config.fred_api_key = "test-key"
        mock_fetch.return_value = {
            "count": 1,
            "seriess": [
                {
                    "id": "GDP",
                    "title": "Gross Domestic Product",
                    "frequency": "Quarterly",
                    "units": "Billions of Dollars",
                    "seasonal_adjustment": "Seasonally Adjusted Annual Rate",
                    "observation_start": "1947-01-01",
                    "observation_end": "2024-10-01",
                }
            ],
        }

        result = await search_fred_series("GDP", limit=5)

        self.assertIn("Gross Domestic Product", result)
        self.assertIn("GDP", result)
        self.assertIn("Quarterly", result)
        self.assertIn("Billions of Dollars", result)
        mock_fetch.assert_awaited_once()
        call_args = mock_fetch.call_args
        self.assertEqual(call_args.kwargs["params"]["search_text"], "GDP")
        self.assertEqual(call_args.kwargs["params"]["limit"], 5)

    @patch("mcp_govt_api.tools.fred.config")
    @patch(
        "mcp_govt_api.tools.fred.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_search_fred_series_no_results(self, mock_fetch, mock_config):
        mock_config.fred_api_key = "test-key"
        mock_fetch.return_value = {"count": 0, "seriess": []}

        result = await search_fred_series("xyznonexistent")

        self.assertIn("No FRED series found", result)

    @patch("mcp_govt_api.tools.fred.config")
    @patch(
        "mcp_govt_api.tools.fred.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_fred_series_returns_observations(self, mock_fetch, mock_config):
        mock_config.fred_api_key = "test-key"
        mock_fetch.return_value = {
            "observations": [
                {"date": "2024-10-01", "value": "29351.9"},
                {"date": "2024-07-01", "value": "28850.1"},
            ]
        }

        result = await get_fred_series("GDP", limit=2)

        self.assertIn("FRED Series: GDP", result)
        self.assertIn("2024-10-01", result)
        self.assertIn("29351.9", result)
        self.assertIn("2024-07-01", result)
        mock_fetch.assert_awaited_once()
        call_args = mock_fetch.call_args
        self.assertEqual(call_args.kwargs["params"]["series_id"], "GDP")
        self.assertEqual(call_args.kwargs["params"]["sort_order"], "desc")

    @patch("mcp_govt_api.tools.fred.config")
    @patch(
        "mcp_govt_api.tools.fred.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_fred_series_no_observations(self, mock_fetch, mock_config):
        mock_config.fred_api_key = "test-key"
        mock_fetch.return_value = {"observations": []}

        result = await get_fred_series("BADID")

        self.assertIn("No observations found", result)

    @patch("mcp_govt_api.tools.fred.config")
    @patch(
        "mcp_govt_api.tools.fred.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_fred_series_info_returns_metadata(self, mock_fetch, mock_config):
        mock_config.fred_api_key = "test-key"
        mock_fetch.return_value = {
            "seriess": [
                {
                    "id": "UNRATE",
                    "title": "Unemployment Rate",
                    "frequency": "Monthly",
                    "units": "Percent",
                    "seasonal_adjustment": "Seasonally Adjusted",
                    "observation_start": "1948-01-01",
                    "observation_end": "2024-12-01",
                    "last_updated": "2025-01-10 07:46:01-06",
                    "notes": "The unemployment rate represents the number...",
                }
            ]
        }

        result = await get_fred_series_info("UNRATE")

        self.assertIn("Unemployment Rate", result)
        self.assertIn("UNRATE", result)
        self.assertIn("Monthly", result)
        self.assertIn("Percent", result)
        self.assertIn("Seasonally Adjusted", result)
        self.assertIn("1948-01-01", result)
        mock_fetch.assert_awaited_once()

    @patch("mcp_govt_api.tools.fred.config")
    async def test_missing_api_key_returns_error(self, mock_config):
        mock_config.fred_api_key = None

        result = await search_fred_series("GDP")
        self.assertIn("FRED_API_KEY is not set", result)

        result = await get_fred_series("GDP")
        self.assertIn("FRED_API_KEY is not set", result)

        result = await get_fred_series_info("GDP")
        self.assertIn("FRED_API_KEY is not set", result)

    @patch("mcp_govt_api.tools.fred.config")
    @patch(
        "mcp_govt_api.tools.fred.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_fetch_error_handled_gracefully(self, mock_fetch, mock_config):
        mock_config.fred_api_key = "test-key"
        mock_fetch.side_effect = Exception("Connection timeout")

        result = await search_fred_series("GDP")
        self.assertIn("Error searching FRED", result)

        result = await get_fred_series("GDP")
        self.assertIn("Error fetching FRED series", result)

        result = await get_fred_series_info("GDP")
        self.assertIn("Error fetching FRED series info", result)


if __name__ == "__main__":
    unittest.main()
