"""Tests for CMS healthcare provider and hospital quality tools."""

import unittest
from unittest.mock import AsyncMock, patch


class TestSearchHospitals(unittest.IsolatedAsyncioTestCase):
    """Tests for search_hospitals tool."""

    @patch("mcp_govt_api.tools.cms.fetch_json", new_callable=AsyncMock)
    async def test_search_hospitals_by_name(self, mock_fetch):
        from mcp_govt_api.tools.cms import search_hospitals

        mock_fetch.return_value = [
            {
                "facility_id": "050001",
                "hospital_name": "GENERAL HOSPITAL",
                "address": "123 Main St",
                "city": "Los Angeles",
                "state": "CA",
                "zip_code": "90001",
                "hospital_type": "Acute Care Hospitals",
                "hospital_ownership": "Government - State",
                "hospital_overall_rating": "4",
                "phone_number": "2135551234",
            }
        ]

        result = await search_hospitals(name="general", limit=5)

        self.assertIn("GENERAL HOSPITAL", result)
        self.assertIn("050001", result)
        self.assertIn("Los Angeles", result)
        self.assertIn("4 / 5", result)
        self.assertIn("Acute Care Hospitals", result)
        mock_fetch.assert_called_once()

    @patch("mcp_govt_api.tools.cms.fetch_json", new_callable=AsyncMock)
    async def test_search_hospitals_by_state(self, mock_fetch):
        from mcp_govt_api.tools.cms import search_hospitals

        mock_fetch.return_value = [
            {
                "facility_id": "100001",
                "hospital_name": "FLORIDA MEDICAL CENTER",
                "address": "456 Oak Ave",
                "city": "Miami",
                "state": "FL",
                "zip_code": "33101",
                "hospital_type": "Acute Care Hospitals",
                "hospital_ownership": "Voluntary non-profit - Private",
                "hospital_overall_rating": "3",
                "phone_number": "3055559876",
            }
        ]

        result = await search_hospitals(state="FL")

        self.assertIn("FLORIDA MEDICAL CENTER", result)
        self.assertIn("Miami", result)

    @patch("mcp_govt_api.tools.cms.fetch_json", new_callable=AsyncMock)
    async def test_search_hospitals_no_results(self, mock_fetch):
        from mcp_govt_api.tools.cms import search_hospitals

        mock_fetch.return_value = []

        result = await search_hospitals(name="nonexistenthospital")

        self.assertIn("No hospitals found", result)

    async def test_search_hospitals_no_params(self):
        from mcp_govt_api.tools.cms import search_hospitals

        result = await search_hospitals()

        self.assertIn("Error: at least one of", result)

    @patch("mcp_govt_api.tools.cms.fetch_json", new_callable=AsyncMock)
    async def test_search_hospitals_api_error(self, mock_fetch):
        from mcp_govt_api.tools.cms import search_hospitals

        mock_fetch.side_effect = Exception("API unavailable")

        result = await search_hospitals(state="CA")

        self.assertIn("Error fetching hospital data", result)


class TestGetHospitalQuality(unittest.IsolatedAsyncioTestCase):
    """Tests for get_hospital_quality tool."""

    @patch("mcp_govt_api.tools.cms.fetch_json", new_callable=AsyncMock)
    async def test_get_quality_basic(self, mock_fetch):
        from mcp_govt_api.tools.cms import get_hospital_quality

        mock_fetch.return_value = [
            {
                "facility_id": "050001",
                "hospital_name": "GENERAL HOSPITAL",
                "address": "123 Main St",
                "city": "Los Angeles",
                "state": "CA",
                "zip_code": "90001",
                "hospital_type": "Acute Care Hospitals",
                "hospital_ownership": "Government - State",
                "emergency_services": "Yes",
                "phone_number": "2135551234",
                "hospital_overall_rating": "4",
                "mortality_national_comparison": "Above the National Average",
                "safety_of_care_national_comparison": "Same as the National Average",
                "readmission_national_comparison": "Below the National Average",
                "patient_experience_national_comparison": "Above the National Average",
                "effectiveness_of_care_national_comparison": "Same as the National Average",
                "timeliness_of_care_national_comparison": "Above the National Average",
            }
        ]

        result = await get_hospital_quality(facility_id="050001")

        self.assertIn("GENERAL HOSPITAL", result)
        self.assertIn("4 / 5", result)
        self.assertIn("Above the National Average", result)
        self.assertIn("Emergency Services: Yes", result)
        self.assertIn("Mortality", result)
        self.assertIn("Safety of Care", result)
        mock_fetch.assert_called_once()

    @patch("mcp_govt_api.tools.cms.fetch_json", new_callable=AsyncMock)
    async def test_get_quality_not_found(self, mock_fetch):
        from mcp_govt_api.tools.cms import get_hospital_quality

        mock_fetch.return_value = []

        result = await get_hospital_quality(facility_id="999999")

        self.assertIn("No hospital found", result)

    async def test_get_quality_empty_id(self):
        from mcp_govt_api.tools.cms import get_hospital_quality

        result = await get_hospital_quality(facility_id="")

        self.assertIn("Error: facility_id is required", result)

    @patch("mcp_govt_api.tools.cms.fetch_json", new_callable=AsyncMock)
    async def test_get_quality_api_error(self, mock_fetch):
        from mcp_govt_api.tools.cms import get_hospital_quality

        mock_fetch.side_effect = Exception("Connection timeout")

        result = await get_hospital_quality(facility_id="050001")

        self.assertIn("Error fetching hospital quality data", result)


