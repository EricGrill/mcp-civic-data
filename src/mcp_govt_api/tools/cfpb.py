from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

CFPB_BASE_URL = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"


@mcp.tool()
async def search_cfpb_complaints(
    query: str = "",
    product: str = "",
    company: str = "",
    state: str = "",
    date_received_min: str = "",
    date_received_max: str = "",
    limit: int = 10,
) -> str:
    """Search the CFPB Consumer Complaint Database.

    The Consumer Financial Protection Bureau collects complaints about
    financial products and services. This tool searches complaints
    submitted by consumers against financial companies.

    Args:
        query: Search term in complaint narratives (e.g., 'mortgage', 'debt collection')
        product: Filter by product type (e.g., 'Mortgage', 'Credit card',
                 'Student loan', 'Debt collection', 'Credit reporting')
        company: Filter by company name (e.g., 'Bank of America', 'Wells Fargo')
        state: Two-letter US state code (e.g., 'CA', 'NY', 'TX')
        date_received_min: Start date in YYYY-MM-DD format (e.g., '2024-01-01')
        date_received_max: End date in YYYY-MM-DD format (e.g., '2024-12-31')
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of consumer complaints with product, issue, company, state,
        date received, and company response details.
    """
    limit = min(max(1, limit), 100)

    params = {
        "size": str(limit),
        "sort": "created_date_desc",
    }

    if query:
        params["search_term"] = query
    if product:
        params["product"] = product
    if company:
        params["company"] = company
    if state:
        params["state"] = state.upper()
    if date_received_min:
        params["date_received_min"] = date_received_min
    if date_received_max:
        params["date_received_max"] = date_received_max

    try:
        data = await fetch_json(CFPB_BASE_URL, params=params)
    except Exception as e:
        return f"Error fetching CFPB complaints: {e}"

    hits = data.get("hits", {}).get("hits", [])
    total = data.get("hits", {}).get("total", {}).get("value", 0)

    if not hits:
        filters = []
        if query:
            filters.append(f"query '{query}'")
        if product:
            filters.append(f"product '{product}'")
        if company:
            filters.append(f"company '{company}'")
        if state:
            filters.append(f"state '{state.upper()}'")
        filter_str = " and ".join(filters) if filters else "the given criteria"
        return f"No CFPB complaints found matching {filter_str}."

    lines = [f"CFPB Consumer Complaints ({len(hits)} of {total} total):\n"]

    for hit in hits:
        source = hit.get("_source", {})
        complaint_id = source.get("complaint_id", "N/A")
        prod = source.get("product", "N/A")
        sub_product = source.get("sub_product", "")
        issue = source.get("issue", "N/A")
        sub_issue = source.get("sub_issue", "")
        comp = source.get("company", "N/A")
        comp_state = source.get("state", "N/A")
        date_received = source.get("date_received", "N/A")
        company_response = source.get("company_response", "N/A")
        timely = source.get("timely", "N/A")
        consumer_disputed = source.get("consumer_disputed", "N/A")

        lines.append(f"**Complaint #{complaint_id}**")
        product_str = f"{prod} — {sub_product}" if sub_product else prod
        lines.append(f"  Product: {product_str}")
        issue_str = f"{issue} — {sub_issue}" if sub_issue else issue
        lines.append(f"  Issue: {issue_str}")
        lines.append(f"  Company: {comp}")
        lines.append(f"  State: {comp_state}")
        lines.append(f"  Date Received: {date_received}")
        lines.append(f"  Company Response: {company_response}")
        lines.append(f"  Timely Response: {timely}")
        if consumer_disputed and consumer_disputed != "N/A":
            lines.append(f"  Consumer Disputed: {consumer_disputed}")
        lines.append("")

    lines.append(f"\n_Total matching complaints: {total}_")
    lines.append("_Source: CFPB Consumer Complaint Database_")

    return "\n".join(lines)


