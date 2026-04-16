import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.usda import (
    get_crop_data,
    get_food_details,
    search_usda_foods,
)


class SearchUsdaFoodsTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_error_when_key_missing(self):
        with patch("mcp_govt_api.tools.usda.config") as mock_config:
            mock_config.usda_api_key = None
            result = await search_usda_foods(query="apple")

        self.assertIn("USDA_API_KEY", result)

    async def test_returns_formatted_search_results(self):
        api_response = {
            "totalHits": 25,
            "foods": [
                {
                    "fdcId": 171688,
                    "description": "Apples, raw, with skin",
                    "dataType": "SR Legacy",
                    "brandOwner": "",
                    "foodNutrients": [
                        {"nutrientName": "Energy", "value": 52, "unitName": "KCAL"},
                        {"nutrientName": "Protein", "value": 0.26, "unitName": "G"},
                        {
                            "nutrientName": "Carbohydrate, by difference",
                            "value": 13.81,
                            "unitName": "G",
                        },
                    ],
                }
            ],
        }
        with patch("mcp_govt_api.tools.usda.config") as mock_config, patch(
            "mcp_govt_api.tools.usda.fetch_json",
            new=AsyncMock(return_value=api_response),
        ):
            mock_config.usda_api_key = "test-key"
            result = await search_usda_foods(query="apple", limit=10)

        self.assertIn("FoodData Central", result)
        self.assertIn("apple", result)
        self.assertIn("Apples, raw, with skin", result)
        self.assertIn("171688", result)
        self.assertIn("Energy", result)

    async def test_empty_results(self):
        api_response = {"totalHits": 0, "foods": []}
        with patch("mcp_govt_api.tools.usda.config") as mock_config, patch(
            "mcp_govt_api.tools.usda.fetch_json",
            new=AsyncMock(return_value=api_response),
        ):
            mock_config.usda_api_key = "test-key"
            result = await search_usda_foods(query="xyzzyx")

        self.assertIn("No foods found", result)

    async def test_api_error_handled(self):
        with patch("mcp_govt_api.tools.usda.config") as mock_config, patch(
            "mcp_govt_api.tools.usda.fetch_json",
            new=AsyncMock(side_effect=Exception("timeout")),
        ):
            mock_config.usda_api_key = "test-key"
            result = await search_usda_foods(query="apple")

        self.assertIn("Error", result)


class GetFoodDetailsTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_error_when_key_missing(self):
        with patch("mcp_govt_api.tools.usda.config") as mock_config:
            mock_config.usda_api_key = None
            result = await get_food_details(fdc_id=171688)

        self.assertIn("USDA_API_KEY", result)

    async def test_returns_formatted_food_details(self):
        api_response = {
            "fdcId": 171688,
            "description": "Apples, raw, with skin",
            "dataType": "SR Legacy",
            "brandOwner": "",
            "servingSize": 182,
            "servingSizeUnit": "g",
            "ingredients": "",
            "foodNutrients": [
                {
                    "nutrient": {"name": "Energy", "unitName": "KCAL"},
                    "amount": 52,
                },
                {
                    "nutrient": {"name": "Protein", "unitName": "G"},
                    "amount": 0.26,
                },
            ],
        }
        with patch("mcp_govt_api.tools.usda.config") as mock_config, patch(
            "mcp_govt_api.tools.usda.fetch_json",
            new=AsyncMock(return_value=api_response),
        ):
            mock_config.usda_api_key = "test-key"
            result = await get_food_details(fdc_id=171688)

        self.assertIn("Apples, raw, with skin", result)
        self.assertIn("Energy", result)
        self.assertIn("52", result)
        self.assertIn("Protein", result)
        self.assertIn("Serving Size", result)

    async def test_api_error_handled(self):
        with patch("mcp_govt_api.tools.usda.config") as mock_config, patch(
            "mcp_govt_api.tools.usda.fetch_json",
            new=AsyncMock(side_effect=Exception("not found")),
        ):
            mock_config.usda_api_key = "test-key"
            result = await get_food_details(fdc_id=999999)

        self.assertIn("Error", result)


class GetCropDataTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_error_when_key_missing(self):
        with patch("mcp_govt_api.tools.usda.config") as mock_config:
            mock_config.usda_api_key = None
            result = await get_crop_data(commodity="CORN")

        self.assertIn("USDA_API_KEY", result)

    async def test_returns_formatted_crop_data(self):
        api_response = {
            "data": [
                {
                    "commodity_desc": "CORN",
                    "year": "2023",
                    "state_alpha": "IA",
                    "state_name": "IOWA",
                    "statisticcat_desc": "PRODUCTION",
                    "short_desc": "CORN, GRAIN - PRODUCTION, MEASURED IN BU",
                    "Value": "2,382,400,000",
                    "unit_desc": "BU",
                }
            ]
        }
        with patch("mcp_govt_api.tools.usda.config") as mock_config, patch(
            "mcp_govt_api.tools.usda.fetch_json",
            new=AsyncMock(return_value=api_response),
        ):
            mock_config.usda_api_key = "test-key"
            result = await get_crop_data(commodity="CORN", state="IA", year="2023")

        self.assertIn("CORN", result)
        self.assertIn("2023", result)
        self.assertIn("IA", result)
        self.assertIn("PRODUCTION", result)
        self.assertIn("BU", result)

    async def test_empty_results(self):
        api_response = {"data": []}
        with patch("mcp_govt_api.tools.usda.config") as mock_config, patch(
            "mcp_govt_api.tools.usda.fetch_json",
            new=AsyncMock(return_value=api_response),
        ):
            mock_config.usda_api_key = "test-key"
            result = await get_crop_data(commodity="XYZZYX")

        self.assertIn("No crop data found", result)

    async def test_national_data_no_state(self):
        api_response = {
            "data": [
                {
                    "commodity_desc": "SOYBEANS",
                    "year": "2023",
                    "state_alpha": "US",
                    "state_name": "US TOTAL",
                    "statisticcat_desc": "PRODUCTION",
                    "short_desc": "SOYBEANS - PRODUCTION, MEASURED IN BU",
                    "Value": "4,165,000,000",
                    "unit_desc": "BU",
                }
            ]
        }
        with patch("mcp_govt_api.tools.usda.config") as mock_config, patch(
            "mcp_govt_api.tools.usda.fetch_json",
            new=AsyncMock(return_value=api_response),
        ):
            mock_config.usda_api_key = "test-key"
            result = await get_crop_data(commodity="SOYBEANS", year="2023")

        self.assertIn("SOYBEANS", result)
        self.assertIn("US", result)

    async def test_api_error_handled(self):
        with patch("mcp_govt_api.tools.usda.config") as mock_config, patch(
            "mcp_govt_api.tools.usda.fetch_json",
            new=AsyncMock(side_effect=Exception("timeout")),
        ):
            mock_config.usda_api_key = "test-key"
            result = await get_crop_data(commodity="CORN")

        self.assertIn("Error", result)


if __name__ == "__main__":
    unittest.main()
