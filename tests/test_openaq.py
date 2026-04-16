"""Tests for OpenAQ air quality tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.openaq import (
    get_air_quality,
    get_air_quality_history,
    query_openaq,
)


class TestGetAirQuality(unittest.IsolatedAsyncioTestCase):
    """Tests for get_air_quality tool."""

    @patch("mcp_govt_api.tools.openaq.resolve_location", new_callable=AsyncMock)
    @patch("mcp_govt_api.tools.openaq.fetch_json", new_callable=AsyncMock)
    async def test_successful_air_quality(self, mock_fetch, mock_resolve):
        from mcp_govt_api.utils.location import ResolvedLocation

        mock_resolve.return_value = ResolvedLocation(
            latitude=40.7128, longitude=-74.006, display_name="New York, NY", source="test"
        )
        mock_fetch.return_value = {
            "results": [
                {
                    "name": "Queens College",
                    "country": {"code": "US"},
                    "distance": 5000,
                    "sensors": [
                        {
                            "parameter": {"displayName": "PM2.5", "name": "pm25", "units": "µg/m³"},
                            "latest": {"value": 12.5},
                        }
                    ],
                }
            ]
        }
        result = await get_air_quality(latitude=40.7128, longitude=-74.006)
        self.assertIn("New York", result)
        self.assertIn("Queens College", result)
        self.assertIn("PM2.5", result)
        self.assertIn("12.5", result)

    @patch("mcp_govt_api.tools.openaq.resolve_location", new_callable=AsyncMock)
    @patch("mcp_govt_api.tools.openaq.fetch_json", new_callable=AsyncMock)
    async def test_no_stations_found(self, mock_fetch, mock_resolve):
        from mcp_govt_api.utils.location import ResolvedLocation

        mock_resolve.return_value = ResolvedLocation(
            latitude=0.0, longitude=0.0, display_name="Middle of Ocean", source="test"
        )
        mock_fetch.return_value = {"results": []}
        result = await get_air_quality(latitude=0.0, longitude=0.0)
        self.assertIn("No air quality monitoring stations", result)

    @patch("mcp_govt_api.tools.openaq.resolve_location", new_callable=AsyncMock)
    @patch("mcp_govt_api.tools.openaq.fetch_json", new_callable=AsyncMock)
    async def test_stations_with_no_sensors(self, mock_fetch, mock_resolve):
        from mcp_govt_api.utils.location import ResolvedLocation

        mock_resolve.return_value = ResolvedLocation(
            latitude=40.0, longitude=-74.0, display_name="Test Location", source="test"
        )
        mock_fetch.return_value = {
            "results": [
                {"name": "Empty Station", "country": {"code": "US"}, "distance": 1000, "sensors": []}
            ]
        }
        result = await get_air_quality(latitude=40.0, longitude=-74.0)
        self.assertIn("no current measurements", result)

    @patch("mcp_govt_api.tools.openaq.resolve_location", new_callable=AsyncMock)
    @patch("mcp_govt_api.tools.openaq.fetch_json", new_callable=AsyncMock)
    async def test_air_quality_with_location_string(self, mock_fetch, mock_resolve):
        from mcp_govt_api.utils.location import ResolvedLocation

        mock_resolve.return_value = ResolvedLocation(
            latitude=34.05, longitude=-118.24, display_name="Los Angeles, CA", source="test"
        )
        mock_fetch.return_value = {
            "results": [
                {
                    "name": "LA Station",
                    "country": {"code": "US"},
                    "distance": 2000,
                    "sensors": [
                        {
                            "parameter": {"displayName": "O3", "name": "o3", "units": "ppb"},
                            "latest": {"value": 45},
                        }
                    ],
                }
            ]
        }
        result = await get_air_quality(location="Los Angeles, CA")
        self.assertIn("Los Angeles", result)
        self.assertIn("O3", result)


class TestGetAirQualityHistory(unittest.IsolatedAsyncioTestCase):
    """Tests for get_air_quality_history tool."""

    @patch("mcp_govt_api.tools.openaq.fetch_json", new_callable=AsyncMock)
    async def test_successful_history(self, mock_fetch):
        mock_fetch.return_value = {
            "results": [
                {
                    "parameter": {"displayName": "PM2.5", "name": "pm25", "units": "µg/m³"},
                    "value": 15.0,
                    "period": {"datetimeFrom": {"utc": "2024-01-15T12:00:00Z"}},
                },
                {
                    "parameter": {"displayName": "PM2.5", "name": "pm25", "units": "µg/m³"},
                    "value": 18.0,
                    "period": {"datetimeFrom": {"utc": "2024-01-15T13:00:00Z"}},
                },
            ]
        }
        result = await get_air_quality_history(location_id=12345)
        self.assertIn("PM2.5", result)
        self.assertIn("15.0", result)
        self.assertIn("18.0", result)

    @patch("mcp_govt_api.tools.openaq.fetch_json", new_callable=AsyncMock)
    async def test_no_measurements(self, mock_fetch):
        mock_fetch.return_value = {"results": []}
        result = await get_air_quality_history(location_id=99999)
        self.assertIn("No measurements found", result)

    @patch("mcp_govt_api.tools.openaq.fetch_json", new_callable=AsyncMock)
    async def test_history_with_date_range(self, mock_fetch):
        mock_fetch.return_value = {"results": []}
        result = await get_air_quality_history(
            location_id=123, date_from="2024-01-01T00:00:00Z", date_to="2024-01-31T23:59:59Z"
        )
        self.assertIn("between", result)


class TestQueryOpenaq(unittest.IsolatedAsyncioTestCase):
    """Tests for query_openaq tool."""

    @patch("mcp_govt_api.tools.openaq.fetch_json", new_callable=AsyncMock)
    async def test_raw_query(self, mock_fetch):
        mock_fetch.return_value = {"results": [], "meta": {"found": 0}}
        result = await query_openaq("/locations", params={"limit": "5"})
        self.assertIn("results", result)
        mock_fetch.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
