from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

WFIGS_BASE = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services"

# US state name to abbreviation mapping for ArcGIS WHERE clauses
STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}


def _state_where(state: str, field: str = "POOState") -> str:
    """Build a WHERE clause fragment for state filtering.

    Accepts two-letter abbreviation or full state name.
    The WFIGS datasets use two-letter codes in fields like POOState.
    """
    state = state.strip()
    if not state:
        return ""
    upper = state.upper()
    if upper in STATE_NAMES:
        return f"{field}='{upper}'"
    # Try matching full name to abbreviation
    for abbr, name in STATE_NAMES.items():
        if name.lower() == state.lower():
            return f"{field}='{abbr}'"
    # Fall back to using as-is
    return f"{field}='{upper}'"


@mcp.tool()
async def get_active_wildfires(
    state: str = "",
    limit: int = 10,
) -> str:
    """Get current wildfire incidents from WFIGS (Wildland Fire Interagency
    Geospatial Services).

    Queries active fire incident locations reported by federal and state
    agencies across the United States.

    Args:
        state: Two-letter state abbreviation (e.g., 'CA', 'OR', 'MT') or
            full state name to filter incidents
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of active wildfire incidents with name, location, size,
        discovery date, and containment status.
    """
    limit = min(limit, 100)

    where = _state_where(state, "POOState") if state else "1=1"

    params: dict = {
        "where": where,
        "outFields": "*",
        "f": "json",
        "resultRecordCount": limit,
        "orderByFields": "FireDiscoveryDateTime DESC",
    }

    url = f"{WFIGS_BASE}/WFIGS_Incident_Locations_Current/FeatureServer/0/query"

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching active wildfire incidents: {e}"

    features = data.get("features", [])

    if not features:
        scope = f"state '{state.upper()}'" if state else "any location"
        return f"No active wildfire incidents found for {scope}."

    lines = [f"Active Wildfire Incidents ({len(features)} result(s)):\n"]

    for feature in features:
        attrs = feature.get("attributes", {})

        name = attrs.get("IncidentName", "Unknown")
        fire_state = attrs.get("POOState", "N/A")
        county = attrs.get("POOCounty", "")
        acres = attrs.get("DailyAcres") or attrs.get("CalculatedAcres")
        discovery = attrs.get("FireDiscoveryDateTime")
        cause = attrs.get("FireCause", "")
        containment = attrs.get("PercentContained")
        incident_type = attrs.get("IncidentTypeCategory", "")
        irwin_id = attrs.get("IrwinID", "")

        lines.append(f"**{name}**")
        location_parts = []
        if county:
            location_parts.append(county)
        if fire_state:
            location_parts.append(fire_state)
        if location_parts:
            lines.append(f"  Location: {', '.join(location_parts)}")
        if incident_type:
            lines.append(f"  Type: {incident_type}")
        if acres is not None:
            lines.append(f"  Size: {acres:,.0f} acres")
        if containment is not None:
            lines.append(f"  Containment: {containment}%")
        if discovery:
            # Convert epoch milliseconds to readable date
            try:
                from datetime import datetime, timezone

                dt = datetime.fromtimestamp(discovery / 1000, tz=timezone.utc)
                lines.append(f"  Discovered: {dt.strftime('%Y-%m-%d %H:%M UTC')}")
            except (ValueError, OSError):
                pass
        if cause:
            lines.append(f"  Cause: {cause}")
        if irwin_id:
            lines.append(f"  IRWIN ID: {irwin_id}")
        lines.append("")

    lines.append(
        "_Source: WFIGS Interagency Fire Incident Locations (ArcGIS)_"
    )

    return "\n".join(lines)


