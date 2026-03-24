# Design: Five Improvements to mcp-civic-data

**Date:** 2026-03-24
**Status:** Approved

---

## Overview

Five targeted improvements to the `mcp-civic-data` MCP server:

1. Package rename (`mcp_govt_api` → `mcp_civic_data`)
2. In-memory response caching with per-source TTLs
3. MCP Resources for reference data (Census variables, NOAA zones, earthquake regions)
4. Test suite with `respx` HTTP mocking
5. Unified `get_hazards_near` tool with caller-specified sources

---

## 1. Package Rename

Rename `src/mcp_govt_api/` → `src/mcp_civic_data/` and update all references:

- All `from mcp_govt_api` imports across every `.py` file, including `__main__.py`
- `pyproject.toml`: `[project.scripts]` entry point and `[tool.hatch.build.targets.wheel]` packages path (the `name` field is already `mcp-civic-data` — no change needed)
- `[tool.mypy]` has no package references to change

The CLI entry point becomes:
```toml
mcp-civic-data = "mcp_civic_data:main"
```

---

## 2. In-Memory Response Cache

### New file: `src/mcp_civic_data/utils/cache.py`

A `SimpleCache` class backed by a plain dict:

```python
@dataclass
class CacheEntry:
    data: Any
    expires_at: float  # time.monotonic()

class SimpleCache:
    def get(self, key) -> Any | None
    def set(self, key, data, ttl_seconds: int)
    def make_key(self, url: str, params: dict | None) -> tuple
```

A module-level `cache = SimpleCache()` instance is used by the HTTP layer.

### Changes to `utils/http.py`

Add optional `ttl_seconds: int | None = None` parameter to `fetch_json` and `fetch_text`. When set, check the cache before making the request and populate on miss.

### Special case: `tools/firms.py`

`firms.py` uses a private `_fetch_firms_csv` function that creates its own `httpx.AsyncClient` and returns CSV text — it does not use `fetch_json` or `fetch_text`. Caching for FIRMS must be added directly inside `_fetch_firms_csv` using the shared `cache` instance from `utils/cache.py`, with a 600s TTL.

### TTLs applied at call sites

| Source | TTL | Via |
|---|---|---|
| NOAA weather forecast | 3600s | `fetch_json` |
| NOAA weather alerts | 300s | `fetch_json` |
| OpenWeather current | 600s | `fetch_json` |
| NOAA GOES imagery | 300s | `fetch_json` |
| Census data | 86400s | `fetch_json` |
| World Bank indicators | 86400s | `fetch_json` |
| Data.gov search | 3600s | `fetch_json` |
| EU Open Data | 3600s | `fetch_json` |
| Safecast radiation | 3600s | `fetch_json` |
| OpenAQ air quality | 3600s | `fetch_json` |
| USGS water | 600s | `fetch_json` |
| USGS earthquakes | 600s | `fetch_json` |
| NASA FIRMS wildfires | 600s | `_fetch_firms_csv` directly |
| NOAA space weather | 300s | `fetch_json` |
| RSOE-EDIS disasters | 300s | `fetch_text` |

---

## 3. MCP Resources

### New files: `src/mcp_civic_data/resources/__init__.py` and `src/mcp_civic_data/resources/reference.py`

`resources/__init__.py` is an empty package marker. `reference.py` contains three resources registered with `@mcp.resource(uri)`:

**`civic-data://census/variables`**
- Fetches the ACS5 variable catalog: `https://api.census.gov/data/2022/acs/acs5/variables.json`
- Returns a formatted list of variable codes and labels (top 200 most useful, filtered to exclude MOE entries)

**`civic-data://noaa/alert-zones`**
- Fetches `https://api.weather.gov/zones?type=public`
- Returns a list of zone IDs and names grouped by state

**`civic-data://usgs/earthquake-regions`**
- Fetches `https://earthquake.usgs.gov/fdsnws/event/1/catalogs`
- Returns available catalog and contributor identifiers

Resources import the shared `fetch_json` from `utils/http.py` (no caching — reference reads are infrequent).

### Registration in `server.py`

```python
from mcp_civic_data.resources import reference  # noqa: E402, F401
```

---

## 4. Test Suite

### New dev dependency: `respx>=0.21`

Add to `[dependency-groups] dev` in `pyproject.toml`.

### Test files

