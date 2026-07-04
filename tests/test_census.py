"""Tests for Census API tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.census import (
    get_population,
    get_demographics,
    get_housing_stats,
    query_census,
)


class TestGetPopulation(unittest.IsolatedAsyncioTestCase):
    """Tests for get_population tool."""

    @patch("mcp_govt_api.tools.census.fetch_json", new_callable=AsyncMock)
    async def test_state_population(self, mock_fetch):
        mock_fetch.return_value = [
            ["NAME", "B01003_001E", "state"],
            ["California", "39538223", "06"],
        ]
        result = await get_population(state="CA")
        self.assertIn("California", result)
        self.assertIn("39,538,223", result)
        self.assertIn("2022", result)

    @patch("mcp_govt_api.tools.census.fetch_json", new_callable=AsyncMock)
    async def test_county_population(self, mock_fetch):
        mock_fetch.return_value = [
            ["NAME", "B01003_001E", "state", "county"],
            ["Los Angeles County, California", "10014009", "06", "037"],
            ["San Diego County, California", "3298634", "06", "073"],
        ]
        result = await get_population(state="CA", county="*")
        self.assertIn("Los Angeles County", result)
        self.assertIn("10,014,009", result)

    @patch("mcp_govt_api.tools.census.fetch_json", new_callable=AsyncMock)
    async def test_population_limits_results(self, mock_fetch):
        rows = [["NAME", "B01003_001E", "state", "county"]]
        for i in range(25):
            rows.append([f"County {i}", str(1000 + i), "06", f"{i:03d}"])
        mock_fetch.return_value = rows
        result = await get_population(state="CA", county="*")
        # Should limit to 20 rows
        self.assertIn("County 19", result)
        self.assertNotIn("County 20", result)

    async def test_invalid_state(self):
        result = await get_population(state="ZZ")
        self.assertIn("Error: [Census API]", result)
        self.assertIn("ZZ", result)

    @patch("mcp_govt_api.tools.census.fetch_json", new_callable=AsyncMock)
    async def test_network_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("Network error")
        result = await get_population(state="CA")
        self.assertIn("Error: [Census API]", result)
        self.assertIn("Network error", result)


class TestGetDemographics(unittest.IsolatedAsyncioTestCase):
    """Tests for get_demographics tool."""

    @patch("mcp_govt_api.tools.census.fetch_json", new_callable=AsyncMock)
    async def test_state_demographics(self, mock_fetch):
        mock_fetch.return_value = [
            ["NAME", "B01003_001E", "B01002_001E", "B19013_001E",
             "B02001_002E", "B02001_003E", "B02001_005E", "B03001_003E", "state"],
            ["California", "39538223", "36.7", "84097",
             "16296122", "2175825", "6085947", "15579652", "06"],
        ]
        result = await get_demographics(state="CA")
        self.assertIn("California", result)
        self.assertIn("39,538,223", result)
        self.assertIn("36.7", result)
        self.assertIn("$84,097", result)
        self.assertIn("White", result)
        self.assertIn("Hispanic/Latino", result)

    @patch("mcp_govt_api.tools.census.fetch_json", new_callable=AsyncMock)
    async def test_demographics_with_county(self, mock_fetch):
        mock_fetch.return_value = [
            ["NAME", "B01003_001E", "B01002_001E", "B19013_001E",
             "B02001_002E", "B02001_003E", "B02001_005E", "B03001_003E",
             "state", "county"],
            ["Cook County, Illinois", "5275541", "37.0", "67000",
             "2100000", "1300000", "400000", "1200000", "17", "031"],
        ]
        result = await get_demographics(state="IL", county="031")
        self.assertIn("Cook County", result)

    @patch("mcp_govt_api.tools.census.fetch_json", new_callable=AsyncMock)
    async def test_demographics_zero_population(self, mock_fetch):
        mock_fetch.return_value = [
            ["NAME", "B01003_001E", "B01002_001E", "B19013_001E",
             "B02001_002E", "B02001_003E", "B02001_005E", "B03001_003E", "state"],
            ["Empty State", "0", "0", "0", "0", "0", "0", "0", "99"],
        ]
        result = await get_demographics(state="CA")
        self.assertIn("N/A", result)


class TestGetHousingStats(unittest.IsolatedAsyncioTestCase):
    """Tests for get_housing_stats tool."""

    @patch("mcp_govt_api.tools.census.fetch_json", new_callable=AsyncMock)
    async def test_state_housing(self, mock_fetch):
        mock_fetch.return_value = [
            ["NAME", "B25001_001E", "B25002_002E", "B25002_003E",
             "B25077_001E", "B25064_001E", "state"],
            ["Texas", "11200000", "10000000", "1200000",
             "187200", "1100", "48"],
        ]
        result = await get_housing_stats(state="TX")
        self.assertIn("Texas", result)
        self.assertIn("$187,200", result)
        self.assertIn("vacancy rate", result)

    @patch("mcp_govt_api.tools.census.fetch_json", new_callable=AsyncMock)
    async def test_housing_zero_units(self, mock_fetch):
        mock_fetch.return_value = [
            ["NAME", "B25001_001E", "B25002_002E", "B25002_003E",
             "B25077_001E", "B25064_001E", "state"],
            ["Empty", "0", "0", "0", "0", "0", "99"],
        ]
        result = await get_housing_stats(state="CA")
        self.assertIn("0.0% vacancy rate", result)


class TestQueryCensus(unittest.IsolatedAsyncioTestCase):
    """Tests for query_census tool."""

    @patch("mcp_govt_api.tools.census.fetch_json", new_callable=AsyncMock)
    async def test_raw_query(self, mock_fetch):
        mock_fetch.return_value = [["NAME", "B01003_001E"], ["California", "39538223"]]
        result = await query_census(
            dataset="acs/acs5", variables=["NAME", "B01003_001E"], geo="state:06"
        )
        self.assertEqual(result[1][0], "California")
        mock_fetch.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
