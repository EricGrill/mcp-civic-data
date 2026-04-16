from mcp_govt_api.server import mcp
from mcp_govt_api.utils.config import config
from mcp_govt_api.utils.http import fetch_json


FBI_CDE_BASE = "https://api.usa.gov/crime/fbi/cde"


def get_api_key() -> str:
    """Return FBI Crime Data Explorer API key or raise an error if not configured."""
    if not config.fbi_cde_api_key:
        raise ValueError(
            "FBI_CDE_API_KEY is not set. "
            "Get a free key at https://api.data.gov/signup/"
        )
    return config.fbi_cde_api_key


@mcp.tool()
async def get_crime_estimates(
    state: str = "",
    from_year: str = "2019",
    to_year: str = "2023",
) -> str:
    """Get crime estimates by state from the FBI Crime Data Explorer.

    Returns estimated crime statistics including violent crime, property
    crime, robbery, burglary, and more from the FBI Uniform Crime Reporting
    (UCR) program.

    Args:
        state: Two-letter US state abbreviation (e.g., 'CA', 'NY', 'TX').
               If empty, returns national-level estimates.
        from_year: Start year for the data range (default: '2019')
        to_year: End year for the data range (default: '2023')

    Returns:
        Crime estimate data with annual totals by offense type
    """
    try:
        api_key = get_api_key()
    except ValueError as exc:
        return str(exc)

    params = {
        "from": from_year,
        "to": to_year,
        "API_KEY": api_key,
    }

    if state:
        url = f"{FBI_CDE_BASE}/estimate/state/{state.upper()}"
    else:
        url = f"{FBI_CDE_BASE}/estimate/national"

    try:
        data = await fetch_json(url, params=params)
    except Exception as exc:
        location = state.upper() if state else "national"
        return f"Error fetching crime estimates for {location}: {exc}"

    results = data.get("results", data) if isinstance(data, dict) else data
    if not results:
        location = state.upper() if state else "national"
        return f"No crime estimate data found for {location} ({from_year}-{to_year})."

    if isinstance(results, list):
        entries = results
    elif isinstance(results, dict):
        entries = [results]
    else:
        location = state.upper() if state else "national"
        return f"Unexpected response format for {location} crime estimates."

    location = state.upper() if state else "National"
    lines = [f"**Crime Estimates: {location} ({from_year}-{to_year})**\n"]

    for entry in entries:
        year = entry.get("year", "N/A")
        population = entry.get("population", "N/A")

        lines.append(f"**Year: {year}** (Population: {population:,} )"
                      if isinstance(population, (int, float))
                      else f"**Year: {year}** (Population: {population})")

        violent = entry.get("violent_crime", "N/A")
        property_crime = entry.get("property_crime", "N/A")
        murder = entry.get("homicide", entry.get("murder_and_nonnegligent_manslaughter", "N/A"))
        robbery = entry.get("robbery", "N/A")
        assault = entry.get("aggravated_assault", "N/A")
        burglary = entry.get("burglary", "N/A")
        larceny = entry.get("larceny", "N/A")
        motor_theft = entry.get("motor_vehicle_theft", "N/A")

        lines.append(f"  Violent Crime: {violent:,}" if isinstance(violent, (int, float)) else f"  Violent Crime: {violent}")
        lines.append(f"  Property Crime: {property_crime:,}" if isinstance(property_crime, (int, float)) else f"  Property Crime: {property_crime}")
        lines.append(f"  Murder/Manslaughter: {murder:,}" if isinstance(murder, (int, float)) else f"  Murder/Manslaughter: {murder}")
        lines.append(f"  Robbery: {robbery:,}" if isinstance(robbery, (int, float)) else f"  Robbery: {robbery}")
        lines.append(f"  Aggravated Assault: {assault:,}" if isinstance(assault, (int, float)) else f"  Aggravated Assault: {assault}")
        lines.append(f"  Burglary: {burglary:,}" if isinstance(burglary, (int, float)) else f"  Burglary: {burglary}")
        lines.append(f"  Larceny: {larceny:,}" if isinstance(larceny, (int, float)) else f"  Larceny: {larceny}")
        lines.append(f"  Motor Vehicle Theft: {motor_theft:,}" if isinstance(motor_theft, (int, float)) else f"  Motor Vehicle Theft: {motor_theft}")
        lines.append("")

    lines.append("_Source: FBI Crime Data Explorer (UCR)_")
    return "\n".join(lines)


