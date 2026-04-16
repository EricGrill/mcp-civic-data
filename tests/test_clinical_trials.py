"""Tests for ClinicalTrials.gov health research tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.clinical_trials import (
    get_clinical_trial,
    get_trial_statistics,
    search_clinical_trials,
)


class TestSearchClinicalTrials(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_results(self):
        mock_data = {
            "totalCount": 1,
            "studies": [
                {
                    "protocolSection": {
                        "identificationModule": {
                            "nctId": "NCT04280705",
                            "briefTitle": "Adaptive COVID-19 Treatment Trial",
                        },
                        "statusModule": {
                            "overallStatus": "COMPLETED",
                            "startDateStruct": {"date": "2020-02-21"},
                        },
                        "conditionsModule": {
                            "conditions": ["COVID-19"],
                        },
                        "designModule": {
                            "studyType": "INTERVENTIONAL",
                            "phases": ["PHASE3"],
                        },
                    }
                }
            ],
        }
        with patch(
            "mcp_govt_api.tools.clinical_trials.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await search_clinical_trials(query="covid")

        self.assertIn("Adaptive COVID-19 Treatment Trial", result)
        self.assertIn("NCT04280705", result)
        self.assertIn("COMPLETED", result)
        self.assertIn("COVID-19", result)
        self.assertIn("INTERVENTIONAL", result)
        self.assertIn("Source: ClinicalTrials.gov", result)

    async def test_returns_message_when_no_results(self):
        mock_data = {"totalCount": 0, "studies": []}
        with patch(
            "mcp_govt_api.tools.clinical_trials.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await search_clinical_trials(query="nonexistentdisease12345")

        self.assertIn("No clinical trials found", result)

    async def test_returns_error_on_exception(self):
        with patch(
            "mcp_govt_api.tools.clinical_trials.fetch_json",
            new=AsyncMock(side_effect=Exception("timeout")),
        ):
            result = await search_clinical_trials(query="test")

        self.assertIn("Error searching clinical trials", result)

    async def test_passes_all_search_params(self):
        mock_data = {"totalCount": 0, "studies": []}
        mock_fetch = AsyncMock(return_value=mock_data)
        with patch("mcp_govt_api.tools.clinical_trials.fetch_json", new=mock_fetch):
            await search_clinical_trials(
                query="cancer",
                condition="breast cancer",
                intervention="pembrolizumab",
                status="RECRUITING",
                limit=5,
            )

        _, kwargs = mock_fetch.call_args
        params = kwargs.get("params", {})
        self.assertEqual(params["query.term"], "cancer")
        self.assertEqual(params["query.cond"], "breast cancer")
        self.assertEqual(params["query.intr"], "pembrolizumab")
        self.assertEqual(params["filter.overallStatus"], "RECRUITING")
        self.assertEqual(params["pageSize"], "5")

    async def test_limits_capped_at_50(self):
        mock_data = {"totalCount": 0, "studies": []}
        mock_fetch = AsyncMock(return_value=mock_data)
        with patch("mcp_govt_api.tools.clinical_trials.fetch_json", new=mock_fetch):
            await search_clinical_trials(query="test", limit=100)

        _, kwargs = mock_fetch.call_args
        params = kwargs.get("params", {})
        self.assertEqual(params["pageSize"], "50")


class TestGetClinicalTrial(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_trial_details(self):
        mock_data = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT04280705",
                    "briefTitle": "Adaptive COVID-19 Treatment Trial",
                    "officialTitle": "A Multicenter Adaptive Randomized Trial",
                },
                "statusModule": {
                    "overallStatus": "COMPLETED",
                    "startDateStruct": {"date": "2020-02-21"},
                    "completionDateStruct": {"date": "2023-03-31"},
                },
                "descriptionModule": {
                    "briefSummary": "This study evaluates treatments for COVID-19.",
                },
                "conditionsModule": {
                    "conditions": ["COVID-19", "SARS-CoV-2"],
                },
                "designModule": {
                    "studyType": "INTERVENTIONAL",
                    "phases": ["PHASE3"],
                    "enrollmentInfo": {"count": 1062, "type": "ACTUAL"},
                },
                "eligibilityModule": {
                    "minimumAge": "18 Years",
                    "sex": "ALL",
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {
                        "name": "National Institute of Allergy and Infectious Diseases",
                    },
                    "collaborators": [{"name": "Gilead Sciences"}],
                },
                "armsInterventionsModule": {
                    "interventions": [
                        {"type": "DRUG", "name": "Remdesivir"},
                    ],
                },
            }
        }
        with patch(
            "mcp_govt_api.tools.clinical_trials.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_clinical_trial(nct_id="NCT04280705")

        self.assertIn("Adaptive COVID-19 Treatment Trial", result)
        self.assertIn("NCT04280705", result)
        self.assertIn("COMPLETED", result)
        self.assertIn("INTERVENTIONAL", result)
        self.assertIn("PHASE3", result)
        self.assertIn("1062", result)
        self.assertIn("COVID-19", result)
        self.assertIn("Remdesivir", result)
        self.assertIn("18 Years", result)
        self.assertIn("National Institute of Allergy", result)
        self.assertIn("Gilead Sciences", result)
        self.assertIn("Source: ClinicalTrials.gov", result)

    async def test_returns_error_for_invalid_nct_id(self):
        result = await get_clinical_trial(nct_id="INVALID123")
        self.assertIn("Error: NCT ID must start with 'NCT'", result)

    async def test_returns_error_on_exception(self):
        with patch(
            "mcp_govt_api.tools.clinical_trials.fetch_json",
            new=AsyncMock(side_effect=Exception("not found")),
        ):
            result = await get_clinical_trial(nct_id="NCT00000000")

        self.assertIn("Error fetching clinical trial", result)

    async def test_handles_empty_protocol(self):
        mock_data = {"protocolSection": {}}
        with patch(
            "mcp_govt_api.tools.clinical_trials.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_clinical_trial(nct_id="NCT99999999")

        # Should not raise, should still produce output
        self.assertIn("NCT99999999", result)

    async def test_normalizes_nct_id(self):
        mock_data = {"protocolSection": {}}
        mock_fetch = AsyncMock(return_value=mock_data)
        with patch("mcp_govt_api.tools.clinical_trials.fetch_json", new=mock_fetch):
            await get_clinical_trial(nct_id="  nct04280705  ")

        url = mock_fetch.call_args[0][0]
        self.assertIn("NCT04280705", url)


class TestGetTrialStatistics(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_statistics(self):
        mock_data = {"totalStudies": 500000}
        with patch(
            "mcp_govt_api.tools.clinical_trials.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_trial_statistics()

        self.assertIn("500,000", result)
        self.assertIn("Source: ClinicalTrials.gov", result)

    async def test_returns_error_on_exception(self):
        with patch(
            "mcp_govt_api.tools.clinical_trials.fetch_json",
            new=AsyncMock(side_effect=Exception("server error")),
        ):
            result = await get_trial_statistics()

        self.assertIn("Error fetching ClinicalTrials.gov statistics", result)

    async def test_handles_alternative_response_key(self):
        mock_data = {"total": 450000}
        with patch(
            "mcp_govt_api.tools.clinical_trials.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_trial_statistics()

        self.assertIn("450,000", result)


if __name__ == "__main__":
    unittest.main()
