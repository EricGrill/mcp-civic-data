from mcp_govt_api.server import mcp
from mcp_govt_api.utils.config import config
from mcp_govt_api.utils.http import fetch_json

BEA_BASE = "https://apps.bea.gov/api/data/"


def _require_key() -> str:
    """Return the BEA API key or raise an error."""
    if not config.bea_api_key:
        raise ValueError(
            "BEA_API_KEY environment variable is not set. "
            "Get a free key at https://apps.bea.gov/API/signup/"
        )
    return config.bea_api_key


@mcp.tool()
async def get_bea_regional_data(
    table: str = "CAGDP1",
    state: str = "",
    year: str = "",
    limit: int = 10,
) -> str:
    """Get regional economic data (GDP, income, employment) by state from the BEA.

    Args:
        table: BEA table name. Common tables:
               'CAGDP1' (GDP summary), 'CAINC1' (personal income),
               'CAINC4' (income and employment), 'CAGDP9' (real GDP).
        state: Two-letter state code (e.g., 'CA', 'TX') or FIPS code.
               Leave empty for all states.
        year: Year(s) for data (e.g., '2022' or '2020,2021,2022').
              Leave empty for the most recent year.
        limit: Maximum number of records to return (default 10).

    Returns:
        Regional economic data for the specified state(s) and table.
    """
    try:
        api_key = _require_key()
    except ValueError as exc:
        return str(exc)

    # Map state abbreviations to BEA GeoFips codes
    state_fips = {
        "AL": "01000", "AK": "02000", "AZ": "04000", "AR": "05000",
        "CA": "06000", "CO": "08000", "CT": "09000", "DE": "10000",
        "FL": "12000", "GA": "13000", "HI": "15000", "ID": "16000",
        "IL": "17000", "IN": "18000", "IA": "19000", "KS": "20000",
        "KY": "21000", "LA": "22000", "ME": "23000", "MD": "24000",
        "MA": "25000", "MI": "26000", "MN": "27000", "MS": "28000",
        "MO": "29000", "MT": "30000", "NE": "31000", "NV": "32000",
        "NH": "33000", "NJ": "34000", "NM": "35000", "NY": "36000",
        "NC": "37000", "ND": "38000", "OH": "39000", "OK": "40000",
        "OR": "41000", "PA": "42000", "RI": "44000", "SC": "45000",
        "SD": "46000", "TN": "47000", "TX": "48000", "UT": "49000",
        "VT": "50000", "VA": "51000", "WA": "53000", "WV": "54000",
        "WI": "55000", "WY": "56000", "DC": "11000",
    }

    geo_fips = "STATE"
    if state:
        upper = state.upper()
        geo_fips = state_fips.get(upper, upper)

    params: dict = {
        "UserID": api_key,
        "method": "GetData",
        "DataSetName": "Regional",
        "TableName": table,
        "GeoFips": geo_fips,
        "ResultFormat": "JSON",
    }
    if year:
        params["Year"] = year
    else:
        params["Year"] = "LAST5"

    try:
        data = await fetch_json(BEA_BASE, params=params)
    except Exception as exc:
        return f"Error fetching BEA regional data: {exc}"

    results = data.get("BEAAPI", {}).get("Results", {})

    # Handle API-level errors
    error = results.get("Error")
    if error:
        msg = error.get("APIErrorDescription", str(error))
        return f"BEA API error: {msg}"

    records = results.get("Data", [])
    if not records:
        label = state.upper() if state else "all states"
        return f"No BEA regional data found for {label} (table={table})."

    # Limit records
    records = records[:limit]

    label = state.upper() if state else "All States"
    lines = [f"**BEA Regional Data — {label}** (Table: {table})\n"]

    for rec in records:
        geo = rec.get("GeoName", "N/A")
        yr = rec.get("TimePeriod", "N/A")
        value = rec.get("DataValue", "N/A")
        desc = rec.get("Description", "")
        unit = rec.get("UNIT_MULT_DESC", "")

        parts = [f"  - **{geo}** ({yr})"]
        if desc:
            parts.append(desc)
        parts.append(str(value))
        if unit:
            parts.append(f"[{unit}]")

        lines.append(" | ".join(parts))

    note_text = results.get("NoteText", "")
    if note_text:
        lines.append(f"\n_{note_text[:200]}_")

    return "\n".join(lines)


