from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

SBA_CKAN_BASE = "https://data.sba.gov/api/3/action"
SBA_DATA_BASE = "https://data.sba.gov/resource"

# Socrata dataset identifiers on data.sba.gov
SIZE_STANDARDS_DATASET = "jfx9-jbxa"
DISASTER_LOANS_DATASET = "bnkb-3gaf"


@mcp.tool()
async def search_sba_datasets(query: str = "", limit: int = 10) -> str:
    """Search SBA open datasets on data.sba.gov.

    Queries the SBA CKAN data catalog to discover available datasets
    related to small business programs, loans, size standards, and more.

    Args:
        query: Search terms (e.g., 'PPP loans', 'disaster', 'size standards')
        limit: Maximum number of results to return (default: 10, max: 50)

    Returns:
        List of matching SBA datasets with titles, descriptions, and resource counts.
    """
    limit = min(limit, 50)
    url = f"{SBA_CKAN_BASE}/package_search"
    params: dict = {"q": query, "rows": limit}

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error searching SBA datasets: {e}"

    results = data.get("result", {}).get("results", [])
    total = data.get("result", {}).get("count", 0)

    if not results:
        return f"No SBA datasets found for '{query}'."

    lines = [f"SBA Dataset Search: '{query}'"]
    lines.append(f"Found {total} datasets (showing {len(results)})\n")

    for ds in results:
        title = ds.get("title", "Untitled")
        org = ds.get("organization", {}).get("title", "SBA")
        notes = ds.get("notes", "No description")[:200]
        dataset_id = ds.get("id", "")
        num_resources = len(ds.get("resources", []))

        lines.append(f"**{title}**")
        lines.append(f"  Organization: {org}")
        lines.append(f"  Resources: {num_resources} files")
        lines.append(f"  ID: `{dataset_id}`")
        lines.append(f"  {notes}")
        lines.append("")

    lines.append("_Source: SBA Open Data (data.sba.gov)_")

    return "\n".join(lines)


@mcp.tool()
async def get_sba_size_standards(
    industry: str = "",
    naics_code: str = "",
    limit: int = 10,
) -> str:
    """Look up SBA small business size standards by industry or NAICS code.

    Size standards define the largest a business can be and still qualify
    as a small business for federal programs and contracting.

    Args:
        industry: Industry name or keyword to search (e.g., 'restaurant',
            'software', 'construction')
        naics_code: NAICS industry code (e.g., '541511' for custom
            computer programming)
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        Size standard records showing NAICS code, industry description,
        and the size standard (revenue or employee threshold).
    """
    limit = min(limit, 100)

    url = f"{SBA_DATA_BASE}/{SIZE_STANDARDS_DATASET}.json"
    params: dict = {"$limit": limit}

    if naics_code:
        params["NAICS_Code"] = naics_code
    if industry:
        params["$where"] = f"upper(NAICS_Industry_Description) like upper('%{industry}%')"

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching SBA size standards: {e}"

    if not isinstance(data, list):
        data = []

    if not data:
        filter_parts = []
        if industry:
            filter_parts.append(f"industry '{industry}'")
        if naics_code:
            filter_parts.append(f"NAICS code '{naics_code}'")
        filter_str = ", ".join(filter_parts) if filter_parts else "the given criteria"
        return f"No SBA size standards found for {filter_str}."

    lines = [f"SBA Size Standards ({len(data)} result(s)):\n"]

    for r in data:
        naics = r.get("NAICS_Code", r.get("naics_code", "N/A"))
        desc = r.get("NAICS_Industry_Description", r.get("naics_industry_description", "Unknown"))
        size_standard = r.get("Size_Standard", r.get("size_standard", "N/A"))

        lines.append(f"**NAICS {naics}** - {desc}")
        lines.append(f"  Size Standard: {size_standard}")
        lines.append("")

    lines.append("_Source: SBA Size Standards (data.sba.gov)_")

    return "\n".join(lines)


@mcp.tool()
async def get_sba_disaster_loans(
    state: str = "",
    year: str = "",
    limit: int = 20,
) -> str:
    """Get SBA disaster loan data by state or year.

    Queries SBA disaster loan approval data from data.sba.gov. These loans
    help businesses and homeowners recover from declared disasters.

    Args:
        state: Two-letter state abbreviation (e.g., 'CA', 'TX', 'FL')
        year: Filter by fiscal year (e.g., '2024')
        limit: Maximum number of results to return (default: 20, max: 100)

    Returns:
        Disaster loan records showing loan amounts, declaration numbers,
        damage categories, and location information.
    """
    limit = min(limit, 100)

    url = f"{SBA_DATA_BASE}/{DISASTER_LOANS_DATASET}.json"
    params: dict = {"$limit": limit, "$order": ":id DESC"}

    where_clauses = []
    if state:
        where_clauses.append(f"upper(damaged_state_abbreviation) = upper('{state}')")
    if year:
        where_clauses.append(f"fiscal_year = '{year}'")

    if where_clauses:
        params["$where"] = " AND ".join(where_clauses)

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching SBA disaster loans: {e}"

    if not isinstance(data, list):
        data = []

    if not data:
        filter_parts = []
        if state:
            filter_parts.append(f"state '{state.upper()}'")
        if year:
            filter_parts.append(f"year '{year}'")
        filter_str = ", ".join(filter_parts) if filter_parts else "the given criteria"
        return f"No SBA disaster loans found for {filter_str}."

    lines = [f"SBA Disaster Loans ({len(data)} result(s)):\n"]

    for r in data:
        decl_num = r.get("fema_disaster_number", r.get("declaration_number", "N/A"))
        loan_state = r.get("damaged_state_abbreviation", "N/A")
        county = r.get("damaged_county", "Unknown")
        damage_cat = r.get("damage_category", "N/A")
        total_approved = r.get("total_approved_loan_amount", r.get("approved_amount", ""))
        fy = r.get("fiscal_year", "N/A")

        lines.append(f"**Disaster #{decl_num}** - {county}, {loan_state}")
        lines.append(f"  Fiscal Year: {fy}")
        lines.append(f"  Damage Category: {damage_cat}")
        if total_approved:
            try:
                amount = float(total_approved)
                lines.append(f"  Approved Amount: ${amount:,.2f}")
            except (ValueError, TypeError):
                lines.append(f"  Approved Amount: {total_approved}")
        lines.append("")

    lines.append("_Source: SBA Disaster Loans (data.sba.gov)_")

    return "\n".join(lines)
