"""Tests for EU Open Data Portal tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.eu_data import (
    get_eu_dataset_info,
    query_eu_data,
    search_eu_datasets,
)


class TestSearchEuDatasets(unittest.IsolatedAsyncioTestCase):
    """Tests for search_eu_datasets tool."""

    @patch("mcp_govt_api.tools.eu_data.fetch_json", new_callable=AsyncMock)
    async def test_successful_search(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "count": 50,
                "results": [
                    {
                        "title": {"en": "European Air Quality Data"},
                        "description": {"en": "Air quality monitoring across EU."},
                        "publisher": {"name": "EEA"},
                        "id": "eu-aq-001",
                    }
                ],
            }
        }
        result = await search_eu_datasets(query="air quality")
        self.assertIn("European Air Quality Data", result)
        self.assertIn("EEA", result)
        self.assertIn("50 datasets", result)

    @patch("mcp_govt_api.tools.eu_data.fetch_json", new_callable=AsyncMock)
    async def test_no_results(self, mock_fetch):
        mock_fetch.return_value = {"result": {"count": 0, "results": []}}
        result = await search_eu_datasets(query="xyznonexistent")
        self.assertIn("No EU datasets found", result)

    @patch("mcp_govt_api.tools.eu_data.fetch_json", new_callable=AsyncMock)
    async def test_multilingual_title_fallback(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "count": 1,
                "results": [
                    {
                        "title": {"de": "Deutsche Daten"},
                        "description": {"de": "Beschreibung"},
                        "publisher": {"name": "Eurostat"},
                        "id": "de-001",
                    }
                ],
            }
        }
        result = await search_eu_datasets(query="test")
        # Should fall back to first available language
        self.assertIn("Deutsche Daten", result)

    @patch("mcp_govt_api.tools.eu_data.fetch_json", new_callable=AsyncMock)
    async def test_limit_capped_at_50(self, mock_fetch):
        mock_fetch.return_value = {"result": {"count": 0, "results": []}}
        await search_eu_datasets(query="test", limit=100)
        call_params = mock_fetch.call_args[1].get("params") or mock_fetch.call_args[0][1]
        self.assertEqual(call_params["limit"], 50)

    @patch("mcp_govt_api.tools.eu_data.fetch_json", new_callable=AsyncMock)
    async def test_string_title(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "count": 1,
                "results": [
                    {
                        "title": "Plain String Title",
                        "description": "Plain description",
                        "publisher": {"name": "EU"},
                        "id": "str-001",
                    }
                ],
            }
        }
        result = await search_eu_datasets(query="test")
        self.assertIn("Plain String Title", result)


class TestGetEuDatasetInfo(unittest.IsolatedAsyncioTestCase):
    """Tests for get_eu_dataset_info tool."""

    @patch("mcp_govt_api.tools.eu_data.fetch_json", new_callable=AsyncMock)
    async def test_successful_info(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "title": {"en": "EU Economic Indicators"},
                "description": {"en": "Economic data for EU member states."},
                "publisher": {"name": "Eurostat"},
                "modified": "2024-03-01T00:00:00",
                "license": "CC-BY-4.0",
                "distributions": [
                    {
                        "title": {"en": "CSV Export"},
                        "format": "CSV",
                        "accessUrl": "https://data.europa.eu/export.csv",
                    }
                ],
            }
        }
        result = await get_eu_dataset_info(dataset_id="eu-econ-001")
        self.assertIn("EU Economic Indicators", result)
        self.assertIn("Eurostat", result)
        self.assertIn("CC-BY-4.0", result)
        self.assertIn("CSV Export", result)

    @patch("mcp_govt_api.tools.eu_data.fetch_json", new_callable=AsyncMock)
    async def test_dataset_not_found(self, mock_fetch):
        mock_fetch.return_value = {"result": {}}
        result = await get_eu_dataset_info(dataset_id="nonexistent")
        self.assertIn("Dataset not found", result)

    @patch("mcp_govt_api.tools.eu_data.fetch_json", new_callable=AsyncMock)
    async def test_no_distributions(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "title": {"en": "Empty Dataset"},
                "description": {"en": "No files."},
                "publisher": {"name": "Test"},
                "distributions": [],
            }
        }
        result = await get_eu_dataset_info(dataset_id="empty")
        self.assertIn("Empty Dataset", result)
        self.assertNotIn("Available Distributions", result)


class TestQueryEuData(unittest.IsolatedAsyncioTestCase):
    """Tests for query_eu_data tool."""

    @patch("mcp_govt_api.tools.eu_data.fetch_json", new_callable=AsyncMock)
    async def test_raw_query(self, mock_fetch):
        mock_fetch.return_value = {"result": {"results": []}}
        await query_eu_data("/datasets", params={"q": "test"})
        mock_fetch.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
