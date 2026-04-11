from mcp_govt_api.server import mcp
from mcp_govt_api.utils.location import resolve_location


@mcp.tool()
async def lookup_location(
    location: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
) -> str:
    """Resolve a place name, ZIP code, address, or coordinates to a normalized location.

    Args:
        location: Free-form location string such as a city, ZIP code, address,
            or a plain 'lat, lon' coordinate pair.
        latitude: Latitude in decimal degrees when resolving coordinates directly.
        longitude: Longitude in decimal degrees when resolving coordinates directly.

    Returns:
        A normalized location summary including display name, coordinates, and source.
    """
    resolved = await resolve_location(
        location=location,
        latitude=latitude,
        longitude=longitude,
    )
    return (
        f"**{resolved.display_name}**\n\n"
        f"Latitude: {resolved.latitude:.4f}\n"
        f"Longitude: {resolved.longitude:.4f}\n"
        f"Source: {resolved.source}"
    )
