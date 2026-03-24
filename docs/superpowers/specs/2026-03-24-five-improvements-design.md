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

- All `from mcp_govt_api` imports across every `.py` file
- `pyproject.toml`: `name`, `[project.scripts]` entry point, `[tool.hatch.build.targets.wheel]` packages path
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

### TTLs applied at call sites

| Source | TTL |
|---|---|
| NOAA weather forecast | 3600s |
| NOAA weather alerts | 300s |
| OpenWeather current | 600s |
| NOAA GOES imagery | 300s |
| Census data | 86400s |
| World Bank indicators | 86400s |
| Data.gov search | 3600s |
| EU Open Data | 3600s |
| Safecast radiation | 3600s |
| OpenAQ air quality | 3600s |
| USGS water | 600s |
| USGS earthquakes | 600s |
| NASA FIRMS wildfires | 600s |
| NOAA space weather | 300s |
| RSOE-EDIS disasters | 300s |

---

## 3. MCP Resources

### New file: `src/mcp_civic_data/resources/reference.py`

Three resources registered with `@mcp.resource(uri)`:

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
- Validates `sources` list; returns error string listing valid options if unknown source provided
- Fans out to selected sources in parallel via `asyncio.gather(..., return_exceptions=True)`
- Each source is a private async helper (e.g. `_fetch_earthquakes`, `_fetch_wildfires`) that calls `fetch_json` directly — not wrapping the existing MCP tools
- Failed sources are noted inline ("earthquakes: unavailable") rather than failing the whole call
- Returns unified markdown with a `## Source Name` section per source

**Coordinate filtering:**
- Earthquakes: USGS bbox derived from lat/lon ± radius approximation
- Wildfires: NASA FIRMS uses a bounding box param
- Weather alerts: NOAA alerts API doesn't support radius — query by nearest point and note this limitation
- Air quality: OpenAQ `coordinates` + `radius` params (supports km radius natively)
- Space weather: global, not location-filtered — returned as-is with a note

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
