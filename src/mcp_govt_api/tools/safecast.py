from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json


SAFECAST_BASE = "https://api.safecast.org"


@mcp.tool()
async def get_radiation_measurements(
    latitude: float, longitude: float, distance: int = 100
) -> str:
    """Get radiation measurements near a location.

    Args:
        latitude: Latitude of the location (e.g., 35.6762 for Tokyo)
        longitude: Longitude of the location (e.g., 139.6503 for Tokyo)
        distance: Search radius in km (default: 100)

    Returns:
        Recent radiation measurements near the location in CPM and µSv/h
    """
    url = f"{SAFECAST_BASE}/measurements.json"
    params = {
        "latitude": str(latitude),
        "longitude": str(longitude),
        "distance": str(distance),
    }

    data = await fetch_json(url, params=params)

    if not data:
        return f"No radiation measurements found within {distance}km of {latitude}, {longitude}"

    result = [
        f"Radiation measurements within {distance}km of {latitude}, {longitude}:\n"
    ]

    for m in data[:15]:
        unit = m.get("unit", "unknown")
        value = m.get("value", "N/A")
        captured = m.get("captured_at", "N/A")
        lat = m.get("latitude", "N/A")
        lon = m.get("longitude", "N/A")
        device = m.get("device_id", "unknown")

        result.append(
            f"**{value} {unit}** at ({lat}, {lon})\n"
            f"Captured: {captured} | Device: {device}"
        )

    return "\n\n---\n\n".join(result)


@mcp.tool()
async def get_radiation_history(
    latitude: float,
    longitude: float,
    captured_after: str = "",
    captured_before: str = "",
) -> str:
    """Get radiation measurement history for a location over a time range.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        captured_after: Start date in ISO format (e.g., '2024-01-01')
        captured_before: End date in ISO format (e.g., '2024-12-31')

    Returns:
        Radiation measurements within the time range
    """
    url = f"{SAFECAST_BASE}/measurements.json"
    params = {
        "latitude": str(latitude),
        "longitude": str(longitude),
        "distance": "50",
    }

    if captured_after:
        params["captured_after"] = captured_after
    if captured_before:
        params["captured_before"] = captured_before

    data = await fetch_json(url, params=params)

    if not data:
        return f"No radiation measurements found for the specified location and time range"

    result = [f"Radiation history for ({latitude}, {longitude}):\n"]

    for m in data[:20]:
        unit = m.get("unit", "unknown")
        value = m.get("value", "N/A")
        captured = m.get("captured_at", "N/A")

        result.append(f"- {captured}: **{value} {unit}**")

    return "\n".join(result)


@mcp.tool()
async def query_safecast(endpoint: str, params: dict | None = None) -> dict:
    """Make a raw query to the Safecast API.

    Args:
        endpoint: API endpoint path (e.g., '/measurements.json', '/devices.json')
        params: Optional query parameters as a dictionary

    Returns:
        Raw JSON response from Safecast API
    """
    url = f"{SAFECAST_BASE}{endpoint}"
    return await fetch_json(url, params=params)
