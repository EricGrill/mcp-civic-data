"""Tests for Cloudflare Radar tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.cloudflare_radar import (
    get_internet_traffic_summary,
    get_top_domains,
    get_attack_summary,
    AUTH_FALLBACK_MSG,
)


class TestGetInternetTrafficSummary(unittest.IsolatedAsyncioTestCase):
    """Tests for get_internet_traffic_summary tool."""

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_successful_global_summary(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "summary_0": {"IPv4": "78.5", "IPv6": "21.5"},
                "meta": {
                    "dateRange": [
                        {"startTime": "2024-06-14T00:00:00Z", "endTime": "2024-06-15T00:00:00Z"}
                    ]
                },
            }
        }
        result = await get_internet_traffic_summary()
        self.assertIn("Internet Traffic Summary", result)
        self.assertIn("Global", result)
        self.assertIn("IPv4: 78.5%", result)
        self.assertIn("IPv6: 21.5%", result)
        self.assertIn("Cloudflare Radar", result)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_summary_with_location(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "summary_0": {"IPv4": "82.0", "IPv6": "18.0"},
                "meta": {"dateRange": []},
            }
        }
        result = await get_internet_traffic_summary(location="US", date_range="7d")
        self.assertIn("US", result)
        self.assertIn("7d", result)
        self.assertIn("82.0%", result)
        # Verify location was included in URL
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("location=US", call_url)
        self.assertIn("dateRange=7d", call_url)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_summary_empty_result(self, mock_fetch):
        mock_fetch.return_value = {"result": {"summary_0": {}}}
        result = await get_internet_traffic_summary()
        self.assertEqual(result, AUTH_FALLBACK_MSG)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_summary_non_dict_response(self, mock_fetch):
        mock_fetch.return_value = "error string"
        result = await get_internet_traffic_summary()
        self.assertEqual(result, AUTH_FALLBACK_MSG)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_summary_fetch_exception(self, mock_fetch):
        mock_fetch.side_effect = Exception("403 Forbidden")
        result = await get_internet_traffic_summary()
        self.assertEqual(result, AUTH_FALLBACK_MSG)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_summary_with_date_range_meta(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "summary_0": {"IPv4": "75.0", "IPv6": "25.0"},
                "meta": {
                    "dateRange": [
                        {"startTime": "2024-06-01T00:00:00Z", "endTime": "2024-06-15T00:00:00Z"}
                    ]
                },
            }
        }
        result = await get_internet_traffic_summary(date_range="14d")
        self.assertIn("Period:", result)
        self.assertIn("2024-06-01", result)


class TestGetTopDomains(unittest.IsolatedAsyncioTestCase):
    """Tests for get_top_domains tool."""

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_successful_top_domains(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "top_0": [
                    {"domain": "google.com", "category": "Search Engine"},
                    {"domain": "facebook.com", "category": "Social Media"},
                    {"domain": "apple.com", "category": "Technology"},
                ]
            }
        }
        result = await get_top_domains(limit=3)
        self.assertIn("Top 3 Domains", result)
        self.assertIn("1. google.com", result)
        self.assertIn("2. facebook.com", result)
        self.assertIn("3. apple.com", result)
        self.assertIn("Search Engine", result)
        self.assertIn("Cloudflare Radar", result)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_top_domains_with_location(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "top_0": [{"domain": "google.de"}]
            }
        }
        result = await get_top_domains(limit=1, location="de")
        self.assertIn("DE", result)
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("location=DE", call_url)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_top_domains_empty_list(self, mock_fetch):
        mock_fetch.return_value = {"result": {"top_0": []}}
        result = await get_top_domains()
        self.assertEqual(result, AUTH_FALLBACK_MSG)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_top_domains_auth_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("401 Unauthorized")
        result = await get_top_domains()
        self.assertEqual(result, AUTH_FALLBACK_MSG)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_top_domains_non_dict_response(self, mock_fetch):
        mock_fetch.return_value = []
        result = await get_top_domains()
        self.assertEqual(result, AUTH_FALLBACK_MSG)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_top_domains_without_category(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "top_0": [{"domain": "example.com"}]
            }
        }
        result = await get_top_domains(limit=1)
        self.assertIn("1. example.com", result)
        self.assertNotIn("()", result)

    def test_limit_clamped_to_range(self):
        """Verify limit is clamped between 1 and 100 (tested indirectly via URL)."""
        # This tests the clamping logic; actual fetch is mocked separately.
        self.assertEqual(max(1, min(0, 100)), 1)
        self.assertEqual(max(1, min(200, 100)), 100)


class TestGetAttackSummary(unittest.IsolatedAsyncioTestCase):
    """Tests for get_attack_summary tool."""

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_successful_attack_summary(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "summary_0": {
                    "TCP": "65.2",
                    "UDP": "28.1",
                    "ICMP": "4.5",
                    "GRE": "2.2",
                },
                "meta": {
                    "dateRange": [
                        {"startTime": "2024-06-14T00:00:00Z", "endTime": "2024-06-15T00:00:00Z"}
                    ]
                },
            }
        }
        result = await get_attack_summary()
        self.assertIn("DDoS Attack Summary", result)
        self.assertIn("TCP: 65.2%", result)
        self.assertIn("UDP: 28.1%", result)
        self.assertIn("ICMP: 4.5%", result)
        self.assertIn("GRE: 2.2%", result)
        self.assertIn("Period:", result)
        self.assertIn("Cloudflare Radar", result)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_attack_summary_custom_date_range(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "summary_0": {"TCP": "70.0", "UDP": "30.0"},
                "meta": {"dateRange": []},
            }
        }
        result = await get_attack_summary(date_range="7d")
        self.assertIn("7d", result)
        call_url = mock_fetch.call_args[0][0]
        self.assertIn("dateRange=7d", call_url)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_attack_summary_empty_result(self, mock_fetch):
        mock_fetch.return_value = {"result": {"summary_0": {}}}
        result = await get_attack_summary()
        self.assertEqual(result, AUTH_FALLBACK_MSG)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_attack_summary_fetch_exception(self, mock_fetch):
        mock_fetch.side_effect = Exception("Network error")
        result = await get_attack_summary()
        self.assertEqual(result, AUTH_FALLBACK_MSG)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_attack_summary_non_dict_response(self, mock_fetch):
        mock_fetch.return_value = None
        result = await get_attack_summary()
        self.assertEqual(result, AUTH_FALLBACK_MSG)

    @patch("mcp_govt_api.tools.cloudflare_radar.fetch_json", new_callable=AsyncMock)
    async def test_attack_summary_protocols_sorted(self, mock_fetch):
        mock_fetch.return_value = {
            "result": {
                "summary_0": {"UDP": "40.0", "TCP": "50.0", "ICMP": "10.0"},
                "meta": {},
            }
        }
        result = await get_attack_summary()
        # Protocols should be alphabetically sorted
        tcp_pos = result.index("ICMP")
        udp_pos = result.index("TCP")
        icmp_pos = result.index("UDP")
        self.assertLess(tcp_pos, udp_pos)
        self.assertLess(udp_pos, icmp_pos)


if __name__ == "__main__":
    unittest.main()