class TestSearchMedicareProviders(unittest.IsolatedAsyncioTestCase):
    """Tests for search_medicare_providers tool."""

    @patch("mcp_govt_api.tools.cms.fetch_json", new_callable=AsyncMock)
    async def test_search_providers_by_name(self, mock_fetch):
        from mcp_govt_api.tools.cms import search_medicare_providers

        mock_fetch.return_value = [
            {
                "npi": "1234567890",
                "lst_nm": "SMITH",
                "frst_nm": "JOHN",
                "org_name": "",
                "cred": "MD",
                "pri_spec": "Internal Medicine",
                "cty": "Chicago",
                "st": "IL",
                "zip": "60601",
            }
        ]

        result = await search_medicare_providers(name="smith", limit=5)

        self.assertIn("JOHN SMITH", result)
        self.assertIn("MD", result)
        self.assertIn("Internal Medicine", result)
        self.assertIn("1234567890", result)
        self.assertIn("Chicago", result)
        mock_fetch.assert_called_once()

    @patch("mcp_govt_api.tools.cms.fetch_json", new_callable=AsyncMock)
    async def test_search_providers_organization(self, mock_fetch):
        from mcp_govt_api.tools.cms import search_medicare_providers

        mock_fetch.return_value = [
            {
                "npi": "9876543210",
                "lst_nm": "",
                "frst_nm": "",
                "org_name": "CITY MEDICAL GROUP",
                "cred": "",
                "pri_spec": "Family Practice",
                "cty": "New York",
                "st": "NY",
                "zip": "10001",
            }
        ]

        result = await search_medicare_providers(name="city medical")

        self.assertIn("CITY MEDICAL GROUP", result)
        self.assertIn("Family Practice", result)

    @patch("mcp_govt_api.tools.cms.fetch_json", new_callable=AsyncMock)
    async def test_search_providers_by_specialty(self, mock_fetch):
        from mcp_govt_api.tools.cms import search_medicare_providers

        mock_fetch.return_value = [
            {
                "npi": "1111111111",
                "lst_nm": "DOE",
                "frst_nm": "JANE",
                "org_name": "",
                "cred": "DO",
                "pri_spec": "Cardiology",
                "cty": "Houston",
                "st": "TX",
                "zip": "77001",
            }
        ]

        result = await search_medicare_providers(specialty="Cardiology", state="TX")

        self.assertIn("JANE DOE", result)
        self.assertIn("Cardiology", result)
        self.assertIn("Houston", result)

    @patch("mcp_govt_api.tools.cms.fetch_json", new_callable=AsyncMock)
    async def test_search_providers_no_results(self, mock_fetch):
        from mcp_govt_api.tools.cms import search_medicare_providers

        mock_fetch.return_value = []

        result = await search_medicare_providers(name="zzzznonexistent")

        self.assertIn("No Medicare providers found", result)

    async def test_search_providers_no_params(self):
        from mcp_govt_api.tools.cms import search_medicare_providers

        result = await search_medicare_providers()

        self.assertIn("Error: at least one of", result)

    @patch("mcp_govt_api.tools.cms.fetch_json", new_callable=AsyncMock)
    async def test_search_providers_api_error(self, mock_fetch):
        from mcp_govt_api.tools.cms import search_medicare_providers

        mock_fetch.side_effect = Exception("Server error")

        result = await search_medicare_providers(state="CA")

        self.assertIn("Error fetching Medicare provider data", result)


if __name__ == "__main__":
    unittest.main()
