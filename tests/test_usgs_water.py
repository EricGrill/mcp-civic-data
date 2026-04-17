"""Tests for USGS Water Services tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.usgs_water import (
    get_water_conditions,
    get_water_site,
    query_usgs_water,
    _format_time_series,
)


class TestFormatTimeSeries(unittest.TestCase):
    """Tests for the _format_time_series helper."""

    def test_formats_streamflow_data(self):
        time_series = [
            {
                "sourceInfo": {
                    "siteName": "Potomac River at Little Falls",
                    "siteCode": [{"value": "01646500"}],
                },
                "variable": {
                    "variableName": "Streamflow",
                    "variableCode": [{"value": "00060"}],
                    "unit": {"unitCode": "ft3/s"},
                },
                "values": [{"value": [{"value": "5200", "dateTime": "2024-06-15T12:00:00Z"}]}],
            }
        ]
        lines = _format_time_series(time_series)
        self.assertEqual(len(lines), 1)
        self.assertIn("Potomac River", lines[0])
        self.assertIn("5200", lines[0])

    def test_empty_time_series(self):
        lines = _format_time_series([])
        self.assertEqual(len(lines), 0)

    def test_groups_by_site(self):
        time_series = [
            {
                "sourceInfo": {"siteName": "Site A", "siteCode": [{"value": "001"}]},
                "variable": {
                    "variableName": "Streamflow",
                    "variableCode": [{"value": "00060"}],
                    "unit": {"unitCode": "ft3/s"},
                },
                "values": [{"value": [{"value": "100", "dateTime": "2024-01-01T00:00:00Z"}]}],
            },
            {
                "sourceInfo": {"siteName": "Site A", "siteCode": [{"value": "001"}]},
                "variable": {
                    "variableName": "Gage height",
                    "variableCode": [{"value": "00065"}],
                    "unit": {"unitCode": "ft"},
                },
                "values": [{"value": [{"value": "3.5", "dateTime": "2024-01-01T00:00:00Z"}]}],
            },
        ]
        lines = _format_time_series(time_series)
        # Should be grouped into one site entry
        self.assertEqual(len(lines), 1)
        self.assertIn("100", lines[0])
        self.assertIn("3.5", lines[0])


class TestGetWaterConditions(unittest.IsolatedAsyncioTestCase):
    """Tests for get_water_conditions tool."""

    @patch("mcp_govt_api.tools.usgs_water.fetch_json", new_callable=AsyncMock)
    async def test_successful_conditions(self, mock_fetch):
        mock_fetch.return_value = {
            "value": {
                "timeSeries": [
                    {
                        "sourceInfo": {"siteName": "Test River", "siteCode": [{"value": "12345"}]},
                        "variable": {
                            "variableName": "Streamflow",
                            "variableCode": [{"value": "00060"}],
                            "unit": {"unitCode": "ft3/s"},
                        },
                        "values": [{"value": [{"value": "500", "dateTime": "2024-06-15T12:00:00Z"}]}],
                    }
                ]
            }
        }
        result = await get_water_conditions(state="WA")
        self.assertIn("Test River", result)
        self.assertIn("500", result)
        self.assertIn("USGS Real-Time Stream Conditions: WA", result)

    @patch("mcp_govt_api.tools.usgs_water.fetch_json", new_callable=AsyncMock)
    async def test_no_data_found(self, mock_fetch):
        mock_fetch.return_value = {"value": {"timeSeries": []}}
        result = await get_water_conditions(state="HI")
        self.assertIn("No active stream monitoring data", result)

    async def test_invalid_state_code(self):
        result = await get_water_conditions(state="INVALID")
        self.assertIn("Error", result)
        self.assertIn("2-letter code", result)

    @patch("mcp_govt_api.tools.usgs_water.fetch_json", new_callable=AsyncMock)
    async def test_limits_to_10_sites(self, mock_fetch):
        series = []
        for i in range(25):
            series.append({
                "sourceInfo": {"siteName": f"Site {i}", "siteCode": [{"value": f"{i:08d}"}]},
                "variable": {
                    "variableName": "Streamflow",
                    "variableCode": [{"value": "00060"}],
                    "unit": {"unitCode": "ft3/s"},
                },
                "values": [{"value": [{"value": str(100 + i), "dateTime": "2024-01-01T00:00:00Z"}]}],
            })
        mock_fetch.return_value = {"value": {"timeSeries": series}}
        result = await get_water_conditions(state="CA")
        # Should have at most 10 sites
        self.assertIn("Site 9", result)
        self.assertNotIn("Site 11", result)


class TestGetWaterSite(unittest.IsolatedAsyncioTestCase):
    """Tests for get_water_site tool."""

    @patch("mcp_govt_api.tools.usgs_water.fetch_json", new_callable=AsyncMock)
    async def test_successful_site(self, mock_fetch):
        mock_fetch.return_value = {
            "value": {
                "timeSeries": [
                    {
                        "sourceInfo": {
                            "siteName": "Potomac River at Little Falls",
                            "siteCode": [{"value": "01646500"}],
                        },
                        "variable": {
                            "variableName": "Streamflow",
                            "variableCode": [{"value": "00060"}],
                            "unit": {"unitCode": "ft3/s"},
                        },
                        "values": [{"value": [{"value": "4500", "dateTime": "2024-06-15T12:00:00Z"}]}],
                    }
                ]
            }
        }
        result = await get_water_site(site_number="01646500")
        self.assertIn("Potomac River", result)
        self.assertIn("4500", result)

    @patch("mcp_govt_api.tools.usgs_water.fetch_json", new_callable=AsyncMock)
    async def test_site_not_found(self, mock_fetch):
        mock_fetch.return_value = {"value": {"timeSeries": []}}
        result = await get_water_site(site_number="99999999")
        self.assertIn("No data found", result)

    async def test_empty_site_number(self):
        result = await get_water_site(site_number="")
        self.assertIn("Error", result)


class TestQueryUsgsWater(unittest.IsolatedAsyncioTestCase):
    """Tests for query_usgs_water tool."""

    @patch("mcp_govt_api.tools.usgs_water.fetch_json", new_callable=AsyncMock)
    async def test_raw_query(self, mock_fetch):
        mock_fetch.return_value = {"value": {"timeSeries": []}}
        result = await query_usgs_water(params={"stateCd": "OR", "parameterCd": "00060"})
        call_params = mock_fetch.call_args[1].get("params") or mock_fetch.call_args[0][1]
        self.assertEqual(call_params["format"], "json")


if __name__ == "__main__":
    unittest.main()
