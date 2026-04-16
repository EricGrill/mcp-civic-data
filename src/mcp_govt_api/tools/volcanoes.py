"""USGS Volcano Hazards Program tools.

Provides access to USGS volcano monitoring data including current alert
levels, active volcano information, and volcano database search.

API docs: https://volcanoes.usgs.gov/vsc/api/volcanoApi/
"""

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

VOLCANO_API_BASE = "https://volcanoes.usgs.gov/vsc/api/volcanoApi"


def _format_alert_feature(feature: dict) -> str:
    """Format a single GeoJSON volcano alert feature into a readable string."""
    props = feature.get("properties", {})
    coords = feature.get("geometry", {}).get("coordinates", [None, None])

    name = props.get("volcanoName", "Unknown")
    alert_level = props.get("alertLevel", "Unknown")
    color_code = props.get("colorCode", "Unknown")
    observatory = props.get("obsCode", "")
    date = props.get("alertDate", "N/A")

    lines = [
        f"**{name}**",
        f"Alert Level: {alert_level}",
        f"Aviation Color Code: {color_code}",
    ]

    if date and date != "N/A":
        lines.append(f"Alert Date: {date}")
    if observatory:
        lines.append(f"Observatory: {observatory}")
    if coords[0] is not None and coords[1] is not None:
        lines.append(f"Location: {coords[1]:.4f}, {coords[0]:.4f}")

    return "\n".join(lines)


def _format_volcano_feature(feature: dict) -> str:
    """Format a single GeoJSON volcano feature into a readable string."""
    props = feature.get("properties", {})
    coords = feature.get("geometry", {}).get("coordinates", [None, None])

    name = props.get("vName", "Unknown")
    subregion = props.get("subregion", "")
    elev_m = props.get("elev", None)
    v_type = props.get("vType", "")
    alert_level = props.get("alertLevel", "")
    color_code = props.get("colorCode", "")

    lines = [f"**{name}**"]

    if subregion:
        lines.append(f"Region: {subregion}")
    if v_type:
        lines.append(f"Type: {v_type}")
    if elev_m is not None:
        lines.append(f"Elevation: {elev_m} m")
    if alert_level:
        lines.append(f"Alert Level: {alert_level}")
    if color_code:
        lines.append(f"Aviation Color Code: {color_code}")
    if coords[0] is not None and coords[1] is not None:
        lines.append(f"Location: {coords[1]:.4f}, {coords[0]:.4f}")

    return "\n".join(lines)


@mcp.tool()
async def get_active_volcanoes(region: str = "", limit: int = 20) -> str:
    """Get currently monitored volcanoes in the United States with their status.

    Retrieves volcano data from the USGS Volcano Hazards Program GeoJSON
    feed, which covers US volcanoes including Alaska, Hawaii, and the
    Cascades.

    Args:
        region: Optional region filter (e.g., 'Alaska', 'Hawaii', 'Cascades').
            Matches against the subregion field, case-insensitive.
        limit: Maximum number of volcanoes to return (default: 20, max: 100)

    Returns:
        List of monitored volcanoes with alert levels, types, and locations
    """
    if limit < 1:
        limit = 20
    if limit > 100:
        limit = 100

    url = f"{VOLCANO_API_BASE}/volcanoesGeoJSON"
    data = await fetch_json(url)

    features = data.get("features", [])
    if not features:
        return "No volcano data available from USGS at this time."

    # Filter by region if provided
    if region:
        region_lower = region.lower()
        features = [
            f for f in features
            if region_lower in (f.get("properties", {}).get("subregion", "") or "").lower()
        ]
        if not features:
            return f"No volcanoes found matching region '{region}'."

    # Sort: elevated alerts first, then alphabetically
    alert_priority = {"WARNING": 0, "WATCH": 1, "ADVISORY": 2, "NORMAL": 3}
    features.sort(
        key=lambda f: (
            alert_priority.get(
                (f.get("properties", {}).get("alertLevel") or "").upper(), 4
            ),
            f.get("properties", {}).get("vName", ""),
        )
    )

    features = features[:limit]

    header = "USGS Monitored Volcanoes"
    if region:
        header += f" - {region}"
    header += f" ({len(features)} result(s)):\n"

    result = [header]
    for feature in features:
        result.append(_format_volcano_feature(feature))

    return "\n\n---\n\n".join(result)


