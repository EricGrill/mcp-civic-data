"""Tests for NASA FIRMS fire detection tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.firms import (
    get_active_fires,
    get_country_fires,
    query_firms,
    _bounding_box,
    _format_hotspot,
)


class TestBoundingBox(unittest.TestCase):
    """Tests for _bounding_box helper."""

    def test_normal_case(self):
        west, south, east, north = _bounding_box(34.0, -118.0, 100)
        self.assertLess(west, -118.0)
        self.assertGreater(east, -118.0)
        self.assertLess(south, 34.0)
        self.assertGreater(north, 34.0)

    def test_clamped_to_valid_range(self):
        west, south, east, north = _bounding_box(89.0, 179.0, 500)
        self.assertGreaterEqual(south, -90.0)
        self.assertLessEqual(north, 90.0)
        self.assertLessEqual(east, 180.0)


class TestFormatHotspot(unittest.TestCase):
    """Tests for _format_hotspot helper."""

    def test_formats_basic_hotspot(self):
        row = {
            "latitude": "34.05",
            "longitude": "-118.24",
            "bright_ti4": "350.5",
            "confidence": "high",
            "acq_date": "2024-06-15",
            "acq_time": "1430",
            "frp": "25.3",
            "satellite": "N20",
        }
        result = _format_hotspot(row, 1)
        self.assertIn("Hotspot 1", result)
        self.assertIn("34.05", result)
        self.assertIn("14:30 UTC", result)
        self.assertIn("25.3 MW", result)

    def test_missing_fields(self):
        row = {}
        result = _format_hotspot(row, 1)
        self.assertIn("N/A", result)


class TestGetActiveFires(unittest.IsolatedAsyncioTestCase):
    """Tests for get_active_fires tool."""

    @patch("mcp_govt_api.tools.firms._fetch_firms_csv", new_callable=AsyncMock)
    async def test_successful_fires(self, mock_csv):
        mock_csv.return_value = [
            {
                "latitude": "34.05",
                "longitude": "-118.24",
                "bright_ti4": "350",
                "confidence": "nominal",
                "acq_date": "2024-06-15",
                "acq_time": "0800",
                "frp": "15.0",
                "satellite": "N20",
            }
        ]
        result = await get_active_fires(latitude=34.05, longitude=-118.24)
        self.assertIn("1 hotspot", result)
        self.assertIn("34.05", result)

    @patch("mcp_govt_api.tools.firms._fetch_firms_csv", new_callable=AsyncMock)
    async def test_no_fires(self, mock_csv):
        mock_csv.return_value = []
        result = await get_active_fires(latitude=34.05, longitude=-118.24)
        self.assertIn("No active fires detected", result)

    @patch("mcp_govt_api.tools.firms._fetch_firms_csv", new_callable=AsyncMock)
    async def test_fires_limited_to_15(self, mock_csv):
        rows = [
            {
                "latitude": str(34.0 + i * 0.01),
                "longitude": "-118.24",
                "bright_ti4": "300",
                "confidence": "nominal",
                "acq_date": "2024-06-15",
                "acq_time": "0800",
                "frp": "10",
                "satellite": "N20",
            }
            for i in range(20)
        ]
        mock_csv.return_value = rows
        result = await get_active_fires(latitude=34.05, longitude=-118.24)
        self.assertIn("showing 15 of 20", result)

    @patch("mcp_govt_api.tools.firms._fetch_firms_csv", new_callable=AsyncMock)
    async def test_network_error(self, mock_csv):
        mock_csv.side_effect = Exception("Request timed out")
        with self.assertRaises(Exception):
            await get_active_fires(latitude=34.05, longitude=-118.24)


class TestGetCountryFires(unittest.IsolatedAsyncioTestCase):
    """Tests for get_country_fires tool."""

    @patch("mcp_govt_api.tools.firms._fetch_firms_csv", new_callable=AsyncMock)
    async def test_successful_country_fires(self, mock_csv):
        mock_csv.return_value = [
            {
                "latitude": "-15.0",
                "longitude": "-47.0",
                "bright_ti4": "400",
                "confidence": "high",
                "acq_date": "2024-08-01",
                "acq_time": "1200",
                "frp": "50.0",
                "satellite": "N20",
            }
        ]
        result = await get_country_fires(country_code="BRA")
        self.assertIn("BRA", result)
        self.assertIn("1 hotspot", result)

    @patch("mcp_govt_api.tools.firms._fetch_firms_csv", new_callable=AsyncMock)
    async def test_no_country_fires(self, mock_csv):
        mock_csv.return_value = []
        result = await get_country_fires(country_code="ISL")
        self.assertIn("No active fires detected", result)

    @patch("mcp_govt_api.tools.firms._fetch_firms_csv", new_callable=AsyncMock)
    async def test_days_clamped(self, mock_csv):
        mock_csv.return_value = []
        result = await get_country_fires(country_code="USA", days=15)
        # days should be clamped to 10
        call_url = mock_csv.call_args[0][0]
        self.assertTrue(call_url.endswith("/10"))


class TestQueryFirms(unittest.IsolatedAsyncioTestCase):
    """Tests for query_firms tool."""

    @patch("mcp_govt_api.tools.firms._fetch_firms_csv", new_callable=AsyncMock)
    async def test_with_area(self, mock_csv):
        mock_csv.return_value = []
        result = await query_firms(area="-125,24,-66,49")
        mock_csv.assert_awaited_once()

    @patch("mcp_govt_api.tools.firms._fetch_firms_csv", new_callable=AsyncMock)
    async def test_with_country(self, mock_csv):
        mock_csv.return_value = []
        result = await query_firms(country="USA")
        mock_csv.assert_awaited_once()

    async def test_no_area_or_country(self):
        with self.assertRaises(Exception):
            await query_firms()


if __name__ == "__main__":
    unittest.main()
