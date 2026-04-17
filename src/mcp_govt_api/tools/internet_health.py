from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

IHR_BASE = "https://ihr.iijlab.net/ihr/api"


@mcp.tool()
async def get_network_disconnections(
    country: str = "",
    asn: int = 0,
    limit: int = 20,
) -> str:
    """Get recent network disconnection and outage events from the Internet Health Report.

    Monitors network disconnections detected by the IHR platform, which tracks
    BGP routing data to identify networks that become unreachable.

    Args:
        country: Filter by country code (e.g., 'US', 'DE', 'JP')
        asn: Filter by Autonomous System Number (e.g., 15169 for Google)
        limit: Maximum number of events to return (default: 20)

    Returns:
        Recent network disconnection events with severity, duration, and
        affected network details.
    """
    url = f"{IHR_BASE}/disco/events/?format=json&limit={limit}"

    if asn:
        url += f"&streamtype=asn&streamname={asn}"
    if country:
        url += f"&streamtype=country&streamname={country}"

    try:
        data = await fetch_json(url)
    except Exception as e:
        return f"Error fetching disconnection events: {e}"

    results = data.get("results", [])

    if not results:
        filters = []
        if country:
            filters.append(f"country={country}")
        if asn:
            filters.append(f"ASN {asn}")
        filter_text = f" for {', '.join(filters)}" if filters else ""
        return f"No disconnection events found{filter_text}."

    lines = ["## Network Disconnection Events\n"]

    for event in results:
        stream_name = event.get("streamname", "Unknown")
        stream_type = event.get("streamtype", "unknown")
        start = event.get("starttime", "N/A")
        end = event.get("endtime", "N/A")
        avglevel = event.get("avglevel", "N/A")
        nbdiscoprobes = event.get("nbdiscoprobes", "N/A")

        lines.append(
            f"**{stream_name}** ({stream_type})\n"
            f"- Start: {start}\n"
            f"- End: {end}\n"
            f"- Avg Level: {avglevel}\n"
            f"- Disconnected Probes: {nbdiscoprobes}"
        )

    return "\n\n---\n\n".join(lines)


@mcp.tool()
async def get_network_delays(
    startpoint: str = "",
    endpoint_name: str = "",
    limit: int = 20,
) -> str:
    """Get network delay measurements between networks from the Internet Health Report.

    Measures latency and delay changes between networks using RIPE Atlas
    traceroute data, useful for detecting congestion or routing changes.

    Args:
        startpoint: Starting network name or ASN (e.g., 'AS15169')
        endpoint_name: Destination network name or ASN (e.g., 'AS13335')
        limit: Maximum number of results to return (default: 20)

    Returns:
        Network delay measurements showing latency between network pairs.
    """
    url = f"{IHR_BASE}/network_delay/?format=json&limit={limit}"

    if startpoint:
        url += f"&startpoint_name={startpoint}"
    if endpoint_name:
        url += f"&endpoint_name={endpoint_name}"

    try:
        data = await fetch_json(url)
    except Exception as e:
        return f"Error fetching network delay data: {e}"

    results = data.get("results", [])

    if not results:
        filters = []
        if startpoint:
            filters.append(f"startpoint={startpoint}")
        if endpoint_name:
            filters.append(f"endpoint={endpoint_name}")
        filter_text = f" for {', '.join(filters)}" if filters else ""
        return f"No network delay data found{filter_text}."

    lines = ["## Network Delay Measurements\n"]

    for entry in results:
        start = entry.get("startpoint_name", "Unknown")
        end = entry.get("endpoint_name", "Unknown")
        median = entry.get("median", "N/A")
        timebin = entry.get("timebin", "N/A")
        nbtracks = entry.get("nbtracks", "N/A")
        nbprobes = entry.get("nbprobes", "N/A")

        lines.append(
            f"**{start}** -> **{end}**\n"
            f"- Median Delay: {median} ms\n"
            f"- Time: {timebin}\n"
            f"- Traceroutes: {nbtracks} | Probes: {nbprobes}"
        )

    return "\n\n---\n\n".join(lines)


@mcp.tool()
async def get_as_hegemony(asn: int, limit: int = 20) -> str:
    """Get AS hegemony scores showing network dependency for a given ASN.

    AS hegemony quantifies how much other networks depend on a specific
    Autonomous System for connectivity. High hegemony scores indicate that
    the ASN is a critical transit provider.

    Args:
        asn: The Autonomous System Number to analyze (e.g., 15169 for Google)
        limit: Maximum number of results to return (default: 20)

    Returns:
        AS hegemony scores showing which origin ASNs depend on the queried
        ASN, with dependency weight and measurement timestamps.
    """
    url = f"{IHR_BASE}/hegemony/?format=json&asn={asn}&limit={limit}"

    try:
        data = await fetch_json(url)
    except Exception as e:
        return f"Error fetching AS hegemony data: {e}"

    results = data.get("results", [])

    if not results:
        return f"No AS hegemony data found for ASN {asn}."

    lines = [f"## AS Hegemony for ASN {asn}\n"]

    for entry in results:
        origin_asn = entry.get("originasn", "N/A")
        hege = entry.get("hege", "N/A")
        timebin = entry.get("timebin", "N/A")
        origin_name = entry.get("originasn_name", "")

        origin_label = f"AS{origin_asn}"
        if origin_name:
            origin_label += f" ({origin_name})"

        lines.append(
            f"**Origin: {origin_label}**\n"
            f"- Hegemony Score: {hege}\n"
            f"- Time: {timebin}"
        )

    return "\n\n---\n\n".join(lines)
