"""Satellite tracking tools using the N2YO API.

N2YO provides real-time satellite tracking data including positions,
TLE (Two-Line Element) sets, visual passes, and overhead satellite queries.

API docs: https://www.n2yo.com/api/
Requires a free API key from https://www.n2yo.com/
"""

import os
from datetime import datetime, timezone
from typing import Any

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.config import config
from mcp_govt_api.utils.http import fetch_json

BASE = "https://api.n2yo.com/rest/v1/satellite"

# Well-known NORAD IDs for reference
COMMON_SATELLITES = {
    25544: "ISS (International Space Station)",
    20580: "Hubble Space Telescope",
    48274: "James Webb Space Telescope (JWST)",
    43013: "NOAA-20",
    25338: "NOAA-15",
    36516: "Suomi NPP",
}

# N2YO satellite category IDs
CATEGORIES = {
    0: "All",
    1: "Brightest",
    2: "ISS",
    3: "Weather",
    4: "NOAA",
    6: "GOES",
    7: "Earth Resources",
    8: "Search & Rescue",
    9: "Disaster Monitoring",
    10: "Tracking & Data Relay",
    11: "Geostationary",
    12: "Intelsat",
    14: "Gorizont",
    15: "Raduga",
    16: "Molniya",
    17: "Iridium",
    18: "Orbcomm",
    19: "Globalstar",
    20: "Amateur Radio",
    21: "Experimental",
    22: "GPS Operational",
    23: "Glonass Operational",
    24: "Galileo",
    25: "Satellite-Based Augmentation",
    26: "Navy Navigation",
    27: "Russian LEO Navigation",
    28: "Space & Earth Science",
    29: "Geodetic",
    30: "Engineering",
    31: "Education",
    32: "Military",
    33: "Radar Calibration",
    34: "CubeSats",
    35: "XM and Sirius",
    36: "TV",
    37: "Beidou",
    38: "Yaogan",
    39: "Westford Needles",
    40: "Parus",
    41: "Strela",
    42: "Gonets",
    43: "Cosmos 2251 Debris",
    44: "Iridium 33 Debris",
    45: "Weather (Active)",
    46: "Starlink",
    47: "OneWeb",
    48: "Science (Active)",
    49: "Miscellaneous Military",
    50: "Radar Calibration (Active)",
    51: "O3B Networks",
    52: "Tselina",
    53: "Cosmos 1408 Debris",
    54: "GNSS",
}


def get_api_key() -> str | None:
    """Return the N2YO API key from config or environment.

    Returns:
        API key string if available, or None if not configured.
    """
    return getattr(config, "n2yo_api_key", None) or os.environ.get("N2YO_API_KEY")


def _build_url(path: str) -> str:
    """Build a full N2YO API URL with API key parameter.

    Args:
        path: API path after the base URL (e.g., '/tle/25544').

    Returns:
        Full URL with apiKey query parameter.

    Raises:
        ValueError: If no API key is configured.
    """
    api_key = get_api_key()
    if not api_key:
        raise ValueError(
            "N2YO API key not configured. Set N2YO_API_KEY environment variable "
            "or add n2yo_api_key to config. Get a free key at https://www.n2yo.com/api/"
        )
    separator = "&" if "?" in path else "?"
    return f"{BASE}{path}{separator}apiKey={api_key}"


