"""Tests for BTS transportation tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.bts import (
    get_airline_ontime_stats,
    get_border_crossing_data,
    search_bts_datasets,
)


class TestGetAirlineOntimeStats(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_results(self):
        mock_data = [
            {
                "carrier": "AA",
                "carrier_name": "American Airlines",
                "origin": "ORD",
                "dest": "LAX",
                "arr_delay": "12",
                "dep_delay": "5",
                "cancelled": "0.00",
                "flights": "150",
            },
            {
                "carrier": "UA",
                "carrier_name": "United Airlines",
                "origin": "SFO",
                "dest": "JFK",
                "arr_delay": "-3",
                "dep_delay": "0",
                "cancelled": "0.01",
                "flights": "200",
            },
        ]

        with patch(
            "mcp_govt_api.tools.bts.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_airline_ontime_stats(limit=10)

        self.assertIn("Airline On-Time Performance", result)
        self.assertIn("American Airlines", result)
        self.assertIn("United Airlines", result)
        self.assertIn("ORD -> LAX", result)
        self.assertIn("Arrival Delay: 12 min", result)

    async def test_carrier_filter_passed_to_params(self):
        with patch(
            "mcp_govt_api.tools.bts.fetch_json",
            new=AsyncMock(return_value=[]),
        ) as mock_fetch:
            result = await get_airline_ontime_stats(carrier="DL")

        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertIn("$where", params)
        self.assertIn("DL", params["$where"])
        self.assertIn("No airline on-time performance data found", result)

    async def test_airport_filter_passed_to_params(self):
        with patch(
            "mcp_govt_api.tools.bts.fetch_json",
            new=AsyncMock(return_value=[]),
        ) as mock_fetch:
            result = await get_airline_ontime_stats(airport="ATL")

        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertIn("$where", params)
        self.assertIn("ATL", params["$where"])

    async def test_handles_api_error(self):
        with patch(
            "mcp_govt_api.tools.bts.fetch_json",
            new=AsyncMock(side_effect=Exception("timeout")),
        ):
            result = await get_airline_ontime_stats()

        self.assertIn("Error fetching airline on-time data", result)


class TestGetBorderCrossingData(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_results(self):
        mock_data = [
            {
                "port_name": "El Paso",
                "state": "Texas",
                "border": "US-Mexico Border",
                "date": "2024-01-01T00:00:00.000",
                "measure": "Personal Vehicles",
                "value": "125000",
            },
        ]

        with patch(
            "mcp_govt_api.tools.bts.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_border_crossing_data(limit=10)

        self.assertIn("Border Crossing Data", result)
        self.assertIn("El Paso", result)
        self.assertIn("Texas", result)
        self.assertIn("US-Mexico Border", result)
        self.assertIn("Personal Vehicles", result)
        self.assertIn("2024-01-01", result)

    async def test_port_filter_passed_to_params(self):
        with patch(
            "mcp_govt_api.tools.bts.fetch_json",
            new=AsyncMock(return_value=[]),
        ) as mock_fetch:
            await get_border_crossing_data(port="Detroit")

        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertIn("$where", params)
        self.assertIn("DETROIT", params["$where"])

    async def test_state_filter_passed_to_params(self):
        with patch(
            "mcp_govt_api.tools.bts.fetch_json",
            new=AsyncMock(return_value=[]),
        ) as mock_fetch:
            await get_border_crossing_data(state="Texas")

        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertIn("$where", params)
        self.assertIn("TEXAS", params["$where"])

    async def test_handles_api_error(self):
        with patch(
            "mcp_govt_api.tools.bts.fetch_json",
            new=AsyncMock(side_effect=Exception("connection refused")),
        ):
            result = await get_border_crossing_data()

        self.assertIn("Error fetching border crossing data", result)

    async def test_empty_results(self):
        with patch(
            "mcp_govt_api.tools.bts.fetch_json",
            new=AsyncMock(return_value=[]),
        ):
            result = await get_border_crossing_data(port="Nonexistent")

        self.assertIn("No border crossing data found", result)


class TestSearchBtsDatasets(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_results(self):
        mock_data = {
            "results": [
                {
                    "resource": {
                        "name": "Airline On-Time Performance",
                        "id": "2wkt-wbq2",
                        "description": "Flight delay and cancellation data",
                        "updatedAt": "2024-06-01T00:00:00.000Z",
                    },
                    "permalink": "https://data.bts.gov/d/2wkt-wbq2",
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.bts.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await search_bts_datasets(query="airline")

        self.assertIn("BTS Datasets", result)
        self.assertIn("Airline On-Time Performance", result)
        self.assertIn("2wkt-wbq2", result)
        self.assertIn("Flight delay and cancellation data", result)

    async def test_empty_results(self):
        with patch(
            "mcp_govt_api.tools.bts.fetch_json",
            new=AsyncMock(return_value={"results": []}),
        ):
            result = await search_bts_datasets(query="nonexistent")

        self.assertIn("No BTS datasets found", result)

    async def test_handles_api_error(self):
        with patch(
            "mcp_govt_api.tools.bts.fetch_json",
            new=AsyncMock(side_effect=Exception("server error")),
        ):
            result = await search_bts_datasets(query="freight")

        self.assertIn("Error searching BTS datasets", result)

    async def test_query_passed_to_params(self):
        with patch(
            "mcp_govt_api.tools.bts.fetch_json",
            new=AsyncMock(return_value={"results": []}),
        ) as mock_fetch:
            await search_bts_datasets(query="freight")

        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertEqual(params["q"], "freight")


if __name__ == "__main__":
    unittest.main()
