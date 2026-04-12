from mcp_govt_api.server import mcp
from mcp_govt_api.utils.config import config
from mcp_govt_api.utils.http import fetch_json


NPS_BASE = "https://developer.nps.gov/api/v1"


def get_api_key() -> str:
    """Return NPS API key or raise if not configured."""
    key = config.nps_api_key
    if not key:
        raise Exception(
            "NPS_API_KEY not configured. Get a free key at "
            "https://www.nps.gov/subjects/developer/get-started.htm"
        )
    return key


@mcp.tool()
async def search_parks(
    state: str = "",
    query: str = "",
    limit: int = 10
) -> str:
    """Search for National Parks by state, name, or keywords.

    Args:
        state: Two-letter state code (e.g., 'CA', 'NY', 'WY')
        query: Search term for park name (e.g., 'Yellowstone', 'Grand Canyon')
        limit: Maximum number of results (default: 10)

    Returns:
        List of parks with name, code, description, and location
    """
    params = {
        "api_key": get_api_key(),
        "limit": min(limit, 50)  # API max is 50
    }

    if state:
        params["stateCode"] = state.upper()
    if query:
        params["q"] = query

    data = await fetch_json(f"{NPS_BASE}/parks", params=params)

    parks = data.get("data", [])
    if not parks:
        return "No parks found matching your criteria."

    result = [f"**National Parks Search Results**\n"]
    if state:
        result.append(f"State: {state.upper()}")
    if query:
        result.append(f"Query: '{query}'")
    result.append(f"Found {len(parks)} park(s)\n")

    for park in parks:
        states = park.get("states", "N/A")
        result.append(
            f"**{park.get('fullName', 'Unknown')}**\n"
            f"Code: `{park.get('parkCode', 'N/A')}`\n"
            f"States: {states}\n"
            f"Description: {park.get('description', 'No description available.')[:200]}...\n"
            f"Learn more: {park.get('url', 'N/A')}"
        )

    return "\n\n---\n\n".join(result)


@mcp.tool()
async def get_park_details(park_code: str) -> str:
    """Get detailed information about a specific National Park.

    Args:
        park_code: Park code (e.g., 'yell' for Yellowstone, 'grca' for Grand Canyon)

    Returns:
        Full park details including description, activities, topics, contacts, and entrance fees
    """
    params = {
        "api_key": get_api_key(),
        "parkCode": park_code.lower()
    }

    data = await fetch_json(f"{NPS_BASE}/parks", params=params)

    parks = data.get("data", [])
    if not parks:
        return f"Park with code '{park_code}' not found."

    park = parks[0]

    result = [f"**{park.get('fullName', 'Unknown Park')}**\n"]
    result.append(f"Park Code: `{park.get('parkCode', 'N/A')}`")
    result.append(f"States: {park.get('states', 'N/A')}")
    result.append(f"Designation: {park.get('designation', 'N/A')}\n")

    result.append(f"**Description**\n{park.get('description', 'No description available.')}\n")

    # Weather info
    weather = park.get('weatherInfo', '')
    if weather:
        result.append(f"**Weather**\n{weather}\n")

    # Activities
    activities = park.get('activities', [])
    if activities:
        activity_names = [a.get('name', '') for a in activities[:15]]
        result.append(f"**Activities**\n{', '.join(activity_names)}\n")

    # Topics
    topics = park.get('topics', [])
    if topics:
        topic_names = [t.get('name', '') for t in topics[:10]]
        result.append(f"**Topics**\n{', '.join(topic_names)}\n")

    # Entrance fees
    fees = park.get('entranceFees', [])
    if fees:
        result.append("**Entrance Fees**")
        for fee in fees:
            result.append(f"- {fee.get('title', 'Fee')}: ${fee.get('cost', '0')} - {fee.get('description', '')}")
        result.append("")

    # Operating hours
    hours = park.get('operatingHours', [])
    if hours:
        result.append("**Operating Hours**")
        for h in hours:
            result.append(f"- {h.get('name', 'Standard Hours')}:")
            standard_hours = h.get('standardHours', {})
            for day, time in standard_hours.items():
                result.append(f"  - {day.capitalize()}: {time}")
        result.append("")

    # Contacts
    contacts = park.get('contacts', {})
    phone_numbers = contacts.get('phoneNumbers', [])
    if phone_numbers:
        result.append("**Contact**")
        for phone in phone_numbers[:2]:
            result.append(f"- {phone.get('type', 'Phone')}: {phone.get('phoneNumber', 'N/A')}")
        result.append("")

    # Directions
    directions = park.get('directionsInfo', '')
    if directions:
        result.append(f"**Directions**\n{directions[:300]}...\n")

    result.append(f"**Website**: {park.get('url', 'N/A')}")

    return "\n".join(result)


@mcp.tool()
async def get_park_alerts(park_code: str = "") -> str:
    """Get current alerts, closures, and warnings for National Parks.

    Args:
        park_code: Optional park code to filter alerts (e.g., 'yell' for Yellowstone)
                  If not provided, returns alerts from all parks

    Returns:
        List of active alerts with category, title, and description
    """
    params = {
        "api_key": get_api_key(),
        "limit": 50
    }

    if park_code:
        params["parkCode"] = park_code.lower()

    data = await fetch_json(f"{NPS_BASE}/alerts", params=params)

    alerts = data.get("data", [])
    if not alerts:
        if park_code:
            return f"No active alerts for park '{park_code}'."
        return "No active alerts across all National Parks."

    if park_code:
        result = [f"**Park Alerts for '{park_code.upper()}'**\n"]
    else:
        result = [f"**National Park Alerts**\n"]

    result.append(f"Found {len(alerts)} active alert(s)\n")

    # Group alerts by category
    categories = {}
    for alert in alerts:
        category = alert.get('category', 'General')
        if category not in categories:
            categories[category] = []
        categories[category].append(alert)

    # Display alerts grouped by category
    for category, cat_alerts in categories.items():
        result.append(f"**{category} ({len(cat_alerts)})**\n")
        for alert in cat_alerts:
            result.append(
                f"- **{alert.get('title', 'Alert')}**\n"
                f"  Park: {alert.get('fullName', 'Unknown')}\n"
                f"  {alert.get('description', 'No details available.')}\n"
            )

    return "\n".join(result)


@mcp.tool()
async def query_nps(endpoint: str, params: dict | None = None) -> dict:
    """Make a raw query to the NPS API.

    Args:
        endpoint: API endpoint (e.g., '/parks', '/alerts', '/events', '/campgrounds')
        params: Query parameters (api_key will be added automatically)

    Returns:
        Raw JSON response from NPS API
    """
    url = f"{NPS_BASE}{endpoint}"
    params = params or {}
    params["api_key"] = get_api_key()
    return await fetch_json(url, params=params)