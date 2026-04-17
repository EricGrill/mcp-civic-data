"""Submarine cable data tools using the Submarine Cable Map API.

Provides tools to search and explore the global submarine fiber-optic
cable network, including cable details, landing points, and country
connectivity information.

API docs: https://www.submarinecablemap.com/api/v3/
"""

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json
from mcp_govt_api.utils.validation import validate_limit

BASE = "https://www.submarinecablemap.com/api/v3"


@mcp.tool()
async def search_submarine_cables(query: str = "", limit: int = 20) -> str:
    """Search or list submarine fiber-optic cables worldwide.

    Returns a list of submarine cables from the Submarine Cable Map.
    Optionally filter by name using a search query.

    Args:
        query: Optional search string to filter cables by name
            (case-insensitive). Leave empty to list all cables.
        limit: Maximum number of results to return (default: 20, max: 100).

    Returns:
        Formatted list of submarine cables with name, cable ID, RFS
        (ready-for-service) year, and length where available.
    """
    limit = validate_limit(limit, max_val=100, default=20)

    try:
        data = await fetch_json(f"{BASE}/cable/all.json")
    except Exception as e:
        return f"Error fetching submarine cable data: {e}"

    if not data or not isinstance(data, list):
        return "No submarine cable data available."

    cables = data

    # Filter by query if provided
    if query:
        query_lower = query.lower()
        cables = [
            c for c in cables
            if query_lower in c.get("name", "").lower()
        ]

    if not cables:
        return f"No submarine cables found matching '{query}'."

    cables = cables[:limit]

    lines: list[str] = [
        f"**Submarine Cables** (showing {len(cables)} result(s)):\n"
    ]

    for cable in cables:
        name = cable.get("name", "Unknown")
        cable_id = cable.get("id", "N/A")
        rfs = cable.get("rfs", "N/A")
        length = cable.get("length", "")

        entry = f"- **{name}**\n  ID: `{cable_id}`"
        if rfs and rfs != "N/A":
            entry += f" | RFS: {rfs}"
        if length:
            entry += f" | Length: {length} km"
        lines.append(entry)

    return "\n".join(lines)


@mcp.tool()
async def get_submarine_cable_details(cable_id: str) -> str:
    """Get detailed information about a specific submarine cable.

    Fetches full details for a cable including its landing points,
    owners, length, ready-for-service date, and route information.

    Args:
        cable_id: The unique cable identifier (e.g., 'sea-me-we-5',
            'africa-coast-to-europe'). Use search_submarine_cables
            to find cable IDs.

    Returns:
        Detailed cable information including owners, landing points,
        RFS date, length, and URL.
    """
    if not cable_id or not cable_id.strip():
        return "Error: cable_id is required."

    try:
        data = await fetch_json(f"{BASE}/cable/{cable_id}.json")
    except Exception as e:
        return f"Error fetching cable details: {e}"

    if not data or not isinstance(data, dict):
        return f"No details found for cable '{cable_id}'."

    name = data.get("name", "Unknown")
    rfs = data.get("rfs", "N/A")
    length = data.get("length", "N/A")
    cable_url = data.get("url", "")
    owners = data.get("owners", "")
    notes = data.get("notes", "")

    lines: list[str] = [f"**{name}**\n"]

    lines.append(f"- **Cable ID:** `{cable_id}`")
    if rfs and rfs != "N/A":
        lines.append(f"- **RFS (Ready for Service):** {rfs}")
    if length and length != "N/A":
        lines.append(f"- **Length:** {length} km")
    if owners:
        lines.append(f"- **Owners:** {owners}")
    if cable_url:
        lines.append(f"- **URL:** {cable_url}")
    if notes:
        # Trim long notes
        if len(notes) > 500:
            notes = notes[:500] + "...[truncated]"
        lines.append(f"- **Notes:** {notes}")

    # Landing points
    landing_points = data.get("landing_points", [])
    if landing_points:
        lines.append(f"\n**Landing Points** ({len(landing_points)}):")
        for lp in landing_points:
            lp_name = lp.get("name", "Unknown")
            country = lp.get("country", "")
            entry = f"  - {lp_name}"
            if country:
                entry += f" ({country})"
            lines.append(entry)

    return "\n".join(lines)


@mcp.tool()
async def get_cable_landing_points(
    country: str = "", limit: int = 20
) -> str:
    """Get submarine cable landing points worldwide.

    Returns a list of locations where submarine cables come ashore.
    Optionally filter by country name.

    Args:
        country: Optional country name to filter results
            (case-insensitive, partial match). Leave empty to list all.
        limit: Maximum number of results to return (default: 20, max: 100).

    Returns:
        List of cable landing points with name, country, and
        associated cable count.
    """
    limit = validate_limit(limit, max_val=100, default=20)

    try:
        data = await fetch_json(f"{BASE}/landing-point/all.json")
    except Exception as e:
        return f"Error fetching landing point data: {e}"

    if not data or not isinstance(data, list):
        return "No landing point data available."

    points = data

    # Filter by country if provided
    if country:
        country_lower = country.lower()
        points = [
            p for p in points
            if country_lower in p.get("country", "").lower()
        ]

    if not points:
        if country:
            return f"No landing points found for country '{country}'."
        return "No landing points available."

    points = points[:limit]

    header = f"**Cable Landing Points** (showing {len(points)} result(s))"
    if country:
        header += f" for '{country}'"
    header += ":\n"

    lines: list[str] = [header]

    for point in points:
        name = point.get("name", "Unknown")
        pt_country = point.get("country", "N/A")
        lp_id = point.get("id", "N/A")
        cable_count = len(point.get("cables", []))

        entry = f"- **{name}** ({pt_country})"
        entry += f"\n  ID: `{lp_id}`"
        if cable_count:
            entry += f" | Cables: {cable_count}"
        lines.append(entry)

    return "\n".join(lines)