```
tests/
  conftest.py          # shared fixtures: mock HTTP client, sample responses
  test_cache.py        # TTL expiry, cache hit, cache miss, key collision
  test_weather.py      # get_weather_forecast, get_weather_alerts, get_global_weather
  test_census.py       # search_census_data
  test_nasa.py         # get_apod, get_mars_photos
  test_economics.py    # get_country_indicators
  test_earthquakes.py  # get_recent_earthquakes
  test_openaq.py       # get_air_quality
  test_usgs_water.py   # get_stream_flow
  test_hazards.py      # get_hazards_near with various source combinations
```

### Test approach

Each tool test:
1. Uses `respx.mock` as a context manager to intercept `httpx` calls
2. Provides a minimal but realistic fixture response
3. Calls the tool function directly (not via MCP protocol)
4. Asserts the returned string contains expected content

`test_cache.py` uses `time.monotonic` patching to simulate TTL expiry without sleeping.

---

## 5. Unified Hazard Query

### New file: `src/mcp_civic_data/tools/hazards.py`

```python
@mcp.tool()
async def get_hazards_near(
    latitude: float,
    longitude: float,
    radius_km: float,
    sources: list[str],
) -> str
```

**Valid sources:** `earthquakes`, `wildfires`, `weather_alerts`, `air_quality`, `space_weather`

**Behavior:**
- Validates `sources` list **before** `asyncio.gather` runs; if any unknown source is provided, returns immediately with an error string listing valid options (no partial results)
- Fans out to selected valid sources in parallel via `asyncio.gather(..., return_exceptions=True)`
- Each source is a private async helper that queries the underlying API directly — not wrapping the existing MCP tools
- Failed sources are noted inline ("earthquakes: unavailable") rather than failing the whole call
- Returns unified markdown with a `## Source Name` section per source

**Per-source fetch approach:**
- `_fetch_earthquakes`: calls `fetch_json` against USGS bbox endpoint
- `_fetch_wildfires`: calls `fetch_text` against the NASA FIRMS CSV endpoint, then parses the CSV response (same approach as `firms.py`'s `_fetch_firms_csv`) — does NOT use `fetch_json` since FIRMS returns CSV
- `_fetch_weather_alerts`: calls `fetch_json` against `https://api.weather.gov/alerts/active?point={lat},{lon}` — NOAA supports point-based alert queries even though it doesn't support radius; response covers the zone containing the point; result notes this limitation
- `_fetch_air_quality`: calls `fetch_json` against OpenAQ with `coordinates={lat},{lon}&radius={radius_m}` (OpenAQ accepts meters)
- `_fetch_space_weather`: calls `fetch_json` for solar wind/flare data — global feed, radius ignored; result notes this

**Coordinate filtering:**
- Earthquakes: USGS bbox derived from lat/lon ± radius approximation (degrees)
- Wildfires: NASA FIRMS bounding box param derived from lat/lon ± radius approximation
- Weather alerts: `?point=lat,lon` on NOAA `/alerts/active` — zone-level, not radius-based
- Air quality: OpenAQ native `radius` param (convert km → meters)
- Space weather: global, not location-filtered

### Registration in `server.py`

```python
from mcp_civic_data.tools import hazards  # noqa: E402, F401
```

---

## File Changes Summary

### New files
- `src/mcp_civic_data/utils/cache.py`
- `src/mcp_civic_data/resources/__init__.py`
- `src/mcp_civic_data/resources/reference.py`
- `src/mcp_civic_data/tools/hazards.py`
- `tests/conftest.py`
- `tests/test_cache.py`
- `tests/test_weather.py`
- `tests/test_census.py`
- `tests/test_nasa.py`
- `tests/test_economics.py`
- `tests/test_earthquakes.py`
- `tests/test_openaq.py`
- `tests/test_usgs_water.py`
- `tests/test_hazards.py`

### Modified files
- `src/mcp_govt_api/` → `src/mcp_civic_data/` (rename entire directory)
- All `.py` files: update imports
- `pyproject.toml`: name, entry point, build target, add `respx` dev dep
- `src/mcp_civic_data/utils/http.py`: add `ttl_seconds` param + cache integration
- `src/mcp_civic_data/server.py`: add resources import
- All tool files: add `ttl_seconds` to `fetch_json`/`fetch_text` calls
