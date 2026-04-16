<div align="center">

# mcp-civic-data

### Authoritative civic and government data for AI agents

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![CI](https://github.com/EricGrill/mcp-civic-data/actions/workflows/ci.yml/badge.svg)](https://github.com/EricGrill/mcp-civic-data/actions/workflows/ci.yml)
[![110 Tools](https://img.shields.io/badge/tools-110-2563eb.svg?style=flat-square)](#tool-reference)
[![33 APIs](https://img.shields.io/badge/APIs-33-7c3aed.svg?style=flat-square)](#data-sources)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776ab.svg?style=flat-square)](https://python.org)
[![MCP](https://img.shields.io/badge/protocol-MCP-f97316.svg?style=flat-square)](https://modelcontextprotocol.io)

An [MCP](https://modelcontextprotocol.io) server that connects AI agents to **33 free, authoritative public data APIs** across weather, hazards, air quality, water, tides, radiation, demographics, economics, education, energy, labor statistics, public health, behavioral health, healthcare quality, disaster management, FDA safety data, vehicle safety, workplace safety, national parks, national forests, consumer financial protection, open data discovery, cybersecurity, SEC disclosures, Federal Reserve economic indicators, BEA economic accounts, BTS transportation data, SBA small business data, USDA food and agriculture data, and USFS wildfire and forest data.

Built for practical agent workflows: concise high-level tools, raw query access where it matters, and location-aware inputs that accept city names, ZIP codes, addresses, or raw coordinates.

No API keys required for 22 of 33 sources. Install it, point your MCP client at it, and start querying real civic data.

[Get Started](#get-started) · [What's New](#whats-new) · [Data Sources](#data-sources) · [Tool Reference](#tool-reference) · [Roadmap](#implementation-roadmap) · [Contributing](CONTRIBUTING.md)

</div>

---

## Get Started

**Claude Desktop / Claude Code**

```json
{
  "mcpServers": {
    "civic-data": {
      "command": "python3",
      "args": ["-m", "mcp_govt_api"],
      "env": {
        "OPENWEATHER_API_KEY": "optional",
        "NASA_API_KEY": "optional",
        "FRED_API_KEY": "optional",
        "BLS_API_KEY": "optional",
        "NPS_API_KEY": "optional",
        "EIA_API_KEY": "optional",
        "BEA_API_KEY": "optional",
        "USDA_API_KEY": "optional"
      }
    }
  }
}
```

**Standalone**

```bash
pip install mcp-civic-data
python3 -m mcp_govt_api
```

---

## What's New

- Added USDA Forest Service tools for active wildfires, fire perimeters, and National Forest search via WFIGS/ArcGIS
- Added SAMHSA tools for mental health and substance abuse treatment facility locator and behavioral health data
- Added CMS tools for hospital quality ratings, Medicare provider search, and healthcare data
- Added FDA tools for recalls, adverse events, and drug labels via openFDA
- Added CDC public health surveillance tools for disease tracking and vaccination coverage
- Added shared geolocation support with a new `lookup_location` tool
- Upgraded weather, earthquake, and air-quality tools to accept human-friendly location strings
- Added CISA cybersecurity tools and integrated them into the server and README
- Added SEC EDGAR tools for filings, submissions, and company facts
- Added GitHub Actions CI for install, compile, unit test, import, and build validation
- Added `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md`
- Added BEA regional and national economic accounts tools (GDP, income, industry)
- Added branch protection and required automated checks on `main`

---

## Data Sources

### Earth & Environment

| Source | What It Covers | Key |
|--------|---------------|-----|
| [NOAA Weather](https://weather.gov) | US forecasts, severe weather alerts | -- |
| [OpenWeather](https://openweathermap.org) | Global weather for any city | Required |
| [OpenAQ](https://openaq.org) | Air quality from stations worldwide | -- |
| [USGS Water](https://waterservices.usgs.gov) | Real-time stream flow and flood levels across every US river | -- |
| [NOAA CO-OPS](https://tidesandcurrents.noaa.gov) | Tide predictions, observed water levels, coastal stations | -- |
| [Safecast](https://safecast.org) | Community radiation monitoring, 150M+ measurements | -- |

### Hazards & Events

| Source | What It Covers | Key |
|--------|---------------|-----|
| [USGS Earthquakes](https://earthquake.usgs.gov) | Every earthquake on Earth, real-time | -- |
| [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov) | Active wildfires detected from satellites | Optional |
| [NOAA Space Weather](https://swpc.noaa.gov) | Solar wind, geomagnetic storms, solar flares | -- |
| [CISA](https://www.cisa.gov) | Known exploited vulnerabilities, security alerts, advisories | -- |
| [FEMA](https://www.fema.gov/api/open) | Disaster declarations, assistance data, housing assistance | -- |
| [USFS (WFIGS)](https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/) | Active wildfires, fire perimeters, National Forest boundaries | -- |

### Health & Safety

| Source | What It Covers | Key |
|--------|---------------|-----|
| [CMS](https://data.cms.gov) | Hospital quality ratings, Medicare provider search, healthcare data | -- |
| [FDA (openFDA)](https://open.fda.gov) | Drug/food/device recalls, adverse events, drug labels | -- |
| [SAMHSA](https://findtreatment.gov) | Mental health and substance abuse treatment facilities, behavioral health data | -- |
| [NHTSA](https://www.nhtsa.gov) | Vehicle recalls, consumer complaints, VIN decoding | -- |
| [OSHA (DOL)](https://enforcedata.dol.gov) | Workplace inspections, violations, fatality reports | -- |

### Education

| Source | What It Covers | Key |
|--------|---------------|-----|
| [NCES (Education Data Portal)](https://educationdata.urban.org) | School districts, school enrollment, college/university data | -- |

### Demographics & Economics

| Source | What It Covers | Key |
|--------|---------------|-----|
| [US Census](https://census.gov) | Population, demographics, housing for every US county | -- |
| [World Bank](https://worldbank.org) | GDP, poverty, unemployment for 200+ countries | -- |
| [FRED](https://fred.stlouisfed.org) | Federal Reserve economic data: GDP, inflation, employment, interest rates | Required |
| [BLS](https://www.bls.gov) | CPI, unemployment, employment, labor statistics | Optional |
| [BEA](https://www.bea.gov) | Regional GDP, personal income, GDP by industry | Required |

### Energy

| Source | What It Covers | Key |
|--------|---------------|-----|
| [EIA](https://www.eia.gov/opendata/) | Electricity, petroleum, natural gas, coal, and energy market data | Required |

### Transportation

| Source | What It Covers | Key |
|--------|---------------|-----|
| [BTS](https://data.bts.gov) | Airline on-time performance, border crossing data, transportation datasets | -- |

### Small Business

| Source | What It Covers | Key |
|--------|---------------|-----|
| [SBA](https://data.sba.gov) | Small business size standards, disaster loans, open datasets | -- |

### Food & Agriculture

| Source | What It Covers | Key |
|--------|---------------|-----|
| [USDA](https://fdc.nal.usda.gov/) | Food nutrition data (FoodData Central), crop production and acreage (NASS) | Required |

### Finance & Consumer Protection

| Source | What It Covers | Key |
|--------|---------------|-----|
| [SEC EDGAR](https://sec.gov/edgar) | Company filings, 10-K, 10-Q, 8-K forms | -- |
| [CFPB](https://www.consumerfinance.gov) | Consumer complaints, financial product issues, company responses | -- |

### Public Health

| Source | What It Covers | Key |
|--------|---------------|-----|
| [CDC Open Data](https://data.cdc.gov) | Disease surveillance, vaccination coverage, public health datasets | -- |

### Parks & Recreation

| Source | What It Covers | Key |
|--------|---------------|-----|
| [NPS](https://www.nps.gov/subjects/developer) | National parks, alerts, closures, park details | Required |

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
"What's the air quality near 10001?"
"Any recent earthquakes near San Francisco?"
"Resolve 1600 Pennsylvania Ave NW to coordinates"
"Are there active fires in Australia?"
"What's the current space weather like?"
"Compare GDP between USA, China, and India"
"What's the population and median income in California?"
"Show me recent photos from the Perseverance rover"
"What are the radiation levels near Fukushima?"
"What are stream flow levels in Colorado?"
"What are the tide predictions for Providence, RI?"
"Find tide stations in Florida"
"Find datasets about climate change on Data.gov"
"What's the current US GDP from FRED?"
"Search FRED for unemployment rate data"
"Get Apple's latest 10-K filing from SEC"
"Show me recent SEC filings for Tesla"
"Search CDC datasets about influenza"
"What are the latest disease surveillance reports for Salmonellosis?"
"Show me vaccination coverage data for Influenza"
"Are there any known exploited vulnerabilities for Microsoft products?"
"What are the latest CISA security alerts?"
"Show me consumer complaints about mortgages in California"
"What are the most common complaint types filed with the CFPB?"
"What's the current CPI?"
"What's the unemployment rate in California?"
"Show me BLS employment data for 2023"
"What FEMA disaster declarations were made in Florida this year?"
"Show me housing assistance data for Hurricane Ian"
"Search for hospitals in New York with quality ratings"
"What's the quality rating for facility 050001?"
"Find Medicare providers specializing in Cardiology in Texas"
"Show me recent FDA drug recalls in California"
"What adverse events have been reported for aspirin?"
"Get drug label information for ibuprofen"
"Search for national parks in California"
"Are there any alerts at Yosemite?"
"Tell me about Grand Canyon National Park"
"Are there any recalls for 2020 Toyota Camry?"
"Show me consumer complaints for Ford F-150"
"Decode VIN 1HGCM82633A004352"
"Search for school districts in California"
"What's the enrollment at schools in Texas?"
"Find colleges in New York"
"Search for nutritional info on chicken breast"
"What are the detailed nutrients in FDC ID 171688?"
"Show me corn production data for Iowa in 2023"
"What are the current gasoline prices?"
"Show me electricity data for California"
"What energy data categories does the EIA provide?"
"What's California's GDP from BEA?"
"Show me GDP by industry for 2022"
"What datasets does the BEA offer?"
"Show me airline on-time stats for American Airlines"
"What's the border crossing data for El Paso?"
"Search BTS datasets about freight"
"Search SBA datasets for PPP loans"
"What is the SBA size standard for restaurants?"
"Show me SBA disaster loans in Florida"
"Show me OSHA inspections in California"
"What violations were found in OSHA inspection 1234567?"
"Search for workplace fatality reports in Texas"
"Find mental health treatment facilities near Chicago"
"Search SAMHSA data for opioid treatment admissions"
"What are the active wildfires in California?"
"Show me wildfire perimeters in Oregon"
"Search for National Forests in Montana"
```

---

## Tool Reference

Every data source exposes **high-level tools** for common queries and a **raw query tool** for full API access.

<details>
<summary><strong>Weather</strong> — 5 tools</summary>

| Tool | Description |
|------|-------------|
| `get_weather_forecast` | 7-day forecast for a US location by place name or coordinates |
| `get_weather_alerts` | Active severe weather alerts by state |
| `get_global_weather` | Current conditions for any city worldwide |
| `query_noaa` | Raw NOAA API access |
| `query_openweather` | Raw OpenWeather API access |

</details>

<details>
<summary><strong>NOAA Radar & Alerts</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_forecast_discussion` | Area Forecast Discussion from a NWS Weather Forecast Office |
| `get_active_weather_alerts` | Active weather alerts filtered by state, event type, and severity |
| `get_radar_stations` | NEXRAD radar stations, optionally filtered by state |

</details>

<details>
<summary><strong>Geolocation</strong> — 1 tool</summary>

| Tool | Description |
|------|-------------|
| `lookup_location` | Resolve a city, ZIP code, address, or coordinates to a normalized location |

</details>

<details>
<summary><strong>Air Quality</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_air_quality` | Current readings from stations near a place name or coordinates |
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
<summary><strong>Tides & Coastal (NOAA CO-OPS)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_tide_predictions` | Tide predictions for a CO-OPS station |
| `get_water_levels` | Observed water levels from a CO-OPS station |
| `search_tide_stations` | Search for NOAA CO-OPS tide prediction stations |

</details>

<details>
<summary><strong>Earthquakes</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_recent_earthquakes` | Recent quakes worldwide above a magnitude threshold |
| `get_earthquakes_near` | Recent quakes near a place name or coordinates |
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
<summary><strong>Cybersecurity (CISA)</strong> — 4 tools</summary>

| Tool | Description |
|------|-------------|
| `search_known_exploited_vulnerabilities` | Search CISA's catalog of actively exploited vulnerabilities |
| `get_recent_cisa_alerts` | Recent CISA security alerts and advisories |
| `get_cisa_bulletins` | Weekly CISA vulnerability summaries from major vendors |
| `query_cisa_kev` | Raw CISA Known Exploited Vulnerabilities catalog access |

</details>

<details>
<summary><strong>CDC Public Health</strong> — 4 tools</summary>

| Tool | Description |
|------|-------------|
| `search_cdc_datasets` | Search CDC's open data catalog by keyword |
| `get_cdc_disease_surveillance` | Notifiable disease case counts from the NNDSS |
| `get_cdc_vaccination_coverage` | Vaccination coverage estimates by vaccine and state |
| `query_cdc_open_data` | Raw CDC SODA API access for any dataset |

</details>

<details>
<summary><strong>CMS Healthcare</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `search_hospitals` | Search hospitals by name or state with overall quality ratings |
| `get_hospital_quality` | Get detailed quality measures and ratings for a specific hospital |
| `search_medicare_providers` | Search Medicare-enrolled healthcare providers by name, state, or specialty |

</details>

<details>
<summary><strong>FEMA Disasters</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_fema_disasters` | Search disaster declarations by state, year, or type |
| `get_fema_disaster_summary` | Detailed summary for a specific disaster number |
| `get_fema_assistance` | Housing assistance data for disaster survivors |

</details>

<details>
<summary><strong>USDA Forest Service (USFS)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_active_wildfires` | Current wildfire incidents from WFIGS by state |
| `get_wildfire_perimeters` | Active fire perimeters and boundaries with acreage |
| `search_national_forests` | Search National Forests by name or state |

</details>

<details>
<summary><strong>FDA (openFDA)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `search_fda_recalls` | Search FDA drug, food, and device recall/enforcement reports |
| `get_fda_adverse_events` | Search drug adverse event reports from FAERS |
| `get_fda_drug_labels` | Search drug labeling and SPL data (indications, warnings, dosage) |

</details>

<details>
<summary><strong>SBA (Small Business)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `search_sba_datasets` | Search SBA open datasets on data.sba.gov |
| `get_sba_size_standards` | Look up small business size standards by industry or NAICS code |
| `get_sba_disaster_loans` | Get SBA disaster loan data by state or year |

</details>

<details>
<summary><strong>Workplace Safety (OSHA)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `search_osha_inspections` | Search OSHA workplace inspections by state or establishment |
| `get_osha_violations` | Get violations for a specific OSHA inspection |
| `search_osha_fatalities` | Search workplace fatality and catastrophe reports |

</details>

<details>
<summary><strong>NHTSA Vehicle Safety</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `search_vehicle_recalls` | Search NHTSA vehicle recall campaigns by make, model, and year |
| `get_vehicle_complaints` | Get consumer complaints about vehicles from NHTSA |
| `decode_vin` | Decode a Vehicle Identification Number for make/model/year/specs |

</details>

<details>
<summary><strong>SAMHSA (Behavioral Health)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `find_treatment_facilities` | Find mental health and substance abuse treatment facilities near a location |
| `search_samhsa_datasets` | Search SAMHSA open data catalog for behavioral health datasets |
| `get_samhsa_facility_details` | Get detailed info about a specific SAMHSA treatment facility |

</details>

<details>
<summary><strong>SEC EDGAR</strong> — 5 tools</summary>

| Tool | Description |
|------|-------------|
| `get_company_filings` | Get SEC filings by ticker or CIK (10-K, 10-Q, 8-K) |
| `search_company` | Find a company CIK by name or ticker guidance |
| `get_latest_submissions` | Get recent submissions filtered by form type |
| `get_company_facts` | Get company facts and XBRL financial data |
| `query_sec_edgar` | Raw SEC EDGAR API access |

</details>

<details>
<summary><strong>CFPB Consumer Complaints</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `search_cfpb_complaints` | Search consumer complaints by product, company, state, or keyword |
| `get_cfpb_complaint` | Get full details of a specific consumer complaint by ID |
| `get_cfpb_complaint_stats` | Aggregate complaint statistics by product, company, or state |

</details>

<details>
<summary><strong>National Parks (NPS)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `search_national_parks` | Search parks by name, keyword, or state code |
| `get_park_alerts` | Active alerts for a park (closures, cautions, dangers) |
| `get_park_info` | Detailed park info including hours, fees, and contacts |

</details>

<details>
<summary><strong>Food & Agriculture (USDA)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `search_usda_foods` | Search FoodData Central for nutritional info on foods |
| `get_food_details` | Get detailed nutrition data for a specific food by FDC ID |
| `get_crop_data` | Get NASS crop production, acreage, and yield data by state and year |

</details>

<details>
<summary><strong>Energy (EIA)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_electricity_data` | Retail electricity sales, prices, and revenue by state |
| `get_petroleum_prices` | Gasoline, diesel, and heating oil price data |
| `get_energy_overview` | Browse available EIA data categories and routes |

</details>

<details>
<summary><strong>Transportation (BTS)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_airline_ontime_stats` | Airline on-time performance, delays, and cancellations |
| `get_border_crossing_data` | US-Canada and US-Mexico border crossing entry data |
| `search_bts_datasets` | Search BTS open datasets on data.bts.gov |

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
<summary><strong>Economics (World Bank)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_country_indicators` | GDP, population, poverty for any country |
| `compare_countries` | Compare indicators across multiple countries |
| `query_worldbank` | Raw World Bank API access |

</details>

<details>
<summary><strong>Economics (FRED)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `search_fred_series` | Search for economic data series by keyword |
| `get_fred_series` | Get observations for a series (e.g., GDP, UNRATE, CPIAUCSL) |
| `get_fred_series_info` | Get metadata about a series |

</details>

<details>
<summary><strong>Labor Statistics (BLS)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_bls_timeseries` | Get time series data for any BLS series (CPI, employment, PPI) |
| `search_bls_series` | Look up common BLS series IDs by keyword |
| `get_unemployment_rate` | National or state-level unemployment rate data |

</details>

<details>
<summary><strong>Economics (BEA)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `get_bea_regional_data` | Regional GDP, income, and employment data by state |
| `get_bea_gdp_by_industry` | GDP breakdown by industry sector |
| `search_bea_datasets` | List available BEA datasets and tables |

</details>

<details>
<summary><strong>Education (NCES)</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `search_school_districts` | Search school districts by state or name |
| `get_school_enrollment` | Get school enrollment data by state or district |
| `search_colleges` | Search colleges and universities via IPEDS |

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
| `FRED_API_KEY` | Enables FRED economic data tools | *(disabled)* |
| `BLS_API_KEY` | Higher rate limits for BLS (25 to 500 queries/day) | *(works without key)* |
| `NPS_API_KEY` | Enables National Park Service tools | *(disabled)* |
| `EIA_API_KEY` | Enables EIA energy market tools | *(disabled)* |
| `BEA_API_KEY` | Enables BEA economic accounts tools | *(disabled)* |
| `USDA_API_KEY` | Enables USDA food nutrition and crop data tools | *(disabled)* |
| `API_TIMEOUT` | Request timeout in seconds | `30` |

On startup the server prints which APIs are available:

```
API Availability:
  ✓ NOAA Weather          ✓ Census         ✓ World Bank
  ✓ OpenAQ                ✓ USGS Water     ✓ USGS Earthquakes
  ✓ Safecast              ✓ Data.gov       ✓ EU Open Data
  ✓ Space Weather         ✓ NASA FIRMS     ✓ NASA
  ✓ SEC EDGAR             ✓ CDC Open Data
  ✓ BLS                   ✓ FEMA
  ✓ SBA                   ✓ CFPB
  ✓ CMS Healthcare        ✓ SAMHSA
  ✗ OpenWeather (key not set)
  ✗ EIA (key not set)
  ✗ BEA (key not set)
  ✗ USDA (key not set)
```

---

## Implementation Roadmap

The active roadmap lives in [#87](https://github.com/EricGrill/mcp-civic-data/issues/87) and the first delivery milestone is [First Wave: Foundation + Core Data](https://github.com/EricGrill/mcp-civic-data/milestone/1). The backlog below reflects the implementation plan staged in GitHub issues.

### First Wave

**Foundation**

- [#48](https://github.com/EricGrill/mcp-civic-data/issues/48) Add comprehensive error handling with fallback sources
- [#47](https://github.com/EricGrill/mcp-civic-data/issues/47) Add intelligent caching for API responses
- [#44](https://github.com/EricGrill/mcp-civic-data/issues/44) Add unit tests for 13 API integrations
- [#45](https://github.com/EricGrill/mcp-civic-data/issues/45) Extend CI/CD toward publishing and release automation

**Core Data Sources**

- [#55](https://github.com/EricGrill/mcp-civic-data/issues/55) Add NOAA radar and forecast discussion tools
- [#54](https://github.com/EricGrill/mcp-civic-data/issues/54) Add FRED economic indicators tools
- [#53](https://github.com/EricGrill/mcp-civic-data/issues/53) Add CDC public health surveillance tools
- [#56](https://github.com/EricGrill/mcp-civic-data/issues/56) Add EPA environmental compliance and site tools
- [#77](https://github.com/EricGrill/mcp-civic-data/issues/77) Add NOAA CO-OPS tides, currents, and coastal flooding tools

### Expansion Backlog

**Civic, Health, and Public Services**

- [#57](https://github.com/EricGrill/mcp-civic-data/issues/57) Add BLS labor statistics tools
- [#61](https://github.com/EricGrill/mcp-civic-data/issues/61) Add FEMA disaster declarations and assistance tools
- [#62](https://github.com/EricGrill/mcp-civic-data/issues/62) Add ClinicalTrials.gov health research tools
- [#63](https://github.com/EricGrill/mcp-civic-data/issues/63) Add USDA Forest Service land and wildfire tools
- [#64](https://github.com/EricGrill/mcp-civic-data/issues/64) Add Bureau of Justice Statistics tools
- [#65](https://github.com/EricGrill/mcp-civic-data/issues/65) Add USDA food and agriculture data tools
- [#68](https://github.com/EricGrill/mcp-civic-data/issues/68) Add SAMHSA mental health and treatment facility tools
- [#71](https://github.com/EricGrill/mcp-civic-data/issues/71) Add NCES education and school district tools
- [#72](https://github.com/EricGrill/mcp-civic-data/issues/72) Add NHTSA traffic safety and crash statistics tools
- [#73](https://github.com/EricGrill/mcp-civic-data/issues/73) Add OSHA workplace safety and enforcement tools
- [#78](https://github.com/EricGrill/mcp-civic-data/issues/78) Add SBA small business and disaster loan tools
- [#80](https://github.com/EricGrill/mcp-civic-data/issues/80) Add FDA recalls, shortages, and safety alert tools
- [#84](https://github.com/EricGrill/mcp-civic-data/issues/84) Add National Park Service parks and alerts tools

**Economics, Finance, and Infrastructure**

- [#49](https://github.com/EricGrill/mcp-civic-data/issues/49) Add composite queries for multi-source data aggregation
- [#59](https://github.com/EricGrill/mcp-civic-data/issues/59) Add EIA energy market and grid tools
- ~~[#75](https://github.com/EricGrill/mcp-civic-data/issues/75) Add CFPB consumer complaint and financial protection tools~~
- [#79](https://github.com/EricGrill/mcp-civic-data/issues/79) Add BTS freight and transportation performance tools
- [#82](https://github.com/EricGrill/mcp-civic-data/issues/82) Add SEC filings and company disclosure tools
- [#83](https://github.com/EricGrill/mcp-civic-data/issues/83) Add BEA regional and national economic accounts tools

### Deferred / High-Complexity Integrations

- [#52](https://github.com/EricGrill/mcp-civic-data/issues/52) Add GTFS transit and mobility tools
- [#58](https://github.com/EricGrill/mcp-civic-data/issues/58) Add FAA airport delay and NAS status tools
- [#60](https://github.com/EricGrill/mcp-civic-data/issues/60) Add HUD housing and homelessness tools
- [#66](https://github.com/EricGrill/mcp-civic-data/issues/66) Add NREL renewable energy and charging tools
- [#67](https://github.com/EricGrill/mcp-civic-data/issues/67) Add USDA NRCS soil, snowpack, and water tools
- [#69](https://github.com/EricGrill/mcp-civic-data/issues/69) Add OpenSecrets campaign finance and lobbying tools
- [#70](https://github.com/EricGrill/mcp-civic-data/issues/70) Add USCIS immigration statistics tools
- [#76](https://github.com/EricGrill/mcp-civic-data/issues/76) Add FCC broadband coverage and internet access tools
- [#81](https://github.com/EricGrill/mcp-civic-data/issues/81) Add FEC election results and committee filing tools
- [#85](https://github.com/EricGrill/mcp-civic-data/issues/85) Add USITC trade and tariff data tools

The backlog is intentionally opinionated: build strong shared foundations first, then layer in the highest-value public data sources, then take on the messy, identifier-heavy, or operations-heavy integrations.

---

## Development

```bash
git clone https://github.com/EricGrill/mcp-civic-data.git
cd mcp-civic-data
python3 -m pip install -e .
python3 -m mcp_govt_api
```

Validation commands:

```bash
python3 -m compileall src
uv run python -m unittest discover -s tests -p "test_*.py"
uv build
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, validation, and pull request guidance.

## Code of Conduct

Contributor expectations are documented in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

Please report vulnerabilities using the process in [SECURITY.md](SECURITY.md).

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <a href="https://github.com/EricGrill/agents-skills-plugins">
    <img src="https://img.shields.io/badge/Part%20of-Claude%20Code%20Plugin%20Marketplace-7c3aed?style=for-the-badge" alt="Plugin Marketplace">
  </a>
</p>
