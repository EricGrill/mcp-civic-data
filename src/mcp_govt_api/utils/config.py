import os
from dataclasses import dataclass


@dataclass
class Config:
    """API configuration from environment variables."""

    openweather_api_key: str | None = None
    nasa_api_key: str | None = None
    fred_api_key: str | None = None
    bls_api_key: str | None = None
    nps_api_key: str | None = None
    eia_api_key: str | None = None
    bea_api_key: str | None = None
    usda_api_key: str | None = None
    timeout: int = 30
    cache_enabled: bool = True
    cache_ttl: int = 300
    log_level: str = "INFO"

    def __post_init__(self):
        self.openweather_api_key = os.environ.get("OPENWEATHER_API_KEY")
        self.nasa_api_key = os.environ.get("NASA_API_KEY")
        self.fred_api_key = os.environ.get("FRED_API_KEY")
        self.bls_api_key = os.environ.get("BLS_API_KEY")
        self.nps_api_key = os.environ.get("NPS_API_KEY")
        self.eia_api_key = os.environ.get("EIA_API_KEY")
        self.bea_api_key = os.environ.get("BEA_API_KEY")
        self.usda_api_key = os.environ.get("USDA_API_KEY")
        self.timeout = int(os.environ.get("API_TIMEOUT", "30"))
        self.cache_enabled = os.environ.get(
            "CACHE_ENABLED", "true"
        ).lower() in ("true", "1", "yes")
        self.cache_ttl = int(os.environ.get("CACHE_TTL", "300"))
        self.log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    @property
    def has_openweather(self) -> bool:
        return bool(self.openweather_api_key)

    @property
    def has_nasa_key(self) -> bool:
        return bool(self.nasa_api_key)

    @property
    def has_fred(self) -> bool:
        return bool(self.fred_api_key)

    @property
    def has_bls(self) -> bool:
        return bool(self.bls_api_key)

    @property
    def has_nps(self) -> bool:
        return bool(self.nps_api_key)

    @property
    def has_eia(self) -> bool:
        return bool(self.eia_api_key)

    @property
    def has_bea(self) -> bool:
        return bool(self.bea_api_key)

    @property
    def has_usda(self) -> bool:
        return bool(self.usda_api_key)

    def get_availability_summary(self) -> str:
        """Return a summary of API availability."""
        lines = [
            "API Availability:",
            "  ✓ NOAA (no key required)",
            "  ✓ Census (no key required)",
        ]
        if self.has_nasa_key:
            lines.append("  ✓ NASA (using API key for higher limits)")
        else:
            lines.append("  ✓ NASA (no key, limited to 30 req/hour)")
        if self.has_openweather:
            lines.append("  ✓ OpenWeather (API key configured)")
        else:
            lines.append("  ✗ OpenWeather (OPENWEATHER_API_KEY not set)")
        lines.extend(
            [
                "  ✓ World Bank (no key required)",
                "  ✓ Data.gov (no key required)",
                "  ✓ EU Open Data (no key required)",
                "  ✓ Safecast (no key required)",
                "  ✓ OpenAQ (no key required)",
                "  ✓ USGS Water (no key required)",
                "  ✓ USGS Earthquakes (no key required)",
                "  ✓ NOAA Space Weather (no key required)",
                "  ✓ SEC EDGAR (no key required)",
                "  ✓ CISA (no key required)",
            ]
        )
        if self.has_fred:
            lines.append("  ✓ FRED (API key configured)")
        else:
            lines.append("  ✗ FRED (FRED_API_KEY not set)")
        if self.has_bls:
            lines.append("  ✓ BLS (using API key for higher limits)")
        else:
            lines.append("  ✓ BLS (no key, limited to 25 queries/day)")
        if self.has_nps:
            lines.append("  ✓ NPS (API key configured)")
        else:
            lines.append("  ✗ NPS (NPS_API_KEY not set)")
        if self.has_eia:
            lines.append("  ✓ EIA (API key configured)")
        else:
            lines.append("  ✗ EIA (EIA_API_KEY not set)")
        if self.has_bea:
            lines.append("  ✓ BEA (API key configured)")
        else:
            lines.append("  ✗ BEA (BEA_API_KEY not set)")
        if self.has_usda:
            lines.append("  ✓ USDA (API key configured)")
        else:
            lines.append("  ✗ USDA (USDA_API_KEY not set)")
        if self.has_nasa_key:
            lines.append("  ✓ NASA FIRMS (using NASA API key)")
        else:
            lines.append("  ✓ NASA FIRMS (using DEMO_KEY, limited)")
        return "\n".join(lines)


config = Config()
