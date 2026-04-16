from mcp_govt_api.server import mcp
from mcp_govt_api.utils.errors import handle_api_error
from mcp_govt_api.utils.http import fetch_json

FDA_BASE_URL = "https://api.fda.gov"


@mcp.tool()
@handle_api_error(context="FDA API")
async def search_fda_recalls(
    query: str = "",
    state: str = "",
    category: str = "drug",
    limit: int = 10,
) -> str:
    """Search FDA enforcement actions and recall reports.

    Searches the openFDA enforcement endpoint for recalls across drugs,
    food, and medical devices. Can filter by keyword, state, and product
    category.

    Args:
        query: Search term for recall reason or product description
        state: Two-letter US state code to filter by (e.g., 'CA', 'NY')
        category: Product category — 'drug', 'food', or 'device' (default: 'drug')
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of recall reports with classification, product description,
        recalling firm, reason, and status.
    """
    category = category.lower()
    if category not in ("drug", "food", "device"):
        return "Error: category must be 'drug', 'food', or 'device'."

    limit = min(max(1, limit), 100)

    url = f"{FDA_BASE_URL}/{category}/enforcement.json"

    search_parts = []
    if query:
        search_parts.append(f'reason_for_recall:"{query}"')
    if state:
        search_parts.append(f'state:"{state.upper()}"')

    params = {"limit": str(limit)}
    if search_parts:
        params["search"] = "+AND+".join(search_parts)

    data = await fetch_json(url, params=params)

    results = data.get("results", [])
    if not results:
        return f"No {category} recall reports found matching the given criteria."

    total = data.get("meta", {}).get("results", {}).get("total", len(results))

    lines = [f"FDA {category.title()} Recall Reports ({len(results)} of {total} total):\n"]

    for r in results:
        classification = r.get("classification", "Unknown")
        product = r.get("product_description", "N/A")
        firm = r.get("recalling_firm", "Unknown")
        reason = r.get("reason_for_recall", "N/A")
        status = r.get("status", "Unknown")
        recall_date = r.get("recall_initiation_date", "Unknown")
        city = r.get("city", "")
        st = r.get("state", "")
        location = f"{city}, {st}" if city and st else city or st or "Unknown"

        lines.append(f"**{classification}** — {firm}")
        lines.append(f"  Product: {product}")
        lines.append(f"  Reason: {reason}")
        lines.append(f"  Status: {status}")
        lines.append(f"  Date: {recall_date}")
        lines.append(f"  Location: {location}")
        lines.append("")

    lines.append(f"_Source: openFDA {category.title()} Enforcement_")

    return "\n".join(lines)


@mcp.tool()
@handle_api_error(context="FDA API")
async def get_fda_adverse_events(
    drug_name: str,
    limit: int = 10,
) -> str:
    """Search FDA drug adverse event reports (FAERS).

    Queries the FDA Adverse Event Reporting System for reports associated
    with a given drug name. Returns serious outcomes, patient reactions,
    and report details.

    Args:
        drug_name: Brand or generic drug name to search (e.g., 'aspirin', 'lipitor')
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of adverse event reports with patient reactions, outcomes,
        and seriousness indicators.
    """
    if not drug_name:
        return "Error: drug_name is required."

    limit = min(max(1, limit), 100)

    url = f"{FDA_BASE_URL}/drug/event.json"
    params = {
        "search": f'patient.drug.openfda.brand_name:"{drug_name}"',
        "limit": str(limit),
    }

    data = await fetch_json(url, params=params)

    results = data.get("results", [])
    if not results:
        return f"No adverse event reports found for drug '{drug_name}'."

    total = data.get("meta", {}).get("results", {}).get("total", len(results))

    lines = [f"FDA Adverse Event Reports for '{drug_name}' ({len(results)} of {total} total):\n"]

    for r in results:
        receive_date = r.get("receivedate", "Unknown")
        serious = r.get("serious", "0")
        serious_label = "Yes" if str(serious) == "1" else "No"

        # Get patient reactions
        reactions = r.get("patient", {}).get("reaction", [])
        reaction_names = [rx.get("reactionmeddrapt", "") for rx in reactions if rx.get("reactionmeddrapt")]
        reactions_str = ", ".join(reaction_names[:5]) if reaction_names else "N/A"

        # Get outcome
        outcomes_map = {
            "1": "Recovered",
            "2": "Recovering",
            "3": "Not recovered",
            "4": "Recovered with sequelae",
            "5": "Fatal",
            "6": "Unknown",
        }
        patient_outcome = ""
        for rx in reactions:
            outcome_code = str(rx.get("reactionoutcome", ""))
            if outcome_code in outcomes_map:
                patient_outcome = outcomes_map[outcome_code]
                break
        if not patient_outcome:
            patient_outcome = "Unknown"

        # Get drugs involved
        drugs = r.get("patient", {}).get("drug", [])
        drug_names = []
        for d in drugs:
            name = d.get("openfda", {}).get("brand_name", [""])[0] or d.get("medicinalproduct", "")
            if name:
                drug_names.append(name)
        drugs_str = ", ".join(drug_names[:5]) if drug_names else "N/A"

        lines.append(f"**Report Date: {receive_date}**")
        lines.append(f"  Serious: {serious_label}")
        lines.append(f"  Reactions: {reactions_str}")
        lines.append(f"  Outcome: {patient_outcome}")
        lines.append(f"  Drugs Involved: {drugs_str}")
        lines.append("")

    lines.append(f"_Source: openFDA Drug Adverse Events (FAERS)_")

    return "\n".join(lines)


