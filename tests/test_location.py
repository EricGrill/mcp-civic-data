import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.location import lookup_location
from mcp_govt_api.tools.weather import get_weather_forecast
from mcp_govt_api.utils.location import ResolvedLocation, geocode_location, resolve_location


class LocationResolutionTests(unittest.IsolatedAsyncioTestCase):
    async def test_geocode_location_resolves_plain_query(self):
        with patch(
            "mcp_govt_api.utils.location.fetch_json",
            new=AsyncMock(
                return_value=[
                    {
                        "lat": "38.8894",
                        "lon": "-77.0352",
                        "display_name": "Washington, District of Columbia, United States",
                    }
                ]
            ),
        ):
            resolved = await geocode_location("Washington, DC")

        self.assertEqual(resolved.latitude, 38.8894)
        self.assertEqual(resolved.longitude, -77.0352)
        self.assertEqual(
            resolved.display_name,
            "Washington, District of Columbia, United States",
        )
        self.assertEqual(resolved.source, "nominatim")

    async def test_resolve_location_accepts_coordinates_without_search(self):
        with patch(
            "mcp_govt_api.utils.location.reverse_geocode",
            new=AsyncMock(return_value="Washington, DC"),
        ) as reverse_geocode:
            resolved = await resolve_location(
                latitude=38.8894,
                longitude=-77.0352,
            )

        reverse_geocode.assert_awaited_once_with(38.8894, -77.0352)
        self.assertEqual(resolved.display_name, "Washington, DC")
        self.assertEqual(resolved.source, "reverse_geocode")

    async def test_lookup_location_accepts_coordinate_string(self):
        with patch(
            "mcp_govt_api.utils.location.reverse_geocode",
            new=AsyncMock(return_value="Washington Monument"),
        ):
            result = await lookup_location(location="38.8894, -77.0352")

        self.assertIn("Washington Monument", result)
        self.assertIn("Latitude: 38.8894", result)
        self.assertIn("Longitude: -77.0352", result)


class WeatherToolLocationTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_weather_forecast_accepts_location_string(self):
        periods = [
            {
                "name": "Today",
                "detailedForecast": "Sunny and clear.",
            },
            {
                "name": "Tonight",
                "detailedForecast": "Cool and calm.",
            },
        ]

        with patch(
            "mcp_govt_api.tools.weather.resolve_location",
            new=AsyncMock(
                return_value=ResolvedLocation(
                    latitude=38.8894,
                    longitude=-77.0352,
                    display_name="Washington, DC",
                    source="nominatim",
                )
            ),
        ) as resolve_mock, patch(
            "mcp_govt_api.tools.weather.fetch_json",
            new=AsyncMock(
                side_effect=[
                    {"properties": {"forecast": "https://example.com/forecast"}},
                    {"properties": {"periods": periods}},
                ]
            ),
        ) as fetch_mock:
            result = await get_weather_forecast(location="Washington, DC")

        resolve_mock.assert_awaited_once_with(
            location="Washington, DC",
            latitude=None,
            longitude=None,
        )
        self.assertEqual(fetch_mock.await_count, 2)
        self.assertIn("Weather forecast for Washington, DC", result)
        self.assertIn("Sunny and clear.", result)


if __name__ == "__main__":
    unittest.main()
