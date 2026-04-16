import unittest
from unittest.mock import AsyncMock, patch
from urllib.parse import unquote

from mcp_govt_api.tools.railway import (
    find_railway_stations,
    get_railway_lines,
    search_railway_stations_by_name,
)


class FindRailwayStationsTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_results(self):
        mock_response = {
            "elements": [
                {
                    "type": "node",
                    "id": 123456,
                    "lat": 51.5308,
                    "lon": -0.1238,
                    "tags": {
                        "name": "King's Cross",
                        "operator": "Network Rail",
                        "network": "National Rail",
                        "platforms": "12",
                        "wheelchair": "yes",
                        "wikidata": "Q203163",
                    },
                },
                {
                    "type": "node",
                    "id": 789012,
                    "lat": 51.5282,
                    "lon": -0.1337,
                    "tags": {
                        "name": "Euston",
                        "operator": "Network Rail",
                        "network": "National Rail",
                    },
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await find_railway_stations(lat=51.5074, lon=-0.1278)

        self.assertIn("King's Cross", result)
        self.assertIn("Network Rail", result)
        self.assertIn("National Rail", result)
        self.assertIn("Platforms: 12", result)
        self.assertIn("Wheelchair access: yes", result)
        self.assertIn("Wikidata: Q203163", result)
        self.assertIn("Euston", result)
        self.assertIn("Found 2 station(s)", result)

    async def test_empty_results(self):
        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(return_value={"elements": []}),
        ):
            result = await find_railway_stations(lat=0.0, lon=0.0)

        self.assertIn("No railway stations found", result)

    async def test_handles_error(self):
        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(side_effect=Exception("Connection timeout")),
        ):
            result = await find_railway_stations(lat=51.5074, lon=-0.1278)

        self.assertIn("Error searching for railway stations", result)
        self.assertIn("Connection timeout", result)

    async def test_limit_capped_at_50(self):
        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(return_value={"elements": []}),
        ) as mock_fetch:
            await find_railway_stations(lat=51.5074, lon=-0.1278, limit=100)

        call_url = unquote(mock_fetch.call_args[0][0])
        self.assertIn("out body 50", call_url)

    async def test_custom_radius(self):
        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(return_value={"elements": []}),
        ) as mock_fetch:
            await find_railway_stations(lat=51.5074, lon=-0.1278, radius=2000)

        call_url = unquote(mock_fetch.call_args[0][0])
        self.assertIn("around:2000", call_url)

    async def test_station_missing_optional_tags(self):
        mock_response = {
            "elements": [
                {
                    "type": "node",
                    "id": 111,
                    "lat": 40.75,
                    "lon": -73.99,
                    "tags": {
                        "name": "Minimal Station",
                    },
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await find_railway_stations(lat=40.75, lon=-73.99)

        self.assertIn("Minimal Station", result)
        self.assertIn("Unknown operator", result)


class GetRailwayLinesTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_results(self):
        mock_response = {
            "elements": [
                {
                    "type": "way",
                    "id": 456789,
                    "tags": {
                        "name": "East Coast Main Line",
                        "operator": "Network Rail",
                        "usage": "main",
                        "electrified": "contact_line",
                        "gauge": "1435",
                        "maxspeed": "200",
                    },
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await get_railway_lines(lat=51.5074, lon=-0.1278)

        self.assertIn("East Coast Main Line", result)
        self.assertIn("Network Rail", result)
        self.assertIn("Usage: main", result)
        self.assertIn("Electrified: contact_line", result)
        self.assertIn("Gauge: 1435", result)
        self.assertIn("Max speed: 200", result)
        self.assertIn("Found 1 line(s)", result)

    async def test_empty_results(self):
        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(return_value={"elements": []}),
        ):
            result = await get_railway_lines(lat=0.0, lon=0.0)

        self.assertIn("No railway lines found", result)

    async def test_handles_error(self):
        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(side_effect=Exception("Server error")),
        ):
            result = await get_railway_lines(lat=48.8566, lon=2.3522)

        self.assertIn("Error searching for railway lines", result)
        self.assertIn("Server error", result)

    async def test_default_radius_is_10000(self):
        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(return_value={"elements": []}),
        ) as mock_fetch:
            await get_railway_lines(lat=48.8566, lon=2.3522)

        call_url = unquote(mock_fetch.call_args[0][0])
        self.assertIn("around:10000", call_url)

    async def test_line_with_service_tag(self):
        mock_response = {
            "elements": [
                {
                    "type": "way",
                    "id": 999,
                    "tags": {
                        "name": "Siding Track",
                        "operator": "DB Netz",
                        "service": "siding",
                    },
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await get_railway_lines(lat=52.52, lon=13.405)

        self.assertIn("Service: siding", result)


class SearchRailwayStationsByNameTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_formatted_results(self):
        mock_response = {
            "elements": [
                {
                    "type": "node",
                    "id": 333,
                    "lat": 40.7505,
                    "lon": -73.9935,
                    "tags": {
                        "name": "Penn Station",
                        "operator": "Amtrak",
                        "network": "Amtrak",
                    },
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await search_railway_stations_by_name(name="Penn Station")

        self.assertIn("Penn Station", result)
        self.assertIn("Amtrak", result)
        self.assertIn('matching "Penn Station"', result)
        self.assertIn("Found 1 result(s)", result)

    async def test_search_with_country_code(self):
        mock_response = {
            "elements": [
                {
                    "type": "node",
                    "id": 444,
                    "lat": 52.525,
                    "lon": 13.369,
                    "tags": {
                        "name": "Berlin Hauptbahnhof",
                        "operator": "DB Station&Service",
                    },
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(return_value=mock_response),
        ) as mock_fetch:
            result = await search_railway_stations_by_name(
                name="Berlin", country_code="DE"
            )

        self.assertIn("Berlin Hauptbahnhof", result)
        self.assertIn("in DE", result)
        call_url = unquote(mock_fetch.call_args[0][0])
        self.assertIn("ISO3166-1", call_url)
        self.assertIn("DE", call_url)

    async def test_empty_results(self):
        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(return_value={"elements": []}),
        ):
            result = await search_railway_stations_by_name(name="Nonexistent XYZ")

        self.assertIn("No railway stations matching", result)
        self.assertIn("Nonexistent XYZ", result)

    async def test_empty_results_with_country(self):
        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(return_value={"elements": []}),
        ):
            result = await search_railway_stations_by_name(
                name="Fake Station", country_code="GB"
            )

        self.assertIn("No railway stations matching", result)
        self.assertIn("in GB", result)

    async def test_handles_error(self):
        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(side_effect=Exception("API unavailable")),
        ):
            result = await search_railway_stations_by_name(name="London")

        self.assertIn("Error searching for railway stations by name", result)
        self.assertIn("API unavailable", result)

    async def test_no_country_code_omits_area_filter(self):
        with patch(
            "mcp_govt_api.tools.railway.fetch_json",
            new=AsyncMock(return_value={"elements": []}),
        ) as mock_fetch:
            await search_railway_stations_by_name(name="Central")

        call_url = unquote(mock_fetch.call_args[0][0])
        self.assertNotIn("ISO3166-1", call_url)
        self.assertNotIn("searchArea", call_url)


if __name__ == "__main__":
    unittest.main()
