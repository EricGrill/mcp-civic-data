import csv
import io

import httpx

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.config import config


FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api"

# Degrees per km (approximate at the equator; good enough for bounding boxes)
_KM_PER_DEGREE = 111.0


def _get_map_key() -> str:
    """Return the FIRMS map key, falling back to the public DEMO_KEY."""
    return config.nasa_api_key or "DEMO_KEY"


def _bounding_box(
    latitude: float, longitude: float, radius_km: int
) -> tuple[float, float, float, float]:
    """Compute a (west, south, east, north) bounding box from a centre and radius.

    Args:
        latitude: Centre latitude in decimal degrees.
        longitude: Centre longitude in decimal degrees.
        radius_km: Half-width of the box in kilometres.

    Returns:
        Tuple of (west, south, east, north) clamped to valid WGS-84 ranges.
    """
    delta = radius_km / _KM_PER_DEGREE
    west = max(-180.0, longitude - delta)
    east = min(180.0, longitude + delta)
    south = max(-90.0, latitude - delta)
    north = min(90.0, latitude + delta)
    return west, south, east, north


async def _fetch_firms_csv(url: str) -> list[dict[str, str]]:
    """Fetch and parse a CSV response from the FIRMS API.

    Args:
        url: Fully constructed FIRMS CSV endpoint URL.

    Returns:
        List of row dicts keyed by the CSV header names.

    Raises:
        Exception: On network errors or non-2xx HTTP status codes.
    """
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(config.timeout),
        follow_redirects=True,
        headers={"User-Agent": "mcp-civic-data/0.1.0"},
    ) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.TimeoutException:
            raise Exception(f"Request timed out after {config.timeout}s: {url}")
        except httpx.HTTPStatusError as exc:
            raise Exception(
                f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
            )
        except httpx.RequestError as exc:
            raise Exception(f"Request failed: {exc}")

    reader = csv.DictReader(io.StringIO(response.text))
    return list(reader)


def _format_hotspot(row: dict[str, str], index: int) -> str:
    """Format a single FIRMS CSV row into a readable string.

    Args:
        row: A dict of field names to string values from the CSV.
        index: 1-based display index.

    Returns:
        Human-readable multi-line string for this hotspot.
    """
    lat = row.get("latitude", "N/A")
    lon = row.get("longitude", "N/A")
    brightness = row.get("bright_ti4") or row.get("brightness", "N/A")
    confidence = row.get("confidence", "N/A")
    acq_date = row.get("acq_date", "N/A")
    acq_time = row.get("acq_time", "N/A")
    frp = row.get("frp", "N/A")
    satellite = row.get("satellite", "N/A")

    # Format acquisition time as HH:MM when it is a plain 4-digit string
    if acq_time != "N/A" and len(acq_time) == 4 and acq_time.isdigit():
        acq_time = f"{acq_time[:2]}:{acq_time[2:]} UTC"

    lines = [
        f"**Hotspot {index}**",
        f"Location: {lat}, {lon}",
        f"Detected: {acq_date} at {acq_time}",
        f"Brightness (Ti4): {brightness} K",
        f"Fire Radiative Power: {frp} MW",
        f"Confidence: {confidence}",
        f"Satellite: {satellite}",
    ]
    return "\n".join(lines)


@mcp.tool()
async def get_active_fires(
    latitude: float,
    longitude: float,
    range_km: int = 100,
) -> str:
    """Get active fires and hotspots near a location detected by NASA satellites.

    Uses VIIRS S-NPP Near Real-Time data from the NASA FIRMS system.
    Results cover the past 24 hours. Requires a NASA API key for full access;
    falls back to the public DEMO_KEY for limited queries.

    Args:
        latitude: Centre latitude of the search area (e.g., 34.05 for Los Angeles).
        longitude: Centre longitude of the search area (e.g., -118.24 for Los Angeles).
        range_km: Approximate search radius in kilometres (default: 100).

    Returns:
        Up to 15 active fire/hotspot detections near the location, showing
        coordinates, detection time, brightness, fire radiative power, and
        confidence level. Returns a message if no fires are detected.
    """
    west, south, east, north = _bounding_box(latitude, longitude, range_km)
    area = f"{west:.4f},{south:.4f},{east:.4f},{north:.4f}"
    map_key = _get_map_key()

    url = f"{FIRMS_BASE}/area/csv/{map_key}/VIIRS_SNPP_NRT/{area}/1"
    rows = await _fetch_firms_csv(url)

    if not rows:
        return (
            f"No active fires detected within {range_km} km of "
            f"({latitude}, {longitude}) in the past 24 hours."
        )

    total = len(rows)
    displayed = rows[:15]

    header = (
        f"Active fires within ~{range_km} km of ({latitude}, {longitude}) "
        f"- {total} hotspot(s) detected in the past 24 hours"
        + (f" (showing 15 of {total})" if total > 15 else "")
        + ":\n"
    )

    sections = [header] + [
        _format_hotspot(row, i + 1) for i, row in enumerate(displayed)
    ]
    return "\n\n---\n\n".join(sections)


