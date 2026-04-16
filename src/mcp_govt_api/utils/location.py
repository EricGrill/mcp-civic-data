from dataclasses import dataclass

from mcp_govt_api.utils.http import fetch_json

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"


@dataclass
class ResolvedLocation:
    """Normalized location data for downstream tool usage."""

    latitude: float
    longitude: float
    display_name: str
    source: str
    query: str = ""


def _format_coordinates(latitude: float, longitude: float) -> str:
    """Return a stable coordinate label."""
    return f"{latitude:.4f}, {longitude:.4f}"


def _validate_coordinates(latitude: float, longitude: float) -> tuple[float, float]:
    """Validate and normalize decimal coordinates."""
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("Latitude must be between -90 and 90")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError("Longitude must be between -180 and 180")
    return latitude, longitude


def _parse_coordinate_string(value: str) -> tuple[float, float] | None:
    """Parse a simple 'lat, lon' string without hitting a geocoder."""
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 2:
        return None

    try:
        latitude = float(parts[0])
        longitude = float(parts[1])
    except ValueError:
        return None

    return _validate_coordinates(latitude, longitude)


async def reverse_geocode(latitude: float, longitude: float) -> str:
    """Return a human-friendly label for coordinates when possible."""
    latitude, longitude = _validate_coordinates(latitude, longitude)
    data = await fetch_json(
        f"{NOMINATIM_BASE}/reverse",
        params={
            "format": "jsonv2",
            "lat": str(latitude),
            "lon": str(longitude),
        },
    )
    return data.get("display_name") or _format_coordinates(latitude, longitude)


async def geocode_location(query: str) -> ResolvedLocation:
    """Resolve a human-readable location string to coordinates."""
    query = query.strip()
    if not query:
        raise ValueError("Provide a location string or both latitude and longitude")

    parsed = _parse_coordinate_string(query)
    if parsed is not None:
        latitude, longitude = parsed
        try:
            display_name = await reverse_geocode(latitude, longitude)
        except Exception:
            display_name = _format_coordinates(latitude, longitude)
        return ResolvedLocation(
            latitude=latitude,
            longitude=longitude,
            display_name=display_name,
            source="coordinates",
            query=query,
        )

    data = await fetch_json(
        f"{NOMINATIM_BASE}/search",
        params={
            "q": query,
            "format": "jsonv2",
            "limit": "1",
            "addressdetails": "1",
        },
    )
    if not data:
        raise ValueError(f"Could not resolve location: {query}")

    match = data[0]
    latitude = float(match["lat"])
    longitude = float(match["lon"])
    _validate_coordinates(latitude, longitude)
    return ResolvedLocation(
        latitude=latitude,
        longitude=longitude,
        display_name=match.get("display_name") or query,
        source="nominatim",
        query=query,
    )


async def resolve_location(
    *,
    location: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
) -> ResolvedLocation:
    """Resolve either a free-form location or explicit coordinates."""
    if latitude is not None or longitude is not None:
        if latitude is None or longitude is None:
            raise ValueError("Provide both latitude and longitude together")

        latitude, longitude = _validate_coordinates(latitude, longitude)
        try:
            display_name = await reverse_geocode(latitude, longitude)
        except Exception:
            display_name = _format_coordinates(latitude, longitude)
        return ResolvedLocation(
            latitude=latitude,
            longitude=longitude,
            display_name=display_name,
            source="reverse_geocode",
        )

    return await geocode_location(location)
