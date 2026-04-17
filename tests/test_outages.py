"""Tests for service outage monitoring tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.outages import (
    STATUS_PAGES,
    check_service_status,
    get_service_incidents,
    list_monitored_services,
)


class TestCheckServiceStatus(unittest.IsolatedAsyncioTestCase):
    async def test_returns_operational_status(self):
        mock_data = {
            "page": {"name": "GitHub"},
            "status": {
                "indicator": "none",
                "description": "All Systems Operational",
            },
            "components": [
                {"name": "Git Operations", "status": "operational"},
                {"name": "API Requests", "status": "operational"},
                {"name": "Actions", "status": "operational"},
            ],
        }

        with patch(
            "mcp_govt_api.tools.outages.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await check_service_status("github")

        self.assertIn("GitHub", result)
        self.assertIn("All Systems Operational", result)
        self.assertIn("green", result)
        self.assertIn("Git Operations", result)
        self.assertIn("Operational", result)
        self.assertIn("API Requests", result)
        self.assertIn("Actions", result)

    async def test_returns_degraded_status(self):
        mock_data = {
            "page": {"name": "Cloudflare"},
            "status": {
                "indicator": "minor",
                "description": "Minor Service Outage",
            },
            "components": [
                {"name": "CDN", "status": "operational"},
                {"name": "DNS", "status": "degraded_performance"},
                {"name": "Workers", "status": "operational"},
            ],
        }

        with patch(
            "mcp_govt_api.tools.outages.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await check_service_status("cloudflare")

        self.assertIn("Cloudflare", result)
        self.assertIn("Minor Service Outage", result)
        self.assertIn("yellow", result)
        self.assertIn("DNS", result)
        self.assertIn("Degraded Performance", result)

    async def test_returns_major_outage_status(self):
        mock_data = {
            "page": {"name": "Stripe"},
            "status": {
                "indicator": "major",
                "description": "Major System Outage",
            },
            "components": [
                {"name": "API", "status": "major_outage"},
                {"name": "Dashboard", "status": "partial_outage"},
            ],
        }

        with patch(
            "mcp_govt_api.tools.outages.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await check_service_status("stripe")

        self.assertIn("Stripe", result)
        self.assertIn("Major System Outage", result)
        self.assertIn("orange", result)
        self.assertIn("API", result)
        self.assertIn("Major Outage", result)
        self.assertIn("Partial Outage", result)

    async def test_unknown_service(self):
        result = await check_service_status("nonexistent_service")

        self.assertIn("Unknown service", result)
        self.assertIn("nonexistent_service", result)
        self.assertIn("Supported services", result)

    async def test_handles_api_error(self):
        with patch(
            "mcp_govt_api.tools.outages.fetch_json",
            new=AsyncMock(side_effect=Exception("Connection refused")),
        ):
            result = await check_service_status("github")

        self.assertIn("Error fetching status for github", result)
        self.assertIn("Connection refused", result)

    async def test_case_insensitive_service_name(self):
        mock_data = {
            "page": {"name": "GitHub"},
            "status": {"indicator": "none", "description": "All Systems Operational"},
            "components": [],
        }

        with patch(
            "mcp_govt_api.tools.outages.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ) as mock_fetch:
            result = await check_service_status("GitHub")

        self.assertIn("GitHub", result)
        mock_fetch.assert_called_once()

    async def test_skips_group_components(self):
        mock_data = {
            "page": {"name": "Vercel"},
            "status": {"indicator": "none", "description": "All Systems Operational"},
            "components": [
                {"name": "Infrastructure", "status": "operational", "group": True},
                {"name": "API", "status": "operational", "group": False},
            ],
        }

        with patch(
            "mcp_govt_api.tools.outages.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await check_service_status("vercel")

        self.assertNotIn("Infrastructure", result)
        self.assertIn("API", result)

    async def test_empty_components(self):
        mock_data = {
            "page": {"name": "NPM"},
            "status": {"indicator": "none", "description": "All Systems Operational"},
            "components": [],
        }

        with patch(
            "mcp_govt_api.tools.outages.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await check_service_status("npm")

        self.assertIn("NPM", result)
        self.assertIn("All Systems Operational", result)
        self.assertNotIn("Components", result)


class TestGetServiceIncidents(unittest.IsolatedAsyncioTestCase):
    async def test_returns_recent_incidents(self):
        mock_data = {
            "incidents": [
                {
                    "name": "Degraded API Performance",
                    "status": "resolved",
                    "impact": "minor",
                    "created_at": "2024-12-15T14:30:00.000Z",
                    "resolved_at": "2024-12-15T16:45:00.000Z",
                    "incident_updates": [
                        {
                            "body": "This incident has been resolved. "
                            "API response times have returned to normal."
                        }
                    ],
                },
                {
                    "name": "Elevated Error Rates",
                    "status": "resolved",
                    "impact": "major",
                    "created_at": "2024-12-10T09:00:00.000Z",
                    "resolved_at": "2024-12-10T12:00:00.000Z",
                    "incident_updates": [
                        {"body": "All services fully recovered."}
                    ],
                },
            ]
        }

        with patch(
            "mcp_govt_api.tools.outages.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_service_incidents("github", limit=5)

        self.assertIn("Degraded API Performance", result)
        self.assertIn("Resolved", result)
        self.assertIn("Minor", result)
        self.assertIn("2024-12-15", result)
        self.assertIn("returned to normal", result)
        self.assertIn("Elevated Error Rates", result)
        self.assertIn("Major", result)
        self.assertIn("2024-12-10", result)

    async def test_no_incidents(self):
        mock_data = {"incidents": []}

        with patch(
            "mcp_govt_api.tools.outages.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_service_incidents("cloudflare")

        self.assertIn("No recent incidents found for cloudflare", result)

    async def test_unknown_service(self):
        result = await get_service_incidents("fake_service")

        self.assertIn("Unknown service", result)
        self.assertIn("fake_service", result)

    async def test_handles_api_error(self):
        with patch(
            "mcp_govt_api.tools.outages.fetch_json",
            new=AsyncMock(side_effect=Exception("Timeout")),
        ):
            result = await get_service_incidents("github")

        self.assertIn("Error fetching incidents for github", result)
        self.assertIn("Timeout", result)

    async def test_respects_limit(self):
        incidents = [
            {
                "name": f"Incident {i}",
                "status": "resolved",
                "impact": "minor",
                "created_at": f"2024-12-{15 - i:02d}T00:00:00.000Z",
                "resolved_at": f"2024-12-{15 - i:02d}T01:00:00.000Z",
                "incident_updates": [],
            }
            for i in range(10)
        ]
        mock_data = {"incidents": incidents}

        with patch(
            "mcp_govt_api.tools.outages.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_service_incidents("github", limit=3)

        self.assertIn("3 shown", result)
        self.assertIn("Incident 0", result)
        self.assertIn("Incident 2", result)
        self.assertNotIn("Incident 3", result)

    async def test_limit_clamped_to_max(self):
        mock_data = {"incidents": []}

        with patch(
            "mcp_govt_api.tools.outages.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_service_incidents("github", limit=100)

        self.assertIn("No recent incidents", result)

    async def test_truncates_long_update_body(self):
        long_body = "A" * 500
        mock_data = {
            "incidents": [
                {
                    "name": "Long Incident",
                    "status": "investigating",
                    "impact": "minor",
                    "created_at": "2024-12-15T00:00:00.000Z",
                    "resolved_at": None,
                    "incident_updates": [{"body": long_body}],
                }
            ]
        }

        with patch(
            "mcp_govt_api.tools.outages.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_service_incidents("github")

        self.assertIn("...", result)
        # Should not contain the full 500-char string
        self.assertNotIn("A" * 500, result)

    async def test_incident_without_resolution(self):
        mock_data = {
            "incidents": [
                {
                    "name": "Ongoing Issue",
                    "status": "investigating",
                    "impact": "major",
                    "created_at": "2024-12-15T00:00:00.000Z",
                    "resolved_at": None,
                    "incident_updates": [
                        {"body": "We are investigating reports of issues."}
                    ],
                }
            ]
        }

        with patch(
            "mcp_govt_api.tools.outages.fetch_json",
            new=AsyncMock(return_value=mock_data),
        ):
            result = await get_service_incidents("github")

        self.assertIn("Ongoing Issue", result)
        self.assertIn("Investigating", result)
        self.assertNotIn("Resolved:", result)


class TestListMonitoredServices(unittest.IsolatedAsyncioTestCase):
    async def test_returns_all_services(self):
        result = await list_monitored_services()

        self.assertIn("Monitored Services", result)
        for service_name in STATUS_PAGES:
            self.assertIn(service_name, result)
            self.assertIn(STATUS_PAGES[service_name], result)

    async def test_includes_total_count(self):
        result = await list_monitored_services()

        self.assertIn(f"**Total:** {len(STATUS_PAGES)} services", result)

    async def test_markdown_table_format(self):
        result = await list_monitored_services()

        self.assertIn("| Service | Status Page URL |", result)
        self.assertIn("|---------|", result)


class TestStatusPagesMapping(unittest.TestCase):
    def test_all_urls_are_https(self):
        for service, url in STATUS_PAGES.items():
            self.assertTrue(
                url.startswith("https://"),
                f"{service} URL does not start with https://: {url}",
            )

    def test_expected_services_present(self):
        expected = [
            "github", "cloudflare", "slack", "discord", "reddit",
            "dropbox", "notion", "vercel", "netlify", "heroku",
            "digitalocean", "datadog", "pagerduty", "stripe",
            "twilio", "sendgrid", "npm", "figma", "twitch",
        ]
        for svc in expected:
            self.assertIn(svc, STATUS_PAGES, f"Missing expected service: {svc}")


if __name__ == "__main__":
    unittest.main()
