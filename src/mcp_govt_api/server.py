from mcp.server.fastmcp import FastMCP

from mcp_govt_api.utils.config import config

mcp = FastMCP(
    "Government API Server",
    instructions="""Access free government and open data APIs including:
- NOAA Weather (US forecasts and alerts)
- OpenWeather (global weather, requires API key)
- US Census (population, demographics, housing)
- NASA (astronomy photos, Mars rover, image search)
- World Bank (country economic indicators)
- Data.gov (US government datasets)
- EU Open Data (European datasets)
- Safecast (community radiation monitoring worldwide)
- OpenAQ (global air quality monitoring)
- USGS Water (US stream flow and flood levels)
- USGS Earthquakes (global seismic data)
- NASA FIRMS (active wildfire detection)
- NOAA Space Weather (solar wind, flares, geomagnetic storms)
""",
)


def main():
    """Entry point for the MCP server."""
    print(config.get_availability_summary())
    mcp.run()


# Import tools to register them
from mcp_govt_api.tools import weather  # noqa: E402, F401
from mcp_govt_api.tools import census  # noqa: E402, F401
from mcp_govt_api.tools import nasa  # noqa: E402, F401
from mcp_govt_api.tools import economics  # noqa: E402, F401
from mcp_govt_api.tools import datagov  # noqa: E402, F401
from mcp_govt_api.tools import eu_data  # noqa: E402, F401
from mcp_govt_api.tools import safecast  # noqa: E402, F401
from mcp_govt_api.tools import openaq  # noqa: E402, F401
from mcp_govt_api.tools import usgs_water  # noqa: E402, F401
from mcp_govt_api.tools import earthquakes  # noqa: E402, F401
from mcp_govt_api.tools import firms  # noqa: E402, F401
from mcp_govt_api.tools import space_weather  # noqa: E402, F401
