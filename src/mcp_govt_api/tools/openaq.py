from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json


OPENAQ_BASE = "https://api.openaq.org/v3"

# Common pollutant parameter IDs in OpenAQ v3
POLLUTANT_NAMES = {
    1: "PM10",
    2: "PM2.5",
    3: "O3",
    7: "NO2",
    8: "CO",
    9: "SO2",
}


@mcp.tool()
async def get_air_quality(
    latitude: float, longitude: float, radius_km: int = 25
) -> str:
    """Get current air quality measurements near a location.

    Args:
        latitude: Latitude of the location (e.g., 40.7128 for New York City)
        longitude: Longitude of the location (e.g., -74.0060 for New York City)
        radius_km: Search radius in kilometers (default: 25)

    Returns:
        Latest air quality measurements from nearby monitoring stations,
        showing pollutant name, value, unit, and station name
    """
    radius_m = radius_km * 1000
    url = f"{OPENAQ_BASE}/locations"
    params = {
        "coordinates": f"{latitude},{longitude}",
        "radius": str(radius_m),
        "limit": "10",
    }

    data = await fetch_json(url, params=params)
    locations = data.get("results", [])

    if not locations:
        return (
            f"No air quality monitoring stations found within {radius_km}km "
            f"of {latitude}, {longitude}"
        )

    result = [
        f"Air quality near {latitude}, {longitude} "
        f"(within {radius_km}km):\n"
    ]

    for loc in locations[:10]:
        name = loc.get("name") or loc.get("locality") or "Unknown station"
        country = loc.get("country", {}).get("code", "")
        distance_m = loc.get("distance")
        distance_str = (
            f"{distance_m / 1000:.1f}km away" if distance_m is not None else ""
        )

        sensors = loc.get("sensors", [])
        if not sensors:
            continue

        header_parts = [f"**{name}**"]
        if country:
            header_parts.append(f"({country})")
        if distance_str:
            header_parts.append(f"- {distance_str}")
        header = " ".join(header_parts)

        readings = []
        for sensor in sensors:
            parameter = sensor.get("parameter", {})
            pollutant = parameter.get("displayName") or parameter.get("name", "Unknown")
            latest = sensor.get("latest", {})
            value = latest.get("value")
            unit = parameter.get("units", "")
            if value is not None:
                readings.append(f"  - {pollutant}: **{value} {unit}**")

        if readings:
            result.append(header + "\n" + "\n".join(readings))

    if len(result) == 1:
        return (
            f"Stations found near {latitude}, {longitude} but no current "
            f"measurements are available"
        )

    return "\n\n---\n\n".join(result)


@mcp.tool()
async def get_air_quality_history(
    location_id: int,
    date_from: str = "",
    date_to: str = "",
) -> str:
    """Get historical air quality measurements for a specific monitoring station.

    Args:
        location_id: OpenAQ location ID (obtain from get_air_quality results
            or query_openaq('/locations'))
        date_from: Start date in ISO 8601 format (e.g., '2024-01-01T00:00:00Z').
            Defaults to the last 7 days if omitted.
        date_to: End date in ISO 8601 format (e.g., '2024-01-31T23:59:59Z').
            Defaults to now if omitted.

    Returns:
        Historical air quality measurements for the location, ordered by time
    """
    url = f"{OPENAQ_BASE}/locations/{location_id}/measurements"
    params: dict[str, str] = {"limit": "15"}

    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    data = await fetch_json(url, params=params)
    measurements = data.get("results", [])

    if not measurements:
        date_range = ""
        if date_from or date_to:
            date_range = f" between {date_from or 'start'} and {date_to or 'now'}"
        return (
            f"No measurements found for location ID {location_id}{date_range}"
        )

    result = [f"Air quality history for location ID {location_id}:\n"]

    for m in measurements[:15]:
        parameter = m.get("parameter", {})
        pollutant = parameter.get("displayName") or parameter.get("name", "Unknown")
        value = m.get("value", "N/A")
        unit = parameter.get("units", "")
        period = m.get("period", {})
        timestamp = (
            period.get("datetimeFrom", {}).get("utc")
            or m.get("date", {}).get("utc", "N/A")
        )

        result.append(f"- {timestamp}: **{pollutant} {value} {unit}**")

    return "\n".join(result)


@mcp.tool()
async def query_openaq(endpoint: str, params: dict | None = None) -> dict:
    """Make a raw query to the OpenAQ v3 API.

    Args:
        endpoint: API endpoint path (e.g., '/locations', '/parameters',
            '/locations/12345/measurements')
        params: Optional query parameters as a dictionary (e.g.,
            {"limit": "10", "coordinates": "40.7,-74.0", "radius": "5000"})

    Returns:
        Raw JSON response from OpenAQ API
    """
    url = f"{OPENAQ_BASE}{endpoint}"
    return await fetch_json(url, params=params)
