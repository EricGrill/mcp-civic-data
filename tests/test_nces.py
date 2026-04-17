import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.nces import (
    get_school_enrollment,
    search_colleges,
    search_school_districts,
)


class SearchSchoolDistrictsTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_returns_formatted_results(self):
        mock_response = {
            "results": [
                {
                    "lea_name": "Los Angeles Unified",
                    "state_name": "California",
                    "city_location": "Los Angeles",
                    "enrollment": 600000,
                    "phone": "213-241-1000",
                    "zip_location": "90012",
                    "leaid": "0622710",
                }
            ],
        }

        with patch(
            "mcp_govt_api.tools.nces.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await search_school_districts(state="California")

        self.assertIn("Los Angeles Unified", result)
        self.assertIn("California", result)
        self.assertIn("Los Angeles", result)
        self.assertIn("600000", result)
        self.assertIn("0622710", result)

    async def test_search_empty_results(self):
        with patch(
            "mcp_govt_api.tools.nces.fetch_json",
            new=AsyncMock(return_value={"results": []}),
        ):
            result = await search_school_districts(state="Nonexistent")

        self.assertIn("No school districts found", result)

    async def test_search_handles_error(self):
        with patch(
            "mcp_govt_api.tools.nces.fetch_json",
            new=AsyncMock(side_effect=Exception("API error")),
        ):
            result = await search_school_districts(state="California")

        self.assertIn("Error searching school districts", result)


class GetSchoolEnrollmentTests(unittest.IsolatedAsyncioTestCase):
    async def test_enrollment_returns_formatted_results(self):
        mock_response = {
            "results": [
                {
                    "school_name": "Lincoln Elementary",
                    "state_name": "California",
                    "enrollment": 450,
                    "grade": "3",
                    "lea_name": "Los Angeles Unified",
                    "race": "Total",
                    "sex": "Total",
                }
            ],
        }

        with patch(
            "mcp_govt_api.tools.nces.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await get_school_enrollment(state="California")

        self.assertIn("Lincoln Elementary", result)
        self.assertIn("Los Angeles Unified", result)
        self.assertIn("450", result)
        self.assertIn("California", result)

    async def test_enrollment_empty_results(self):
        with patch(
            "mcp_govt_api.tools.nces.fetch_json",
            new=AsyncMock(return_value={"results": []}),
        ):
            result = await get_school_enrollment(state="Nonexistent")

        self.assertIn("No enrollment data found", result)

    async def test_enrollment_handles_error(self):
        with patch(
            "mcp_govt_api.tools.nces.fetch_json",
            new=AsyncMock(side_effect=Exception("Timeout")),
        ):
            result = await get_school_enrollment(state="California")

        self.assertIn("Error fetching school enrollment", result)


class SearchCollegesTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_returns_formatted_results(self):
        mock_response = {
            "results": [
                {
                    "inst_name": "Stanford University",
                    "state_name": "California",
                    "city": "Stanford",
                    "zip": "94305",
                    "inst_level": "4-year",
                    "inst_control": "Private nonprofit",
                    "hbcu": 0,
                    "unitid": "243744",
                }
            ],
        }

        with patch(
            "mcp_govt_api.tools.nces.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await search_colleges(state="California", name="Stanford")

        self.assertIn("Stanford University", result)
        self.assertIn("California", result)
        self.assertIn("94305", result)
        self.assertIn("Private nonprofit", result)
        self.assertIn("HBCU: No", result)
        self.assertIn("243744", result)

    async def test_search_hbcu(self):
        mock_response = {
            "results": [
                {
                    "inst_name": "Howard University",
                    "state_name": "District of Columbia",
                    "city": "Washington",
                    "zip": "20059",
                    "inst_level": "4-year",
                    "inst_control": "Private nonprofit",
                    "hbcu": 1,
                    "unitid": "131520",
                }
            ],
        }

        with patch(
            "mcp_govt_api.tools.nces.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await search_colleges(name="Howard")

        self.assertIn("Howard University", result)
        self.assertIn("HBCU: Yes", result)

    async def test_search_empty_results(self):
        with patch(
            "mcp_govt_api.tools.nces.fetch_json",
            new=AsyncMock(return_value={"results": []}),
        ):
            result = await search_colleges(name="Nonexistent")

        self.assertIn("No colleges found", result)

    async def test_search_handles_error(self):
        with patch(
            "mcp_govt_api.tools.nces.fetch_json",
            new=AsyncMock(side_effect=Exception("Connection error")),
        ):
            result = await search_colleges(state="California")

        self.assertIn("Error searching colleges", result)


if __name__ == "__main__":
    unittest.main()
