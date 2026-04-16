import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.nps import (
    get_park_alerts,
    get_park_info,
    search_national_parks,
)


class SearchNationalParksTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_returns_formatted_results(self):
        mock_response = {
            "total": "1",
            "data": [
                {
                    "fullName": "Yosemite National Park",
                    "parkCode": "yose",
                    "states": "CA",
                    "designation": "National Park",
                    "description": "Yosemite is famous for its granite cliffs.",
                    "url": "https://www.nps.gov/yose/index.htm",
                }
            ],
        }

        with patch(
            "mcp_govt_api.tools.nps.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await search_national_parks(query="Yosemite", state="CA")

        self.assertIn("Yosemite National Park", result)
        self.assertIn("yose", result)
        self.assertIn("CA", result)
        self.assertIn("granite cliffs", result)

    async def test_search_empty_results(self):
        with patch(
            "mcp_govt_api.tools.nps.fetch_json",
            new=AsyncMock(return_value={"total": "0", "data": []}),
        ):
            result = await search_national_parks(query="nonexistentpark")

        self.assertIn("No national parks found", result)

    async def test_search_handles_error(self):
        with patch(
            "mcp_govt_api.tools.nps.fetch_json",
            new=AsyncMock(side_effect=Exception("API error")),
        ):
            result = await search_national_parks(query="Yosemite")

        self.assertIn("Error searching national parks", result)


class GetParkAlertsTests(unittest.IsolatedAsyncioTestCase):
    async def test_alerts_returns_formatted_results(self):
        mock_response = {
            "total": "1",
            "data": [
                {
                    "category": "Park Closure",
                    "title": "Tioga Road Closed",
                    "parkCode": "yose",
                    "description": "Tioga Road is closed for the season due to snow.",
                    "url": "https://www.nps.gov/yose/planyourvisit/conditions.htm",
                }
            ],
        }

        with patch(
            "mcp_govt_api.tools.nps.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await get_park_alerts(park_code="yose")

        self.assertIn("Park Closure", result)
        self.assertIn("Tioga Road Closed", result)
        self.assertIn("YOSE", result)
        self.assertIn("closed for the season", result)

    async def test_alerts_empty_results(self):
        with patch(
            "mcp_govt_api.tools.nps.fetch_json",
            new=AsyncMock(return_value={"total": "0", "data": []}),
        ):
            result = await get_park_alerts(park_code="yose")

        self.assertIn("No active alerts", result)

    async def test_alerts_handles_error(self):
        with patch(
            "mcp_govt_api.tools.nps.fetch_json",
            new=AsyncMock(side_effect=Exception("Timeout")),
        ):
            result = await get_park_alerts(park_code="yose")

        self.assertIn("Error fetching park alerts", result)


class GetParkInfoTests(unittest.IsolatedAsyncioTestCase):
    async def test_park_info_returns_detailed_info(self):
        mock_response = {
            "total": "1",
            "data": [
                {
                    "fullName": "Yosemite National Park",
                    "parkCode": "yose",
                    "states": "CA",
                    "designation": "National Park",
                    "description": "Yosemite is known for waterfalls and granite.",
                    "weatherInfo": "Expect snow in winter.",
                    "operatingHours": [
                        {
                            "name": "Yosemite Valley",
                            "description": "Open 24 hours",
                            "standardHours": {
                                "monday": "All Day",
                                "tuesday": "All Day",
                            },
                        }
                    ],
                    "entranceFees": [
                        {
                            "cost": "35.00",
                            "title": "Private Vehicle",
                        }
                    ],
                    "contacts": {
                        "phoneNumbers": [
                            {"type": "Voice", "phoneNumber": "209-372-0200"}
                        ],
                        "emailAddresses": [
                            {"emailAddress": "yose_info@nps.gov"}
                        ],
                    },
                    "url": "https://www.nps.gov/yose/index.htm",
                }
            ],
        }

        with patch(
            "mcp_govt_api.tools.nps.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await get_park_info(park_code="yose")

        self.assertIn("Yosemite National Park", result)
        self.assertIn("waterfalls and granite", result)
        self.assertIn("Expect snow in winter", result)
        self.assertIn("$35.00", result)
        self.assertIn("209-372-0200", result)
        self.assertIn("yose_info@nps.gov", result)
        self.assertIn("All Day", result)

    async def test_park_info_not_found(self):
        with patch(
            "mcp_govt_api.tools.nps.fetch_json",
            new=AsyncMock(return_value={"total": "0", "data": []}),
        ):
            result = await get_park_info(park_code="xxxx")

        self.assertIn("No park found", result)

    async def test_park_info_handles_error(self):
        with patch(
            "mcp_govt_api.tools.nps.fetch_json",
            new=AsyncMock(side_effect=Exception("Connection error")),
        ):
            result = await get_park_info(park_code="yose")

        self.assertIn("Error fetching park info", result)


if __name__ == "__main__":
    unittest.main()
