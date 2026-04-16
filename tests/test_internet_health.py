"""Tests for Internet Health Report (IHR) monitoring tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.internet_health import (
    get_network_disconnections,
    get_network_delays,
    get_as_hegemony,
)


class TestGetNetworkDisconnections(unittest.IsolatedAsyncioTestCase):
    """Tests for get_network_disconnections tool."""

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_successful_disconnections(self, mock_fetch):
        mock_fetch.return_value = {
            "results": [
                {
                    "streamname": "AS15169",
                    "streamtype": "asn",
                    "starttime": "2024-06-15T10:00:00Z",
                    "endtime": "2024-06-15T10:30:00Z",
                    "avglevel": 7.5,
                    "nbdiscoprobes": 12,
                },
                {
                    "streamname": "AS13335",
                    "streamtype": "asn",
                    "starttime": "2024-06-15T09:00:00Z",
                    "endtime": "2024-06-15T09:15:00Z",
                    "avglevel": 5.2,
                    "nbdiscoprobes": 8,
                },
            ]
        }
        result = await get_network_disconnections()
        self.assertIn("AS15169", result)
        self.assertIn("AS13335", result)
        self.assertIn("Disconnection Events", result)
        self.assertIn("7.5", result)
        self.assertIn("12", result)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_no_disconnections(self, mock_fetch):
        mock_fetch.return_value = {"results": []}
        result = await get_network_disconnections()
        self.assertIn("No disconnection events found", result)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_filter_by_asn(self, mock_fetch):
        mock_fetch.return_value = {"results": []}
        await get_network_disconnections(asn=15169)
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("streamtype=asn", call_url)
        self.assertIn("streamname=15169", call_url)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_filter_by_country(self, mock_fetch):
        mock_fetch.return_value = {"results": []}
        await get_network_disconnections(country="US")
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("streamtype=country", call_url)
        self.assertIn("streamname=US", call_url)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_empty_results_with_filters(self, mock_fetch):
        mock_fetch.return_value = {"results": []}
        result = await get_network_disconnections(country="JP")
        self.assertIn("No disconnection events found", result)
        self.assertIn("country=JP", result)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_error_handling(self, mock_fetch):
        mock_fetch.side_effect = Exception("Connection timeout")
        result = await get_network_disconnections()
        self.assertIn("Error fetching disconnection events", result)
        self.assertIn("Connection timeout", result)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_custom_limit(self, mock_fetch):
        mock_fetch.return_value = {"results": []}
        await get_network_disconnections(limit=5)
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("limit=5", call_url)


class TestGetNetworkDelays(unittest.IsolatedAsyncioTestCase):
    """Tests for get_network_delays tool."""

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_successful_delays(self, mock_fetch):
        mock_fetch.return_value = {
            "results": [
                {
                    "startpoint_name": "AS15169",
                    "endpoint_name": "AS13335",
                    "median": 25.3,
                    "timebin": "2024-06-15T10:00:00Z",
                    "nbtracks": 150,
                    "nbprobes": 30,
                },
            ]
        }
        result = await get_network_delays()
        self.assertIn("AS15169", result)
        self.assertIn("AS13335", result)
        self.assertIn("25.3", result)
        self.assertIn("Network Delay", result)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_no_delays(self, mock_fetch):
        mock_fetch.return_value = {"results": []}
        result = await get_network_delays()
        self.assertIn("No network delay data found", result)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_filter_by_startpoint(self, mock_fetch):
        mock_fetch.return_value = {"results": []}
        await get_network_delays(startpoint="AS15169")
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("startpoint_name=AS15169", call_url)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_filter_by_endpoint(self, mock_fetch):
        mock_fetch.return_value = {"results": []}
        await get_network_delays(endpoint_name="AS13335")
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("endpoint_name=AS13335", call_url)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_empty_results_with_filters(self, mock_fetch):
        mock_fetch.return_value = {"results": []}
        result = await get_network_delays(startpoint="AS99999")
        self.assertIn("No network delay data found", result)
        self.assertIn("startpoint=AS99999", result)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_error_handling(self, mock_fetch):
        mock_fetch.side_effect = Exception("API unreachable")
        result = await get_network_delays()
        self.assertIn("Error fetching network delay data", result)
        self.assertIn("API unreachable", result)


class TestGetAsHegemony(unittest.IsolatedAsyncioTestCase):
    """Tests for get_as_hegemony tool."""

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_successful_hegemony(self, mock_fetch):
        mock_fetch.return_value = {
            "results": [
                {
                    "originasn": 13335,
                    "originasn_name": "Cloudflare",
                    "hege": 0.85,
                    "timebin": "2024-06-15T10:00:00Z",
                },
                {
                    "originasn": 32934,
                    "originasn_name": "Facebook",
                    "hege": 0.72,
                    "timebin": "2024-06-15T10:00:00Z",
                },
            ]
        }
        result = await get_as_hegemony(asn=15169)
        self.assertIn("AS13335", result)
        self.assertIn("Cloudflare", result)
        self.assertIn("0.85", result)
        self.assertIn("AS32934", result)
        self.assertIn("Hegemony", result)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_no_hegemony_data(self, mock_fetch):
        mock_fetch.return_value = {"results": []}
        result = await get_as_hegemony(asn=99999)
        self.assertIn("No AS hegemony data found", result)
        self.assertIn("99999", result)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_hegemony_without_origin_name(self, mock_fetch):
        mock_fetch.return_value = {
            "results": [
                {
                    "originasn": 64512,
                    "originasn_name": "",
                    "hege": 0.45,
                    "timebin": "2024-06-15T10:00:00Z",
                },
            ]
        }
        result = await get_as_hegemony(asn=15169)
        self.assertIn("AS64512", result)
        self.assertNotIn("()", result)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_asn_in_url(self, mock_fetch):
        mock_fetch.return_value = {"results": []}
        await get_as_hegemony(asn=15169, limit=10)
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("asn=15169", call_url)
        self.assertIn("limit=10", call_url)

    @patch("mcp_govt_api.tools.internet_health.fetch_json", new_callable=AsyncMock)
    async def test_error_handling(self, mock_fetch):
        mock_fetch.side_effect = Exception("Server error")
        result = await get_as_hegemony(asn=15169)
        self.assertIn("Error fetching AS hegemony data", result)
        self.assertIn("Server error", result)


if __name__ == "__main__":
    unittest.main()
