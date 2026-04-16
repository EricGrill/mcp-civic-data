import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.usfs import (
    get_active_wildfires,
    get_wildfire_perimeters,
    search_national_forests,
)


class GetActiveWildfiresTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_results(self):
        mock_response = {
            "features": [
                {
                    "attributes": {
                        "IncidentName": "Smith River Complex",
                        "POOState": "CA",
                        "POOCounty": "Del Norte",
                        "DailyAcres": 1500,
                        "PercentContained": 30,
                        "FireDiscoveryDateTime": 1720000000000,
                        "FireCause": "Lightning",
                        "IncidentTypeCategory": "WF",
                        "IrwinID": "abc-123",
                    }
                }
            ]
        }

        with patch(
            "mcp_govt_api.tools.usfs.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await get_active_wildfires(state="CA")

        self.assertIn("Smith River Complex", result)
        self.assertIn("Del Norte", result)
        self.assertIn("1,500 acres", result)
        self.assertIn("30%", result)
        self.assertIn("Lightning", result)
        self.assertIn("abc-123", result)

    async def test_empty_results(self):
        with patch(
            "mcp_govt_api.tools.usfs.fetch_json",
            new=AsyncMock(return_value={"features": []}),
        ):
            result = await get_active_wildfires(state="RI")

        self.assertIn("No active wildfire incidents", result)

    async def test_handles_error(self):
        with patch(
            "mcp_govt_api.tools.usfs.fetch_json",
            new=AsyncMock(side_effect=Exception("API error")),
        ):
            result = await get_active_wildfires()

        self.assertIn("Error fetching active wildfire incidents", result)

    async def test_limit_capped_at_100(self):
        with patch(
            "mcp_govt_api.tools.usfs.fetch_json",
            new=AsyncMock(return_value={"features": []}),
        ) as mock_fetch:
            await get_active_wildfires(limit=200)

        call_params = mock_fetch.call_args
        self.assertEqual(call_params.kwargs.get("params", call_params[1].get("params", {})).get("resultRecordCount"), 100)


class GetWildfirePerimetersTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_results(self):
        mock_response = {
            "features": [
                {
                    "attributes": {
                        "IncidentName": "Dixie Fire",
                        "POOState": "CA",
                        "GISAcres": 963309.5,
                        "PercentContained": 94,
                        "IncidentTypeCategory": "WF",
                        "CreateDate": 1720000000000,
                        "IrwinID": "def-456",
                    }
                }
            ]
        }

        with patch(
            "mcp_govt_api.tools.usfs.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await get_wildfire_perimeters(state="CA")

        self.assertIn("Dixie Fire", result)
        self.assertIn("CA", result)
        self.assertIn("963,309.5", result)
        self.assertIn("94%", result)
        self.assertIn("def-456", result)

    async def test_empty_results(self):
        with patch(
            "mcp_govt_api.tools.usfs.fetch_json",
            new=AsyncMock(return_value={"features": []}),
        ):
            result = await get_wildfire_perimeters()

        self.assertIn("No active wildfire perimeters", result)

    async def test_handles_error(self):
        with patch(
            "mcp_govt_api.tools.usfs.fetch_json",
            new=AsyncMock(side_effect=Exception("Timeout")),
        ):
            result = await get_wildfire_perimeters()

        self.assertIn("Error fetching wildfire perimeters", result)


class SearchNationalForestsTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_results(self):
        mock_response = {
            "features": [
                {
                    "attributes": {
                        "FORESTNAME": "Tongass National Forest",
                        "FORESTNUMBER": "1001",
                        "REGION": "10",
                        "GIS_ACRES": 16700000,
                    }
                }
            ]
        }

        with patch(
            "mcp_govt_api.tools.usfs.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await search_national_forests(name="Tongass")

        self.assertIn("Tongass National Forest", result)
        self.assertIn("1001", result)
        self.assertIn("16,700,000 acres", result)

    async def test_empty_results(self):
        with patch(
            "mcp_govt_api.tools.usfs.fetch_json",
            new=AsyncMock(return_value={"features": []}),
        ):
            result = await search_national_forests(name="Nonexistent")

        self.assertIn("No National Forests found", result)

    async def test_handles_error(self):
        with patch(
            "mcp_govt_api.tools.usfs.fetch_json",
            new=AsyncMock(side_effect=Exception("Connection error")),
        ):
            result = await search_national_forests()

        self.assertIn("Error searching National Forests", result)


if __name__ == "__main__":
    unittest.main()
