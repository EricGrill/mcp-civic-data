"""Tests for FDA tools (openFDA API)."""

import unittest
from unittest.mock import AsyncMock, patch


class TestSearchFdaRecalls(unittest.IsolatedAsyncioTestCase):
    """Tests for search_fda_recalls tool."""

    @patch("mcp_govt_api.tools.fda.fetch_json", new_callable=AsyncMock)
    async def test_search_recalls_basic(self, mock_fetch):
        from mcp_govt_api.tools.fda import search_fda_recalls

        mock_fetch.return_value = {
            "meta": {"results": {"total": 1}},
            "results": [
                {
                    "classification": "Class I",
                    "product_description": "Test Drug 100mg tablets",
                    "recalling_firm": "Test Pharma Inc",
                    "reason_for_recall": "Contamination",
                    "status": "Ongoing",
                    "recall_initiation_date": "20240101",
                    "city": "New York",
                    "state": "NY",
                }
            ],
        }

        result = await search_fda_recalls(query="contamination", category="drug", limit=5)

        self.assertIn("Class I", result)
        self.assertIn("Test Pharma Inc", result)
        self.assertIn("Contamination", result)
        self.assertIn("Test Drug 100mg tablets", result)
        mock_fetch.assert_called_once()

    @patch("mcp_govt_api.tools.fda.fetch_json", new_callable=AsyncMock)
    async def test_search_recalls_with_state(self, mock_fetch):
        from mcp_govt_api.tools.fda import search_fda_recalls

        mock_fetch.return_value = {
            "meta": {"results": {"total": 0}},
            "results": [],
        }

        result = await search_fda_recalls(state="CA", category="food")

        self.assertIn("No food recall reports found", result)

    async def test_search_recalls_invalid_category(self):
        from mcp_govt_api.tools.fda import search_fda_recalls

        result = await search_fda_recalls(category="invalid")

        self.assertIn("Error: category must be", result)

    @patch("mcp_govt_api.tools.fda.fetch_json", new_callable=AsyncMock)
    async def test_search_recalls_api_error(self, mock_fetch):
        from mcp_govt_api.tools.fda import search_fda_recalls

        mock_fetch.side_effect = Exception("API unavailable")

        result = await search_fda_recalls()

        self.assertIn("Error fetching FDA recalls", result)

    @patch("mcp_govt_api.tools.fda.fetch_json", new_callable=AsyncMock)
    async def test_search_recalls_device_category(self, mock_fetch):
        from mcp_govt_api.tools.fda import search_fda_recalls

        mock_fetch.return_value = {
            "meta": {"results": {"total": 1}},
            "results": [
                {
                    "classification": "Class II",
                    "product_description": "Medical device X",
                    "recalling_firm": "Device Corp",
                    "reason_for_recall": "Malfunction",
                    "status": "Completed",
                    "recall_initiation_date": "20240301",
                    "city": "",
                    "state": "",
                }
            ],
        }

        result = await search_fda_recalls(category="device")

        self.assertIn("Device", result)
        self.assertIn("Class II", result)


class TestGetFdaAdverseEvents(unittest.IsolatedAsyncioTestCase):
    """Tests for get_fda_adverse_events tool."""

    @patch("mcp_govt_api.tools.fda.fetch_json", new_callable=AsyncMock)
    async def test_adverse_events_basic(self, mock_fetch):
        from mcp_govt_api.tools.fda import get_fda_adverse_events

        mock_fetch.return_value = {
            "meta": {"results": {"total": 100}},
            "results": [
                {
                    "receivedate": "20240115",
                    "serious": "1",
                    "patient": {
                        "reaction": [
                            {
                                "reactionmeddrapt": "Nausea",
                                "reactionoutcome": "1",
                            },
                            {
                                "reactionmeddrapt": "Headache",
                                "reactionoutcome": "1",
                            },
                        ],
                        "drug": [
                            {
                                "openfda": {"brand_name": ["ASPIRIN"]},
                                "medicinalproduct": "ASPIRIN",
                            }
                        ],
                    },
                }
            ],
        }

        result = await get_fda_adverse_events(drug_name="aspirin", limit=5)

        self.assertIn("aspirin", result)
        self.assertIn("Nausea", result)
        self.assertIn("Headache", result)
        self.assertIn("Serious: Yes", result)
        self.assertIn("Recovered", result)

    @patch("mcp_govt_api.tools.fda.fetch_json", new_callable=AsyncMock)
    async def test_adverse_events_no_results(self, mock_fetch):
        from mcp_govt_api.tools.fda import get_fda_adverse_events

        mock_fetch.return_value = {
            "meta": {"results": {"total": 0}},
            "results": [],
        }

        result = await get_fda_adverse_events(drug_name="nonexistentdrug123")

        self.assertIn("No adverse event reports found", result)

    async def test_adverse_events_empty_drug_name(self):
        from mcp_govt_api.tools.fda import get_fda_adverse_events

        result = await get_fda_adverse_events(drug_name="")

        self.assertIn("Error: drug_name is required", result)

    @patch("mcp_govt_api.tools.fda.fetch_json", new_callable=AsyncMock)
    async def test_adverse_events_api_error(self, mock_fetch):
        from mcp_govt_api.tools.fda import get_fda_adverse_events

        mock_fetch.side_effect = Exception("Connection timeout")

        result = await get_fda_adverse_events(drug_name="aspirin")

        self.assertIn("Error fetching FDA adverse events", result)


