"""Tests for N2YO satellite tracking tools."""

import unittest
from unittest.mock import AsyncMock, patch


from mcp_govt_api.tools.n2yo import (
    get_satellite_position,
    get_satellites_above,
    get_satellite_tle,
    get_api_key,
)


class TestGetApiKey(unittest.TestCase):
    """Tests for get_api_key helper."""

    @patch.dict("os.environ", {"N2YO_API_KEY": "env-key-123"}, clear=False)
    def test_key_from_environment(self):
        with patch("mcp_govt_api.tools.n2yo.config") as mock_config:
            # config has no n2yo_api_key attribute
            del mock_config.n2yo_api_key
            result = get_api_key()
            self.assertEqual(result, "env-key-123")

    @patch.dict("os.environ", {}, clear=False)
    def test_no_key_returns_none(self):
        with patch("mcp_govt_api.tools.n2yo.config") as mock_config:
            del mock_config.n2yo_api_key
            # Also remove from env if present
            import os
            os.environ.pop("N2YO_API_KEY", None)
            result = get_api_key()
            self.assertIsNone(result)

    def test_key_from_config(self):
        with patch("mcp_govt_api.tools.n2yo.config") as mock_config:
            mock_config.n2yo_api_key = "config-key-456"
            result = get_api_key()
            self.assertEqual(result, "config-key-456")


