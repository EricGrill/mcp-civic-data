"""Tests for CISA cybersecurity tools."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_govt_api.tools.cisa import (
    search_known_exploited_vulnerabilities,
    get_recent_cisa_alerts,
    get_cisa_bulletins,
    query_cisa_kev,
)


class TestSearchKnownExploitedVulnerabilities(unittest.IsolatedAsyncioTestCase):
    """Tests for search_known_exploited_vulnerabilities tool."""

    @patch("mcp_govt_api.tools.cisa.fetch_json", new_callable=AsyncMock)
    async def test_search_by_vendor(self, mock_fetch):
        mock_fetch.return_value = {
            "vulnerabilities": [
                {
                    "cveID": "CVE-2021-44228",
                    "vendorProject": "Apache",
                    "product": "Log4j",
                    "vulnerabilityName": "Apache Log4j Remote Code Execution",
                    "dateAdded": "2021-12-10",
                    "dueDate": "2021-12-24",
                    "requiredAction": "Apply updates per vendor instructions.",
                }
            ]
        }
        result = await search_known_exploited_vulnerabilities(vendor="Apache")
        self.assertIn("CVE-2021-44228", result)
        self.assertIn("Log4j", result)
        self.assertIn("Apache", result)

    @patch("mcp_govt_api.tools.cisa.fetch_json", new_callable=AsyncMock)
    async def test_search_by_cve_id(self, mock_fetch):
        mock_fetch.return_value = {
            "vulnerabilities": [
                {
                    "cveID": "CVE-2021-44228",
                    "vendorProject": "Apache",
                    "product": "Log4j",
                    "vulnerabilityName": "Apache Log4j RCE",
                    "dateAdded": "2021-12-10",
                    "dueDate": "2021-12-24",
                    "requiredAction": "Apply updates.",
                }
            ]
        }
        result = await search_known_exploited_vulnerabilities(cve_id="CVE-2021-44228")
        self.assertIn("CVE-2021-44228", result)

    @patch("mcp_govt_api.tools.cisa.fetch_json", new_callable=AsyncMock)
    async def test_no_matching_vulnerabilities(self, mock_fetch):
        mock_fetch.return_value = {
            "vulnerabilities": [
                {
                    "cveID": "CVE-2021-44228",
                    "vendorProject": "Apache",
                    "product": "Log4j",
                }
            ]
        }
        result = await search_known_exploited_vulnerabilities(vendor="NonexistentVendor")
        self.assertIn("No known exploited vulnerabilities found", result)

    @patch("mcp_govt_api.tools.cisa.fetch_json", new_callable=AsyncMock)
    async def test_empty_catalog(self, mock_fetch):
        mock_fetch.return_value = {"vulnerabilities": []}
        result = await search_known_exploited_vulnerabilities()
        self.assertIn("No vulnerabilities found", result)

    @patch("mcp_govt_api.tools.cisa.fetch_json", new_callable=AsyncMock)
    async def test_network_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("Connection error")
        result = await search_known_exploited_vulnerabilities()
        self.assertIn("Error fetching KEV catalog", result)


class TestGetRecentCisaAlerts(unittest.IsolatedAsyncioTestCase):
    """Tests for get_recent_cisa_alerts tool."""

    @patch("mcp_govt_api.tools.cisa.http_client")
    async def test_successful_alerts(self, mock_client):
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Critical Vulnerability in Widget Software</title>
                <published>2024-06-15T00:00:00Z</published>
                <link href="https://www.cisa.gov/alerts/aa24-001"/>
                <summary>A critical vulnerability has been found.</summary>
            </entry>
        </feed>"""
        mock_response = MagicMock()
        mock_response.text = xml_content
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await get_recent_cisa_alerts(limit=5)
        self.assertIn("Critical Vulnerability", result)
        self.assertIn("2024-06-15", result)

    @patch("mcp_govt_api.tools.cisa.http_client")
    async def test_no_entries(self, mock_client):
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
        </feed>"""
        mock_response = MagicMock()
        mock_response.text = xml_content
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await get_recent_cisa_alerts()
        self.assertIn("No recent alerts", result)

    @patch("mcp_govt_api.tools.cisa.http_client")
    async def test_network_error(self, mock_client):
        mock_client.get = AsyncMock(side_effect=Exception("Timeout"))
        result = await get_recent_cisa_alerts()
        self.assertIn("Error fetching CISA alerts", result)


class TestGetCisaBulletins(unittest.IsolatedAsyncioTestCase):
    """Tests for get_cisa_bulletins tool."""

    @patch("mcp_govt_api.tools.cisa.http_client")
    async def test_successful_bulletins(self, mock_client):
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Vulnerability Summary for Week of June 10</title>
                <published>2024-06-14T00:00:00Z</published>
                <link href="https://www.cisa.gov/bulletins/sb24-166"/>
            </entry>
        </feed>"""
        mock_response = MagicMock()
        mock_response.text = xml_content
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        result = await get_cisa_bulletins(limit=5)
        self.assertIn("Vulnerability Summary", result)

    @patch("mcp_govt_api.tools.cisa.http_client")
    async def test_network_error(self, mock_client):
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
        result = await get_cisa_bulletins()
        self.assertIn("Error fetching CISA bulletins", result)


class TestQueryCisaKev(unittest.IsolatedAsyncioTestCase):
    """Tests for query_cisa_kev tool."""

    @patch("mcp_govt_api.tools.cisa.fetch_json", new_callable=AsyncMock)
    async def test_raw_query(self, mock_fetch):
        mock_fetch.return_value = {"catalogVersion": "2024.06.15", "vulnerabilities": []}
        result = await query_cisa_kev()
        mock_fetch.assert_awaited_once()
        self.assertIn("vulnerabilities", result)


if __name__ == "__main__":
    unittest.main()
