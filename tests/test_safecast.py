"""Tests for Safecast radiation monitoring tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.safecast import (
    get_radiation_measurements,
    get_radiation_history,
    query_safecast,
)


class TestGetRadiationMeasurements(unittest.IsolatedAsyncioTestCase):
    """Tests for get_radiation_measurements tool."""

    @patch("mcp_govt_api.tools.safecast.fetch_json", new_callable=AsyncMock)
    async def test_successful_measurements(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "unit": "cpm",
                "value": 35.2,
                "captured_at": "2024-06-15T12:00:00Z",
                "latitude": 35.676,
                "longitude": 139.650,
                "device_id": 12345,
            },
            {
                "unit": "cpm",
                "value": 38.1,
                "captured_at": "2024-06-15T11:00:00Z",
                "latitude": 35.680,
                "longitude": 139.655,
                "device_id": 12346,
            },
        ]
        result = await get_radiation_measurements(latitude=35.6762, longitude=139.6503)
        self.assertIn("35.2 cpm", result)
        self.assertIn("38.1 cpm", result)
        self.assertIn("Radiation measurements", result)

    @patch("mcp_govt_api.tools.safecast.fetch_json", new_callable=AsyncMock)
    async def test_no_measurements(self, mock_fetch):
        mock_fetch.return_value = []
        result = await get_radiation_measurements(latitude=0.0, longitude=0.0)
        self.assertIn("No radiation measurements found", result)

    @patch("mcp_govt_api.tools.safecast.fetch_json", new_callable=AsyncMock)
    async def test_measurements_limited_to_15(self, mock_fetch):
        measurements = [
            {
                "unit": "cpm",
                "value": 30 + i,
                "captured_at": f"2024-06-15T{i:02d}:00:00Z",
                "latitude": 35.0 + i * 0.001,
                "longitude": 139.0,
                "device_id": i,
            }
            for i in range(20)
        ]
        mock_fetch.return_value = measurements
        result = await get_radiation_measurements(latitude=35.0, longitude=139.0)
        self.assertIn("44 cpm", result)  # measurement at index 14
        self.assertNotIn("45 cpm", result)  # measurement at index 15

    @patch("mcp_govt_api.tools.safecast.fetch_json", new_callable=AsyncMock)
    async def test_network_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("Connection refused")
        with self.assertRaises(Exception):
            await get_radiation_measurements(latitude=35.0, longitude=139.0)


class TestGetRadiationHistory(unittest.IsolatedAsyncioTestCase):
    """Tests for get_radiation_history tool."""

    @patch("mcp_govt_api.tools.safecast.fetch_json", new_callable=AsyncMock)
    async def test_successful_history(self, mock_fetch):
        mock_fetch.return_value = [
            {"unit": "cpm", "value": 30.0, "captured_at": "2024-01-15T12:00:00Z"},
            {"unit": "cpm", "value": 32.0, "captured_at": "2024-01-16T12:00:00Z"},
        ]
        result = await get_radiation_history(latitude=35.6762, longitude=139.6503)
        self.assertIn("30.0 cpm", result)
        self.assertIn("32.0 cpm", result)
        self.assertIn("Radiation history", result)

    @patch("mcp_govt_api.tools.safecast.fetch_json", new_callable=AsyncMock)
    async def test_no_history(self, mock_fetch):
        mock_fetch.return_value = []
        result = await get_radiation_history(latitude=0.0, longitude=0.0)
        self.assertIn("No radiation measurements found", result)

    @patch("mcp_govt_api.tools.safecast.fetch_json", new_callable=AsyncMock)
    async def test_history_with_date_range(self, mock_fetch):
        mock_fetch.return_value = [
            {"unit": "cpm", "value": 28.0, "captured_at": "2024-06-01T12:00:00Z"},
        ]
        result = await get_radiation_history(
            latitude=35.0, longitude=139.0,
            captured_after="2024-06-01", captured_before="2024-06-30"
        )
        call_params = mock_fetch.call_args[1].get("params") or mock_fetch.call_args[0][1]
        self.assertEqual(call_params["captured_after"], "2024-06-01")
        self.assertEqual(call_params["captured_before"], "2024-06-30")


class TestQuerySafecast(unittest.IsolatedAsyncioTestCase):
    """Tests for query_safecast tool."""

    @patch("mcp_govt_api.tools.safecast.fetch_json", new_callable=AsyncMock)
    async def test_raw_query(self, mock_fetch):
        mock_fetch.return_value = [{"id": 1}]
        result = await query_safecast("/measurements.json", params={"limit": "5"})
        mock_fetch.assert_awaited_once()
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