@mcp.tool()
async def get_bea_gdp_by_industry(
    year: str = "",
    industry: str = "",
    limit: int = 10,
) -> str:
    """Get GDP data broken down by industry sector from the BEA.

    Args:
        year: Year for data (e.g., '2022'). Leave empty for the most recent year.
        industry: Industry code (e.g., '11' for Agriculture, '54' for Professional Services).
                  Leave empty for all industries.
        limit: Maximum number of records to return (default 10).

    Returns:
        GDP by industry data showing value added by sector.
    """
    try:
        api_key = _require_key()
    except ValueError as exc:
        return str(exc)

    params: dict = {
        "UserID": api_key,
        "method": "GetData",
        "DataSetName": "GDPbyIndustry",
        "TableID": "1",
        "Frequency": "A",
        "ResultFormat": "JSON",
    }
    if year:
        params["Year"] = year
    else:
        params["Year"] = "LAST5"

    if industry:
        params["Industry"] = industry
    else:
        params["Industry"] = "ALL"

    try:
        data = await fetch_json(BEA_BASE, params=params)
    except Exception as exc:
        return f"Error fetching BEA GDP by industry: {exc}"

    results = data.get("BEAAPI", {}).get("Results", {})

    error = results.get("Error")
    if error:
        msg = error.get("APIErrorDescription", str(error))
        return f"BEA API error: {msg}"

    records = results.get("Data", [])
    if not records:
        label = f"industry {industry}" if industry else "all industries"
        return f"No BEA GDP by industry data found for {label}."

    records = records[:limit]

    label = f"Industry {industry}" if industry else "All Industries"
    lines = [f"**BEA GDP by Industry — {label}**\n"]

    for rec in records:
        ind_desc = rec.get("IndustrYDescription", rec.get("IndustryDescription", "N/A"))
        yr = rec.get("Year", "N/A")
        value = rec.get("DataValue", "N/A")
        freq = rec.get("FreqDesc", "")

        parts = [f"  - **{ind_desc}** ({yr})"]
        parts.append(str(value))
        if freq:
            parts.append(f"[{freq}]")

        lines.append(" | ".join(parts))

    return "\n".join(lines)


@mcp.tool()
async def search_bea_datasets() -> str:
    """List available BEA datasets and their descriptions.

    Returns:
        A list of all available BEA API datasets with descriptions.
    """
    try:
        api_key = _require_key()
    except ValueError as exc:
        return str(exc)

    params = {
        "UserID": api_key,
        "method": "GetDataSetList",
        "ResultFormat": "JSON",
    }

    try:
        data = await fetch_json(BEA_BASE, params=params)
    except Exception as exc:
        return f"Error fetching BEA datasets: {exc}"

    results = data.get("BEAAPI", {}).get("Results", {})

    error = results.get("Error")
    if error:
        msg = error.get("APIErrorDescription", str(error))
        return f"BEA API error: {msg}"

    datasets = results.get("Dataset", [])
    if not datasets:
        return "No BEA datasets found."

    lines = ["**Available BEA Datasets**\n"]

    for ds in datasets:
        name = ds.get("DatasetName", "N/A")
        desc = ds.get("DatasetDescription", "")
        lines.append(f"  - **{name}**: {desc}")

    lines.append("\n_Common Regional tables: CAGDP1 (GDP summary), "
                 "CAINC1 (personal income), CAINC4 (income & employment), "
                 "CAGDP9 (real GDP by state)._")

    return "\n".join(lines)