@mcp.tool()
async def get_cfpb_complaint(complaint_id: str) -> str:
    """Get details of a specific CFPB consumer complaint by ID.

    Retrieves the full details of a single consumer complaint from the
    CFPB Consumer Complaint Database.

    Args:
        complaint_id: The CFPB complaint ID number (e.g., '3648850')

    Returns:
        Full complaint details including product, issue, company, narrative,
        company response, and resolution status.
    """
    if not complaint_id:
        return "Error: complaint_id is required."

    url = f"{CFPB_BASE_URL}{complaint_id}"

    try:
        data = await fetch_json(url)
    except Exception as e:
        return f"Error fetching CFPB complaint {complaint_id}: {e}"

    source = data.get("_source", data)
    if not source:
        return f"No complaint found with ID {complaint_id}."

    cid = source.get("complaint_id", complaint_id)
    product = source.get("product", "N/A")
    sub_product = source.get("sub_product", "")
    issue = source.get("issue", "N/A")
    sub_issue = source.get("sub_issue", "")
    company = source.get("company", "N/A")
    state = source.get("state", "N/A")
    zip_code = source.get("zip_code", "N/A")
    date_received = source.get("date_received", "N/A")
    date_sent = source.get("date_sent_to_company", "N/A")
    company_response = source.get("company_response", "N/A")
    company_public_response = source.get("company_public_response", "")
    timely = source.get("timely", "N/A")
    consumer_disputed = source.get("consumer_disputed", "")
    consumer_consent = source.get("consumer_consent_provided", "")
    submitted_via = source.get("submitted_via", "N/A")
    narrative = source.get("complaint_what_happened", "")
    tags = source.get("tags", "")

    lines = [f"**CFPB Complaint #{cid}**\n"]

    product_str = f"{product} — {sub_product}" if sub_product else product
    lines.append(f"Product: {product_str}")
    issue_str = f"{issue} — {sub_issue}" if sub_issue else issue
    lines.append(f"Issue: {issue_str}")
    lines.append(f"Company: {company}")
    lines.append(f"State: {state}")
    lines.append(f"ZIP Code: {zip_code}")
    lines.append(f"Date Received: {date_received}")
    lines.append(f"Date Sent to Company: {date_sent}")
    lines.append(f"Submitted Via: {submitted_via}")
    if tags:
        lines.append(f"Tags: {tags}")
    lines.append("")
    lines.append(f"**Company Response:** {company_response}")
    if company_public_response:
        lines.append(f"**Public Response:** {company_public_response}")
    lines.append(f"Timely Response: {timely}")
    if consumer_disputed:
        lines.append(f"Consumer Disputed: {consumer_disputed}")
    if consumer_consent:
        lines.append(f"Consumer Consent Provided: {consumer_consent}")

    if narrative:
        lines.append("\n**Consumer Narrative:**")
        if len(narrative) > 1000:
            lines.append(narrative[:1000] + "...")
        else:
            lines.append(narrative)

    lines.append("\n_Source: CFPB Consumer Complaint Database_")

    return "\n".join(lines)


@mcp.tool()
async def get_cfpb_complaint_stats(
    product: str = "",
    company: str = "",
    state: str = "",
    date_received_min: str = "",
    date_received_max: str = "",
) -> str:
    """Get aggregate statistics on CFPB consumer complaints.

    Queries the CFPB Consumer Complaint Database to provide summary
    statistics, including total complaint counts broken down by product,
    issue, and company response type.

    Args:
        product: Filter by product type (e.g., 'Mortgage', 'Credit card')
        company: Filter by company name (e.g., 'Bank of America')
        state: Two-letter US state code (e.g., 'CA', 'NY')
        date_received_min: Start date in YYYY-MM-DD format
        date_received_max: End date in YYYY-MM-DD format

    Returns:
        Summary statistics including total complaints, top products,
        top issues, and company response breakdown.
    """
    params = {
        "size": "0",
        "sort": "created_date_desc",
    }

    if product:
        params["product"] = product
    if company:
        params["company"] = company
    if state:
        params["state"] = state.upper()
    if date_received_min:
        params["date_received_min"] = date_received_min
    if date_received_max:
        params["date_received_max"] = date_received_max

    try:
        data = await fetch_json(CFPB_BASE_URL, params=params)
    except Exception as e:
        return f"Error fetching CFPB complaint stats: {e}"

    total = data.get("hits", {}).get("total", {}).get("value", 0)

    aggs = data.get("aggregations", {})

    lines = ["**CFPB Consumer Complaint Statistics**\n"]

    filter_parts = []
    if product:
        filter_parts.append(f"Product: {product}")
    if company:
        filter_parts.append(f"Company: {company}")
    if state:
        filter_parts.append(f"State: {state.upper()}")
    if date_received_min or date_received_max:
        date_range = f"{date_received_min or 'start'} to {date_received_max or 'present'}"
        filter_parts.append(f"Date Range: {date_range}")

    if filter_parts:
        lines.append("Filters: " + ", ".join(filter_parts))

    lines.append(f"Total Complaints: {total:,}\n")

    product_agg = aggs.get("product", {})
    product_buckets = product_agg.get("product", {}).get("buckets", [])
    if product_buckets:
        lines.append("**Top Products:**")
        for bucket in product_buckets[:10]:
            key = bucket.get("key", "Unknown")
            count = bucket.get("doc_count", 0)
            lines.append(f"  - {key}: {count:,}")
        lines.append("")

    issue_agg = aggs.get("issue", {})
    issue_buckets = issue_agg.get("issue", {}).get("buckets", [])
    if issue_buckets:
        lines.append("**Top Issues:**")
        for bucket in issue_buckets[:10]:
            key = bucket.get("key", "Unknown")
            count = bucket.get("doc_count", 0)
            lines.append(f"  - {key}: {count:,}")
        lines.append("")

    company_response_agg = aggs.get("company_response", {})
    response_buckets = company_response_agg.get("company_response", {}).get("buckets", [])
    if response_buckets:
        lines.append("**Company Response Breakdown:**")
        for bucket in response_buckets[:10]:
            key = bucket.get("key", "Unknown")
            count = bucket.get("doc_count", 0)
            lines.append(f"  - {key}: {count:,}")
        lines.append("")

    company_agg = aggs.get("company", {})
    company_buckets = company_agg.get("company", {}).get("buckets", [])
    if company_buckets:
        lines.append("**Top Companies by Complaint Volume:**")
        for bucket in company_buckets[:10]:
            key = bucket.get("key", "Unknown")
            count = bucket.get("doc_count", 0)
            lines.append(f"  - {key}: {count:,}")
        lines.append("")

    if not any([product_buckets, issue_buckets, response_buckets, company_buckets]):
        lines.append("No aggregation data available for the given filters.")

    lines.append("_Source: CFPB Consumer Complaint Database_")

    return "\n".join(lines)
