from datetime import datetime, timezone

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json


BASE = "https://earthquake.usgs.gov/fdsnws/event/1/"


def _format_time(epoch_ms: int) -> str:
    """Format epoch milliseconds to a human-readable UTC string."""
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def _format_feature(feature: dict) -> str:
    """Format a single GeoJSON earthquake feature into a readable string."""
    props = feature.get("properties", {})
    coords = feature.get("geometry", {}).get("coordinates", [None, None, None])

    mag = props.get("mag", "N/A")
    place = props.get("place", "Unknown location")
    time_ms = props.get("time")
    time_str = _format_time(time_ms) if time_ms is not None else "N/A"
    depth_km = coords[2] if coords[2] is not None else "N/A"
    url = props.get("url", "")
    tsunami = props.get("tsunami", 0)
    alert = props.get("alert")

    lines = [
        f"**M{mag}** - {place}",
        f"Time: {time_str}",
        f"Depth: {depth_km} km",
    ]

    if tsunami:
        lines.append("TSUNAMI WARNING: Yes")
    if alert:
        lines.append(f"Alert level: {alert}")
    if url:
        lines.append(f"Details: {url}")

    return "\n".join(lines)


@mcp.tool()
async def get_recent_earthquakes(min_magnitude: float = 4.0, limit: int = 10) -> str:
    """Get recent earthquakes worldwide above a magnitude threshold.

    Args:
        min_magnitude: Minimum Richter magnitude to include (default: 4.0)
        limit: Maximum number of earthquakes to return (default: 10)

    Returns:
        Recent earthquakes ordered by time descending, showing magnitude,
        location, time, depth, and tsunami warning where applicable
    """
    url = f"{BASE}query"
    params = {
        "format": "geojson",
        "minmagnitude": min_magnitude,
        "limit": limit,
        "orderby": "time",
    }

    data = await fetch_json(url, params=params)

    features = data.get("features", [])
    if not features:
        return f"No earthquakes found with magnitude >= {min_magnitude}"

    meta = data.get("metadata", {})
    count = meta.get("count", len(features))

    result = [
        f"Recent earthquakes worldwide (M >= {min_magnitude}) - {count} result(s):\n"
    ]
    for feature in features:
        result.append(_format_feature(feature))

    return "\n\n---\n\n".join(result)


@mcp.tool()
async def get_earthquakes_near(
    latitude: float,
    longitude: float,
    max_radius_km: int = 200,
    min_magnitude: float = 2.0,
) -> str:
    """Get recent earthquakes near a geographic location.

    Args:
        latitude: Latitude of the center point (e.g., 37.7749 for San Francisco)
        longitude: Longitude of the center point (e.g., -122.4194 for San Francisco)
        max_radius_km: Search radius in kilometers (default: 200)
        min_magnitude: Minimum Richter magnitude to include (default: 2.0)

    Returns:
        Up to 10 recent earthquakes near the location, ordered by time descending,
        showing magnitude, location, time, depth, and tsunami warning where applicable
    """
    url = f"{BASE}query"
    params = {
        "format": "geojson",
        "latitude": latitude,
        "longitude": longitude,
        "maxradiuskm": max_radius_km,
        "minmagnitude": min_magnitude,
        "limit": 10,
        "orderby": "time",
    }

    data = await fetch_json(url, params=params)

    features = data.get("features", [])
    if not features:
        return (
            f"No earthquakes found within {max_radius_km} km of "
            f"({latitude}, {longitude}) with magnitude >= {min_magnitude}"
        )

    meta = data.get("metadata", {})
    count = meta.get("count", len(features))

    result = [
        f"Recent earthquakes within {max_radius_km} km of "
        f"({latitude}, {longitude}) (M >= {min_magnitude}) - {count} result(s):\n"
    ]
    for feature in features:
        result.append(_format_feature(feature))

    return "\n\n---\n\n".join(result)


@mcp.tool()
async def query_earthquakes(params: dict) -> dict:
    """Make a raw query to the USGS Earthquake Hazards API.

    Provides direct access to the USGS FDSN Event Web Service. The
    ``format=geojson`` parameter is always injected automatically.

    Full parameter reference: https://earthquake.usgs.gov/fdsnws/event/1/

    Common parameters:
        starttime: Start of time window (e.g., '2024-01-01')
        endtime: End of time window (e.g., '2024-01-31')
        minmagnitude: Minimum magnitude
        maxmagnitude: Maximum magnitude
        latitude: Center latitude for radius search
        longitude: Center longitude for radius search
        maxradiuskm: Radius in km for location-based search
        limit: Maximum number of results (max 20000)
        orderby: Sort order - 'time' or 'magnitude'

    Args:
        params: Query parameters as a dictionary. ``format`` will be set
            to ``geojson`` automatically, overriding any supplied value.

    Returns:
        Raw GeoJSON response from the USGS API
    """
    url = f"{BASE}query"
    params = dict(params)
    params["format"] = "geojson"
    return await fetch_json(url, params=params)
