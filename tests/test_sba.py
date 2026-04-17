"""Tests for SBA small business and disaster loan tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.sba import (
    get_sba_disaster_loans,
    get_sba_size_standards,
    search_sba_datasets,
)


class TestSearchSbaDatasets(unittest.IsolatedAsyncioTestCase):
    async def test_returns_datasets(self):
        mock_data = {
            "result": {
                "count": 25,
                "results": [
                    {
                        "title": "PPP FOIA Dataset",
                        "organization": {"title": "SBA"},
                        "notes": "Paycheck Protection Program loan data",
                        "id": "abc-123",
                        "resources": [{"id": "r1"}, {"id": "r2"}],
                    },
                ],
            }
        }

        with patch(
            "mcp_govt_api.tools.sba.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await search_sba_datasets(query="PPP loans", limit=5)

        self.assertIn("PPP FOIA Dataset", result)
        self.assertIn("SBA", result)
        self.assertIn("25 datasets", result)
        self.assertIn("2 files", result)
        self.assertIn("abc-123", result)

    async def test_empty_results(self):
        mock_data = {"result": {"count": 0, "results": []}}

        with patch(
            "mcp_govt_api.tools.sba.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await search_sba_datasets(query="nonexistent")

        self.assertIn("No SBA datasets found", result)

    async def test_handles_api_error(self):
        with patch(
            "mcp_govt_api.tools.sba.fetch_json",
            new=AsyncMock(side_effect=Exception("Connection failed")),
        ):
            result = await search_sba_datasets(query="loans")

        self.assertIn("Error searching SBA datasets", result)
        self.assertIn("Connection failed", result)


class TestGetSbaSizeStandards(unittest.IsolatedAsyncioTestCase):
    async def test_returns_size_standards(self):
        mock_data = [
            {
                "NAICS_Code": "541511",
                "NAICS_Industry_Description": "Custom Computer Programming Services",
                "Size_Standard": "$34.0 Million",
            },
        ]

        with patch(
            "mcp_govt_api.tools.sba.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_sba_size_standards(naics_code="541511")

        self.assertIn("541511", result)
        self.assertIn("Custom Computer Programming Services", result)
        self.assertIn("$34.0 Million", result)

    async def test_search_by_industry(self):
        mock_data = [
            {
                "NAICS_Code": "722511",
                "NAICS_Industry_Description": "Full-Service Restaurants",
                "Size_Standard": "$10.0 Million",
            },
        ]

        with patch(
            "mcp_govt_api.tools.sba.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ) as mock_fetch:
            result = await get_sba_size_standards(industry="restaurant")

        self.assertIn("Full-Service Restaurants", result)
        self.assertIn("$10.0 Million", result)
        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertIn("restaurant", params["$where"])

    async def test_empty_results(self):
        mock_data = []

        with patch(
            "mcp_govt_api.tools.sba.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_sba_size_standards(naics_code="000000")

        self.assertIn("No SBA size standards found", result)

    async def test_handles_api_error(self):
        with patch(
            "mcp_govt_api.tools.sba.fetch_json",
            new=AsyncMock(side_effect=Exception("Timeout")),
        ):
            result = await get_sba_size_standards(industry="tech")

        self.assertIn("Error fetching SBA size standards", result)
        self.assertIn("Timeout", result)


class TestGetSbaDisasterLoans(unittest.IsolatedAsyncioTestCase):
    async def test_returns_disaster_loans(self):
        mock_data = [
            {
                "fema_disaster_number": "4699",
                "damaged_state_abbreviation": "FL",
                "damaged_county": "Lee County",
                "damage_category": "Real Property",
                "total_approved_loan_amount": "150000.00",
                "fiscal_year": "2023",
            },
        ]

        with patch(
            "mcp_govt_api.tools.sba.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_sba_disaster_loans(state="FL", limit=5)

        self.assertIn("4699", result)
        self.assertIn("FL", result)
        self.assertIn("Lee County", result)
        self.assertIn("Real Property", result)
        self.assertIn("$150,000.00", result)
        self.assertIn("2023", result)

    async def test_filter_by_year(self):
        mock_data = [
            {
                "fema_disaster_number": "4800",
                "damaged_state_abbreviation": "TX",
                "damaged_county": "Harris County",
                "damage_category": "Economic Injury",
                "total_approved_loan_amount": "50000.00",
                "fiscal_year": "2024",
            },
        ]

        with patch(
            "mcp_govt_api.tools.sba.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ) as mock_fetch:
            result = await get_sba_disaster_loans(year="2024")

        self.assertIn("Harris County", result)
        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertIn("fiscal_year = '2024'", params["$where"])

    async def test_empty_results(self):
        mock_data = []

        with patch(
            "mcp_govt_api.tools.sba.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_sba_disaster_loans(state="ZZ")

        self.assertIn("No SBA disaster loans found", result)

    async def test_handles_api_error(self):
        with patch(
            "mcp_govt_api.tools.sba.fetch_json",
            new=AsyncMock(side_effect=Exception("Server error")),
        ):
            result = await get_sba_disaster_loans(state="CA")

        self.assertIn("Error fetching SBA disaster loans", result)
        self.assertIn("Server error", result)


if __name__ == "__main__":
    unittest.main()
