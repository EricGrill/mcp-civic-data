import os
from dataclasses import dataclass


@dataclass
class Config:
    """API configuration from environment variables."""

    openweather_api_key: str | None = None
    nasa_api_key: str | None = None
    timeout: int = 30

    def __post_init__(self):
        self.openweather_api_key = os.environ.get("OPENWEATHER_API_KEY")
        self.nasa_api_key = os.environ.get("NASA_API_KEY")
        self.timeout = int(os.environ.get("API_TIMEOUT", "30"))

    @property
    def has_openweather(self) -> bool:
        return bool(self.openweather_api_key)

    @property
    def has_nasa_key(self) -> bool:
        return bool(self.nasa_api_key)

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
        lines.extend([
            "  ✓ World Bank (no key required)",
            "  ✓ Data.gov (no key required)",
            "  ✓ EU Open Data (no key required)",
            "  ✓ Safecast (no key required)",
            "  ✓ OpenAQ (no key required)",
            "  ✓ USGS Water (no key required)",
            "  ✓ USGS Earthquakes (no key required)",
            "  ✓ NOAA Space Weather (no key required)",
        ])
        if self.has_nasa_key:
            lines.append("  ✓ NASA FIRMS (using NASA API key)")
        else:
            lines.append("  ✓ NASA FIRMS (using DEMO_KEY, limited)")
        return "\n".join(lines)


config = Config()
