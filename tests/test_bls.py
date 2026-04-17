"""Tests for BLS labor statistics tools."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_govt_api.tools.bls import (
    get_bls_timeseries,
    get_unemployment_rate,
    search_bls_series,
)


class TestGetBlsTimeseries(unittest.IsolatedAsyncioTestCase):
    """Tests for get_bls_timeseries tool."""

    async def test_successful_timeseries_request(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "REQUEST_SUCCEEDED",
            "Results": {
                "series": [
                    {
                        "seriesID": "CUUR0000SA0",
                        "data": [
                            {
                                "year": "2024",
                                "period": "M12",
                                "periodName": "December",
                                "value": "315.605",
                                "footnotes": [{}],
                            },
                            {
                                "year": "2024",
                                "period": "M11",
                                "periodName": "November",
                                "value": "315.493",
                                "footnotes": [{}],
                            },
                        ],
                    }
                ]
            },
        }
        mock_response.raise_for_status = MagicMock()

        with patch(
            "mcp_govt_api.tools.bls.http_client.post",
            new=AsyncMock(return_value=mock_response),
        ) as mock_post:
            result = await get_bls_timeseries(
                series_id="CUUR0000SA0",
                start_year="2024",
                end_year="2024",
            )

        mock_post.assert_awaited_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        self.assertEqual(payload["seriesid"], ["CUUR0000SA0"])
        self.assertEqual(payload["startyear"], "2024")
        self.assertEqual(payload["endyear"], "2024")

        self.assertIn("CUUR0000SA0", result)
        self.assertIn("December 2024: 315.605", result)
        self.assertIn("November 2024: 315.493", result)

    async def test_api_error_status(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "REQUEST_FAILED",
            "message": ["Invalid series ID"],
        }
        mock_response.raise_for_status = MagicMock()

        with patch(
            "mcp_govt_api.tools.bls.http_client.post",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await get_bls_timeseries(series_id="INVALID")

        self.assertIn("BLS API error", result)
        self.assertIn("Invalid series ID", result)

    async def test_network_error(self):
        with patch(
            "mcp_govt_api.tools.bls.http_client.post",
            new=AsyncMock(side_effect=Exception("Connection refused")),
        ):
            result = await get_bls_timeseries(series_id="CUUR0000SA0")

        self.assertIn("Error fetching BLS data", result)

    async def test_no_data_points(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "REQUEST_SUCCEEDED",
            "Results": {
                "series": [{"seriesID": "CUUR0000SA0", "data": []}]
            },
        }
        mock_response.raise_for_status = MagicMock()

        with patch(
            "mcp_govt_api.tools.bls.http_client.post",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await get_bls_timeseries(series_id="CUUR0000SA0")

        self.assertIn("No data points", result)

    async def test_footnotes_included(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "REQUEST_SUCCEEDED",
            "Results": {
                "series": [
                    {
                        "seriesID": "LNS14000000",
                        "data": [
                            {
                                "year": "2024",
                                "period": "M01",
                                "periodName": "January",
                                "value": "3.7",
                                "footnotes": [
                                    {"text": "Preliminary"}
                                ],
                            }
                        ],
                    }
                ]
            },
        }
        mock_response.raise_for_status = MagicMock()

        with patch(
            "mcp_govt_api.tools.bls.http_client.post",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await get_bls_timeseries(series_id="LNS14000000")

        self.assertIn("Preliminary", result)


class TestSearchBlsSeries(unittest.IsolatedAsyncioTestCase):
    """Tests for search_bls_series tool."""

    async def test_search_cpi(self):
        result = await search_bls_series(query="cpi")
        self.assertIn("Consumer Price Index", result)
        self.assertIn("CUUR0000SA0", result)

    async def test_search_unemployment(self):
        result = await search_bls_series(query="unemployment")
        self.assertIn("Unemployment Rate", result)
        self.assertIn("LNS14000000", result)

    async def test_search_no_results(self):
        result = await search_bls_series(query="xyznonexistent")
        self.assertIn("No BLS series found", result)
        self.assertIn("Try one of these keywords", result)

    async def test_search_employment(self):
        result = await search_bls_series(query="employment")
        self.assertIn("CES0000000001", result)

    async def test_search_case_insensitive(self):
        result = await search_bls_series(query="CPI")
        self.assertIn("Consumer Price Index", result)


class TestGetUnemploymentRate(unittest.IsolatedAsyncioTestCase):
    """Tests for get_unemployment_rate tool."""

    async def test_national_unemployment(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "REQUEST_SUCCEEDED",
            "Results": {
                "series": [
                    {
                        "seriesID": "LNS14000000",
                        "data": [
                            {
                                "year": "2024",
                                "period": "M12",
                                "periodName": "December",
                                "value": "4.1",
                                "footnotes": [{}],
                            },
                        ],
                    }
                ]
            },
        }
        mock_response.raise_for_status = MagicMock()

        with patch(
            "mcp_govt_api.tools.bls.http_client.post",
            new=AsyncMock(return_value=mock_response),
        ):
            result = await get_unemployment_rate()

        self.assertIn("National Unemployment Rate", result)
        self.assertIn("December 2024: 4.1%", result)

    async def test_state_unemployment(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "REQUEST_SUCCEEDED",
            "Results": {
                "series": [
                    {
                        "seriesID": "LASST060000000000003",
                        "data": [
                            {
                                "year": "2024",
                                "period": "M11",
                                "periodName": "November",
                                "value": "5.2",
                                "footnotes": [{}],
                            },
                        ],
                    }
                ]
            },
        }
        mock_response.raise_for_status = MagicMock()

        with patch(
            "mcp_govt_api.tools.bls.http_client.post",
            new=AsyncMock(return_value=mock_response),
        ) as mock_post:
            result = await get_unemployment_rate(state="CA")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        self.assertIn("LASST060000000000003", payload["seriesid"])
        self.assertIn("Unemployment Rate - CA", result)
        self.assertIn("November 2024: 5.2%", result)

    async def test_invalid_state_code(self):
        result = await get_unemployment_rate(state="ZZ")
        self.assertIn("Unknown state code", result)

    async def test_state_with_year(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "REQUEST_SUCCEEDED",
            "Results": {
                "series": [
                    {
                        "seriesID": "LASST480000000000003",
                        "data": [
                            {
                                "year": "2023",
                                "period": "M12",
                                "periodName": "December",
                                "value": "4.0",
                                "footnotes": [{}],
                            },
                        ],
                    }
                ]
            },
        }
        mock_response.raise_for_status = MagicMock()

        with patch(
            "mcp_govt_api.tools.bls.http_client.post",
            new=AsyncMock(return_value=mock_response),
        ) as mock_post:
            result = await get_unemployment_rate(state="TX", year="2023")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        self.assertEqual(payload["startyear"], "2023")
        self.assertEqual(payload["endyear"], "2023")
        self.assertIn("TX", result)

    async def test_network_error(self):
        with patch(
            "mcp_govt_api.tools.bls.http_client.post",
            new=AsyncMock(side_effect=Exception("Timeout")),
        ):
            result = await get_unemployment_rate()

        self.assertIn("Error fetching unemployment data", result)


if __name__ == "__main__":
    unittest.main()
