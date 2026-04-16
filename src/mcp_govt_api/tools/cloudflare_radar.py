"""Cloudflare Radar tools for internet traffic, top domains, and attack data."""

from typing import Any

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

BASE = "https://api.cloudflare.com/client/v4/radar"

AUTH_FALLBACK_MSG = (
    "The Cloudflare Radar API returned an error. This endpoint may require "
    "an API token for access. You can explore Cloudflare Radar data "
    "interactively at https://radar.cloudflare.com"
)


@mcp.tool()
async def get_internet_traffic_summary(
    location: str = "", date_range: str = "1d"
) -> str:
    """Get internet traffic summary from Cloudflare Radar.

    Fetches HTTP traffic breakdown by IP version (IPv4 vs IPv6) for a given
    time range and optional country location.

    Args:
        location: Two-letter country code (e.g. 'US', 'GB', 'DE'). Empty
            string for global data.
        date_range: Time range for the summary. Valid values include '1d',
            '7d', '14d', '28d'.

    Returns:
        Formatted summary of internet traffic distribution by IP version,
        or a message explaining how to access the data if the API requires
        authentication.
    """
    url = f"{BASE}/http/summary/ip_version?dateRange={date_range}"
    if location:
        url += f"&location={location.upper()}"

    try:
        data: Any = await fetch_json(url)
    except Exception:
        return AUTH_FALLBACK_MSG

    if not isinstance(data, dict):
        return AUTH_FALLBACK_MSG

    result = data.get("result", {})
    summary = result.get("summary_0", {}) if isinstance(result, dict) else {}

    if not summary:
        return AUTH_FALLBACK_MSG

    location_label = location.upper() if location else "Global"

    lines: list[str] = [
        f"**Cloudflare Radar - Internet Traffic Summary ({location_label}, {date_range})**\n"
    ]

    lines.append("Traffic by IP Version:")
    ipv4 = summary.get("IPv4", "N/A")
    ipv6 = summary.get("IPv6", "N/A")
    lines.append(f"  IPv4: {ipv4}%")
    lines.append(f"  IPv6: {ipv6}%")

    meta = result.get("meta", {})
    if isinstance(meta, dict):
        date_range_info = meta.get("dateRange", [])
        if date_range_info and isinstance(date_range_info, list):
            period = date_range_info[0] if isinstance(date_range_info[0], dict) else {}
            start = period.get("startTime", "")
            end = period.get("endTime", "")
            if start and end:
                lines.append(f"\nPeriod: {start} to {end}")

    lines.append(
        "\nSource: Cloudflare Radar (https://radar.cloudflare.com)"
    )

    return "\n".join(lines)


@mcp.tool()
async def get_top_domains(limit: int = 10, location: str = "") -> str:
    """Get top internet domains from Cloudflare Radar.

    Fetches the most popular domains ranked by Cloudflare's traffic data
    over the past 7 days.

    Args:
        limit: Number of domains to return (default 10, max 100).
        location: Two-letter country code (e.g. 'US', 'DE'). Empty string
            for global ranking.

    Returns:
        Ranked list of top domains, or a message explaining how to access
        the data if the API requires authentication.
    """
    limit = max(1, min(limit, 100))
    url = f"{BASE}/ranking/top?limit={limit}&name=top&dateRange=7d"
    if location:
        url += f"&location={location.upper()}"

    try:
        data: Any = await fetch_json(url)
    except Exception:
        return AUTH_FALLBACK_MSG

    if not isinstance(data, dict):
        return AUTH_FALLBACK_MSG

    result = data.get("result", {})
    top_list = result.get("top_0", []) if isinstance(result, dict) else []

    if not top_list:
        return AUTH_FALLBACK_MSG

    location_label = location.upper() if location else "Global"

    lines: list[str] = [
        f"**Cloudflare Radar - Top {len(top_list)} Domains ({location_label}, 7d)**\n"
    ]

    for i, entry in enumerate(top_list, start=1):
        domain = entry.get("domain", "unknown") if isinstance(entry, dict) else str(entry)
        rank_entry = f"{i}. {domain}"
        if isinstance(entry, dict):
            category = entry.get("category", "")
            if category:
                rank_entry += f" ({category})"
        lines.append(rank_entry)

    lines.append(
        "\nSource: Cloudflare Radar (https://radar.cloudflare.com)"
    )

    return "\n".join(lines)


@mcp.tool()
async def get_attack_summary(date_range: str = "1d") -> str:
    """Get DDoS and cyber attack summary from Cloudflare Radar.

    Fetches Layer 3 (network layer) DDoS attack statistics including
    breakdowns by protocol and attack vector.

    Args:
        date_range: Time range for the summary. Valid values include '1d',
            '7d', '14d', '28d'.

    Returns:
        Summary of DDoS attack activity by protocol, or a message
        explaining how to access the data if the API requires
        authentication.
    """
    url = f"{BASE}/attacks/layer3/summary?dateRange={date_range}"

    try:
        data: Any = await fetch_json(url)
    except Exception:
        return AUTH_FALLBACK_MSG

    if not isinstance(data, dict):
        return AUTH_FALLBACK_MSG

    result = data.get("result", {})
    summary = result.get("summary_0", {}) if isinstance(result, dict) else {}

    if not summary:
        return AUTH_FALLBACK_MSG

    lines: list[str] = [
        f"**Cloudflare Radar - DDoS Attack Summary ({date_range})**\n"
    ]

    lines.append("Attack Distribution by Protocol:")
    for protocol, percentage in sorted(summary.items()):
        lines.append(f"  {protocol}: {percentage}%")

    meta = result.get("meta", {})
    if isinstance(meta, dict):
        date_range_info = meta.get("dateRange", [])
        if date_range_info and isinstance(date_range_info, list):
            period = date_range_info[0] if isinstance(date_range_info[0], dict) else {}
            start = period.get("startTime", "")
            end = period.get("endTime", "")
            if start and end:
                lines.append(f"\nPeriod: {start} to {end}")

    lines.append(
        "\nSource: Cloudflare Radar (https://radar.cloudflare.com)"
    )

    return "\n".join(lines)
