from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json
from mcp_govt_api.utils.validation import validate_limit

BTS_BASE = "https://data.bts.gov/resource"
AIRLINE_ONTIME_DATASET = "2wkt-wbq2"
BORDER_CROSSING_DATASET = "keg4-3bc2"
BTS_DISCOVERY_URL = "https://data.bts.gov/api/catalog/v1"


@mcp.tool()
async def get_airline_ontime_stats(
    carrier: str = "",
    airport: str = "",
    limit: int = 20,
) -> str:
    """Get airline on-time performance statistics from BTS.

    Returns data on flight delays, cancellations, and on-time arrival
    performance for US airlines. Data sourced from the Bureau of
    Transportation Statistics via data.bts.gov.

    Args:
        carrier: Filter by airline carrier code (e.g., 'AA', 'UA', 'DL', 'WN')
        airport: Filter by airport code (e.g., 'ATL', 'ORD', 'LAX', 'JFK')
        limit: Maximum number of records to return (default: 20, max: 100)

    Returns:
        Airline on-time performance records including carrier, airport,
        arrival delays, departure delays, and cancellation information.
    """
    limit = validate_limit(limit, max_val=100, default=20)

    url = f"{BTS_BASE}/{AIRLINE_ONTIME_DATASET}.json"
    params: dict[str, str | int] = {
        "$limit": limit,
        "$order": ":id",
    }

    where_clauses: list[str] = []
    if carrier:
        where_clauses.append(f"upper(carrier) = '{carrier.strip().upper()}'")
    if airport:
        airport_upper = airport.strip().upper()
        where_clauses.append(
            f"(upper(origin) = '{airport_upper}' OR upper(dest) = '{airport_upper}')"
        )

    if where_clauses:
        params["$where"] = " AND ".join(where_clauses)

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching airline on-time data: {e}"

    if not data:
        filters = []
        if carrier:
            filters.append(f"carrier '{carrier}'")
        if airport:
            filters.append(f"airport '{airport}'")
        filter_str = " and ".join(filters) if filters else "the given criteria"
        return f"No airline on-time performance data found for {filter_str}."

    lines = [f"Airline On-Time Performance ({len(data)} records):\n"]

    for record in data:
        carrier_name = record.get("carrier_name") or record.get("carrier", "N/A")
        carrier_code = record.get("carrier", "N/A")
        origin = record.get("origin", "N/A")
        dest = record.get("dest", "N/A")
        arr_delay = record.get("arr_delay", "N/A")
        dep_delay = record.get("dep_delay", "N/A")
        cancelled = record.get("cancelled", "N/A")
        flights = record.get("flights", record.get("fl_date", "N/A"))

        lines.append(f"**{carrier_name}** ({carrier_code})")
        lines.append(f"  Route: {origin} -> {dest}")
        if arr_delay != "N/A":
            lines.append(f"  Arrival Delay: {arr_delay} min")
        if dep_delay != "N/A":
            lines.append(f"  Departure Delay: {dep_delay} min")
        if cancelled != "N/A":
            lines.append(f"  Cancelled: {cancelled}")
        if flights != "N/A":
            lines.append(f"  Flights/Date: {flights}")
        lines.append("")

    lines.append("_Source: Bureau of Transportation Statistics (data.bts.gov)_")
    return "\n".join(lines)


