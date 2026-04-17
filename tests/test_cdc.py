"""Tests for CDC public health surveillance tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.cdc import (
    get_cdc_disease_surveillance,
    get_cdc_vaccination_coverage,
    query_cdc_open_data,
    search_cdc_datasets,
)


class TestSearchCdcDatasets(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_results(self):
        mock_data = [
            {
                "id": "abc-123",
                "name": "COVID-19 Case Surveillance",
                "description": "Nationwide COVID-19 case data",
                "category": "Public Health",
                "rowsUpdatedAt": 1700000000,
            },
        ]
        with patch(
            "mcp_govt_api.tools.cdc.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await search_cdc_datasets(query="covid")

        self.assertIn("COVID-19 Case Surveillance", result)
        self.assertIn("abc-123", result)
        self.assertIn("Public Health", result)
        self.assertIn("Source: CDC Open Data", result)

    async def test_returns_message_when_no_results(self):
        with patch(
            "mcp_govt_api.tools.cdc.fetch_json",
            new=AsyncMock(return_value=[]),
        ):
            result = await search_cdc_datasets(query="nonexistent")

        self.assertIn("No CDC datasets found", result)

    async def test_returns_error_on_exception(self):
        with patch(
            "mcp_govt_api.tools.cdc.fetch_json",
            new=AsyncMock(side_effect=Exception("timeout")),
        ):
            result = await search_cdc_datasets(query="test")

        self.assertIn("Error searching CDC datasets", result)


class TestGetCdcDiseaseSurveillance(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_surveillance_data(self):
        mock_data = [
            {
                "disease": "Salmonellosis",
                "reporting_area": "California",
                "mmwr_year": "2024",
                "mmwr_week": "42",
                "current_week": "15",
            },
        ]
        with patch(
            "mcp_govt_api.tools.cdc.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_cdc_disease_surveillance(
                disease="Salmonellosis", state="California"
            )

        self.assertIn("Salmonellosis", result)
        self.assertIn("California", result)
        self.assertIn("2024/42", result)
        self.assertIn("Current Week Cases: 15", result)
        self.assertIn("Source: CDC NNDSS", result)

    async def test_returns_message_when_no_data(self):
        with patch(
            "mcp_govt_api.tools.cdc.fetch_json",
            new=AsyncMock(return_value=[]),
        ):
            result = await get_cdc_disease_surveillance(disease="FakeDisease")

        self.assertIn("No NNDSS surveillance records found", result)

    async def test_returns_error_on_exception(self):
        with patch(
            "mcp_govt_api.tools.cdc.fetch_json",
            new=AsyncMock(side_effect=Exception("connection error")),
        ):
            result = await get_cdc_disease_surveillance()

        self.assertIn("Error fetching CDC disease surveillance data", result)

    async def test_passes_soda_params(self):
        mock_fetch = AsyncMock(return_value=[])
        with patch("mcp_govt_api.tools.cdc.fetch_json", new=mock_fetch):
            await get_cdc_disease_surveillance(
                disease="Hepatitis", state="Texas", limit=5
            )

        # Verify the call was made with the right URL
        url = mock_fetch.call_args[0][0]
        self.assertIn("x9gk-5huc", url)


class TestGetCdcVaccinationCoverage(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_vaccination_data(self):
        mock_data = [
            {
                "vaccine": "Influenza",
                "dose": ">=1 Dose",
                "geography": "National",
                "survey_year": "2023",
                "dimension_type": "Age",
                "dimension": "6 months - 17 years",
                "coverage_estimate": "57.4",
                "_95_ci_low": "55.1",
                "_95_ci_high": "59.7",
            },
        ]
        with patch(
            "mcp_govt_api.tools.cdc.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_cdc_vaccination_coverage(
                vaccine_type="Influenza"
            )

        self.assertIn("Influenza", result)
        self.assertIn("National", result)
        self.assertIn("57.4%", result)
        self.assertIn("55.1%", result)
        self.assertIn("Source: CDC National Immunization Survey", result)

    async def test_returns_message_when_no_data(self):
        with patch(
            "mcp_govt_api.tools.cdc.fetch_json",
            new=AsyncMock(return_value=[]),
        ):
            result = await get_cdc_vaccination_coverage(
                vaccine_type="NonexistentVaccine"
            )

        self.assertIn("No vaccination coverage records found", result)

    async def test_returns_error_on_exception(self):
        with patch(
            "mcp_govt_api.tools.cdc.fetch_json",
            new=AsyncMock(side_effect=Exception("server error")),
        ):
            result = await get_cdc_vaccination_coverage()

        self.assertIn("Error fetching CDC vaccination coverage data", result)


class TestQueryCdcOpenData(unittest.IsolatedAsyncioTestCase):
    async def test_returns_raw_data(self):
        mock_data = [{"col": "val"}]
        with patch(
            "mcp_govt_api.tools.cdc.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ) as mock_fetch:
            result = await query_cdc_open_data(
                dataset_id="x9gk-5huc",
                params={"$limit": "5"},
            )

        self.assertEqual(result, mock_data)
        mock_fetch.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
