<div align="center">

# mcp-civic-data

### Real-time government and open data for AI agents

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![40 Tools](https://img.shields.io/badge/tools-40-2563eb.svg?style=flat-square)](#tool-reference)
[![13 APIs](https://img.shields.io/badge/APIs-13-7c3aed.svg?style=flat-square)](#data-sources)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776ab.svg?style=flat-square)](https://python.org)
[![MCP](https://img.shields.io/badge/protocol-MCP-f97316.svg?style=flat-square)](https://modelcontextprotocol.io)

An [MCP](https://modelcontextprotocol.io) server that connects AI agents to **13 free, authoritative data APIs** — weather, earthquakes, air quality, wildfires, space weather, demographics, economics, and more.

No API keys required for 11 of 13 sources. Just install and go.

[Get Started](#get-started) · [Data Sources](#data-sources) · [Tool Reference](#tool-reference) · [Configuration](#configuration)

</div>

---

## Get Started

**Claude Desktop / Claude Code**

```json
{
  "mcpServers": {
    "civic-data": {
      "command": "python",
      "args": ["-m", "mcp_govt_api"],
      "env": {
        "OPENWEATHER_API_KEY": "optional",
        "NASA_API_KEY": "optional"
      }
    }
  }
}
```

**Standalone**

```bash
pip install mcp-civic-data
python -m mcp_govt_api
```

---

## Data Sources

### Earth & Environment

| Source | What It Covers | Key |
|--------|---------------|-----|
| [NOAA Weather](https://weather.gov) | US forecasts, severe weather alerts | -- |
| [OpenWeather](https://openweathermap.org) | Global weather for any city | Required |
| [OpenAQ](https://openaq.org) | Air quality from stations worldwide | -- |
| [USGS Water](https://waterservices.usgs.gov) | Real-time stream flow and flood levels across every US river | -- |
| [Safecast](https://safecast.org) | Community radiation monitoring, 150M+ measurements | -- |

### Hazards & Events

| Source | What It Covers | Key |
|--------|---------------|-----|
| [USGS Earthquakes](https://earthquake.usgs.gov) | Every earthquake on Earth, real-time | -- |
| [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov) | Active wildfires detected from satellites | Optional |
| [NOAA Space Weather](https://swpc.noaa.gov) | Solar wind, geomagnetic storms, solar flares | -- |

### Demographics & Economics

| Source | What It Covers | Key |
|--------|---------------|-----|
| [US Census](https://census.gov) | Population, demographics, housing for every US county | -- |
| [World Bank](https://worldbank.org) | GDP, poverty, unemployment for 200+ countries | -- |

### Open Data Catalogs

| Source | What It Covers | Key |
|--------|---------------|-----|
| [Data.gov](https://data.gov) | 300,000+ US government datasets | -- |
| [EU Open Data](https://data.europa.eu) | European Union datasets, multilingual | -- |
| [NASA](https://api.nasa.gov) | APOD, Mars rover photos, image/video library | Optional |

> **Key**: `--` = no key needed. `Optional` = works without a key, key unlocks higher rate limits. `Required` = key needed to enable.

---

## What You Can Ask

```
"What's the weather forecast for Washington DC?"
"What's the air quality in Beijing right now?"
"Any recent earthquakes near San Francisco?"
"Are there active fires in Australia?"
"What's the current space weather like?"
"Compare GDP between USA, China, and India"
"What's the population and median income in California?"
"Show me recent photos from the Perseverance rover"
"What are the radiation levels near Fukushima?"
"What are stream flow levels in Colorado?"
"Find datasets about climate change on Data.gov"
```

---

## Tool Reference

Every data source exposes **high-level tools** for common queries and a **raw query tool** for full API access.

<details>
<summary><strong>Weather</strong> — 5 tools</summary>

| Tool | Description |
|------|-------------|
| `get_weather_forecast` | 7-day forecast for US coordinates |
| `get_weather_alerts` | Active severe weather alerts by state |
| `get_global_weather` | Current conditions for any city worldwide |
| `query_noaa` | Raw NOAA API access |
| `query_openweather` | Raw OpenWeather API access |

</details>

<details>
<summary><strong>Air Quality</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_air_quality` | Current readings from stations near a location |
| `get_air_quality_history` | Historical measurements for a monitoring station |
| `query_openaq` | Raw OpenAQ v3 API access |

</details>

<details>
<summary><strong>Water</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_water_conditions` | Stream flow and gage height by US state |
| `get_water_site` | All readings for a specific USGS monitoring site |
| `query_usgs_water` | Raw USGS Water Services API access |

</details>

<details>
<summary><strong>Earthquakes</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_recent_earthquakes` | Recent quakes worldwide above a magnitude threshold |
| `get_earthquakes_near` | Recent quakes near a geographic location |
| `query_earthquakes` | Raw USGS Earthquake API access |

</details>

<details>
<summary><strong>Wildfires</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_active_fires` | Active fires and hotspots near a location |
| `get_country_fires` | Active fires for an entire country (ISO alpha-3) |
| `query_firms` | Raw NASA FIRMS API access |

</details>

<details>
<summary><strong>Space Weather</strong> — 4 tools</summary>

| Tool | Description |
|------|-------------|
| `get_space_weather_summary` | Solar wind speed, Kp index, NOAA storm scales |
| `get_solar_flares` | Recent solar flare activity and classifications |
| `get_space_weather_alerts` | Active NOAA space weather alerts and warnings |
| `query_space_weather` | Raw SWPC API access |

</details>

<details>
<summary><strong>Radiation</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_radiation_measurements` | Radiation readings near a location |
| `get_radiation_history` | Radiation history with date range filtering |
| `query_safecast` | Raw Safecast API access |

</details>

<details>
<summary><strong>Demographics</strong> — 4 tools</summary>

| Tool | Description |
|------|-------------|
| `get_population` | Population by state or county |
| `get_demographics` | Age, race, income breakdown |
| `get_housing_stats` | Home values, rent, vacancy rates |
| `query_census` | Raw Census API with custom variables |

</details>

<details>
<summary><strong>Economics</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_country_indicators` | GDP, population, poverty for any country |
| `compare_countries` | Compare indicators across multiple countries |
| `query_worldbank` | Raw World Bank API access |

</details>

<details>
<summary><strong>NASA</strong> — 4 tools</summary>

| Tool | Description |
|------|-------------|
| `get_astronomy_photo` | Astronomy Picture of the Day |
| `get_mars_rover_photos` | Photos from Curiosity, Perseverance, and more |
| `search_nasa_images` | Search NASA's image and video library |
| `query_nasa` | Raw NASA API access |

</details>

<details>
<summary><strong>Open Data</strong> — 6 tools</summary>

| Tool | Description |
|------|-------------|
| `search_datasets` | Search 300,000+ US government datasets |
| `get_dataset_info` | Dataset metadata and download links |
| `query_datagov` | Raw CKAN API access |
| `search_eu_datasets` | Search European Union datasets |
| `get_eu_dataset_info` | EU dataset details and distributions |
| `query_eu_data` | Raw EU Data Portal API access |

</details>

---

## Configuration

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENWEATHER_API_KEY` | Enables global weather tools | *(disabled)* |
| `NASA_API_KEY` | Higher rate limits for NASA + FIRMS | `DEMO_KEY` (30 req/hr) |
| `API_TIMEOUT` | Request timeout in seconds | `30` |

On startup the server prints which APIs are available:

```
API Availability:
  ✓ NOAA Weather          ✓ Census         ✓ World Bank
  ✓ OpenAQ                ✓ USGS Water     ✓ USGS Earthquakes
  ✓ Safecast              ✓ Data.gov       ✓ EU Open Data
  ✓ Space Weather         ✓ NASA FIRMS     ✓ NASA
  ✗ OpenWeather (key not set)
```

---

## Development

```bash
git clone https://github.com/EricGrill/mcp-civic-data.git
cd mcp-civic-data
pip install -e .
python -m mcp_govt_api
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-source`)
3. Commit your changes
4. Open a Pull Request

See the [issue tracker](https://github.com/EricGrill/mcp-civic-data/issues) for data sources we'd like to add.

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <a href="https://github.com/EricGrill/agents-skills-plugins">
    <img src="https://img.shields.io/badge/Part%20of-Claude%20Code%20Plugin%20Marketplace-7c3aed?style=for-the-badge" alt="Plugin Marketplace">
  </a>
</p>
