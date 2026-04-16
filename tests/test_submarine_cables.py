"""Tests for submarine cable tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.submarine_cables import (
    search_submarine_cables,
    get_submarine_cable_details,
    get_cable_landing_points,
)


class TestSearchSubmarineCables(unittest.IsolatedAsyncioTestCase):
    """Tests for search_submarine_cables tool."""

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_list_all_cables(self, mock_fetch):
        mock_fetch.return_value = [
            {"name": "SEA-ME-WE 5", "id": "sea-me-we-5", "rfs": "2017", "length": "20000"},
            {"name": "MAREA", "id": "marea", "rfs": "2018", "length": "6600"},
        ]
        result = await search_submarine_cables()
        self.assertIn("SEA-ME-WE 5", result)
        self.assertIn("MAREA", result)
        self.assertIn("sea-me-we-5", result)
        self.assertIn("2017", result)
        self.assertIn("showing 2 result(s)", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_search_by_query(self, mock_fetch):
        mock_fetch.return_value = [
            {"name": "SEA-ME-WE 5", "id": "sea-me-we-5", "rfs": "2017", "length": "20000"},
            {"name": "MAREA", "id": "marea", "rfs": "2018", "length": "6600"},
            {"name": "SEA-ME-WE 6", "id": "sea-me-we-6", "rfs": "2025", "length": ""},
        ]
        result = await search_submarine_cables(query="sea-me-we")
        self.assertIn("SEA-ME-WE 5", result)
        self.assertIn("SEA-ME-WE 6", result)
        self.assertNotIn("MAREA", result)
        self.assertIn("showing 2 result(s)", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_search_case_insensitive(self, mock_fetch):
        mock_fetch.return_value = [
            {"name": "MAREA", "id": "marea", "rfs": "2018", "length": "6600"},
        ]
        result = await search_submarine_cables(query="marea")
        self.assertIn("MAREA", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_search_no_results(self, mock_fetch):
        mock_fetch.return_value = [
            {"name": "MAREA", "id": "marea", "rfs": "2018", "length": "6600"},
        ]
        result = await search_submarine_cables(query="nonexistent")
        self.assertIn("No submarine cables found matching", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_empty_response(self, mock_fetch):
        mock_fetch.return_value = []
        result = await search_submarine_cables()
        self.assertIn("No submarine cable data available", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_none_response(self, mock_fetch):
        mock_fetch.return_value = None
        result = await search_submarine_cables()
        self.assertIn("No submarine cable data available", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_limit_respected(self, mock_fetch):
        mock_fetch.return_value = [
            {"name": f"Cable {i}", "id": f"cable-{i}", "rfs": "2020", "length": ""}
            for i in range(10)
        ]
        result = await search_submarine_cables(limit=3)
        self.assertIn("showing 3 result(s)", result)
        self.assertIn("Cable 0", result)
        self.assertIn("Cable 2", result)
        self.assertNotIn("Cable 3", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_error_handling(self, mock_fetch):
        mock_fetch.side_effect = Exception("Network error")
        result = await search_submarine_cables()
        self.assertIn("Error fetching submarine cable data", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_cable_without_length(self, mock_fetch):
        mock_fetch.return_value = [
            {"name": "TestCable", "id": "test-cable", "rfs": "2023", "length": ""},
        ]
        result = await search_submarine_cables()
        self.assertIn("TestCable", result)
        self.assertNotIn("Length:", result)


class TestGetSubmarineCableDetails(unittest.IsolatedAsyncioTestCase):
    """Tests for get_submarine_cable_details tool."""

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_successful_details(self, mock_fetch):
        mock_fetch.return_value = {
            "name": "MAREA",
            "rfs": "2018",
            "length": "6600",
            "url": "https://example.com/marea",
            "owners": "Microsoft, Facebook, Telxius",
            "notes": "Transatlantic cable",
            "landing_points": [
                {"name": "Virginia Beach", "country": "United States"},
                {"name": "Bilbao", "country": "Spain"},
            ],
        }
        result = await get_submarine_cable_details("marea")
        self.assertIn("MAREA", result)
        self.assertIn("2018", result)
        self.assertIn("6600", result)
        self.assertIn("Microsoft", result)
        self.assertIn("Virginia Beach", result)
        self.assertIn("United States", result)
        self.assertIn("Bilbao", result)
        self.assertIn("Spain", result)
        self.assertIn("Landing Points", result)
        self.assertIn("2", result)  # landing point count

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_cable_not_found(self, mock_fetch):
        mock_fetch.return_value = None
        result = await get_submarine_cable_details("nonexistent")
        self.assertIn("No details found", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_empty_cable_id(self, mock_fetch):
        result = await get_submarine_cable_details("")
        self.assertIn("Error: cable_id is required", result)
        mock_fetch.assert_not_awaited()

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_error_handling(self, mock_fetch):
        mock_fetch.side_effect = Exception("Connection timeout")
        result = await get_submarine_cable_details("marea")
        self.assertIn("Error fetching cable details", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_long_notes_truncated(self, mock_fetch):
        mock_fetch.return_value = {
            "name": "TestCable",
            "notes": "A" * 600,
            "landing_points": [],
        }
        result = await get_submarine_cable_details("test-cable")
        self.assertIn("truncated", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_no_landing_points(self, mock_fetch):
        mock_fetch.return_value = {
            "name": "TestCable",
            "rfs": "2024",
            "landing_points": [],
        }
        result = await get_submarine_cable_details("test-cable")
        self.assertIn("TestCable", result)
        self.assertNotIn("Landing Points", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_minimal_cable_data(self, mock_fetch):
        mock_fetch.return_value = {
            "name": "MinimalCable",
        }
        result = await get_submarine_cable_details("minimal")
        self.assertIn("MinimalCable", result)


class TestGetCableLandingPoints(unittest.IsolatedAsyncioTestCase):
    """Tests for get_cable_landing_points tool."""

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_list_all_landing_points(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "name": "Bude",
                "id": "bude-united-kingdom",
                "country": "United Kingdom",
                "cables": ["cable-1", "cable-2"],
            },
            {
                "name": "Marseille",
                "id": "marseille-france",
                "country": "France",
                "cables": ["cable-3"],
            },
        ]
        result = await get_cable_landing_points()
        self.assertIn("Bude", result)
        self.assertIn("United Kingdom", result)
        self.assertIn("Marseille", result)
        self.assertIn("France", result)
        self.assertIn("showing 2 result(s)", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_filter_by_country(self, mock_fetch):
        mock_fetch.return_value = [
            {"name": "Bude", "id": "bude-uk", "country": "United Kingdom", "cables": ["c1"]},
            {"name": "Marseille", "id": "marseille-fr", "country": "France", "cables": ["c2"]},
            {"name": "Highbridge", "id": "highbridge-uk", "country": "United Kingdom", "cables": ["c3"]},
        ]
        result = await get_cable_landing_points(country="United Kingdom")
        self.assertIn("Bude", result)
        self.assertIn("Highbridge", result)
        self.assertNotIn("Marseille", result)
        self.assertIn("showing 2 result(s)", result)
        self.assertIn("'United Kingdom'", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_filter_partial_country_match(self, mock_fetch):
        mock_fetch.return_value = [
            {"name": "Bude", "id": "bude-uk", "country": "United Kingdom", "cables": []},
            {"name": "New York", "id": "ny-us", "country": "United States", "cables": []},
        ]
        result = await get_cable_landing_points(country="united")
        self.assertIn("Bude", result)
        self.assertIn("New York", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_no_results_for_country(self, mock_fetch):
        mock_fetch.return_value = [
            {"name": "Bude", "id": "bude-uk", "country": "United Kingdom", "cables": []},
        ]
        result = await get_cable_landing_points(country="Mars")
        self.assertIn("No landing points found for country 'Mars'", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_empty_response(self, mock_fetch):
        mock_fetch.return_value = []
        result = await get_cable_landing_points()
        self.assertIn("No landing point data available", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_none_response(self, mock_fetch):
        mock_fetch.return_value = None
        result = await get_cable_landing_points()
        self.assertIn("No landing point data available", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_limit_respected(self, mock_fetch):
        mock_fetch.return_value = [
            {"name": f"Point {i}", "id": f"point-{i}", "country": "Test", "cables": []}
            for i in range(10)
        ]
        result = await get_cable_landing_points(limit=3)
        self.assertIn("showing 3 result(s)", result)
        self.assertIn("Point 0", result)
        self.assertIn("Point 2", result)
        self.assertNotIn("Point 3", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_error_handling(self, mock_fetch):
        mock_fetch.side_effect = Exception("API unavailable")
        result = await get_cable_landing_points()
        self.assertIn("Error fetching landing point data", result)

    @patch("mcp_govt_api.tools.submarine_cables.fetch_json", new_callable=AsyncMock)
    async def test_cable_count_displayed(self, mock_fetch):
        mock_fetch.return_value = [
            {"name": "Bude", "id": "bude-uk", "country": "UK", "cables": ["a", "b", "c"]},
        ]
        result = await get_cable_landing_points()
        self.assertIn("Cables: 3", result)


if __name__ == "__main__":
    unittest.main()
