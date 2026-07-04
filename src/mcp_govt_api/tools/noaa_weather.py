from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

NOAA_BASE = "https://api.weather.gov"

# Common WFO codes for reference
COMMON_WFO_CODES = {
    "OKX": "New York, NY",
    "LOT": "Chicago, IL",
    "LAX": "Los Angeles, CA",
    "HFO": "Honolulu, HI",
    "BOX": "Boston, MA",
    "PHI": "Philadelphia, PA",
    "LWX": "Washington DC / Baltimore",
    "MFL": "Miami, FL",
    "HGX": "Houston, TX",
    "FWD": "Dallas / Fort Worth, TX",
    "SEW": "Seattle, WA",
    "SFO": "San Francisco, CA",
    "DEN": "Denver, CO (Boulder)",
    "ATL": "Atlanta, GA (Peachtree City)",
    "DTX": "Detroit, MI",
    "MPX": "Minneapolis, MN",
    "ILN": "Cincinnati / Dayton, OH (Wilmington)",
    "OUN": "Norman, OK",
    "JAX": "Jacksonville, FL",
    "RAH": "Raleigh, NC",
}


@mcp.tool()
async def get_forecast_discussion(wfo: str = "") -> str:
    """Get the Area Forecast Discussion (AFD) from a NWS Weather Forecast Office.

    The AFD is a detailed narrative written by meteorologists explaining current
    and expected weather patterns, model guidance, and forecast reasoning.

    Args:
        wfo: Three-letter Weather Forecast Office code (e.g., 'OKX' for New York,
             'LOT' for Chicago). Leave empty to see a list of common WFO codes.

    Returns:
        Latest forecast discussion text from the specified WFO
    """
    if not wfo:
        lines = ["Provide a 3-letter WFO code. Common codes:\n"]
        for code, name in sorted(COMMON_WFO_CODES.items()):
            lines.append(f"  **{code}** - {name}")
        lines.append(
            "\nFull list: https://www.weather.gov/srh/nwsoffices"
        )
        return "\n".join(lines)

    wfo = wfo.upper().strip()
    if len(wfo) != 3 or not wfo.isalpha():
        return "Error: WFO code must be exactly 3 letters (e.g., 'OKX', 'LOT')"

    try:
        # Get the list of AFD products for this WFO
        products_url = f"{NOAA_BASE}/products/types/AFD/locations/{wfo}"
        products_data = await fetch_json(products_url)

        graph = products_data.get("@graph", [])
        if not graph:
            return f"No forecast discussions found for WFO '{wfo}'. Check the code at https://www.weather.gov/srh/nwsoffices"

        # Fetch the most recent discussion
        latest_id = graph[0]["id"]
        product_url = f"{NOAA_BASE}/products/{latest_id}"
        product_data = await fetch_json(product_url)

        issued = product_data.get("issuanceTime", "Unknown")
        text = product_data.get("productText", "No discussion text available.")
        office = product_data.get("issuingOffice", wfo)

        return (
            f"**Area Forecast Discussion — {office}**\n"
            f"Issued: {issued}\n\n"
            f"{text.strip()}"
        )
    except Exception as e:
        return f"Error fetching forecast discussion for WFO '{wfo}': {e}"


