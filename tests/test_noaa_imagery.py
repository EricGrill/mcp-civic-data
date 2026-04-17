"""Tests for NOAA satellite imagery tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.noaa_imagery import (
    get_satellite_imagery_info,
    get_latest_satellite_timestamps,
    get_satellite_sectors,
    _validate_satellite,
    _validate_sector,
    _validate_product,
)


class TestValidationHelpers(unittest.TestCase):
    """Tests for parameter validation helpers."""

    def test_valid_satellite(self):
        self.assertIsNone(_validate_satellite("GOES-East"))
        self.assertIsNone(_validate_satellite("GOES-West"))

    def test_invalid_satellite(self):
        result = _validate_satellite("GOES-North")
        self.assertIn("Error", result)
        self.assertIn("GOES-North", result)
        self.assertIn("GOES-East", result)

    def test_valid_sector(self):
        self.assertIsNone(_validate_sector("CONUS"))
        self.assertIsNone(_validate_sector("FullDisk"))

    def test_invalid_sector(self):
        result = _validate_sector("Antarctica")
        self.assertIn("Error", result)
        self.assertIn("Antarctica", result)

    def test_valid_product(self):
        self.assertIsNone(_validate_product("GeoColor"))
        self.assertIsNone(_validate_product("Band13"))

    def test_invalid_product(self):
        result = _validate_product("Band99")
        self.assertIn("Error", result)
        self.assertIn("Band99", result)


class TestGetSatelliteImageryInfo(unittest.IsolatedAsyncioTestCase):
    """Tests for get_satellite_imagery_info tool."""

    @patch("mcp_govt_api.tools.noaa_imagery.fetch_json", new_callable=AsyncMock)
    async def test_successful_default_params(self, mock_fetch):
        mock_fetch.return_value = {
            "timestamps_int": [20240615120000, 20240615115500, 20240615115000]
        }
        result = await get_satellite_imagery_info()
        self.assertIn("GOES-East", result)
        self.assertIn("CONUS", result)
        self.assertIn("GeoColor", result)
        self.assertIn("Latest Image:", result)
        self.assertIn("cdn.star.nesdis.noaa.gov", result)
        self.assertIn("20240615120000", result)

    @patch("mcp_govt_api.tools.noaa_imagery.fetch_json", new_callable=AsyncMock)
    async def test_goes_west_fulldisk(self, mock_fetch):
        mock_fetch.return_value = {"timestamps_int": [20240615100000]}
        result = await get_satellite_imagery_info(
            satellite="GOES-West", sector="FullDisk", product="Band13"
        )
        self.assertIn("GOES-West", result)
        self.assertIn("GOES18", result)
        self.assertIn("Full Disk", result)
        self.assertIn("latest.jpg", result)

    @patch("mcp_govt_api.tools.noaa_imagery.fetch_json", new_callable=AsyncMock)
    async def test_timestamps_as_list(self, mock_fetch):
        mock_fetch.return_value = [20240615120000, 20240615115500]
        result = await get_satellite_imagery_info()
        self.assertIn("20240615120000", result)

    @patch("mcp_govt_api.tools.noaa_imagery.fetch_json", new_callable=AsyncMock)
    async def test_fetch_error_still_returns_info(self, mock_fetch):
        mock_fetch.side_effect = Exception("Network error")
        result = await get_satellite_imagery_info()
        self.assertIn("GOES-East", result)
        self.assertIn("Could not determine latest timestamp", result)
        self.assertIn("Latest Image:", result)

    async def test_invalid_satellite(self):
        result = await get_satellite_imagery_info(satellite="GOES-North")
        self.assertIn("Error", result)
        self.assertIn("GOES-North", result)

    async def test_invalid_sector(self):
        result = await get_satellite_imagery_info(sector="Pacific")
        self.assertIn("Error", result)
        self.assertIn("Pacific", result)

    async def test_invalid_product(self):
        result = await get_satellite_imagery_info(product="Infrared")
        self.assertIn("Error", result)
        self.assertIn("Infrared", result)

    @patch("mcp_govt_api.tools.noaa_imagery.fetch_json", new_callable=AsyncMock)
    async def test_empty_timestamps_response(self, mock_fetch):
        mock_fetch.return_value = {}
        result = await get_satellite_imagery_info()
        self.assertIn("Could not determine latest timestamp", result)

    @patch("mcp_govt_api.tools.noaa_imagery.fetch_json", new_callable=AsyncMock)
    async def test_links_contain_correct_paths(self, mock_fetch):
        mock_fetch.return_value = {"timestamps_int": [20240615120000]}
        result = await get_satellite_imagery_info(
            satellite="GOES-East", sector="Mesoscale-1", product="Band02"
        )
        self.assertIn("GOES16/ABI/SECTOR/meso1/02/latest.jpg", result)
        self.assertIn("Interactive Viewer:", result)


class TestGetLatestSatelliteTimestamps(unittest.IsolatedAsyncioTestCase):
    """Tests for get_latest_satellite_timestamps tool."""

    @patch("mcp_govt_api.tools.noaa_imagery.fetch_json", new_callable=AsyncMock)
    async def test_successful_dict_response(self, mock_fetch):
        mock_fetch.return_value = {
            "timestamps_int": [
                20240615120000,
                20240615115500,
                20240615115000,
            ]
        }
        result = await get_latest_satellite_timestamps()
        self.assertIn("GOES-16", result)
        self.assertIn("CONUS", result)
        self.assertIn("2024-06-15 12:00:00 UTC", result)
        self.assertIn("Showing 3 of 3", result)

    @patch("mcp_govt_api.tools.noaa_imagery.fetch_json", new_callable=AsyncMock)
    async def test_successful_list_response(self, mock_fetch):
        mock_fetch.return_value = [20240615120000, 20240615115500]
        result = await get_latest_satellite_timestamps()
        self.assertIn("2024-06-15 12:00:00 UTC", result)
        self.assertIn("Showing 2 of 2", result)

    @patch("mcp_govt_api.tools.noaa_imagery.fetch_json", new_callable=AsyncMock)
    async def test_limits_to_10(self, mock_fetch):
        mock_fetch.return_value = {
            "timestamps_int": [20240615120000 + i for i in range(15)]
        }
        result = await get_latest_satellite_timestamps()
        self.assertIn("Showing 10 of 15", result)

    @patch("mcp_govt_api.tools.noaa_imagery.fetch_json", new_callable=AsyncMock)
    async def test_non_standard_timestamp_format(self, mock_fetch):
        mock_fetch.return_value = {"timestamps_int": [12345]}
        result = await get_latest_satellite_timestamps()
        self.assertIn("12345", result)

    @patch("mcp_govt_api.tools.noaa_imagery.fetch_json", new_callable=AsyncMock)
    async def test_empty_response(self, mock_fetch):
        mock_fetch.return_value = None
        result = await get_latest_satellite_timestamps()
        self.assertIn("No timestamp data available", result)

    @patch("mcp_govt_api.tools.noaa_imagery.fetch_json", new_callable=AsyncMock)
    async def test_empty_timestamps_list(self, mock_fetch):
        mock_fetch.return_value = {"timestamps_int": []}
        result = await get_latest_satellite_timestamps()
        self.assertIn("No timestamps found", result)

    @patch("mcp_govt_api.tools.noaa_imagery.fetch_json", new_callable=AsyncMock)
    async def test_fetch_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("Connection timeout")
        result = await get_latest_satellite_timestamps()
        self.assertIn("Error fetching satellite timestamps", result)
        self.assertIn("Connection timeout", result)

    async def test_invalid_satellite(self):
        result = await get_latest_satellite_timestamps(satellite="goes-99")
        self.assertIn("Error", result)
        self.assertIn("goes-99", result)

    async def test_invalid_sector(self):
        result = await get_latest_satellite_timestamps(sector="pacific")
        self.assertIn("Error", result)
        self.assertIn("pacific", result)

    @patch("mcp_govt_api.tools.noaa_imagery.fetch_json", new_callable=AsyncMock)
    async def test_goes_18_fd(self, mock_fetch):
        mock_fetch.return_value = [20240615100000]
        result = await get_latest_satellite_timestamps(
            satellite="goes-18", sector="fd"
        )
        self.assertIn("GOES-18", result)
        self.assertIn("FD", result)


class TestGetSatelliteSectors(unittest.IsolatedAsyncioTestCase):
    """Tests for get_satellite_sectors tool."""

    async def test_contains_satellites(self):
        result = await get_satellite_sectors()
        self.assertIn("GOES-East", result)
        self.assertIn("GOES-West", result)
        self.assertIn("GOES16", result)
        self.assertIn("GOES18", result)

    async def test_contains_sectors(self):
        result = await get_satellite_sectors()
        self.assertIn("CONUS", result)
        self.assertIn("FullDisk", result)
        self.assertIn("Mesoscale-1", result)
        self.assertIn("Mesoscale-2", result)
        self.assertIn("Continental United States", result)

    async def test_contains_products(self):
        result = await get_satellite_sectors()
        self.assertIn("GeoColor", result)
        self.assertIn("Band13", result)
        self.assertIn("Band02", result)

    async def test_contains_quick_links(self):
        result = await get_satellite_sectors()
        self.assertIn("Quick Links", result)
        self.assertIn("cdn.star.nesdis.noaa.gov", result)
        self.assertIn("rammb-slider", result)

    async def test_contains_product_descriptions(self):
        result = await get_satellite_sectors()
        self.assertIn("True-color", result)
        self.assertIn("cloud top temperatures", result)
        self.assertIn("visible", result.lower())


if __name__ == "__main__":
    unittest.main()
