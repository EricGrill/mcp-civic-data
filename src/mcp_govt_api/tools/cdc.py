from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json


CDC_OPEN_DATA_BASE = "https://data.cdc.gov"
CDC_NNDSS_DATASET = "x9gk-5huc"
CDC_VACCINATION_DATASET = "unsk-b7fc"


@mcp.tool()
async def search_cdc_datasets(
    query: str,
    limit: int = 10,
) -> str:
    """Search CDC open datasets by keyword.

    Browse the CDC's open data catalog to find datasets on public health
    topics including disease surveillance, vaccination, mortality, and more.

    Args:
        query: Search term (e.g., 'influenza', 'covid', 'vaccination')
        limit: Maximum number of results to return (default: 10, max: 50)

    Returns:
        List of matching CDC datasets with titles, descriptions, and identifiers.
    """
    limit = min(limit, 50)
    url = f"{CDC_OPEN_DATA_BASE}/api/views.json"
    params = {"q": query, "limit": limit}

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error searching CDC datasets: {e}"

    if not data:
        return f"No CDC datasets found matching '{query}'."

    lines = [f"CDC Open Datasets matching '{query}' ({len(data)} results):\n"]

    for ds in data:
        name = ds.get("name", "Untitled")
        dataset_id = ds.get("id", "N/A")
        description = ds.get("description", "No description available")
        if len(description) > 200:
            description = description[:200] + "..."
        category = ds.get("category", "Uncategorized")
        updated = ds.get("rowsUpdatedAt")
        updated_str = ""
        if updated:
            from datetime import datetime, timezone

            try:
                updated_str = datetime.fromtimestamp(
                    updated, tz=timezone.utc
                ).strftime("%Y-%m-%d")
            except (ValueError, OSError):
                updated_str = "Unknown"

        lines.append(f"**{name}**")
        lines.append(f"  Dataset ID: {dataset_id}")
        lines.append(f"  Category: {category}")
        if updated_str:
            lines.append(f"  Last Updated: {updated_str}")
        lines.append(f"  Description: {description}")
        lines.append(
            f"  URL: {CDC_OPEN_DATA_BASE}/resource/{dataset_id}.json"
        )
        lines.append("")

    lines.append("_Source: CDC Open Data (data.cdc.gov)_")

    return "\n".join(lines)


@mcp.tool()
async def get_cdc_disease_surveillance(
    disease: str = "",
    state: str = "",
    limit: int = 20,
) -> str:
    """Get notifiable disease surveillance data from the CDC NNDSS.

    The National Notifiable Diseases Surveillance System (NNDSS) tracks
    weekly counts of nationally notifiable infectious diseases reported
    by US states and territories.

    Args:
        disease: Filter by disease name (e.g., 'Salmonellosis', 'Hepatitis')
        state: Filter by reporting area / state name (e.g., 'California', 'New York')
        limit: Maximum number of records to return (default: 20, max: 100)

    Returns:
        Disease surveillance records with case counts by disease and reporting area.
    """
    limit = min(limit, 100)
    url = f"{CDC_OPEN_DATA_BASE}/resource/{CDC_NNDSS_DATASET}.json"

    where_clauses = []
    if disease:
        where_clauses.append(f"upper(disease) like upper('%{disease}%')")
    if state:
        where_clauses.append(
            f"upper(reporting_area) like upper('%{state}%')"
        )

    params: dict = {"$limit": str(limit), "$order": "mmwr_year DESC"}
    if where_clauses:
        params["$where"] = " AND ".join(where_clauses)

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching CDC disease surveillance data: {e}"

    if not data:
        filters = []
        if disease:
            filters.append(f"disease '{disease}'")
        if state:
            filters.append(f"state '{state}'")
        filter_str = " and ".join(filters) if filters else "the given criteria"
        return f"No NNDSS surveillance records found for {filter_str}."

    lines = [f"CDC NNDSS Disease Surveillance ({len(data)} records):\n"]

    for record in data:
        disease_name = record.get("disease", "Unknown")
        reporting_area = record.get("reporting_area", "Unknown")
        mmwr_year = record.get("mmwr_year", "N/A")
        mmwr_week = record.get("mmwr_week", "N/A")
        current_week = record.get("current_week", "N/A")
        cum_2024 = record.get("cum_2024_flag", record.get("cum_2024", "N/A"))

        lines.append(f"**{disease_name}** - {reporting_area}")
        lines.append(f"  MMWR Year/Week: {mmwr_year}/{mmwr_week}")
        lines.append(f"  Current Week Cases: {current_week}")
        lines.append(f"  Cumulative: {cum_2024}")
        lines.append("")

    lines.append("_Source: CDC NNDSS (National Notifiable Diseases Surveillance System)_")

    return "\n".join(lines)


