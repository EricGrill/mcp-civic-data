import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.bea import (
    get_bea_gdp_by_industry,
    get_bea_regional_data,
    search_bea_datasets,
)


class BeaToolTests(unittest.IsolatedAsyncioTestCase):
    @patch("mcp_govt_api.tools.bea.config")
    @patch(
        "mcp_govt_api.tools.bea.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_bea_regional_data_returns_results(self, mock_fetch, mock_config):
        mock_config.bea_api_key = "test-key"
        mock_fetch.return_value = {
            "BEAAPI": {
                "Results": {
                    "Data": [
                        {
                            "GeoName": "California",
                            "TimePeriod": "2022",
                            "DataValue": "3,598,103",
                            "Description": "Real GDP (millions of chained 2017 dollars)",
                            "UNIT_MULT_DESC": "Millions of dollars",
                        }
                    ]
                }
            }
        }

        result = await get_bea_regional_data(table="CAGDP1", state="CA", year="2022")

        self.assertIn("California", result)
        self.assertIn("2022", result)
        self.assertIn("3,598,103", result)
        self.assertIn("BEA Regional Data", result)
        mock_fetch.assert_awaited_once()
        call_args = mock_fetch.call_args
        self.assertEqual(call_args.kwargs["params"]["TableName"], "CAGDP1")
        self.assertEqual(call_args.kwargs["params"]["GeoFips"], "06000")

    @patch("mcp_govt_api.tools.bea.config")
    @patch(
        "mcp_govt_api.tools.bea.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_bea_regional_data_all_states(self, mock_fetch, mock_config):
        mock_config.bea_api_key = "test-key"
        mock_fetch.return_value = {
            "BEAAPI": {
                "Results": {
                    "Data": [
                        {
                            "GeoName": "United States",
                            "TimePeriod": "2022",
                            "DataValue": "25,462,700",
                            "Description": "GDP",
                        }
                    ]
                }
            }
        }

        result = await get_bea_regional_data()

        self.assertIn("All States", result)
        self.assertIn("United States", result)
        mock_fetch.assert_awaited_once()
        call_args = mock_fetch.call_args
        self.assertEqual(call_args.kwargs["params"]["GeoFips"], "STATE")

    @patch("mcp_govt_api.tools.bea.config")
    @patch(
        "mcp_govt_api.tools.bea.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_bea_regional_data_no_results(self, mock_fetch, mock_config):
        mock_config.bea_api_key = "test-key"
        mock_fetch.return_value = {"BEAAPI": {"Results": {"Data": []}}}

        result = await get_bea_regional_data(state="ZZ")

        self.assertIn("No BEA regional data found", result)

    @patch("mcp_govt_api.tools.bea.config")
    @patch(
        "mcp_govt_api.tools.bea.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_bea_regional_data_api_error(self, mock_fetch, mock_config):
        mock_config.bea_api_key = "test-key"
        mock_fetch.return_value = {
            "BEAAPI": {
                "Results": {
                    "Error": {
                        "APIErrorDescription": "Invalid table name"
                    }
                }
            }
        }

        result = await get_bea_regional_data(table="BADTABLE")

        self.assertIn("BEA API error", result)
        self.assertIn("Invalid table name", result)

    @patch("mcp_govt_api.tools.bea.config")
    @patch(
        "mcp_govt_api.tools.bea.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_bea_gdp_by_industry_returns_results(self, mock_fetch, mock_config):
        mock_config.bea_api_key = "test-key"
        mock_fetch.return_value = {
            "BEAAPI": {
                "Results": {
                    "Data": [
                        {
                            "IndustryDescription": "All industries",
                            "Year": "2022",
                            "DataValue": "25,462.7",
                            "FreqDesc": "Annual",
                        }
                    ]
                }
            }
        }

        result = await get_bea_gdp_by_industry(year="2022")

        self.assertIn("All industries", result)
        self.assertIn("2022", result)
        self.assertIn("25,462.7", result)
        self.assertIn("BEA GDP by Industry", result)
        mock_fetch.assert_awaited_once()
        call_args = mock_fetch.call_args
        self.assertEqual(call_args.kwargs["params"]["DataSetName"], "GDPbyIndustry")

    @patch("mcp_govt_api.tools.bea.config")
    @patch(
        "mcp_govt_api.tools.bea.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_get_bea_gdp_by_industry_no_results(self, mock_fetch, mock_config):
        mock_config.bea_api_key = "test-key"
        mock_fetch.return_value = {"BEAAPI": {"Results": {"Data": []}}}

        result = await get_bea_gdp_by_industry(industry="99")

        self.assertIn("No BEA GDP by industry data found", result)

    @patch("mcp_govt_api.tools.bea.config")
    @patch(
        "mcp_govt_api.tools.bea.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_search_bea_datasets_returns_results(self, mock_fetch, mock_config):
        mock_config.bea_api_key = "test-key"
        mock_fetch.return_value = {
            "BEAAPI": {
                "Results": {
                    "Dataset": [
                        {
                            "DatasetName": "Regional",
                            "DatasetDescription": "Regional economic data",
                        },
                        {
                            "DatasetName": "NIPA",
                            "DatasetDescription": "National Income and Product Accounts",
                        },
                    ]
                }
            }
        }

        result = await search_bea_datasets()

        self.assertIn("Available BEA Datasets", result)
        self.assertIn("Regional", result)
        self.assertIn("NIPA", result)
        self.assertIn("National Income and Product Accounts", result)
        mock_fetch.assert_awaited_once()

    @patch("mcp_govt_api.tools.bea.config")
    @patch(
        "mcp_govt_api.tools.bea.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_search_bea_datasets_no_results(self, mock_fetch, mock_config):
        mock_config.bea_api_key = "test-key"
        mock_fetch.return_value = {"BEAAPI": {"Results": {"Dataset": []}}}

        result = await search_bea_datasets()

        self.assertIn("No BEA datasets found", result)

    @patch("mcp_govt_api.tools.bea.config")
    async def test_missing_api_key_returns_error(self, mock_config):
        mock_config.bea_api_key = None

        result = await get_bea_regional_data()
        self.assertIn("BEA_API_KEY", result)

        result = await get_bea_gdp_by_industry()
        self.assertIn("BEA_API_KEY", result)

        result = await search_bea_datasets()
        self.assertIn("BEA_API_KEY", result)

    @patch("mcp_govt_api.tools.bea.config")
    @patch(
        "mcp_govt_api.tools.bea.fetch_json",
        new_callable=AsyncMock,
    )
    async def test_fetch_error_handled_gracefully(self, mock_fetch, mock_config):
        mock_config.bea_api_key = "test-key"
        mock_fetch.side_effect = Exception("Connection timeout")

        result = await get_bea_regional_data()
        self.assertIn("Error fetching BEA regional data", result)

        result = await get_bea_gdp_by_industry()
        self.assertIn("Error fetching BEA GDP by industry", result)

        result = await search_bea_datasets()
        self.assertIn("Error fetching BEA datasets", result)


if __name__ == "__main__":
    unittest.main()
