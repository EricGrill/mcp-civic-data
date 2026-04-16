import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.eia import (
    get_electricity_data,
    get_energy_overview,
    get_petroleum_prices,
)


class ElectricityDataTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_error_when_key_missing(self):
        with patch("mcp_govt_api.tools.eia.config") as mock_config:
            mock_config.eia_api_key = None
            result = await get_electricity_data(state="CA")

        self.assertIn("EIA_API_KEY", result)

    async def test_returns_formatted_electricity_data(self):
        api_response = {
            "response": {
                "total": 100,
                "data": [
                    {
                        "period": "2024-01",
                        "stateid": "CA",
                        "sectorName": "Residential",
                        "revenue": 5000,
                        "sales": 25000,
                        "price": 25.5,
                        "customers": 14000000,
                    }
                ],
            }
        }
        with patch("mcp_govt_api.tools.eia.config") as mock_config, patch(
            "mcp_govt_api.tools.eia.fetch_json",
            new=AsyncMock(return_value=api_response),
        ):
            mock_config.eia_api_key = "test-key"
            result = await get_electricity_data(state="CA", frequency="monthly")

        self.assertIn("Electricity Retail Sales", result)
        self.assertIn("CA", result)
        self.assertIn("2024-01", result)
        self.assertIn("25.5", result)
        self.assertIn("Residential", result)

    async def test_empty_state_returns_national(self):
        api_response = {"response": {"total": 0, "data": []}}
        with patch("mcp_govt_api.tools.eia.config") as mock_config, patch(
            "mcp_govt_api.tools.eia.fetch_json",
            new=AsyncMock(return_value=api_response),
        ):
            mock_config.eia_api_key = "test-key"
            result = await get_electricity_data(state="")

        self.assertIn("US", result)


class PetroleumPricesTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_error_when_key_missing(self):
        with patch("mcp_govt_api.tools.eia.config") as mock_config:
            mock_config.eia_api_key = None
            result = await get_petroleum_prices()

        self.assertIn("EIA_API_KEY", result)

    async def test_returns_formatted_petroleum_data(self):
        api_response = {
            "response": {
                "total": 50,
                "data": [
                    {
                        "period": "2024-01-15",
                        "value": 3.245,
                        "series-description": "Regular Gasoline",
                        "areaName": "U.S.",
                        "units": "$/gal",
                    }
                ],
            }
        }
        with patch("mcp_govt_api.tools.eia.config") as mock_config, patch(
            "mcp_govt_api.tools.eia.fetch_json",
            new=AsyncMock(return_value=api_response),
        ):
            mock_config.eia_api_key = "test-key"
            result = await get_petroleum_prices(product="gasoline")

        self.assertIn("Petroleum Prices", result)
        self.assertIn("Gasoline", result)
        self.assertIn("$3.245", result)
        self.assertIn("2024-01-15", result)

    async def test_diesel_product_accepted(self):
        api_response = {"response": {"total": 0, "data": []}}
        with patch("mcp_govt_api.tools.eia.config") as mock_config, patch(
            "mcp_govt_api.tools.eia.fetch_json",
            new=AsyncMock(return_value=api_response),
        ):
            mock_config.eia_api_key = "test-key"
            result = await get_petroleum_prices(product="diesel")

        self.assertIn("diesel", result.lower())


class EnergyOverviewTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_error_when_key_missing(self):
        with patch("mcp_govt_api.tools.eia.config") as mock_config:
            mock_config.eia_api_key = None
            result = await get_energy_overview()

        self.assertIn("EIA_API_KEY", result)

    async def test_returns_category_routes(self):
        api_response = {
            "response": {
                "name": "Electricity",
                "description": "EIA electricity data",
                "routes": [
                    {
                        "id": "retail-sales",
                        "name": "Retail Sales",
                        "description": "Retail sales of electricity",
                    },
                    {
                        "id": "electric-power-operational-data",
                        "name": "Electric Power Operations",
                        "description": "Monthly and annual data",
                    },
                ],
            }
        }
        with patch("mcp_govt_api.tools.eia.config") as mock_config, patch(
            "mcp_govt_api.tools.eia.fetch_json",
            new=AsyncMock(return_value=api_response),
        ):
            mock_config.eia_api_key = "test-key"
            result = await get_energy_overview(category="electricity")

        self.assertIn("Electricity", result)
        self.assertIn("retail-sales", result)
        self.assertIn("Retail Sales", result)
        self.assertIn("Electric Power Operations", result)

    async def test_empty_category_fetches_root(self):
        api_response = {
            "response": {
                "name": "EIA Data",
                "description": "",
                "routes": [
                    {"id": "electricity", "name": "Electricity", "description": ""},
                    {"id": "petroleum", "name": "Petroleum", "description": ""},
                ],
            }
        }
        with patch("mcp_govt_api.tools.eia.config") as mock_config, patch(
            "mcp_govt_api.tools.eia.fetch_json",
            new=AsyncMock(return_value=api_response),
        ) as mock_fetch:
            mock_config.eia_api_key = "test-key"
            result = await get_energy_overview(category="")

        # Verify the root URL was called (no category path segment)
        call_url = mock_fetch.call_args[0][0]
        self.assertTrue(call_url.endswith("/v2"))
        self.assertIn("Electricity", result)
        self.assertIn("Petroleum", result)


if __name__ == "__main__":
    unittest.main()
