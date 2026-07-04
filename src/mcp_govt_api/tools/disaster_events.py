"""ReliefWeb global disaster and emergency event tools.

Provides access to the ReliefWeb API (https://api.reliefweb.int/v1/)
for querying global disaster events, detailed disaster information,
and situation reports. No API key required.
"""

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json
from mcp_govt_api.utils.validation import validate_limit

BASE_URL = "https://api.reliefweb.int/v1"
APP_NAME = "mcp-civic-data"

DISASTER_FIELDS = [
    "name",
    "date",
    "country",
    "type",
    "status",
    "glide",
]


def _build_fields_params(fields: list[str]) -> dict[str, str]:
    """Build query parameters for ReliefWeb field selection."""
    params: dict[str, str] = {}
    for field in fields:
        params["fields[include][]"] = field  # httpx handles list params
    return params


def _build_fields_list(fields: list[str]) -> list[tuple[str, str]]:
    """Build list of tuples for ReliefWeb field selection (supports duplicate keys)."""
    return [("fields[include][]", field) for field in fields]


@mcp.tool()
async def get_recent_disasters(
    country: str = "",
    type: str = "",
    limit: int = 15,
) -> str:
    """Get recent global disaster events from ReliefWeb.

    Queries the ReliefWeb disasters endpoint for recent natural disasters,
    epidemics, and other emergency events worldwide.

    Args:
        country: Filter by country name (e.g., 'Haiti', 'Japan', 'Philippines')
        type: Filter by disaster type (e.g., 'earthquake', 'flood', 'epidemic',
            'drought', 'cyclone', 'volcano', 'wildfire', 'cold wave',
            'heat wave', 'storm surge', 'tsunami', 'landslide')
        limit: Maximum number of results to return (default: 15, max: 50)

    Returns:
        List of recent disasters with name, date, country, type, and status.
    """
    limit = validate_limit(limit, max_val=50, default=15)

    params: list[tuple[str, str]] = [
        ("appname", APP_NAME),
        ("limit", str(limit)),
        ("sort[]", "date:desc"),
    ]

    # Add field selection
    params.extend(_build_fields_list(DISASTER_FIELDS))

    # Add filters
    filters: list[dict] = []
    if country:
        filters.append({
            "field": "country.name",
            "value": country,
        })
    if type:
        filters.append({
            "field": "type.name",
            "value": type,
        })

    # Build URL with filters
    url = f"{BASE_URL}/disasters"

    try:
        # Build the full URL with field parameters
        field_params = "&".join(
            f"fields[include][]={f}" for f in DISASTER_FIELDS
        )
        filter_params = ""
        if country:
            filter_params += f'&filter[operator]=AND&filter[conditions][0][field]=country.name&filter[conditions][0][value]={country}'
            if type:
                filter_params += f'&filter[conditions][1][field]=type.name&filter[conditions][1][value]={type}'
        elif type:
            filter_params += f'&filter[field]=type.name&filter[value]={type}'

        full_url = (
            f"{url}?appname={APP_NAME}&limit={limit}"
            f"&sort[]=date:desc&{field_params}{filter_params}"
        )

        data = await fetch_json(full_url)
    except Exception as e:
        return f"Error fetching disasters from ReliefWeb: {e}"

    items = data.get("data", [])

    if not items:
        filter_parts = []
        if country:
            filter_parts.append(f"country '{country}'")
        if type:
            filter_parts.append(f"type '{type}'")
        filter_str = ", ".join(filter_parts) if filter_parts else "the given criteria"
        return f"No disasters found for {filter_str}."

    lines = [f"## Recent Disasters ({len(items)} result(s))\n"]

    for item in items:
        fields = item.get("fields", {})
        disaster_id = item.get("id", "N/A")
        name = fields.get("name", "Unknown")
        date_info = fields.get("date", {})
        date_str = ""
        if isinstance(date_info, dict):
            date_str = date_info.get("created", "")
        elif isinstance(date_info, str):
            date_str = date_info
        if date_str and len(date_str) >= 10:
            date_str = date_str[:10]

        # Country info
        countries = fields.get("country", [])
        if isinstance(countries, list):
            country_names = [c.get("name", "") for c in countries if isinstance(c, dict)]
            country_str = ", ".join(country_names) if country_names else "N/A"
        else:
            country_str = "N/A"

        # Type info
        types = fields.get("type", [])
        if isinstance(types, list):
            type_names = [t.get("name", "") for t in types if isinstance(t, dict)]
            type_str = ", ".join(type_names) if type_names else "N/A"
        else:
            type_str = "N/A"

        status = fields.get("status", "N/A")
        glide = fields.get("glide", "")

        lines.append(f"### {name}")
        lines.append(f"- **ID:** {disaster_id}")
        lines.append(f"- **Date:** {date_str}")
        lines.append(f"- **Country:** {country_str}")
        lines.append(f"- **Type:** {type_str}")
        lines.append(f"- **Status:** {status}")
        if glide:
            lines.append(f"- **GLIDE:** {glide}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def get_disaster_details(disaster_id: int) -> str:
    """Get detailed information about a specific disaster from ReliefWeb.

    Args:
        disaster_id: The ReliefWeb disaster ID number

    Returns:
        Detailed disaster information including name, date, affected countries,
        disaster type, status, description, and related links.
    """
    url = f"{BASE_URL}/disasters/{disaster_id}"

    try:
        data = await fetch_json(f"{url}?appname={APP_NAME}")
    except Exception as e:
        return f"Error fetching disaster details: {e}"

    items = data.get("data", [])

    if not items:
        return f"No disaster found with ID {disaster_id}."

    item = items[0] if isinstance(items, list) else items
    fields = item.get("fields", {})

    name = fields.get("name", "Unknown")
    description = fields.get("description", "")
    status = fields.get("status", "N/A")
    glide = fields.get("glide", "")
    url_field = fields.get("url", "")
    primary_country = fields.get("primary_country", {})
    primary_country_name = primary_country.get("name", "N/A") if isinstance(primary_country, dict) else "N/A"

    # Date info
    date_info = fields.get("date", {})
    date_str = ""
    if isinstance(date_info, dict):
        date_str = date_info.get("created", "")
    elif isinstance(date_info, str):
        date_str = date_info
    if date_str and len(date_str) >= 10:
        date_str = date_str[:10]

    # Country list
    countries = fields.get("country", [])
    if isinstance(countries, list):
        country_names = [c.get("name", "") for c in countries if isinstance(c, dict)]
        country_str = ", ".join(country_names) if country_names else primary_country_name
    else:
        country_str = primary_country_name

    # Type info
    types = fields.get("type", [])
    if isinstance(types, list):
        type_names = [t.get("name", "") for t in types if isinstance(t, dict)]
        type_str = ", ".join(type_names) if type_names else "N/A"
    else:
        type_str = "N/A"

    lines = [f"## Disaster: {name}\n"]
    lines.append(f"- **ID:** {disaster_id}")
    lines.append(f"- **Date:** {date_str}")
    lines.append(f"- **Primary Country:** {primary_country_name}")
    lines.append(f"- **Affected Countries:** {country_str}")
    lines.append(f"- **Type:** {type_str}")
    lines.append(f"- **Status:** {status}")
    if glide:
        lines.append(f"- **GLIDE Number:** {glide}")
    if url_field:
        lines.append(f"- **URL:** {url_field}")

    if description:
        # Truncate very long descriptions
        if len(description) > 1000:
            description = description[:1000] + "..."
        lines.append(f"\n### Description\n{description}")

    return "\n".join(lines)


@mcp.tool()
async def search_disaster_reports(
    query: str,
    country: str = "",
    limit: int = 10,
) -> str:
    """Search ReliefWeb situation reports and disaster updates.

    Search for reports, situation updates, assessments, and other documents
    related to humanitarian crises and disasters worldwide.

    Args:
        query: Search query (e.g., 'earthquake damage', 'cholera outbreak',
            'hurricane response', 'food insecurity')
        country: Filter by country name (e.g., 'Syria', 'Ukraine', 'Somalia')
        limit: Maximum number of results to return (default: 10, max: 50)

    Returns:
        List of matching reports with title, source, date, and country.
    """
    limit = validate_limit(limit, max_val=50, default=10)

    if not query or not query.strip():
        return "Error: A search query is required."

    field_params = "&".join([
        "fields[include][]=title",
        "fields[include][]=date",
        "fields[include][]=country",
        "fields[include][]=source",
        "fields[include][]=url",
        "fields[include][]=format",
    ])

    filter_params = ""
    if country:
        filter_params = (
            f"&filter[field]=country.name&filter[value]={country}"
        )

    url = (
        f"{BASE_URL}/reports?appname={APP_NAME}"
        f"&query[value]={query}&limit={limit}"
        f"&sort[]=date:desc&{field_params}{filter_params}"
    )

    try:
        data = await fetch_json(url)
    except Exception as e:
        return f"Error searching disaster reports: {e}"

    items = data.get("data", [])

    if not items:
        filter_parts = [f"query '{query}'"]
        if country:
            filter_parts.append(f"country '{country}'")
        filter_str = ", ".join(filter_parts)
        return f"No reports found for {filter_str}."

    lines = [f"## Disaster Reports ({len(items)} result(s))\n"]

    for item in items:
        fields = item.get("fields", {})
        report_id = item.get("id", "N/A")
        title = fields.get("title", "Unknown")

        # Date
        date_info = fields.get("date", {})
        date_str = ""
        if isinstance(date_info, dict):
            date_str = date_info.get("created", "")
        elif isinstance(date_info, str):
            date_str = date_info
        if date_str and len(date_str) >= 10:
            date_str = date_str[:10]

        # Country
        countries = fields.get("country", [])
        if isinstance(countries, list):
            country_names = [c.get("name", "") for c in countries if isinstance(c, dict)]
            country_str = ", ".join(country_names) if country_names else "N/A"
        else:
            country_str = "N/A"

        # Source
        sources = fields.get("source", [])
        if isinstance(sources, list):
            source_names = [s.get("name", "") for s in sources if isinstance(s, dict)]
            source_str = ", ".join(source_names) if source_names else "N/A"
        else:
            source_str = "N/A"

        # Format
        formats = fields.get("format", [])
        if isinstance(formats, list):
            format_names = [f.get("name", "") for f in formats if isinstance(f, dict)]
            format_str = ", ".join(format_names) if format_names else ""
        else:
            format_str = ""

        report_url = fields.get("url", "")

        lines.append(f"### {title}")
        lines.append(f"- **ID:** {report_id}")
        lines.append(f"- **Date:** {date_str}")
        lines.append(f"- **Country:** {country_str}")
        lines.append(f"- **Source:** {source_str}")
        if format_str:
            lines.append(f"- **Format:** {format_str}")
        if report_url:
            lines.append(f"- **URL:** {report_url}")
        lines.append("")

    return "\n".join(lines)
