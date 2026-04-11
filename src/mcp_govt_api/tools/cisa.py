from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json
import xml.etree.ElementTree as ET
import httpx

CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
CISA_ALERTS_URL = "https://www.cisa.gov/news.xml"
CISA_BULLETINS_URL = "https://www.cisa.gov/bulletins.xml"

http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(30),
    follow_redirects=True,
    headers={"User-Agent": "mcp-civic-data/0.1.0"},
)


@mcp.tool()
async def search_known_exploited_vulnerabilities(
    vendor: str = "",
    product: str = "",
    cve_id: str = "",
    limit: int = 10,
) -> str:
    """Search CISA's Known Exploited Vulnerabilities (KEV) catalog.

    This catalog contains vulnerabilities that have been exploited in the wild
    and are actively being used by attackers. CISA requires federal agencies
    to remediate these vulnerabilities according to specified due dates.

    Args:
        vendor: Filter by vendor name (e.g., 'Microsoft', 'Adobe', 'Cisco')
        product: Filter by product name (e.g., 'Windows', 'Acrobat', 'IOS')
        cve_id: Search for a specific CVE ID (e.g., 'CVE-2021-44228')
        limit: Maximum number of results to return (default: 10, max: 100)

    Returns:
        List of known exploited vulnerabilities matching the criteria, including
        CVE ID, vendor/product, vulnerability name, remediation due date, and
        required action.
    """
    try:
        data = await fetch_json(CISA_KEV_URL)
    except Exception as e:
        return f"Error fetching KEV catalog: {e}"

    vulnerabilities = data.get("vulnerabilities", [])
    
    if not vulnerabilities:
        return "No vulnerabilities found in the KEV catalog."

    # Apply filters
    filtered = vulnerabilities
    
    if cve_id:
        cve_upper = cve_id.upper()
        filtered = [v for v in filtered if v.get("cveID", "").upper() == cve_upper]
    else:
        if vendor:
            vendor_lower = vendor.lower()
            filtered = [v for v in filtered if vendor_lower in v.get("vendorProject", "").lower()]
        
        if product:
            product_lower = product.lower()
            filtered = [v for v in filtered if product_lower in v.get("product", "").lower()]

    if not filtered:
        filters = []
        if cve_id:
            filters.append(f"CVE ID '{cve_id}'")
        if vendor:
            filters.append(f"vendor '{vendor}'")
        if product:
            filters.append(f"product '{product}'")
        filter_str = " and ".join(filters)
        return f"No known exploited vulnerabilities found matching {filter_str}."

    # Sort by date added (most recent first)
    filtered.sort(key=lambda x: x.get("dateAdded", ""), reverse=True)
    
    results = filtered[:min(limit, 100)]
    
    lines = [f"CISA Known Exploited Vulnerabilities ({len(results)} of {len(filtered)} total):\n"]
    
    for v in results:
        cve = v.get("cveID", "N/A")
        vendor_project = v.get("vendorProject", "Unknown")
        product_name = v.get("product", "Unknown")
        vuln_name = v.get("vulnerabilityName", "Unknown")
        date_added = v.get("dateAdded", "Unknown")
        due_date = v.get("dueDate", "Unknown")
        action = v.get("requiredAction", "No action specified")
        
        lines.append(f"**{cve}** — {vuln_name}")
        lines.append(f"  Vendor: {vendor_project}")
        lines.append(f"  Product: {product_name}")
        lines.append(f"  Date Added: {date_added}")
        lines.append(f"  Remediation Due: {due_date}")
        lines.append(f"  Required Action: {action}")
        lines.append("")

    lines.append(f"\n_Total matching vulnerabilities: {len(filtered)}_")
    lines.append(f"_Source: CISA Known Exploited Vulnerabilities Catalog_")
    
    return "\n".join(lines)


