# Five Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the package, add in-memory caching, add MCP Resources for reference data, build a test suite, and add a unified hazard query tool.

**Architecture:** Package rename first (all other tasks depend on it), then cache infrastructure (needed by tools), then TTLs applied to call sites, then tests added to existing tools, then new MCP Resources and hazard tool both developed TDD.

**Tech Stack:** Python 3.11+, FastMCP, httpx, respx (new dev dep), pytest, standard library only for cache

**Spec:** `docs/superpowers/specs/2026-03-24-five-improvements-design.md`

---

## File Map

### Modified
- `pyproject.toml` — entry point `mcp_civic_data:main`, build target `src/mcp_civic_data`, add `respx>=0.21` dev dep
- `src/mcp_civic_data/utils/http.py` — add `ttl_seconds` param + cache integration to `fetch_json` and `fetch_text`
- `src/mcp_civic_data/tools/firms.py` — add cache directly inside `_fetch_firms_csv`
- All other tool files — add `ttl_seconds=N` to every `fetch_json`/`fetch_text` call
- `src/mcp_civic_data/server.py` — add resources import

### Created
- `src/mcp_civic_data/utils/cache.py` — `SimpleCache` class + module-level `cache` instance
- `src/mcp_civic_data/resources/__init__.py` — empty package marker
- `src/mcp_civic_data/resources/reference.py` — three MCP resources (census vars, NOAA zones, earthquake regions)
- `src/mcp_civic_data/tools/hazards.py` — `get_hazards_near` tool
- `tests/conftest.py` — shared pytest fixtures
- `tests/test_cache.py` — cache unit tests
- `tests/test_weather.py` — weather tool tests
- `tests/test_census.py` — census tool test
- `tests/test_nasa.py` — NASA tool tests
- `tests/test_economics.py` — World Bank tool test
- `tests/test_earthquakes.py` — earthquake tool test
- `tests/test_openaq.py` — air quality tool test
- `tests/test_usgs_water.py` — USGS water tool test
- `tests/test_hazards.py` — hazard tool tests

---

## Task 1: Package Rename

**Files:**
- Rename: `src/mcp_govt_api/` → `src/mcp_civic_data/`
- Modify: `pyproject.toml`

- [ ] **Step 1: Rename the package directory**

```bash
git mv src/mcp_govt_api src/mcp_civic_data
```

- [ ] **Step 2: Replace all import references in Python files**

```bash
find src/mcp_civic_data -name "*.py" -exec sed -i '' 's/mcp_govt_api/mcp_civic_data/g' {} +
```

- [ ] **Step 3: Update `pyproject.toml`**

Replace these two lines (the `name` field is already correct):

```toml
# Before:
mcp-civic-data = "mcp_govt_api:main"
packages = ["src/mcp_govt_api"]

# After:
mcp-civic-data = "mcp_civic_data:main"
packages = ["src/mcp_civic_data"]
```

- [ ] **Step 4: Verify the server starts without import errors**

```bash
cd /Users/eric/code/mcp-civic-data
uv run python -c "from mcp_civic_data import main; print('OK')"
```

Expected: `OK` printed (plus API availability summary lines).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: rename package mcp_govt_api -> mcp_civic_data"
```

---

## Task 2: Write Failing Cache Tests

**Files:**
- Create: `tests/test_cache.py`

- [ ] **Step 1: Create the test file**

```python
# tests/test_cache.py
from unittest.mock import patch
import pytest
from mcp_civic_data.utils.cache import SimpleCache


def test_cache_miss_returns_none():
    c = SimpleCache()
    assert c.get(("http://example.com",)) is None


def test_cache_hit_returns_data():
    c = SimpleCache()
    key = c.make_key("http://example.com", None)
    c.set(key, {"foo": "bar"}, ttl_seconds=60)
    assert c.get(key) == {"foo": "bar"}


def test_cache_expired_returns_none():
    c = SimpleCache()
    key = c.make_key("http://example.com", None)
    # Set with TTL=1, then advance time past expiry
    with patch("mcp_civic_data.utils.cache.time") as mock_time:
        mock_time.monotonic.return_value = 1000.0
        c.set(key, {"foo": "bar"}, ttl_seconds=1)
        mock_time.monotonic.return_value = 1002.0
        assert c.get(key) is None


def test_cache_key_includes_params():
    c = SimpleCache()
    key1 = c.make_key("http://example.com", {"a": "1"})
    key2 = c.make_key("http://example.com", {"a": "2"})
    assert key1 != key2


def test_cache_key_param_order_independent():
    c = SimpleCache()
    key1 = c.make_key("http://example.com", {"a": "1", "b": "2"})
    key2 = c.make_key("http://example.com", {"b": "2", "a": "1"})
    assert key1 == key2


