from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

ECHO_BASE_URL = "https://echodata.epa.gov/echo"
ENVIROFACTS_BASE_URL = "https://data.epa.gov/efservice"


@mcp.tool()
async def search_epa_facilities(
    state: str = "",
    zip_code: str = "",
    name: str = "",
    limit: int = 10,
) -> str:
    """Search EPA-regulated facilities via the ECHO enforcement database.

    Finds facilities tracked by EPA's Enforcement and Compliance History
    Online (ECHO) system. Can filter by state, ZIP code, or facility name.

    Args:
        state: Two-letter US state code (e.g., 'CA', 'NY')
        zip_code: Five-digit US ZIP code (e.g., '90210')
        name: Facility name or partial name to search
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of EPA-regulated facilities with name, address, compliance
        status, and registry IDs.
    """
    if not state and not zip_code and not name:
        return "Error: at least one of state, zip_code, or name is required."

    limit = min(max(1, limit), 100)

    url = f"{ECHO_BASE_URL}/echo_rest_services.get_facilities"
    params = {"output": "JSON"}

    if state:
        params["p_st"] = state.upper()
    if zip_code:
        params["p_zip"] = zip_code
    if name:
        params["p_fn"] = name

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching EPA facilities: {e}"

    results = data.get("Results", {})
    facilities = results.get("Facilities", [])

    if not facilities:
        return "No EPA-regulated facilities found matching the given criteria."

    facilities = facilities[:limit]

    lines = [f"EPA-Regulated Facilities ({len(facilities)} results):\n"]

    for f in facilities:
        name_val = f.get("FacName", "Unknown")
        addr = f.get("FacStreet", "")
        city = f.get("FacCity", "")
        st = f.get("FacState", "")
        fac_zip = f.get("FacZip", "")
        registry_id = f.get("RegistryId", "N/A")
        compliance = f.get("DfrUrl", "")

        location = ", ".join(p for p in [addr, city, st, fac_zip] if p)

        lines.append(f"**{name_val}**")
        lines.append(f"  Registry ID: {registry_id}")
        lines.append(f"  Address: {location or 'N/A'}")
        if compliance:
            lines.append(f"  Details: {compliance}")
        lines.append("")

    lines.append("_Source: EPA ECHO (Enforcement and Compliance History Online)_")

    return "\n".join(lines)


@mcp.tool()
async def get_epa_facility_info(
    facility_id: str,
) -> str:
    """Get detailed EPA compliance information for a specific facility.

    Retrieves enforcement and compliance history from EPA's Detailed
    Facility Report (DFR) system using a facility registry ID.

    Args:
        facility_id: EPA facility registry ID (e.g., '110000350174')

    Returns:
        Detailed facility information including name, address, programs,
        compliance status, inspection history, and enforcement actions.
    """
    if not facility_id:
        return "Error: facility_id is required."

    url = f"{ECHO_BASE_URL}/dfr_rest_services.get_facility_info"
    params = {"p_id": facility_id, "output": "JSON"}

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching EPA facility info: {e}"

    results = data.get("Results", {})
    facility = results.get("Facility", {})

    if not facility:
        return f"No facility information found for ID '{facility_id}'."

    name = facility.get("FacName", "Unknown")
    addr = facility.get("FacStreet", "")
    city = facility.get("FacCity", "")
    state = facility.get("FacState", "")
    fac_zip = facility.get("FacZip", "")
    county = facility.get("FacCounty", "")
    lat = facility.get("FacLat", "")
    lon = facility.get("FacLong", "")

    location = ", ".join(p for p in [addr, city, state, fac_zip] if p)

    lines = [f"EPA Facility Detail: {name}\n"]
    lines.append(f"  Registry ID: {facility_id}")
    lines.append(f"  Address: {location or 'N/A'}")
    if county:
        lines.append(f"  County: {county}")
    if lat and lon:
        lines.append(f"  Coordinates: {lat}, {lon}")

    # Programs (CWA, CAA, RCRA, etc.)
    programs = facility.get("Programs", [])
    if programs:
        prog_names = [p.get("ProgramAcronym", "") for p in programs if p.get("ProgramAcronym")]
        if prog_names:
            lines.append(f"  EPA Programs: {', '.join(prog_names)}")

    # Compliance status
    cwa_status = facility.get("CWAComplianceStatus", "")
    caa_status = facility.get("CAAComplianceStatus", "")
    rcra_status = facility.get("RCRAComplianceStatus", "")

    if cwa_status or caa_status or rcra_status:
        lines.append("  Compliance Status:")
        if cwa_status:
            lines.append(f"    Clean Water Act: {cwa_status}")
        if caa_status:
            lines.append(f"    Clean Air Act: {caa_status}")
        if rcra_status:
            lines.append(f"    RCRA (Waste): {rcra_status}")

    # Inspections
    inspections = facility.get("Inspections5yr", "")
    if inspections:
        lines.append(f"  Inspections (5yr): {inspections}")

    # Enforcement actions
    enforcement = facility.get("EnforcementActions5yr", "")
    if enforcement:
        lines.append(f"  Enforcement Actions (5yr): {enforcement}")

    # Penalties
    penalties = facility.get("Penalties5yr", "")
    if penalties:
        lines.append(f"  Penalties (5yr): ${penalties}")

    lines.append("")
    lines.append("_Source: EPA ECHO Detailed Facility Report_")

    return "\n".join(lines)


