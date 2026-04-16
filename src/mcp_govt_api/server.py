from mcp.server.fastmcp import FastMCP

from mcp_govt_api.utils.config import config
from mcp_govt_api.utils.http import http_lifespan
from mcp_govt_api.utils.logging import get_logger

logger = get_logger(__name__)

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
- CMS (hospital quality ratings, Medicare provider search, healthcare data)
- CDC (public health surveillance, disease tracking, vaccination coverage)
- ClinicalTrials.gov (clinical study search, trial details, database statistics)
- BLS (labor statistics, CPI, unemployment, employment data)
- FEMA (disaster declarations, disaster summaries, housing assistance)
- EPA (facility compliance via ECHO, toxic releases via Envirofacts TRI)
- FDA (drug/food/device recalls, adverse events, drug labels via openFDA)
- NHTSA (vehicle recalls, consumer complaints, VIN decoding)
- NOAA CO-OPS (tide predictions, observed water levels, coastal stations)
- NPS (national parks, park alerts, and park details)
- EIA (electricity data, petroleum prices, energy market overview; requires API key)
- BEA (regional GDP, personal income, GDP by industry; requires API key)
- BTS (airline on-time performance, border crossing data, transportation datasets)
- SBA (small business size standards, disaster loans, open datasets)
- CFPB (consumer complaints, financial product issues, company response data)
- OSHA (workplace inspections, violations, fatality reports via DOL enforcement data)
- NCES (school districts, school enrollment, college/university data via Education Data Portal)
- SAMHSA (mental health and substance abuse treatment facility locator, behavioral health data)
- USDA (food nutrition via FoodData Central, crop production via NASS; requires API key)
- USFS (active wildfires, fire perimeters, National Forest boundaries via WFIGS/ArcGIS)
- BJS / FBI CDE (crime estimates, arrest data, justice datasets; requires API key)
- Blitzortung (real-time lightning strike detection worldwide)
- N2YO (satellite tracking, positions, TLE data; requires API key)
- Submarine Cable Map (undersea internet cable infrastructure)
- NOAA Satellite Imagery (GOES-East/West satellite imagery links and timestamps)
- USGS Volcanoes (active volcanoes, alerts, eruption monitoring)
- ReliefWeb (global disaster events, situation reports)
- OpenRailwayMap (railway stations, lines via Overpass/OSM)
- Cloudflare Radar (internet traffic, top domains, DDoS attacks)
- IHR Internet Health (network disconnections, delays, AS hegemony)
- Service Outages (status page monitoring for GitHub, Slack, etc.)
""",
)


def main():
    """Entry point for the MCP server."""
    logger.info("Starting MCP Government API Server")
    for line in config.get_availability_summary().splitlines():
        logger.info(line.strip())
    mcp.run()


# Import tools to register them
from mcp_govt_api.tools import (  # noqa: E402
    bea,  # noqa: F401
    bjs,  # noqa: F401
    bls,  # noqa: F401
    bts,  # noqa: F401
    cdc,  # noqa: F401
    census,  # noqa: F401
    cfpb,  # noqa: F401
    cisa,  # noqa: F401
    clinical_trials,  # noqa: F401
    cms,  # noqa: F401
    datagov,  # noqa: F401
    earthquakes,  # noqa: F401
    economics,  # noqa: F401
    eia,  # noqa: F401
    epa,  # noqa: F401
    eu_data,  # noqa: F401
    fda,  # noqa: F401
    fema,  # noqa: F401
    firms,  # noqa: F401
    fred,  # noqa: F401
    location,  # noqa: F401
    nasa,  # noqa: F401
    nces,  # noqa: F401
    nhtsa,  # noqa: F401
    noaa_coops,  # noqa: F401
    noaa_weather,  # noqa: F401
    nps,  # noqa: F401
    openaq,  # noqa: F401
    osha,  # noqa: F401
    safecast,  # noqa: F401
    samhsa,  # noqa: F401
    sba,  # noqa: F401
    sec,  # noqa: F401
    space_weather,  # noqa: F401
    usda,  # noqa: F401
    usfs,  # noqa: F401
    usgs_water,  # noqa: F401
    weather,  # noqa: F401
)

from mcp_govt_api.tools import (  # noqa: E402
    blitzortung,  # noqa: F401
    cloudflare_radar,  # noqa: F401
    disaster_events,  # noqa: F401
    internet_health,  # noqa: F401
    n2yo,  # noqa: F401
    noaa_imagery,  # noqa: F401
    outages,  # noqa: F401
    railway,  # noqa: F401
    submarine_cables,  # noqa: F401
    volcanoes,  # noqa: F401
)
