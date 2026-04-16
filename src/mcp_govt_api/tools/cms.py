from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

CMS_BASE_URL = "https://data.cms.gov/resource"

HOSPITAL_GENERAL_INFO = f"{CMS_BASE_URL}/xubh-q36u.json"
MEDICARE_PROVIDERS = f"{CMS_BASE_URL}/mj5m-pzi6.json"


@mcp.tool()
async def search_hospitals(
    name: str = "",
    state: str = "",
    limit: int = 10,
) -> str:
    """Search hospitals by name or state with overall quality ratings.

    Queries the CMS Hospital General Information dataset for hospitals
    matching the given name and/or state. Returns hospital name, address,
    type, ownership, and overall quality rating (1-5 stars).

    Args:
        name: Hospital name or partial name to search for (case-insensitive)
        state: Two-letter US state code to filter by (e.g., 'CA', 'NY')
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of hospitals with name, address, type, ownership, and
        overall quality rating.
    """
    if not name and not state:
        return "Error: at least one of 'name' or 'state' is required."

    limit = min(max(1, limit), 100)

    where_parts = []
    if name:
        where_parts.append(f"upper(hospital_name) like '%{name.upper()}%'")
    if state:
        where_parts.append(f"state='{state.upper()}'")

    params = {
        "$where": " AND ".join(where_parts),
        "$limit": str(limit),
        "$order": "hospital_name ASC",
    }

    try:
        data = await fetch_json(HOSPITAL_GENERAL_INFO, params=params)
    except Exception as e:
        return f"Error fetching hospital data: {e}"

    if not data:
        return "No hospitals found matching the given criteria."

    lines = [f"CMS Hospital Search Results ({len(data)} hospitals):\n"]

    for h in data:
        hospital_name = h.get("hospital_name", "N/A")
        facility_id = h.get("facility_id", "N/A")
        address = h.get("address", "")
        city = h.get("city", "")
        st = h.get("state", "")
        zip_code = h.get("zip_code", "")
        full_address = ", ".join(filter(None, [address, city, st, zip_code]))
        hospital_type = h.get("hospital_type", "N/A")
        ownership = h.get("hospital_ownership", "N/A")
        rating = h.get("hospital_overall_rating", "Not Available")
        phone = h.get("phone_number", "N/A")

        lines.append(f"**{hospital_name}** (ID: {facility_id})")
        lines.append(f"  Address: {full_address or 'N/A'}")
        lines.append(f"  Type: {hospital_type}")
        lines.append(f"  Ownership: {ownership}")
        lines.append(f"  Overall Rating: {rating} / 5")
        lines.append(f"  Phone: {phone}")
        lines.append("")

    lines.append("_Source: CMS Hospital General Information (Hospital Compare)_")

    return "\n".join(lines)


