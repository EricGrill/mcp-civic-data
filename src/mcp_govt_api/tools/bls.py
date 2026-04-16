from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import http_client
from mcp_govt_api.utils.config import config


BLS_BASE = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# State FIPS codes for LAUS series construction
STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "DC": "11", "FL": "12",
    "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18",
    "IA": "19", "KS": "20", "KY": "21", "LA": "22", "ME": "23",
    "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28",
    "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33",
    "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38",
    "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44",
    "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49",
    "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55",
    "WY": "56", "PR": "72",
}

# Common BLS series for keyword lookup
COMMON_SERIES = {
    "cpi": {
        "series_id": "CUUR0000SA0",
        "name": "Consumer Price Index - All Urban Consumers",
        "description": "CPI for all urban consumers, all items, US city average, "
                       "not seasonally adjusted",
    },
    "cpi seasonally adjusted": {
        "series_id": "CUSR0000SA0",
        "name": "Consumer Price Index - All Urban Consumers (Seasonally Adjusted)",
        "description": "CPI for all urban consumers, all items, US city average, "
                       "seasonally adjusted",
    },
    "cpi food": {
        "series_id": "CUUR0000SAF1",
        "name": "Consumer Price Index - Food",
        "description": "CPI for all urban consumers, food, US city average",
    },
    "cpi energy": {
        "series_id": "CUUR0000SA0E",
        "name": "Consumer Price Index - Energy",
        "description": "CPI for all urban consumers, energy, US city average",
    },
    "unemployment": {
        "series_id": "LNS14000000",
        "name": "Unemployment Rate",
        "description": "Unemployment rate, seasonally adjusted, 16 years and over",
    },
    "unemployment men": {
        "series_id": "LNS14000001",
        "name": "Unemployment Rate - Men",
        "description": "Unemployment rate for men, 16 years and over, "
                       "seasonally adjusted",
    },
    "unemployment women": {
        "series_id": "LNS14000002",
        "name": "Unemployment Rate - Women",
        "description": "Unemployment rate for women, 16 years and over, "
                       "seasonally adjusted",
    },
    "employment": {
        "series_id": "CES0000000001",
        "name": "Total Nonfarm Employment",
        "description": "All employees, total nonfarm, seasonally adjusted, "
                       "in thousands",
    },
    "nonfarm payrolls": {
        "series_id": "CES0000000001",
        "name": "Total Nonfarm Employment",
        "description": "All employees, total nonfarm, seasonally adjusted, "
                       "in thousands",
    },
    "ppi": {
        "series_id": "WPUFD49104",
        "name": "Producer Price Index - Finished Goods",
        "description": "PPI for finished goods, not seasonally adjusted",
    },
    "average hourly earnings": {
        "series_id": "CES0500000003",
        "name": "Average Hourly Earnings - Private",
        "description": "Average hourly earnings of all employees, "
                       "total private, seasonally adjusted",
    },
    "average weekly hours": {
        "series_id": "CES0500000002",
        "name": "Average Weekly Hours - Private",
        "description": "Average weekly hours of all employees, "
                       "total private, seasonally adjusted",
    },
    "labor force participation": {
        "series_id": "LNS11300000",
        "name": "Labor Force Participation Rate",
        "description": "Civilian labor force participation rate, "
                       "seasonally adjusted",
    },
    "initial claims": {
        "series_id": "LNS14000000",
        "name": "Unemployment Rate",
        "description": "Note: For weekly initial claims, see the DOL ETA. "
                       "This is the monthly unemployment rate.",
    },
    "job openings": {
        "series_id": "JTS000000000000000JOL",
        "name": "Job Openings - Total Nonfarm",
        "description": "Job openings, total nonfarm, seasonally adjusted",
    },
    "quits": {
        "series_id": "JTS000000000000000QUL",
        "name": "Quits - Total Nonfarm",
        "description": "Quits, total nonfarm, seasonally adjusted",
    },
}


