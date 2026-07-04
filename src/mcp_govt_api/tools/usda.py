from mcp_govt_api.server import mcp
from mcp_govt_api.utils.config import config
from mcp_govt_api.utils.http import fetch_json

FDC_BASE = "https://api.nal.usda.gov/fdc/v1"
NASS_BASE = "https://quickstats.nass.usda.gov/api"


def _require_key() -> str:
    """Return the USDA API key or raise an error."""
    if not config.usda_api_key:
        raise ValueError(
            "USDA_API_KEY environment variable is not set. "
            "Get a free key at https://fdc.nal.usda.gov/api-key-signup.html"
        )
    return config.usda_api_key


@mcp.tool()
async def search_usda_foods(
    query: str,
    limit: int = 10,
) -> str:
    """Search USDA FoodData Central for nutritional information on foods.

    Args:
        query: Food to search for (e.g., 'apple', 'cheddar cheese', 'chicken breast').
        limit: Number of results to return (default 10, max 50).

    Returns:
        Matching foods with basic nutritional data and FDC IDs for detail lookup.
    """
    try:
        api_key = _require_key()
    except ValueError as exc:
        return str(exc)

    url = f"{FDC_BASE}/foods/search"
    params = {
        "api_key": api_key,
        "query": query,
        "pageSize": str(min(limit, 50)),
    }

    try:
        data = await fetch_json(url, params=params)
    except Exception as exc:
        return f"Error searching FoodData Central: {exc}"

    foods = data.get("foods", [])
    total = data.get("totalHits", 0)

    if not foods:
        return f"No foods found matching '{query}'."

    lines = [f"**USDA FoodData Central — '{query}'** ({total} total results)\n"]

    for food in foods:
        fdc_id = food.get("fdcId", "N/A")
        description = food.get("description", "Unknown")
        data_type = food.get("dataType", "")
        brand = food.get("brandOwner", "")

        parts = [f"  - **{description}**"]
        if brand:
            parts[0] += f" ({brand})"
        parts.append(f"FDC ID: {fdc_id}")
        if data_type:
            parts.append(f"Type: {data_type}")

        nutrients = food.get("foodNutrients", [])
        nutrient_strs = []
        for n in nutrients:
            name = n.get("nutrientName", "")
            value = n.get("value")
            unit = n.get("unitName", "")
            if name and value is not None and name in (
                "Energy",
                "Protein",
                "Total lipid (fat)",
                "Carbohydrate, by difference",
                "Fiber, total dietary",
            ):
                nutrient_strs.append(f"{name}: {value} {unit}")
        if nutrient_strs:
            parts.append(" | ".join(nutrient_strs))

        lines.append(" | ".join(parts[:3]))
        if nutrient_strs:
            lines.append(f"    {' | '.join(nutrient_strs)}")

    return "\n".join(lines)


@mcp.tool()
async def get_food_details(
    fdc_id: int,
) -> str:
    """Get detailed nutrition data for a specific food from USDA FoodData Central.

    Args:
        fdc_id: FoodData Central ID (get from search_usda_foods results).

    Returns:
        Comprehensive nutritional information including calories, macros, vitamins, and minerals.
    """
    try:
        api_key = _require_key()
    except ValueError as exc:
        return str(exc)

    url = f"{FDC_BASE}/food/{fdc_id}"
    params = {"api_key": api_key}

    try:
        data = await fetch_json(url, params=params)
    except Exception as exc:
        return f"Error fetching food details: {exc}"

    description = data.get("description", "Unknown Food")
    data_type = data.get("dataType", "")
    brand = data.get("brandOwner", "")
    ingredients = data.get("ingredients", "")
    serving = data.get("servingSize")
    serving_unit = data.get("servingSizeUnit", "")

    lines = [f"**{description}**"]
    if brand:
        lines.append(f"Brand: {brand}")
    if data_type:
        lines.append(f"Data Type: {data_type}")
    if serving is not None:
        lines.append(f"Serving Size: {serving} {serving_unit}")
    if ingredients:
        lines.append(f"Ingredients: {ingredients}")

    nutrients = data.get("foodNutrients", [])
    if nutrients:
        lines.append("\n**Nutrients (per 100g):**")
        for n in nutrients:
            nutrient_info = n.get("nutrient", {})
            name = nutrient_info.get("name", n.get("nutrientName", ""))
            unit = nutrient_info.get("unitName", n.get("unitName", ""))
            amount = n.get("amount", n.get("value"))
            if name and amount is not None:
                lines.append(f"  - {name}: {amount} {unit}")

    return "\n".join(lines)


@mcp.tool()
async def get_crop_data(
    commodity: str = "",
    state: str = "",
    year: str = "",
    limit: int = 10,
) -> str:
    """Get USDA NASS crop production, acreage, and yield data.

    Args:
        commodity: Crop name (e.g., 'CORN', 'SOYBEANS', 'WHEAT'). Case-insensitive.
        state: Two-letter state code (e.g., 'IA', 'IL'). Leave empty for national data.
        year: Year for data (e.g., '2023'). Leave empty for most recent.
        limit: Number of records to return (default 10).

    Returns:
        Crop production statistics including acreage, yield, and production volume.
    """
    try:
        api_key = _require_key()
    except ValueError as exc:
        return str(exc)

    url = f"{NASS_BASE}/api_GET/"
    params: dict = {
        "key": api_key,
        "format": "JSON",
    }
    if commodity:
        params["commodity_desc"] = commodity.upper()
    if state:
        params["state_alpha"] = state.upper()
    if year:
        params["year"] = year
    # Focus on key statistics
    params["statisticcat_desc"] = "PRODUCTION"

    try:
        data = await fetch_json(url, params=params)
    except Exception as exc:
        return f"Error fetching NASS crop data: {exc}"

    records = data.get("data", [])

    if not records:
        parts = []
        if commodity:
            parts.append(commodity.upper())
        if state:
            parts.append(state.upper())
        if year:
            parts.append(year)
        label = ", ".join(parts) if parts else "the given criteria"
        return f"No crop data found for {label}."

    # Limit results
    records = records[:limit]

    title_parts = ["**USDA NASS Crop Data**"]
    if commodity:
        title_parts[0] = f"**USDA NASS — {commodity.upper()}**"
    if state:
        title_parts.append(f"State: {state.upper()}")
    if year:
        title_parts.append(f"Year: {year}")

    lines = [" | ".join(title_parts) + "\n"]

    for rec in records:
        rec_commodity = rec.get("commodity_desc", "")
        rec_year = rec.get("year", "")
        rec_state = rec.get("state_alpha", rec.get("state_name", ""))
        stat_cat = rec.get("statisticcat_desc", "")
        short_desc = rec.get("short_desc", "")
        value = rec.get("Value", "N/A")
        unit = rec.get("unit_desc", "")

        entry = f"  - **{rec_commodity}** ({rec_year}, {rec_state})"
        if stat_cat:
            entry += f" | {stat_cat}"
        entry += f": {value} {unit}"
        if short_desc and short_desc != rec_commodity:
            entry += f"\n    _{short_desc}_"

        lines.append(entry)

    return "\n".join(lines)
