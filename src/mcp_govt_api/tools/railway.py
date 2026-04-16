from urllib.parse import quote

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"


async def _overpass_query(query: str) -> dict:
    """Execute an Overpass API query."""
    return await fetch_json(f"{OVERPASS_API_URL}?data={quote(query)}")


def _format_station(element: dict) -> str:
    """Format a single railway station element into a readable string."""
    tags = element.get("tags", {})
    name = tags.get("name", "Unnamed station")
    operator = tags.get("operator", "Unknown operator")
    network = tags.get("network", "")
    lat = element.get("lat", "")
    lon = element.get("lon", "")
    platforms = tags.get("platforms", "")
    wheelchair = tags.get("wheelchair", "")
    wikidata = tags.get("wikidata", "")

    lines = [f"**{name}**"]
    lines.append(f"  Operator: {operator}")
    if network:
        lines.append(f"  Network: {network}")
    if platforms:
        lines.append(f"  Platforms: {platforms}")
    if wheelchair:
        lines.append(f"  Wheelchair access: {wheelchair}")
    if wikidata:
        lines.append(f"  Wikidata: {wikidata}")
    if lat and lon:
        lines.append(f"  Location: {lat}, {lon}")
    return "\n".join(lines)


def _format_railway_line(element: dict) -> str:
    """Format a single railway line/way element into a readable string."""
    tags = element.get("tags", {})
    name = tags.get("name", "Unnamed line")
    operator = tags.get("operator", "Unknown operator")
    usage = tags.get("usage", "")
    electrified = tags.get("electrified", "")
    gauge = tags.get("gauge", "")
    maxspeed = tags.get("maxspeed", "")
    service = tags.get("service", "")

    lines = [f"**{name}**"]
    lines.append(f"  Operator: {operator}")
    if usage:
        lines.append(f"  Usage: {usage}")
    if service:
        lines.append(f"  Service: {service}")
    if electrified:
        lines.append(f"  Electrified: {electrified}")
    if gauge:
        lines.append(f"  Gauge: {gauge}")
    if maxspeed:
        lines.append(f"  Max speed: {maxspeed}")
    return "\n".join(lines)


@mcp.tool()
async def find_railway_stations(
    lat: float,
    lon: float,
    radius: int = 5000,
    limit: int = 20,
) -> str:
    """Find railway stations near a geographic location using OpenStreetMap data.

    Queries the Overpass API (OpenStreetMap) for nodes tagged as railway
    stations within the specified radius.

    Args:
        lat: Latitude of the search center (e.g., 51.5074 for London).
        lon: Longitude of the search center (e.g., -0.1278 for London).
        radius: Search radius in meters (default: 5000).
        limit: Maximum number of stations to return (default: 20).

    Returns:
        Formatted list of nearby railway stations with name, operator,
        network, platform count, and location details.
    """
    try:
        limit = min(limit, 50)
        query = (
            f'[out:json];node["railway"="station"]'
            f"(around:{radius},{lat},{lon});"
            f"out body {limit};"
        )
        data = await _overpass_query(query)
        elements = data.get("elements", [])

        if not elements:
            return (
                f"No railway stations found within {radius}m "
                f"of ({lat}, {lon})."
            )

        result = [
            f"## Railway Stations near ({lat}, {lon})\n"
            f"Found {len(elements)} station(s) within {radius}m:\n"
        ]
        for element in elements:
            result.append(_format_station(element))

        return "\n\n".join(result)

    except Exception as e:
        return f"Error searching for railway stations: {e}"


@mcp.tool()
async def get_railway_lines(
    lat: float,
    lon: float,
    radius: int = 10000,
    limit: int = 20,
) -> str:
    """Get railway lines and tracks near a geographic location using OpenStreetMap data.

    Queries the Overpass API (OpenStreetMap) for ways tagged as railway
    tracks within the specified radius.

    Args:
        lat: Latitude of the search center (e.g., 48.8566 for Paris).
        lon: Longitude of the search center (e.g., 2.3522 for Paris).
        radius: Search radius in meters (default: 10000).
        limit: Maximum number of lines to return (default: 20).

    Returns:
        Formatted list of nearby railway lines with name, operator,
        usage type, electrification, gauge, and speed details.
    """
    try:
        limit = min(limit, 50)
        query = (
            f'[out:json];way["railway"="rail"]'
            f"(around:{radius},{lat},{lon});"
            f"out body {limit};"
        )
        data = await _overpass_query(query)
        elements = data.get("elements", [])

        if not elements:
            return (
                f"No railway lines found within {radius}m "
                f"of ({lat}, {lon})."
            )

        result = [
            f"## Railway Lines near ({lat}, {lon})\n"
            f"Found {len(elements)} line(s) within {radius}m:\n"
        ]
        for element in elements:
            result.append(_format_railway_line(element))

        return "\n\n".join(result)

    except Exception as e:
        return f"Error searching for railway lines: {e}"


@mcp.tool()
async def search_railway_stations_by_name(
    name: str,
    country_code: str = "",
    limit: int = 10,
) -> str:
    """Search for railway stations by name using OpenStreetMap data.

    Performs a case-insensitive regex search across all railway stations
    in the OpenStreetMap database. Optionally filter by country using an
    ISO 3166-1 alpha-2 country code.

    Args:
        name: Station name or partial name to search for (e.g., 'Penn Station').
        country_code: Optional ISO country code to restrict results (e.g., 'US', 'DE', 'GB').
        limit: Maximum number of results to return (default: 10).

    Returns:
        Formatted list of matching railway stations with name, operator,
        network, and location details.
    """
    try:
        limit = min(limit, 50)

        if country_code:
            cc = country_code.strip().upper()
            query = (
                f"[out:json];"
                f'area["ISO3166-1"="{cc}"]->.searchArea;'
                f'node["railway"="station"]["name"~"{name}",i]'
                f"(area.searchArea);"
                f"out body {limit};"
            )
        else:
            query = (
                f'[out:json];node["railway"="station"]'
                f'["name"~"{name}",i];'
                f"out body {limit};"
            )

        data = await _overpass_query(query)
        elements = data.get("elements", [])

        if not elements:
            location_msg = f" in {country_code.upper()}" if country_code else ""
            return f'No railway stations matching "{name}"{location_msg} found.'

        country_msg = f" in {country_code.upper()}" if country_code else ""
        result = [
            f'## Railway Stations matching "{name}"{country_msg}\n'
            f"Found {len(elements)} result(s):\n"
        ]
        for element in elements:
            result.append(_format_station(element))

        return "\n\n".join(result)

    except Exception as e:
        return f"Error searching for railway stations by name: {e}"
