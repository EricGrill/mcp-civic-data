import csv
import io
import json
import math
import os
import re
import time
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_bytes, fetch_json, fetch_text

PUBLIC_AVIATION_DISCLAIMER = (
    "FAA aviation data is provided for informational use only; verify official FAA, "
    "NOTAM, chart, and flight briefing sources before making operational decisions."
)

REGISTRY_PRIVACY_CAVEAT = (
    "FAA aircraft registry records are public records and may include owner "
    "information; searches are intentionally bounded."
)

FAA_SOURCES: dict[str, dict[str, str]] = {
    "FAA AIS": {
        "auth": "none",
        "freshness": "FAA AIS publication cycle; service metadata reports edit dates",
        "url": "https://adds-faa.opendata.arcgis.com/",
        "caveat": PUBLIC_AVIATION_DISCLAIMER,
    },
    "FAA TFR": {
        "auth": "none",
        "freshness": "active FAA TFR site data",
        "url": "https://tfr.faa.gov/",
        "caveat": PUBLIC_AVIATION_DISCLAIMER,
    },
    "FAA NAS Status": {
        "auth": "none",
        "freshness": "current NAS Status API data",
        "url": "https://nasstatus.faa.gov/",
        "caveat": PUBLIC_AVIATION_DISCLAIMER,
    },
    "FAA Aircraft Registry": {
        "auth": "none",
        "freshness": "daily FAA registry ZIP download",
        "url": "https://registry.faa.gov/database/ReleasableAircraft.zip",
        "caveat": REGISTRY_PRIVACY_CAVEAT,
    },
    "FAA Aircraft Characteristics": {
        "auth": "none",
        "freshness": "FAA published aircraft characteristics workbook",
        "url": "https://www.faa.gov/airports/engineering/aircraft_char_database/aircraft_data",
        "caveat": "Aircraft type characteristics, not live operational data.",
    },
    "FAA Data Catalog": {
        "auth": "none",
        "freshness": "FAA CKAN catalog metadata",
        "url": "https://catalog.data.faa.gov/api/3/action/package_search",
        "caveat": "Catalog discovery only; dataset resources vary.",
    },
    "FAA Wildlife Strike": {
        "auth": "unverified",
        "freshness": "deferred pending production-host validation",
        "url": "https://qa-wildlife.faa.gov/api/swagger/v1/swagger.json",
        "caveat": "Candidate API only; QA-looking hostname is not wrapped in first wave.",
    },
}

FAA_ARCGIS_BASE = "https://services6.arcgis.com/ssFJjBXIUyZDrSYZ/arcgis/rest/services"
FAA_AIS_SERVICES = {
    "airports": f"{FAA_ARCGIS_BASE}/US_Airport/FeatureServer/0/query",
    "runways": f"{FAA_ARCGIS_BASE}/Runways/FeatureServer/0/query",
    "class_airspace": f"{FAA_ARCGIS_BASE}/Class_Airspace/FeatureServer/0/query",
    "special_use_airspace": f"{FAA_ARCGIS_BASE}/Special_Use_Airspace/FeatureServer/0/query",
    "navaids": f"{FAA_ARCGIS_BASE}/NAVAIDSystem/FeatureServer/0/query",
    "designated_points": f"{FAA_ARCGIS_BASE}/DesignatedPoints/FeatureServer/0/query",
    "obstacles": f"{FAA_ARCGIS_BASE}/Digital_Obstacle_File/FeatureServer/0/query",
    "uas_facility_map": f"{FAA_ARCGIS_BASE}/FAA_UAS_FacilityMap_Data_V5/FeatureServer/0/query",
}

FAA_TFR_BASE = "https://tfr.faa.gov"
FAA_TFR_API_BASE = f"{FAA_TFR_BASE}/tfrapi"
FAA_TFR_WFS_URL = f"{FAA_TFR_BASE}/geoserver/TFR/ows"
FAA_NAS_API_BASE = "https://nasstatus.faa.gov/api"
FAA_CATALOG_BASE = "https://catalog.data.faa.gov/api/3"
FAA_REGISTRY_ZIP_URL = "https://registry.faa.gov/database/ReleasableAircraft.zip"
FAA_AIRCRAFT_CHARACTERISTICS_URL = (
    "https://www.faa.gov/airports/engineering/aircraft_char_database/aircraft_data"
)


def _cache_dir() -> Path:
    root = os.environ.get("MCP_CIVIC_DATA_CACHE_DIR")
    if root:
        return Path(root) / "faa"
    return Path.home() / ".cache" / "mcp-civic-data" / "faa"


async def _cached_bytes(url: str, cache_name: str, max_age_seconds: int) -> bytes:
    cache_path = _cache_dir() / cache_name
    if cache_path.exists():
        age = time.time() - cache_path.stat().st_mtime
        if age <= max_age_seconds:
            return cache_path.read_bytes()

    data = await fetch_bytes(url)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(data)
    return data


def _limit(value: int, *, default: int = 10, maximum: int = 50) -> int:
    if value <= 0:
        return default
    return min(value, maximum)


def _sql_quote(value: str) -> str:
    return value.replace("'", "''")


def _contains(field: str, value: str) -> str:
    return f"UPPER({field}) LIKE '%{_sql_quote(value.upper())}%'"


