"""Tests for World Bank economics tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.economics import (
    get_country_indicators,
    compare_countries,
    query_worldbank,
)


class TestGetCountryIndicators(unittest.IsolatedAsyncioTestCase):
    """Tests for get_country_indicators tool."""

    @patch("mcp_govt_api.tools.economics.fetch_json", new_callable=AsyncMock)
    async def test_successful_indicators(self, mock_fetch):
        # World Bank API returns a 2-element array: [metadata, data]
        mock_fetch.return_value = [
            {"page": 1, "pages": 1},
            [{"indicator": {"id": "NY.GDP.MKTP.CD"}, "value": 25462700000000, "date": "2022"}],
        ]
        result = await get_country_indicators(country="USA", indicators=["NY.GDP.MKTP.CD"])
        self.assertIn("USA", result)
        self.assertIn("trillion", result)

    @patch("mcp_govt_api.tools.economics.fetch_json", new_callable=AsyncMock)
    async def test_population_formatting(self, mock_fetch):
        mock_fetch.return_value = [
            {"page": 1},
            [{"indicator": {"id": "SP.POP.TOTL"}, "value": 331900000, "date": "2022"}],
        ]
        result = await get_country_indicators(country="USA", indicators=["SP.POP.TOTL"])
        self.assertIn("million", result)

    @patch("mcp_govt_api.tools.economics.fetch_json", new_callable=AsyncMock)
    async def test_no_data_available(self, mock_fetch):
        mock_fetch.return_value = [{"page": 1}, [{"value": None, "date": "2022"}]]
        result = await get_country_indicators(country="USA", indicators=["SI.POV.DDAY"])
        self.assertIn("No data available", result)

    @patch("mcp_govt_api.tools.economics.fetch_json", new_callable=AsyncMock)
    async def test_api_error_handled(self, mock_fetch):
        mock_fetch.side_effect = Exception("Network error")
        result = await get_country_indicators(country="USA", indicators=["NY.GDP.MKTP.CD"])
        self.assertIn("Error fetching data", result)

    @patch("mcp_govt_api.tools.economics.fetch_json", new_callable=AsyncMock)
    async def test_default_indicators(self, mock_fetch):
        # Should use default indicators when none specified
        mock_fetch.return_value = [{"page": 1}, [{"value": 100, "date": "2022"}]]
        result = await get_country_indicators(country="USA")
        # Should have been called 4 times (4 default indicators)
        self.assertEqual(mock_fetch.await_count, 4)


class TestCompareCountries(unittest.IsolatedAsyncioTestCase):
    """Tests for compare_countries tool."""

    @patch("mcp_govt_api.tools.economics.fetch_json", new_callable=AsyncMock)
    async def test_compare_gdp(self, mock_fetch):
        mock_fetch.side_effect = [
            [{"page": 1}, [{"value": 25000000000000, "date": "2022", "country": {"value": "United States"}}]],
            [{"page": 1}, [{"value": 18000000000000, "date": "2022", "country": {"value": "China"}}]],
        ]
        result = await compare_countries(countries=["USA", "CHN"])
        self.assertIn("United States", result)
        self.assertIn("China", result)
        # Should be sorted by value descending
        us_pos = result.index("United States")
        china_pos = result.index("China")
        self.assertLess(us_pos, china_pos)

    @patch("mcp_govt_api.tools.economics.fetch_json", new_callable=AsyncMock)
    async def test_compare_with_missing_data(self, mock_fetch):
        mock_fetch.side_effect = [
            [{"page": 1}, [{"value": 25000000000000, "date": "2022", "country": {"value": "United States"}}]],
            Exception("API error"),
        ]
        result = await compare_countries(countries=["USA", "INVALID"])
        self.assertIn("United States", result)

    @patch("mcp_govt_api.tools.economics.fetch_json", new_callable=AsyncMock)
    async def test_compare_population(self, mock_fetch):
        mock_fetch.return_value = [
            {"page": 1},
            [{"value": 1400000000, "date": "2022", "country": {"value": "India"}}],
        ]
        result = await compare_countries(countries=["IND"], indicator="SP.POP.TOTL")
        self.assertIn("India", result)
        self.assertIn("M", result)


class TestQueryWorldbank(unittest.IsolatedAsyncioTestCase):
    """Tests for query_worldbank tool."""

    @patch("mcp_govt_api.tools.economics.fetch_json", new_callable=AsyncMock)
    async def test_raw_query(self, mock_fetch):
        mock_fetch.return_value = [{"page": 1}, [{"value": 100}]]
        result = await query_worldbank(country="USA", indicator="NY.GDP.MKTP.CD")
        mock_fetch.assert_awaited_once()
        # Verify format=json was injected
        call_args = mock_fetch.call_args
        params = call_args.kwargs.get("params", {})
        self.assertEqual(params.get("format"), "json")


if __name__ == "__main__":
    unittest.main()
