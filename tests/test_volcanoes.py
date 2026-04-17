"""Tests for USGS volcano monitoring tools."""

import unittest
from unittest.mock import AsyncMock, patch

from mcp_govt_api.tools.volcanoes import (
    _format_alert_feature,
    _format_volcano_feature,
    get_active_volcanoes,
    get_volcano_alerts,
    search_volcanoes,
)

# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

def _make_volcano_feature(
    name="Mount Rainier",
    subregion="US-Washington",
    v_type="Stratovolcano",
    elev=4392,
    alert_level="NORMAL",
    color_code="GREEN",
    lat=46.8523,
    lon=-121.7603,
):
    return {
        "type": "Feature",
        "properties": {
            "vName": name,
            "subregion": subregion,
            "vType": v_type,
            "elev": elev,
            "alertLevel": alert_level,
            "colorCode": color_code,
        },
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    }


def _make_alert_feature(
    name="Kilauea",
    alert_level="WARNING",
    color_code="RED",
    obs_code="HVO",
    alert_date="2024-06-15",
    lat=19.4069,
    lon=-155.2834,
):
    return {
        "type": "Feature",
        "properties": {
            "volcanoName": name,
            "alertLevel": alert_level,
            "colorCode": color_code,
            "obsCode": obs_code,
            "alertDate": alert_date,
        },
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    }


# ---------------------------------------------------------------------------
# Formatter tests
# ---------------------------------------------------------------------------

class TestFormatVolcanoFeature(unittest.TestCase):
    """Tests for _format_volcano_feature helper."""

    def test_formats_full_feature(self):
        feature = _make_volcano_feature()
        result = _format_volcano_feature(feature)
        self.assertIn("Mount Rainier", result)
        self.assertIn("Stratovolcano", result)
        self.assertIn("4392", result)
        self.assertIn("US-Washington", result)
        self.assertIn("NORMAL", result)
        self.assertIn("GREEN", result)

    def test_handles_missing_optional_fields(self):
        feature = {
            "properties": {"vName": "Test Volcano"},
            "geometry": {"coordinates": [None, None]},
        }
        result = _format_volcano_feature(feature)
        self.assertIn("Test Volcano", result)
        self.assertNotIn("Region:", result)
        self.assertNotIn("Type:", result)
        self.assertNotIn("Elevation:", result)

    def test_formats_coordinates(self):
        feature = _make_volcano_feature(lat=46.8523, lon=-121.7603)
        result = _format_volcano_feature(feature)
        self.assertIn("46.8523", result)
        self.assertIn("-121.7603", result)


class TestFormatAlertFeature(unittest.TestCase):
    """Tests for _format_alert_feature helper."""

    def test_formats_full_alert(self):
        feature = _make_alert_feature()
        result = _format_alert_feature(feature)
        self.assertIn("Kilauea", result)
        self.assertIn("WARNING", result)
        self.assertIn("RED", result)
        self.assertIn("HVO", result)
        self.assertIn("2024-06-15", result)

    def test_handles_missing_fields(self):
        feature = {
            "properties": {"volcanoName": "Unknown Peak", "alertLevel": "WATCH"},
            "geometry": {"coordinates": [None, None]},
        }
        result = _format_alert_feature(feature)
        self.assertIn("Unknown Peak", result)
        self.assertIn("WATCH", result)


# ---------------------------------------------------------------------------
# get_active_volcanoes tests
# ---------------------------------------------------------------------------