@mcp.tool()
async def get_recent_cisa_alerts(limit: int = 5) -> str:
    """Get recent CISA security alerts and advisories.

    CISA publishes alerts about current security issues, vulnerabilities,
    and threats that require immediate attention.

    Args:
        limit: Number of recent alerts to return (default: 5, max: 20)

    Returns:
        Recent CISA alerts with titles, publication dates, and links to full advisories.
    """
    limit = min(limit, 20)
    
    try:
        response = await http_client.get(CISA_ALERTS_URL)
        response.raise_for_status()
        xml_content = response.text
    except Exception as e:
        return f"Error fetching CISA alerts: {e}"

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        return f"Error parsing CISA alerts feed: {e}"

    # Define namespace
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    
    entries = root.findall("atom:entry", ns)
    
    if not entries:
        # Try without namespace
        entries = root.findall("entry")
    
    if not entries:
        return "No recent alerts found from CISA."

    lines = [f"Recent CISA Security Alerts ({min(limit, len(entries))} of {len(entries)} total):\n"]
    
    for entry in entries[:limit]:
        # Try with namespace first, then without
        title = entry.find("atom:title", ns)
        if title is None:
            title = entry.find("title")
        title_text = title.text if title is not None else "No title"
        
        published = entry.find("atom:published", ns)
        if published is None:
            published = entry.find("published")
        published_text = published.text[:10] if published is not None else "Unknown date"
        
        link = entry.find("atom:link", ns)
        if link is None:
            link = entry.find("link")
        link_href = link.get("href") if link is not None else None
        
        summary = entry.find("atom:summary", ns)
        if summary is None:
            summary = entry.find("summary")
        summary_text = summary.text if summary is not None else ""
        
        lines.append(f"**{title_text}**")
        lines.append(f"  Published: {published_text}")
        if link_href:
            lines.append(f"  Link: {link_href}")
        if summary_text:
            # Clean up HTML tags if present
            import re
            clean_summary = re.sub(r'<[^>]+>', '', summary_text)
            if len(clean_summary) > 200:
                clean_summary = clean_summary[:200] + "..."
            lines.append(f"  Summary: {clean_summary}")
        lines.append("")

    lines.append(f"_Source: CISA Security Alerts_")
    
    return "\n".join(lines)


@mcp.tool()
async def get_cisa_bulletins(limit: int = 5) -> str:
    """Get recent CISA bulletins with summarized vulnerability information.

    CISA bulletins provide weekly summaries of new vulnerabilities and
    security updates from major vendors.

    Args:
        limit: Number of recent bulletins to return (default: 5, max: 10)

    Returns:
        Recent CISA bulletins with publication dates and links.
    """
    limit = min(limit, 10)
    
    try:
        response = await http_client.get(CISA_BULLETINS_URL)
        response.raise_for_status()
        xml_content = response.text
    except Exception as e:
        return f"Error fetching CISA bulletins: {e}"

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        return f"Error parsing CISA bulletins feed: {e}"

    # Define namespace
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    
    entries = root.findall("atom:entry", ns)
    
    if not entries:
        # Try without namespace
        entries = root.findall("entry")
    
    if not entries:
        return "No recent bulletins found from CISA."

    lines = [f"Recent CISA Bulletins ({min(limit, len(entries))} of {len(entries)} total):\n"]
    
    for entry in entries[:limit]:
        title = entry.find("atom:title", ns)
        if title is None:
            title = entry.find("title")
        title_text = title.text if title is not None else "No title"
        
        published = entry.find("atom:published", ns)
        if published is None:
            published = entry.find("published")
        published_text = published.text[:10] if published is not None else "Unknown date"
        
        link = entry.find("atom:link", ns)
        if link is None:
            link = entry.find("link")
        link_href = link.get("href") if link is not None else None
        
        lines.append(f"**{title_text}**")
        lines.append(f"  Published: {published_text}")
        if link_href:
            lines.append(f"  Link: {link_href}")
        lines.append("")

    lines.append(f"_Source: CISA Weekly Bulletins_")
    
    return "\n".join(lines)


@mcp.tool()
async def query_cisa_kev() -> dict:
    """Get the raw CISA Known Exploited Vulnerabilities catalog data.

    Returns:
        Complete raw JSON data from the CISA KEV catalog API.
    """
    return await fetch_json(CISA_KEV_URL)
