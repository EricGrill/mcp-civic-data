import asyncio
import io
import zipfile

from mcp_govt_api.tools import faa


def _zip_bytes(files: dict[str, str | bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def _minimal_xlsx() -> bytes:
    return _zip_bytes(
        {
            "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8"?>
                <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
                  <Override PartName="/xl/worksheets/sheet1.xml"
                    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
                  <Override PartName="/xl/sharedStrings.xml"
                    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
                </Types>""",
            "xl/sharedStrings.xml": """<?xml version="1.0" encoding="UTF-8"?>
                <sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
                  <si><t>ICAO Code</t></si>
                  <si><t>Manufacturer</t></si>
                  <si><t>Model</t></si>
                  <si><t>Wingspan (ft)</t></si>
                  <si><t>Approach Category</t></si>
                  <si><t>B738</t></si>
                  <si><t>BOEING</t></si>
                  <si><t>737-800</t></si>
                  <si><t>117.5</t></si>
                  <si><t>C</t></si>
                </sst>""",
            "xl/worksheets/sheet1.xml": """<?xml version="1.0" encoding="UTF-8"?>
                <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
                  <sheetData>
                    <row r="1">
                      <c r="A1" t="s"><v>0</v></c>
                      <c r="B1" t="s"><v>1</v></c>
                      <c r="C1" t="s"><v>2</v></c>
                      <c r="D1" t="s"><v>3</v></c>
                      <c r="E1" t="s"><v>4</v></c>
                    </row>
                    <row r="2">
                      <c r="A2" t="s"><v>5</v></c>
                      <c r="B2" t="s"><v>6</v></c>
                      <c r="C2" t="s"><v>7</v></c>
                      <c r="D2" t="s"><v>8</v></c>
                      <c r="E2" t="s"><v>9</v></c>
                    </row>
                  </sheetData>
                </worksheet>""",
        }
    )


def test_faa_source_metadata_includes_public_safety_caveat() -> None:
    assert "FAA AIS" in faa.FAA_SOURCES
    assert "informational" in faa.PUBLIC_AVIATION_DISCLAIMER.lower()
    assert faa.FAA_SOURCES["FAA Aircraft Registry"]["auth"] == "none"


def test_arcgis_query_params_include_bbox_limit_and_fields() -> None:
    params = faa.build_arcgis_query_params(
        where="STATE = 'CA'",
        out_fields=["IDENT", "NAME"],
        limit=5,
        bbox=(-119.0, 33.0, -117.0, 35.0),
    )

    assert params["f"] == "json"
    assert params["where"] == "STATE = 'CA'"
    assert params["outFields"] == "IDENT,NAME"
    assert params["resultRecordCount"] == 5
    assert params["returnGeometry"] == "true"
    assert params["geometryType"] == "esriGeometryEnvelope"
    assert '"xmin": -119.0' in params["geometry"]


def test_search_faa_airports_prefers_exact_identifier(monkeypatch) -> None:
    calls = []

    async def fake_query_arcgis(service, *, where="1=1", out_fields=None, limit=10, **kwargs):
        calls.append((service, where, out_fields, limit, kwargs))
        return {
            "features": [
                {
                    "attributes": {
                        "IDENT": "LAX",
                        "ICAO_ID": "KLAX",
                        "NAME": "Los Angeles Intl",
                        "SERVCITY": "LOS ANGELES",
                        "STATE": "CA",
                    }
                }
            ]
        }

    monkeypatch.setattr(faa, "_query_arcgis", fake_query_arcgis)

    output = asyncio.run(faa.search_faa_airports(query="LAX", limit=1))

    assert "Los Angeles Intl" in output
    assert len(calls) == 1
    assert "IDENT = 'LAX'" in calls[0][1]


def test_get_faa_runways_resolves_airport_global_id(monkeypatch) -> None:
    calls = []

    async def fake_query_arcgis(service, *, where="1=1", out_fields=None, limit=10, **kwargs):
        calls.append((service, where, out_fields, limit, kwargs))
        if service == "airports":
            return {
                "features": [
                    {"attributes": {"IDENT": "LAX", "ICAO_ID": "KLAX", "GLOBAL_ID": "airport-guid"}}
                ]
            }
        return {
            "features": [
                {
                    "attributes": {
                        "AIRPORT_ID": "airport-guid",
                        "DESIGNATOR": "06L/24R",
                        "LENGTH": 8925,
                        "WIDTH": 150,
                        "DIM_UOM": "FT",
                        "COMP_CODE": "CONC",
                    }
                }
            ]
        }

    monkeypatch.setattr(faa, "_query_arcgis", fake_query_arcgis)

    output = asyncio.run(faa.get_faa_runways("LAX", limit=2))

    assert "06L/24R" in output
    assert calls[0][0] == "airports"
    assert calls[1][0] == "runways"
    assert calls[1][1] == "AIRPORT_ID = 'airport-guid'"


def test_tfr_helpers_filter_state_and_parse_detail_xml() -> None:
    records = [
        {
            "notam_id": "6/2842",
            "facility": "ZDC",
            "state": "VA",
            "type": "VIP",
            "description": "MIDDLEBURG, VA",
            "mod_date": "07/04/2026 02:31:00",
        },
        {
            "notam_id": "6/2828",
            "facility": "ZBW",
            "state": "MA",
            "type": "SECURITY",
            "description": "Boston, MA",
        },
    ]

    output = faa.format_tfr_list(records, state="va", limit=5)

    assert "6/2842" in output
    assert "MIDDLEBURG" in output
    assert "6/2828" not in output
    assert "verify official FAA" in output
    assert faa.tfr_detail_url("6/2842").endswith("/download/detail_6_2842.xml")

    parsed = faa.parse_tfr_detail_xml(
        "<XNOTAM><notam_id>6/2842</notam_id><title>VIP movement</title></XNOTAM>"
    )
    assert parsed == {"notam_id": "6/2842", "title": "VIP movement"}


def test_nas_airport_event_formatter_filters_and_summarizes_events() -> None:
    events = [
        {
            "airportId": "DCA",
            "airportLongName": "Ronald Reagan Washington National",
            "groundDelay": {
                "avgDelay": 35,
                "maxDelay": 55,
                "impactingCondition": "air show",
            },
            "airportClosure": {"simpleText": "!DCA AD AP CLSD"},
            "arrivalDelay": None,
            "departureDelay": None,
        },
        {"airportId": "EWR", "freeForm": {"simpleText": "EWR notice"}},
    ]

    output = faa.format_nas_airport_events(events, airport="dca")

    assert "DCA" in output
    assert "Ground Delay" in output
    assert "air show" in output
    assert "Airport Closure" in output
    assert "EWR" not in output


def test_registry_zip_parser_normalizes_n_numbers_and_joins_reference() -> None:
    zip_data = _zip_bytes(
        {
            "MASTER.txt": (
                "N-NUMBER,NAME,MFR MDL CODE,SERIAL NUMBER,STATE,STATUS CODE\n"
                "23FX,DOE AVIATION LLC,0563361,1234,TX,V\n"
            ),
            "ACFTREF.txt": "CODE,MFR,MODEL,TYPE-ACFT,TYPE-ENG\n0563361,CIRRUS DESIGN CORP,SR22,4,1\n",
        }
    )

    registry = faa.parse_aircraft_registry_zip(zip_data)
    record = faa.lookup_aircraft_registration_record(registry, "N23FX")
    matches = faa.search_aircraft_registry_records(registry, make="cirrus", limit=5)

    assert record is not None
    assert record["n_number"] == "N23FX"
    assert record["manufacturer"] == "CIRRUS DESIGN CORP"
    assert record["model"] == "SR22"
    assert matches == [record]


def test_aircraft_characteristics_xlsx_parser_normalizes_rows() -> None:
    rows = faa.read_xlsx_rows(_minimal_xlsx())
    records = faa.parse_aircraft_characteristics_rows(rows)

    assert records == [
        {
            "icao_code": "B738",
            "manufacturer": "BOEING",
            "model": "737-800",
            "wingspan_ft": "117.5",
            "approach_category": "C",
        }
    ]
    assert faa.find_aircraft_characteristics(records, "b738") == records[0]


def test_aircraft_characteristics_parser_maps_live_faa_headers() -> None:
    rows = [
        [
            "ICAO_Code",
            "FAA_Designator",
            "Manufacturer",
            "Model_FAA",
            "AAC",
            "Wingspan_ft_without_winglets_sharklets",
            "Wingspan_ft_with_winglets_sharklets",
        ],
        ["B738", "B738", "BOEING", "Boeing 737-800", "D", "112.6", "117.4"],
    ]

    records = faa.parse_aircraft_characteristics_rows(rows)

    assert records[0]["icao_code"] == "B738"
    assert records[0]["model"] == "Boeing 737-800"
    assert records[0]["wingspan_ft"] == "117.4"
    assert records[0]["approach_category"] == "D"


def test_faa_catalog_formatter_reports_count_and_resources() -> None:
    data = {
        "result": {
            "count": 1,
            "results": [
                {
                    "title": "FAA Chart Supplements",
                    "notes": "Airport and facility directory data.",
                    "metadata_modified": "2026-07-01T00:00:00",
                    "resources": [{"format": "PDF", "url": "https://example.test/chart.pdf"}],
                }
            ],
        }
    }

    output = faa.format_faa_catalog_results(data, query="chart", rows=10)

    assert "FAA Chart Supplements" in output
    assert "Found 1 datasets" in output
    assert "PDF" in output
    assert "https://example.test/chart.pdf" in output
