"""NOAA satellite imagery tools.

Provides access to NOAA GOES satellite imagery metadata, latest timestamps,
and sector/coverage reference information via the NESDIS CDN and RAMMB-SLIDER
APIs.
"""

from typing import Any

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

NESDIS_CDN = "https://cdn.star.nesdis.noaa.gov"
RAMMB_SLIDER = "https://rammb-slider.cira.colostate.edu"

# Maps user-friendly satellite names to CDN path segments and slider IDs.
SATELLITE_MAP: dict[str, dict[str, str]] = {
    "GOES-East": {"cdn_path": "GOES16", "slider_id": "goes-16"},
    "GOES-West": {"cdn_path": "GOES18", "slider_id": "goes-18"},
}

# Maps user-friendly sector names to CDN path segments.
SECTOR_MAP: dict[str, str] = {
    "CONUS": "CONUS",
    "FullDisk": "FD",
    "Mesoscale-1": "meso1",
    "Mesoscale-2": "meso2",
}

# Maps user-friendly product names to CDN path segments.
PRODUCT_MAP: dict[str, str] = {
    "GeoColor": "GEOCOLOR",
    "Band13": "13",
    "Band02": "02",
}

# Sector descriptions for the reference tool.
SECTOR_INFO: dict[str, dict[str, str]] = {
    "CONUS": {
        "name": "Continental United States",
        "description": "Contiguous US coverage, updated every 5 minutes.",
        "coverage": "Approximately 24N-50N latitude, 125W-66W longitude",
    },
    "FullDisk": {
        "name": "Full Disk",
        "description": "Full hemisphere view of Earth, updated every 10 minutes.",
        "coverage": "Full Earth disk as seen from the satellite's geostationary position",
    },
    "Mesoscale-1": {
        "name": "Mesoscale Domain 1",
        "description": "Small, targeted sector for severe weather, updated every 60 seconds.",
        "coverage": "Approximately 1000x1000 km region, repositioned as needed by NWS",
    },
    "Mesoscale-2": {
        "name": "Mesoscale Domain 2",
        "description": "Second mesoscale sector for simultaneous severe weather monitoring.",
        "coverage": "Approximately 1000x1000 km region, repositioned as needed by NWS",
    },
}


def _validate_satellite(satellite: str) -> str | None:
    """Return an error message if the satellite name is invalid, else None."""
    if satellite not in SATELLITE_MAP:
        valid = ", ".join(sorted(SATELLITE_MAP.keys()))
        return f"Error: Unknown satellite '{satellite}'. Valid options: {valid}"
    return None


def _validate_sector(sector: str) -> str | None:
    """Return an error message if the sector name is invalid, else None."""
    if sector not in SECTOR_MAP:
        valid = ", ".join(sorted(SECTOR_MAP.keys()))
        return f"Error: Unknown sector '{sector}'. Valid options: {valid}"
    return None


def _validate_product(product: str) -> str | None:
    """Return an error message if the product name is invalid, else None."""
    if product not in PRODUCT_MAP:
        valid = ", ".join(sorted(PRODUCT_MAP.keys()))
        return f"Error: Unknown product '{product}'. Valid options: {valid}"
    return None


@mcp.tool()
async def get_satellite_imagery_info(
    satellite: str = "GOES-East",
    sector: str = "CONUS",
    product: str = "GeoColor",
) -> str:
    """Get info about available NOAA GOES satellite imagery with direct links.

    Returns metadata and direct CDN links for the specified satellite, sector,
    and product combination. No authentication required.

    Args:
        satellite: Satellite name. Options: GOES-East (GOES-16), GOES-West (GOES-18).
        sector: Imagery sector. Options: CONUS, FullDisk, Mesoscale-1, Mesoscale-2.
        product: Imagery product. Options: GeoColor, Band13 (IR), Band02 (Visible).

    Returns:
        Formatted summary with imagery details and direct links.
    """
    if err := _validate_satellite(satellite):
        return err
    if err := _validate_sector(sector):
        return err
    if err := _validate_product(product):
        return err

    sat_info = SATELLITE_MAP[satellite]
    cdn_path = sat_info["cdn_path"]
    slider_id = sat_info["slider_id"]
    sector_path = SECTOR_MAP[sector]
    product_path = PRODUCT_MAP[product]

    latest_url = f"{NESDIS_CDN}/{cdn_path}/ABI/SECTOR/{sector_path}/{product_path}/latest.jpg"
    browse_url = f"{NESDIS_CDN}/{cdn_path}/ABI/SECTOR/{sector_path}/{product_path}/"
    slider_url = f"{RAMMB_SLIDER}/?sat={slider_id}&sec={sector_path}&p=geocolor"

    sector_desc = SECTOR_INFO.get(sector, {})

    try:
        # Fetch latest timestamps to confirm data availability
        ts_url = (
            f"{RAMMB_SLIDER}/data/json/{slider_id}"
            f"/natural_color/{sector_path.lower()}/latest_times.json"
        )
        timestamps: Any = await fetch_json(ts_url)
        latest_time = None
        if isinstance(timestamps, dict):
            times_list = timestamps.get("timestamps_int", [])
            if times_list:
                latest_time = str(times_list[0])
        elif isinstance(timestamps, list) and timestamps:
            latest_time = str(timestamps[0])
    except Exception:
        latest_time = None

    lines: list[str] = [
        f"**NOAA {satellite} Satellite Imagery**\n",
        f"**Satellite:** {satellite} ({cdn_path})",
        f"**Sector:** {sector_desc.get('name', sector)}",
        f"**Coverage:** {sector_desc.get('description', 'N/A')}",
        f"**Product:** {product} ({product_path})",
    ]

    if latest_time:
        lines.append(f"**Latest Available:** {latest_time}")
    else:
        lines.append("**Latest Available:** Could not determine latest timestamp")

    lines.append("")
    lines.append("**Links:**")
    lines.append(f"- Latest Image: {latest_url}")
    lines.append(f"- Browse Directory: {browse_url}")
    lines.append(f"- Interactive Viewer: {slider_url}")

    return "\n".join(lines)


