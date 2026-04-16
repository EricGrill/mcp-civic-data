from datetime import datetime, timedelta

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json


COOPS_DATA_BASE = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
COOPS_STATIONS_BASE = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json"


def _default_date_range() -> tuple[str, str]:
    """Return today and tomorrow as YYYYMMDD strings."""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    return today.strftime("%Y%m%d"), tomorrow.strftime("%Y%m%d")


def _format_predictions(data: dict, station_id: str, datum: str) -> str:
    """Format tide prediction data into a readable string."""
    predictions = data.get("predictions", [])
    if not predictions:
        return f"No tide predictions found for station {station_id}"

    lines = [f"**Tide Predictions for Station {station_id}** (Datum: {datum})"]

    for pred in predictions:
        time_str = pred.get("t", "")
        value = pred.get("v", "N/A")
        lines.append(f"  {time_str}: {value} ft")

    return "\n".join(lines)


def _format_water_levels(data: dict, station_id: str, datum: str) -> str:
    """Format observed water level data into a readable string."""
    observations = data.get("data", [])
    if not observations:
        return f"No water level data found for station {station_id}"

    lines = [f"**Observed Water Levels for Station {station_id}** (Datum: {datum})"]

    for obs in observations:
        time_str = obs.get("t", "")
        value = obs.get("v", "N/A")
        quality = obs.get("q", "")
        flag = f" [{quality}]" if quality else ""
        lines.append(f"  {time_str}: {value} ft{flag}")

    return "\n".join(lines)


def _format_stations(data: dict, state: str) -> str:
    """Format station list data into a readable string."""
    stations = data.get("stations", [])
    if not stations:
        label = f" in {state.upper()}" if state else ""
        return f"No tide stations found{label}"

    label = f" in {state.upper()}" if state else ""
    lines = [f"**NOAA CO-OPS Tide Stations{label}** ({len(stations)} results)"]

    for stn in stations:
        stn_id = stn.get("id", "N/A")
        name = stn.get("name", "Unknown")
        state_code = stn.get("state", "")
        lat = stn.get("lat", "")
        lng = stn.get("lng", "")
        location = f" ({lat}, {lng})" if lat and lng else ""
        state_part = f", {state_code}" if state_code else ""
        lines.append(f"  {stn_id}: {name}{state_part}{location}")

    return "\n".join(lines)


@mcp.tool()
async def get_tide_predictions(
    station_id: str,
    begin_date: str = "",
    end_date: str = "",
    datum: str = "MLLW",
) -> str:
    """Get tide predictions for a NOAA CO-OPS station.

    Returns predicted tide water levels (high/low tides) for the specified
    station and date range. Defaults to today through tomorrow if no dates
    are provided.

    Args:
        station_id: NOAA CO-OPS station ID (e.g., '8454000' for Providence, RI).
        begin_date: Start date as YYYYMMDD (e.g., '20240101'). Defaults to today.
        end_date: End date as YYYYMMDD (e.g., '20240102'). Defaults to tomorrow.
        datum: Tidal datum reference. Options: MLLW, MSL, NAVD, etc.
               Defaults to MLLW (Mean Lower Low Water).

    Returns:
        Predicted tide levels with timestamps, or an error message.
    """
    station_id = station_id.strip()
    if not station_id:
        return "Error: A station ID must be provided (e.g., '8454000')"

    if not begin_date or not end_date:
        default_begin, default_end = _default_date_range()
        begin_date = begin_date or default_begin
        end_date = end_date or default_end

    params = {
        "begin_date": begin_date,
        "end_date": end_date,
        "station": station_id,
        "product": "predictions",
        "datum": datum,
        "units": "english",
        "time_zone": "lst_ldt",
        "format": "json",
    }

    try:
        data = await fetch_json(COOPS_DATA_BASE, params=params)
    except Exception as e:
        return f"Error fetching tide predictions: {e}"

    if "error" in data:
        return f"NOAA CO-OPS API error: {data['error'].get('message', str(data['error']))}"

    return _format_predictions(data, station_id, datum)


@mcp.tool()
async def get_water_levels(
    station_id: str,
    begin_date: str = "",
    end_date: str = "",
    datum: str = "MLLW",
) -> str:
    """Get observed water levels from a NOAA CO-OPS station.

    Returns actual measured water levels from tide gauges at the specified
    station. Defaults to today through tomorrow if no dates are provided.

    Args:
        station_id: NOAA CO-OPS station ID (e.g., '8454000' for Providence, RI).
        begin_date: Start date as YYYYMMDD (e.g., '20240101'). Defaults to today.
        end_date: End date as YYYYMMDD (e.g., '20240102'). Defaults to tomorrow.
        datum: Tidal datum reference. Options: MLLW, MSL, NAVD, etc.
               Defaults to MLLW (Mean Lower Low Water).

    Returns:
        Observed water levels with timestamps and quality flags, or an error message.
    """
    station_id = station_id.strip()
    if not station_id:
        return "Error: A station ID must be provided (e.g., '8454000')"

    if not begin_date or not end_date:
        default_begin, default_end = _default_date_range()
        begin_date = begin_date or default_begin
        end_date = end_date or default_end

    params = {
        "begin_date": begin_date,
        "end_date": end_date,
        "station": station_id,
        "product": "water_level",
        "datum": datum,
        "units": "english",
        "time_zone": "lst_ldt",
        "format": "json",
    }

    try:
        data = await fetch_json(COOPS_DATA_BASE, params=params)
    except Exception as e:
        return f"Error fetching water levels: {e}"

    if "error" in data:
        return f"NOAA CO-OPS API error: {data['error'].get('message', str(data['error']))}"

    return _format_water_levels(data, station_id, datum)


@mcp.tool()
async def search_tide_stations(state: str = "", limit: int = 20) -> str:
    """Search for NOAA CO-OPS tide prediction stations.

    Returns a list of stations that provide tide predictions. Optionally
    filter by US state code.

    Args:
        state: Two-letter US state code to filter by (e.g., 'CA', 'FL').
               Leave empty to list all stations.
        limit: Maximum number of stations to return (default 20).

    Returns:
        List of station IDs, names, and locations, or an error message.
    """
    params: dict[str, str] = {
        "type": "tidepredictions",
    }

    if state:
        state = state.upper().strip()
        if len(state) != 2:
            return "Error: State must be a 2-letter code (e.g., 'CA', 'FL')"
        params["state"] = state

    try:
        data = await fetch_json(COOPS_STATIONS_BASE, params=params)
    except Exception as e:
        return f"Error searching tide stations: {e}"

    # Apply limit to stations list
    stations = data.get("stations", [])
    if stations and limit:
        data["stations"] = stations[:limit]

    return _format_stations(data, state)
