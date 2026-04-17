"""Tests for EPA tools (ECHO, Envirofacts TRI)."""

import unittest
from unittest.mock import AsyncMock, patch


class TestSearchEpaFacilities(unittest.IsolatedAsyncioTestCase):
    """Tests for search_epa_facilities tool."""

    @patch("mcp_govt_api.tools.epa.fetch_json", new_callable=AsyncMock)
    async def test_search_facilities_by_state(self, mock_fetch):
        from mcp_govt_api.tools.epa import search_epa_facilities

        mock_fetch.return_value = {
            "Results": {
                "Message": "1 results found",
                "Facilities": [
                    {
                        "FacName": "ACME Chemical Plant",
                        "FacStreet": "123 Industrial Rd",
                        "FacCity": "Los Angeles",
                        "FacState": "CA",
                        "FacZip": "90001",
                        "RegistryId": "110000350174",
                        "DfrUrl": "https://echo.epa.gov/dfr/110000350174",
                    }
                ],
            }
        }

        result = await search_epa_facilities(state="CA")

        self.assertIn("ACME Chemical Plant", result)
        self.assertIn("110000350174", result)
        self.assertIn("Los Angeles", result)
        mock_fetch.assert_called_once()

    @patch("mcp_govt_api.tools.epa.fetch_json", new_callable=AsyncMock)
    async def test_search_facilities_by_zip(self, mock_fetch):
        from mcp_govt_api.tools.epa import search_epa_facilities

        mock_fetch.return_value = {
            "Results": {
                "Message": "1 results found",
                "Facilities": [
                    {
                        "FacName": "Zip Facility",
                        "FacStreet": "456 Main St",
                        "FacCity": "Beverly Hills",
                        "FacState": "CA",
                        "FacZip": "90210",
                        "RegistryId": "110000999999",
                    }
                ],
            }
        }

        result = await search_epa_facilities(zip_code="90210")

        self.assertIn("Zip Facility", result)
        self.assertIn("Beverly Hills", result)

    @patch("mcp_govt_api.tools.epa.fetch_json", new_callable=AsyncMock)
    async def test_search_facilities_no_results(self, mock_fetch):
        from mcp_govt_api.tools.epa import search_epa_facilities

        mock_fetch.return_value = {
            "Results": {
                "Message": "0 results found",
                "Facilities": [],
            }
        }

        result = await search_epa_facilities(state="XX")

        self.assertIn("No EPA-regulated facilities found", result)

    async def test_search_facilities_no_params(self):
        from mcp_govt_api.tools.epa import search_epa_facilities

        result = await search_epa_facilities()

        self.assertIn("Error: at least one of", result)

    @patch("mcp_govt_api.tools.epa.fetch_json", new_callable=AsyncMock)
    async def test_search_facilities_api_error(self, mock_fetch):
        from mcp_govt_api.tools.epa import search_epa_facilities

        mock_fetch.side_effect = Exception("API unavailable")

        result = await search_epa_facilities(state="CA")

        self.assertIn("Error fetching EPA facilities", result)

    @patch("mcp_govt_api.tools.epa.fetch_json", new_callable=AsyncMock)
    async def test_search_facilities_by_name(self, mock_fetch):
        from mcp_govt_api.tools.epa import search_epa_facilities

        mock_fetch.return_value = {
            "Results": {
                "Message": "1 results found",
                "Facilities": [
                    {
                        "FacName": "Test Refinery",
                        "FacStreet": "",
                        "FacCity": "Houston",
                        "FacState": "TX",
                        "FacZip": "77001",
                        "RegistryId": "220000111111",
                    }
                ],
            }
        }

        result = await search_epa_facilities(name="Test Refinery")

        self.assertIn("Test Refinery", result)
        self.assertIn("Houston", result)


class TestGetEpaFacilityInfo(unittest.IsolatedAsyncioTestCase):
    """Tests for get_epa_facility_info tool."""

    @patch("mcp_govt_api.tools.epa.fetch_json", new_callable=AsyncMock)
    async def test_facility_info_basic(self, mock_fetch):
        from mcp_govt_api.tools.epa import get_epa_facility_info

        mock_fetch.return_value = {
            "Results": {
                "Facility": {
                    "FacName": "ACME Chemical Plant",
                    "FacStreet": "123 Industrial Rd",
                    "FacCity": "Los Angeles",
                    "FacState": "CA",
                    "FacZip": "90001",
                    "FacCounty": "Los Angeles",
                    "FacLat": "34.0522",
                    "FacLong": "-118.2437",
                    "Programs": [
                        {"ProgramAcronym": "CWA"},
                        {"ProgramAcronym": "CAA"},
                    ],
                    "CWAComplianceStatus": "No Violation",
                    "CAAComplianceStatus": "In Violation",
                    "RCRAComplianceStatus": "",
                    "Inspections5yr": "3",
                    "EnforcementActions5yr": "1",
                    "Penalties5yr": "25000",
                }
            }
        }

        result = await get_epa_facility_info(facility_id="110000350174")

        self.assertIn("ACME Chemical Plant", result)
        self.assertIn("Los Angeles", result)
        self.assertIn("CWA", result)
        self.assertIn("No Violation", result)
        self.assertIn("In Violation", result)
        self.assertIn("$25000", result)
        self.assertIn("34.0522", result)
        mock_fetch.assert_called_once()

    @patch("mcp_govt_api.tools.epa.fetch_json", new_callable=AsyncMock)
    async def test_facility_info_not_found(self, mock_fetch):
        from mcp_govt_api.tools.epa import get_epa_facility_info

        mock_fetch.return_value = {
            "Results": {
                "Facility": {},
            }
        }

        result = await get_epa_facility_info(facility_id="000000000000")

        self.assertIn("No facility information found", result)

    async def test_facility_info_empty_id(self):
        from mcp_govt_api.tools.epa import get_epa_facility_info

        result = await get_epa_facility_info(facility_id="")

        self.assertIn("Error: facility_id is required", result)

    @patch("mcp_govt_api.tools.epa.fetch_json", new_callable=AsyncMock)
    async def test_facility_info_api_error(self, mock_fetch):
        from mcp_govt_api.tools.epa import get_epa_facility_info

        mock_fetch.side_effect = Exception("Connection timeout")

        result = await get_epa_facility_info(facility_id="110000350174")

        self.assertIn("Error fetching EPA facility info", result)


