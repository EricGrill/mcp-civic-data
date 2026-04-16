"""Tests for ReliefWeb disaster event tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.disaster_events import (
    get_recent_disasters,
    get_disaster_details,
    search_disaster_reports,
)


class TestGetRecentDisasters(unittest.IsolatedAsyncioTestCase):
    """Tests for get_recent_disasters tool."""

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_recent_disasters_basic(self, mock_fetch):
        mock_fetch.return_value = {
            "data": [
                {
                    "id": 12345,
                    "fields": {
                        "name": "Turkey-Syria Earthquake - Feb 2023",
                        "date": {"created": "2023-02-06T00:00:00+00:00"},
                        "country": [{"name": "Turkey"}, {"name": "Syria"}],
                        "type": [{"name": "Earthquake"}],
                        "status": "ongoing",
                        "glide": "EQ-2023-000015-TUR",
                    },
                }
            ]
        }
        result = await get_recent_disasters()
        self.assertIn("Recent Disasters", result)
        self.assertIn("Turkey-Syria Earthquake", result)
        self.assertIn("12345", result)
        self.assertIn("Turkey", result)
        self.assertIn("Syria", result)
        self.assertIn("Earthquake", result)
        self.assertIn("ongoing", result)
        self.assertIn("EQ-2023-000015-TUR", result)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_filter_by_country(self, mock_fetch):
        mock_fetch.return_value = {
            "data": [
                {
                    "id": 99,
                    "fields": {
                        "name": "Japan Earthquake 2024",
                        "date": {"created": "2024-01-01T00:00:00+00:00"},
                        "country": [{"name": "Japan"}],
                        "type": [{"name": "Earthquake"}],
                        "status": "past",
                    },
                }
            ]
        }
        result = await get_recent_disasters(country="Japan")
        self.assertIn("Japan Earthquake 2024", result)
        # Verify the URL passed to fetch_json contains country filter
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("Japan", call_url)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_filter_by_type(self, mock_fetch):
        mock_fetch.return_value = {
            "data": [
                {
                    "id": 200,
                    "fields": {
                        "name": "West Africa Flood 2023",
                        "date": {"created": "2023-09-15T00:00:00+00:00"},
                        "country": [{"name": "Nigeria"}],
                        "type": [{"name": "Flood"}],
                        "status": "ongoing",
                    },
                }
            ]
        }
        result = await get_recent_disasters(type="flood")
        self.assertIn("Flood", result)
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("flood", call_url)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_filter_by_country_and_type(self, mock_fetch):
        mock_fetch.return_value = {
            "data": [
                {
                    "id": 300,
                    "fields": {
                        "name": "Philippines Cyclone 2023",
                        "date": {"created": "2023-11-01T00:00:00+00:00"},
                        "country": [{"name": "Philippines"}],
                        "type": [{"name": "Cyclone"}],
                        "status": "past",
                    },
                }
            ]
        }
        result = await get_recent_disasters(country="Philippines", type="cyclone")
        self.assertIn("Philippines Cyclone 2023", result)
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("Philippines", call_url)
        self.assertIn("cyclone", call_url)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_empty_results(self, mock_fetch):
        mock_fetch.return_value = {"data": []}
        result = await get_recent_disasters(country="Atlantis")
        self.assertIn("No disasters found", result)
        self.assertIn("Atlantis", result)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_empty_results_no_filters(self, mock_fetch):
        mock_fetch.return_value = {"data": []}
        result = await get_recent_disasters()
        self.assertIn("No disasters found", result)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_network_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("Connection timeout")
        result = await get_recent_disasters()
        self.assertIn("Error fetching disasters from ReliefWeb", result)
        self.assertIn("Connection timeout", result)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_date_string_format(self, mock_fetch):
        """Test that date strings are handled correctly."""
        mock_fetch.return_value = {
            "data": [
                {
                    "id": 1,
                    "fields": {
                        "name": "Test Disaster",
                        "date": "2024-03-15",
                        "country": [{"name": "TestLand"}],
                        "type": [{"name": "Flood"}],
                        "status": "ongoing",
                    },
                }
            ]
        }
        result = await get_recent_disasters()
        self.assertIn("2024-03-15", result)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_multiple_disasters(self, mock_fetch):
        mock_fetch.return_value = {
            "data": [
                {
                    "id": 1,
                    "fields": {
                        "name": "Disaster One",
                        "date": {"created": "2024-01-01T00:00:00+00:00"},
                        "country": [{"name": "CountryA"}],
                        "type": [{"name": "Earthquake"}],
                        "status": "ongoing",
                    },
                },
                {
                    "id": 2,
                    "fields": {
                        "name": "Disaster Two",
                        "date": {"created": "2024-02-01T00:00:00+00:00"},
                        "country": [{"name": "CountryB"}],
                        "type": [{"name": "Flood"}],
                        "status": "past",
                    },
                },
            ]
        }
        result = await get_recent_disasters()
        self.assertIn("2 result(s)", result)
        self.assertIn("Disaster One", result)
        self.assertIn("Disaster Two", result)


class TestGetDisasterDetails(unittest.IsolatedAsyncioTestCase):
    """Tests for get_disaster_details tool."""

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_get_details_success(self, mock_fetch):
        mock_fetch.return_value = {
            "data": [
                {
                    "id": 12345,
                    "fields": {
                        "name": "Turkey-Syria Earthquake - Feb 2023",
                        "date": {"created": "2023-02-06T00:00:00+00:00"},
                        "primary_country": {"name": "Turkey"},
                        "country": [{"name": "Turkey"}, {"name": "Syria"}],
                        "type": [{"name": "Earthquake"}],
                        "status": "ongoing",
                        "glide": "EQ-2023-000015-TUR",
                        "description": "A devastating earthquake struck southeastern Turkey.",
                        "url": "https://reliefweb.int/disaster/eq-2023-000015-tur",
                    },
                }
            ]
        }
        result = await get_disaster_details(12345)
        self.assertIn("Turkey-Syria Earthquake", result)
        self.assertIn("12345", result)
        self.assertIn("Turkey", result)
        self.assertIn("Syria", result)
        self.assertIn("Earthquake", result)
        self.assertIn("EQ-2023-000015-TUR", result)
        self.assertIn("devastating earthquake", result)
        self.assertIn("reliefweb.int", result)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_disaster_not_found(self, mock_fetch):
        mock_fetch.return_value = {"data": []}
        result = await get_disaster_details(99999)
        self.assertIn("No disaster found with ID 99999", result)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_network_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("Server error")
        result = await get_disaster_details(12345)
        self.assertIn("Error fetching disaster details", result)
        self.assertIn("Server error", result)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_long_description_truncated(self, mock_fetch):
        long_desc = "A" * 2000
        mock_fetch.return_value = {
            "data": [
                {
                    "id": 1,
                    "fields": {
                        "name": "Test Disaster",
                        "date": {"created": "2024-01-01T00:00:00+00:00"},
                        "primary_country": {"name": "TestLand"},
                        "country": [{"name": "TestLand"}],
                        "type": [{"name": "Flood"}],
                        "status": "ongoing",
                        "description": long_desc,
                    },
                }
            ]
        }
        result = await get_disaster_details(1)
        self.assertIn("...", result)
        # The description should be truncated to ~1000 chars + "..."
        self.assertLess(len(result), 2000 + 500)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_minimal_fields(self, mock_fetch):
        """Test with minimal fields present in the response."""
        mock_fetch.return_value = {
            "data": [
                {
                    "id": 5,
                    "fields": {
                        "name": "Minimal Disaster",
                    },
                }
            ]
        }
        result = await get_disaster_details(5)
        self.assertIn("Minimal Disaster", result)
        self.assertIn("N/A", result)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_url_contains_appname(self, mock_fetch):
        mock_fetch.return_value = {"data": []}
        await get_disaster_details(100)
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("appname=mcp-civic-data", call_url)
        self.assertIn("/disasters/100", call_url)


class TestSearchDisasterReports(unittest.IsolatedAsyncioTestCase):
    """Tests for search_disaster_reports tool."""

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_search_reports_basic(self, mock_fetch):
        mock_fetch.return_value = {
            "data": [
                {
                    "id": 5001,
                    "fields": {
                        "title": "Syria: Earthquake Flash Update #5",
                        "date": {"created": "2023-02-10T00:00:00+00:00"},
                        "country": [{"name": "Syria"}],
                        "source": [{"name": "OCHA"}],
                        "format": [{"name": "Situation Report"}],
                        "url": "https://reliefweb.int/report/5001",
                    },
                }
            ]
        }
        result = await search_disaster_reports(query="earthquake Syria")
        self.assertIn("Disaster Reports", result)
        self.assertIn("Syria: Earthquake Flash Update #5", result)
        self.assertIn("OCHA", result)
        self.assertIn("Situation Report", result)
        self.assertIn("5001", result)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_search_with_country_filter(self, mock_fetch):
        mock_fetch.return_value = {
            "data": [
                {
                    "id": 6001,
                    "fields": {
                        "title": "Ukraine Situation Report",
                        "date": {"created": "2024-01-15T00:00:00+00:00"},
                        "country": [{"name": "Ukraine"}],
                        "source": [{"name": "UNHCR"}],
                    },
                }
            ]
        }
        result = await search_disaster_reports(query="conflict", country="Ukraine")
        self.assertIn("Ukraine Situation Report", result)
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("Ukraine", call_url)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_empty_results(self, mock_fetch):
        mock_fetch.return_value = {"data": []}
        result = await search_disaster_reports(query="xyznonexistent")
        self.assertIn("No reports found", result)
        self.assertIn("xyznonexistent", result)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_empty_query(self, mock_fetch):
        result = await search_disaster_reports(query="")
        self.assertIn("Error: A search query is required", result)
        mock_fetch.assert_not_called()

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_whitespace_query(self, mock_fetch):
        result = await search_disaster_reports(query="   ")
        self.assertIn("Error: A search query is required", result)
        mock_fetch.assert_not_called()

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_network_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("API unavailable")
        result = await search_disaster_reports(query="flood")
        self.assertIn("Error searching disaster reports", result)
        self.assertIn("API unavailable", result)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_multiple_reports(self, mock_fetch):
        mock_fetch.return_value = {
            "data": [
                {
                    "id": 7001,
                    "fields": {
                        "title": "Report One",
                        "date": {"created": "2024-01-01T00:00:00+00:00"},
                        "country": [{"name": "Haiti"}],
                        "source": [{"name": "WHO"}],
                    },
                },
                {
                    "id": 7002,
                    "fields": {
                        "title": "Report Two",
                        "date": {"created": "2024-02-01T00:00:00+00:00"},
                        "country": [{"name": "Haiti"}],
                        "source": [{"name": "UNICEF"}],
                    },
                },
            ]
        }
        result = await search_disaster_reports(query="cholera")
        self.assertIn("2 result(s)", result)
        self.assertIn("Report One", result)
        self.assertIn("Report Two", result)
        self.assertIn("WHO", result)
        self.assertIn("UNICEF", result)

    @patch("mcp_govt_api.tools.disaster_events.fetch_json", new_callable=AsyncMock)
    async def test_url_construction(self, mock_fetch):
        mock_fetch.return_value = {"data": []}
        await search_disaster_reports(query="flood damage", limit=5)
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("appname=mcp-civic-data", call_url)
        self.assertIn("query[value]=flood damage", call_url)
        self.assertIn("limit=5", call_url)
        self.assertIn("sort[]=date:desc", call_url)


if __name__ == "__main__":
    unittest.main()