class TestGetFdaDrugLabels(unittest.IsolatedAsyncioTestCase):
    """Tests for get_fda_drug_labels tool."""

    @patch("mcp_govt_api.tools.fda.fetch_json", new_callable=AsyncMock)
    async def test_drug_labels_basic(self, mock_fetch):
        from mcp_govt_api.tools.fda import get_fda_drug_labels

        mock_fetch.return_value = {
            "meta": {"results": {"total": 1}},
            "results": [
                {
                    "openfda": {
                        "brand_name": ["IBUPROFEN"],
                        "generic_name": ["IBUPROFEN"],
                        "manufacturer_name": ["Test Pharma"],
                        "route": ["ORAL"],
                    },
                    "indications_and_usage": ["Pain relief and fever reduction."],
                    "warnings": ["Do not use if allergic to ibuprofen."],
                    "dosage_and_administration": ["Take 200-400mg every 4-6 hours."],
                }
            ],
        }

        result = await get_fda_drug_labels(drug_name="ibuprofen")

        self.assertIn("IBUPROFEN", result)
        self.assertIn("Test Pharma", result)
        self.assertIn("Pain relief", result)
        self.assertIn("ORAL", result)

    @patch("mcp_govt_api.tools.fda.fetch_json", new_callable=AsyncMock)
    async def test_drug_labels_no_results(self, mock_fetch):
        from mcp_govt_api.tools.fda import get_fda_drug_labels

        mock_fetch.return_value = {
            "meta": {"results": {"total": 0}},
            "results": [],
        }

        result = await get_fda_drug_labels(drug_name="fakemedicine")

        self.assertIn("No drug label information found", result)

    async def test_drug_labels_empty_name(self):
        from mcp_govt_api.tools.fda import get_fda_drug_labels

        result = await get_fda_drug_labels(drug_name="")

        self.assertIn("Error: drug_name is required", result)

    @patch("mcp_govt_api.tools.fda.fetch_json", new_callable=AsyncMock)
    async def test_drug_labels_api_error(self, mock_fetch):
        from mcp_govt_api.tools.fda import get_fda_drug_labels

        mock_fetch.side_effect = Exception("Server error")

        result = await get_fda_drug_labels(drug_name="ibuprofen")

        self.assertIn("Error fetching FDA drug labels", result)

    @patch("mcp_govt_api.tools.fda.fetch_json", new_callable=AsyncMock)
    async def test_drug_labels_truncates_long_text(self, mock_fetch):
        from mcp_govt_api.tools.fda import get_fda_drug_labels

        long_text = "A" * 500
        mock_fetch.return_value = {
            "meta": {"results": {"total": 1}},
            "results": [
                {
                    "openfda": {
                        "brand_name": ["TESTDRUG"],
                        "generic_name": ["TESTDRUG"],
                        "manufacturer_name": ["Mfr"],
                        "route": ["ORAL"],
                    },
                    "indications_and_usage": [long_text],
                    "warnings": [long_text],
                    "dosage_and_administration": [long_text],
                }
            ],
        }

        result = await get_fda_drug_labels(drug_name="testdrug")

        self.assertIn("...", result)
        # Should be truncated, not the full 500 chars per field
        self.assertNotIn("A" * 400, result)


if __name__ == "__main__":
    unittest.main()