class TestGetActiveVolcanoes(unittest.IsolatedAsyncioTestCase):
    """Tests for get_active_volcanoes tool."""

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_returns_formatted_volcanoes(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_volcano_feature(name="Mount Rainier", subregion="US-Washington"),
                _make_volcano_feature(name="Kilauea", subregion="US-Hawaii", v_type="Shield"),
            ]
        }
        result = await get_active_volcanoes()
        self.assertIn("Mount Rainier", result)
        self.assertIn("Kilauea", result)
        self.assertIn("2 result(s)", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_filters_by_region(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_volcano_feature(name="Mount Rainier", subregion="US-Washington"),
                _make_volcano_feature(name="Kilauea", subregion="US-Hawaii"),
            ]
        }
        result = await get_active_volcanoes(region="Hawaii")
        self.assertIn("Kilauea", result)
        self.assertNotIn("Mount Rainier", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_region_filter_case_insensitive(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_volcano_feature(name="Kilauea", subregion="US-Hawaii"),
            ]
        }
        result = await get_active_volcanoes(region="hawaii")
        self.assertIn("Kilauea", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_no_results_for_region(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_volcano_feature(name="Mount Rainier", subregion="US-Washington"),
            ]
        }
        result = await get_active_volcanoes(region="Antarctica")
        self.assertIn("No volcanoes found", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_empty_features(self, mock_fetch):
        mock_fetch.return_value = {"features": []}
        result = await get_active_volcanoes()
        self.assertIn("No volcano data available", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_sorts_elevated_alerts_first(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_volcano_feature(name="Normal Volcano", alert_level="NORMAL"),
                _make_volcano_feature(name="Warning Volcano", alert_level="WARNING"),
                _make_volcano_feature(name="Watch Volcano", alert_level="WATCH"),
            ]
        }
        result = await get_active_volcanoes()
        warning_pos = result.index("Warning Volcano")
        watch_pos = result.index("Watch Volcano")
        normal_pos = result.index("Normal Volcano")
        self.assertLess(warning_pos, watch_pos)
        self.assertLess(watch_pos, normal_pos)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_respects_limit(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_volcano_feature(name=f"Volcano {i}")
                for i in range(10)
            ]
        }
        result = await get_active_volcanoes(limit=3)
        self.assertIn("3 result(s)", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_clamps_invalid_limit(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [_make_volcano_feature()]
        }
        # Negative limit should be clamped to default
        result = await get_active_volcanoes(limit=-5)
        self.assertIn("1 result(s)", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_network_error(self, mock_fetch):
        mock_fetch.side_effect = RuntimeError("Connection timeout")
        with self.assertRaises(RuntimeError):
            await get_active_volcanoes()


# ---------------------------------------------------------------------------
# get_volcano_alerts tests
# ---------------------------------------------------------------------------

class TestGetVolcanoAlerts(unittest.IsolatedAsyncioTestCase):
    """Tests for get_volcano_alerts tool."""

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_returns_elevated_alerts(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_alert_feature(name="Kilauea", alert_level="WARNING", color_code="RED"),
                _make_alert_feature(name="Mauna Loa", alert_level="ADVISORY", color_code="YELLOW"),
                _make_alert_feature(name="Mount Rainier", alert_level="NORMAL", color_code="GREEN"),
            ]
        }
        result = await get_volcano_alerts()
        self.assertIn("Kilauea", result)
        self.assertIn("Mauna Loa", result)
        self.assertNotIn("Mount Rainier", result)
        self.assertIn("2 elevated alert(s)", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_all_normal_alerts(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_alert_feature(name="Mount Rainier", alert_level="NORMAL"),
                _make_alert_feature(name="Mount Hood", alert_level="NORMAL"),
            ]
        }
        result = await get_volcano_alerts()
        self.assertIn("NORMAL alert level", result)
        self.assertIn("2", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_no_features(self, mock_fetch):
        mock_fetch.return_value = {"features": []}
        result = await get_volcano_alerts()
        self.assertIn("No current volcano alerts", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_sorts_by_severity(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_alert_feature(name="Advisory Peak", alert_level="ADVISORY"),
                _make_alert_feature(name="Warning Peak", alert_level="WARNING"),
                _make_alert_feature(name="Watch Peak", alert_level="WATCH"),
            ]
        }
        result = await get_volcano_alerts()
        warning_pos = result.index("Warning Peak")
        watch_pos = result.index("Watch Peak")
        advisory_pos = result.index("Advisory Peak")
        self.assertLess(warning_pos, watch_pos)
        self.assertLess(watch_pos, advisory_pos)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_network_error(self, mock_fetch):
        mock_fetch.side_effect = RuntimeError("API unavailable")
        with self.assertRaises(RuntimeError):
            await get_volcano_alerts()


# ---------------------------------------------------------------------------
# search_volcanoes tests
# ---------------------------------------------------------------------------

class TestSearchVolcanoes(unittest.IsolatedAsyncioTestCase):
    """Tests for search_volcanoes tool."""

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_search_by_name(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_volcano_feature(name="Mount Rainier"),
                _make_volcano_feature(name="Mount St. Helens"),
                _make_volcano_feature(name="Kilauea"),
            ]
        }
        result = await search_volcanoes(query="Mount")
        self.assertIn("Mount Rainier", result)
        self.assertIn("Mount St. Helens", result)
        self.assertNotIn("Kilauea", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_search_case_insensitive(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_volcano_feature(name="Kilauea"),
            ]
        }
        result = await search_volcanoes(query="kilauea")
        self.assertIn("Kilauea", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_search_by_type(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_volcano_feature(name="Kilauea", v_type="Shield"),
                _make_volcano_feature(name="Mount Rainier", v_type="Stratovolcano"),
            ]
        }
        result = await search_volcanoes(volcano_type="Shield")
        self.assertIn("Kilauea", result)
        self.assertNotIn("Mount Rainier", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_search_combined_filters(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_volcano_feature(name="Mount Rainier", v_type="Stratovolcano"),
                _make_volcano_feature(name="Mount Baker", v_type="Stratovolcano"),
                _make_volcano_feature(name="Kilauea", v_type="Shield"),
            ]
        }
        result = await search_volcanoes(query="Mount", volcano_type="Strato")
        self.assertIn("Mount Rainier", result)
        self.assertIn("Mount Baker", result)
        self.assertNotIn("Kilauea", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_no_results(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_volcano_feature(name="Kilauea"),
            ]
        }
        result = await search_volcanoes(query="Nonexistent")
        self.assertIn("No volcanoes found", result)
        self.assertIn("'Nonexistent'", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_no_results_with_type_filter(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_volcano_feature(name="Kilauea", v_type="Shield"),
            ]
        }
        result = await search_volcanoes(query="Kilauea", volcano_type="Caldera")
        self.assertIn("No volcanoes found", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_empty_database(self, mock_fetch):
        mock_fetch.return_value = {"features": []}
        result = await search_volcanoes(query="anything")
        self.assertIn("No volcano data available", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_results_sorted_alphabetically(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_volcano_feature(name="Mount St. Helens"),
                _make_volcano_feature(name="Mount Adams"),
                _make_volcano_feature(name="Mount Baker"),
            ]
        }
        result = await search_volcanoes(query="Mount")
        adams_pos = result.index("Mount Adams")
        baker_pos = result.index("Mount Baker")
        helens_pos = result.index("Mount St. Helens")
        self.assertLess(adams_pos, baker_pos)
        self.assertLess(baker_pos, helens_pos)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_limits_to_25_results(self, mock_fetch):
        mock_fetch.return_value = {
            "features": [
                _make_volcano_feature(name=f"Volcano {i:03d}")
                for i in range(30)
            ]
        }
        result = await search_volcanoes()
        self.assertIn("25 of 30", result)

    @patch("mcp_govt_api.tools.volcanoes.fetch_json", new_callable=AsyncMock)
    async def test_network_error(self, mock_fetch):
        mock_fetch.side_effect = RuntimeError("Connection refused")
        with self.assertRaises(RuntimeError):
            await search_volcanoes(query="test")


if __name__ == "__main__":
    unittest.main()
