"""CISA cybersecurity tools - Known Exploited Vulnerabilities and Alerts."""

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json


CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
CISA_ALERTS_URL = "https://www.cisa.gov/news.xml"


@mcp.tool()
async def get_kev_vulnerabilities(cve_id: str = None, limit: int = 20) -> str:
    """Get CISA Known Exploited Vulnerabilities (KEV) catalog.

    Args:
        cve_id: Filter by specific CVE ID (e.g., 'CVE-2023-4966')
        limit: Maximum number of vulnerabilities to return (default: 20)

    Returns:
        List of known exploited vulnerabilities with details
    """
    try:
        data = await fetch_json(CISA_KEV_URL)
        vulnerabilities = data.get("vulnerabilities", [])
        
        if cve_id:
            # Filter by specific CVE
            cve_upper = cve_id.upper()
            vulnerabilities = [
                v for v in vulnerabilities 
                if v.get("cveID", "").upper() == cve_upper
            ]
            if not vulnerabilities:
                return f"No vulnerability found with CVE ID: {cve_id}"
        
        # Limit results
        vulnerabilities = vulnerabilities[:limit]
        
        if not vulnerabilities:
            return "No known exploited vulnerabilities found."
        
        result = [f"**CISA Known Exploited Vulnerabilities** ({len(vulnerabilities)} shown)\n"]
        
        for v in vulnerabilities:
            cve = v.get("cveID", "N/A")
            vendor = v.get("vendorProject", "N/A")
            product = v.get("product", "N/A")
            desc = v.get("vulnerabilityName", "N/A")
            date_added = v.get("dateAdded", "N/A")
            due_date = v.get("dueDate", "N/A")
            ransomware = v.get("knownRansomwareCampaignUse", "Unknown")
            
            result.append(
                f"\n**{cve}** - {desc}\n"
                f"- Vendor: {vendor}\n"
                f"- Product: {product}\n"
                f"- Date Added: {date_added}\n"
                f"- Remediation Due: {due_date}\n"
                f"- Ransomware Campaign: {ransomware}"
            )
        
        return "\n".join(result)
        
    except Exception as e:
        return f"Error fetching KEV data: {str(e)}"


@mcp.tool()
async def get_cisa_alerts(limit: int = 10, keyword: str = None) -> str:
    """Get CISA security alerts and advisories.

    Args:
        limit: Maximum number of alerts to return (default: 10)
        keyword: Filter alerts by keyword in title or description

    Returns:
        List of recent CISA security alerts
    """
    try:
        import xml.etree.ElementTree as ET
        import httpx
        
        from mcp_govt_api.utils.http import http_client
        
        response = await http_client.get(CISA_ALERTS_URL)
        response.raise_for_status()
        
        root = ET.fromstring(response.text)
        
        # Handle RSS/Atom namespace
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'content': 'http://purl.org/rss/1.0/modules/content/'
        }
        
        alerts = []
        
        # Try Atom format first
        entries = root.findall('.//atom:entry', ns)
        if entries:
            for entry in entries[:limit]:
                title = entry.findtext('atom:title', '', ns)
                link = entry.findtext('atom:link[@href]/@href', '', ns)
                if not link:
                    link_elem = entry.find('atom:link', ns)
                    if link_elem is not None:
                        link = link_elem.get('href', '')
                published = entry.findtext('atom:published', '', ns)
                summary = entry.findtext('atom:summary', '', ns)
                
                alerts.append({
                    'title': title,
                    'link': link,
                    'date': published[:10] if published else 'N/A',
                    'summary': summary[:200] + '...' if len(summary) > 200 else summary
                })
        else:
            # Try RSS format
            items = root.findall('.//item') or root.findall('.//channel/item')
            for item in items[:limit]:
                title = item.findtext('title', '')
                link = item.findtext('link', '')
                pub_date = item.findtext('pubDate', '')
                desc = item.findtext('description', '')
                
                alerts.append({
                    'title': title,
                    'link': link,
                    'date': pub_date,
                    'summary': desc[:200] + '...' if len(desc) > 200 else desc
                })
        
        # Filter by keyword if provided
        if keyword:
            keyword_lower = keyword.lower()
            alerts = [
                a for a in alerts 
                if keyword_lower in a['title'].lower() or keyword_lower in a['summary'].lower()
            ]
        
        if not alerts:
            return "No CISA alerts found."
        
        result = [f"**CISA Security Alerts** ({len(alerts)} shown)\n"]
        
        for alert in alerts[:limit]:
            result.append(
                f"\n**{alert['title']}**\n"
                f"- Date: {alert['date']}\n"
                f"- Link: {alert['link']}\n"
                f"- Summary: {alert['summary']}"
            )
        
        return "\n".join(result)
        
    except Exception as e:
        return f"Error fetching CISA alerts: {str(e)}"