@mcp.tool()
async def get_hospital_quality(
    facility_id: str,
) -> str:
    """Get detailed quality measures and ratings for a specific hospital.

    Retrieves comprehensive hospital quality data from CMS including
    overall rating, mortality, safety, readmission, patient experience,
    and timeliness scores for a given facility ID.

    Args:
        facility_id: CMS facility ID (e.g., '050001'). Use search_hospitals
            to find facility IDs.

    Returns:
        Detailed hospital quality information including overall rating,
        type, ownership, emergency services status, and quality measure
        footnotes.
    """
    if not facility_id:
        return "Error: facility_id is required."

    params = {
        "$where": f"facility_id='{facility_id}'",
        "$limit": "1",
    }

    try:
        data = await fetch_json(HOSPITAL_GENERAL_INFO, params=params)
    except Exception as e:
        return f"Error fetching hospital quality data: {e}"

    if not data:
        return f"No hospital found with facility ID '{facility_id}'."

    h = data[0]

    hospital_name = h.get("hospital_name", "N/A")
    address = h.get("address", "")
    city = h.get("city", "")
    st = h.get("state", "")
    zip_code = h.get("zip_code", "")
    full_address = ", ".join(filter(None, [address, city, st, zip_code]))
    hospital_type = h.get("hospital_type", "N/A")
    ownership = h.get("hospital_ownership", "N/A")
    emergency = h.get("emergency_services", "N/A")
    phone = h.get("phone_number", "N/A")

    overall_rating = h.get("hospital_overall_rating", "Not Available")
    mortality = h.get("mortality_national_comparison", "N/A")
    safety = h.get("safety_of_care_national_comparison", "N/A")
    readmission = h.get("readmission_national_comparison", "N/A")
    patient_exp = h.get("patient_experience_national_comparison", "N/A")
    effectiveness = h.get("effectiveness_of_care_national_comparison", "N/A")
    timeliness = h.get("timeliness_of_care_national_comparison", "N/A")

    lines = [
        f"Hospital Quality Report for {hospital_name} (ID: {facility_id}):\n",
        f"**{hospital_name}**",
        f"  Address: {full_address or 'N/A'}",
        f"  Phone: {phone}",
        f"  Type: {hospital_type}",
        f"  Ownership: {ownership}",
        f"  Emergency Services: {emergency}",
        "",
        "Quality Ratings:",
        f"  Overall Rating: {overall_rating} / 5",
        f"  Mortality: {mortality}",
        f"  Safety of Care: {safety}",
        f"  Readmission: {readmission}",
        f"  Patient Experience: {patient_exp}",
        f"  Effectiveness of Care: {effectiveness}",
        f"  Timeliness of Care: {timeliness}",
        "",
        "_Source: CMS Hospital General Information (Hospital Compare)_",
    ]

    return "\n".join(lines)


@mcp.tool()
async def search_medicare_providers(
    name: str = "",
    state: str = "",
    specialty: str = "",
    limit: int = 10,
) -> str:
    """Search Medicare-enrolled healthcare providers.

    Queries the CMS Medicare provider dataset for providers matching
    the given name, state, and/or specialty. Returns provider details
    including name, specialty, address, and enrollment information.

    Args:
        name: Provider last name or organization name (case-insensitive)
        state: Two-letter US state code to filter by (e.g., 'CA', 'NY')
        specialty: Medical specialty to filter by (e.g., 'Internal Medicine',
            'Cardiology', 'Family Practice')
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of Medicare providers with name, specialty, address,
        and enrollment details.
    """
    if not name and not state and not specialty:
        return "Error: at least one of 'name', 'state', or 'specialty' is required."

    limit = min(max(1, limit), 100)

    where_parts = []
    if name:
        where_parts.append(f"upper(org_name) like '%{name.upper()}%' OR upper(lst_nm) like '%{name.upper()}%'")
    if state:
        where_parts.append(f"st='{state.upper()}'")
    if specialty:
        where_parts.append(f"upper(pri_spec) like '%{specialty.upper()}%'")

    params = {
        "$where": " AND ".join(where_parts),
        "$limit": str(limit),
        "$order": "lst_nm ASC",
    }

    try:
        data = await fetch_json(MEDICARE_PROVIDERS, params=params)
    except Exception as e:
        return f"Error fetching Medicare provider data: {e}"

    if not data:
        return "No Medicare providers found matching the given criteria."

    lines = [f"CMS Medicare Provider Search Results ({len(data)} providers):\n"]

    for p in data:
        # Handle individual vs organization
        org_name = p.get("org_name", "")
        first_name = p.get("frst_nm", "")
        last_name = p.get("lst_nm", "")
        if org_name:
            display_name = org_name
        elif first_name or last_name:
            display_name = f"{first_name} {last_name}".strip()
        else:
            display_name = "N/A"

        npi = p.get("npi", "N/A")
        spec = p.get("pri_spec", "N/A")
        city = p.get("cty", "")
        st = p.get("st", "")
        zip_code = p.get("zip", "")
        location = ", ".join(filter(None, [city, st, zip_code]))
        credential = p.get("cred", "")

        lines.append(f"**{display_name}**{f' ({credential})' if credential else ''}")
        lines.append(f"  NPI: {npi}")
        lines.append(f"  Specialty: {spec}")
        lines.append(f"  Location: {location or 'N/A'}")
        lines.append("")

    lines.append("_Source: CMS Medicare Provider Data_")

    return "\n".join(lines)