@mcp.tool()
async def get_cdc_vaccination_coverage(
    vaccine_type: str = "",
    state: str = "",
    limit: int = 20,
) -> str:
    """Get vaccination coverage data from the CDC.

    Provides vaccination coverage estimates from the National Immunization
    Survey, including childhood and adult immunization rates by state.

    Args:
        vaccine_type: Filter by vaccine name (e.g., 'Influenza', 'HPV', 'MMR')
        state: Filter by state or geography name (e.g., 'Texas', 'National')
        limit: Maximum number of records to return (default: 20, max: 100)

    Returns:
        Vaccination coverage records with coverage estimates by vaccine and geography.
    """
    limit = min(limit, 100)
    url = f"{CDC_OPEN_DATA_BASE}/resource/{CDC_VACCINATION_DATASET}.json"

    where_clauses = []
    if vaccine_type:
        where_clauses.append(f"upper(vaccine) like upper('%{vaccine_type}%')")
    if state:
        where_clauses.append(
            f"upper(geography) like upper('%{state}%')"
        )

    params: dict = {"$limit": str(limit), "$order": "survey_year DESC"}
    if where_clauses:
        params["$where"] = " AND ".join(where_clauses)

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching CDC vaccination coverage data: {e}"

    if not data:
        filters = []
        if vaccine_type:
            filters.append(f"vaccine '{vaccine_type}'")
        if state:
            filters.append(f"state '{state}'")
        filter_str = " and ".join(filters) if filters else "the given criteria"
        return f"No vaccination coverage records found for {filter_str}."

    lines = [f"CDC Vaccination Coverage ({len(data)} records):\n"]

    for record in data:
        vaccine = record.get("vaccine", "Unknown")
        dose = record.get("dose", "")
        geography = record.get("geography", "Unknown")
        survey_year = record.get("survey_year", "N/A")
        dimension_type = record.get("dimension_type", "")
        dimension = record.get("dimension", "")
        coverage = record.get("coverage_estimate", "N/A")
        ci_low = record.get("_95_ci_low", "")
        ci_high = record.get("_95_ci_high", "")

        vaccine_label = vaccine
        if dose:
            vaccine_label = f"{vaccine} ({dose})"

        lines.append(f"**{vaccine_label}** - {geography}")
        lines.append(f"  Survey Year: {survey_year}")
        if dimension_type and dimension:
            lines.append(f"  {dimension_type}: {dimension}")
        lines.append(f"  Coverage Estimate: {coverage}%")
        if ci_low and ci_high:
            lines.append(f"  95% CI: {ci_low}% - {ci_high}%")
        lines.append("")

    lines.append("_Source: CDC National Immunization Survey_")

    return "\n".join(lines)


@mcp.tool()
async def query_cdc_open_data(
    dataset_id: str,
    params: dict | None = None,
) -> dict:
    """Make a raw query to any CDC open data dataset (SODA API).

    Args:
        dataset_id: The CDC dataset identifier (e.g., 'x9gk-5huc')
        params: SODA query parameters ($where, $limit, $offset, $order, $select, $group)

    Returns:
        Raw JSON response from the CDC SODA API.
    """
    url = f"{CDC_OPEN_DATA_BASE}/resource/{dataset_id}.json"
    return await fetch_json(url, params=params)
