from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

LOCATOR_BASE_URL = "https://findtreatment.gov/locator"
DATA_BASE_URL = "https://data.samhsa.gov/resource"


@mcp.tool()
async def find_treatment_facilities(
    location: str,
    service_type: str = "BOTH",
    limit: int = 10,
) -> str:
    """Find SAMHSA treatment facilities near a location.

    Searches the SAMHSA treatment locator for substance abuse and mental
    health treatment facilities across the United States.

    Args:
        location: Location to search near (city/state, ZIP code, or address)
        service_type: Type of service - 'SA' (substance abuse),
            'MH' (mental health), or 'BOTH' (default: 'BOTH')
        limit: Maximum number of results to return (default: 10, max: 50)

    Returns:
        List of treatment facilities with name, address, phone,
        services offered, and accepted payment types.
    """
    limit = min(limit, 50)
    service_type = service_type.upper()
    if service_type not in ("SA", "MH", "BOTH"):
        return "Error: service_type must be 'SA' (substance abuse), 'MH' (mental health), or 'BOTH'."

    params: dict = {
        "sAddr": location,
        "sType": service_type,
        "limitValue": limit,
        "pageSize": limit,
    }

    url = f"{LOCATOR_BASE_URL}/listing"

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching SAMHSA treatment facilities: {e}"

    rows = data if isinstance(data, list) else data.get("rows", data.get("results", []))

    if not rows:
        return f"No SAMHSA treatment facilities found near '{location}' for service type '{service_type}'."

    lines = [f"SAMHSA Treatment Facilities near '{location}' ({len(rows)} result(s)):\n"]

    for r in rows:
        name = r.get("name1", r.get("name", "Unknown"))
        street = r.get("street1", r.get("street", ""))
        city = r.get("city", "")
        state = r.get("state", "")
        zip_code = r.get("zip", r.get("zip5", ""))
        phone = r.get("phone", "")
        services = r.get("services", r.get("typeFacility", ""))
        payment = r.get("payment", "")

        lines.append(f"**{name}**")
        address_parts = [p for p in [street, city, state, zip_code] if p]
        if address_parts:
            lines.append(f"  Address: {', '.join(address_parts)}")
        if phone:
            lines.append(f"  Phone: {phone}")
        if services:
            if isinstance(services, list):
                services = ", ".join(services)
            lines.append(f"  Services: {services}")
        if payment:
            if isinstance(payment, list):
                payment = ", ".join(payment)
            lines.append(f"  Payment: {payment}")
        lines.append("")

    lines.append("_Source: SAMHSA Treatment Locator (findtreatment.gov)_")

    return "\n".join(lines)


@mcp.tool()
async def search_samhsa_datasets(
    query: str = "",
    limit: int = 10,
) -> str:
    """Search SAMHSA open data catalog for behavioral health datasets.

    Queries the SAMHSA data portal (data.samhsa.gov) for datasets
    related to mental health, substance abuse, and behavioral health.

    Args:
        query: Search keywords (e.g., 'opioid', 'mental health',
            'substance abuse', 'treatment admissions')
        limit: Maximum number of results to return (default: 10, max: 50)

    Returns:
        List of matching datasets with name, description, and data link.
    """
    limit = min(limit, 50)

    params: dict = {
        "limit": limit,
    }
    if query:
        params["q"] = query

    url = "https://data.samhsa.gov/api/views/metadata/v1"

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error searching SAMHSA datasets: {e}"

    records = data if isinstance(data, list) else []

    if not records:
        search_desc = f"query '{query}'" if query else "all datasets"
        return f"No SAMHSA datasets found for {search_desc}."

    # Limit results
    records = records[:limit]

    lines = [f"SAMHSA Open Data Catalog ({len(records)} result(s)):\n"]

    for r in records:
        name = r.get("name", "Unknown")
        description = r.get("description", "No description available")
        dataset_id = r.get("id", "")
        category = r.get("category", "")
        updated = r.get("dataUpdatedAt", r.get("updatedAt", ""))

        # Truncate long descriptions
        if len(description) > 200:
            description = description[:200] + "..."

        lines.append(f"**{name}**")
        if dataset_id:
            lines.append(f"  ID: {dataset_id}")
            lines.append(f"  URL: https://data.samhsa.gov/resource/{dataset_id}")
        if category:
            lines.append(f"  Category: {category}")
        if updated and len(updated) >= 10:
            lines.append(f"  Updated: {updated[:10]}")
        lines.append(f"  Description: {description}")
        lines.append("")

    lines.append("_Source: SAMHSA Open Data Portal (data.samhsa.gov)_")

    return "\n".join(lines)


@mcp.tool()
async def get_samhsa_facility_details(
    facility_id: str,
) -> str:
    """Get detailed information about a SAMHSA treatment facility.

    Retrieves comprehensive details about a specific treatment facility
    from the SAMHSA treatment locator, including services offered,
    payment options, special programs, and certifications.

    Args:
        facility_id: The facility identifier (from find_treatment_facilities results)

    Returns:
        Detailed facility information including services, payment options,
        special programs, languages, and certifications.
    """
    if not facility_id:
        return "Error: facility_id is required. Use find_treatment_facilities to discover facility IDs."

    url = f"{LOCATOR_BASE_URL}/detail/{facility_id}"

    try:
        data = await fetch_json(url)
    except Exception as e:
        return f"Error fetching SAMHSA facility details: {e}"

    if not data:
        return f"No SAMHSA facility found with ID '{facility_id}'."

    name = data.get("name1", data.get("name", "Unknown"))
    street = data.get("street1", data.get("street", ""))
    city = data.get("city", "")
    state = data.get("state", "")
    zip_code = data.get("zip", data.get("zip5", ""))
    phone = data.get("phone", "")
    website = data.get("website", "")
    services = data.get("services", [])
    payment = data.get("payment", [])
    languages = data.get("languages", [])
    special_programs = data.get("specialPrograms", data.get("special_programs", []))
    intake_process = data.get("intakeProcess", "")
    hours = data.get("hours", "")

    lines = [f"SAMHSA Facility Details - {name}\n"]

    address_parts = [p for p in [street, city, state, zip_code] if p]
    if address_parts:
        lines.append(f"**Address:** {', '.join(address_parts)}")
    if phone:
        lines.append(f"**Phone:** {phone}")
    if website:
        lines.append(f"**Website:** {website}")
    if hours:
        lines.append(f"**Hours:** {hours}")

    lines.append("")

    if services:
        if isinstance(services, list):
            lines.append("**Services:**")
            for s in services:
                lines.append(f"  - {s}")
        else:
            lines.append(f"**Services:** {services}")

    if payment:
        if isinstance(payment, list):
            lines.append("**Payment Options:**")
            for p in payment:
                lines.append(f"  - {p}")
        else:
            lines.append(f"**Payment Options:** {payment}")

    if special_programs:
        if isinstance(special_programs, list):
            lines.append("**Special Programs:**")
            for sp in special_programs:
                lines.append(f"  - {sp}")
        else:
            lines.append(f"**Special Programs:** {special_programs}")

    if languages:
        if isinstance(languages, list):
            lines.append(f"**Languages:** {', '.join(languages)}")
        else:
            lines.append(f"**Languages:** {languages}")

    if intake_process:
        lines.append(f"**Intake Process:** {intake_process}")

    lines.append("")
    lines.append("_Source: SAMHSA Treatment Locator (findtreatment.gov)_")

    return "\n".join(lines)