class TestGetToxicReleases(unittest.IsolatedAsyncioTestCase):
    """Tests for get_toxic_releases tool."""

    @patch("mcp_govt_api.tools.epa.fetch_json", new_callable=AsyncMock)
    async def test_toxic_releases_by_state(self, mock_fetch):
        from mcp_govt_api.tools.epa import get_toxic_releases

        mock_fetch.return_value = [
            {
                "FAC_NAME": "Big Chemical Corp",
                "FAC_CITY": "Sacramento",
                "FAC_STATE": "CA",
                "FAC_ZIP": "95814",
                "FAC_COUNTY": "Sacramento",
                "TRI_FACILITY_ID": "95814BGCHM12345",
                "REPORTING_YEAR": "2022",
                "PRIMARY_SIC": "2819",
                "FAC_LATITUDE": "38.5816",
                "FAC_LONGITUDE": "-121.4944",
            }
        ]

        result = await get_toxic_releases(state="CA")

        self.assertIn("Big Chemical Corp", result)
        self.assertIn("Sacramento", result)
        self.assertIn("95814BGCHM12345", result)
        self.assertIn("2022", result)
        mock_fetch.assert_called_once()

    @patch("mcp_govt_api.tools.epa.fetch_json", new_callable=AsyncMock)
    async def test_toxic_releases_by_year(self, mock_fetch):
        from mcp_govt_api.tools.epa import get_toxic_releases

        mock_fetch.return_value = [
            {
                "FAC_NAME": "Year Facility",
                "FAC_CITY": "Austin",
                "FAC_STATE": "TX",
                "FAC_ZIP": "73301",
                "FAC_COUNTY": "",
                "TRI_FACILITY_ID": "73301YRFCL99999",
                "REPORTING_YEAR": "2023",
                "PRIMARY_SIC": "",
                "FAC_LATITUDE": "",
                "FAC_LONGITUDE": "",
            }
        ]

        result = await get_toxic_releases(year="2023")

        self.assertIn("Year Facility", result)
        self.assertIn("2023", result)

    @patch("mcp_govt_api.tools.epa.fetch_json", new_callable=AsyncMock)
    async def test_toxic_releases_no_results(self, mock_fetch):
        from mcp_govt_api.tools.epa import get_toxic_releases

        mock_fetch.return_value = []

        result = await get_toxic_releases(state="XX")

        self.assertIn("No Toxics Release Inventory records found", result)

    async def test_toxic_releases_no_params(self):
        from mcp_govt_api.tools.epa import get_toxic_releases

        result = await get_toxic_releases()

        self.assertIn("Error: at least one of", result)

    @patch("mcp_govt_api.tools.epa.fetch_json", new_callable=AsyncMock)
    async def test_toxic_releases_api_error(self, mock_fetch):
        from mcp_govt_api.tools.epa import get_toxic_releases

        mock_fetch.side_effect = Exception("Server error")

        result = await get_toxic_releases(state="CA")

        self.assertIn("Error fetching TRI data", result)

    @patch("mcp_govt_api.tools.epa.fetch_json", new_callable=AsyncMock)
    async def test_toxic_releases_by_facility(self, mock_fetch):
        from mcp_govt_api.tools.epa import get_toxic_releases

        mock_fetch.return_value = [
            {
                "FAC_NAME": "Specific Plant",
                "FAC_CITY": "Portland",
                "FAC_STATE": "OR",
                "FAC_ZIP": "97201",
                "FAC_COUNTY": "Multnomah",
                "TRI_FACILITY_ID": "97201SPCPL00001",
                "REPORTING_YEAR": "2021",
                "PRIMARY_SIC": "3312",
                "FAC_LATITUDE": "45.5155",
                "FAC_LONGITUDE": "-122.6789",
            }
        ]

        result = await get_toxic_releases(facility="Specific Plant")

        self.assertIn("Specific Plant", result)
        self.assertIn("Multnomah", result)
        self.assertIn("3312", result)


if __name__ == "__main__":
    unittest.main()