def test_cache_clears_expired_on_read():
    c = SimpleCache()
    key = c.make_key("http://example.com", None)
    with patch("mcp_civic_data.utils.cache.time") as mock_time:
        mock_time.monotonic.return_value = 1000.0
        c.set(key, "data", ttl_seconds=10)
        assert len(c._store) == 1
        mock_time.monotonic.return_value = 1011.0
        c.get(key)  # triggers cleanup
        assert len(c._store) == 0
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /Users/eric/code/mcp-civic-data
uv run pytest tests/test_cache.py -v
```

Expected: `ModuleNotFoundError: No module named 'mcp_civic_data.utils.cache'`

---

## Task 3: Implement SimpleCache

**Files:**
- Create: `src/mcp_civic_data/utils/cache.py`

- [ ] **Step 1: Create the cache module**

```python
# src/mcp_civic_data/utils/cache.py
import time
from typing import Any


class _CacheEntry:
    __slots__ = ("data", "expires_at")

    def __init__(self, data: Any, expires_at: float) -> None:
        self.data = data
        self.expires_at = expires_at


class SimpleCache:
    def __init__(self) -> None:
        self._store: dict[tuple, _CacheEntry] = {}

    def make_key(self, url: str, params: dict | None) -> tuple:
        if params is None:
            return (url,)
        return (url, tuple(sorted(params.items())))

    def get(self, key: tuple) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() >= entry.expires_at:
            del self._store[key]
            return None
        return entry.data

    def set(self, key: tuple, data: Any, ttl_seconds: int) -> None:
        self._store[key] = _CacheEntry(
            data=data,
            expires_at=time.monotonic() + ttl_seconds,
        )


cache = SimpleCache()
```

- [ ] **Step 2: Run tests to confirm they pass**

```bash
uv run pytest tests/test_cache.py -v
```

Expected: 6 tests pass.

- [ ] **Step 3: Commit**

```bash
git add src/mcp_civic_data/utils/cache.py tests/test_cache.py
git commit -m "feat: add SimpleCache with TTL expiry"
```

---

## Task 4: Integrate Cache into `http.py`

**Files:**
- Modify: `src/mcp_civic_data/utils/http.py`

- [ ] **Step 1: Update `http.py` to support optional caching**

Replace the full contents of `src/mcp_civic_data/utils/http.py`:

```python
import httpx
from typing import Any

from mcp_civic_data.utils.cache import cache
from mcp_civic_data.utils.config import config


http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(config.timeout),
    follow_redirects=True,
    headers={"User-Agent": "mcp-civic-data/0.1.0"},
)