@mcp.tool()
async def get_latest_satellite_timestamps(
    satellite: str = "goes-16",
    sector: str = "conus",
) -> str:
    """Get timestamps of latest available NOAA GOES satellite images.

    Queries the RAMMB-SLIDER API for the most recent image timestamps
    for a given satellite and sector combination.

    Args:
        satellite: Satellite identifier (goes-16 or goes-18).
        sector: Sector identifier (conus, fd, meso1, meso2) in lowercase.

    Returns:
        Formatted list of the most recent available image timestamps.
    """
    valid_satellites = {"goes-16", "goes-18"}
    if satellite not in valid_satellites:
        return (
            f"Error: Unknown satellite '{satellite}'. "
            f"Valid options: {', '.join(sorted(valid_satellites))}"
        )

    valid_sectors = {"conus", "fd", "meso1", "meso2"}
    if sector not in valid_sectors:
        return (
            f"Error: Unknown sector '{sector}'. "
            f"Valid options: {', '.join(sorted(valid_sectors))}"
        )

    url = (
        f"{RAMMB_SLIDER}/data/json/{satellite}"
        f"/natural_color/{sector}/latest_times.json"
    )

    try:
        data: Any = await fetch_json(url)
    except Exception as exc:
        return f"Error fetching satellite timestamps: {exc}"

    if not data:
        return "No timestamp data available for this satellite/sector combination."

    # Response may be a dict with timestamps_int key or a plain list.
    timestamps: list[Any] = []
    if isinstance(data, dict):
        timestamps = data.get("timestamps_int", [])
    elif isinstance(data, list):
        timestamps = data

    if not timestamps:
        return "No timestamps found in the response data."

    # Show up to 10 most recent timestamps.
    display_count = min(len(timestamps), 10)

    lines: list[str] = [
        f"**Latest Satellite Timestamps** ({satellite.upper()} / {sector.upper()})\n",
        f"Showing {display_count} of {len(timestamps)} available times:\n",
    ]

    for ts in timestamps[:display_count]:
        ts_str = str(ts)
        # Timestamps are typically in YYYYMMDDHHMMSS format.
        if len(ts_str) == 14:
            formatted = (
                f"{ts_str[:4]}-{ts_str[4:6]}-{ts_str[6:8]} "
                f"{ts_str[8:10]}:{ts_str[10:12]}:{ts_str[12:14]} UTC"
            )
            lines.append(f"- {formatted}")
        else:
            lines.append(f"- {ts_str}")

    lines.append(f"\nTotal available images: {len(timestamps)}")

    return "\n".join(lines)


@mcp.tool()
async def get_satellite_sectors() -> str:
    """List available NOAA GOES satellite sectors and coverage areas.

    Returns a static reference of all supported satellites, sectors, and
    imagery products with descriptions.

    Returns:
        Formatted reference listing all available options.
    """
    lines: list[str] = ["**NOAA GOES Satellite Imagery - Available Options**\n"]

    # Satellites
    lines.append("## Satellites\n")
    for name, info in SATELLITE_MAP.items():
        lines.append(
            f"- **{name}** ({info['cdn_path']}) - Slider ID: {info['slider_id']}"
        )

    # Sectors
    lines.append("\n## Sectors\n")
    for key, info in SECTOR_INFO.items():
        lines.append(f"- **{key}** ({info['name']})")
        lines.append(f"  {info['description']}")
        lines.append(f"  Coverage: {info['coverage']}")

    # Products
    lines.append("\n## Products\n")
    product_descriptions = {
        "GeoColor": "True-color daytime / multispectral IR nighttime composite",
        "Band13": "Clean IR longwave window (10.3 um) - cloud top temperatures",
        "Band02": "Red visible band (0.64 um) - daytime cloud/surface detail",
    }
    for name, path in PRODUCT_MAP.items():
        desc = product_descriptions.get(name, "")
        lines.append(f"- **{name}** (Band/Path: {path}) - {desc}")

    # Usage tips
    lines.append("\n## Quick Links\n")
    lines.append(
        f"- GOES-East CONUS GeoColor: {NESDIS_CDN}/GOES16/ABI/SECTOR/CONUS/GEOCOLOR/latest.jpg"
    )
    lines.append(
        f"- GOES-West CONUS GeoColor: {NESDIS_CDN}/GOES18/ABI/SECTOR/CONUS/GEOCOLOR/latest.jpg"
    )
    lines.append(f"- Interactive Viewer: {RAMMB_SLIDER}/")

    return "\n".join(lines)