def _equals(field: str, value: str) -> str:
    return f"{field} = '{_sql_quote(value.upper())}'"


def _equals_raw(field: str, value: str) -> str:
    return f"{field} = '{_sql_quote(value)}'"


def _airport_identifier_where(identifier: str) -> str:
    ident = identifier.strip().upper()
    clauses = {_equals("IDENT", ident), _equals("ICAO_ID", ident)}
    if ident.startswith("K") and len(ident) == 4:
        clauses.add(_equals("IDENT", ident[1:]))
    elif len(ident) == 3:
        clauses.add(_equals("ICAO_ID", f"K{ident}"))
    return " OR ".join(sorted(clauses))


def build_arcgis_query_params(
    *,
    where: str = "1=1",
    out_fields: list[str] | None = None,
    limit: int = 10,
    bbox: tuple[float, float, float, float] | None = None,
    return_geometry: bool = True,
) -> dict[str, Any]:
    """Build bounded ArcGIS FeatureServer query parameters."""
    params: dict[str, Any] = {
        "f": "json",
        "where": where or "1=1",
        "outFields": ",".join(out_fields or ["*"]),
        "returnGeometry": "true" if return_geometry else "false",
        "outSR": 4326,
        "resultRecordCount": _limit(limit, maximum=100),
    }
    if bbox:
        xmin, ymin, xmax, ymax = bbox
        params.update(
            {
                "geometryType": "esriGeometryEnvelope",
                "spatialRel": "esriSpatialRelIntersects",
                "inSR": 4326,
                "geometry": json.dumps(
                    {
                        "xmin": xmin,
                        "ymin": ymin,
                        "xmax": xmax,
                        "ymax": ymax,
                        "spatialReference": {"wkid": 4326},
                    }
                ),
            }
        )
    return params


async def _query_arcgis(
    service: str,
    *,
    where: str = "1=1",
    out_fields: list[str] | None = None,
    limit: int = 10,
    bbox: tuple[float, float, float, float] | None = None,
    return_geometry: bool = True,
) -> dict[str, Any]:
    if service not in FAA_AIS_SERVICES:
        valid = ", ".join(sorted(FAA_AIS_SERVICES))
        return {"error": f"Unknown FAA AIS service '{service}'. Valid services: {valid}"}
    params = build_arcgis_query_params(
        where=where,
        out_fields=out_fields,
        limit=limit,
        bbox=bbox,
        return_geometry=return_geometry,
    )
    return await fetch_json(FAA_AIS_SERVICES[service], params=params)


def _features(data: dict[str, Any]) -> list[dict[str, Any]]:
    return list(data.get("features") or [])


def _attrs(feature: dict[str, Any]) -> dict[str, Any]:
    return dict(feature.get("attributes") or feature.get("properties") or {})


def _fmt_value(value: Any) -> str:
    if value is None or value == "":
        return "N/A"
    return str(value)


def _format_feature_lines(
    *,
    title: str,
    data: dict[str, Any],
    fields: list[tuple[str, str]],
    limit: int,
) -> str:
    features = _features(data)[: _limit(limit, maximum=100)]
    if not features:
        return f"No {title.lower()} found.\n\n{PUBLIC_AVIATION_DISCLAIMER}"

    lines = [f"**{title}** (showing {len(features)})\n"]
    for feature in features:
        attrs = _attrs(feature)
        item: list[str] = []
        primary = next((_fmt_value(attrs.get(name)) for name, _ in fields), "FAA record")
        item.append(f"**{primary}**")
        for field, label in fields:
            item.append(f"- {label}: {_fmt_value(attrs.get(field))}")
        geometry = feature.get("geometry")
        if isinstance(geometry, dict):
            if "x" in geometry and "y" in geometry:
                item.append(f"- Geometry: {geometry['y']}, {geometry['x']}")
            elif "rings" in geometry:
                item.append("- Geometry: polygon")
            elif "paths" in geometry:
                item.append("- Geometry: line")
        lines.append("\n".join(item))

    lines.append(PUBLIC_AVIATION_DISCLAIMER)
    return "\n\n---\n\n".join(lines)


def _bbox_around(latitude: float, longitude: float, radius_nm: float) -> tuple[float, float, float, float]:
    radius_nm = max(1.0, min(radius_nm, 250.0))
    lat_delta = radius_nm / 60.0
    lon_scale = max(math.cos(math.radians(latitude)), 0.1)
    lon_delta = radius_nm / (60.0 * lon_scale)
    return (
        longitude - lon_delta,
        latitude - lat_delta,
        longitude + lon_delta,
        latitude + lat_delta,
    )


