import html
import re

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_text

RSOE_EVENT_LIST_URL = "https://rsoe-edis.org/eventList"


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def parse_rsoe_event_list_html(*, html_text: str, limit: int) -> list[dict[str, str]]:
    """
    Best-effort parser for RSOE-EDIS event list HTML.

    The page renders category sections with event titles (typically in <h5>)
    and a table row containing a datetime cell and a location cell.
    """
    if limit <= 0:
        return []
    limit = min(limit, 50)

    # Find all event-title blocks.
    title_matches = list(
        re.finditer(r"<h5[^>]*>\s*(?P<title>.*?)\s*</h5>", html_text, flags=re.I | re.S)
    )

    events: list[dict[str, str]] = []

    for tm in title_matches:
        title_html = tm.group("title")
        title = _strip_html(title_html)
        if not title:
            continue

        # Search forward from this title for the first (datetime, location) pair.
        fragment = html_text[tm.end() : tm.end() + 2500]
        dt_loc = re.search(
            r"<td[^>]*>\s*(?P<dt>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*</td>\s*<td[^>]*>\s*(?P<loc>[^<]+?)\s*</td>",
            fragment,
            flags=re.I | re.S,
        )
        if not dt_loc:
            continue

        dt = dt_loc.group("dt").strip()
        loc = _strip_html(dt_loc.group("loc"))

        events.append({"title": title, "datetime": dt, "location": loc})
        if len(events) >= limit:
            break

    # Events are already displayed in descending order on the page, but keep the returned list stable.
    return events


@mcp.tool()
async def get_recent_disaster_events(limit: int = 10) -> str:
    """
    Get recent global disaster and emergency events from RSOE-EDIS.

    This is implemented by scraping the public event list page.
    """
    try:
        html_text = await fetch_text(RSOE_EVENT_LIST_URL)
    except Exception as e:
        return f"Error fetching RSOE-EDIS event list: {e}"

    events = parse_rsoe_event_list_html(html_text=html_text, limit=limit)
    if not events:
        return "No events found in the RSOE-EDIS event list page (or parsing failed)."

    lines: list[str] = [f"Recent RSOE-EDIS disaster events (showing up to {limit}):\n"]
    for ev in events:
        title = ev["title"]
        dt = ev["datetime"]
        loc = ev["location"]
        lines.append(f"**{title}**\n- When: {dt}\n- Where: {loc}")
    return "\n\n---\n\n".join(lines)

