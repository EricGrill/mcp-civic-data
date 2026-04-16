"""Tests for NHTSA traffic safety tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.nhtsa import (
    decode_vin,
    get_vehicle_complaints,
    search_vehicle_recalls,
)


class TestSearchVehicleRecalls(unittest.IsolatedAsyncioTestCase):
    async def test_returns_recalls(self):
        mock_data = {
            "results": [
                {
                    "NHTSACampaignNumber": "20V123000",
                    "Manufacturer": "Toyota Motor",
                    "Component": "AIR BAGS",
                    "Summary": "Air bag may not deploy properly.",
                    "Consequence": "Increased risk of injury.",
                    "Remedy": "Dealers will replace the air bag module.",
                    "ReportReceivedDate": "03/15/2020",
                },
                {
                    "NHTSACampaignNumber": "20V456000",
                    "Manufacturer": "Toyota Motor",
                    "Component": "FUEL SYSTEM",
                    "Summary": "Fuel pump may fail.",
                    "Consequence": "Engine stall while driving.",
                    "Remedy": "Dealers will replace the fuel pump.",
                    "ReportReceivedDate": "06/01/2020",
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.nhtsa.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ) as mock_fetch:
            result = await search_vehicle_recalls(make="Toyota", model="Camry", year="2020")

        mock_fetch.assert_awaited_once()
        self.assertIn("20V123000", result)
        self.assertIn("AIR BAGS", result)
        self.assertIn("20V456000", result)
        self.assertIn("FUEL SYSTEM", result)
        self.assertIn("Total recalls found: 2", result)
        self.assertIn("NHTSA Recalls API", result)

    async def test_no_filters_returns_message(self):
        result = await search_vehicle_recalls()
        self.assertIn("Please provide at least one filter", result)

    async def test_no_results(self):
        with patch(
            "mcp_govt_api.tools.nhtsa.fetch_json",
            new=AsyncMock(return_value={"results": []}),
        ):
            result = await search_vehicle_recalls(make="FakeMake")

        self.assertIn("No recalls found", result)

    async def test_api_error(self):
        with patch(
            "mcp_govt_api.tools.nhtsa.fetch_json",
            new=AsyncMock(side_effect=Exception("Connection refused")),
        ):
            result = await search_vehicle_recalls(make="Toyota")

        self.assertIn("Error fetching recall data", result)

    async def test_limit_applied(self):
        mock_data = {
            "results": [
                {"NHTSACampaignNumber": f"20V{i:03d}000", "Component": f"Part {i}"}
                for i in range(20)
            ]
        }

        with patch(
            "mcp_govt_api.tools.nhtsa.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await search_vehicle_recalls(make="Toyota", limit=5)

        self.assertIn("5 of 20 total", result)


class TestGetVehicleComplaints(unittest.IsolatedAsyncioTestCase):
    async def test_returns_complaints(self):
        mock_data = {
            "results": [
                {
                    "odiNumber": "11234567",
                    "components": "ENGINE",
                    "summary": "Engine stalls at highway speeds.",
                    "crash": "No",
                    "fire": "No",
                    "injuries": 0,
                    "deaths": 0,
                    "dateComplaintFiled": "01/10/2020",
                    "dateOfIncident": "12/25/2019",
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.nhtsa.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ) as mock_fetch:
            result = await get_vehicle_complaints(make="Toyota", model="Camry", year="2020")

        mock_fetch.assert_awaited_once()
        self.assertIn("11234567", result)
        self.assertIn("ENGINE", result)
        self.assertIn("Engine stalls at highway speeds", result)
        self.assertIn("NHTSA Complaints API", result)

    async def test_no_filters_returns_message(self):
        result = await get_vehicle_complaints()
        self.assertIn("Please provide at least one filter", result)

    async def test_no_results(self):
        with patch(
            "mcp_govt_api.tools.nhtsa.fetch_json",
            new=AsyncMock(return_value={"results": []}),
        ):
            result = await get_vehicle_complaints(make="FakeMake")

        self.assertIn("No complaints found", result)

    async def test_api_error(self):
        with patch(
            "mcp_govt_api.tools.nhtsa.fetch_json",
            new=AsyncMock(side_effect=Exception("Timeout")),
        ):
            result = await get_vehicle_complaints(make="Ford")

        self.assertIn("Error fetching complaint data", result)


class TestDecodeVin(unittest.IsolatedAsyncioTestCase):
    async def test_decodes_vin(self):
        mock_data = {
            "Results": [
                {
                    "Make": "Honda",
                    "Model": "Accord",
                    "ModelYear": "2003",
                    "BodyClass": "Sedan/Saloon",
                    "VehicleType": "PASSENGER CAR",
                    "DriveType": "FWD",
                    "EngineCylinders": "4",
                    "DisplacementL": "2.4",
                    "FuelTypePrimary": "Gasoline",
                    "Manufacturer": "HONDA MOTOR CO., LTD",
                    "ErrorCode": "0",
                    "ErrorText": "",
                }
            ]
        }

        with patch(
            "mcp_govt_api.tools.nhtsa.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ) as mock_fetch:
            result = await decode_vin("1HGCM82633A004352")

        mock_fetch.assert_awaited_once()
        self.assertIn("1HGCM82633A004352", result)
        self.assertIn("Honda", result)
        self.assertIn("Accord", result)
        self.assertIn("2003", result)
        self.assertIn("Sedan/Saloon", result)
        self.assertIn("NHTSA vPIC", result)

    async def test_empty_vin(self):
        result = await decode_vin("")
        self.assertIn("Please provide a VIN", result)

    async def test_invalid_length(self):
        result = await decode_vin("ABC123")
        self.assertIn("Invalid VIN length", result)
        self.assertIn("got 6", result)

    async def test_api_error(self):
        with patch(
            "mcp_govt_api.tools.nhtsa.fetch_json",
            new=AsyncMock(side_effect=Exception("Server error")),
        ):
            result = await decode_vin("1HGCM82633A004352")

        self.assertIn("Error decoding VIN", result)

    async def test_no_results(self):
        with patch(
            "mcp_govt_api.tools.nhtsa.fetch_json",
            new=AsyncMock(return_value={"Results": []}),
        ):
            result = await decode_vin("1HGCM82633A004352")

        self.assertIn("No results returned", result)

    async def test_vin_error_code(self):
        mock_data = {
            "Results": [
                {
                    "ErrorCode": "5",
                    "ErrorText": "VIN has an invalid check digit.",
                }
            ]
        }

        with patch(
            "mcp_govt_api.tools.nhtsa.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await decode_vin("1HGCM82633A004353")

        self.assertIn("VIN decode error", result)


if __name__ == "__main__":
    unittest.main()
