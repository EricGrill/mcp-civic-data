"""Tests for CFPB consumer complaint tools."""

import unittest
from unittest.mock import AsyncMock, patch


class TestSearchCfpbComplaints(unittest.IsolatedAsyncioTestCase):
    """Tests for search_cfpb_complaints tool."""

    @patch("mcp_govt_api.tools.cfpb.fetch_json", new_callable=AsyncMock)
    async def test_search_basic(self, mock_fetch):
        from mcp_govt_api.tools.cfpb import search_cfpb_complaints

        mock_fetch.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_source": {
                            "complaint_id": "1234567",
                            "product": "Mortgage",
                            "sub_product": "Conventional home mortgage",
                            "issue": "Trouble during payment process",
                            "sub_issue": "",
                            "company": "Test Bank Inc",
                            "state": "CA",
                            "date_received": "2024-03-15",
                            "company_response": "Closed with explanation",
                            "timely": "Yes",
                            "consumer_disputed": "No",
                        }
                    }
                ],
            }
        }

        result = await search_cfpb_complaints(query="mortgage", state="CA", limit=5)

        self.assertIn("Complaint #1234567", result)
        self.assertIn("Mortgage", result)
        self.assertIn("Test Bank Inc", result)
        self.assertIn("CA", result)
        self.assertIn("Closed with explanation", result)
        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertEqual(params["search_term"], "mortgage")
        self.assertEqual(params["state"], "CA")
        self.assertEqual(params["size"], "5")

    @patch("mcp_govt_api.tools.cfpb.fetch_json", new_callable=AsyncMock)
    async def test_search_no_results(self, mock_fetch):
        from mcp_govt_api.tools.cfpb import search_cfpb_complaints

        mock_fetch.return_value = {
            "hits": {"total": {"value": 0}, "hits": []},
        }

        result = await search_cfpb_complaints(product="Nonexistent product")

        self.assertIn("No CFPB complaints found", result)

    @patch("mcp_govt_api.tools.cfpb.fetch_json", new_callable=AsyncMock)
    async def test_search_api_error(self, mock_fetch):
        from mcp_govt_api.tools.cfpb import search_cfpb_complaints

        mock_fetch.side_effect = Exception("API unavailable")

        result = await search_cfpb_complaints()

        self.assertIn("Error fetching CFPB complaints", result)

    @patch("mcp_govt_api.tools.cfpb.fetch_json", new_callable=AsyncMock)
    async def test_search_with_all_filters(self, mock_fetch):
        from mcp_govt_api.tools.cfpb import search_cfpb_complaints

        mock_fetch.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_source": {
                            "complaint_id": "9999999",
                            "product": "Credit card",
                            "sub_product": "",
                            "issue": "Billing disputes",
                            "sub_issue": "",
                            "company": "Big Bank Corp",
                            "state": "NY",
                            "date_received": "2024-06-01",
                            "company_response": "Closed with monetary relief",
                            "timely": "Yes",
                            "consumer_disputed": "",
                        }
                    }
                ],
            }
        }

        result = await search_cfpb_complaints(
            query="billing",
            product="Credit card",
            company="Big Bank Corp",
            state="NY",
            date_received_min="2024-01-01",
            date_received_max="2024-12-31",
        )

        self.assertIn("Credit card", result)
        self.assertIn("Big Bank Corp", result)
        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertEqual(params["product"], "Credit card")
        self.assertEqual(params["company"], "Big Bank Corp")
        self.assertEqual(params["date_received_min"], "2024-01-01")
        self.assertEqual(params["date_received_max"], "2024-12-31")

    @patch("mcp_govt_api.tools.cfpb.fetch_json", new_callable=AsyncMock)
    async def test_search_limits_capped(self, mock_fetch):
        from mcp_govt_api.tools.cfpb import search_cfpb_complaints

        mock_fetch.return_value = {
            "hits": {"total": {"value": 0}, "hits": []},
        }

        await search_cfpb_complaints(limit=200)

        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertEqual(params["size"], "100")