@mcp.tool()
async def get_arrest_data(
    offense: str = "",
    from_year: str = "2019",
    to_year: str = "2023",
) -> str:
    """Get national arrest data from the FBI Crime Data Explorer.

    Returns arrest statistics from the FBI Uniform Crime Reporting (UCR)
    program, broken down by offense type. Covers all reported arrests
    from participating law enforcement agencies.

    Args:
        offense: Offense category filter (e.g., 'aggravated-assault',
                 'burglary', 'robbery', 'drug-abuse', 'dui',
                 'larceny'). If empty, returns total arrest data.
        from_year: Start year for the data range (default: '2019')
        to_year: End year for the data range (default: '2023')

    Returns:
        Arrest data with annual totals and breakdowns
    """
    try:
        api_key = get_api_key()
    except ValueError as exc:
        return str(exc)

    params = {
        "from": from_year,
        "to": to_year,
        "API_KEY": api_key,
    }

    if offense:
        url = f"{FBI_CDE_BASE}/arrest/national/{offense}"
    else:
        url = f"{FBI_CDE_BASE}/arrest/national"

    try:
        data = await fetch_json(url, params=params)
    except Exception as exc:
        offense_str = offense if offense else "all offenses"
        return f"Error fetching arrest data for {offense_str}: {exc}"

    results = data.get("results", data) if isinstance(data, dict) else data
    if not results:
        offense_str = offense if offense else "all offenses"
        return f"No arrest data found for {offense_str} ({from_year}-{to_year})."

    if isinstance(results, list):
        entries = results
    elif isinstance(results, dict):
        entries = [results]
    else:
        offense_str = offense if offense else "all offenses"
        return f"Unexpected response format for {offense_str} arrest data."

    offense_label = offense.replace("-", " ").title() if offense else "All Offenses"
    lines = [f"**National Arrest Data: {offense_label} ({from_year}-{to_year})**\n"]

    for entry in entries:
        year = entry.get("year", entry.get("data_year", "N/A"))

        lines.append(f"**Year: {year}**")

        total = entry.get("total_arrests", entry.get("value", "N/A"))
        if isinstance(total, (int, float)):
            lines.append(f"  Total Arrests: {total:,}")
        elif total != "N/A":
            lines.append(f"  Total Arrests: {total}")

        male = entry.get("male", "")
        female = entry.get("female", "")
        if male or female:
            if isinstance(male, (int, float)):
                lines.append(f"  Male: {male:,}")
            if isinstance(female, (int, float)):
                lines.append(f"  Female: {female:,}")

        juvenile = entry.get("juvenile", "")
        adult = entry.get("adult", "")
        if juvenile or adult:
            if isinstance(adult, (int, float)):
                lines.append(f"  Adult: {adult:,}")
            if isinstance(juvenile, (int, float)):
                lines.append(f"  Juvenile: {juvenile:,}")

        for key, val in entry.items():
            if key not in ("year", "data_year", "total_arrests", "value",
                           "male", "female", "juvenile", "adult",
                           "month", "month_num"):
                if isinstance(val, (int, float)) and val > 0:
                    label = key.replace("_", " ").title()
                    lines.append(f"  {label}: {val:,}")
        lines.append("")

    lines.append("_Source: FBI Crime Data Explorer (UCR)_")
    return "\n".join(lines)


@mcp.tool()
async def search_crime_datasets(query: str = "") -> str:
    """Search available crime and justice datasets from Data.gov.

    Searches the federal open data catalog for crime, justice, and
    law enforcement datasets. Useful for finding data beyond what the
    FBI Crime Data Explorer provides, including Bureau of Justice
    Statistics (BJS) reports and other DOJ datasets.

    Args:
        query: Search keywords (e.g., 'prisoner statistics',
               'recidivism', 'victimization', 'hate crime',
               'law enforcement'). If empty, returns recent
               crime/justice datasets.

    Returns:
        List of matching datasets with titles, descriptions, and download links
    """
    search_query = f"crime justice {query}".strip() if query else "crime justice statistics"

    params = {
        "q": search_query,
        "rows": "10",
    }

    try:
        data = await fetch_json(
            "https://catalog.data.gov/api/3/action/package_search",
            params=params,
        )
    except Exception as exc:
        return f"Error searching crime/justice datasets: {exc}"

    results = data.get("result", {}).get("results", [])
    total = data.get("result", {}).get("count", 0)

    if not results:
        return f"No crime/justice datasets found for '{query or 'general'}'."

    lines = [f"**Crime & Justice Dataset Search: '{query or 'general'}'**\n"]
    lines.append(f"Found {total} total datasets (showing {len(results)})\n")

    for ds in results:
        title = ds.get("title", "Untitled")
        org = ds.get("organization", {}).get("title", "N/A")
        notes = ds.get("notes", "")
        if len(notes) > 300:
            notes = notes[:300] + "..."

        resources = ds.get("resources", [])
        formats = set()
        download_url = ""
        for r in resources:
            fmt = r.get("format", "").upper()
            if fmt:
                formats.add(fmt)
            if not download_url and r.get("url"):
                download_url = r["url"]

        lines.append(f"**{title}**")
        lines.append(f"  Organization: {org}")
        if notes:
            lines.append(f"  Description: {notes}")
        if formats:
            lines.append(f"  Formats: {', '.join(sorted(formats))}")
        if download_url:
            lines.append(f"  URL: {download_url}")
        lines.append("")

    lines.append("_Source: Data.gov (CKAN)_")
    return "\n".join(lines)
