from mcp_govt_api.server import mcp
from mcp_govt_api.utils.config import config
from mcp_govt_api.utils.http import fetch_json

FRED_BASE = "https://api.stlouisfed.org/fred"


def get_api_key() -> str:
    """Return FRED API key or raise an error if not configured."""
    if not config.fred_api_key:
        raise ValueError(
            "FRED_API_KEY is not set. "
            "Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html"
        )
    return config.fred_api_key


@mcp.tool()
async def search_fred_series(query: str, limit: int = 10) -> str:
    """Search for FRED economic data series by keyword.

    Args:
        query: Search terms (e.g., 'GDP', 'unemployment rate', 'consumer price index')
        limit: Maximum number of results to return (default: 10)

    Returns:
        Matching series with IDs, titles, and descriptions
    """
    try:
        api_key = get_api_key()
    except ValueError as exc:
        return str(exc)

    params = {
        "search_text": query,
        "api_key": api_key,
        "file_type": "json",
        "limit": limit,
    }

    try:
        data = await fetch_json(f"{FRED_BASE}/series/search", params=params)
    except Exception as exc:
        return f"Error searching FRED: {exc}"

    series_list = data.get("seriess", [])
    if not series_list:
        return f"No FRED series found for '{query}'"

    result = [f"**FRED Series Search: '{query}'**\n"]
    result.append(f"Found {data.get('count', len(series_list))} total results "
                  f"(showing {len(series_list)})\n")

    for s in series_list:
        frequency = s.get("frequency", "N/A")
        units = s.get("units", "N/A")
        seasonal = s.get("seasonal_adjustment", "N/A")
        obs_start = s.get("observation_start", "N/A")
        obs_end = s.get("observation_end", "N/A")
        result.append(
            f"**{s.get('title', 'Untitled')}**\n"
            f"  Series ID: {s.get('id', 'N/A')}\n"
            f"  Frequency: {frequency} | Units: {units}\n"
            f"  Seasonal Adjustment: {seasonal}\n"
            f"  Date Range: {obs_start} to {obs_end}"
        )

    return "\n\n".join(result)


@mcp.tool()
async def get_fred_series(series_id: str, limit: int = 10) -> str:
    """Get observations (data points) for a FRED economic data series.

    Args:
        series_id: FRED series ID (e.g., 'GDP', 'UNRATE', 'CPIAUCSL', 'DFF')
        limit: Number of most recent observations to return (default: 10)

    Returns:
        Recent data points with dates and values
    """
    try:
        api_key = get_api_key()
    except ValueError as exc:
        return str(exc)

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    }

    try:
        data = await fetch_json(
            f"{FRED_BASE}/series/observations", params=params
        )
    except Exception as exc:
        return f"Error fetching FRED series '{series_id}': {exc}"

    observations = data.get("observations", [])
    if not observations:
        return f"No observations found for series '{series_id}'"

    result = [f"**FRED Series: {series_id}**\n"]
    result.append(f"Showing {len(observations)} most recent observations\n")

    for obs in observations:
        date = obs.get("date", "N/A")
        value = obs.get("value", "N/A")
        result.append(f"  {date}: {value}")

    return "\n".join(result)


@mcp.tool()
async def get_fred_series_info(series_id: str) -> str:
    """Get metadata about a FRED economic data series.

    Args:
        series_id: FRED series ID (e.g., 'GDP', 'UNRATE', 'CPIAUCSL')

    Returns:
        Series title, frequency, units, seasonal adjustment, and date range
    """
    try:
        api_key = get_api_key()
    except ValueError as exc:
        return str(exc)

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
    }

    try:
        data = await fetch_json(f"{FRED_BASE}/series", params=params)
    except Exception as exc:
        return f"Error fetching FRED series info for '{series_id}': {exc}"

    series_list = data.get("seriess", [])
    if not series_list:
        return f"No series found with ID '{series_id}'"

    s = series_list[0]
    return (
        f"**{s.get('title', 'Untitled')}**\n"
        f"Series ID: {s.get('id', 'N/A')}\n"
        f"Frequency: {s.get('frequency', 'N/A')}\n"
        f"Units: {s.get('units', 'N/A')}\n"
        f"Seasonal Adjustment: {s.get('seasonal_adjustment', 'N/A')}\n"
        f"Date Range: {s.get('observation_start', 'N/A')} to "
        f"{s.get('observation_end', 'N/A')}\n"
        f"Last Updated: {s.get('last_updated', 'N/A')}\n"
        f"Notes: {s.get('notes', 'N/A')[:500]}"
    )
