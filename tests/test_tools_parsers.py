from mcp_govt_api.tools.noaa_goes_imagery import _extract_latest_file_from_directory
from mcp_govt_api.tools.rsoe_edis import parse_rsoe_event_list_html


def test_noaa_goes_extract_latest_for_resolution() -> None:
    directory_listing = "\n".join(
        [
            "20260681750_GOES19-ABI-FD-GEOCOLOR-21696x21696.jpg 09-Mar-2026 17:06",
            "20260681800_GOES19-ABI-FD-GEOCOLOR-21696x21696.jpg 09-Mar-2026 17:15",
            "20260681810_GOES19-ABI-FD-GEOCOLOR-5424x5424.jpg 09-Mar-2026 17:25",
        ]
    )

    latest = _extract_latest_file_from_directory(
        directory_listing_text=directory_listing,
        resolution="21696x21696",
    )
    assert latest == "20260681800_GOES19-ABI-FD-GEOCOLOR-21696x21696.jpg"


def test_rsoe_event_list_parser_limit_and_fields() -> None:
    html = """
    <html><body>
      <h5>Test Event A</h5>
      <table><tr><td>2026-03-19 11:18:30</td><td>Brazil, South America</td></tr></table>
      <h5>Test Event B</h5>
      <table><tr><td>2026-03-18 10:22:05</td><td>Nigeria, Africa</td></tr></table>
    </body></html>
    """

    events = parse_rsoe_event_list_html(html_text=html, limit=1)
    assert len(events) == 1
    assert events[0]["title"] == "Test Event A"
    assert events[0]["datetime"] == "2026-03-19 11:18:30"
    assert "Brazil" in events[0]["location"]