@mcp.tool()
async def get_satellite_position(
    norad_id: int,
    observer_lat: float = 0.0,
    observer_lng: float = 0.0,
    seconds: int = 1,
) -> str:
    """Get current position of a satellite by NORAD ID.

    Returns the satellite's latitude, longitude, altitude, and other
    orbital parameters for the specified time window.

    Common NORAD IDs:
        25544 = ISS, 20580 = Hubble, 48274 = JWST

    Args:
        norad_id: NORAD catalog ID of the satellite.
        observer_lat: Observer latitude in decimal degrees (default 0.0).
        observer_lng: Observer longitude in decimal degrees (default 0.0).
        seconds: Number of future seconds to predict positions for (1-300).

    Returns:
        Formatted satellite position data including coordinates and altitude.
    """
    try:
        seconds = max(1, min(seconds, 300))
        path = f"/positions/{norad_id}/{observer_lat}/{observer_lng}/0/{seconds}"
        url = _build_url(path)
        data: Any = await fetch_json(url)
    except ValueError as exc:
        return str(exc)
    except Exception as exc:
        return f"Error fetching satellite position: {exc}"

    if not data or not isinstance(data, dict):
        return f"No position data returned for NORAD ID {norad_id}."

    info = data.get("info", {})
    positions = data.get("positions", [])

    sat_name = info.get("satname", f"NORAD {norad_id}")
    known_name = COMMON_SATELLITES.get(norad_id, "")
    if known_name and known_name != sat_name:
        sat_name = f"{sat_name} ({known_name})"

    lines: list[str] = [f"**Satellite Position: {sat_name}**\n"]

    # Satellite info
    sat_id = info.get("satid", norad_id)
    trans_count = info.get("transactionscount", "N/A")
    lines.append(f"NORAD ID: {sat_id}")
    lines.append(f"API Transactions: {trans_count}\n")

    if not positions:
        lines.append("No position data available.")
        return "\n".join(lines)

    for i, pos in enumerate(positions):
        sat_lat = pos.get("satlatitude", "N/A")
        sat_lng = pos.get("satlongitude", "N/A")
        sat_alt = pos.get("sataltitude", "N/A")
        azimuth = pos.get("azimuth", "N/A")
        elevation = pos.get("elevation", "N/A")
        ra = pos.get("ra", "N/A")
        dec = pos.get("dec", "N/A")
        timestamp = pos.get("timestamp", 0)

        time_str = "N/A"
        if timestamp:
            try:
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except (OSError, ValueError):
                time_str = str(timestamp)

        if len(positions) > 1:
            lines.append(f"--- Position {i + 1} ---")

        lines.append(f"Time: {time_str}")
        lines.append(f"Latitude: {sat_lat}")
        lines.append(f"Longitude: {sat_lng}")
        lines.append(f"Altitude: {sat_alt} km")
        lines.append(f"Azimuth: {azimuth}")
        lines.append(f"Elevation: {elevation}")
        lines.append(f"Right Ascension: {ra}")
        lines.append(f"Declination: {dec}")

        if len(positions) > 1:
            lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def get_satellites_above(
    observer_lat: float,
    observer_lng: float,
    search_radius: int = 70,
    category: int = 0,
) -> str:
    """Find satellites currently above a given location.

    Returns a list of satellites within the specified search radius
    of the observer's position.

    Category IDs: 0=All, 1=Brightest, 2=ISS, 3=Weather, 18=Orbcomm,
    22=GPS, 34=CubeSats, 46=Starlink, 52=Tselina

    Args:
        observer_lat: Observer latitude in decimal degrees.
        observer_lng: Observer longitude in decimal degrees.
        search_radius: Search radius in degrees (0-90, default 70).
        category: Satellite category ID (default 0 for all).

    Returns:
        List of satellites overhead with names, positions, and launch dates.
    """
    try:
        search_radius = max(0, min(search_radius, 90))
        path = f"/above/{observer_lat}/{observer_lng}/0/{search_radius}/{category}"
        url = _build_url(path)
        data: Any = await fetch_json(url)
    except ValueError as exc:
        return str(exc)
    except Exception as exc:
        return f"Error fetching satellites above: {exc}"

    if not data or not isinstance(data, dict):
        return "No data returned for satellites above query."

    info = data.get("info", {})
    sats = data.get("above", [])
    category_name = info.get("category", CATEGORIES.get(category, "Unknown"))

    lines: list[str] = [
        f"**Satellites Above ({observer_lat}, {observer_lng})**\n"
        f"Category: {category_name}\n"
        f"Search Radius: {search_radius} degrees\n"
        f"Satellites Found: {len(sats)}\n"
    ]

    if not sats:
        lines.append("No satellites currently overhead for the given parameters.")
        return "\n".join(lines)

    for sat in sats[:25]:
        sat_name = sat.get("satname", "Unknown")
        sat_id = sat.get("satid", "N/A")
        sat_lat = sat.get("satlat", "N/A")
        sat_lng = sat.get("satlng", "N/A")
        sat_alt = sat.get("satalt", "N/A")
        launch_date = sat.get("launchDate", "N/A")
        intl_desig = sat.get("intDesignator", "N/A")

        entry = (
            f"**{sat_name}** (NORAD {sat_id})\n"
            f"  Position: {sat_lat}, {sat_lng} at {sat_alt} km\n"
            f"  Launch: {launch_date} | Designator: {intl_desig}"
        )
        lines.append(entry)

    if len(sats) > 25:
        lines.append(f"\n...and {len(sats) - 25} more satellites.")

    return "\n\n".join(lines)


@mcp.tool()
async def get_satellite_tle(norad_id: int) -> str:
    """Get Two-Line Element (TLE) set for a satellite.

    TLE data describes the satellite's orbit and is used for tracking
    and prediction. Updated regularly from public sources.

    Common NORAD IDs:
        25544 = ISS, 20580 = Hubble, 48274 = JWST

    Args:
        norad_id: NORAD catalog ID of the satellite.

    Returns:
        Satellite name and TLE lines with orbital parameters.
    """
    try:
        path = f"/tle/{norad_id}"
        url = _build_url(path)
        data: Any = await fetch_json(url)
    except ValueError as exc:
        return str(exc)
    except Exception as exc:
        return f"Error fetching TLE data: {exc}"

    if not data or not isinstance(data, dict):
        return f"No TLE data returned for NORAD ID {norad_id}."

    info = data.get("info", {})
    tle = data.get("tle", "")

    sat_name = info.get("satname", f"NORAD {norad_id}")
    sat_id = info.get("satid", norad_id)
    trans_count = info.get("transactionscount", "N/A")

    known_name = COMMON_SATELLITES.get(norad_id, "")
    if known_name and known_name != sat_name:
        sat_name = f"{sat_name} ({known_name})"

    lines: list[str] = [f"**TLE Data: {sat_name}**\n"]
    lines.append(f"NORAD ID: {sat_id}")
    lines.append(f"API Transactions: {trans_count}\n")

    if not tle:
        lines.append("No TLE data available for this satellite.")
        return "\n".join(lines)

    tle_lines = tle.strip().split("\r\n") if "\r\n" in tle else tle.strip().split("\n")

    if len(tle_lines) >= 2:
        lines.append(f"```\n{tle_lines[0]}\n{tle_lines[1]}\n```")
    else:
        lines.append(f"```\n{tle}\n```")

    return "\n".join(lines)
