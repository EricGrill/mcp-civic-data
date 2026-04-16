"""Tests for FEMA disaster declarations and assistance tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.fema import (
    get_fema_assistance,
    get_fema_disaster_summary,
    get_fema_disasters,
)


class TestGetFemaDisasters(unittest.IsolatedAsyncioTestCase):
    async def test_returns_disaster_declarations(self):
        mock_data = {
            "DisasterDeclarationsSummaries": [
                {
                    "disasterNumber": 4699,
                    "declarationTitle": "HURRICANE IAN",
                    "state": "FL",
                    "incidentType": "Hurricane",
                    "declarationType": "DR",
                    "declarationDate": "2022-09-29T00:00:00.000Z",
                    "designatedArea": "Lee County",
                    "ihProgramDeclared": True,
                    "iaProgramDeclared": False,
                    "paProgramDeclared": True,
                    "hmProgramDeclared": True,
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.fema.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_fema_disasters(state="FL", limit=5)

        self.assertIn("DR-4699", result)
        self.assertIn("HURRICANE IAN", result)
        self.assertIn("FL", result)
        self.assertIn("Hurricane", result)
        self.assertIn("2022-09-29", result)
        self.assertIn("Lee County", result)
        self.assertIn("Public Assistance", result)

    async def test_empty_results(self):
        mock_data = {"DisasterDeclarationsSummaries": []}

        with patch(
            "mcp_govt_api.tools.fema.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_fema_disasters(state="ZZ")

        self.assertIn("No FEMA disaster declarations found", result)
        self.assertIn("ZZ", result)

    async def test_handles_api_error(self):
        with patch(
            "mcp_govt_api.tools.fema.fetch_json",
            new=AsyncMock(side_effect=Exception("Connection failed")),
        ):
            result = await get_fema_disasters(state="CA")

        self.assertIn("Error fetching FEMA disaster declarations", result)
        self.assertIn("Connection failed", result)

    async def test_filters_by_year_and_type(self):
        mock_data = {
            "DisasterDeclarationsSummaries": [
                {
                    "disasterNumber": 4800,
                    "declarationTitle": "SEVERE STORMS",
                    "state": "TX",
                    "incidentType": "Severe Storm",
                    "declarationType": "DR",
                    "declarationDate": "2024-05-15T00:00:00.000Z",
                    "ihProgramDeclared": False,
                    "iaProgramDeclared": False,
                    "paProgramDeclared": False,
                    "hmProgramDeclared": False,
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.fema.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ) as mock_fetch:
            result = await get_fema_disasters(
                year="2024", disaster_type="Severe Storm"
            )

        self.assertIn("SEVERE STORMS", result)
        call_args = mock_fetch.call_args
        params = call_args[1].get("params") or call_args[0][1]
        self.assertIn("fyDeclared eq '2024'", params["$filter"])
        self.assertIn("incidentType eq 'Severe Storm'", params["$filter"])


class TestGetFemaDisasterSummary(unittest.IsolatedAsyncioTestCase):
    async def test_returns_disaster_summary(self):
        mock_data = {
            "FemaWebDisasterSummaries": [
                {
                    "disasterNumber": 4699,
                    "declarationTitle": "HURRICANE IAN",
                    "declarationDate": "2022-09-29T00:00:00.000Z",
                    "state": "FL",
                    "incidentType": "Hurricane",
                    "totalAmountIhpApproved": 2500000000.50,
                    "totalAmountHaApproved": 1800000000.25,
                    "totalAmountOnaApproved": 700000000.25,
                    "totalNumberIhpApproved": 350000,
                    "totalObligatedAmountPa": 500000000.00,
                    "totalObligatedAmountHmgp": 100000000.00,
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.fema.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_fema_disaster_summary(disaster_number="4699")

        self.assertIn("DR-4699", result)
        self.assertIn("HURRICANE IAN", result)
        self.assertIn("FL", result)
        self.assertIn("$2,500,000,000.50", result)
        self.assertIn("350,000", result)

    async def test_missing_disaster_number(self):
        result = await get_fema_disaster_summary(disaster_number="")
        self.assertIn("Error", result)
        self.assertIn("disaster_number is required", result)

    async def test_not_found(self):
        mock_data = {"FemaWebDisasterSummaries": []}

        with patch(
            "mcp_govt_api.tools.fema.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_fema_disaster_summary(disaster_number="9999")

        self.assertIn("No FEMA disaster summary found", result)
        self.assertIn("9999", result)

    async def test_handles_api_error(self):
        with patch(
            "mcp_govt_api.tools.fema.fetch_json",
            new=AsyncMock(side_effect=Exception("Timeout")),
        ):
            result = await get_fema_disaster_summary(disaster_number="4699")

        self.assertIn("Error fetching FEMA disaster summary", result)


class TestGetFemaAssistance(unittest.IsolatedAsyncioTestCase):
    async def test_returns_housing_assistance(self):
        mock_data = {
            "HousingAssistanceOwners": [
                {
                    "disasterNumber": 4699,
                    "state": "FL",
                    "county": "Lee County",
                    "city": "Fort Myers",
                    "totalApprovedIhpAmount": 150000000.00,
                    "repairReplaceAmount": 120000000.00,
                    "rentalAmount": 30000000.00,
                    "totalInspected": 50000,
                    "totalDamaged": 35000,
                    "approvedBetween1And10000": 15000,
                    "approvedOver25000": 5000,
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.fema.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_fema_assistance(state="FL", disaster_number="4699")

        self.assertIn("DR-4699", result)
        self.assertIn("Fort Myers", result)
        self.assertIn("Lee County", result)
        self.assertIn("$150,000,000.00", result)
        self.assertIn("50,000", result)

    async def test_empty_results(self):
        mock_data = {"HousingAssistanceOwners": []}

        with patch(
            "mcp_govt_api.tools.fema.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_fema_assistance(state="ZZ")

        self.assertIn("No FEMA housing assistance data found", result)

    async def test_handles_api_error(self):
        with patch(
            "mcp_govt_api.tools.fema.fetch_json",
            new=AsyncMock(side_effect=Exception("Server error")),
        ):
            result = await get_fema_assistance(state="TX")

        self.assertIn("Error fetching FEMA housing assistance data", result)
        self.assertIn("Server error", result)


if __name__ == "__main__":
    unittest.main()
