"""Tests for space weather tools (NOAA SWPC)."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.space_weather import (
    get_space_weather_summary,
    get_solar_flares,
    get_space_weather_alerts,
    query_space_weather,
    _kp_storm_level,
)


class TestKpStormLevel(unittest.TestCase):
    """Tests for _kp_storm_level helper."""

    def test_quiet(self):
        self.assertEqual(_kp_storm_level(2.0), "Quiet")

    def test_unsettled(self):
        self.assertEqual(_kp_storm_level(4.5), "Unsettled")

    def test_minor_storm(self):
        self.assertIn("G1", _kp_storm_level(5.5))

    def test_extreme_storm(self):
        self.assertIn("G5", _kp_storm_level(9.0))

    def test_severe_storm(self):
        self.assertIn("G4", _kp_storm_level(8.5))


class TestGetSpaceWeatherSummary(unittest.IsolatedAsyncioTestCase):
    """Tests for get_space_weather_summary tool."""

    @patch("mcp_govt_api.tools.space_weather.fetch_json", new_callable=AsyncMock)
    async def test_successful_summary(self, mock_fetch):
        mock_fetch.side_effect = [
            # plasma data (header + data rows)
            [["time_tag", "density", "speed", "temperature"], ["2024-06-15 12:00", "5.2", "420", "150000"]],
            # kp data
            [["time_tag", "Kp", "a_running"], ["2024-06-15 12:00", "3.0", "7"]],
            # scales data
            {
                "R": {"-1": {"Scale": "0", "Text": ""}},
                "S": {"-1": {"Scale": "0", "Text": ""}},
                "G": {"-1": {"Scale": "1", "Text": "Minor"}},
            },
        ]
        result = await get_space_weather_summary()
        self.assertIn("Space Weather Summary", result)
        self.assertIn("420", result)  # solar wind speed
        self.assertIn("5.2", result)  # density
        self.assertIn("Kp Index", result)
        self.assertIn("Quiet", result)
        self.assertIn("Radio Blackouts", result)
        self.assertIn("G (Geomagnetic Storms): 1", result)

    @patch("mcp_govt_api.tools.space_weather.fetch_json", new_callable=AsyncMock)
    async def test_missing_plasma_data(self, mock_fetch):
        mock_fetch.side_effect = [
            [["header"]],  # only header, no data
            [["time_tag", "Kp"], ["2024-06-15", "2.0"]],
            {"R": {"-1": {"Scale": "0"}}, "S": {"-1": {"Scale": "0"}}, "G": {"-1": {"Scale": "0"}}},
        ]
        result = await get_space_weather_summary()
        self.assertIn("plasma data unavailable", result)

    @patch("mcp_govt_api.tools.space_weather.fetch_json", new_callable=AsyncMock)
    async def test_scales_not_dict(self, mock_fetch):
        mock_fetch.side_effect = [
            [["h", "d", "s", "t"], ["2024-06-15", "5", "400", "100000"]],
            [["h", "k"], ["2024-06-15", "4.0"]],
            "unexpected string response",
        ]
        result = await get_space_weather_summary()
        self.assertIn("scales data unavailable", result)


class TestGetSolarFlares(unittest.IsolatedAsyncioTestCase):
    """Tests for get_solar_flares tool."""

    @patch("mcp_govt_api.tools.space_weather.fetch_json", new_callable=AsyncMock)
    async def test_successful_flares(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "class": "M2.5",
                "begin_time": "2024-06-15 10:00",
                "max_time": "2024-06-15 10:15",
                "end_time": "2024-06-15 10:30",
                "location": "N15E20",
                "region": "3712",
            },
        ]
        result = await get_solar_flares()
        self.assertIn("M2.5", result)
        self.assertIn("N15E20", result)
        self.assertIn("3712", result)

    @patch("mcp_govt_api.tools.space_weather.fetch_json", new_callable=AsyncMock)
    async def test_no_flares(self, mock_fetch):
        mock_fetch.return_value = []
        result = await get_solar_flares()
        self.assertIn("No recent solar flare", result)

    @patch("mcp_govt_api.tools.space_weather.fetch_json", new_callable=AsyncMock)
    async def test_none_response(self, mock_fetch):
        mock_fetch.return_value = None
        result = await get_solar_flares()
        self.assertIn("No recent solar flare data", result)

    @patch("mcp_govt_api.tools.space_weather.fetch_json", new_callable=AsyncMock)
    async def test_flares_limited_to_10(self, mock_fetch):
        flares = [
            {
                "class": f"C{i}.0",
                "begin_time": f"2024-06-15 {i:02d}:00",
                "max_time": "",
                "end_time": "",
                "location": "N10E10",
                "region": "",
            }
            for i in range(15)
        ]
        mock_fetch.return_value = flares
        result = await get_solar_flares()
        self.assertIn("C9.0", result)
        self.assertNotIn("C10.0", result)


class TestGetSpaceWeatherAlerts(unittest.IsolatedAsyncioTestCase):
    """Tests for get_space_weather_alerts tool."""

    @patch("mcp_govt_api.tools.space_weather.fetch_json", new_callable=AsyncMock)
    async def test_successful_alerts(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "product_id": "ALTK04",
                "issue_datetime": "2024-06-15T12:00:00Z",
                "message": "Geomagnetic K-index of 4 expected.",
            }
        ]
        result = await get_space_weather_alerts()
        self.assertIn("ALTK04", result)
        self.assertIn("Geomagnetic K-index", result)

    @patch("mcp_govt_api.tools.space_weather.fetch_json", new_callable=AsyncMock)
    async def test_no_alerts(self, mock_fetch):
        mock_fetch.return_value = []
        result = await get_space_weather_alerts()
        self.assertIn("No active space weather alerts", result)

    @patch("mcp_govt_api.tools.space_weather.fetch_json", new_callable=AsyncMock)
    async def test_long_message_truncated(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "product_id": "WATA50",
                "issue_datetime": "2024-06-15T00:00:00Z",
                "message": "A" * 1000,
            }
        ]
        result = await get_space_weather_alerts()
        self.assertIn("truncated", result)


class TestQuerySpaceWeather(unittest.IsolatedAsyncioTestCase):
    """Tests for query_space_weather tool."""

    @patch("mcp_govt_api.tools.space_weather.fetch_json", new_callable=AsyncMock)
    async def test_raw_query(self, mock_fetch):
        mock_fetch.return_value = [["header"], ["data"]]
        result = await query_space_weather("/products/noaa-planetary-k-index.json")
        mock_fetch.assert_awaited_once()
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
