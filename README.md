# mcp-civic-data

An MCP server providing access to free government and open data APIs.

## APIs Included

- NOAA Weather API (forecasts, alerts)
- OpenWeather API (global weather, requires API key)
- US Census API (population, demographics, housing)
- NASA API (APOD, Mars rover photos, image search)
- World Bank API (country indicators, comparisons)
- Data.gov (US government datasets)
- European Open Data Portal (EU datasets)

## Installation

```bash
pip install mcp-civic-data
```

## Configuration

Optional environment variables:
- `OPENWEATHER_API_KEY` - Required for global weather tools
- `NASA_API_KEY` - Optional, increases rate limits

## Claude Desktop Setup

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "civic-data": {
      "command": "python",
      "args": ["-m", "mcp_govt_api"],
      "env": {
        "OPENWEATHER_API_KEY": "your-key-here",
        "NASA_API_KEY": "your-key-here"
      }
    }
  }
}
```

## Available Tools

### Weather
- `get_weather_forecast` - US weather forecast by coordinates (NOAA)
- `get_weather_alerts` - Active weather alerts by state (NOAA)
- `get_global_weather` - Weather for any city worldwide (OpenWeather)

### Census
- `get_population` - Population data by state/county
- `get_demographics` - Age, race, income demographics
- `get_housing_stats` - Housing statistics and vacancy rates

### NASA
- `get_astronomy_photo` - Astronomy Picture of the Day
- `get_mars_rover_photos` - Mars rover photos by date/sol
- `search_nasa_images` - Search NASA image library

### Economics (World Bank)
- `get_country_indicators` - GDP, population, poverty data
- `compare_countries` - Compare indicators across countries

### Data.gov
- `search_datasets` - Search US government datasets
- `get_dataset_info` - Dataset details and download links

### EU Open Data
- `search_eu_datasets` - Search European datasets
- `get_eu_dataset_info` - EU dataset details

### Raw API Access
Each API also has a `query_*` tool for direct API access.

## License

MIT
