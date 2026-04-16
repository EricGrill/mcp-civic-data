from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

STATUS_PAGES = {
    "github": "https://www.githubstatus.com",
    "cloudflare": "https://www.cloudflarestatus.com",
    "slack": "https://status.slack.com",
    "discord": "https://discordstatus.com",
    "reddit": "https://www.redditstatus.com",
    "dropbox": "https://status.dropbox.com",
    "notion": "https://status.notion.so",
    "vercel": "https://www.vercel-status.com",
    "netlify": "https://www.netlifystatus.com",
    "heroku": "https://status.heroku.com",
    "digitalocean": "https://status.digitalocean.com",
    "datadog": "https://status.datadoghq.com",
    "pagerduty": "https://status.pagerduty.com",
    "stripe": "https://status.stripe.com",
    "twilio": "https://status.twilio.com",
    "sendgrid": "https://status.sendgrid.com",
    "npm": "https://status.npmjs.org",
    "figma": "https://status.figma.com",
    "twitch": "https://status.twitch.tv",
}


def _resolve_service(service: str) -> tuple[str, str]:
    """Return (service_key, base_url) or raise ValueError."""
    key = service.strip().lower()
    if key not in STATUS_PAGES:
        raise ValueError(
            f"Unknown service '{service}'. "
            f"Supported services: {', '.join(sorted(STATUS_PAGES))}"
        )
    return key, STATUS_PAGES[key]


def _indicator_emoji(indicator: str) -> str:
    mapping = {
        "none": "green",
        "minor": "yellow",
        "major": "orange",
        "critical": "red",
    }
    return mapping.get(indicator, indicator)


@mcp.tool()
async def check_service_status(service: str) -> str:
    """Check the current operational status of a major internet service.

    Queries the service's public Atlassian Statuspage API to retrieve
    real-time component health and overall status.

    Args:
        service: Name of the service to check (e.g., 'github', 'cloudflare',
            'slack', 'discord', 'stripe', 'npm'). Use list_monitored_services()
            to see all supported services.

    Returns:
        Overall status indicator and per-component breakdown showing
        which parts of the service are operational, degraded, or down.
    """
    try:
        key, base_url = _resolve_service(service)
    except ValueError as e:
        return str(e)

    url = f"{base_url}/api/v2/summary.json"

    try:
        data = await fetch_json(url)
    except Exception as e:
        return f"Error fetching status for {key}: {e}"

    status = data.get("status", {})
    indicator = status.get("indicator", "unknown")
    description = status.get("description", "No description available")

    page = data.get("page", {})
    page_name = page.get("name", key.capitalize())

    components = data.get("components", [])

    lines = [
        f"## {page_name} - Service Status\n",
        f"**Overall:** {description} ({_indicator_emoji(indicator)})\n",
    ]

    if components:
        lines.append("### Components\n")
        for comp in components:
            name = comp.get("name", "Unknown")
            comp_status = comp.get("status", "unknown")
            # Skip group headers (components that are just grouping labels)
            if comp.get("group", False) and not comp.get("components"):
                continue
            status_display = comp_status.replace("_", " ").title()
            lines.append(f"- **{name}**: {status_display}")

    return "\n".join(lines)


@mcp.tool()
async def get_service_incidents(service: str, limit: int = 5) -> str:
    """Get recent incidents and outages for a major internet service.

    Retrieves the latest incident reports from the service's public
    status page, including incident timeline and current resolution state.

    Args:
        service: Name of the service (e.g., 'github', 'cloudflare', 'slack').
            Use list_monitored_services() to see all supported services.
        limit: Maximum number of incidents to return (default: 5, max: 25).

    Returns:
        List of recent incidents with their status, impact level,
        creation date, and most recent status update message.
    """
    try:
        key, base_url = _resolve_service(service)
    except ValueError as e:
        return str(e)

    limit = max(1, min(limit, 25))

    url = f"{base_url}/api/v2/incidents.json"

    try:
        data = await fetch_json(url)
    except Exception as e:
        return f"Error fetching incidents for {key}: {e}"

    incidents = data.get("incidents", [])

    if not incidents:
        return f"No recent incidents found for {key}."

    incidents = incidents[:limit]

    lines = [f"## Recent Incidents for {key.capitalize()} ({len(incidents)} shown)\n"]

    for inc in incidents:
        name = inc.get("name", "Unknown Incident")
        status = inc.get("status", "unknown")
        impact = inc.get("impact", "unknown")
        created = inc.get("created_at", "Unknown")
        if created and len(created) >= 10:
            created = created[:10]

        resolved = inc.get("resolved_at")
        if resolved and len(resolved) >= 10:
            resolved = resolved[:10]

        lines.append(f"### {name}")
        lines.append(f"- **Status:** {status.replace('_', ' ').title()}")
        lines.append(f"- **Impact:** {impact.replace('_', ' ').title()}")
        lines.append(f"- **Created:** {created}")
        if resolved:
            lines.append(f"- **Resolved:** {resolved}")

        updates = inc.get("incident_updates", [])
        if updates:
            latest = updates[0]
            body = latest.get("body", "").strip()
            if body:
                # Truncate long update bodies
                if len(body) > 300:
                    body = body[:297] + "..."
                lines.append(f"- **Latest Update:** {body}")

        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def list_monitored_services() -> str:
    """List all internet services available for status monitoring.

    Returns the full catalog of services whose public status pages
    can be queried for real-time operational health and incident history.

    Returns:
        Table of supported service names and their status page URLs,
        for use with check_service_status() and get_service_incidents().
    """
    lines = [
        "## Monitored Services\n",
        "The following services can be checked with `check_service_status()` "
        "and `get_service_incidents()`:\n",
        "| Service | Status Page URL |",
        "|---------|----------------|",
    ]

    for key in sorted(STATUS_PAGES):
        lines.append(f"| {key} | {STATUS_PAGES[key]} |")

    lines.append(f"\n**Total:** {len(STATUS_PAGES)} services monitored")

    return "\n".join(lines)