async def fetch_json(
    url: str,
    params: dict[str, Any] | None = None,
    ttl_seconds: int | None = None,
) -> dict[str, Any]:
    """Fetch JSON from a URL with error handling and optional caching."""
    if ttl_seconds is not None:
        key = cache.make_key(url, params)
        cached = cache.get(key)
        if cached is not None:
            return cached

    try:
        response = await http_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except httpx.TimeoutException:
        raise Exception(f"Request timed out after {config.timeout}s: {url}")
    except httpx.HTTPStatusError as e:
        raise Exception(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
    except httpx.RequestError as e:
        raise Exception(f"Request failed: {e}")

    if ttl_seconds is not None:
        cache.set(key, data, ttl_seconds)
    return data


async def fetch_text(
    url: str,
    params: dict[str, Any] | None = None,
    ttl_seconds: int | None = None,
) -> str:
    """Fetch text from a URL with error handling and optional caching."""
    if ttl_seconds is not None:
        key = cache.make_key(url, params)
        cached = cache.get(key)
        if cached is not None:
            return cached

    try:
        response = await http_client.get(url, params=params)
        response.raise_for_status()
        data = response.text
    except httpx.TimeoutException:
        raise Exception(f"Request timed out after {config.timeout}s: {url}")
    except httpx.HTTPStatusError as e:
        raise Exception(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
    except httpx.RequestError as e:
        raise Exception(f"Request failed: {e}")

    if ttl_seconds is not None:
        cache.set(key, data, ttl_seconds)
    return data
```

- [ ] **Step 2: Verify existing tests still pass**

```bash
uv run pytest tests/test_cache.py -v
```

Expected: 6 pass.

- [ ] **Step 3: Commit**

```bash
git add src/mcp_civic_data/utils/http.py
git commit -m "feat: add ttl_seconds caching support to fetch_json and fetch_text"
```

---

## Task 5: Apply TTLs to All Tool Call Sites

**Files:**
- Modify: all tool files in `src/mcp_civic_data/tools/` except `firms.py` (handled in Task 6)

Add `ttl_seconds=N` to every `fetch_json` and `fetch_text` call according to this table:

| File | TTL |
|---|---|
| `weather.py` (NOAA forecast) | 3600 |
| `weather.py` (NOAA alerts) | 300 |
| `weather.py` (OpenWeather) | 600 |
| `noaa_goes_imagery.py` | 300 |
| `census.py` | 86400 |
| `economics.py` | 86400 |
| `datagov.py` | 3600 |
| `eu_data.py` | 3600 |
| `safecast.py` | 3600 |
| `openaq.py` | 3600 |
| `usgs_water.py` | 600 |
| `earthquakes.py` | 600 |
| `space_weather.py` | 300 |
| `rsoe_edis.py` | 300 |

- [ ] **Step 1: Update each tool file**

For each `fetch_json(url, ...)` or `fetch_text(url, ...)` call in the above files, add the `ttl_seconds` keyword argument. Example for `weather.py`:

```python
# Before:
points_data = await fetch_json(points_url)
forecast_data = await fetch_json(forecast_url)

# After:
points_data = await fetch_json(points_url, ttl_seconds=3600)
forecast_data = await fetch_json(forecast_url, ttl_seconds=3600)
```

```python
# Before (alerts):
data = await fetch_json(url, params={"area": state})

# After:
data = await fetch_json(url, params={"area": state}, ttl_seconds=300)
```

Note: `query_noaa`, `query_openweather`, `query_openaq`, `query_earthquakes` and other raw passthrough tools should NOT get TTLs — they're for ad-hoc queries where caching would be confusing.

- [ ] **Step 2: Verify the server still imports cleanly**

```bash
uv run python -c "from mcp_civic_data import main; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/mcp_civic_data/tools/
git commit -m "feat: apply cache TTLs to all tool call sites"
```

---

## Task 6: Add Cache to `firms.py`

**Files:**
- Modify: `src/mcp_civic_data/tools/firms.py`

`firms.py` uses its own `httpx.AsyncClient` (not `fetch_json`), so caching must be wired in directly.

- [ ] **Step 1: Add cache import and TTL logic to `_fetch_firms_csv`**

Add the import at the top of the file:

```python
from mcp_civic_data.utils.cache import cache
```

Replace `_fetch_firms_csv`:

```python
_FIRMS_TTL = 600  # 10 minutes


async def _fetch_firms_csv(url: str) -> list[dict[str, str]]:
    """Fetch and parse a CSV response from the FIRMS API (with caching)."""
    key = cache.make_key(url, None)
    cached = cache.get(key)
    if cached is not None:
        return cached

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

    rows = list(csv.DictReader(io.StringIO(response.text)))
    cache.set(key, rows, _FIRMS_TTL)
    return rows
```

- [ ] **Step 2: Verify import**

```bash
uv run python -c "from mcp_civic_data.tools import firms; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add src/mcp_civic_data/tools/firms.py
git commit -m "feat: add cache to FIRMS CSV fetch"
```

---

## Task 7: Add respx + conftest

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/conftest.py`

- [ ] **Step 1: Add respx to dev dependencies in `pyproject.toml`**

```toml
[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "respx>=0.21",
    "ruff>=0.6.0",
    "mypy>=1.10.0",
]
```

Also add pytest-asyncio config so async tests run without per-test decorators:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 2: Install dev dependencies**

```bash
uv sync --group dev
```

- [ ] **Step 3: Create `tests/conftest.py`**

```python
# tests/conftest.py
import pytest
from mcp_civic_data.utils.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Reset the shared cache before each test."""
    cache._store.clear()
    yield
    cache._store.clear()
```

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock tests/conftest.py
git commit -m "chore: add respx, pytest-asyncio, and test conftest"
```

---

## Task 8: Weather Tool Tests

**Files:**
- Create: `tests/test_weather.py`

- [ ] **Step 1: Create the test file**

```python
# tests/test_weather.py
import respx
import httpx
import pytest
from mcp_civic_data.tools.weather import (
    get_weather_forecast,
    get_weather_alerts,
    get_global_weather,
)


POINTS_RESPONSE = {
    "properties": {
        "forecast": "https://api.weather.gov/gridpoints/LWX/96,70/forecast"
    }
}

FORECAST_RESPONSE = {
    "properties": {
        "periods": [
            {
                "name": "Tonight",
                "detailedForecast": "Clear skies. Low around 55.",
            },
            {
                "name": "Monday",
                "detailedForecast": "Sunny. High near 72.",
            },
        ]
    }
}

ALERTS_RESPONSE = {
    "features": [
        {
            "properties": {
                "event": "Frost Advisory",
                "severity": "Minor",
                "areaDesc": "Northern Virginia",
                "headline": "Frost Advisory in effect until 9 AM EDT",
            }
        }
    ]
}

OPENWEATHER_RESPONSE = {
    "name": "London",
    "sys": {"country": "GB"},
    "weather": [{"description": "light rain"}],
    "main": {"temp": 12.0, "feels_like": 10.0, "humidity": 85, "pressure": 1012},
    "wind": {"speed": 4.5},
}


@respx.mock
async def test_get_weather_forecast():
    respx.get("https://api.weather.gov/points/38.8894,-77.0352").mock(
        return_value=httpx.Response(200, json=POINTS_RESPONSE)
    )
    respx.get("https://api.weather.gov/gridpoints/LWX/96,70/forecast").mock(
        return_value=httpx.Response(200, json=FORECAST_RESPONSE)
    )
    result = await get_weather_forecast(38.8894, -77.0352)
    assert "Tonight" in result
    assert "Monday" in result


@respx.mock
async def test_get_weather_alerts():
    respx.get("https://api.weather.gov/alerts/active").mock(
        return_value=httpx.Response(200, json=ALERTS_RESPONSE)
    )
    result = await get_weather_alerts("VA")
    assert "Frost Advisory" in result
    assert "Minor" in result


@respx.mock
async def test_get_weather_alerts_none():
    respx.get("https://api.weather.gov/alerts/active").mock(
        return_value=httpx.Response(200, json={"features": []})
    )
    result = await get_weather_alerts("WY")
    assert "No active weather alerts" in result


@respx.mock
async def test_get_global_weather(monkeypatch):
    from mcp_civic_data.utils import config as cfg
    monkeypatch.setattr(cfg.config, "openweather_api_key", "test-key")
    respx.get("https://api.openweathermap.org/data/2.5/weather").mock(
        return_value=httpx.Response(200, json=OPENWEATHER_RESPONSE)
    )
    result = await get_global_weather("London", "GB")
    assert "London" in result
    assert "light rain" in result


async def test_get_global_weather_no_key():
    result = await get_global_weather("London")
    assert "OPENWEATHER_API_KEY" in result
```

- [ ] **Step 2: Run tests**

```bash
uv run pytest tests/test_weather.py -v
```

Expected: 5 tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/test_weather.py
git commit -m "test: add weather tool tests"
```

---

## Task 9: Census, NASA, and Economics Tests

**Files:**
- Create: `tests/test_census.py`, `tests/test_nasa.py`, `tests/test_economics.py`

- [ ] **Step 1: Create `tests/test_census.py`**

```python
# tests/test_census.py
import re
import respx
import httpx
from mcp_civic_data.tools.census import get_population


@respx.mock
async def test_get_population():
    # Census API embeds query params in the URL string (not as a params dict),
    # so match with a regex pattern rather than an exact URL.
    respx.get(re.compile(r"https://api\.census\.gov/data/2022/acs/acs5")).mock(
        return_value=httpx.Response(200, json=[
            ["NAME", "B01003_001E", "state"],
            ["California", "39538223", "06"],
        ])
    )
    result = await get_population("CA")
    assert "California" in result or "39538223" in result or "CA" in result
```

- [ ] **Step 2: Create `tests/test_nasa.py`**

```python
# tests/test_nasa.py
import respx
import httpx
from mcp_civic_data.tools.nasa import get_astronomy_photo


APOD_RESPONSE = {
    "title": "Pillars of Creation",
    "date": "2024-01-15",
    "explanation": "Eagle Nebula region.",
    "url": "https://apod.nasa.gov/apod/image/2401/pillars.jpg",
    "media_type": "image",
}


@respx.mock
async def test_get_astronomy_photo():
    respx.get("https://api.nasa.gov/planetary/apod").mock(
        return_value=httpx.Response(200, json=APOD_RESPONSE)
    )
    result = await get_astronomy_photo()
    assert "Pillars of Creation" in result
    assert "2024-01-15" in result
```

- [ ] **Step 3: Create `tests/test_economics.py`**

```python
# tests/test_economics.py
import respx
import httpx
from mcp_civic_data.tools.economics import get_country_indicators


WB_RESPONSE = [
    {"page": 1, "pages": 1, "per_page": 5, "total": 1},
    [
        {
            "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
            "country": {"id": "DE", "value": "Germany"},
            "date": "2022",
            "value": 4072191714000.0,
        }
    ],
]


@respx.mock
async def test_get_country_indicators():
    # Pass a single indicator to avoid mocking all 4 default World Bank calls
    respx.get(
        "https://api.worldbank.org/v2/country/DE/indicator/NY.GDP.MKTP.CD"
    ).mock(return_value=httpx.Response(200, json=WB_RESPONSE))
    result = await get_country_indicators("DE", indicators=["NY.GDP.MKTP.CD"])
    assert "Germany" in result or "GDP" in result
```

- [ ] **Step 4: Run all three**

```bash
uv run pytest tests/test_census.py tests/test_nasa.py tests/test_economics.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_census.py tests/test_nasa.py tests/test_economics.py
git commit -m "test: add census, NASA, and economics tool tests"
```

---

## Task 10: Earthquakes, OpenAQ, and USGS Water Tests

**Files:**
- Create: `tests/test_earthquakes.py`, `tests/test_openaq.py`, `tests/test_usgs_water.py`

- [ ] **Step 1: Create `tests/test_earthquakes.py`**

```python
# tests/test_earthquakes.py
import respx
import httpx
from mcp_civic_data.tools.earthquakes import get_recent_earthquakes


EQ_RESPONSE = {
    "metadata": {"count": 1},
    "features": [
        {
            "properties": {
                "mag": 5.2,
                "place": "15 km NW of Ridgecrest, CA",
                "time": 1705000000000,
                "tsunami": 0,
                "alert": None,
                "url": "https://earthquake.usgs.gov/earthquakes/eventpage/test",
            },
            "geometry": {"coordinates": [-117.7, 35.6, 8.5]},
        }
    ],
}


@respx.mock
async def test_get_recent_earthquakes():
    respx.get("https://earthquake.usgs.gov/fdsnws/event/1/query").mock(
        return_value=httpx.Response(200, json=EQ_RESPONSE)
    )
    result = await get_recent_earthquakes(min_magnitude=5.0)
    assert "M5.2" in result
    assert "Ridgecrest" in result
```

- [ ] **Step 2: Create `tests/test_openaq.py`**

```python
# tests/test_openaq.py
import respx
import httpx
from mcp_civic_data.tools.openaq import get_air_quality


AQ_RESPONSE = {
    "results": [
        {
            "name": "Central Park Monitor",
            "country": {"code": "US"},
            "distance": 1200,
            "sensors": [
                {
                    "parameter": {
                        "displayName": "PM2.5",
                        "units": "µg/m³",
                    },
                    "latest": {"value": 8.3},
                }
            ],
        }
    ]
}


@respx.mock
async def test_get_air_quality():
    respx.get("https://api.openaq.org/v3/locations").mock(
        return_value=httpx.Response(200, json=AQ_RESPONSE)
    )
    result = await get_air_quality(40.7829, -73.9654)
    assert "PM2.5" in result
    assert "8.3" in result
```

- [ ] **Step 3: Create `tests/test_usgs_water.py`**

```python
# tests/test_usgs_water.py
import respx
import httpx
from mcp_civic_data.tools.usgs_water import get_stream_flow


USGS_RESPONSE = {
    "value": {
        "timeSeries": [
            {
                "sourceInfo": {"siteName": "POTOMAC RIVER AT CHAIN BRIDGE"},
                "variable": {
                    "variableName": "Streamflow, ft&#179;/s",
                    "unit": {"unitCode": "ft3/s"},
                },
                "values": [
                    {"value": [{"value": "12500", "dateTime": "2024-01-15T12:00:00"}]}
                ],
            }
        ]
    }
}


@respx.mock
async def test_get_stream_flow():
    respx.get("https://waterservices.usgs.gov/nwis/iv/").mock(
        return_value=httpx.Response(200, json=USGS_RESPONSE)
    )
    result = await get_stream_flow("01646500")
    assert "POTOMAC" in result or "12500" in result or "01646500" in result
```

- [ ] **Step 4: Run all three**

```bash
uv run pytest tests/test_earthquakes.py tests/test_openaq.py tests/test_usgs_water.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_earthquakes.py tests/test_openaq.py tests/test_usgs_water.py
git commit -m "test: add earthquake, air quality, and USGS water tests"
```

---

## Task 11: Write Failing MCP Resource Tests

**Files:**
- Create: `tests/test_resources.py`

- [ ] **Step 1: Create the test file**

```python
# tests/test_resources.py
import respx
import httpx
import pytest


CENSUS_VARS_RESPONSE = {
    "variables": {
        "B01003_001E": {"label": "Total population", "concept": "Total Population"},
        "B01003_001M": {"label": "Margin of error", "concept": "Total Population"},
        "B19013_001E": {"label": "Median household income", "concept": "Median Income"},
    }
}

NOAA_ZONES_RESPONSE = {
    "features": [
        {
            "properties": {
                "id": "VAZ505",
                "name": "Northern Virginia",
                "state": "VA",
            }
        },
        {
            "properties": {
                "id": "MDZ505",
                "name": "Montgomery County",
                "state": "MD",
            }
        },
    ]
}

USGS_CATALOGS_RESPONSE = {
    "catalogs": ["NEIC PDE", "ISC", "GCMT"],
}


@respx.mock
async def test_census_variables_resource():
    from mcp_civic_data.resources.reference import get_census_variables
    respx.get("https://api.census.gov/data/2022/acs/acs5/variables.json").mock(
        return_value=httpx.Response(200, json=CENSUS_VARS_RESPONSE)
    )
    result = await get_census_variables()
    assert "B01003_001E" in result
    assert "Total population" in result
    # MOE entries should be excluded
    assert "B01003_001M" not in result


@respx.mock
async def test_noaa_alert_zones_resource():
    from mcp_civic_data.resources.reference import get_noaa_alert_zones
    respx.get("https://api.weather.gov/zones", params={"type": "public"}).mock(
        return_value=httpx.Response(200, json=NOAA_ZONES_RESPONSE)
    )
    result = await get_noaa_alert_zones()
    assert "VAZ505" in result
    assert "Northern Virginia" in result


@respx.mock
async def test_earthquake_regions_resource():
    from mcp_civic_data.resources.reference import get_earthquake_regions
    respx.get("https://earthquake.usgs.gov/fdsnws/event/1/catalogs").mock(
        return_value=httpx.Response(200, text="NEIC PDE\nISC\nGCMT\n")
    )
    result = await get_earthquake_regions()
    assert "NEIC PDE" in result or "ISC" in result
```

- [ ] **Step 2: Run to confirm they fail**

```bash
uv run pytest tests/test_resources.py -v
```

Expected: `ModuleNotFoundError: No module named 'mcp_civic_data.resources'`

---

## Task 12: Implement MCP Resources

**Files:**
- Create: `src/mcp_civic_data/resources/__init__.py`
- Create: `src/mcp_civic_data/resources/reference.py`
- Modify: `src/mcp_civic_data/server.py`

- [ ] **Step 1: Create the package marker**

```bash
touch src/mcp_civic_data/resources/__init__.py
```

- [ ] **Step 2: Create `reference.py`**

```python
# src/mcp_civic_data/resources/reference.py
from mcp_civic_data.server import mcp
from mcp_civic_data.utils.http import fetch_json, fetch_text


@mcp.resource("civic-data://census/variables")
async def get_census_variables() -> str:
    """ACS5 variable catalog — codes and labels for Census data queries."""
    data = await fetch_json("https://api.census.gov/data/2022/acs/acs5/variables.json")
    variables = data.get("variables", {})

    lines = ["# Census ACS5 Variable Codes\n"]
    count = 0
    for code, info in variables.items():
        # Skip margin-of-error entries (end in M or MA)
        if code.endswith("M") or code.endswith("MA"):
            continue
        label = info.get("label", "")
        concept = info.get("concept", "")
        lines.append(f"**{code}** — {label}" + (f" ({concept})" if concept else ""))
        count += 1
        if count >= 200:
            break

    return "\n".join(lines)


@mcp.resource("civic-data://noaa/alert-zones")
async def get_noaa_alert_zones() -> str:
    """NOAA public forecast zones — IDs for use in weather alert queries."""
    data = await fetch_json(
        "https://api.weather.gov/zones", params={"type": "public"}
    )
    features = data.get("features", [])

    by_state: dict[str, list[str]] = {}
    for f in features:
        props = f.get("properties", {})
        state = props.get("state", "??")
        zone_id = props.get("id", "")
        name = props.get("name", "")
        by_state.setdefault(state, []).append(f"{zone_id}: {name}")

    lines = ["# NOAA Public Forecast Zones\n"]
    for state in sorted(by_state):
        lines.append(f"\n## {state}")
        lines.extend(by_state[state])

    return "\n".join(lines)


@mcp.resource("civic-data://usgs/earthquake-regions")
async def get_earthquake_regions() -> str:
    """USGS earthquake catalog and contributor identifiers."""
    text = await fetch_text(
        "https://earthquake.usgs.gov/fdsnws/event/1/catalogs"
    )
    lines = ["# USGS Earthquake Catalogs\n"]
    lines.extend(line.strip() for line in text.strip().splitlines() if line.strip())
    return "\n".join(lines)
```

- [ ] **Step 3: Register resources in `server.py`**

Add at the bottom of `src/mcp_civic_data/server.py`:

```python
from mcp_civic_data.resources import reference  # noqa: E402, F401
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_resources.py -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/mcp_civic_data/resources/ src/mcp_civic_data/server.py tests/test_resources.py
git commit -m "feat: add MCP resources for Census variables, NOAA zones, and USGS catalogs"
```

---

## Task 13: Write Failing Hazard Tool Tests

**Files:**
- Create: `tests/test_hazards.py`

- [ ] **Step 1: Create the test file**

```python
# tests/test_hazards.py
import respx
import httpx
import pytest


EQ_RESPONSE = {
    "metadata": {"count": 1},
    "features": [
        {
            "properties": {
                "mag": 3.1,
                "place": "10 km N of Test City",
                "time": 1705000000000,
                "tsunami": 0,
                "alert": None,
                "url": "",
            },
            "geometry": {"coordinates": [-120.0, 37.5, 5.0]},
        }
    ],
}

NOAA_ALERTS_RESPONSE = {
    "features": [
        {
            "properties": {
                "event": "Winter Storm Watch",
                "severity": "Moderate",
                "areaDesc": "Test County",
                "headline": "Winter Storm Watch issued",
            }
        }
    ]
}

AQ_RESPONSE = {
    "results": [
        {
            "name": "Test Station",
            "country": {"code": "US"},
            "distance": 500,
            "sensors": [
                {
                    "parameter": {"displayName": "PM2.5", "units": "µg/m³"},
                    "latest": {"value": 12.0},
                }
            ],
        }
    ]
}


async def test_hazards_invalid_source():
    from mcp_civic_data.tools.hazards import get_hazards_near
    result = await get_hazards_near(37.5, -120.0, 50.0, ["bogus_source"])
    assert "bogus_source" in result
    assert "Valid sources" in result


@respx.mock
async def test_hazards_earthquakes_only():
    from mcp_civic_data.tools.hazards import get_hazards_near
    respx.get("https://earthquake.usgs.gov/fdsnws/event/1/query").mock(
        return_value=httpx.Response(200, json=EQ_RESPONSE)
    )
    result = await get_hazards_near(37.5, -120.0, 100.0, ["earthquakes"])
    assert "Earthquakes" in result
    assert "M3.1" in result


@respx.mock
async def test_hazards_weather_alerts():
    from mcp_civic_data.tools.hazards import get_hazards_near
    respx.get("https://api.weather.gov/alerts/active", params={"point": "37.5,-120.0"}).mock(
        return_value=httpx.Response(200, json=NOAA_ALERTS_RESPONSE)
    )
    result = await get_hazards_near(37.5, -120.0, 50.0, ["weather_alerts"])
    assert "Weather Alerts" in result
    assert "Winter Storm Watch" in result


@respx.mock
async def test_hazards_multiple_sources():
    from mcp_civic_data.tools.hazards import get_hazards_near
    respx.get("https://earthquake.usgs.gov/fdsnws/event/1/query").mock(
        return_value=httpx.Response(200, json=EQ_RESPONSE)
    )
    respx.get("https://api.openaq.org/v3/locations").mock(
        return_value=httpx.Response(200, json=AQ_RESPONSE)
    )
    result = await get_hazards_near(37.5, -120.0, 100.0, ["earthquakes", "air_quality"])
    assert "Earthquakes" in result
    assert "Air Quality" in result


@respx.mock
async def test_hazards_failed_source_noted_inline():
    from mcp_civic_data.tools.hazards import get_hazards_near
    respx.get("https://earthquake.usgs.gov/fdsnws/event/1/query").mock(
        return_value=httpx.Response(500, text="Server error")
    )
    result = await get_hazards_near(37.5, -120.0, 100.0, ["earthquakes"])
    # Should not raise — should note failure inline
    assert "unavailable" in result.lower() or "error" in result.lower()
```

- [ ] **Step 2: Run to confirm failure**

```bash
uv run pytest tests/test_hazards.py -v
```

Expected: `ModuleNotFoundError: No module named 'mcp_civic_data.tools.hazards'`

---

## Task 14: Implement `get_hazards_near`

**Files:**
- Create: `src/mcp_civic_data/tools/hazards.py`
- Modify: `src/mcp_civic_data/server.py`

- [ ] **Step 1: Create `hazards.py`**

```python
# src/mcp_civic_data/tools/hazards.py
import asyncio
import csv
import io

import httpx

from mcp_civic_data.server import mcp
from mcp_civic_data.utils.config import config
from mcp_civic_data.utils.http import fetch_json, fetch_text


_VALID_SOURCES = {"earthquakes", "wildfires", "weather_alerts", "air_quality", "space_weather"}
_KM_PER_DEGREE = 111.0


def _bbox(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    """Return (west, south, east, north) bounding box."""
    d = radius_km / _KM_PER_DEGREE
    return (
        max(-180.0, lon - d),
        max(-90.0, lat - d),
        min(180.0, lon + d),
        min(90.0, lat + d),
    )


async def _fetch_earthquakes(lat: float, lon: float, radius_km: float) -> str:
    data = await fetch_json(
        "https://earthquake.usgs.gov/fdsnws/event/1/query",
        params={
            "format": "geojson",
            "latitude": lat,
            "longitude": lon,
            "maxradiuskm": radius_km,
            "minmagnitude": 2.0,
            "limit": 10,
            "orderby": "time",
        },
    )
    features = data.get("features", [])
    if not features:
        return f"No earthquakes (M≥2.0) within {radius_km:.0f} km."
    lines = []
    for f in features:
        p = f.get("properties", {})
        lines.append(f"- **M{p.get('mag', '?')}** {p.get('place', '')}")
    return "\n".join(lines)


async def _fetch_wildfires(lat: float, lon: float, radius_km: float) -> str:
    west, south, east, north = _bbox(lat, lon, radius_km)
    area = f"{west:.4f},{south:.4f},{east:.4f},{north:.4f}"
    map_key = config.nasa_api_key or "DEMO_KEY"
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/VIIRS_SNPP_NRT/{area}/1"

    text = await fetch_text(url)
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return f"No active fires detected within {radius_km:.0f} km."
    lines = [f"- {r.get('acq_date', '?')} at ({r.get('latitude', '?')}, {r.get('longitude', '?')}) confidence={r.get('confidence', '?')}" for r in rows[:10]]
    total = len(rows)
    prefix = f"{total} hotspot(s) detected" + (" (showing 10)" if total > 10 else "") + ":\n"
    return prefix + "\n".join(lines)


async def _fetch_weather_alerts(lat: float, lon: float) -> str:
    data = await fetch_json(
        "https://api.weather.gov/alerts/active",
        params={"point": f"{lat},{lon}"},
    )
    alerts = data.get("features", [])
    if not alerts:
        return "No active weather alerts for this location."
    lines = []
    for a in alerts[:5]:
        p = a.get("properties", {})
        lines.append(f"- **{p.get('event', '?')}** ({p.get('severity', '?')}): {p.get('headline', '')}")
    note = "\n_Note: NOAA alerts are zone-based, not radius-filtered._"
    return "\n".join(lines) + note


async def _fetch_air_quality(lat: float, lon: float, radius_km: float) -> str:
    data = await fetch_json(
        "https://api.openaq.org/v3/locations",
        params={
            "coordinates": f"{lat},{lon}",
            "radius": str(int(radius_km * 1000)),
            "limit": "5",
        },
    )
    locations = data.get("results", [])
    if not locations:
        return f"No air quality stations within {radius_km:.0f} km."
    lines = []
    for loc in locations:
        name = loc.get("name") or "Unknown"
        sensors = loc.get("sensors", [])
        readings = []
        for s in sensors:
            param = s.get("parameter", {})
            val = s.get("latest", {}).get("value")
            if val is not None:
                readings.append(f"{param.get('displayName', '?')}: {val} {param.get('units', '')}")
        if readings:
            lines.append(f"- **{name}**: " + ", ".join(readings))
    return "\n".join(lines) if lines else "Stations found but no current readings."


async def _fetch_space_weather() -> str:
    data = await fetch_json(
        "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
    )
    if not data or not isinstance(data, list) or len(data) < 2:
        return "Space weather data unavailable."
    # Last entry: [time_tag, kp, kp_fraction, kp_int]
    latest = data[-1]
    kp = latest[1] if len(latest) > 1 else "?"
    return f"Current Kp index: **{kp}** (global, not location-filtered)"


@mcp.tool()
async def get_hazards_near(
    latitude: float,
    longitude: float,
    radius_km: float,
    sources: list[str],
) -> str:
    """Get active hazards near a location from multiple data sources.

    Args:
        latitude: Center latitude (e.g., 37.7749 for San Francisco)
        longitude: Center longitude (e.g., -122.4194 for San Francisco)
        radius_km: Search radius in kilometers
        sources: List of sources to query. Valid values:
            'earthquakes', 'wildfires', 'weather_alerts', 'air_quality', 'space_weather'

    Returns:
        Unified hazard summary grouped by source
    """
    unknown = [s for s in sources if s not in _VALID_SOURCES]
    if unknown:
        valid_list = ", ".join(sorted(_VALID_SOURCES))
        return (
            f"Unknown source(s): {', '.join(unknown)}\n"
            f"Valid sources: {valid_list}"
        )

    async def run(source: str):
        if source == "earthquakes":
            return source, await _fetch_earthquakes(latitude, longitude, radius_km)
        if source == "wildfires":
            return source, await _fetch_wildfires(latitude, longitude, radius_km)
        if source == "weather_alerts":
            return source, await _fetch_weather_alerts(latitude, longitude)
        if source == "air_quality":
            return source, await _fetch_air_quality(latitude, longitude, radius_km)
        if source == "space_weather":
            return source, await _fetch_space_weather()

    results = await asyncio.gather(*[run(s) for s in sources], return_exceptions=True)

    _LABELS = {
        "earthquakes": "Earthquakes",
        "wildfires": "Wildfires",
        "weather_alerts": "Weather Alerts",
        "air_quality": "Air Quality",
        "space_weather": "Space Weather",
    }

    sections = [f"## Hazards near ({latitude}, {longitude}) within {radius_km:.0f} km\n"]
    for source, result in zip(sources, results):
        label = _LABELS[source]
        if isinstance(result, Exception):
            sections.append(f"### {label}\n_{source}: unavailable ({result})_")
        else:
            _, text = result
            sections.append(f"### {label}\n{text}")

    return "\n\n".join(sections)
```

- [ ] **Step 2: Register in `server.py`**

Add at the bottom of `src/mcp_civic_data/server.py`:

```python
from mcp_civic_data.tools import hazards  # noqa: E402, F401
```

- [ ] **Step 3: Run the hazard tests**

```bash
uv run pytest tests/test_hazards.py -v
```

Expected: 5 tests pass.

- [ ] **Step 4: Run the full test suite**

```bash
uv run pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/mcp_civic_data/tools/hazards.py src/mcp_civic_data/server.py tests/test_hazards.py
git commit -m "feat: add get_hazards_near unified hazard query tool"
```

---

## Done

All five improvements are now implemented. Verify the final state:

```bash
uv run python -c "from mcp_civic_data import main; print('OK')"
uv run pytest tests/ -v --tb=short
```

Both should succeed with no errors.