@mcp.tool()
@handle_api_error(context="FDA API")
async def get_fda_drug_labels(
    drug_name: str,
    limit: int = 5,
) -> str:
    """Search FDA drug labeling and SPL (Structured Product Labeling) data.

    Retrieves drug label information including indications, warnings,
    dosage, and active ingredients for a given drug name.

    Args:
        drug_name: Brand or generic drug name to search (e.g., 'ibuprofen', 'metformin')
        limit: Maximum number of results to return (default: 5, max: 25)

    Returns:
        Drug label information including brand name, generic name,
        indications, warnings, and dosage instructions.
    """
    if not drug_name:
        return "Error: drug_name is required."

    limit = min(max(1, limit), 25)

    url = f"{FDA_BASE_URL}/drug/label.json"
    params = {
        "search": f'openfda.brand_name:"{drug_name}"',
        "limit": str(limit),
    }

    data = await fetch_json(url, params=params)

    results = data.get("results", [])
    if not results:
        return f"No drug label information found for '{drug_name}'."

    total = data.get("meta", {}).get("results", {}).get("total", len(results))

    lines = [f"FDA Drug Label Information for '{drug_name}' ({len(results)} of {total} total):\n"]

    for r in results:
        openfda = r.get("openfda", {})
        brand_names = openfda.get("brand_name", [])
        generic_names = openfda.get("generic_name", [])
        manufacturer = openfda.get("manufacturer_name", [])
        route = openfda.get("route", [])

        brand = ", ".join(brand_names) if brand_names else "N/A"
        generic = ", ".join(generic_names) if generic_names else "N/A"
        mfr = ", ".join(manufacturer) if manufacturer else "N/A"
        route_str = ", ".join(route) if route else "N/A"

        # Get key label sections (they are arrays of strings)
        indications = r.get("indications_and_usage", ["N/A"])[0]
        warnings = r.get("warnings", ["N/A"])[0]
        dosage = r.get("dosage_and_administration", ["N/A"])[0]

        # Truncate long text
        if len(indications) > 300:
            indications = indications[:300] + "..."
        if len(warnings) > 300:
            warnings = warnings[:300] + "..."
        if len(dosage) > 300:
            dosage = dosage[:300] + "..."

        lines.append(f"**{brand}**")
        lines.append(f"  Generic Name: {generic}")
        lines.append(f"  Manufacturer: {mfr}")
        lines.append(f"  Route: {route_str}")
        lines.append(f"  Indications: {indications}")
        lines.append(f"  Warnings: {warnings}")
        lines.append(f"  Dosage: {dosage}")
        lines.append("")

    lines.append(f"_Source: openFDA Drug Labels (SPL)_")

    return "\n".join(lines)