@mcp.tool()
async def search_faa_airports(query: str = "", state: str = "", limit: int = 10) -> str:
    """Search FAA AIS public airport geodata by identifier, name, city, or state.

    Args:
        query: Airport identifier, ICAO ID, name, or served city.
        state: Optional two-letter state code.
        limit: Maximum records to return (default 10, max 50).

    Returns:
        Matching FAA AIS airport records with location and source caveat.
    """
    clauses = []
    if query.strip():
        q = query.strip()
        exact_clauses = [f"({_airport_identifier_where(q)})"]
        if state.strip():
            exact_clauses.append(_equals("STATE", state.strip()))
        exact_data = await _query_arcgis(
            "airports",
            where=" AND ".join(exact_clauses),
            out_fields=[
                "IDENT",
                "ICAO_ID",
                "NAME",
                "SERVCITY",
                "STATE",
                "TYPE_CODE",
                "OPERSTATUS",
                "LATITUDE",
                "LONGITUDE",
                "ELEVATION",
            ],
            limit=limit,
        )
        if _features(exact_data):
            return _format_feature_lines(
                title="FAA AIS Airports",
                data=exact_data,
                fields=[
                    ("IDENT", "Identifier"),
                    ("ICAO_ID", "ICAO"),
                    ("NAME", "Name"),
                    ("SERVCITY", "Served city"),
                    ("STATE", "State"),
                    ("TYPE_CODE", "Type"),
                    ("OPERSTATUS", "Status"),
                    ("LATITUDE", "Latitude"),
                    ("LONGITUDE", "Longitude"),
                    ("ELEVATION", "Elevation"),
                ],
                limit=limit,
            )
        clauses.append(
            "("
            + " OR ".join(
                [
                    _contains("IDENT", q),
                    _contains("ICAO_ID", q),
                    _contains("NAME", q),
                    _contains("SERVCITY", q),
                ]
            )
            + ")"
        )
    if state.strip():
        clauses.append(_equals("STATE", state.strip()))
    where = " AND ".join(clauses) if clauses else "1=1"
    data = await _query_arcgis(
        "airports",
        where=where,
        out_fields=[
            "IDENT",
            "ICAO_ID",
            "NAME",
            "SERVCITY",
            "STATE",
            "TYPE_CODE",
            "OPERSTATUS",
            "LATITUDE",
            "LONGITUDE",
            "ELEVATION",
        ],
        limit=limit,
    )
    return _format_feature_lines(
        title="FAA AIS Airports",
        data=data,
        fields=[
            ("IDENT", "Identifier"),
            ("ICAO_ID", "ICAO"),
            ("NAME", "Name"),
            ("SERVCITY", "Served city"),
            ("STATE", "State"),
            ("TYPE_CODE", "Type"),
            ("OPERSTATUS", "Status"),
            ("LATITUDE", "Latitude"),
            ("LONGITUDE", "Longitude"),
            ("ELEVATION", "Elevation"),
        ],
        limit=limit,
    )


@mcp.tool()
async def get_faa_airport(identifier: str) -> str:
    """Get one FAA AIS airport record by FAA identifier or ICAO ID."""
    ident = identifier.strip().upper()
    if not ident:
        return "Error: identifier is required."
    where = _airport_identifier_where(ident)
    data = await _query_arcgis(
        "airports",
        where=where,
        out_fields=["*"],
        limit=1,
    )
    return _format_feature_lines(
        title="FAA AIS Airport",
        data=data,
        fields=[
            ("IDENT", "Identifier"),
            ("ICAO_ID", "ICAO"),
            ("NAME", "Name"),
            ("SERVCITY", "Served city"),
            ("STATE", "State"),
            ("COUNTRY", "Country"),
            ("TYPE_CODE", "Type"),
            ("OPERSTATUS", "Status"),
            ("PRIVATEUSE", "Private use"),
            ("LATITUDE", "Latitude"),
            ("LONGITUDE", "Longitude"),
            ("ELEVATION", "Elevation"),
        ],
        limit=1,
    )


@mcp.tool()
async def get_faa_runways(airport_id: str, limit: int = 20) -> str:
    """Get FAA AIS runway records for an airport identifier."""
    ident = airport_id.strip().upper()
    if not ident:
        return "Error: airport_id is required."
    airport_data = await _query_arcgis(
        "airports",
        where=_airport_identifier_where(ident),
        out_fields=["GLOBAL_ID", "IDENT", "ICAO_ID", "NAME"],
        limit=1,
        return_geometry=False,
    )
    airport_features = _features(airport_data)
    if not airport_features:
        return f"No FAA AIS airport found for {ident}.\n\n{PUBLIC_AVIATION_DISCLAIMER}"
    airport_guid = _attrs(airport_features[0]).get("GLOBAL_ID")
    if not airport_guid:
        return f"FAA AIS airport {ident} did not include a runway lookup identifier."
    where = _equals_raw("AIRPORT_ID", str(airport_guid))
    data = await _query_arcgis(
        "runways",
        where=where,
        out_fields=["AIRPORT_ID", "DESIGNATOR", "LENGTH", "WIDTH", "DIM_UOM", "COMP_CODE"],
        limit=limit,
    )
    return _format_feature_lines(
        title=f"FAA AIS Runways for {ident}",
        data=data,
        fields=[
            ("AIRPORT_ID", "Airport"),
            ("DESIGNATOR", "Runway"),
            ("LENGTH", "Length"),
            ("WIDTH", "Width"),
            ("DIM_UOM", "Units"),
            ("COMP_CODE", "Composition"),
        ],
        limit=limit,
    )


