"""OSHA workplace safety and enforcement tools via DOL Enforcement API."""

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

OSHA_BASE = "https://enforcedata.dol.gov/api"
OSHA_INSPECTION_URL = f"{OSHA_BASE}/osha_inspection"
OSHA_VIOLATION_URL = f"{OSHA_BASE}/osha_violation"
OSHA_FATALITY_URL = f"{OSHA_BASE}/osha_fatality"


@mcp.tool()
async def search_osha_inspections(
    state: str = "",
    establishment: str = "",
    limit: int = 10,
) -> str:
    """Search OSHA workplace inspections from the DOL enforcement database.

    OSHA inspections are conducted to ensure workplace safety and health
    compliance. Results include inspection details, establishment info,
    and enforcement outcomes.

    Args:
        state: Two-letter state abbreviation to filter by (e.g., 'CA', 'TX')
        establishment: Establishment name to search for (partial match)
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of OSHA inspections matching the criteria, including inspection
        number, establishment, open/close dates, and inspection type.
    """
    limit = min(limit, 100)

    filters = []
    if state:
        filters.append(f"site_state:{state.upper()}")
    if establishment:
        filters.append(f"estab_name:{establishment}")

    params: dict[str, str | int] = {"per_page": limit}
    if filters:
        params["filters"] = ",".join(filters)

    try:
        data = await fetch_json(OSHA_INSPECTION_URL, params=params)
    except Exception as e:
        return f"Error fetching OSHA inspections: {e}"

    if not data:
        return "No OSHA inspections found matching the criteria."

    lines = [f"OSHA Workplace Inspections ({len(data)} results):\n"]

    for insp in data:
        insp_nr = insp.get("activity_nr", "N/A")
        estab = insp.get("estab_name", "Unknown")
        site_city = insp.get("site_city", "")
        site_state = insp.get("site_state", "")
        open_date = insp.get("open_date", "Unknown")
        close_case_date = insp.get("close_case_date", "")
        insp_type = insp.get("insp_type", "Unknown")
        industry = insp.get("sic_code", "")
        nr_violations = insp.get("total_current_penalty", "")

        location = ", ".join(filter(None, [site_city, site_state]))

        lines.append(f"**Inspection #{insp_nr}** — {estab}")
        if location:
            lines.append(f"  Location: {location}")
        lines.append(f"  Opened: {open_date}")
        if close_case_date:
            lines.append(f"  Closed: {close_case_date}")
        lines.append(f"  Type: {insp_type}")
        if industry:
            lines.append(f"  SIC Code: {industry}")
        if nr_violations:
            lines.append(f"  Total Penalty: ${nr_violations}")
        lines.append("")

    lines.append(f"_Source: OSHA Enforcement Data (DOL)_")
    return "\n".join(lines)


@mcp.tool()
async def get_osha_violations(
    inspection_nr: str = "",
    limit: int = 10,
) -> str:
    """Get OSHA violations for a specific inspection.

    Returns violation details including standards cited, severity,
    penalty amounts, and abatement dates.

    Args:
        inspection_nr: OSHA inspection/activity number to look up violations for
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of violations for the inspection, including standard cited,
        violation type, penalty amounts, and abatement status.
    """
    if not inspection_nr:
        return "Error: Please provide an inspection number (activity_nr)."

    limit = min(limit, 100)

    params: dict[str, str | int] = {
        "filters": f"activity_nr:{inspection_nr}",
        "per_page": limit,
    }

    try:
        data = await fetch_json(OSHA_VIOLATION_URL, params=params)
    except Exception as e:
        return f"Error fetching OSHA violations: {e}"

    if not data:
        return f"No violations found for inspection #{inspection_nr}."

    lines = [f"OSHA Violations for Inspection #{inspection_nr} ({len(data)} results):\n"]

    for viol in data:
        standard = viol.get("standard", "N/A")
        viol_type = viol.get("viol_type", "Unknown")
        gravity = viol.get("gravity", "")
        initial_penalty = viol.get("initial_penalty", 0)
        current_penalty = viol.get("current_penalty", 0)
        abate_date = viol.get("abate_date", "")
        contest = viol.get("abate_complete", "")

        # Map violation type codes to descriptions
        viol_type_map = {
            "S": "Serious",
            "W": "Willful",
            "R": "Repeat",
            "O": "Other-than-Serious",
        }
        viol_desc = viol_type_map.get(viol_type, viol_type)

        lines.append(f"**Standard: {standard}**")
        lines.append(f"  Type: {viol_desc}")
        if gravity:
            lines.append(f"  Gravity: {gravity}")
        lines.append(f"  Initial Penalty: ${initial_penalty}")
        lines.append(f"  Current Penalty: ${current_penalty}")
        if abate_date:
            lines.append(f"  Abatement Date: {abate_date}")
        if contest:
            lines.append(f"  Abatement Complete: {contest}")
        lines.append("")

    lines.append(f"_Source: OSHA Enforcement Data (DOL)_")
    return "\n".join(lines)


@mcp.tool()
async def search_osha_fatalities(
    state: str = "",
    keyword: str = "",
    limit: int = 10,
) -> str:
    """Search OSHA workplace fatality and catastrophe reports.

    OSHA investigates workplace fatalities and catastrophes (incidents
    resulting in hospitalization of three or more workers).

    Args:
        state: Two-letter state abbreviation to filter by (e.g., 'CA', 'TX')
        keyword: Keyword to search in fatality summaries
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of workplace fatality reports including date, location,
        and incident summary.
    """
    limit = min(limit, 100)

    filters = []
    if state:
        filters.append(f"state:{state.upper()}")
    if keyword:
        filters.append(f"summary:{keyword}")

    params: dict[str, str | int] = {"per_page": limit}
    if filters:
        params["filters"] = ",".join(filters)

    try:
        data = await fetch_json(OSHA_FATALITY_URL, params=params)
    except Exception as e:
        return f"Error fetching OSHA fatality reports: {e}"

    if not data:
        return "No OSHA fatality reports found matching the criteria."

    lines = [f"OSHA Workplace Fatality Reports ({len(data)} results):\n"]

    for fat in data:
        fat_id = fat.get("id", "N/A")
        date = fat.get("date_of_incident", fat.get("event_date", "Unknown"))
        city = fat.get("city", "")
        fat_state = fat.get("state", "")
        employer = fat.get("employer", "Unknown")
        summary = fat.get("summary", "No summary available")

        location = ", ".join(filter(None, [city, fat_state]))

        lines.append(f"**Report #{fat_id}**")
        lines.append(f"  Employer: {employer}")
        if location:
            lines.append(f"  Location: {location}")
        lines.append(f"  Date: {date}")
        lines.append(f"  Summary: {summary}")
        lines.append("")

    lines.append(f"_Source: OSHA Fatality and Catastrophe Reports (DOL)_")
    return "\n".join(lines)
