"""Tests for weather tools (NOAA and OpenWeather)."""

import unittest
from unittest.mock import AsyncMock, patch, PropertyMock

from mcp_govt_api.tools.weather import (
    get_weather_forecast,
    get_weather_alerts,
    get_global_weather,
    query_noaa,
    query_openweather,
)


class TestGetWeatherForecast(unittest.IsolatedAsyncioTestCase):
    """Tests for get_weather_forecast tool."""

    @patch("mcp_govt_api.tools.weather.resolve_location", new_callable=AsyncMock)
    @patch("mcp_govt_api.tools.weather.fetch_json", new_callable=AsyncMock)
    async def test_successful_forecast(self, mock_fetch, mock_resolve):
        from mcp_govt_api.utils.location import ResolvedLocation

        mock_resolve.return_value = ResolvedLocation(
            latitude=38.8894, longitude=-77.0352, display_name="Washington, DC", source="test"
        )
        mock_fetch.side_effect = [
            # points response
            {"properties": {"forecast": "https://api.weather.gov/gridpoints/LWX/97,71/forecast"}},
            # forecast response
            {
                "properties": {
                    "periods": [
                        {"name": "Today", "detailedForecast": "Sunny with a high near 75."},
                        {"name": "Tonight", "detailedForecast": "Clear with a low around 55."},
                    ]
                }
            },
        ]

        result = await get_weather_forecast(latitude=38.8894, longitude=-77.0352)
        self.assertIn("Washington, DC", result)
        self.assertIn("Sunny with a high near 75", result)
        self.assertIn("Today", result)

    @patch("mcp_govt_api.tools.weather.resolve_location", new_callable=AsyncMock)
    @patch("mcp_govt_api.tools.weather.fetch_json", new_callable=AsyncMock)
    async def test_forecast_limits_periods(self, mock_fetch, mock_resolve):
        from mcp_govt_api.utils.location import ResolvedLocation

        mock_resolve.return_value = ResolvedLocation(
            latitude=40.0, longitude=-74.0, display_name="Test City", source="test"
        )
        periods = [{"name": f"Period {i}", "detailedForecast": f"Forecast {i}"} for i in range(10)]
        mock_fetch.side_effect = [
            {"properties": {"forecast": "https://api.weather.gov/gridpoints/X/1,2/forecast"}},
            {"properties": {"periods": periods}},
        ]

        result = await get_weather_forecast(latitude=40.0, longitude=-74.0)
        # Should only include first 6 periods
        self.assertIn("Period 5", result)
        self.assertNotIn("Period 6", result)

    @patch("mcp_govt_api.tools.weather.resolve_location", new_callable=AsyncMock)
    @patch("mcp_govt_api.tools.weather.fetch_json", new_callable=AsyncMock)
    async def test_forecast_network_error(self, mock_fetch, mock_resolve):
        from mcp_govt_api.utils.location import ResolvedLocation

        mock_resolve.return_value = ResolvedLocation(
            latitude=38.0, longitude=-77.0, display_name="Test", source="test"
        )
        mock_fetch.side_effect = Exception("Connection refused")

        result = await get_weather_forecast(latitude=38.0, longitude=-77.0)
        self.assertIn("Error: [NOAA Weather]", result)
        self.assertIn("Connection refused", result)


class TestGetWeatherAlerts(unittest.IsolatedAsyncioTestCase):
    """Tests for get_weather_alerts tool."""

    @patch("mcp_govt_api.tools.weather.fetch_json", new_callable=AsyncMock)
    async def test_successful_alerts(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                {
                    "properties": {
                        "event": "Tornado Warning",
                        "severity": "Extreme",
                        "areaDesc": "Central Oklahoma",
                        "headline": "Tornado warning for central OK",
                    }
                }
            ]
        }
        result = await get_weather_alerts(state="OK")
        self.assertIn("Tornado Warning", result)
        self.assertIn("Extreme", result)
        self.assertIn("Central Oklahoma", result)

    @patch("mcp_govt_api.tools.weather.fetch_json", new_callable=AsyncMock)
    async def test_no_alerts(self, mock_fetch):
        mock_fetch.return_value = {"features": []}
        result = await get_weather_alerts(state="CA")
        self.assertIn("No active weather alerts", result)

    async def test_invalid_state(self):
        result = await get_weather_alerts(state="ZZ")
        self.assertIn("Error", result)

    @patch("mcp_govt_api.tools.weather.fetch_json", new_callable=AsyncMock)
    async def test_alerts_limited_to_10(self, mock_fetch):
        alerts = [
            {
                "properties": {
                    "event": f"Alert {i}",
                    "severity": "Minor",
                    "areaDesc": f"Area {i}",
                    "headline": f"Headline {i}",
                }
            }
            for i in range(15)
        ]
        mock_fetch.return_value = {"features": alerts}
        result = await get_weather_alerts(state="TX")
        self.assertIn("Alert 9", result)
        self.assertNotIn("Alert 10", result)


class TestGetGlobalWeather(unittest.IsolatedAsyncioTestCase):
    """Tests for get_global_weather tool."""

    @patch("mcp_govt_api.tools.weather.config")
    @patch("mcp_govt_api.tools.weather.fetch_json", new_callable=AsyncMock)
    async def test_successful_global_weather(self, mock_fetch, mock_config):
        mock_config.has_openweather = True
        mock_config.openweather_api_key = "test-key"

        mock_fetch.return_value = {
            "name": "London",
            "sys": {"country": "GB"},
            "weather": [{"description": "overcast clouds"}],
            "main": {"temp": 12.5, "feels_like": 10.0, "humidity": 80, "pressure": 1013},
            "wind": {"speed": 5.2},
        }

        result = await get_global_weather(city="London", country_code="GB")
        self.assertIn("London", result)
        self.assertIn("GB", result)
        self.assertIn("12.5", result)
        self.assertIn("Overcast clouds", result)

    @patch("mcp_govt_api.tools.weather.config")
    async def test_missing_api_key(self, mock_config):
        mock_config.has_openweather = False
        result = await get_global_weather(city="London")
        self.assertIn("OPENWEATHER_API_KEY", result)


class TestQueryNoaa(unittest.IsolatedAsyncioTestCase):
    """Tests for query_noaa tool."""

    @patch("mcp_govt_api.tools.weather.fetch_json", new_callable=AsyncMock)
    async def test_query_noaa(self, mock_fetch):
        mock_fetch.return_value = {"type": "Feature", "properties": {}}
        result = await query_noaa("/points/38.8894,-77.0352")
        mock_fetch.assert_awaited_once()
        self.assertEqual(result["type"], "Feature")


class TestQueryOpenweather(unittest.IsolatedAsyncioTestCase):
    """Tests for query_openweather tool."""

    @patch("mcp_govt_api.tools.weather.config")
    async def test_missing_api_key(self, mock_config):
        mock_config.has_openweather = False
        result = await query_openweather("/data/2.5/weather")
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
