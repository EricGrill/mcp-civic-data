# mcp-civic-data

**Access free government and open data APIs through Claude**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![40 Tools](https://img.shields.io/badge/Tools-40-blue.svg)](#-tool-catalog)
[![13 APIs](https://img.shields.io/badge/APIs-13-orange.svg)](#-included-apis)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-yellow.svg)](https://python.org)

[Quick Start](#-quick-start) | [Tool Catalog](#-tool-catalog) | [Configuration](#-configuration) | [Examples](#-examples)

---

## 🌐 What is this?

An MCP (Model Context Protocol) server that gives Claude access to **13 free government and open data APIs** - weather forecasts, census demographics, NASA imagery, economic indicators, and more. No API keys required for most features.

> Part of the [Claude Code Plugin Marketplace](https://github.com/EricGrill/agents-skills-plugins) ecosystem.

---

## 🚀 Quick Start

**Add to Claude Desktop:**

```json
{
  "mcpServers": {
    "civic-data": {
      "command": "python",
      "args": ["-m", "mcp_govt_api"],
      "env": {
        "OPENWEATHER_API_KEY": "optional-for-global-weather",
        "NASA_API_KEY": "optional-for-higher-limits"
      }
    }
  }
}
```

**Or install manually:**

```bash
pip install mcp-civic-data
```

---

## 📡 Included APIs

| API | Coverage | Key Required |
|-----|----------|--------------|
| **NOAA Weather** | US forecasts, alerts, radar | No |
| **OpenWeather** | Global weather conditions | Yes |
| **US Census** | Population, demographics, housing | No |
| **NASA** | APOD, Mars rovers, image library | No (optional) |
| **World Bank** | GDP, poverty, country indicators | No |
| **Data.gov** | 300,000+ US government datasets | No |
| **EU Open Data** | European Union datasets | No |
| **Safecast** | Community radiation monitoring worldwide | No |
| **OpenAQ** | Global air quality from monitoring stations | No |
| **USGS Water** | US stream flow and flood levels | No |
| **USGS Earthquakes** | Global real-time seismic data | No |
| **NASA FIRMS** | Active wildfire detection from satellites | No (optional) |
| **NOAA Space Weather** | Solar wind, flares, geomagnetic storms | No |

---

## 💡 Why Use This?

| Feature | Description |
|---------|-------------|
| **Zero config** | Works immediately - most APIs need no keys |
| **Graceful fallback** | Missing keys? Those tools just won't appear |
| **Real data** | Live government sources, not cached or stale |
| **40 tools** | From quick lookups to raw API access |
| **Well-documented** | Every tool has clear parameters and examples |

---

## 📦 Tool Catalog

| Category | Tools | What You Can Do |
|----------|-------|-----------------|
| **Weather** | 5 | US forecasts, alerts, global conditions |
| **Census** | 4 | Population, demographics, housing stats |
| **NASA** | 4 | Astronomy photos, Mars rovers, image search |
| **Economics** | 3 | Country GDP, poverty, comparisons |
| **Data.gov** | 3 | Search/explore US government datasets |
| **EU Data** | 3 | Search/explore European datasets |
| **Safecast** | 3 | Radiation measurements, history, raw API |
| **OpenAQ** | 3 | Air quality readings, history, raw API |
| **USGS Water** | 3 | Stream flow, site conditions, raw API |
| **Earthquakes** | 3 | Recent quakes, nearby quakes, raw API |
| **NASA FIRMS** | 3 | Active fires by location/country, raw API |
| **Space Weather** | 4 | Solar wind, flares, alerts, raw API |

---

## 🔧 All Tools

### Weather (NOAA + OpenWeather)

| Tool | Description |
|------|-------------|
| `get_weather_forecast` | 7-day forecast for US coordinates |
| `get_weather_alerts` | Active alerts by state (CA, TX, NY...) |
| `get_global_weather` | Current weather for any city worldwide |
| `query_noaa` | Raw NOAA API access |
| `query_openweather` | Raw OpenWeather API access |

### US Census

| Tool | Description |
|------|-------------|
| `get_population` | Population by state or county |
| `get_demographics` | Age, race, income breakdown |
| `get_housing_stats` | Home values, rent, vacancy rates |
| `query_census` | Raw Census API with custom variables |

### NASA

| Tool | Description |
|------|-------------|
| `get_astronomy_photo` | Astronomy Picture of the Day |
| `get_mars_rover_photos` | Curiosity, Perseverance photos |
| `search_nasa_images` | Search NASA's image/video library |
| `query_nasa` | Raw NASA API access |

### World Bank Economics

| Tool | Description |
|------|-------------|
| `get_country_indicators` | GDP, population, poverty for any country |
| `compare_countries` | Compare indicators across countries |
| `query_worldbank` | Raw World Bank API access |

### Data.gov

| Tool | Description |
|------|-------------|
| `search_datasets` | Search 300,000+ US government datasets |
| `get_dataset_info` | Metadata and download links |
| `query_datagov` | Raw CKAN API access |

### EU Open Data

| Tool | Description |
|------|-------------|
| `search_eu_datasets` | Search European Union datasets |
| `get_eu_dataset_info` | Dataset details and distributions |
| `query_eu_data` | Raw EU Data Portal API access |

### Safecast (Radiation Monitoring)

| Tool | Description |
|------|-------------|
| `get_radiation_measurements` | Radiation readings near a location |
| `get_radiation_history` | Radiation history for a location over time |
| `query_safecast` | Raw Safecast API access |

### OpenAQ (Air Quality)

| Tool | Description |
|------|-------------|
| `get_air_quality` | Air quality measurements near a location |
| `get_air_quality_history` | Historical readings for a monitoring station |
| `query_openaq` | Raw OpenAQ v3 API access |

### USGS Water

| Tool | Description |
|------|-------------|
| `get_water_conditions` | Stream flow and gage height by US state |
| `get_water_site` | All readings for a specific USGS site |
| `query_usgs_water` | Raw USGS Water Services API access |

### USGS Earthquakes

| Tool | Description |
|------|-------------|
| `get_recent_earthquakes` | Recent quakes worldwide by magnitude |
| `get_earthquakes_near` | Recent quakes near a location |
| `query_earthquakes` | Raw USGS Earthquake API access |

### NASA FIRMS (Wildfires)

| Tool | Description |
|------|-------------|
| `get_active_fires` | Active fires/hotspots near a location |
| `get_country_fires` | Active fires for an entire country |
| `query_firms` | Raw NASA FIRMS API access |

### NOAA Space Weather

| Tool | Description |
|------|-------------|
| `get_space_weather_summary` | Solar wind, Kp index, NOAA scales |
| `get_solar_flares` | Recent solar flare activity |
| `get_space_weather_alerts` | Active space weather alerts/warnings |
| `query_space_weather` | Raw SWPC API access |

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENWEATHER_API_KEY` | For global weather | [Get free key](https://openweathermap.org/api) |
| `NASA_API_KEY` | Optional | Higher rate limits (1000/hr vs 30/hr) |
| `API_TIMEOUT` | Optional | Request timeout in seconds (default: 30) |

### API Availability on Startup

```
API Availability:
  ✓ NOAA (no key required)
  ✓ Census (no key required)
  ✓ NASA (no key, limited to 30 req/hour)
  ✗ OpenWeather (OPENWEATHER_API_KEY not set)
  ✓ World Bank (no key required)
  ✓ Data.gov (no key required)
  ✓ EU Open Data (no key required)
  ✓ Safecast (no key required)
  ✓ OpenAQ (no key required)
  ✓ USGS Water (no key required)
  ✓ USGS Earthquakes (no key required)
  ✓ NOAA Space Weather (no key required)
  ✓ NASA FIRMS (using DEMO_KEY, limited)
```

---

## 📝 Examples

### Get weather forecast

```
"What's the weather forecast for Washington DC?"
→ Uses get_weather_forecast(38.8894, -77.0352)
```

### Check demographics

```
"What's the population and median income in California?"
→ Uses get_demographics("CA")
```

### Explore Mars

```
"Show me recent photos from the Perseverance rover"
→ Uses get_mars_rover_photos(rover="perseverance")
```

### Compare economies

```
"Compare GDP between USA, China, and India"
→ Uses compare_countries(["USA", "CHN", "IND"])
```

### Check air quality

```
"What's the air quality in Beijing right now?"
→ Uses get_air_quality(39.9042, 116.4074)
```

### Check earthquake activity

```
"Any recent earthquakes near San Francisco?"
→ Uses get_earthquakes_near(37.7749, -122.4194)
```

### Monitor wildfires

```
"Are there active fires in Australia?"
→ Uses get_country_fires("AUS")
```

### Check space weather

```
"What's the current space weather like?"
→ Uses get_space_weather_summary()
```

### Check radiation levels

```
"What are the radiation levels near Fukushima?"
→ Uses get_radiation_measurements(37.4211, 141.0328)
```

### Find government data

```
"Find datasets about climate change on Data.gov"
→ Uses search_datasets("climate change")
```

---

## 🏗️ Development

```bash
# Clone and install
git clone https://github.com/EricGrill/mcp-civic-data.git
cd mcp-civic-data
pip install -e .

# Run locally
python -m mcp_govt_api
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <a href="https://github.com/EricGrill/agents-skills-plugins">
    <img src="https://img.shields.io/badge/Part%20of-Claude%20Code%20Plugin%20Marketplace-blueviolet?style=for-the-badge" alt="Plugin Marketplace">
  </a>
</p>
