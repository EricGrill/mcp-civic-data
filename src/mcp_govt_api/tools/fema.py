from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

BASE_URL = "https://www.fema.gov/api/open/v2"


@mcp.tool()
async def get_fema_disasters(
    state: str = "",
    year: str = "",
    disaster_type: str = "",
    limit: int = 10,
) -> str:
    """Search FEMA disaster declarations by state, year, or type.

    Queries the OpenFEMA DisasterDeclarationsSummaries endpoint to find
    federal disaster declarations across the United States.

    Args:
        state: Two-letter state abbreviation (e.g., 'CA', 'TX', 'FL')
        year: Filter by fiscal year of declaration (e.g., '2024')
        disaster_type: Filter by incident type (e.g., 'Hurricane',
            'Flood', 'Fire', 'Tornado', 'Earthquake', 'Severe Storm')
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of disaster declarations with disaster number, state, type,
        declaration date, title, and program areas designated.
    """
    limit = min(limit, 100)

    filters = []
    if state:
        filters.append(f"state eq '{state.upper()}'")
    if year:
        filters.append(f"fyDeclared eq '{year}'")
    if disaster_type:
        filters.append(f"incidentType eq '{disaster_type}'")

    params: dict = {
        "$top": limit,
        "$orderby": "declarationDate desc",
    }
    if filters:
        params["$filter"] = " and ".join(filters)

    url = f"{BASE_URL}/DisasterDeclarationsSummaries"

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching FEMA disaster declarations: {e}"

    records = data.get("DisasterDeclarationsSummaries", [])

    if not records:
        filter_parts = []
        if state:
            filter_parts.append(f"state '{state.upper()}'")
        if year:
            filter_parts.append(f"year '{year}'")
        if disaster_type:
            filter_parts.append(f"type '{disaster_type}'")
        filter_str = ", ".join(filter_parts) if filter_parts else "the given criteria"
        return f"No FEMA disaster declarations found for {filter_str}."

    lines = [f"FEMA Disaster Declarations ({len(records)} result(s)):\n"]

    for r in records:
        disaster_num = r.get("disasterNumber", "N/A")
        title = r.get("declarationTitle", "Unknown")
        decl_state = r.get("state", "N/A")
        incident = r.get("incidentType", "Unknown")
        decl_date = r.get("declarationDate", "Unknown")
        if decl_date and len(decl_date) >= 10:
            decl_date = decl_date[:10]
        decl_type = r.get("declarationType", "N/A")
        designated_area = r.get("designatedArea", "")

        programs = []
        if r.get("ihProgramDeclared"):
            programs.append("Individual & Households")
        if r.get("iaProgramDeclared"):
            programs.append("Individual Assistance")
        if r.get("paProgramDeclared"):
            programs.append("Public Assistance")
        if r.get("hmProgramDeclared"):
            programs.append("Hazard Mitigation")

        lines.append(f"**DR-{disaster_num}** - {title}")
        lines.append(f"  State: {decl_state}")
        lines.append(f"  Type: {incident} ({decl_type})")
        lines.append(f"  Declared: {decl_date}")
        if designated_area:
            lines.append(f"  Area: {designated_area}")
        if programs:
            lines.append(f"  Programs: {', '.join(programs)}")
        lines.append("")

    lines.append("_Source: FEMA OpenFEMA API - Disaster Declarations Summaries_")

    return "\n".join(lines)