@mcp.tool()
async def get_border_crossing_data(
    port: str = "",
    state: str = "",
    measure: str = "",
    limit: int = 20,
) -> str:
    """Get border crossing and entry data from BTS.

    Returns data on the number of incoming crossings at US-Canada and
    US-Mexico border ports of entry. Includes pedestrians, personal
    vehicles, trucks, trains, and more.

    Args:
        port: Filter by port name (e.g., 'El Paso', 'Detroit', 'Buffalo')
        state: Filter by US state (e.g., 'Texas', 'California', 'New York')
        measure: Filter by crossing type (e.g., 'Trucks', 'Personal Vehicles',
                 'Pedestrians', 'Train Passengers')
        limit: Maximum number of records to return (default: 20, max: 100)

    Returns:
        Border crossing records including port name, state, border,
        crossing measure, and value.
    """
    limit = validate_limit(limit, max_val=100, default=20)

    url = f"{BTS_BASE}/{BORDER_CROSSING_DATASET}.json"
    params: dict[str, str | int] = {
        "$limit": limit,
        "$order": "date DESC",
    }

    where_clauses: list[str] = []
    if port:
        where_clauses.append(f"upper(port_name) like '%{port.strip().upper()}%'")
    if state:
        where_clauses.append(f"upper(state) like '%{state.strip().upper()}%'")
    if measure:
        where_clauses.append(f"upper(measure) like '%{measure.strip().upper()}%'")

    if where_clauses:
        params["$where"] = " AND ".join(where_clauses)

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching border crossing data: {e}"

    if not data:
        filters = []
        if port:
            filters.append(f"port '{port}'")
        if state:
            filters.append(f"state '{state}'")
        if measure:
            filters.append(f"measure '{measure}'")
        filter_str = " and ".join(filters) if filters else "the given criteria"
        return f"No border crossing data found for {filter_str}."

    lines = [f"Border Crossing Data ({len(data)} records):\n"]

    for record in data:
        port_name = record.get("port_name", "N/A")
        rec_state = record.get("state", "N/A")
        border = record.get("border", "N/A")
        date = record.get("date", "N/A")
        rec_measure = record.get("measure", "N/A")
        value = record.get("value", "N/A")

        # Format date if it's a full timestamp
        if isinstance(date, str) and "T" in date:
            date = date.split("T")[0]

        lines.append(f"**{port_name}**, {rec_state}")
        lines.append(f"  Border: {border}")
        lines.append(f"  Date: {date}")
        lines.append(f"  Measure: {rec_measure}")
        lines.append(f"  Value: {value}")
        lines.append("")

    lines.append("_Source: Bureau of Transportation Statistics (data.bts.gov)_")
    return "\n".join(lines)


@mcp.tool()
async def search_bts_datasets(
    query: str = "",
    limit: int = 10,
) -> str:
    """Search BTS open datasets on data.bts.gov.

    Browse and discover datasets published by the Bureau of Transportation
    Statistics, including airline, freight, border crossing, and other
    transportation data.

    Args:
        query: Search term (e.g., 'airline', 'freight', 'border', 'traffic')
        limit: Maximum number of datasets to return (default: 10, max: 50)

    Returns:
        List of matching BTS datasets with names, descriptions, and links.
    """
    limit = validate_limit(limit, max_val=50, default=10)

    params: dict[str, str | int] = {
        "limit": limit,
    }
    if query:
        params["q"] = query.strip()

    try:
        data = await fetch_json(BTS_DISCOVERY_URL, params=params)
    except Exception as e:
        return f"Error searching BTS datasets: {e}"

    results = data.get("results", data) if isinstance(data, dict) else data

    if not results:
        return f"No BTS datasets found matching '{query}'." if query else "No BTS datasets found."

    # Handle both list and dict response formats
    if isinstance(results, dict):
        results = results.get("results", [])

    if not isinstance(results, list):
        return "Unexpected response format from BTS catalog API."

    lines = [f"BTS Datasets ({len(results)} results):\n"]

    for dataset in results[:limit]:
        resource = dataset.get("resource", dataset)
        name = resource.get("name", dataset.get("name", "Untitled"))
        description = resource.get("description", dataset.get("description", ""))
        dataset_id = resource.get("id", dataset.get("id", ""))
        updated = resource.get("updatedAt", dataset.get("updatedAt", ""))
        page_url = dataset.get("permalink", dataset.get("link", ""))

        if isinstance(description, str) and len(description) > 200:
            description = description[:200] + "..."

        # Format updated date
        if isinstance(updated, str) and "T" in updated:
            updated = updated.split("T")[0]

        lines.append(f"**{name}**")
        if dataset_id:
            lines.append(f"  ID: {dataset_id}")
        if description:
            lines.append(f"  Description: {description}")
        if updated:
            lines.append(f"  Last Updated: {updated}")
        if page_url:
            lines.append(f"  Link: {page_url}")
        lines.append("")

    lines.append("_Source: Bureau of Transportation Statistics (data.bts.gov)_")
    return "\n".join(lines)