@mcp.tool()
async def get_toxic_releases(
    state: str = "",
    facility: str = "",
    year: str = "",
    limit: int = 10,
) -> str:
    """Query EPA Toxics Release Inventory (TRI) data via Envirofacts.

    Searches the TRI database for information about toxic chemical
    releases reported by industrial facilities to the EPA.

    Args:
        state: Two-letter US state code (e.g., 'CA', 'TX')
        facility: Facility name to search for
        year: Reporting year (e.g., '2022')
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of TRI facility records with chemical release information,
        facility names, and locations.
    """
    if not state and not facility and not year:
        return "Error: at least one of state, facility, or year is required."

    limit = min(max(1, limit), 100)

    # Build Envirofacts REST URL path segments
    url_parts = [ENVIROFACTS_BASE_URL, "TRI_FACILITY"]

    if state:
        url_parts.append(f"STATE_ABBR/{state.upper()}")
    if facility:
        url_parts.append(f"FAC_NAME/{facility}")
    if year:
        url_parts.append(f"REPORTING_YEAR/{year}")

    url_parts.append(f"JSON/0:{limit}")

    url = "/".join(url_parts)

    try:
        data = await fetch_json(url)
    except Exception as e:
        return f"Error fetching TRI data: {e}"

    if not data or not isinstance(data, list):
        return "No Toxics Release Inventory records found matching the given criteria."

    lines = [f"EPA Toxics Release Inventory ({len(data)} results):\n"]

    for record in data:
        fac_name = record.get("FAC_NAME", "Unknown")
        fac_city = record.get("FAC_CITY", "")
        fac_state = record.get("FAC_STATE", "")
        fac_zip = record.get("FAC_ZIP", "")
        county = record.get("FAC_COUNTY", "")
        tri_id = record.get("TRI_FACILITY_ID", "N/A")
        reporting_year = record.get("REPORTING_YEAR", "N/A")
        industry = record.get("PRIMARY_SIC", "")
        latitude = record.get("FAC_LATITUDE", "")
        longitude = record.get("FAC_LONGITUDE", "")

        location = ", ".join(p for p in [fac_city, fac_state, fac_zip] if p)

        lines.append(f"**{fac_name}**")
        lines.append(f"  TRI ID: {tri_id}")
        lines.append(f"  Location: {location or 'N/A'}")
        if county:
            lines.append(f"  County: {county}")
        lines.append(f"  Reporting Year: {reporting_year}")
        if industry:
            lines.append(f"  Primary SIC: {industry}")
        if latitude and longitude:
            lines.append(f"  Coordinates: {latitude}, {longitude}")
        lines.append("")

    lines.append("_Source: EPA Envirofacts Toxics Release Inventory (TRI)_")

    return "\n".join(lines)
