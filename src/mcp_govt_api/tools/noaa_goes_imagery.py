import re

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_text

GOES_CDN_BASE = "https://cdn.star.nesdis.noaa.gov"

SUPPORTED_SATELLITES: set[str] = {"GOES16", "GOES17", "GOES18", "GOES19"}


def _build_geocolor_directory_url(*, satellite: str) -> str:
    return f"{GOES_CDN_BASE}/{satellite}/ABI/FD/GEOCOLOR/"


def _format_timestamp_from_yyyymmddhhmm(ts: str) -> str:
    # Directory entries commonly look like: 20260681810_<...> (12 digits, sometimes varies).
    # We keep this best-effort and fall back to the raw prefix.
    if len(ts) < 12:
        return ts
    year = ts[0:4]
    month = ts[4:6]
    day = ts[6:8]
    hour = ts[8:10]
    minute = ts[10:12]
    return f"{year}-{month}-{day} {hour}:{minute} (approx)"


def _extract_latest_file_from_directory(*, directory_listing_text: str, resolution: str) -> str:
    """
    Extract the newest filename for a given resolution from an Apache directory listing.

    Example filename:
      20260681750_GOES19-ABI-FD-GEOCOLOR-21696x21696.jpg
    """
    safe_resolution = re.escape(resolution)
    pattern = re.compile(
        rf"(?P<ts>\d{{11,12}})_GOES\d+-ABI-FD-GEOCOLOR-{safe_resolution}\.jpg"
    )

    matches: list[tuple[str, str]] = []
    for m in pattern.finditer(directory_listing_text):
        ts = m.group("ts")
        filename = m.group(0)
        matches.append((ts, filename))

    if not matches:
        raise ValueError(f"No matching images found for resolution={resolution}")

    # ts strings are lexicographically sortable for this format.
    matches.sort(key=lambda x: x[0])
    return matches[-1][1]


@mcp.tool()
async def get_goes_geocolor_full_disk_latest(
    satellite: str = "GOES19",
    resolution: str = "21696x21696",
) -> str:
    """
    Get the latest GOES Earth Real-Time GeoColor full-disk image URL.

    Notes:
    - This implementation scrapes the directory listing from NOAA's STAR CDN.
    - Resolutions are those present in the directory (e.g., 21696x21696, 5424x5424, ...).
    """
    satellite = satellite.upper().strip()
    if satellite not in SUPPORTED_SATELLITES:
        return f"Error: Unsupported satellite={satellite}. Supported: {sorted(SUPPORTED_SATELLITES)}"

    directory_url = _build_geocolor_directory_url(satellite=satellite)
    try:
        listing_text = await fetch_text(directory_url)
    except Exception as e:
        return f"Error fetching GOES directory listing: {e}"

    try:
        latest_filename = _extract_latest_file_from_directory(
            directory_listing_text=listing_text,
            resolution=resolution,
        )
    except ValueError as e:
        return f"Error: {e}"

    ts_prefix = latest_filename.split("_", 1)[0]
    timestamp = _format_timestamp_from_yyyymmddhhmm(ts_prefix)
    image_url = f"{directory_url}{latest_filename}"
    return (
        f"Latest NOAA GOES full-disk GeoColor image\n"
        f"Satellite: {satellite}\n"
        f"Resolution: {resolution}\n"
        f"Timestamp: {timestamp}\n"
        f"URL: {image_url}"
    )

