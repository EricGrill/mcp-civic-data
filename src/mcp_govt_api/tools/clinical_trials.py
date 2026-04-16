from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

CLINICAL_TRIALS_BASE = "https://clinicaltrials.gov/api/v2"


@mcp.tool()
async def search_clinical_trials(
    query: str = "",
    condition: str = "",
    intervention: str = "",
    status: str = "",
    limit: int = 10,
) -> str:
    """Search ClinicalTrials.gov for clinical studies.

    Search the federal database of clinical studies conducted around the world.
    Filter by keyword, medical condition, intervention/treatment, or recruitment
    status.

    Args:
        query: General search term (e.g., 'cancer', 'diabetes vaccine')
        condition: Filter by medical condition or disease (e.g., 'breast cancer', 'asthma')
        intervention: Filter by intervention or treatment (e.g., 'pembrolizumab', 'radiation')
        status: Filter by recruitment status (e.g., 'RECRUITING', 'COMPLETED', 'ACTIVE_NOT_RECRUITING')
        limit: Maximum number of results to return (default: 10, max: 50)

    Returns:
        List of matching clinical trials with titles, status, conditions, and NCT IDs.
    """
    limit = min(max(1, limit), 50)

    params: dict = {"pageSize": str(limit), "format": "json"}
    if query:
        params["query.term"] = query
    if condition:
        params["query.cond"] = condition
    if intervention:
        params["query.intr"] = intervention
    if status:
        params["filter.overallStatus"] = status

    try:
        data = await fetch_json(f"{CLINICAL_TRIALS_BASE}/studies", params=params)
    except Exception as e:
        return f"Error searching clinical trials: {e}"

    studies = data.get("studies", [])
    if not studies:
        filters = []
        if query:
            filters.append(f"query '{query}'")
        if condition:
            filters.append(f"condition '{condition}'")
        if intervention:
            filters.append(f"intervention '{intervention}'")
        if status:
            filters.append(f"status '{status}'")
        filter_str = " and ".join(filters) if filters else "the given criteria"
        return f"No clinical trials found matching {filter_str}."

    total = data.get("totalCount", len(studies))
    lines = [f"ClinicalTrials.gov Search Results ({len(studies)} of {total} studies):\n"]

    for study in studies:
        protocol = study.get("protocolSection", {})
        id_module = protocol.get("identificationModule", {})
        status_module = protocol.get("statusModule", {})
        conditions_module = protocol.get("conditionsModule", {})
        design_module = protocol.get("designModule", {})

        nct_id = id_module.get("nctId", "N/A")
        title = id_module.get("briefTitle", "Untitled")
        overall_status = status_module.get("overallStatus", "Unknown")
        start_date = status_module.get("startDateStruct", {}).get("date", "")
        conditions = conditions_module.get("conditions", [])
        study_type = design_module.get("studyType", "")
        phases = design_module.get("phases", [])

        lines.append(f"**{title}**")
        lines.append(f"  NCT ID: {nct_id}")
        lines.append(f"  Status: {overall_status}")
        if study_type:
            lines.append(f"  Study Type: {study_type}")
        if phases:
            lines.append(f"  Phase: {', '.join(phases)}")
        if conditions:
            lines.append(f"  Conditions: {', '.join(conditions[:5])}")
        if start_date:
            lines.append(f"  Start Date: {start_date}")
        lines.append(f"  URL: https://clinicaltrials.gov/study/{nct_id}")
        lines.append("")

    lines.append("_Source: ClinicalTrials.gov_")

    return "\n".join(lines)


