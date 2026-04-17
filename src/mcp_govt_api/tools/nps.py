from mcp_govt_api.server import mcp
from mcp_govt_api.utils.config import config
from mcp_govt_api.utils.http import fetch_json

NPS_BASE = "https://developer.nps.gov/api/v1"


def get_api_key() -> str | None:
    """Return NPS API key if configured."""
    return config.nps_api_key


def _build_params(**kwargs) -> dict:
    """Build query params, adding API key and dropping empty values."""
    params = {}
    api_key = get_api_key()
    if api_key:
        params["api_key"] = api_key
    for key, value in kwargs.items():
        if value is not None and value != "":
            params[key] = value
    return params


@mcp.tool()
async def search_national_parks(
    query: str = "",
    state: str = "",
    limit: int = 10,
) -> str:
    """Search for national parks by name, keyword, or state.

    Args:
        query: Search term (e.g., 'Yellowstone', 'canyon', 'volcano')
        state: Two-letter state code to filter by (e.g., 'CA', 'WY')
        limit: Maximum number of results (default: 10)

    Returns:
        List of matching national parks with descriptions and locations
    """
    try:
        params = _build_params(q=query, stateCode=state, limit=limit)
        data = await fetch_json(f"{NPS_BASE}/parks", params=params)

        parks = data.get("data", [])
        if not parks:
            return "No national parks found matching your search criteria."

        total = data.get("total", len(parks))
        result = [f"**National Parks Search Results** ({len(parks)} of {total})\n"]

        for park in parks:
            states = park.get("states", "N/A")
            designation = park.get("designation", "")
            desc = park.get("description", "N/A")
            if len(desc) > 200:
                desc = desc[:200] + "..."

            result.append(
                f"**{park.get('fullName', 'Unknown')}** ({park.get('parkCode', '')})\n"
                f"States: {states}\n"
                f"Designation: {designation}\n"
                f"Description: {desc}\n"
                f"URL: {park.get('url', 'N/A')}"
            )

        return "\n\n---\n\n".join(result)
    except Exception as e:
        return f"Error searching national parks: {e}"


@mcp.tool()
async def get_park_alerts(
    park_code: str = "",
    limit: int = 10,
) -> str:
    """Get active alerts for a national park (closures, cautions, dangers).

    Args:
        park_code: Park code (e.g., 'yose' for Yosemite, 'grca' for Grand Canyon).
                   Leave empty to get alerts across all parks.
        limit: Maximum number of alerts (default: 10)

    Returns:
        Active alerts with category, title, and description
    """
    try:
        params = _build_params(parkCode=park_code, limit=limit)
        data = await fetch_json(f"{NPS_BASE}/alerts", params=params)

        alerts = data.get("data", [])
        if not alerts:
            scope = f"park '{park_code}'" if park_code else "any park"
            return f"No active alerts found for {scope}."

        total = data.get("total", len(alerts))
        result = [f"**National Park Alerts** ({len(alerts)} of {total})\n"]

        for alert in alerts:
            category = alert.get("category", "Unknown")
            park = alert.get("parkCode", "N/A").upper()
            desc = alert.get("description", "N/A")
            if len(desc) > 300:
                desc = desc[:300] + "..."

            result.append(
                f"**[{category}] {alert.get('title', 'Untitled')}**\n"
                f"Park: {park}\n"
                f"Description: {desc}\n"
                f"URL: {alert.get('url', 'N/A')}"
            )

        return "\n\n---\n\n".join(result)
    except Exception as e:
        return f"Error fetching park alerts: {e}"


@mcp.tool()
async def get_park_info(park_code: str) -> str:
    """Get detailed information about a specific national park.

    Args:
        park_code: Park code (e.g., 'yose' for Yosemite, 'grca' for Grand Canyon)

    Returns:
        Detailed park information including description, hours, fees, and contacts
    """
    try:
        params = _build_params(parkCode=park_code, limit=1)
        data = await fetch_json(f"{NPS_BASE}/parks", params=params)

        parks = data.get("data", [])
        if not parks:
            return f"No park found with code '{park_code}'."

        park = parks[0]
        result = [f"**{park.get('fullName', 'Unknown')}**\n"]

        result.append(f"Park Code: {park.get('parkCode', 'N/A')}")
        result.append(f"States: {park.get('states', 'N/A')}")
        result.append(f"Designation: {park.get('designation', 'N/A')}")
        result.append(f"Description: {park.get('description', 'N/A')}")

        # Weather info
        weather = park.get("weatherInfo", "")
        if weather:
            result.append(f"\n**Weather:** {weather}")

        # Operating hours
        hours = park.get("operatingHours", [])
        if hours:
            result.append("\n**Operating Hours:**")
            for schedule in hours:
                result.append(f"  {schedule.get('name', 'Standard Hours')}:")
                desc = schedule.get("description", "")
                if desc:
                    result.append(f"  {desc}")
                std_hours = schedule.get("standardHours", {})
                if std_hours:
                    for day, time in std_hours.items():
                        result.append(f"    {day.capitalize()}: {time}")

        # Entrance fees
        fees = park.get("entranceFees", [])
        if fees:
            result.append("\n**Entrance Fees:**")
            for fee in fees:
                cost = fee.get("cost", "N/A")
                title = fee.get("title", "General")
                result.append(f"  ${cost} - {title}")

        # Contacts
        contacts = park.get("contacts", {})
        phones = contacts.get("phoneNumbers", [])
        if phones:
            result.append("\n**Contact:**")
            for phone in phones:
                ptype = phone.get("type", "Voice")
                number = phone.get("phoneNumber", "N/A")
                result.append(f"  {ptype}: {number}")

        emails = contacts.get("emailAddresses", [])
        if emails:
            for email in emails:
                addr = email.get("emailAddress", "")
                if addr:
                    result.append(f"  Email: {addr}")

        result.append(f"\nURL: {park.get('url', 'N/A')}")

        return "\n".join(result)
    except Exception as e:
        return f"Error fetching park info: {e}"
