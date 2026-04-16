from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json
from mcp_govt_api.utils.config import config


EIA_BASE = "https://api.eia.gov/v2"


def _require_key() -> str:
    """Return the EIA API key or raise an error."""
    if not config.eia_api_key:
        raise ValueError(
            "EIA_API_KEY environment variable is not set. "
            "Get a free key at https://www.eia.gov/opendata/register.php"
        )
    return config.eia_api_key


@mcp.tool()
async def get_electricity_data(
    state: str = "",
    frequency: str = "monthly",
    limit: int = 12,
) -> str:
    """Get retail electricity sales and price data by state from the EIA.

    Args:
        state: Two-letter state code (e.g., 'CA', 'TX'). Leave empty for national data.
        frequency: Data frequency — 'monthly', 'quarterly', or 'annual'.
        limit: Number of records to return (default 12).

    Returns:
        Electricity retail sales data including revenue and price information.
    """
    try:
        api_key = _require_key()
    except ValueError as exc:
        return str(exc)

    url = f"{EIA_BASE}/electricity/retail-sales/data/"
    params: dict = {
        "api_key": api_key,
        "frequency": frequency,
        "data[0]": "revenue",
        "data[1]": "sales",
        "data[2]": "price",
        "data[3]": "customers",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": str(limit),
    }
    if state:
        params["facets[stateid][]"] = state.upper()

    try:
        data = await fetch_json(url, params=params)
    except Exception as exc:
        return f"Error fetching electricity data: {exc}"

    response = data.get("response", {})
    records = response.get("data", [])

    if not records:
        label = state.upper() if state else "US"
        return f"No electricity data found for {label} ({frequency})."

    label = state.upper() if state else "US (National)"
    lines = [f"**Electricity Retail Sales — {label}** ({frequency})\n"]

    for rec in records:
        period = rec.get("period", "N/A")
        sector = rec.get("sectorName", "")
        revenue = rec.get("revenue")
        sales = rec.get("sales")
        price = rec.get("price")
        customers = rec.get("customers")

        parts = [f"  - **{period}** | {sector}"]
        if price is not None:
            parts.append(f"Price: {price} cents/kWh")
        if revenue is not None:
            parts.append(f"Revenue: ${revenue:,}k" if isinstance(revenue, (int, float)) else f"Revenue: {revenue}")
        if sales is not None:
            parts.append(f"Sales: {sales:,} MWh" if isinstance(sales, (int, float)) else f"Sales: {sales}")
        if customers is not None:
            parts.append(f"Customers: {customers:,}" if isinstance(customers, (int, float)) else f"Customers: {customers}")

        lines.append(" | ".join(parts))

    total = response.get("total", "")
    if total:
        lines.append(f"\n_{total} total records available._")

    return "\n".join(lines)


@mcp.tool()
async def get_petroleum_prices(
    product: str = "gasoline",
    frequency: str = "weekly",
    limit: int = 12,
) -> str:
    """Get petroleum product prices from the EIA.

    Args:
        product: Product type — 'gasoline', 'diesel', or 'heating_oil'.
        frequency: Data frequency — 'weekly', 'monthly', or 'annual'.
        limit: Number of records to return (default 12).

    Returns:
        Petroleum price data for the requested product.
    """
    try:
        api_key = _require_key()
    except ValueError as exc:
        return str(exc)

    product_map = {
        "gasoline": ("petroleum/pri/gnd/data/", "EMM_EPMR_PTE_NUS_DPG"),
        "diesel": ("petroleum/pri/gnd/data/", "EMM_EPDR_PTE_NUS_DPG"),
        "heating_oil": ("petroleum/pri/wfr/data/", None),
    }

    route, series_id = product_map.get(product.lower(), product_map["gasoline"])
    url = f"{EIA_BASE}/{route}"

    params: dict = {
        "api_key": api_key,
        "frequency": frequency,
        "data[0]": "value",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": str(limit),
    }
    if series_id:
        params["facets[series][]"] = series_id

    try:
        data = await fetch_json(url, params=params)
    except Exception as exc:
        return f"Error fetching petroleum prices: {exc}"

    response = data.get("response", {})
    records = response.get("data", [])

    if not records:
        return f"No petroleum price data found for {product} ({frequency})."

    lines = [f"**Petroleum Prices — {product.title()}** ({frequency})\n"]

    for rec in records:
        period = rec.get("period", "N/A")
        value = rec.get("value")
        series_name = rec.get("series-description", rec.get("seriesDescription", ""))
        area = rec.get("areaName", "")
        unit = rec.get("units", rec.get("unit", "$/gal"))

        price_str = f"${value:.3f}" if isinstance(value, (int, float)) else str(value) if value else "N/A"
        desc = series_name or area or product.title()
        lines.append(f"  - **{period}** | {desc}: {price_str} {unit}")

    total = response.get("total", "")
    if total:
        lines.append(f"\n_{total} total records available._")

    return "\n".join(lines)


@mcp.tool()
async def get_energy_overview(
    category: str = "electricity",
) -> str:
    """Get available EIA data categories and routes for exploration.

    Args:
        category: Top-level category to explore. Options include 'electricity',
                  'petroleum', 'natural-gas', 'coal', 'nuclear-outages',
                  'state-energy-data', 'total-energy', or '' for the root directory.

    Returns:
        Available data routes and descriptions within the selected category.
    """
    try:
        api_key = _require_key()
    except ValueError as exc:
        return str(exc)

    if category:
        url = f"{EIA_BASE}/{category}"
    else:
        url = EIA_BASE

    params = {"api_key": api_key}

    try:
        data = await fetch_json(url, params=params)
    except Exception as exc:
        return f"Error fetching EIA categories: {exc}"

    response = data.get("response", {})
    routes = response.get("routes", [])
    name = response.get("name", category or "EIA Data")
    description = response.get("description", "")

    if not routes:
        return f"No sub-categories found for '{category}'. Try '' for the root directory."

    lines = [f"**{name}**"]
    if description:
        lines.append(f"_{description}_\n")
    else:
        lines.append("")

    for route in routes:
        route_id = route.get("id", "")
        route_name = route.get("name", "")
        route_desc = route.get("description", "")
        lines.append(f"  - **{route_id}**: {route_name}")
        if route_desc:
            lines.append(f"    _{route_desc}_")

    return "\n".join(lines)