@mcp.tool()
async def get_active_weather_alerts(
    state: str = "",
    event: str = "",
    severity: str = "",
    limit: int = 10,
) -> str:
    """Get active weather alerts from the National Weather Service.

    Provides filtering by state, event type, and severity. Returns alerts
    sorted by severity (Extreme > Severe > Moderate > Minor > Unknown).

    Args:
        state: Two-letter state code (e.g., 'CA', 'TX'). Required.
        event: Filter by event type (e.g., 'Tornado Warning', 'Flood Watch')
        severity: Filter by severity: 'Extreme', 'Severe', 'Moderate', or 'Minor'
        limit: Maximum number of alerts to return (default 10, max 50)

    Returns:
        Active weather alerts matching the filters
    """
    if not state:
        return "Error: State code is required (e.g., 'CA', 'TX', 'NY')"

    state = state.upper().strip()
    if len(state) != 2 or not state.isalpha():
        return "Error: State must be a 2-letter code (e.g., 'CA', 'TX')"

    limit = max(1, min(limit, 50))

    try:
        params: dict = {"area": state}
        if severity:
            params["severity"] = severity.capitalize()

        url = f"{NOAA_BASE}/alerts/active"
        data = await fetch_json(url, params=params)

        alerts = data.get("features", [])

        # Filter by event type if specified
        if event:
            event_lower = event.lower()
            alerts = [
                a for a in alerts
                if event_lower in a["properties"].get("event", "").lower()
            ]

        if not alerts:
            filter_desc = " matching filters" if event or severity else ""
            return f"No active weather alerts for {state}{filter_desc}."

        # Sort by severity order
        severity_order = {"Extreme": 0, "Severe": 1, "Moderate": 2, "Minor": 3, "Unknown": 4}
        alerts.sort(
            key=lambda a: severity_order.get(a["properties"].get("severity", "Unknown"), 4)
        )

        alerts = alerts[:limit]

        result = [f"Active weather alerts for {state} ({len(alerts)} shown):\n"]
        for alert in alerts:
            props = alert["properties"]
            urgency = props.get("urgency", "N/A")
            certainty = props.get("certainty", "N/A")
            result.append(
                f"**{props.get('event', 'Unknown Event')}** ({props.get('severity', 'N/A')})\n"
                f"Urgency: {urgency} | Certainty: {certainty}\n"
                f"Areas: {props.get('areaDesc', 'N/A')}\n"
                f"{props.get('headline', 'No headline')}"
            )

        return "\n\n---\n\n".join(result)
    except Exception as e:
        return f"Error fetching weather alerts: {e}"


@mcp.tool()
async def get_radar_stations(state: str = "") -> str:
    """List NEXRAD radar stations, optionally filtered by state.

    Returns station identifiers, names, coordinates, and elevation for
    each radar station. Useful for identifying nearby radar coverage.

    Args:
        state: Two-letter state code to filter (e.g., 'TX', 'FL').
               Leave empty for all stations.

    Returns:
        List of NEXRAD radar stations with location details
    """
    try:
        url = f"{NOAA_BASE}/radar/stations"
        data = await fetch_json(url)

        features = data.get("features", [])
        if not features:
            return "No radar station data available."

        if state:
            state = state.upper().strip()
            if len(state) != 2 or not state.isalpha():
                return "Error: State must be a 2-letter code (e.g., 'TX', 'FL')"
            features = [
                f for f in features
                if f.get("properties", {}).get("stationType", "") == "WSR-88D"
                and state in f.get("properties", {}).get("name", "").upper()
                or state == f.get("properties", {}).get("stationIdentifier", "")[:2]
                or state in (f.get("properties", {}).get("county", "") or "").upper()
                or state in (f.get("properties", {}).get("state", "") or "").upper()
            ]

        if not features:
            return f"No radar stations found for state '{state}'."

        result = ["NEXRAD Radar Stations" + (f" in {state}" if state else "") + f" ({len(features)} stations):\n"]
        for feat in features:
            props = feat.get("properties", {})
            coords = feat.get("geometry", {}).get("coordinates", [None, None])
            station_id = props.get("stationIdentifier", "N/A")
            name = props.get("name", "N/A")
            station_type = props.get("stationType", "N/A")
            elevation = props.get("elevation", {}).get("value", "N/A")

            lon = coords[0] if coords and len(coords) > 0 else "N/A"
            lat = coords[1] if coords and len(coords) > 1 else "N/A"

            result.append(
                f"**{station_id}** — {name}\n"
                f"Type: {station_type} | Elevation: {elevation}m\n"
                f"Coordinates: {lat}, {lon}"
            )

        return "\n\n".join(result)
    except Exception as e:
        return f"Error fetching radar stations: {e}"
