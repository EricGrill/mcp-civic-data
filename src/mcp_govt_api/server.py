from mcp.server.fastmcp import FastMCP

from mcp_govt_api.utils.config import config
from mcp_govt_api.utils.http import http_lifespan

mcp = FastMCP(
    "Government API Server",
    lifespan=http_lifespan,
    instructions="""Access free government and open data APIs including:
- NOAA Weather (US forecasts and alerts)
- OpenWeather (global weather, requires API key)
- US Census (population, demographics, housing)
- NASA (astronomy photos, Mars rover, image search)
- World Bank (country economic indicators)
- Data.gov (US government datasets)
- EU Open Data (European datasets, multilingual)
- Safecast (community radiation monitoring worldwide)
- OpenAQ (global air quality monitoring)
- USGS Water (US stream flow and flood levels)
- USGS Earthquakes (global seismic data)
- NASA FIRMS (active wildfire detection)
- NOAA Space Weather (solar wind, flares, geomagnetic storms)
- CISA (cybersecurity advisories, known exploited vulnerabilities)
- SEC EDGAR (company filings, submissions, and company facts)
- FRED (Federal Reserve economic data, time series, indicators)
- CDC (public health surveillance, disease tracking, vaccination coverage)
- BLS (labor statistics, CPI, unemployment, employment data)
- FEMA (disaster declarations, disaster summaries, housing assistance)
- FDA (drug/food/device recalls, adverse events, drug labels via openFDA)
- NOAA CO-OPS (tide predictions, observed water levels, coastal stations)
- NPS (national parks, park alerts, and park details)
- EIA (electricity data, petroleum prices, energy market overview; requires API key)
- BTS (airline on-time performance, border crossing data, transportation datasets)
""",
)


def main():
    """Entry point for the MCP server."""
    print(config.get_availability_summary())
    mcp.run()


# Import tools to register them
from mcp_govt_api.tools import (  # noqa: E402
    bls,  # noqa: F401
    bts,  # noqa: F401
    cdc,  # noqa: F401
    census,  # noqa: F401
    cisa,  # noqa: F401
    datagov,  # noqa: F401
    earthquakes,  # noqa: F401
    eia,  # noqa: F401
    economics,  # noqa: F401
    eu_data,  # noqa: F401
    fda,  # noqa: F401
    fema,  # noqa: F401
    firms,  # noqa: F401
    fred,  # noqa: F401
    location,  # noqa: F401
    nasa,  # noqa: F401
    noaa_coops,  # noqa: F401
    noaa_weather,  # noqa: F401
    nps,  # noqa: F401
    openaq,  # noqa: F401
    safecast,  # noqa: F401
    sec,  # noqa: F401
    space_weather,  # noqa: F401
    usgs_water,  # noqa: F401
    weather,  # noqa: F401
)
