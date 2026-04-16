import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.bjs import (
    get_arrest_data,
    get_crime_estimates,
    search_crime_datasets,
)


class BjsToolTests(unittest.IsolatedAsyncioTestCase):
    @patch("mcp_govt_api.tools.bjs.config")
    @patch(
        "mcp_govt_api.tools.bjs.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_crime_estimates_state(self, mock_fetch, mock_config):
        mock_config.fbi_cde_api_key = "test-key"
        mock_fetch.return_value = {
            "results": [
                {
                    "year": 2023,
                    "population": 39538223,
                    "violent_crime": 170000,
                    "property_crime": 800000,
                    "homicide": 2000,
                    "robbery": 55000,
                    "aggravated_assault": 110000,
                    "burglary": 150000,
                    "larceny": 500000,
                    "motor_vehicle_theft": 150000,
                }
            ],
        }

        result = await get_crime_estimates(state="CA", from_year="2023", to_year="2023")

        self.assertIn("Crime Estimates: CA", result)
        self.assertIn("2023", result)
        self.assertIn("Violent Crime", result)
        self.assertIn("Property Crime", result)
        self.assertIn("Robbery", result)
        self.assertIn("FBI Crime Data Explorer", result)
        mock_fetch.assert_awaited_once()
        call_args = mock_fetch.call_args
        self.assertIn("/estimate/state/CA", call_args.args[0])
        self.assertEqual(call_args.kwargs["params"]["from"], "2023")

    @patch("mcp_govt_api.tools.bjs.config")
    @patch(
        "mcp_govt_api.tools.bjs.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_crime_estimates_national(self, mock_fetch, mock_config):
        mock_config.fbi_cde_api_key = "test-key"
        mock_fetch.return_value = {
            "results": [
                {
                    "year": 2022,
                    "population": 333287557,
                    "violent_crime": 1200000,
                    "property_crime": 6500000,
                }
            ],
        }

        result = await get_crime_estimates()

        self.assertIn("Crime Estimates: National", result)
        self.assertIn("2022", result)
        mock_fetch.assert_awaited_once()
        call_args = mock_fetch.call_args
        self.assertIn("/estimate/national", call_args.args[0])

    @patch("mcp_govt_api.tools.bjs.config")
    @patch(
        "mcp_govt_api.tools.bjs.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_crime_estimates_no_results(self, mock_fetch, mock_config):
        mock_config.fbi_cde_api_key = "test-key"
        mock_fetch.return_value = {"results": []}

        result = await get_crime_estimates(state="ZZ")

        self.assertIn("No crime estimate data found", result)

    @patch("mcp_govt_api.tools.bjs.config")
    @patch(
        "mcp_govt_api.tools.bjs.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_arrest_data_returns_results(self, mock_fetch, mock_config):
        mock_config.fbi_cde_api_key = "test-key"
        mock_fetch.return_value = {
            "results": [
                {
                    "year": 2022,
                    "total_arrests": 750000,
                    "male": 600000,
                    "female": 150000,
                    "adult": 700000,
                    "juvenile": 50000,
                }
            ],
        }

        result = await get_arrest_data(offense="robbery", from_year="2022", to_year="2022")

        self.assertIn("National Arrest Data: Robbery", result)
        self.assertIn("2022", result)
        self.assertIn("Total Arrests", result)
        self.assertIn("Male", result)
        self.assertIn("Female", result)
        self.assertIn("FBI Crime Data Explorer", result)
        mock_fetch.assert_awaited_once()
        call_args = mock_fetch.call_args
        self.assertIn("/arrest/national/robbery", call_args.args[0])

    @patch("mcp_govt_api.tools.bjs.config")
    @patch(
        "mcp_govt_api.tools.bjs.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_arrest_data_all_offenses(self, mock_fetch, mock_config):
        mock_config.fbi_cde_api_key = "test-key"
        mock_fetch.return_value = {
            "results": [
                {
                    "year": 2022,
                    "total_arrests": 10000000,
                }
            ],
        }

        result = await get_arrest_data()

        self.assertIn("All Offenses", result)
        mock_fetch.assert_awaited_once()
        call_args = mock_fetch.call_args
        self.assertTrue(call_args.args[0].endswith("/arrest/national"))

    @patch("mcp_govt_api.tools.bjs.config")
    @patch(
        "mcp_govt_api.tools.bjs.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_arrest_data_no_results(self, mock_fetch, mock_config):
        mock_config.fbi_cde_api_key = "test-key"
        mock_fetch.return_value = {"results": []}

        result = await get_arrest_data(offense="unknown-offense")

        self.assertIn("No arrest data found", result)

    @patch(
        "mcp_govt_api.tools.bjs.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_search_crime_datasets_returns_results(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "count": 42,
                "results": [
                    {
                        "title": "National Prisoner Statistics",
                        "organization": {"title": "Bureau of Justice Statistics"},
                        "notes": "Annual data on prisoners under jurisdiction.",
                        "resources": [
                            {"format": "CSV", "url": "https://example.com/nps.csv"},
                            {"format": "JSON", "url": "https://example.com/nps.json"},
                        ],
                    }
                ],
            }
        }

        result = await search_crime_datasets("prisoner statistics")

        self.assertIn("National Prisoner Statistics", result)
        self.assertIn("Bureau of Justice Statistics", result)
        self.assertIn("42 total datasets", result)
        self.assertIn("CSV", result)
        self.assertIn("Data.gov", result)
        mock_fetch.assert_awaited_once()
        call_args = mock_fetch.call_args
        self.assertIn("prisoner statistics", call_args.kwargs["params"]["q"])

    @patch(
        "mcp_govt_api.tools.bjs.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_search_crime_datasets_no_results(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "count": 0,
                "results": [],
            }
        }

        result = await search_crime_datasets("xyznonexistent")

        self.assertIn("No crime/justice datasets found", result)

    @patch("mcp_govt_api.tools.bjs.config")
    async def test_missing_api_key_returns_error(self, mock_config):
        mock_config.fbi_cde_api_key = None

        result = await get_crime_estimates(state="CA")
        self.assertIn("FBI_CDE_API_KEY is not set", result)

        result = await get_arrest_data(offense="robbery")
        self.assertIn("FBI_CDE_API_KEY is not set", result)

    @patch("mcp_govt_api.tools.bjs.config")
    @patch(
        "mcp_govt_api.tools.bjs.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_fetch_error_handled_gracefully(self, mock_fetch, mock_config):
        mock_config.fbi_cde_api_key = "test-key"
        mock_fetch.side_effect = Exception("Connection timeout")

        result = await get_crime_estimates(state="CA")
        self.assertIn("Error fetching crime estimates", result)

        result = await get_arrest_data(offense="robbery")
        self.assertIn("Error fetching arrest data", result)

    @patch(
        "mcp_govt_api.tools.bjs.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_search_crime_datasets_error_handled(self, mock_fetch):
        mock_fetch.side_effect = Exception("Network error")

        result = await search_crime_datasets("test")

        self.assertIn("Error searching crime/justice datasets", result)


if __name__ == "__main__":
    unittest.main()