@mcp.tool()
async def get_security_advisories(vendor: str = None, product: str = None, limit: int = 20) -> str:
    """Get CISA security advisories filtered by vendor or product.

    Args:
        vendor: Filter by vendor name (e.g., 'Microsoft', 'Adobe')
        product: Filter by product name
        limit: Maximum number of advisories to return (default: 20)

    Returns:
        Filtered list of security advisories from CISA KEV catalog
    """
    try:
        data = await fetch_json(CISA_KEV_URL)
        vulnerabilities = data.get("vulnerabilities", [])
        
        # Apply filters
        filtered = vulnerabilities
        
        if vendor:
            vendor_lower = vendor.lower()
            filtered = [
                v for v in filtered 
                if vendor_lower in v.get("vendorProject", "").lower()
            ]
        
        if product:
            product_lower = product.lower()
            filtered = [
                v for v in filtered 
                if product_lower in v.get("product", "").lower()
            ]
        
        # Limit results
        filtered = filtered[:limit]
        
        if not filtered:
            filters = []
            if vendor:
                filters.append(f"vendor='{vendor}'")
            if product:
                filters.append(f"product='{product}'")
            filter_str = " and ".join(filters) if filters else "specified criteria"
            return f"No advisories found for {filter_str}."
        
        result = [f"**CISA Security Advisories** ({len(filtered)} found)\n"]
        
        if vendor:
            result.append(f"Vendor filter: {vendor}\n")
        if product:
            result.append(f"Product filter: {product}\n")
        
        for v in filtered:
            cve = v.get("cveID", "N/A")
            vendor_name = v.get("vendorProject", "N/A")
            product_name = v.get("product", "N/A")
            desc = v.get("vulnerabilityName", "N/A")
            date_added = v.get("dateAdded", "N/A")
            due_date = v.get("dueDate", "N/A")
            required_action = v.get("requiredAction", "N/A")
            ransomware = v.get("knownRansomwareCampaignUse", "Unknown")
            
            result.append(
                f"\n**{cve}** - {desc}\n"
                f"- Vendor: {vendor_name}\n"
                f"- Product: {product_name}\n"
                f"- Date Added: {date_added}\n"
                f"- Remediation Due: {due_date}\n"
                f"- Required Action: {required_action}\n"
                f"- Ransomware Campaign: {ransomware}"
            )
        
        return "\n".join(result)
        
    except Exception as e:
        return f"Error fetching security advisories: {str(e)}"


@mcp.tool()
async def search_kev_by_ransomware(limit: int = 20) -> str:
    """Get CISA KEV vulnerabilities known to be used in ransomware campaigns.

    Args:
        limit: Maximum number of vulnerabilities to return (default: 20)

    Returns:
        List of vulnerabilities actively used in ransomware attacks
    """
    try:
        data = await fetch_json(CISA_KEV_URL)
        vulnerabilities = data.get("vulnerabilities", [])
        
        # Filter for ransomware campaigns
        ransomware_vulns = [
            v for v in vulnerabilities 
            if v.get("knownRansomwareCampaignUse", "").lower() == "known"
        ]
        
        # Limit results
        ransomware_vulns = ransomware_vulns[:limit]
        
        if not ransomware_vulns:
            return "No ransomware-related vulnerabilities found in KEV catalog."
        
        result = [
            f"**CISA KEV - Ransomware-Exploited Vulnerabilities** "
            f"({len(ransomware_vulns)} shown)\n",
            "⚠️ These vulnerabilities are known to be used in ransomware campaigns.\n"
        ]
        
        for v in ransomware_vulns:
            cve = v.get("cveID", "N/A")
            vendor = v.get("vendorProject", "N/A")
            product = v.get("product", "N/A")
            desc = v.get("vulnerabilityName", "N/A")
            date_added = v.get("dateAdded", "N/A")
            due_date = v.get("dueDate", "N/A")
            
            result.append(
                f"\n**{cve}** - {desc}\n"
                f"- Vendor: {vendor}\n"
                f"- Product: {product}\n"
                f"- Date Added: {date_added}\n"
                f"- Remediation Due: {due_date}"
            )
        
        return "\n".join(result)
        
    except Exception as e:
        return f"Error fetching ransomware vulnerability data: {str(e)}"


@mcp.tool()
async def get_critical_kev(days: int = 30, limit: int = 20) -> str:
    """Get recently added critical CISA KEV vulnerabilities.

    Args:
        days: Number of days to look back (default: 30)
        limit: Maximum number of vulnerabilities to return (default: 20)

    Returns:
        List of recently added critical vulnerabilities
    """
    try:
        from datetime import datetime, timedelta
        
        data = await fetch_json(CISA_KEV_URL)
        vulnerabilities = data.get("vulnerabilities", [])
        
        # Calculate cutoff date
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_vulns = []
        for v in vulnerabilities:
            date_str = v.get("dateAdded", "")
            if date_str:
                try:
                    v_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if v_date >= cutoff:
                        recent_vulns.append(v)
                except ValueError:
                    continue
        
        # Sort by date added (newest first)
        recent_vulns.sort(key=lambda x: x.get("dateAdded", ""), reverse=True)
        
        # Limit results
        recent_vulns = recent_vulns[:limit]
        
        if not recent_vulns:
            return f"No vulnerabilities added in the last {days} days."
        
        result = [
            f"**Recently Added CISA KEV Vulnerabilities** (last {days} days)\n",
            f"Showing {len(recent_vulns)} of {len(recent_vulns)} recent additions:\n"
        ]
        
        for v in recent_vulns:
            cve = v.get("cveID", "N/A")
            vendor = v.get("vendorProject", "N/A")
            product = v.get("product", "N/A")
            desc = v.get("vulnerabilityName", "N/A")
            date_added = v.get("dateAdded", "N/A")
            due_date = v.get("dueDate", "N/A")
            ransomware = v.get("knownRansomwareCampaignUse", "Unknown")
            
            ransomware_flag = " 🚨 RANSOMWARE" if ransomware == "Known" else ""
            
            result.append(
                f"\n**{cve}**{ransomware_flag}\n"
                f"- Description: {desc}\n"
                f"- Vendor: {vendor}\n"
                f"- Product: {product}\n"
                f"- Date Added: {date_added}\n"
                f"- Remediation Due: {due_date}"
            )
        
        return "\n".join(result)
        
    except Exception as e:
        return f"Error fetching critical KEV data: {str(e)}"
