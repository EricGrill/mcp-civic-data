import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.noaa_coops import (
    get_tide_predictions,
    get_water_levels,
    search_tide_stations,
)


class TidePredictionTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_tide_predictions_returns_formatted_output(self):
        mock_response = {
            "predictions": [
                {"t": "2024-01-01 00:00", "v": "1.234"},
                {"t": "2024-01-01 06:00", "v": "5.678"},
            ]
        }

        with patch(
            "mcp_govt_api.tools.noaa_coops.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ) as fetch_mock:
            result = await get_tide_predictions(
                station_id="8454000",
                begin_date="20240101",
                end_date="20240102",
            )

        fetch_mock.assert_awaited_once()
        call_kwargs = fetch_mock.call_args
        self.assertEqual(call_kwargs[1]["params"]["station"], "8454000")
        self.assertEqual(call_kwargs[1]["params"]["product"], "predictions")
        self.assertIn("Tide Predictions for Station 8454000", result)
        self.assertIn("1.234 ft", result)
        self.assertIn("5.678 ft", result)

    async def test_get_tide_predictions_empty_station_returns_error(self):
        result = await get_tide_predictions(station_id="")
        self.assertIn("Error", result)

    async def test_get_tide_predictions_api_error(self):
        mock_response = {
            "error": {"message": "Station not found"}
        }

        with patch(
            "mcp_govt_api.tools.noaa_coops.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await get_tide_predictions(
                station_id="9999999",
                begin_date="20240101",
                end_date="20240102",
            )

        self.assertIn("NOAA CO-OPS API error", result)
        self.assertIn("Station not found", result)

    async def test_get_tide_predictions_defaults_dates(self):
        mock_response = {"predictions": [{"t": "2024-01-01 00:00", "v": "1.0"}]}

        with patch(
            "mcp_govt_api.tools.noaa_coops.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ) as fetch_mock:
            await get_tide_predictions(station_id="8454000")

        call_kwargs = fetch_mock.call_args
        self.assertIn("begin_date", call_kwargs[1]["params"])
        self.assertIn("end_date", call_kwargs[1]["params"])
        # Dates should be non-empty (auto-filled)
        self.assertTrue(len(call_kwargs[1]["params"]["begin_date"]) == 8)


class WaterLevelTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_water_levels_returns_formatted_output(self):
        mock_response = {
            "data": [
                {"t": "2024-01-01 00:00", "v": "2.345", "q": "v"},
                {"t": "2024-01-01 00:06", "v": "2.350", "q": "v"},
            ]
        }

        with patch(
            "mcp_govt_api.tools.noaa_coops.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ) as fetch_mock:
            result = await get_water_levels(
                station_id="8454000",
                begin_date="20240101",
                end_date="20240102",
            )

        fetch_mock.assert_awaited_once()
        call_kwargs = fetch_mock.call_args
        self.assertEqual(call_kwargs[1]["params"]["product"], "water_level")
        self.assertIn("Observed Water Levels for Station 8454000", result)
        self.assertIn("2.345 ft", result)
        self.assertIn("[v]", result)

    async def test_get_water_levels_empty_station_returns_error(self):
        result = await get_water_levels(station_id="  ")
        self.assertIn("Error", result)

    async def test_get_water_levels_no_data(self):
        mock_response = {"data": []}

        with patch(
            "mcp_govt_api.tools.noaa_coops.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await get_water_levels(
                station_id="8454000",
                begin_date="20240101",
                end_date="20240102",
            )

        self.assertIn("No water level data found", result)


class StationSearchTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_tide_stations_returns_formatted_list(self):
        mock_response = {
            "stations": [
                {
                    "id": "8454000",
                    "name": "Providence",
                    "state": "RI",
                    "lat": 41.8071,
                    "lng": -71.4012,
                },
                {
                    "id": "8447930",
                    "name": "Woods Hole",
                    "state": "MA",
                    "lat": 41.5236,
                    "lng": -70.6719,
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.noaa_coops.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ) as fetch_mock:
            result = await search_tide_stations(state="RI")

        fetch_mock.assert_awaited_once()
        call_kwargs = fetch_mock.call_args
        self.assertEqual(call_kwargs[1]["params"]["state"], "RI")
        self.assertIn("NOAA CO-OPS Tide Stations in RI", result)
        self.assertIn("8454000", result)
        self.assertIn("Providence", result)

    async def test_search_tide_stations_no_state(self):
        mock_response = {
            "stations": [
                {"id": "8454000", "name": "Providence", "state": "RI",
                 "lat": 41.8, "lng": -71.4},
            ]
        }

        with patch(
            "mcp_govt_api.tools.noaa_coops.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ) as fetch_mock:
            result = await search_tide_stations()

        call_kwargs = fetch_mock.call_args
        self.assertNotIn("state", call_kwargs[1]["params"])
        self.assertIn("Providence", result)

    async def test_search_tide_stations_invalid_state(self):
        result = await search_tide_stations(state="XYZ")
        self.assertIn("Error", result)

    async def test_search_tide_stations_applies_limit(self):
        stations = [
            {"id": str(i), "name": f"Station {i}", "state": "FL",
             "lat": 25.0, "lng": -80.0}
            for i in range(50)
        ]
        mock_response = {"stations": stations}

        with patch(
            "mcp_govt_api.tools.noaa_coops.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await search_tide_stations(state="FL", limit=5)

        # Should only show 5 stations
        self.assertIn("5 results", result)

    async def test_search_tide_stations_empty_result(self):
        mock_response = {"stations": []}

        with patch(
            "mcp_govt_api.tools.noaa_coops.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await search_tide_stations(state="AK")

        self.assertIn("No tide stations found", result)


if __name__ == "__main__":
    unittest.main()