@mcp.tool()
async def get_faa_airspace_near(
    latitude: float,
    longitude: float,
    radius_nm: float = 25,
    limit: int = 20,
) -> str:
    """Get FAA class and special-use airspace records near a coordinate."""
    bbox = _bbox_around(latitude, longitude, radius_nm)
    class_data = await _query_arcgis(
        "class_airspace",
        bbox=bbox,
        out_fields=[
            "IDENT",
            "ICAO_ID",
            "NAME",
            "CLASS",
            "TYPE_CODE",
            "LOWER_DESC",
            "UPPER_DESC",
            "CITY",
            "STATE",
        ],
        limit=limit,
    )
    sua_data = await _query_arcgis(
        "special_use_airspace",
        bbox=bbox,
        out_fields=["IDENT", "NAME", "TYPE_CODE", "LOWER_DESC", "UPPER_DESC", "STATE"],
        limit=limit,
    )
    class_section = _format_feature_lines(
        title="FAA AIS Class Airspace",
        data=class_data,
        fields=[
            ("IDENT", "Identifier"),
            ("ICAO_ID", "ICAO"),
            ("NAME", "Name"),
            ("CLASS", "Class"),
            ("TYPE_CODE", "Type"),
            ("LOWER_DESC", "Lower"),
            ("UPPER_DESC", "Upper"),
            ("CITY", "City"),
            ("STATE", "State"),
        ],
        limit=limit,
    )
    sua_section = _format_feature_lines(
        title="FAA AIS Special Use Airspace",
        data=sua_data,
        fields=[
            ("IDENT", "Identifier"),
            ("NAME", "Name"),
            ("TYPE_CODE", "Type"),
            ("LOWER_DESC", "Lower"),
            ("UPPER_DESC", "Upper"),
            ("STATE", "State"),
        ],
        limit=limit,
    )
    return f"{class_section}\n\n===\n\n{sua_section}"


@mcp.tool()
async def get_faa_uas_facility_map(
    latitude: float,
    longitude: float,
    radius_nm: float = 10,
    limit: int = 20,
) -> str:
    """Get FAA UAS Facility Map records near a coordinate."""
    data = await _query_arcgis(
        "uas_facility_map",
        bbox=_bbox_around(latitude, longitude, radius_nm),
        out_fields=["*"],
        limit=limit,
    )
    return _format_feature_lines(
        title="FAA UAS Facility Map Data",
        data=data,
        fields=[
            ("FACILITY", "Facility"),
            ("CEILING", "Ceiling"),
            ("APT1_FAAID", "Airport"),
            ("GLOBAL_ID", "Global ID"),
        ],
        limit=limit,
    )


