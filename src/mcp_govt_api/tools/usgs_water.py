from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json


USGS_BASE = "https://waterservices.usgs.gov/nwis/iv/"

# USGS parameter codes
PARAM_STREAMFLOW = "00060"   # Streamflow, ft³/s
PARAM_GAGE_HEIGHT = "00065"  # Gage height, ft
PARAM_WATER_TEMP = "00010"   # Water temperature, °C


def _format_time_series(time_series: list[dict]) -> list[str]:
    """Extract and format site readings from a USGS timeSeries array.

    Args:
        time_series: The ``data["value"]["timeSeries"]`` list from the API.

    Returns:
        List of formatted strings, one per parameter per site.
    """
    # Group readings by site name so they render together.
    sites: dict[str, dict[str, str]] = {}

    for series in time_series:
        site_name = series.get("sourceInfo", {}).get("siteName", "Unknown site")
        site_code = (
            series.get("sourceInfo", {})
            .get("siteCode", [{}])[0]
            .get("value", "N/A")
        )
        variable_name = series.get("variable", {}).get("variableName", "Unknown")
        variable_code = (
            series.get("variable", {})
            .get("variableCode", [{}])[0]
            .get("value", "")
        )
        unit = (
            series.get("variable", {})
            .get("unit", {})
            .get("unitCode", "")
        )

        values = series.get("values", [{}])[0].get("value", [])
        reading = values[0].get("value", "N/A") if values else "N/A"
        timestamp = values[0].get("dateTime", "")[:16] if values else ""

        key = f"{site_name} (#{site_code})"
        if key not in sites:
            sites[key] = {"timestamp": timestamp}

        if variable_code == PARAM_STREAMFLOW:
            sites[key]["streamflow"] = f"{reading} {unit}"
        elif variable_code == PARAM_GAGE_HEIGHT:
            sites[key]["gage_height"] = f"{reading} {unit}"
        elif variable_code == PARAM_WATER_TEMP:
            sites[key]["water_temp"] = f"{reading} {unit}"
        else:
            sites[key][variable_name] = f"{reading} {unit}"

    lines: list[str] = []
    for site_label, readings in sites.items():
        parts = [f"**{site_label}**"]
        ts = readings.pop("timestamp", "")
        if ts:
            parts.append(f"As of: {ts} UTC")
        for label, value in readings.items():
            parts.append(f"{label.replace('_', ' ').title()}: {value}")
        lines.append("\n".join(parts))

    return lines


@mcp.tool()
async def get_water_conditions(state: str) -> str:
    """Get current stream flow and water conditions for a US state.

    Queries the USGS Instantaneous Values (IV) Water Services API for real-time
    streamflow and gage height readings across stream monitoring sites in the
    requested state. Results are limited to the 10 most recently updated sites.

    Args:
        state: Two-letter US state code (e.g., 'CA', 'TX', 'WA').

    Returns:
        Streamflow (ft³/s) and gage height (ft) for up to 10 stream sites,
        or an error message if no data is available.
    """
    state = state.upper().strip()
    if len(state) != 2:
        return "Error: State must be a 2-letter code (e.g., 'CA', 'TX', 'WA')"

    params = {
        "format": "json",
        "stateCd": state,
        "parameterCd": f"{PARAM_STREAMFLOW},{PARAM_GAGE_HEIGHT}",
        "siteType": "ST",
        "siteStatus": "active",
    }

    data = await fetch_json(USGS_BASE, params=params)

    time_series = data.get("value", {}).get("timeSeries", [])
    if not time_series:
        return f"No active stream monitoring data found for state: {state}"

    # Deduplicate to at most 10 unique sites (timeSeries has one entry per
    # parameter, so we track seen site codes while walking the list).
    seen_sites: set[str] = set()
    limited: list[dict] = []
    for series in time_series:
        site_code = (
            series.get("sourceInfo", {})
            .get("siteCode", [{}])[0]
            .get("value", "")
        )
        if site_code not in seen_sites:
            seen_sites.add(site_code)
            if len(seen_sites) > 10:
                break
        limited.append(series)

    lines = _format_time_series(limited)
    if not lines:
        return f"No readable stream data returned for state: {state}"

    header = f"**USGS Real-Time Stream Conditions: {state}**\n(up to 10 active sites)\n"
    return header + "\n\n---\n\n".join(lines)


@mcp.tool()
async def get_water_site(site_number: str) -> str:
    """Get current conditions for a specific USGS water monitoring site.

    Retrieves all available real-time parameters (streamflow, gage height,
    water temperature, and others) for the given USGS site number.

    Args:
        site_number: USGS site number, typically 8–15 digits
                     (e.g., '01646500' for the Potomac River at Little Falls, MD).

    Returns:
        All current parameter readings for the site, or an error message if
        the site number is not found or has no recent data.
    """
    site_number = site_number.strip()
    if not site_number:
        return "Error: A site number must be provided (e.g., '01646500')"

    params = {
        "format": "json",
        "sites": site_number,
        "siteStatus": "all",
    }

    data = await fetch_json(USGS_BASE, params=params)

    time_series = data.get("value", {}).get("timeSeries", [])
    if not time_series:
        return f"No data found for USGS site: {site_number}"

    lines = _format_time_series(time_series)
    if not lines:
        return f"Site {site_number} returned no readable parameter values"

    return "\n\n---\n\n".join(lines)


@mcp.tool()
async def query_usgs_water(params: dict) -> dict:
    """Make a raw query to the USGS Instantaneous Values Water Services API.

    The ``format=json`` parameter is always injected automatically. Refer to
    https://waterservices.usgs.gov/rest/IV-Service.html for the full list of
    supported query parameters.

    Common parameters:
        - ``stateCd``: 2-letter state code (e.g., ``'OR'``)
        - ``countyCd``: FIPS county code (e.g., ``'41051'``)
        - ``sites``: Comma-separated USGS site numbers
        - ``bBox``: Bounding box ``'west,south,east,north'``
        - ``parameterCd``: Comma-separated parameter codes
          (``00060``=streamflow, ``00065``=gage height, ``00010``=water temp)
        - ``siteType``: ``ST`` (stream) or ``LK`` (lake)
        - ``siteStatus``: ``active``, ``inactive``, or ``all``
        - ``period``: ISO 8601 duration for lookback (e.g., ``'PT2H'`` = 2 hours)

    Args:
        params: Query parameters as a dictionary. ``format`` will be overridden
                to ``'json'`` regardless of what is supplied.

    Returns:
        Raw JSON response from the USGS IV Water Services API.
    """
    params = dict(params)
    params["format"] = "json"
    return await fetch_json(USGS_BASE, params=params)