@mcp.tool()
async def get_fema_disaster_summary(disaster_number: str = "") -> str:
    """Get a detailed summary for a specific FEMA disaster by number.

    Retrieves comprehensive information about a disaster from the
    FemaWebDisasterSummaries endpoint, including financial totals
    and assistance counts.

    Args:
        disaster_number: The FEMA disaster number (e.g., '4699', '4834')

    Returns:
        Detailed disaster summary including total obligated amounts,
        number of approved applications, and program breakdowns.
    """
    if not disaster_number:
        return "Error: disaster_number is required. Provide a FEMA disaster number (e.g., '4699')."

    params: dict = {
        "$filter": f"disasterNumber eq {disaster_number}",
    }

    url = f"{BASE_URL}/FemaWebDisasterSummaries"

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching FEMA disaster summary: {e}"

    records = data.get("FemaWebDisasterSummaries", [])

    if not records:
        return f"No FEMA disaster summary found for disaster number {disaster_number}."

    r = records[0]

    title = r.get("declarationTitle", "Unknown")
    decl_date = r.get("declarationDate", "Unknown")
    if decl_date and len(decl_date) >= 10:
        decl_date = decl_date[:10]
    state = r.get("state", "N/A")
    incident_type = r.get("incidentType", "Unknown")

    total_obligated = r.get("totalAmountIhpApproved", 0)
    total_ha_amount = r.get("totalAmountHaApproved", 0)
    total_ona_amount = r.get("totalAmountOnaApproved", 0)
    total_approved = r.get("totalNumberIhpApproved", 0)
    pa_amount = r.get("totalObligatedAmountPa", 0)
    hmgp_amount = r.get("totalObligatedAmountHmgp", 0)

    lines = [
        f"FEMA Disaster Summary - DR-{disaster_number}\n",
        f"**{title}**",
        f"  State: {state}",
        f"  Type: {incident_type}",
        f"  Declaration Date: {decl_date}",
        "",
        "**Individual & Households Program (IHP)**",
    ]

    if total_obligated:
        lines.append(f"  Total IHP Approved: ${total_obligated:,.2f}")
    if total_ha_amount:
        lines.append(f"  Housing Assistance Approved: ${total_ha_amount:,.2f}")
    if total_ona_amount:
        lines.append(f"  Other Needs Assistance Approved: ${total_ona_amount:,.2f}")
    if total_approved:
        lines.append(f"  Total Applications Approved: {total_approved:,}")

    lines.append("")
    lines.append("**Public Assistance (PA)**")
    if pa_amount:
        lines.append(f"  Total Obligated: ${pa_amount:,.2f}")

    lines.append("")
    lines.append("**Hazard Mitigation Grant Program (HMGP)**")
    if hmgp_amount:
        lines.append(f"  Total Obligated: ${hmgp_amount:,.2f}")

    lines.append("")
    lines.append("_Source: FEMA OpenFEMA API - Web Disaster Summaries_")

    return "\n".join(lines)


@mcp.tool()
async def get_fema_assistance(
    state: str = "",
    disaster_number: str = "",
    limit: int = 10,
) -> str:
    """Get FEMA housing assistance data for disaster survivors.

    Queries the HousingAssistanceOwners endpoint for data about
    housing assistance provided to homeowners after disasters.

    Args:
        state: Two-letter state abbreviation (e.g., 'TX', 'FL')
        disaster_number: Filter by specific FEMA disaster number
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        Housing assistance records showing approved amounts, number of
        applicants, and types of assistance provided per county/area.
    """
    limit = min(limit, 100)

    filters = []
    if state:
        filters.append(f"state eq '{state.upper()}'")
    if disaster_number:
        filters.append(f"disasterNumber eq {disaster_number}")

    params: dict = {
        "$top": limit,
        "$orderby": "disasterNumber desc",
    }
    if filters:
        params["$filter"] = " and ".join(filters)

    url = f"{BASE_URL}/HousingAssistanceOwners"

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching FEMA housing assistance data: {e}"

    records = data.get("HousingAssistanceOwners", [])

    if not records:
        filter_parts = []
        if state:
            filter_parts.append(f"state '{state.upper()}'")
        if disaster_number:
            filter_parts.append(f"disaster {disaster_number}")
        filter_str = ", ".join(filter_parts) if filter_parts else "the given criteria"
        return f"No FEMA housing assistance data found for {filter_str}."

    lines = [f"FEMA Housing Assistance Data ({len(records)} result(s)):\n"]

    for r in records:
        disaster_num = r.get("disasterNumber", "N/A")
        rec_state = r.get("state", "N/A")
        county = r.get("county", "Unknown")
        city = r.get("city", "")

        total_approved = r.get("totalApprovedIhpAmount", 0)
        repair_amount = r.get("repairReplaceAmount", 0)
        rental_amount = r.get("rentalAmount", 0)
        total_applicants = r.get("totalInspected", 0)
        total_damaged = r.get("totalDamaged", 0)
        approved_between = r.get("approvedBetween1And10000", 0)
        approved_over = r.get("approvedOver25000", 0)

        location = f"{county}, {rec_state}"
        if city:
            location = f"{city}, {county}, {rec_state}"

        lines.append(f"**DR-{disaster_num}** - {location}")
        if total_approved:
            lines.append(f"  Total IHP Approved: ${total_approved:,.2f}")
        if repair_amount:
            lines.append(f"  Repair/Replace: ${repair_amount:,.2f}")
        if rental_amount:
            lines.append(f"  Rental Assistance: ${rental_amount:,.2f}")
        if total_applicants:
            lines.append(f"  Total Inspected: {total_applicants:,}")
        if total_damaged:
            lines.append(f"  Total Damaged: {total_damaged:,}")
        if approved_between:
            lines.append(f"  Approved $1-$10K: {approved_between:,}")
        if approved_over:
            lines.append(f"  Approved >$25K: {approved_over:,}")
        lines.append("")

    lines.append("_Source: FEMA OpenFEMA API - Housing Assistance Owners_")

    return "\n".join(lines)
