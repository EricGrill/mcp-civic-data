# MCP Government API Server

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
pip install mcp-govt-api-free
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
    "govt-api": {
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