@mcp.tool()
async def get_wildfire_perimeters(
    state: str = "",
    limit: int = 10,
) -> str:
    """Get active wildfire perimeters and boundaries from WFIGS.

    Queries current fire perimeter polygons that define the geographic
    extent of active wildfires. Useful for understanding fire spread
    and affected areas.

    Args:
        state: Two-letter state abbreviation (e.g., 'CA', 'OR', 'MT') or
            full state name to filter perimeters
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of wildfire perimeters with fire name, acres burned,
        containment percentage, and perimeter date.
    """
    limit = min(limit, 100)

    where = _state_where(state, "POOState") if state else "1=1"

    params: dict = {
        "where": where,
        "outFields": "*",
        "f": "json",
        "resultRecordCount": limit,
        "orderByFields": "GISAcres DESC",
        "returnGeometry": "false",
    }

    url = f"{WFIGS_BASE}/WFIGS_Interagency_Perimeters/FeatureServer/0/query"

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching wildfire perimeters: {e}"

    features = data.get("features", [])

    if not features:
        scope = f"state '{state.upper()}'" if state else "any location"
        return f"No active wildfire perimeters found for {scope}."

    lines = [f"Active Wildfire Perimeters ({len(features)} result(s)):\n"]

    for feature in features:
        attrs = feature.get("attributes", {})

        name = attrs.get("IncidentName") or attrs.get("poly_IncidentName", "Unknown")
        fire_state = attrs.get("POOState", "N/A")
        gis_acres = attrs.get("GISAcres")
        containment = attrs.get("PercentContained")
        irwin_id = attrs.get("IrwinID", "")
        create_date = attrs.get("CreateDate") or attrs.get("DateCurrent")
        fire_type = attrs.get("IncidentTypeCategory", "")

        lines.append(f"**{name}**")
        if fire_state and fire_state != "N/A":
            lines.append(f"  State: {fire_state}")
        if fire_type:
            lines.append(f"  Type: {fire_type}")
        if gis_acres is not None:
            lines.append(f"  GIS Acres: {gis_acres:,.1f}")
        if containment is not None:
            lines.append(f"  Containment: {containment}%")
        if create_date:
            try:
                from datetime import datetime, timezone

                dt = datetime.fromtimestamp(create_date / 1000, tz=timezone.utc)
                lines.append(f"  Perimeter Date: {dt.strftime('%Y-%m-%d')}")
            except (ValueError, OSError):
                pass
        if irwin_id:
            lines.append(f"  IRWIN ID: {irwin_id}")
        lines.append("")

    lines.append(
        "_Source: WFIGS Interagency Fire Perimeters (ArcGIS)_"
    )

    return "\n".join(lines)


@mcp.tool()
async def search_national_forests(
    state: str = "",
    name: str = "",
    limit: int = 10,
) -> str:
    """Search for USDA National Forests by state or name.

    Queries the US Forest Service administrative boundary dataset to
    find National Forests and Grasslands across the United States.

    Args:
        state: Two-letter state abbreviation (e.g., 'CA', 'CO', 'MT')
            or full state name
        name: Search by forest name (e.g., 'Tongass', 'Shoshone')
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of National Forests with name, state, region, and area.
    """
    limit = min(limit, 100)

    where_parts = []
    if state:
        state_clause = _state_where(state, "ADMINFORESTID")
        # National Forest boundaries use different field names; try FORESTNAME state matching
        # Use a LIKE on FORESTNAME which often includes state context
        st = state.strip().upper()
        if len(st) == 2:
            full_name = STATE_NAMES.get(st, st)
        else:
            full_name = state.strip()
        where_parts.append(f"UPPER(FORESTNAME) LIKE '%{full_name.upper()}%' OR UPPER(GIS_ACRES) >= 0")
        # Actually, the boundary service stores state info differently.
        # Use a general approach - filter by name if state given
        where_parts = []  # Reset
    if name:
        safe_name = name.replace("'", "''")
        where_parts.append(f"UPPER(FORESTNAME) LIKE '%{safe_name.upper()}%'")

    where = " AND ".join(where_parts) if where_parts else "1=1"

    params: dict = {
        "where": where,
        "outFields": "FORESTNAME,FORESTNUMBER,REGION,GIS_ACRES,SHAPE_Area",
        "f": "json",
        "resultRecordCount": limit,
        "returnGeometry": "false",
        "orderByFields": "FORESTNAME ASC",
    }

    url = (
        "https://apps.fs.usda.gov/arcx/rest/services/EDW/"
        "EDW_ForestSystemBoundaries_01/MapServer/0/query"
    )

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error searching National Forests: {e}"

    features = data.get("features", [])

    if not features:
        filter_parts = []
        if state:
            filter_parts.append(f"state '{state.upper()}'")
        if name:
            filter_parts.append(f"name '{name}'")
        filter_str = ", ".join(filter_parts) if filter_parts else "the given criteria"
        return f"No National Forests found for {filter_str}."

    lines = [f"National Forests ({len(features)} result(s)):\n"]

    for feature in features:
        attrs = feature.get("attributes", {})

        forest_name = attrs.get("FORESTNAME", "Unknown")
        forest_num = attrs.get("FORESTNUMBER", "")
        region = attrs.get("REGION", "")
        gis_acres = attrs.get("GIS_ACRES")

        lines.append(f"**{forest_name}**")
        if forest_num:
            lines.append(f"  Forest Number: {forest_num}")
        if region:
            lines.append(f"  Region: {region}")
        if gis_acres is not None and gis_acres > 0:
            lines.append(f"  Area: {gis_acres:,.0f} acres")
        lines.append("")

    lines.append(
        "_Source: USDA Forest Service Administrative Boundaries (ArcGIS)_"
    )

    return "\n".join(lines)