@mcp.tool()
async def query_faa_ais(
    service: str,
    where: str = "1=1",
    limit: int = 10,
    bbox: list[float] | None = None,
) -> dict[str, Any]:
    """Make a raw bounded query to a public FAA AIS ArcGIS FeatureServer layer.

    Args:
        service: One of airports, runways, class_airspace, special_use_airspace,
                 navaids, designated_points, obstacles, uas_facility_map.
        where: ArcGIS SQL where clause.
        limit: Maximum records to return (default 10, max 100).
        bbox: Optional bounding box [xmin, ymin, xmax, ymax] in EPSG:4326.

    Returns:
        Raw FAA AIS ArcGIS JSON response.
    """
    bbox_tuple = (
        (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
        if bbox and len(bbox) == 4
        else None
    )
    return await _query_arcgis(
        service,
        where=where,
        limit=limit,
        bbox=bbox_tuple,
    )


def tfr_detail_url(notam_id: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", notam_id.strip()).strip("_")
    return f"{FAA_TFR_BASE}/download/detail_{normalized}.xml"


def parse_tfr_detail_xml(xml_text: str) -> dict[str, str]:
    """Extract leaf XML tags from a TFR detail document."""
    root = ElementTree.fromstring(xml_text)
    result: dict[str, str] = {}
    for elem in root.iter():
        if list(elem):
            continue
        text = (elem.text or "").strip()
        if not text:
            continue
        tag = elem.tag.split("}", 1)[-1]
        if tag not in result:
            result[tag] = text
        if len(result) >= 80:
            break
    return result


def _filter_tfr_records(
    records: list[dict[str, Any]],
    *,
    state: str = "",
    tfr_type: str = "",
    facility: str = "",
) -> list[dict[str, Any]]:
    filtered = []
    for record in records:
        if state and str(record.get("state", "")).upper() != state.upper():
            continue
        if tfr_type and str(record.get("type", "")).upper() != tfr_type.upper():
            continue
        if facility and str(record.get("facility", "")).upper() != facility.upper():
            continue
        filtered.append(record)
    return filtered


def format_tfr_list(
    records: list[dict[str, Any]],
    *,
    state: str = "",
    tfr_type: str = "",
    facility: str = "",
    limit: int = 20,
) -> str:
    filtered = _filter_tfr_records(
        records,
        state=state,
        tfr_type=tfr_type,
        facility=facility,
    )[: _limit(limit, maximum=100)]
    if not filtered:
        return f"No active FAA TFRs found for the requested filters.\n\n{PUBLIC_AVIATION_DISCLAIMER}"
    lines = [f"**FAA Active Temporary Flight Restrictions** (showing {len(filtered)})\n"]
    for record in filtered:
        notam_id = _fmt_value(record.get("notam_id") or record.get("NOTAM_KEY"))
        lines.append(
            f"**{notam_id}**\n"
            f"- Facility: {_fmt_value(record.get('facility'))}\n"
            f"- State: {_fmt_value(record.get('state'))}\n"
            f"- Type: {_fmt_value(record.get('type'))}\n"
            f"- Description: {_fmt_value(record.get('description'))}\n"
            f"- Modified: {_fmt_value(record.get('mod_date') or record.get('LAST_MODIFICATION_DATETIME'))}\n"
            f"- Detail XML: {tfr_detail_url(notam_id)}"
        )
    lines.append(PUBLIC_AVIATION_DISCLAIMER)
    return "\n\n---\n\n".join(lines)


def _format_tfr_summary(records: list[dict[str, Any]]) -> str:
    if not records:
        return "No FAA TFR summary records returned."
    lines = ["**FAA TFR Summary**\n"]
    for record in records:
        lines.append(
            f"- {_fmt_value(record.get('center_id') or record.get('icao_name'))}: "
            f"{_fmt_value(record.get('total_count'))} active, "
            f"{_fmt_value(record.get('last_24_hours'))} in last 24h"
        )
    lines.append(PUBLIC_AVIATION_DISCLAIMER)
    return "\n".join(lines)


@mcp.tool()
async def get_faa_tfrs(
    state: str = "",
    tfr_type: str = "",
    facility: str = "",
    limit: int = 20,
) -> str:
    """Get active FAA Temporary Flight Restrictions from the public TFR API."""
    records = await fetch_json(f"{FAA_TFR_API_BASE}/getTfrList")
    if not isinstance(records, list):
        return "Unexpected FAA TFR API response."
    return format_tfr_list(
        records,
        state=state,
        tfr_type=tfr_type,
        facility=facility,
        limit=limit,
    )


@mcp.tool()
async def get_faa_tfr_summary() -> str:
    """Get FAA TFR counts by center/facility from the public TFR API."""
    records = await fetch_json(f"{FAA_TFR_API_BASE}/getSummary")
    if not isinstance(records, list):
        return "Unexpected FAA TFR summary response."
    return _format_tfr_summary(records)


@mcp.tool()
async def get_faa_tfr_shapes(state: str = "", limit: int = 25) -> dict[str, Any]:
    """Get active FAA TFR shapes from the public GeoServer WFS endpoint."""
    params = {
        "service": "WFS",
        "version": "1.1.0",
        "request": "GetFeature",
        "typeName": "TFR:V_TFR_LOC",
        "maxFeatures": _limit(limit, maximum=300),
        "outputFormat": "application/json",
        "srsname": "EPSG:4326",
    }
    data = await fetch_json(FAA_TFR_WFS_URL, params=params)
    if state:
        features = [
            feature
            for feature in data.get("features", [])
            if str(feature.get("properties", {}).get("STATE", "")).upper()
            == state.upper()
        ]
        data = dict(data)
        data["features"] = features[: _limit(limit, maximum=300)]
    data["source_caveat"] = PUBLIC_AVIATION_DISCLAIMER
    return data


@mcp.tool()
async def get_faa_tfr_detail(notam_id: str) -> dict[str, str]:
    """Get parsed FAA TFR detail XML for a NOTAM ID such as '6/2842'."""
    xml_text = await fetch_text(tfr_detail_url(notam_id))
    parsed = parse_tfr_detail_xml(xml_text)
    parsed["source_url"] = tfr_detail_url(notam_id)
    parsed["source_caveat"] = PUBLIC_AVIATION_DISCLAIMER
    return parsed


def _event_parts(event: dict[str, Any]) -> list[str]:
    parts: list[str] = []
    ground_stop = event.get("groundStop")
    if ground_stop:
        parts.append(
            "Ground Stop: "
            + _fmt_value(ground_stop.get("reason") or ground_stop.get("impactingCondition"))
        )
    ground_delay = event.get("groundDelay")
    if ground_delay:
        parts.append(
            "Ground Delay: "
            f"avg {_fmt_value(ground_delay.get('avgDelay'))} min, "
            f"max {_fmt_value(ground_delay.get('maxDelay'))} min"
            f" ({_fmt_value(ground_delay.get('impactingCondition'))})"
        )
    closure = event.get("airportClosure")
    if closure:
        parts.append("Airport Closure: " + _fmt_value(closure.get("simpleText") or closure.get("text")))
    free_form = event.get("freeForm")
    if free_form:
        parts.append("Notice: " + _fmt_value(free_form.get("simpleText") or free_form.get("text")))
    arrival_delay = event.get("arrivalDelay")
    if arrival_delay:
        parts.append("Arrival Delay: " + _fmt_value(arrival_delay.get("delayReason") or arrival_delay))
    departure_delay = event.get("departureDelay")
    if departure_delay:
        parts.append("Departure Delay: " + _fmt_value(departure_delay.get("delayReason") or departure_delay))
    deicing = event.get("deicing")
    if deicing:
        parts.append("Deicing: " + _fmt_value(deicing.get("status") or deicing))
    airport_config = event.get("airportConfig")
    if airport_config:
        parts.append(
            "Runway config: "
            f"arrivals {_fmt_value(airport_config.get('arrivalRunwayConfig'))}, "
            f"departures {_fmt_value(airport_config.get('departureRunwayConfig'))}"
        )
    return parts


def format_nas_airport_events(
    events: list[dict[str, Any]],
    *,
    airport: str = "",
    event_type: str = "",
    limit: int = 20,
) -> str:
    filtered: list[dict[str, Any]] = []
    for event in events:
        if airport and str(event.get("airportId", "")).upper() != airport.upper():
            continue
        if event_type and not event.get(event_type):
            continue
        filtered.append(event)

    filtered = filtered[: _limit(limit, maximum=100)]
    if not filtered:
        return f"No FAA NAS Status airport events found.\n\n{PUBLIC_AVIATION_DISCLAIMER}"

    lines = [f"**FAA NAS Status Airport Events** (showing {len(filtered)})\n"]
    for event in filtered:
        airport_id = _fmt_value(event.get("airportId"))
        name = _fmt_value(event.get("airportLongName"))
        parts = _event_parts(event)
        lines.append(
            f"**{airport_id} - {name}**\n"
            + "\n".join(f"- {part}" for part in parts)
        )
    lines.append(PUBLIC_AVIATION_DISCLAIMER)
    return "\n\n---\n\n".join(lines)


async def _nas_airport_events() -> list[dict[str, Any]]:
    data = await fetch_json(f"{FAA_NAS_API_BASE}/airport-events")
    return data if isinstance(data, list) else []


@mcp.tool()
async def get_faa_nas_airport_events(airport: str = "", limit: int = 20) -> str:
    """Get current FAA NAS Status airport events, optionally filtered by airport."""
    return format_nas_airport_events(await _nas_airport_events(), airport=airport, limit=limit)


@mcp.tool()
async def get_faa_ground_stops(airport: str = "", limit: int = 20) -> str:
    """Get current FAA NAS Status airport ground stop events."""
    return format_nas_airport_events(
        await _nas_airport_events(),
        airport=airport,
        event_type="groundStop",
        limit=limit,
    )


@mcp.tool()
async def get_faa_ground_delays(airport: str = "", limit: int = 20) -> str:
    """Get current FAA NAS Status airport ground delay events."""
    return format_nas_airport_events(
        await _nas_airport_events(),
        airport=airport,
        event_type="groundDelay",
        limit=limit,
    )


@mcp.tool()
async def get_faa_airport_closures(airport: str = "", limit: int = 20) -> str:
    """Get current FAA NAS Status airport closure events."""
    return format_nas_airport_events(
        await _nas_airport_events(),
        airport=airport,
        event_type="airportClosure",
        limit=limit,
    )


@mcp.tool()
async def get_faa_operations_plan() -> dict[str, Any]:
    """Get the current FAA NAS Status operations plan JSON."""
    data = await fetch_json(f"{FAA_NAS_API_BASE}/operations-plan")
    if isinstance(data, dict):
        data = dict(data)
        data["source_caveat"] = PUBLIC_AVIATION_DISCLAIMER
    return data


@mcp.tool()
async def get_faa_artcc_boundaries() -> dict[str, Any]:
    """Get FAA NAS Status ARTCC boundary data."""
    data = await fetch_json(f"{FAA_NAS_API_BASE}/artcc-boundaries")
    return {"boundaries": data, "source_caveat": PUBLIC_AVIATION_DISCLAIMER}


def _read_csv_from_zip(archive: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    try:
        raw = archive.read(name)
    except KeyError:
        return []
    text = raw.decode("utf-8", errors="replace")
    rows = csv.DictReader(io.StringIO(text))
    return [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in rows]


def _norm_header(row: dict[str, str], key: str) -> str:
    return row.get(key, row.get(key.upper(), row.get(key.lower(), ""))).strip()


def normalize_n_number(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]", "", value).upper()
    if not value:
        return ""
    return value if value.startswith("N") else f"N{value}"


def parse_aircraft_registry_zip(zip_data: bytes) -> dict[str, Any]:
    """Parse FAA registry ZIP bytes into normalized master/reference records."""
    with zipfile.ZipFile(io.BytesIO(zip_data)) as archive:
        master_rows = _read_csv_from_zip(archive, "MASTER.txt")
        acft_rows = _read_csv_from_zip(archive, "ACFTREF.txt")

    refs: dict[str, dict[str, str]] = {}
    for row in acft_rows:
        code = _norm_header(row, "CODE")
        if code:
            refs[code] = row

    records: list[dict[str, str]] = []
    by_n_number: dict[str, dict[str, str]] = {}
    for row in master_rows:
        n_number = normalize_n_number(_norm_header(row, "N-NUMBER"))
        if not n_number:
            continue
        model_code = _norm_header(row, "MFR MDL CODE")
        ref = refs.get(model_code, {})
        record = {
            "n_number": n_number,
            "registrant_name": _norm_header(row, "NAME"),
            "manufacturer": _norm_header(ref, "MFR"),
            "model": _norm_header(ref, "MODEL"),
            "model_code": model_code,
            "serial_number": _norm_header(row, "SERIAL NUMBER"),
            "state": _norm_header(row, "STATE"),
            "status_code": _norm_header(row, "STATUS CODE"),
        }
        records.append(record)
        by_n_number[n_number] = record

    return {
        "records": records,
        "by_n_number": by_n_number,
        "aircraft_reference": refs,
        "source_caveat": REGISTRY_PRIVACY_CAVEAT,
    }


def lookup_aircraft_registration_record(
    registry: dict[str, Any],
    n_number: str,
) -> dict[str, str] | None:
    return registry.get("by_n_number", {}).get(normalize_n_number(n_number))


def search_aircraft_registry_records(
    registry: dict[str, Any],
    *,
    make: str = "",
    model: str = "",
    state: str = "",
    status: str = "",
    limit: int = 10,
) -> list[dict[str, str]]:
    limit = _limit(limit, maximum=25)
    results: list[dict[str, str]] = []
    for record in registry.get("records", []):
        if make and make.upper() not in record.get("manufacturer", "").upper():
            continue
        if model and model.upper() not in record.get("model", "").upper():
            continue
        if state and state.upper() != record.get("state", "").upper():
            continue
        if status and status.upper() != record.get("status_code", "").upper():
            continue
        results.append(record)
        if len(results) >= limit:
            break
    return results


async def _aircraft_registry() -> dict[str, Any]:
    zip_data = await _cached_bytes(FAA_REGISTRY_ZIP_URL, "ReleasableAircraft.zip", 24 * 60 * 60)
    return parse_aircraft_registry_zip(zip_data)


def _format_registry_record(record: dict[str, str]) -> str:
    return (
        f"**{record.get('n_number', 'N/A')}**\n"
        f"- Manufacturer: {_fmt_value(record.get('manufacturer'))}\n"
        f"- Model: {_fmt_value(record.get('model'))}\n"
        f"- Serial number: {_fmt_value(record.get('serial_number'))}\n"
        f"- Registrant: {_fmt_value(record.get('registrant_name'))}\n"
        f"- State: {_fmt_value(record.get('state'))}\n"
        f"- Status code: {_fmt_value(record.get('status_code'))}"
    )


@mcp.tool()
async def lookup_faa_aircraft_registration(n_number: str) -> str:
    """Look up one aircraft in the FAA public aircraft registry by N-number."""
    registry = await _aircraft_registry()
    record = lookup_aircraft_registration_record(registry, n_number)
    if not record:
        return f"No FAA aircraft registry record found for {normalize_n_number(n_number)}."
    return f"{_format_registry_record(record)}\n\n{REGISTRY_PRIVACY_CAVEAT}"


@mcp.tool()
async def search_faa_aircraft_registry(
    make: str = "",
    model: str = "",
    state: str = "",
    status: str = "",
    limit: int = 10,
) -> str:
    """Search bounded FAA public aircraft registry records."""
    if not any([make.strip(), model.strip(), state.strip(), status.strip()]):
        return "Error: provide at least one filter: make, model, state, or status."
    registry = await _aircraft_registry()
    records = search_aircraft_registry_records(
        registry,
        make=make,
        model=model,
        state=state,
        status=status,
        limit=limit,
    )
    if not records:
        return "No FAA aircraft registry records found for the requested filters."
    lines = [f"**FAA Aircraft Registry Search** (showing {len(records)})\n"]
    lines.extend(_format_registry_record(record) for record in records)
    lines.append(REGISTRY_PRIVACY_CAVEAT)
    return "\n\n---\n\n".join(lines)


def _cell_text(cell: ElementTree.Element, shared_strings: list[str]) -> str:
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    value = cell.find(f"{ns}v")
    if value is None or value.text is None:
        inline = cell.find(f"{ns}is/{ns}t")
        return (inline.text or "").strip() if inline is not None else ""
    text = value.text.strip()
    if cell.attrib.get("t") == "s":
        try:
            return shared_strings[int(text)]
        except (ValueError, IndexError):
            return ""
    return text


def _column_index(cell_ref: str) -> int:
    letters = re.sub(r"[^A-Z]", "", cell_ref.upper())
    index = 0
    for letter in letters:
        index = index * 26 + (ord(letter) - ord("A") + 1)
    return max(index - 1, 0)


def read_xlsx_rows(xlsx_data: bytes) -> list[list[str]]:
    """Read rows from the first worksheet in a simple XLSX workbook."""
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(io.BytesIO(xlsx_data)) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall(f"{ns}si"):
                texts = [node.text or "" for node in item.iter(f"{ns}t")]
                shared_strings.append("".join(texts))

        sheet_names = sorted(
            name
            for name in archive.namelist()
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        )
        if not sheet_names:
            return []
        root = ElementTree.fromstring(archive.read(sheet_names[0]))

    rows: list[list[str]] = []
    for row in root.findall(f".//{ns}row"):
        values: dict[int, str] = {}
        max_index = -1
        for cell in row.findall(f"{ns}c"):
            idx = _column_index(cell.attrib.get("r", "A1"))
            values[idx] = _cell_text(cell, shared_strings)
            max_index = max(max_index, idx)
        if max_index >= 0:
            rows.append([values.get(i, "") for i in range(max_index + 1)])
    return rows


def _normalize_header(value: str) -> str:
    value = value.strip().lower()
    value = value.replace("(", "").replace(")", "")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def parse_aircraft_characteristics_rows(rows: list[list[str]]) -> list[dict[str, str]]:
    if not rows:
        return []
    header_index = 0
    for idx, row in enumerate(rows[:10]):
        normalized = [_normalize_header(cell) for cell in row]
        if any(item in normalized for item in ["icao_code", "icao", "icao_aircraft_type"]):
            header_index = idx
            break
    headers = [_normalize_header(cell) for cell in rows[header_index]]
    records: list[dict[str, str]] = []
    for row in rows[header_index + 1 :]:
        raw = {headers[i]: row[i].strip() for i in range(min(len(headers), len(row)))}
        icao = raw.get("icao_code") or raw.get("icao") or raw.get("icao_aircraft_type")
        if not icao:
            continue
        wingspan = (
            raw.get("wingspan_ft")
            or raw.get("wingspan_ft_with_winglets_sharklets")
            or raw.get("wingspan_ft_without_winglets_sharklets")
            or raw.get("wingspan", "")
        )
        record = {
            "icao_code": icao.upper(),
            "manufacturer": raw.get("manufacturer", raw.get("make", "")).upper(),
            "model": raw.get("model") or raw.get("model_faa") or raw.get("aircraft_model", ""),
            "wingspan_ft": wingspan,
            "approach_category": raw.get(
                "approach_category",
                raw.get("aac", raw.get("aircraft_approach_category", "")),
            ),
        }
        for key, value in raw.items():
            record.setdefault(key, value)
        records.append(record)
    return records


def find_aircraft_characteristics(
    records: list[dict[str, str]],
    query: str,
) -> dict[str, str] | None:
    q = query.strip().upper()
    for record in records:
        if record.get("icao_code", "").upper() == q:
            return record
    for record in records:
        haystack = " ".join(
            [record.get("manufacturer", ""), record.get("model", ""), record.get("icao_code", "")]
        ).upper()
        if q in haystack:
            return record
    return None


async def _aircraft_characteristics_records() -> list[dict[str, str]]:
    xlsx_data = await _cached_bytes(
        FAA_AIRCRAFT_CHARACTERISTICS_URL,
        "aircraft_characteristics.xlsx",
        7 * 24 * 60 * 60,
    )
    return parse_aircraft_characteristics_rows(read_xlsx_rows(xlsx_data))


@mcp.tool()
async def get_faa_aircraft_type_characteristics(query: str) -> str:
    """Look up FAA aircraft type characteristics by ICAO type, make, or model."""
    records = await _aircraft_characteristics_records()
    record = find_aircraft_characteristics(records, query)
    if not record:
        return f"No FAA aircraft characteristics record found for '{query}'."
    return (
        f"**{record.get('icao_code', query.upper())} - {record.get('manufacturer', '')} "
        f"{record.get('model', '')}**\n"
        f"- Wingspan: {_fmt_value(record.get('wingspan_ft'))} ft\n"
        f"- Approach category: {_fmt_value(record.get('approach_category'))}\n"
        f"- Source: FAA Aircraft Characteristics Database\n\n"
        "Aircraft characteristics are planning/design data, not live operational data."
    )


@mcp.tool()
async def search_faa_aircraft_type_characteristics(query: str, limit: int = 10) -> str:
    """Search FAA aircraft type characteristics by ICAO type, make, or model."""
    records = await _aircraft_characteristics_records()
    q = query.upper().strip()
    matches = [
        record
        for record in records
        if q
        in " ".join(
            [record.get("icao_code", ""), record.get("manufacturer", ""), record.get("model", "")]
        ).upper()
    ][: _limit(limit, maximum=25)]
    if not matches:
        return f"No FAA aircraft characteristics records found for '{query}'."
    lines = [f"**FAA Aircraft Characteristics Search** (showing {len(matches)})\n"]
    for record in matches:
        lines.append(
            f"**{record.get('icao_code', 'N/A')}** - "
            f"{record.get('manufacturer', '')} {record.get('model', '')}\n"
            f"- Wingspan: {_fmt_value(record.get('wingspan_ft'))} ft\n"
            f"- Approach category: {_fmt_value(record.get('approach_category'))}"
        )
    return "\n\n---\n\n".join(lines)


def format_faa_catalog_results(data: dict[str, Any], *, query: str, rows: int) -> str:
    result = data.get("result", {})
    datasets = result.get("results", [])[: _limit(rows, maximum=50)]
    total = result.get("count", 0)
    if not datasets:
        return f"No FAA catalog datasets found for '{query}'."
    output = [f"**FAA Data Catalog Search: '{query}'**"]
    output.append(f"Found {total} datasets (showing {len(datasets)})\n")
    for dataset in datasets:
        resources = dataset.get("resources", [])
        lines = [
            f"**{dataset.get('title', 'Untitled')}**",
            f"Last updated: {_fmt_value(str(dataset.get('metadata_modified', ''))[:10])}",
            f"Resources: {len(resources)}",
            str(dataset.get("notes", "No description"))[:240],
        ]
        for resource in resources[:5]:
            lines.append(
                f"- [{_fmt_value(resource.get('format'))}] "
                f"{_fmt_value(resource.get('name') or resource.get('description'))}: "
                f"{_fmt_value(resource.get('url'))}"
            )
        output.append("\n".join(lines))
    return "\n\n---\n\n".join(output)


@mcp.tool()
async def search_faa_catalog(query: str, rows: int = 10) -> str:
    """Search the FAA Data Catalog CKAN API."""
    rows = _limit(rows, maximum=50)
    data = await fetch_json(
        f"{FAA_CATALOG_BASE}/action/package_search",
        params={"q": query, "rows": rows},
    )
    return format_faa_catalog_results(data, query=query, rows=rows)


@mcp.tool()
async def query_faa_catalog(action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Make a raw query to the FAA Data Catalog CKAN API."""
    return await fetch_json(f"{FAA_CATALOG_BASE}/action/{action}", params=params)