class TestGetSatellitePosition(unittest.IsolatedAsyncioTestCase):
    """Tests for get_satellite_position tool."""

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_successful_position(self, mock_fetch, _mock_key):
        mock_fetch.return_value = {
            "info": {
                "satname": "ISS (ZARYA)",
                "satid": 25544,
                "transactionscount": 5,
            },
            "positions": [
                {
                    "satlatitude": 45.123,
                    "satlongitude": -93.456,
                    "sataltitude": 420.5,
                    "azimuth": 180.2,
                    "elevation": 35.1,
                    "ra": 120.5,
                    "dec": 45.3,
                    "timestamp": 1718400000,
                }
            ],
        }
        result = await get_satellite_position(25544, 40.0, -74.0, 1)
        self.assertIn("ISS", result)
        self.assertIn("45.123", result)
        self.assertIn("-93.456", result)
        self.assertIn("420.5", result)
        self.assertIn("Azimuth", result)
        self.assertIn("Elevation", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_multiple_positions(self, mock_fetch, _mock_key):
        mock_fetch.return_value = {
            "info": {"satname": "HUBBLE", "satid": 20580, "transactionscount": 2},
            "positions": [
                {
                    "satlatitude": 10.0,
                    "satlongitude": 20.0,
                    "sataltitude": 540.0,
                    "azimuth": 90.0,
                    "elevation": 15.0,
                    "ra": 60.0,
                    "dec": 30.0,
                    "timestamp": 1718400000,
                },
                {
                    "satlatitude": 10.5,
                    "satlongitude": 20.5,
                    "sataltitude": 540.1,
                    "azimuth": 91.0,
                    "elevation": 16.0,
                    "ra": 60.5,
                    "dec": 30.5,
                    "timestamp": 1718400001,
                },
            ],
        }
        result = await get_satellite_position(20580, 0, 0, 2)
        self.assertIn("Position 1", result)
        self.assertIn("Position 2", result)
        self.assertIn("HUBBLE", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_empty_positions(self, mock_fetch, _mock_key):
        mock_fetch.return_value = {
            "info": {"satname": "TEST SAT", "satid": 99999, "transactionscount": 1},
            "positions": [],
        }
        result = await get_satellite_position(99999)
        self.assertIn("No position data available", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_no_data_returned(self, mock_fetch, _mock_key):
        mock_fetch.return_value = None
        result = await get_satellite_position(99999)
        self.assertIn("No position data returned", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value=None)
    async def test_no_api_key(self, _mock_key):
        result = await get_satellite_position(25544)
        self.assertIn("N2YO API key not configured", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_fetch_error(self, mock_fetch, _mock_key):
        mock_fetch.side_effect = Exception("Connection timeout")
        result = await get_satellite_position(25544)
        self.assertIn("Error fetching satellite position", result)
        self.assertIn("Connection timeout", result)


class TestGetSatellitesAbove(unittest.IsolatedAsyncioTestCase):
    """Tests for get_satellites_above tool."""

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_successful_above(self, mock_fetch, _mock_key):
        mock_fetch.return_value = {
            "info": {
                "category": "All",
                "transactionscount": 3,
                "satcount": 2,
            },
            "above": [
                {
                    "satname": "ISS (ZARYA)",
                    "satid": 25544,
                    "satlat": 41.5,
                    "satlng": -73.2,
                    "satalt": 418.0,
                    "launchDate": "1998-11-20",
                    "intDesignator": "1998-067A",
                },
                {
                    "satname": "STARLINK-1234",
                    "satid": 44444,
                    "satlat": 42.0,
                    "satlng": -72.0,
                    "satalt": 550.0,
                    "launchDate": "2020-01-15",
                    "intDesignator": "2020-001A",
                },
            ],
        }
        result = await get_satellites_above(40.0, -74.0, 70, 0)
        self.assertIn("Satellites Above", result)
        self.assertIn("ISS", result)
        self.assertIn("STARLINK-1234", result)
        self.assertIn("Satellites Found: 2", result)
        self.assertIn("1998-067A", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_no_satellites_above(self, mock_fetch, _mock_key):
        mock_fetch.return_value = {
            "info": {"category": "All", "transactionscount": 1, "satcount": 0},
            "above": [],
        }
        result = await get_satellites_above(0.0, 0.0)
        self.assertIn("No satellites currently overhead", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_no_data_returned(self, mock_fetch, _mock_key):
        mock_fetch.return_value = None
        result = await get_satellites_above(40.0, -74.0)
        self.assertIn("No data returned", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value=None)
    async def test_no_api_key(self, _mock_key):
        result = await get_satellites_above(40.0, -74.0)
        self.assertIn("N2YO API key not configured", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_fetch_error(self, mock_fetch, _mock_key):
        mock_fetch.side_effect = Exception("Network error")
        result = await get_satellites_above(40.0, -74.0)
        self.assertIn("Error fetching satellites above", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_results_limited_to_25(self, mock_fetch, _mock_key):
        sats = [
            {
                "satname": f"SAT-{i}",
                "satid": 10000 + i,
                "satlat": 40.0,
                "satlng": -74.0,
                "satalt": 500.0,
                "launchDate": "2020-01-01",
                "intDesignator": f"2020-{i:03d}A",
            }
            for i in range(30)
        ]
        mock_fetch.return_value = {
            "info": {"category": "All", "transactionscount": 1, "satcount": 30},
            "above": sats,
        }
        result = await get_satellites_above(40.0, -74.0)
        self.assertIn("SAT-24", result)
        self.assertNotIn("SAT-25", result)
        self.assertIn("5 more satellites", result)


class TestGetSatelliteTle(unittest.IsolatedAsyncioTestCase):
    """Tests for get_satellite_tle tool."""

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_successful_tle(self, mock_fetch, _mock_key):
        mock_fetch.return_value = {
            "info": {
                "satname": "ISS (ZARYA)",
                "satid": 25544,
                "transactionscount": 1,
            },
            "tle": (
                "1 25544U 98067A   24166.50000000  .00016717  00000-0  30000-3 0  9993\r\n"
                "2 25544  51.6400  10.0000 0001234  90.0000 270.0000 15.49000000456789"
            ),
        }
        result = await get_satellite_tle(25544)
        self.assertIn("TLE Data", result)
        self.assertIn("ISS", result)
        self.assertIn("25544U", result)
        self.assertIn("51.6400", result)
        self.assertIn("```", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_empty_tle(self, mock_fetch, _mock_key):
        mock_fetch.return_value = {
            "info": {"satname": "UNKNOWN SAT", "satid": 99999, "transactionscount": 1},
            "tle": "",
        }
        result = await get_satellite_tle(99999)
        self.assertIn("No TLE data available", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_no_data_returned(self, mock_fetch, _mock_key):
        mock_fetch.return_value = None
        result = await get_satellite_tle(99999)
        self.assertIn("No TLE data returned", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value=None)
    async def test_no_api_key(self, _mock_key):
        result = await get_satellite_tle(25544)
        self.assertIn("N2YO API key not configured", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_fetch_error(self, mock_fetch, _mock_key):
        mock_fetch.side_effect = Exception("Server error")
        result = await get_satellite_tle(25544)
        self.assertIn("Error fetching TLE data", result)
        self.assertIn("Server error", result)

    @patch("mcp_govt_api.tools.n2yo.get_api_key", return_value="test-key")
    @patch("mcp_govt_api.tools.n2yo.fetch_json", new_callable=AsyncMock)
    async def test_tle_newline_format(self, mock_fetch, _mock_key):
        """TLE with plain newlines instead of \\r\\n should also parse."""
        mock_fetch.return_value = {
            "info": {"satname": "HUBBLE", "satid": 20580, "transactionscount": 1},
            "tle": (
                "1 20580U 90037B   24166.50000000  .00000500  00000-0  30000-4 0  9991\n"
                "2 20580  28.4700 200.0000 0002345 100.0000 260.0000 15.09000000123456"
            ),
        }
        result = await get_satellite_tle(20580)
        self.assertIn("HUBBLE", result)
        self.assertIn("20580U", result)
        self.assertIn("```", result)


if __name__ == "__main__":
    unittest.main()
