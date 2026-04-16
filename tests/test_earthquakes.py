"""Tests for USGS earthquake tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.earthquakes import (
    get_recent_earthquakes,
    get_earthquakes_near,
    query_earthquakes,
    _format_feature,
    _format_time,
)


class TestFormatTime(unittest.TestCase):
    """Tests for _format_time helper."""

    def test_formats_epoch_ms(self):
        # 2024-01-01 00:00:00 UTC in ms
        result = _format_time(1704067200000)
        self.assertIn("2024-01-01", result)
        self.assertIn("UTC", result)


class TestFormatFeature(unittest.TestCase):
    """Tests for _format_feature helper."""

    def test_formats_basic_feature(self):
        feature = {
            "properties": {
                "mag": 5.2,
                "place": "10km NW of Los Angeles, CA",
                "time": 1704067200000,
                "url": "https://earthquake.usgs.gov/earthquakes/eventpage/test",
                "tsunami": 0,
                "alert": None,
            },
            "geometry": {"coordinates": [-118.24, 34.05, 15.0]},
        }
        result = _format_feature(feature)
        self.assertIn("M5.2", result)
        self.assertIn("Los Angeles", result)
        self.assertIn("15.0 km", result)

    def test_tsunami_warning(self):
        feature = {
            "properties": {"mag": 7.5, "place": "Pacific Ocean", "time": 1704067200000, "tsunami": 1, "alert": "red"},
            "geometry": {"coordinates": [-130.0, 45.0, 10.0]},
        }
        result = _format_feature(feature)
        self.assertIn("TSUNAMI WARNING", result)
        self.assertIn("red", result)


class TestGetRecentEarthquakes(unittest.IsolatedAsyncioTestCase):
    """Tests for get_recent_earthquakes tool."""

    @patch("mcp_govt_api.tools.earthquakes.fetch_json", new_callable=AsyncMock)
    async def test_successful_earthquakes(self, mock_fetch):
        mock_fetch.return_value = {
            "metadata": {"count": 1},
            "features": [
                {
                    "properties": {
                        "mag": 6.1,
                        "place": "Southern Alaska",
                        "time": 1704067200000,
                        "url": "https://earthquake.usgs.gov/test",
                        "tsunami": 0,
                        "alert": None,
                    },
                    "geometry": {"coordinates": [-150.0, 61.0, 20.0]},
                }
            ],
        }
        result = await get_recent_earthquakes(min_magnitude=5.0)
        self.assertIn("M6.1", result)
        self.assertIn("Southern Alaska", result)

    @patch("mcp_govt_api.tools.earthquakes.fetch_json", new_callable=AsyncMock)
    async def test_no_earthquakes(self, mock_fetch):
        mock_fetch.return_value = {"metadata": {"count": 0}, "features": []}
        result = await get_recent_earthquakes(min_magnitude=9.0)
        self.assertIn("No earthquakes found", result)

    @patch("mcp_govt_api.tools.earthquakes.fetch_json", new_callable=AsyncMock)
    async def test_network_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("API unavailable")
        with self.assertRaises(Exception):
            await get_recent_earthquakes()


class TestGetEarthquakesNear(unittest.IsolatedAsyncioTestCase):
    """Tests for get_earthquakes_near tool."""

    @patch("mcp_govt_api.tools.earthquakes.resolve_location", new_callable=AsyncMock)
    @patch("mcp_govt_api.tools.earthquakes.fetch_json", new_callable=AsyncMock)
    async def test_successful_near_query(self, mock_fetch, mock_resolve):
        from mcp_govt_api.utils.location import ResolvedLocation

        mock_resolve.return_value = ResolvedLocation(
            latitude=37.7749, longitude=-122.4194, display_name="San Francisco, CA", source="test"
        )
        mock_fetch.return_value = {
            "metadata": {"count": 1},
            "features": [
                {
                    "properties": {
                        "mag": 3.2,
                        "place": "5km SE of San Francisco",
                        "time": 1704067200000,
                        "tsunami": 0,
                        "alert": None,
                    },
                    "geometry": {"coordinates": [-122.4, 37.7, 8.0]},
                }
            ],
        }
        result = await get_earthquakes_near(latitude=37.7749, longitude=-122.4194)
        self.assertIn("San Francisco", result)
        self.assertIn("M3.2", result)

    @patch("mcp_govt_api.tools.earthquakes.resolve_location", new_callable=AsyncMock)
    @patch("mcp_govt_api.tools.earthquakes.fetch_json", new_callable=AsyncMock)
    async def test_no_nearby_earthquakes(self, mock_fetch, mock_resolve):
        from mcp_govt_api.utils.location import ResolvedLocation

        mock_resolve.return_value = ResolvedLocation(
            latitude=40.0, longitude=-74.0, display_name="New York, NY", source="test"
        )
        mock_fetch.return_value = {"metadata": {"count": 0}, "features": []}
        result = await get_earthquakes_near(latitude=40.0, longitude=-74.0)
        self.assertIn("No earthquakes found", result)
        self.assertIn("New York", result)


class TestQueryEarthquakes(unittest.IsolatedAsyncioTestCase):
    """Tests for query_earthquakes tool."""

    @patch("mcp_govt_api.tools.earthquakes.fetch_json", new_callable=AsyncMock)
    async def test_raw_query(self, mock_fetch):
        mock_fetch.return_value = {"type": "FeatureCollection", "features": []}
        result = await query_earthquakes(params={"minmagnitude": 7.0})
        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertEqual(params["format"], "geojson")

    @patch("mcp_govt_api.tools.earthquakes.fetch_json", new_callable=AsyncMock)
    async def test_format_always_geojson(self, mock_fetch):
        mock_fetch.return_value = {"features": []}
        await query_earthquakes(params={"format": "csv", "minmagnitude": 5})
        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertEqual(params["format"], "geojson")


if __name__ == "__main__":
    unittest.main()
