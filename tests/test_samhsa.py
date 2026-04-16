"""Tests for SAMHSA mental health and treatment facility tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.samhsa import (
    find_treatment_facilities,
    get_samhsa_facility_details,
    search_samhsa_datasets,
)


class TestFindTreatmentFacilities(unittest.IsolatedAsyncioTestCase):
    async def test_returns_facilities(self):
        mock_data = {
            "rows": [
                {
                    "name1": "Recovery Center of Hope",
                    "street1": "123 Main St",
                    "city": "Springfield",
                    "state": "IL",
                    "zip": "62704",
                    "phone": "217-555-0100",
                    "services": ["Substance abuse treatment", "Mental health services"],
                    "payment": ["Medicaid", "Private insurance"],
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.samhsa.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await find_treatment_facilities(location="Springfield, IL")

        self.assertIn("Recovery Center of Hope", result)
        self.assertIn("123 Main St", result)
        self.assertIn("Springfield", result)
        self.assertIn("217-555-0100", result)
        self.assertIn("Substance abuse treatment", result)
        self.assertIn("Medicaid", result)

    async def test_returns_facilities_from_list(self):
        mock_data = [
            {
                "name1": "Metro Behavioral Health",
                "street1": "456 Oak Ave",
                "city": "Chicago",
                "state": "IL",
                "zip": "60601",
                "phone": "312-555-0200",
            },
        ]

        with patch(
            "mcp_govt_api.tools.samhsa.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await find_treatment_facilities(
                location="Chicago, IL", service_type="MH"
            )

        self.assertIn("Metro Behavioral Health", result)
        self.assertIn("Chicago", result)

    async def test_empty_results(self):
        mock_data = {"rows": []}

        with patch(
            "mcp_govt_api.tools.samhsa.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await find_treatment_facilities(location="Middle of Nowhere")

        self.assertIn("No SAMHSA treatment facilities found", result)
        self.assertIn("Middle of Nowhere", result)

    async def test_invalid_service_type(self):
        result = await find_treatment_facilities(
            location="Chicago", service_type="INVALID"
        )
        self.assertIn("Error", result)
        self.assertIn("service_type", result)

    async def test_handles_api_error(self):
        with patch(
            "mcp_govt_api.tools.samhsa.fetch_json",
            new=AsyncMock(side_effect=Exception("Connection refused")),
        ):
            result = await find_treatment_facilities(location="New York")

        self.assertIn("Error fetching SAMHSA treatment facilities", result)
        self.assertIn("Connection refused", result)

    async def test_limit_capped_at_50(self):
        mock_data = {"rows": []}

        with patch(
            "mcp_govt_api.tools.samhsa.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ) as mock_fetch:
            await find_treatment_facilities(location="LA", limit=100)

        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertEqual(params["limitValue"], 50)


class TestSearchSamhsaDatasets(unittest.IsolatedAsyncioTestCase):
    async def test_returns_datasets(self):
        mock_data = [
            {
                "name": "Treatment Episode Data Set",
                "id": "abcd-1234",
                "description": "Annual data on admissions to substance abuse treatment.",
                "category": "Substance Abuse",
                "dataUpdatedAt": "2024-06-15T00:00:00.000Z",
            },
        ]

        with patch(
            "mcp_govt_api.tools.samhsa.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await search_samhsa_datasets(query="treatment admissions")

        self.assertIn("Treatment Episode Data Set", result)
        self.assertIn("abcd-1234", result)
        self.assertIn("Substance Abuse", result)
        self.assertIn("2024-06-15", result)
        self.assertIn("data.samhsa.gov/resource/abcd-1234", result)

    async def test_empty_results(self):
        mock_data = []

        with patch(
            "mcp_govt_api.tools.samhsa.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await search_samhsa_datasets(query="nonexistent")

        self.assertIn("No SAMHSA datasets found", result)

    async def test_handles_api_error(self):
        with patch(
            "mcp_govt_api.tools.samhsa.fetch_json",
            new=AsyncMock(side_effect=Exception("Timeout")),
        ):
            result = await search_samhsa_datasets(query="opioid")

        self.assertIn("Error searching SAMHSA datasets", result)
        self.assertIn("Timeout", result)

    async def test_truncates_long_descriptions(self):
        mock_data = [
            {
                "name": "Long Dataset",
                "id": "wxyz-5678",
                "description": "A" * 300,
            },
        ]

        with patch(
            "mcp_govt_api.tools.samhsa.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await search_samhsa_datasets(query="test")

        self.assertIn("...", result)


class TestGetSamhsaFacilityDetails(unittest.IsolatedAsyncioTestCase):
    async def test_returns_facility_details(self):
        mock_data = {
            "name1": "Hope Treatment Center",
            "street1": "789 Elm St",
            "city": "Austin",
            "state": "TX",
            "zip": "73301",
            "phone": "512-555-0300",
            "website": "https://hopetreatment.example.com",
            "services": ["Outpatient", "Residential"],
            "payment": ["Medicaid", "Medicare", "Sliding scale"],
            "languages": ["English", "Spanish"],
            "specialPrograms": ["Veterans", "Adolescents"],
            "hours": "Mon-Fri 8am-6pm",
            "intakeProcess": "Walk-in and phone appointments accepted",
        }

        with patch(
            "mcp_govt_api.tools.samhsa.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_samhsa_facility_details(facility_id="12345")

        self.assertIn("Hope Treatment Center", result)
        self.assertIn("789 Elm St", result)
        self.assertIn("Austin", result)
        self.assertIn("512-555-0300", result)
        self.assertIn("hopetreatment.example.com", result)
        self.assertIn("Outpatient", result)
        self.assertIn("Medicaid", result)
        self.assertIn("Spanish", result)
        self.assertIn("Veterans", result)
        self.assertIn("Mon-Fri", result)
        self.assertIn("Walk-in", result)

    async def test_missing_facility_id(self):
        result = await get_samhsa_facility_details(facility_id="")
        self.assertIn("Error", result)
        self.assertIn("facility_id is required", result)

    async def test_not_found(self):
        with patch(
            "mcp_govt_api.tools.samhsa.fetch_json",
            new=AsyncMock(return_value={}),
        ):
            result = await get_samhsa_facility_details(facility_id="99999")

        self.assertIn("No SAMHSA facility found", result)
        self.assertIn("99999", result)

    async def test_handles_api_error(self):
        with patch(
            "mcp_govt_api.tools.samhsa.fetch_json",
            new=AsyncMock(side_effect=Exception("Not found")),
        ):
            result = await get_samhsa_facility_details(facility_id="12345")

        self.assertIn("Error fetching SAMHSA facility details", result)
        self.assertIn("Not found", result)


if __name__ == "__main__":
    unittest.main()