@mcp.tool()
async def get_country_fires(country_code: str, days: int = 1) -> str:
    """Get active fires for an entire country detected by NASA VIIRS satellites.

    Uses VIIRS S-NPP Near Real-Time data from the NASA FIRMS system.
    Requires a NASA API key for full access; falls back to the public DEMO_KEY
    for limited queries.

    Args:
        country_code: ISO 3166-1 alpha-3 country code (e.g., 'USA', 'AUS', 'BRA').
            Three-letter codes are required by the FIRMS API.
        days: Number of past days to retrieve (1-10, default: 1).

    Returns:
        Up to 20 active fire/hotspot detections for the country, showing
        coordinates, detection time, brightness, fire radiative power, and
        confidence level. Returns a message if no fires are detected.
    """
    days = max(1, min(10, days))
    country_code = country_code.upper().strip()
    map_key = _get_map_key()

    url = (
        f"{FIRMS_BASE}/country/csv/{map_key}/VIIRS_SNPP_NRT"
        f"/{country_code}/{days}"
    )
    rows = await _fetch_firms_csv(url)

    if not rows:
        return (
            f"No active fires detected in {country_code} over the past "
            f"{'day' if days == 1 else f'{days} days'}."
        )

    total = len(rows)
    displayed = rows[:20]
    day_label = "day" if days == 1 else f"{days} days"

    header = (
        f"Active fires in {country_code} over the past {day_label} "
        f"- {total} hotspot(s) detected"
        + (f" (showing 20 of {total})" if total > 20 else "")
        + ":\n"
    )

    sections = [header] + [
        _format_hotspot(row, i + 1) for i, row in enumerate(displayed)
    ]
    return "\n\n---\n\n".join(sections)


@mcp.tool()
async def query_firms(
    source: str = "VIIRS_SNPP_NRT",
    area: str = "",
    country: str = "",
    days: int = 1,
) -> list[dict[str, str]]:
    """Make a flexible raw query to the NASA FIRMS fire data API.

    Returns parsed CSV rows as a list of dicts for programmatic use.
    Exactly one of ``area`` or ``country`` must be provided.

    Supported sources:
        - ``VIIRS_SNPP_NRT`` - VIIRS on Suomi-NPP (near real-time, ~375 m)
        - ``VIIRS_NOAA20_NRT`` - VIIRS on NOAA-20 (near real-time, ~375 m)
        - ``MODIS_NRT`` - MODIS Terra/Aqua (near real-time, ~1 km)

    Args:
        source: FIRMS data source identifier (default: 'VIIRS_SNPP_NRT').
        area: Bounding box as 'west,south,east,north' in decimal degrees
            (e.g., '-125,24,-66,49' for the contiguous US). Required when
            ``country`` is not provided.
        country: ISO 3166-1 alpha-3 country code (e.g., 'USA'). Required
            when ``area`` is not provided.
        days: Number of past days to retrieve (1-10, default: 1).

    Returns:
        List of dicts where each dict represents one fire/hotspot row from
        the FIRMS CSV response. Keys include 'latitude', 'longitude',
        'bright_ti4', 'confidence', 'acq_date', 'acq_time', 'frp',
        'satellite', and others depending on the source.

    Raises:
        Exception: If neither ``area`` nor ``country`` is supplied, or if
            the FIRMS API request fails.
    """
    if not area and not country:
        raise Exception("Provide either 'area' (bounding box) or 'country' (ISO alpha-3 code).")

    days = max(1, min(10, days))
    map_key = _get_map_key()
    source = source.upper().strip()

    if country:
        url = (
            f"{FIRMS_BASE}/country/csv/{map_key}/{source}"
            f"/{country.upper().strip()}/{days}"
        )
    else:
        url = f"{FIRMS_BASE}/area/csv/{map_key}/{source}/{area.strip()}/{days}"

    return await _fetch_firms_csv(url)