async def _fetch_bls_series(
    series_ids: list[str],
    start_year: str = "",
    end_year: str = "",
) -> dict:
    """Make a POST request to the BLS Public Data API v2."""
    payload: dict = {"seriesid": series_ids}
    if start_year:
        payload["startyear"] = start_year
    if end_year:
        payload["endyear"] = end_year
    if config.bls_api_key:
        payload["registrationkey"] = config.bls_api_key

    try:
        response = await http_client.post(BLS_BASE, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise Exception(f"BLS API request failed: {e}")


@mcp.tool()
async def get_bls_timeseries(
    series_id: str,
    start_year: str = "",
    end_year: str = "",
) -> str:
    """Get time series data from the Bureau of Labor Statistics.

    Args:
        series_id: BLS series ID (e.g., 'CUUR0000SA0' for CPI,
            'LNS14000000' for unemployment rate)
        start_year: Start year for data range (e.g., '2020'). Defaults to
            latest available.
        end_year: End year for data range (e.g., '2024'). Defaults to
            latest available.

    Returns:
        Time series data points with year, period, and value
    """
    try:
        data = await _fetch_bls_series([series_id], start_year, end_year)
    except Exception as e:
        return f"Error fetching BLS data: {e}"

    if data.get("status") != "REQUEST_SUCCEEDED":
        messages = data.get("message", [])
        return f"BLS API error: {'; '.join(messages)}"

    series_list = data.get("Results", {}).get("series", [])
    if not series_list:
        return f"No data found for series {series_id}"

    series = series_list[0]
    series_data = series.get("data", [])
    if not series_data:
        return f"No data points returned for series {series_id}"

    results = [f"**BLS Series: {series_id}**\n"]

    for point in series_data[:20]:
        year = point.get("year", "")
        period = point.get("periodName", "")
        value = point.get("value", "")
        footnotes = [
            fn.get("text", "")
            for fn in point.get("footnotes", [])
            if fn.get("text")
        ]
        footnote_str = f" ({'; '.join(footnotes)})" if footnotes else ""
        results.append(f"- {period} {year}: {value}{footnote_str}")

    return "\n".join(results)


@mcp.tool()
async def search_bls_series(query: str) -> str:
    """Search for common BLS data series by keyword.

    Provides a lookup of well-known BLS series IDs for topics like CPI,
    unemployment, employment, PPI, wages, and labor force participation.

    Args:
        query: Search keyword (e.g., 'cpi', 'unemployment', 'wages',
            'employment', 'ppi', 'job openings')

    Returns:
        Matching BLS series with IDs and descriptions
    """
    query_lower = query.lower().strip()
    matches = []

    for key, info in COMMON_SERIES.items():
        if query_lower in key or query_lower in info["name"].lower():
            matches.append(info)

    # Deduplicate by series_id
    seen = set()
    unique_matches = []
    for match in matches:
        if match["series_id"] not in seen:
            seen.add(match["series_id"])
            unique_matches.append(match)

    if not unique_matches:
        results = [
            f'**No BLS series found for "{query}"**\n',
            "Try one of these keywords: cpi, unemployment, employment, "
            "ppi, wages, earnings, labor force, job openings, quits",
        ]
        return "\n".join(results)

    results = [f'**BLS Series matching "{query}"**\n']
    for match in unique_matches:
        results.append(
            f"- **{match['name']}**\n"
            f"  Series ID: `{match['series_id']}`\n"
            f"  {match['description']}"
        )

    results.append(
        "\nUse `get_bls_timeseries` with a series ID to retrieve data."
    )
    return "\n".join(results)


@mcp.tool()
async def get_unemployment_rate(
    state: str = "",
    year: str = "",
) -> str:
    """Get unemployment rate data from BLS.

    Returns national unemployment rate by default, or state-level data
    using Local Area Unemployment Statistics (LAUS).

    Args:
        state: Optional two-letter state code (e.g., 'CA', 'TX') for
            state-level data. Omit for national rate.
        year: Optional year to filter results (e.g., '2024'). Defaults to
            latest available.

    Returns:
        Unemployment rate data with monthly values
    """
    if state:
        state_upper = state.upper().strip()
        fips = STATE_FIPS.get(state_upper)
        if not fips:
            return (
                f"Unknown state code: {state}. "
                "Use a two-letter state abbreviation (e.g., 'CA', 'TX')."
            )
        # LAUS series: LASST{fips}0000000000003 = unemployment rate
        series_id = f"LASST{fips}0000000000003"
        label = f"Unemployment Rate - {state_upper}"
    else:
        series_id = "LNS14000000"
        label = "National Unemployment Rate"

    start_year = year if year else ""
    end_year = year if year else ""

    try:
        data = await _fetch_bls_series([series_id], start_year, end_year)
    except Exception as e:
        return f"Error fetching unemployment data: {e}"

    if data.get("status") != "REQUEST_SUCCEEDED":
        messages = data.get("message", [])
        return f"BLS API error: {'; '.join(messages)}"

    series_list = data.get("Results", {}).get("series", [])
    if not series_list:
        return f"No unemployment data found for series {series_id}"

    series = series_list[0]
    series_data = series.get("data", [])
    if not series_data:
        return f"No data points returned for {label}"

    results = [f"**{label}** (Series: {series_id})\n"]

    for point in series_data[:12]:
        year_val = point.get("year", "")
        period = point.get("periodName", "")
        value = point.get("value", "")
        results.append(f"- {period} {year_val}: {value}%")

    return "\n".join(results)
