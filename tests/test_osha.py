"""Tests for OSHA workplace safety and enforcement tools."""

import unittest
from unittest.mock import AsyncMock, patch


class TestSearchOSHAInspections(unittest.IsolatedAsyncioTestCase):
    """Tests for search_osha_inspections tool."""

    async def test_returns_inspections(self):
        from mcp_govt_api.tools.osha import search_osha_inspections

        mock_data = [
            {
                "activity_nr": "1234567",
                "estab_name": "ACME CONSTRUCTION",
                "site_city": "Los Angeles",
                "site_state": "CA",
                "open_date": "2024-01-15",
                "close_case_date": "2024-03-20",
                "insp_type": "Complaint",
                "sic_code": "1521",
                "total_current_penalty": "15000",
            }
        ]

        with patch(
            "mcp_govt_api.tools.osha.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ) as mock_fetch:
            result = await search_osha_inspections(state="CA", limit=10)

        mock_fetch.assert_awaited_once()
        call_args = mock_fetch.call_args
        self.assertIn("site_state:CA", call_args.kwargs.get("params", call_args[1].get("params", {})).get("filters", ""))
        self.assertIn("ACME CONSTRUCTION", result)
        self.assertIn("1234567", result)
        self.assertIn("Los Angeles, CA", result)
        self.assertIn("Complaint", result)

    async def test_returns_message_when_no_results(self):
        from mcp_govt_api.tools.osha import search_osha_inspections

        with patch(
            "mcp_govt_api.tools.osha.fetch_json",
            new=AsyncMock(return_value=[]),
        ):
            result = await search_osha_inspections(state="ZZ")

        self.assertIn("No OSHA inspections found", result)

    async def test_handles_error(self):
        from mcp_govt_api.tools.osha import search_osha_inspections

        with patch(
            "mcp_govt_api.tools.osha.fetch_json",
            new=AsyncMock(side_effect=Exception("Connection error")),
        ):
            result = await search_osha_inspections(state="CA")

        self.assertIn("Error fetching OSHA inspections", result)

    async def test_filters_by_establishment(self):
        from mcp_govt_api.tools.osha import search_osha_inspections

        with patch(
            "mcp_govt_api.tools.osha.fetch_json",
            new=AsyncMock(return_value=[]),
        ) as mock_fetch:
            await search_osha_inspections(establishment="ACME")

        call_args = mock_fetch.call_args
        params = call_args.kwargs.get("params", call_args[1].get("params", {}))
        self.assertIn("estab_name:ACME", params.get("filters", ""))

    async def test_limit_capped_at_100(self):
        from mcp_govt_api.tools.osha import search_osha_inspections

        with patch(
            "mcp_govt_api.tools.osha.fetch_json",
            new=AsyncMock(return_value=[]),
        ) as mock_fetch:
            await search_osha_inspections(limit=200)

        call_args = mock_fetch.call_args
        params = call_args.kwargs.get("params", call_args[1].get("params", {}))
        self.assertEqual(params["per_page"], 100)


class TestGetOSHAViolations(unittest.IsolatedAsyncioTestCase):
    """Tests for get_osha_violations tool."""

    async def test_returns_violations(self):
        from mcp_govt_api.tools.osha import get_osha_violations

        mock_data = [
            {
                "activity_nr": "1234567",
                "standard": "19260501",
                "viol_type": "S",
                "gravity": "10",
                "initial_penalty": 7000,
                "current_penalty": 7000,
                "abate_date": "2024-06-01",
                "abate_complete": "X",
            }
        ]

        with patch(
            "mcp_govt_api.tools.osha.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ) as mock_fetch:
            result = await get_osha_violations(inspection_nr="1234567")

        mock_fetch.assert_awaited_once()
        self.assertIn("19260501", result)
        self.assertIn("Serious", result)
        self.assertIn("$7000", result)

    async def test_requires_inspection_nr(self):
        from mcp_govt_api.tools.osha import get_osha_violations

        result = await get_osha_violations()
        self.assertIn("Error: Please provide an inspection number", result)

    async def test_returns_message_when_no_violations(self):
        from mcp_govt_api.tools.osha import get_osha_violations

        with patch(
            "mcp_govt_api.tools.osha.fetch_json",
            new=AsyncMock(return_value=[]),
        ):
            result = await get_osha_violations(inspection_nr="9999999")

        self.assertIn("No violations found", result)

    async def test_handles_error(self):
        from mcp_govt_api.tools.osha import get_osha_violations

        with patch(
            "mcp_govt_api.tools.osha.fetch_json",
            new=AsyncMock(side_effect=Exception("Timeout")),
        ):
            result = await get_osha_violations(inspection_nr="1234567")

        self.assertIn("Error fetching OSHA violations", result)


class TestSearchOSHAFatalities(unittest.IsolatedAsyncioTestCase):
    """Tests for search_osha_fatalities tool."""

    async def test_returns_fatalities(self):
        from mcp_govt_api.tools.osha import search_osha_fatalities

        mock_data = [
            {
                "id": "42",
                "date_of_incident": "2024-02-10",
                "city": "Houston",
                "state": "TX",
                "employer": "BIG BUILD LLC",
                "summary": "Worker fell from scaffolding at construction site.",
            }
        ]

        with patch(
            "mcp_govt_api.tools.osha.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ) as mock_fetch:
            result = await search_osha_fatalities(state="TX")

        mock_fetch.assert_awaited_once()
        self.assertIn("BIG BUILD LLC", result)
        self.assertIn("Houston, TX", result)
        self.assertIn("fell from scaffolding", result)

    async def test_returns_message_when_no_results(self):
        from mcp_govt_api.tools.osha import search_osha_fatalities

        with patch(
            "mcp_govt_api.tools.osha.fetch_json",
            new=AsyncMock(return_value=[]),
        ):
            result = await search_osha_fatalities(state="ZZ")

        self.assertIn("No OSHA fatality reports found", result)

    async def test_handles_error(self):
        from mcp_govt_api.tools.osha import search_osha_fatalities

        with patch(
            "mcp_govt_api.tools.osha.fetch_json",
            new=AsyncMock(side_effect=Exception("Server error")),
        ):
            result = await search_osha_fatalities(state="TX")

        self.assertIn("Error fetching OSHA fatality reports", result)

    async def test_filters_by_keyword(self):
        from mcp_govt_api.tools.osha import search_osha_fatalities

        with patch(
            "mcp_govt_api.tools.osha.fetch_json",
            new=AsyncMock(return_value=[]),
        ) as mock_fetch:
            await search_osha_fatalities(keyword="fall")

        call_args = mock_fetch.call_args
        params = call_args.kwargs.get("params", call_args[1].get("params", {}))
        self.assertIn("summary:fall", params.get("filters", ""))


if __name__ == "__main__":
    unittest.main()