@mcp.tool()
async def get_clinical_trial(
    nct_id: str,
) -> str:
    """Get detailed information about a specific clinical trial by NCT ID.

    Retrieves full protocol details for a single study registered on
    ClinicalTrials.gov, including eligibility criteria, study design,
    sponsors, and outcome measures.

    Args:
        nct_id: The NCT identifier (e.g., 'NCT04280705')

    Returns:
        Detailed study information including design, eligibility, sponsors, and contacts.
    """
    nct_id = nct_id.strip().upper()
    if not nct_id.startswith("NCT"):
        return "Error: NCT ID must start with 'NCT' (e.g., 'NCT04280705')."

    try:
        data = await fetch_json(
            f"{CLINICAL_TRIALS_BASE}/studies/{nct_id}",
            params={"format": "json"},
        )
    except Exception as e:
        return f"Error fetching clinical trial {nct_id}: {e}"

    protocol = data.get("protocolSection", {})
    if not protocol:
        return f"No data found for clinical trial {nct_id}."

    id_module = protocol.get("identificationModule", {})
    status_module = protocol.get("statusModule", {})
    description_module = protocol.get("descriptionModule", {})
    conditions_module = protocol.get("conditionsModule", {})
    design_module = protocol.get("designModule", {})
    eligibility_module = protocol.get("eligibilityModule", {})
    sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
    arms_module = protocol.get("armsInterventionsModule", {})

    title = id_module.get("briefTitle", "Untitled")
    official_title = id_module.get("officialTitle", "")
    overall_status = status_module.get("overallStatus", "Unknown")
    start_date = status_module.get("startDateStruct", {}).get("date", "")
    completion_date = status_module.get("completionDateStruct", {}).get("date", "")
    brief_summary = description_module.get("briefSummary", "")
    conditions = conditions_module.get("conditions", [])
    study_type = design_module.get("studyType", "")
    phases = design_module.get("phases", [])
    enrollment = design_module.get("enrollmentInfo", {})

    lines = [f"# {title}\n"]
    lines.append(f"**NCT ID:** {nct_id}")
    if official_title and official_title != title:
        lines.append(f"**Official Title:** {official_title}")
    lines.append(f"**Status:** {overall_status}")
    if study_type:
        lines.append(f"**Study Type:** {study_type}")
    if phases:
        lines.append(f"**Phase:** {', '.join(phases)}")
    if enrollment:
        count = enrollment.get("count", "")
        enroll_type = enrollment.get("type", "")
        if count:
            lines.append(f"**Enrollment:** {count} ({enroll_type})")
    if start_date:
        lines.append(f"**Start Date:** {start_date}")
    if completion_date:
        lines.append(f"**Completion Date:** {completion_date}")
    lines.append("")

    if conditions:
        lines.append(f"**Conditions:** {', '.join(conditions)}")
        lines.append("")

    if brief_summary:
        if len(brief_summary) > 500:
            brief_summary = brief_summary[:500] + "..."
        lines.append(f"**Summary:** {brief_summary}")
        lines.append("")

    # Interventions
    interventions = arms_module.get("interventions", [])
    if interventions:
        lines.append("**Interventions:**")
        for intv in interventions[:10]:
            intv_type = intv.get("type", "")
            intv_name = intv.get("name", "")
            lines.append(f"  - {intv_type}: {intv_name}")
        lines.append("")

    # Eligibility
    if eligibility_module:
        lines.append("**Eligibility:**")
        min_age = eligibility_module.get("minimumAge", "")
        max_age = eligibility_module.get("maximumAge", "")
        sex = eligibility_module.get("sex", "")
        if min_age:
            lines.append(f"  Minimum Age: {min_age}")
        if max_age:
            lines.append(f"  Maximum Age: {max_age}")
        if sex:
            lines.append(f"  Sex: {sex}")
        lines.append("")

    # Sponsor
    lead_sponsor = sponsor_module.get("leadSponsor", {})
    if lead_sponsor:
        lines.append(f"**Lead Sponsor:** {lead_sponsor.get('name', 'N/A')}")
        collaborators = sponsor_module.get("collaborators", [])
        if collaborators:
            collab_names = [c.get("name", "") for c in collaborators[:5]]
            lines.append(f"**Collaborators:** {', '.join(collab_names)}")
        lines.append("")

    lines.append(f"**URL:** https://clinicaltrials.gov/study/{nct_id}")
    lines.append("")
    lines.append("_Source: ClinicalTrials.gov_")

    return "\n".join(lines)


@mcp.tool()
async def get_trial_statistics() -> str:
    """Get overall ClinicalTrials.gov database statistics.

    Returns the total number of studies registered in the ClinicalTrials.gov
    database, providing a snapshot of the current scope of the registry.

    Returns:
        Total study count and database overview.
    """
    try:
        data = await fetch_json(
            f"{CLINICAL_TRIALS_BASE}/stats/size",
            params={"format": "json"},
        )
    except Exception as e:
        return f"Error fetching ClinicalTrials.gov statistics: {e}"

    total = data.get("totalStudies", data.get("total", "Unknown"))

    lines = [
        "ClinicalTrials.gov Database Statistics:\n",
        f"**Total Registered Studies:** {total:,}" if isinstance(total, int) else f"**Total Registered Studies:** {total}",
        "",
        "ClinicalTrials.gov is a database of privately and publicly funded",
        "clinical studies conducted around the world.",
        "",
        "_Source: ClinicalTrials.gov_",
    ]

    return "\n".join(lines)