class TestGetCfpbComplaint(unittest.IsolatedAsyncioTestCase):
    """Tests for get_cfpb_complaint tool."""

    @patch("mcp_govt_api.tools.cfpb.fetch_json", new_callable=AsyncMock)
    async def test_get_complaint_basic(self, mock_fetch):
        from mcp_govt_api.tools.cfpb import get_cfpb_complaint

        mock_fetch.return_value = {
            "_source": {
                "complaint_id": "3648850",
                "product": "Mortgage",
                "sub_product": "FHA mortgage",
                "issue": "Applying for a mortgage",
                "sub_issue": "Application denial",
                "company": "Test Lender LLC",
                "state": "TX",
                "zip_code": "75001",
                "date_received": "2024-02-10",
                "date_sent_to_company": "2024-02-11",
                "company_response": "Closed with explanation",
                "company_public_response": "",
                "timely": "Yes",
                "consumer_disputed": "",
                "consumer_consent_provided": "Consent provided",
                "submitted_via": "Web",
                "complaint_what_happened": "I was denied a mortgage.",
                "tags": "",
            }
        }

        result = await get_cfpb_complaint("3648850")

        self.assertIn("Complaint #3648850", result)
        self.assertIn("Mortgage", result)
        self.assertIn("FHA mortgage", result)
        self.assertIn("Test Lender LLC", result)
        self.assertIn("TX", result)
        self.assertIn("I was denied a mortgage.", result)
        self.assertIn("Consent provided", result)

    async def test_get_complaint_no_id(self):
        from mcp_govt_api.tools.cfpb import get_cfpb_complaint

        result = await get_cfpb_complaint("")

        self.assertIn("Error: complaint_id is required", result)

    @patch("mcp_govt_api.tools.cfpb.fetch_json", new_callable=AsyncMock)
    async def test_get_complaint_api_error(self, mock_fetch):
        from mcp_govt_api.tools.cfpb import get_cfpb_complaint

        mock_fetch.side_effect = Exception("Not found")

        result = await get_cfpb_complaint("0000000")

        self.assertIn("Error fetching CFPB complaint", result)

    @patch("mcp_govt_api.tools.cfpb.fetch_json", new_callable=AsyncMock)
    async def test_get_complaint_long_narrative_truncated(self, mock_fetch):
        from mcp_govt_api.tools.cfpb import get_cfpb_complaint

        long_narrative = "A" * 2000
        mock_fetch.return_value = {
            "_source": {
                "complaint_id": "1111111",
                "product": "Student loan",
                "sub_product": "",
                "issue": "Repayment",
                "sub_issue": "",
                "company": "Loan Co",
                "state": "FL",
                "zip_code": "33101",
                "date_received": "2024-01-01",
                "date_sent_to_company": "2024-01-02",
                "company_response": "Closed",
                "company_public_response": "",
                "timely": "Yes",
                "consumer_disputed": "",
                "consumer_consent_provided": "",
                "submitted_via": "Web",
                "complaint_what_happened": long_narrative,
                "tags": "",
            }
        }

        result = await get_cfpb_complaint("1111111")

        self.assertIn("...", result)
        self.assertNotIn("A" * 2000, result)


class TestGetCfpbComplaintStats(unittest.IsolatedAsyncioTestCase):
    """Tests for get_cfpb_complaint_stats tool."""

    @patch("mcp_govt_api.tools.cfpb.fetch_json", new_callable=AsyncMock)
    async def test_stats_basic(self, mock_fetch):
        from mcp_govt_api.tools.cfpb import get_cfpb_complaint_stats

        mock_fetch.return_value = {
            "hits": {"total": {"value": 50000}},
            "aggregations": {
                "product": {
                    "product": {
                        "buckets": [
                            {"key": "Mortgage", "doc_count": 20000},
                            {"key": "Credit card", "doc_count": 15000},
                        ]
                    }
                },
                "issue": {
                    "issue": {
                        "buckets": [
                            {"key": "Trouble during payment process", "doc_count": 10000},
                        ]
                    }
                },
                "company_response": {
                    "company_response": {
                        "buckets": [
                            {"key": "Closed with explanation", "doc_count": 30000},
                        ]
                    }
                },
                "company": {
                    "company": {
                        "buckets": [
                            {"key": "Bank of America", "doc_count": 5000},
                        ]
                    }
                },
            },
        }

        result = await get_cfpb_complaint_stats(state="CA")

        self.assertIn("50,000", result)
        self.assertIn("Mortgage", result)
        self.assertIn("20,000", result)
        self.assertIn("Credit card", result)
        self.assertIn("Trouble during payment process", result)
        self.assertIn("Closed with explanation", result)
        self.assertIn("Bank of America", result)
        self.assertIn("State: CA", result)
        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertEqual(params["size"], "0")

    @patch("mcp_govt_api.tools.cfpb.fetch_json", new_callable=AsyncMock)
    async def test_stats_no_aggregations(self, mock_fetch):
        from mcp_govt_api.tools.cfpb import get_cfpb_complaint_stats

        mock_fetch.return_value = {
            "hits": {"total": {"value": 0}},
            "aggregations": {},
        }

        result = await get_cfpb_complaint_stats(product="Nonexistent")

        self.assertIn("Total Complaints: 0", result)
        self.assertIn("No aggregation data available", result)

    @patch("mcp_govt_api.tools.cfpb.fetch_json", new_callable=AsyncMock)
    async def test_stats_api_error(self, mock_fetch):
        from mcp_govt_api.tools.cfpb import get_cfpb_complaint_stats

        mock_fetch.side_effect = Exception("Server error")

        result = await get_cfpb_complaint_stats()

        self.assertIn("Error fetching CFPB complaint stats", result)

    @patch("mcp_govt_api.tools.cfpb.fetch_json", new_callable=AsyncMock)
    async def test_stats_with_date_filters(self, mock_fetch):
        from mcp_govt_api.tools.cfpb import get_cfpb_complaint_stats

        mock_fetch.return_value = {
            "hits": {"total": {"value": 100}},
            "aggregations": {},
        }

        result = await get_cfpb_complaint_stats(
            date_received_min="2024-01-01",
            date_received_max="2024-06-30",
        )

        self.assertIn("Date Range: 2024-01-01 to 2024-06-30", result)
        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertEqual(params["date_received_min"], "2024-01-01")
        self.assertEqual(params["date_received_max"], "2024-06-30")


if __name__ == "__main__":
    unittest.main()