@mcp.tool()
async def get_volcano_alerts() -> str:
    """Get current USGS volcano alert levels and aviation color codes.

    Returns all volcanoes that currently have elevated alert status
    (above NORMAL). Includes alert level, aviation color code, and
    the date the alert was issued.

    Returns:
        Current volcano alerts ordered by severity, or a message
        indicating no elevated alerts are active
    """
    url = f"{VOLCANO_API_BASE}/alertsGeoJSON"
    data = await fetch_json(url)

    features = data.get("features", [])
    if not features:
        return "No current volcano alerts from USGS."

    # Filter to only elevated alerts (not NORMAL)
    elevated = [
        f for f in features
        if (f.get("properties", {}).get("alertLevel") or "").upper() != "NORMAL"
    ]

    if not elevated:
        return (
            f"All {len(features)} monitored volcanoes are at NORMAL alert level. "
            "No elevated volcanic activity at this time."
        )

    # Sort by severity
    alert_priority = {"WARNING": 0, "WATCH": 1, "ADVISORY": 2}
    elevated.sort(
        key=lambda f: alert_priority.get(
            (f.get("properties", {}).get("alertLevel") or "").upper(), 3
        )
    )

    result = [f"USGS Volcano Alerts - {len(elevated)} elevated alert(s):\n"]
    for feature in elevated:
        result.append(_format_alert_feature(feature))

    return "\n\n---\n\n".join(result)


@mcp.tool()
async def search_volcanoes(
    query: str = "", country: str = "", volcano_type: str = ""
) -> str:
    """Search the USGS volcano database by name, country, or type.

    Searches the USGS Volcano Hazards Program database of monitored
    US volcanoes. For international volcanoes, use the Smithsonian
    Global Volcanism Program directly.

    Args:
        query: Search term to match against volcano name (case-insensitive)
        country: Not used for USGS (US-only); included for API compatibility
        volcano_type: Filter by volcano type (e.g., 'Stratovolcano', 'Shield',
            'Caldera', 'Cinder cone'). Case-insensitive partial match.

    Returns:
        Matching volcanoes with type, elevation, alert status, and location
    """
    url = f"{VOLCANO_API_BASE}/volcanoesGeoJSON"
    data = await fetch_json(url)

    features = data.get("features", [])
    if not features:
        return "No volcano data available from USGS at this time."

    # Apply filters
    if query:
        query_lower = query.lower()
        features = [
            f for f in features
            if query_lower in (f.get("properties", {}).get("vName", "") or "").lower()
        ]

    if volcano_type:
        type_lower = volcano_type.lower()
        features = [
            f for f in features
            if type_lower in (f.get("properties", {}).get("vType", "") or "").lower()
        ]

    if not features:
        parts = []
        if query:
            parts.append(f"name '{query}'")
        if volcano_type:
            parts.append(f"type '{volcano_type}'")
        filter_desc = " and ".join(parts) if parts else "the given criteria"
        return f"No volcanoes found matching {filter_desc}."

    # Sort alphabetically
    features.sort(key=lambda f: f.get("properties", {}).get("vName", ""))

    # Limit results
    total = len(features)
    features = features[:25]

    header = "USGS Volcano Search Results"
    if query:
        header += f" for '{query}'"
    if volcano_type:
        header += f" (type: {volcano_type})"
    shown = len(features)
    header += f" - {shown} of {total} result(s):\n"

    result = [header]
    for feature in features:
        result.append(_format_volcano_feature(feature))

    return "\n\n---\n\n".join(result)
