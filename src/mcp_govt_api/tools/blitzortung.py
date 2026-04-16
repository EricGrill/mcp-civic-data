from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

BLITZORTUNG_BASE = "https://map.blitzortung.org"

REGION_NAMES = {
    1: "Americas",
    2: "Europe",
    3: "Asia",
    4: "Africa",
    5: "Oceania",
}


@mcp.tool()
async def get_recent_lightning_strikes(
    region: int = 1, minutes: int = 10, limit: int = 50
) -> str:
    """Get recent lightning strikes detected by the Blitzortung network.

    Args:
        region: Region code (1=Americas, 2=Europe, 3=Asia, 4=Africa, 5=Oceania)
        minutes: Time window in minutes to look back (default: 10, max: 60)
        limit: Maximum number of strikes to return (default: 50, max: 500)

    Returns:
        Recent lightning strikes with coordinates, timestamps, and signal strength
    """
    try:
        if region not in REGION_NAMES:
            return f"Error: Invalid region code {region}. Valid codes: 1=Americas, 2=Europe, 3=Asia, 4=Africa, 5=Oceania"

        minutes = max(1, min(minutes, 60))
        limit = max(1, min(limit, 500))

        url = f"{BLITZORTUNG_BASE}/GeoJSONStrokes"
        params = {"time": str(minutes), "lang": "en"}

        data = await fetch_json(url, params=params)

        if not data or not isinstance(data, dict):
            return f"No lightning strike data available for {REGION_NAMES[region]}"

        features = data.get("features", [])

        if not features:
            return f"No lightning strikes detected in the last {minutes} minutes"

        # Apply limit
        strikes = features[:limit]

        region_name = REGION_NAMES[region]
        lines: list[str] = [
            f"**Lightning Strikes** - Last {minutes} minute(s)\n"
            f"Region: {region_name} | Showing {len(strikes)} of {len(features)} strikes\n"
        ]

        for i, feature in enumerate(strikes, 1):
            props = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            coords = geometry.get("coordinates", [None, None])

            lon = coords[0] if len(coords) > 0 else "N/A"
            lat = coords[1] if len(coords) > 1 else "N/A"
            timestamp = props.get("time", "N/A")
            polarity = props.get("pol", 0)
            signal_count = props.get("sig", "N/A")
            lateral_error = props.get("lat_err", "N/A")

            polarity_str = "+" if polarity > 0 else "-" if polarity < 0 else "N/A"

            entry = (
                f"**Strike {i}**\n"
                f"  Location: ({lat}, {lon})\n"
                f"  Time: {timestamp}\n"
                f"  Polarity: {polarity_str} | Stations: {signal_count}"
            )
            if lateral_error != "N/A":
                entry += f" | Error: {lateral_error} km"

            lines.append(entry)

        return "\n\n---\n\n".join(lines)

    except Exception as e:
        return f"Error fetching lightning strike data: {e}"


@mcp.tool()
async def get_lightning_summary(region: int = 1, minutes: int = 60) -> str:
    """Get a summary of lightning activity from the Blitzortung network.

    Provides aggregate statistics about recent lightning detections
    including total strike count and geographic spread.

    Args:
        region: Region code (1=Americas, 2=Europe, 3=Asia, 4=Africa, 5=Oceania)
        minutes: Time window in minutes to summarize (default: 60, max: 120)

    Returns:
        Summary of lightning activity including total count, geographic bounds,
        and average signal strength
    """
    try:
        if region not in REGION_NAMES:
            return f"Error: Invalid region code {region}. Valid codes: 1=Americas, 2=Europe, 3=Asia, 4=Africa, 5=Oceania"

        minutes = max(1, min(minutes, 120))

        url = f"{BLITZORTUNG_BASE}/GeoJSONStrokes"
        params = {"time": str(minutes), "lang": "en"}

        data = await fetch_json(url, params=params)

        if not data or not isinstance(data, dict):
            return f"No lightning data available for {REGION_NAMES[region]}"

        features = data.get("features", [])

        if not features:
            return f"No lightning strikes detected in {REGION_NAMES[region]} over the last {minutes} minutes"

        region_name = REGION_NAMES[region]
        total = len(features)

        # Compute geographic bounds and stats
        lats: list[float] = []
        lons: list[float] = []
        positive_count = 0
        negative_count = 0
        station_counts: list[int] = []

        for feature in features:
            geometry = feature.get("geometry", {})
            coords = geometry.get("coordinates", [])
            props = feature.get("properties", {})

            if len(coords) >= 2:
                try:
                    lons.append(float(coords[0]))
                    lats.append(float(coords[1]))
                except (TypeError, ValueError):
                    pass

            polarity = props.get("pol", 0)
            if polarity > 0:
                positive_count += 1
            elif polarity < 0:
                negative_count += 1

            sig = props.get("sig")
            if sig is not None:
                try:
                    station_counts.append(int(sig))
                except (TypeError, ValueError):
                    pass

        rate = total / max(minutes, 1)

        lines: list[str] = [
            f"**Lightning Activity Summary** - {region_name}\n"
            f"Time window: last {minutes} minute(s)\n"
        ]

        lines.append(
            f"**Total Strikes:** {total}\n"
            f"**Strike Rate:** {rate:.1f} strikes/min"
        )

        if lats and lons:
            lines.append(
                f"**Geographic Bounds:**\n"
                f"  Latitude:  {min(lats):.3f} to {max(lats):.3f}\n"
                f"  Longitude: {min(lons):.3f} to {max(lons):.3f}"
            )

        lines.append(
            f"**Polarity:**\n"
            f"  Positive: {positive_count} ({positive_count / total * 100:.1f}%)\n"
            f"  Negative: {negative_count} ({negative_count / total * 100:.1f}%)"
        )

        if station_counts:
            avg_stations = sum(station_counts) / len(station_counts)
            lines.append(
                f"**Detection Stations:**\n"
                f"  Average per strike: {avg_stations:.1f}\n"
                f"  Range: {min(station_counts)} - {max(station_counts)}"
            )

        return "\n\n---\n\n".join(lines)

    except Exception as e:
        return f"Error fetching lightning summary: {e}"
