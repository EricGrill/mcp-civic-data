from typing import Any

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json


BASE = "https://services.swpc.noaa.gov"


def _kp_storm_level(kp: float) -> str:
    """Interpret a Kp index value as a human-readable geomagnetic activity level.

    Args:
        kp: Planetary K-index value (0-9).

    Returns:
        Description string including NOAA G-scale category where applicable.
    """
    if kp < 4:
        return "Quiet"
    if kp < 5:
        return "Unsettled"
    if kp < 6:
        return "Minor storm (G1)"
    if kp < 7:
        return "Moderate storm (G2)"
    if kp < 8:
        return "Strong storm (G3)"
    if kp < 9:
        return "Severe storm (G4)"
    return "Extreme storm (G5)"


@mcp.tool()
async def get_space_weather_summary() -> str:
    """Get current space weather conditions from NOAA SWPC.

    Fetches the latest solar wind plasma readings, planetary K-index, and
    current NOAA space weather scales (R/S/G) and combines them into a
    concise summary.

    Returns:
        Summary of current solar wind speed, density, Kp index with storm
        level interpretation, and active NOAA space weather scale ratings.
    """
    plasma_url = f"{BASE}/products/solar-wind/plasma-5-minute.json"
    kp_url = f"{BASE}/products/noaa-planetary-k-index.json"
    scales_url = f"{BASE}/products/noaa-scales.json"

    plasma_raw: Any = await fetch_json(plasma_url)
    kp_raw: Any = await fetch_json(kp_url)
    scales_data: Any = await fetch_json(scales_url)

    # Both plasma and kp arrays have a header row at index 0; use last data row.
    plasma_row = plasma_raw[-1] if len(plasma_raw) > 1 else None
    kp_row = kp_raw[-1] if len(kp_raw) > 1 else None

    lines: list[str] = ["**Current Space Weather Summary (NOAA SWPC)**\n"]

    # Solar wind plasma
    if plasma_row:
        time_tag = plasma_row[0] if len(plasma_row) > 0 else "N/A"
        density = plasma_row[1] if len(plasma_row) > 1 else "N/A"
        speed = plasma_row[2] if len(plasma_row) > 2 else "N/A"
        temperature = plasma_row[3] if len(plasma_row) > 3 else "N/A"
        lines.append(
            f"Solar Wind (as of {time_tag}):\n"
            f"  Speed:       {speed} km/s\n"
            f"  Density:     {density} p/cm³\n"
            f"  Temperature: {temperature} K"
        )
    else:
        lines.append("Solar wind plasma data unavailable.")

    # Kp index
    if kp_row:
        kp_time = kp_row[0] if len(kp_row) > 0 else "N/A"
        try:
            kp_value = float(kp_row[1])
            kp_label = _kp_storm_level(kp_value)
        except (TypeError, ValueError, IndexError):
            kp_value = kp_row[1] if len(kp_row) > 1 else "N/A"
            kp_label = "Unknown"
        lines.append(
            f"Geomagnetic Activity (as of {kp_time}):\n"
            f"  Kp Index: {kp_value} - {kp_label}"
        )
    else:
        lines.append("Kp index data unavailable.")

    # NOAA scales
    if isinstance(scales_data, dict):
        # scales_data keys are scale categories; the current period is typically "-1"
        # Structure: {"R": {"-1": {"Scale": "0", ...}, "1": {...}}, ...}
        scale_lines: list[str] = []
        for category in ("R", "S", "G"):
            category_data = scales_data.get(category, {})
            current = category_data.get("-1", {})
            scale_val = current.get("Scale", "0")
            text = current.get("Text", "")
            label_map = {
                "R": "Radio Blackouts",
                "S": "Solar Radiation Storms",
                "G": "Geomagnetic Storms",
            }
            label = label_map.get(category, category)
            entry = f"  {category} ({label}): {scale_val}"
            if text and scale_val != "0":
                entry += f" - {text}"
            scale_lines.append(entry)
        lines.append("NOAA Space Weather Scales:\n" + "\n".join(scale_lines))
    else:
        lines.append("NOAA scales data unavailable.")

    return "\n\n".join(lines)


@mcp.tool()
async def get_solar_flares() -> str:
    """Get recent solar flare activity from NOAA SWPC.

    Fetches the latest X-ray flare events recorded by the GOES primary
    satellite and returns up to 10 of the most recent entries.

    Returns:
        List of recent solar flares showing class, begin/peak/end times,
        and heliographic location where available.
    """
    url = f"{BASE}/json/goes/primary/xray-flares-latest.json"
    data: Any = await fetch_json(url)

    if not data:
        return "No recent solar flare data available."

    flares = data if isinstance(data, list) else data.get("flares", [])
    if not flares:
        return "No recent solar flares recorded."

    lines: list[str] = [f"**Recent Solar Flares** ({len(flares)} total):\n"]

    for flare in flares[:10]:
        flare_class = flare.get("class", "N/A")
        begin = flare.get("begin_time", "N/A")
        peak = flare.get("max_time", "N/A")
        end = flare.get("end_time", "N/A")
        location = flare.get("location", "N/A")
        region = flare.get("region", "")

        entry_lines = [f"**Class {flare_class}**"]
        entry_lines.append(f"  Begin: {begin}")
        if peak:
            entry_lines.append(f"  Peak:  {peak}")
        if end:
            entry_lines.append(f"  End:   {end}")
        entry_lines.append(f"  Location: {location}")
        if region:
            entry_lines.append(f"  Active Region: {region}")

        lines.append("\n".join(entry_lines))

    return "\n\n---\n\n".join(lines)


@mcp.tool()
async def get_space_weather_alerts() -> str:
    """Get active space weather alerts and warnings from NOAA SWPC.

    Fetches the current alert product stream and returns up to the 5 most
    recent entries, which may include watches, warnings, and summaries for
    geomagnetic storms, solar radiation storms, and radio blackouts.

    Returns:
        Up to 5 most recent space weather alerts with issue time and message body.
    """
    url = f"{BASE}/products/alerts.json"
    data: Any = await fetch_json(url)

    alerts = data if isinstance(data, list) else []
    if not alerts:
        return "No active space weather alerts."

    lines: list[str] = [f"**Space Weather Alerts** (showing up to 5 most recent):\n"]

    for alert in alerts[:5]:
        product_id = alert.get("product_id", "N/A")
        issue_time = alert.get("issue_datetime", "N/A")
        message = alert.get("message", "").strip()

        # Trim very long messages to keep output readable
        if len(message) > 800:
            message = message[:800] + "...[truncated]"

        lines.append(
            f"**{product_id}**\n"
            f"Issued: {issue_time}\n\n"
            f"{message}"
        )

    return "\n\n---\n\n".join(lines)


@mcp.tool()
async def query_space_weather(endpoint: str) -> Any:
    """Make a raw query to the NOAA Space Weather Prediction Center (SWPC) API.

    Provides direct access to any SWPC JSON product. No authentication is
    required. The base URL ``https://services.swpc.noaa.gov`` is prepended
    automatically.

    Example endpoints:
        /products/solar-wind/plasma-5-minute.json
        /products/solar-wind/mag-5-minute.json
        /products/noaa-planetary-k-index.json
        /json/goes/primary/xray-flares-latest.json
        /products/alerts.json
        /products/noaa-scales.json

    Args:
        endpoint: Path to the SWPC product (must start with '/').

    Returns:
        Raw JSON response from the SWPC API (may be a list or a dict
        depending on the endpoint).
    """
    url = f"{BASE}{endpoint}"
    return await fetch_json(url)
