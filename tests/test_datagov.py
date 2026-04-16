"""Tests for Data.gov CKAN API tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.datagov import (
    search_datasets,
    get_dataset_info,
    query_datagov,
)


class TestSearchDatasets(unittest.IsolatedAsyncioTestCase):
    """Tests for search_datasets tool."""

    @patch("mcp_govt_api.tools.datagov.fetch_json", new_callable=AsyncMock)
    async def test_successful_search(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "count": 150,
                "results": [
                    {
                        "title": "Climate Data Online",
                        "organization": {"title": "NOAA"},
                        "notes": "Comprehensive climate data.",
                        "id": "abc123",
                        "resources": [{"name": "CSV"}, {"name": "JSON"}],
                    }
                ],
            }
        }
        result = await search_datasets(query="climate")
        self.assertIn("Climate Data Online", result)
        self.assertIn("NOAA", result)
        self.assertIn("150 datasets", result)
        self.assertIn("2 files", result)

    @patch("mcp_govt_api.tools.datagov.fetch_json", new_callable=AsyncMock)
    async def test_no_results(self, mock_fetch):
        mock_fetch.return_value = {"result": {"count": 0, "results": []}}
        result = await search_datasets(query="xyznonexistent")
        self.assertIn("No datasets found", result)

    @patch("mcp_govt_api.tools.datagov.fetch_json", new_callable=AsyncMock)
    async def test_rows_capped_at_50(self, mock_fetch):
        mock_fetch.return_value = {"result": {"count": 0, "results": []}}
        await search_datasets(query="test", rows=100)
        call_params = mock_fetch.call_args[1].get("params") or mock_fetch.call_args[0][1]
        self.assertEqual(call_params["rows"], 50)

    @patch("mcp_govt_api.tools.datagov.fetch_json", new_callable=AsyncMock)
    async def test_network_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("Connection error")
        with self.assertRaises(Exception):
            await search_datasets(query="climate")


class TestGetDatasetInfo(unittest.IsolatedAsyncioTestCase):
    """Tests for get_dataset_info tool."""

    @patch("mcp_govt_api.tools.datagov.fetch_json", new_callable=AsyncMock)
    async def test_successful_info(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "title": "US Census Data",
                "organization": {"title": "Census Bureau"},
                "license_title": "Public Domain",
                "metadata_modified": "2024-01-15T00:00:00",
                "notes": "Detailed census data.",
                "resources": [
                    {"name": "Population CSV", "format": "CSV", "url": "https://example.com/data.csv", "size": 1024}
                ],
            }
        }
        result = await get_dataset_info(dataset_id="test-id")
        self.assertIn("US Census Data", result)
        self.assertIn("Census Bureau", result)
        self.assertIn("Public Domain", result)
        self.assertIn("Population CSV", result)
        self.assertIn("CSV", result)

    @patch("mcp_govt_api.tools.datagov.fetch_json", new_callable=AsyncMock)
    async def test_dataset_not_found(self, mock_fetch):
        mock_fetch.return_value = {"result": {}}
        result = await get_dataset_info(dataset_id="nonexistent")
        self.assertIn("Dataset not found", result)

    @patch("mcp_govt_api.tools.datagov.fetch_json", new_callable=AsyncMock)
    async def test_dataset_no_resources(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "title": "Empty Dataset",
                "organization": {"title": "Test Org"},
                "license_title": "MIT",
                "metadata_modified": "2024-01-01T00:00:00",
                "notes": "A dataset with no files.",
                "resources": [],
            }
        }
        result = await get_dataset_info(dataset_id="empty")
        self.assertIn("Empty Dataset", result)
        self.assertNotIn("Available Resources", result)


class TestQueryDatagov(unittest.IsolatedAsyncioTestCase):
    """Tests for query_datagov tool."""

    @patch("mcp_govt_api.tools.datagov.fetch_json", new_callable=AsyncMock)
    async def test_raw_query(self, mock_fetch):
        mock_fetch.return_value = {"result": ["group1", "group2"]}
        result = await query_datagov(action="group_list")
        mock_fetch.assert_awaited_once()
        self.assertIn("result", result)


if __name__ == "__main__":
    unittest.main()
