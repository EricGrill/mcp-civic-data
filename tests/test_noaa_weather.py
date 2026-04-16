import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.noaa_weather import (
    get_active_weather_alerts,
    get_forecast_discussion,
    get_radar_stations,
)


class ForecastDiscussionTests(unittest.IsolatedAsyncioTestCase):
    async def test_no_wfo_returns_common_codes(self):
        result = await get_forecast_discussion()
        self.assertIn("OKX", result)
        self.assertIn("New York", result)
        self.assertIn("3-letter WFO code", result)

    async def test_invalid_wfo_returns_error(self):
        result = await get_forecast_discussion(wfo="ABCD")
        self.assertIn("Error", result)

    async def test_valid_wfo_returns_discussion(self):
        products_response = {
            "@graph": [
                {"id": "abc-123", "issuanceTime": "2025-01-15T12:00:00Z"}
            ]
        }
        product_response = {
            "issuanceTime": "2025-01-15T12:00:00Z",
            "productText": "A strong cold front will push through tonight.",
            "issuingOffice": "NWS New York NY",
        }

        with patch(
            "mcp_govt_api.tools.noaa_weather.fetch_json",
            new=AsyncMock(side_effect=[products_response, product_response]),
        ) as fetch_mock:
            result = await get_forecast_discussion(wfo="OKX")

        self.assertEqual(fetch_mock.await_count, 2)
        self.assertIn("Area Forecast Discussion", result)
        self.assertIn("NWS New York NY", result)
        self.assertIn("cold front", result)

    async def test_empty_graph_returns_not_found(self):
        with patch(
            "mcp_govt_api.tools.noaa_weather.fetch_json",
            new=AsyncMock(return_value={"@graph": []}),
        ):
            result = await get_forecast_discussion(wfo="ZZZ")

        self.assertIn("No forecast discussions found", result)

    async def test_fetch_error_returns_error_message(self):
        with patch(
            "mcp_govt_api.tools.noaa_weather.fetch_json",
            new=AsyncMock(side_effect=Exception("Connection timeout")),
        ):
            result = await get_forecast_discussion(wfo="OKX")

        self.assertIn("Error", result)
        self.assertIn("Connection timeout", result)


class ActiveWeatherAlertsTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_state_returns_error(self):
        result = await get_active_weather_alerts()
        self.assertIn("Error", result)
        self.assertIn("State code is required", result)

    async def test_invalid_state_returns_error(self):
        result = await get_active_weather_alerts(state="XYZ")
        self.assertIn("Error", result)
        self.assertIn("2-letter", result)

    async def test_no_alerts_returns_message(self):
        with patch(
            "mcp_govt_api.tools.noaa_weather.fetch_json",
            new=AsyncMock(return_value={"features": []}),
        ):
            result = await get_active_weather_alerts(state="HI")

        self.assertIn("No active weather alerts", result)

    async def test_alerts_returned_and_sorted(self):
        alerts_response = {
            "features": [
                {
                    "properties": {
                        "event": "Flood Watch",
                        "severity": "Moderate",
                        "urgency": "Expected",
                        "certainty": "Likely",
                        "areaDesc": "Northern Counties",
                        "headline": "Flood Watch in effect",
                    }
                },
                {
                    "properties": {
                        "event": "Tornado Warning",
                        "severity": "Extreme",
                        "urgency": "Immediate",
                        "certainty": "Observed",
                        "areaDesc": "Central Counties",
                        "headline": "Tornado Warning issued",
                    }
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.noaa_weather.fetch_json",
            new=AsyncMock(return_value=alerts_response),
        ):
            result = await get_active_weather_alerts(state="TX")

        self.assertIn("Active weather alerts for TX", result)
        # Tornado Warning (Extreme) should appear before Flood Watch (Moderate)
        tornado_pos = result.index("Tornado Warning")
        flood_pos = result.index("Flood Watch")
        self.assertLess(tornado_pos, flood_pos)

    async def test_event_filter(self):
        alerts_response = {
            "features": [
                {
                    "properties": {
                        "event": "Flood Watch",
                        "severity": "Moderate",
                        "urgency": "Expected",
                        "certainty": "Likely",
                        "areaDesc": "North",
                        "headline": "Flood Watch",
                    }
                },
                {
                    "properties": {
                        "event": "Wind Advisory",
                        "severity": "Minor",
                        "urgency": "Expected",
                        "certainty": "Likely",
                        "areaDesc": "South",
                        "headline": "Wind Advisory",
                    }
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.noaa_weather.fetch_json",
            new=AsyncMock(return_value=alerts_response),
        ):
            result = await get_active_weather_alerts(state="TX", event="flood")

        self.assertIn("Flood Watch", result)
        self.assertNotIn("Wind Advisory", result)

    async def test_limit_respected(self):
        alerts = [
            {
                "properties": {
                    "event": f"Alert {i}",
                    "severity": "Minor",
                    "urgency": "Expected",
                    "certainty": "Possible",
                    "areaDesc": f"Area {i}",
                    "headline": f"Alert {i}",
                }
            }
            for i in range(20)
        ]

        with patch(
            "mcp_govt_api.tools.noaa_weather.fetch_json",
            new=AsyncMock(return_value={"features": alerts}),
        ):
            result = await get_active_weather_alerts(state="CA", limit=5)

        self.assertIn("5 shown", result)


class RadarStationsTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_stations_returned(self):
        stations_response = {
            "features": [
                {
                    "properties": {
                        "stationIdentifier": "KOKX",
                        "name": "Brookhaven, NY",
                        "stationType": "WSR-88D",
                        "elevation": {"value": 26},
                    },
                    "geometry": {"coordinates": [-72.86, 40.86]},
                },
                {
                    "properties": {
                        "stationIdentifier": "KFWS",
                        "name": "Fort Worth, TX",
                        "stationType": "WSR-88D",
                        "elevation": {"value": 208},
                    },
                    "geometry": {"coordinates": [-97.30, 32.57]},
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.noaa_weather.fetch_json",
            new=AsyncMock(return_value=stations_response),
        ):
            result = await get_radar_stations()

        self.assertIn("NEXRAD Radar Stations", result)
        self.assertIn("KOKX", result)
        self.assertIn("KFWS", result)
        self.assertIn("2 stations", result)

    async def test_state_filter(self):
        stations_response = {
            "features": [
                {
                    "properties": {
                        "stationIdentifier": "KOKX",
                        "name": "Brookhaven, NY",
                        "stationType": "WSR-88D",
                        "state": "NY",
                        "county": "Suffolk",
                        "elevation": {"value": 26},
                    },
                    "geometry": {"coordinates": [-72.86, 40.86]},
                },
                {
                    "properties": {
                        "stationIdentifier": "KFWS",
                        "name": "Fort Worth, TX",
                        "stationType": "WSR-88D",
                        "state": "TX",
                        "county": "Tarrant",
                        "elevation": {"value": 208},
                    },
                    "geometry": {"coordinates": [-97.30, 32.57]},
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.noaa_weather.fetch_json",
            new=AsyncMock(return_value=stations_response),
        ):
            result = await get_radar_stations(state="TX")

        self.assertIn("KFWS", result)
        self.assertNotIn("KOKX", result)

    async def test_invalid_state_returns_error(self):
        result = await get_radar_stations(state="123")
        self.assertIn("Error", result)

    async def test_no_stations_for_state(self):
        stations_response = {
            "features": [
                {
                    "properties": {
                        "stationIdentifier": "KOKX",
                        "name": "Brookhaven, NY",
                        "stationType": "WSR-88D",
                        "state": "NY",
                        "county": "Suffolk",
                        "elevation": {"value": 26},
                    },
                    "geometry": {"coordinates": [-72.86, 40.86]},
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.noaa_weather.fetch_json",
            new=AsyncMock(return_value=stations_response),
        ):
            result = await get_radar_stations(state="ZZ")

        self.assertIn("No radar stations found", result)

    async def test_fetch_error_returns_message(self):
        with patch(
            "mcp_govt_api.tools.noaa_weather.fetch_json",
            new=AsyncMock(side_effect=Exception("Network error")),
        ):
            result = await get_radar_stations()

        self.assertIn("Error", result)
        self.assertIn("Network error", result)


if __name__ == "__main__":
    unittest.main()
