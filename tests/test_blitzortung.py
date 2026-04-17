"""Tests for Blitzortung lightning detection tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.blitzortung import (
    get_recent_lightning_strikes,
    get_lightning_summary,
)


SAMPLE_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-80.191, 25.761]},
            "properties": {"time": "2026-04-16T14:32:01Z", "pol": -1, "sig": 8, "lat_err": 1.2},
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-81.379, 28.538]},
            "properties": {"time": "2026-04-16T14:32:05Z", "pol": 1, "sig": 12, "lat_err": 0.8},
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-82.458, 27.950]},
            "properties": {"time": "2026-04-16T14:32:09Z", "pol": -1, "sig": 5},
        },
    ],
}


class TestGetRecentLightningStrikes(unittest.IsolatedAsyncioTestCase):
    """Tests for get_recent_lightning_strikes tool."""

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_returns_formatted_results(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_GEOJSON
        result = await get_recent_lightning_strikes()
        self.assertIn("Lightning Strikes", result)
        self.assertIn("25.761", result)
        self.assertIn("-80.191", result)
        self.assertIn("Strike 1", result)
        self.assertIn("Strike 2", result)
        self.assertIn("Americas", result)

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_polarity_display(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_GEOJSON
        result = await get_recent_lightning_strikes()
        # First strike has pol=-1, second has pol=1
        self.assertIn("Polarity: -", result)
        self.assertIn("Polarity: +", result)

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_station_count(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_GEOJSON
        result = await get_recent_lightning_strikes()
        self.assertIn("Stations: 8", result)
        self.assertIn("Stations: 12", result)

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_empty_features(self, mock_fetch):
        mock_fetch.return_value = {"type": "FeatureCollection", "features": []}
        result = await get_recent_lightning_strikes()
        self.assertIn("No lightning strikes detected", result)

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_empty_response(self, mock_fetch):
        mock_fetch.return_value = None
        result = await get_recent_lightning_strikes()
        self.assertIn("No lightning strike data available", result)

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_invalid_region(self, mock_fetch):
        result = await get_recent_lightning_strikes(region=99)
        self.assertIn("Error", result)
        self.assertIn("Invalid region code", result)
        mock_fetch.assert_not_awaited()

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_limit_applied(self, mock_fetch):
        many_features = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-80.0 + i * 0.01, 25.0]},
                    "properties": {"time": f"2026-04-16T14:32:{i:02d}Z", "pol": -1, "sig": 5},
                }
                for i in range(10)
            ],
        }
        mock_fetch.return_value = many_features
        result = await get_recent_lightning_strikes(limit=3)
        self.assertIn("Strike 1", result)
        self.assertIn("Strike 3", result)
        self.assertNotIn("Strike 4", result)
        self.assertIn("Showing 3 of 10", result)

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_error_handling(self, mock_fetch):
        mock_fetch.side_effect = Exception("Network error")
        result = await get_recent_lightning_strikes()
        self.assertIn("Error", result)
        self.assertIn("Network error", result)

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_lateral_error_displayed(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_GEOJSON
        result = await get_recent_lightning_strikes()
        self.assertIn("Error: 1.2 km", result)
        self.assertIn("Error: 0.8 km", result)


class TestGetLightningSummary(unittest.IsolatedAsyncioTestCase):
    """Tests for get_lightning_summary tool."""

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_returns_summary(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_GEOJSON
        result = await get_lightning_summary()
        self.assertIn("Lightning Activity Summary", result)
        self.assertIn("Total Strikes", result)
        self.assertIn("3", result)
        self.assertIn("Americas", result)

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_geographic_bounds(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_GEOJSON
        result = await get_lightning_summary()
        self.assertIn("Geographic Bounds", result)
        self.assertIn("Latitude", result)
        self.assertIn("Longitude", result)

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_polarity_stats(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_GEOJSON
        result = await get_lightning_summary()
        self.assertIn("Polarity", result)
        self.assertIn("Positive", result)
        self.assertIn("Negative", result)

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_station_stats(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_GEOJSON
        result = await get_lightning_summary()
        self.assertIn("Detection Stations", result)
        self.assertIn("Average per strike", result)

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_strike_rate(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_GEOJSON
        result = await get_lightning_summary(minutes=60)
        self.assertIn("Strike Rate", result)
        self.assertIn("strikes/min", result)

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_empty_features(self, mock_fetch):
        mock_fetch.return_value = {"type": "FeatureCollection", "features": []}
        result = await get_lightning_summary()
        self.assertIn("No lightning strikes detected", result)

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_empty_response(self, mock_fetch):
        mock_fetch.return_value = None
        result = await get_lightning_summary()
        self.assertIn("No lightning data available", result)

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_invalid_region(self, mock_fetch):
        result = await get_lightning_summary(region=0)
        self.assertIn("Error", result)
        self.assertIn("Invalid region code", result)
        mock_fetch.assert_not_awaited()

    @patch("mcp_govt_api.tools.blitzortung.fetch_json", new_callable=AsyncMock)
    async def test_error_handling(self, mock_fetch):
        mock_fetch.side_effect = Exception("Timeout")
        result = await get_lightning_summary()
        self.assertIn("Error", result)
        self.assertIn("Timeout", result)


if __name__ == "__main__":
    unittest.main()
