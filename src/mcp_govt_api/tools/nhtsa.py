from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json
from mcp_govt_api.utils.validation import validate_limit

NHTSA_BASE_URL = "https://api.nhtsa.gov"
VPIC_BASE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles"


@mcp.tool()
async def search_vehicle_recalls(
    make: str = "",
    model: str = "",
    year: str = "",
    limit: int = 10,
) -> str:
    """Search NHTSA vehicle recall campaigns by make, model, and year.

    Queries the NHTSA Recalls API for safety recall information issued by
    manufacturers and the National Highway Traffic Safety Administration.

    Args:
        make: Vehicle manufacturer (e.g., 'Toyota', 'Ford', 'Honda')
        model: Vehicle model (e.g., 'Camry', 'F-150', 'Civic')
        year: Model year (e.g., '2020')
        limit: Maximum number of results to return (default: 10, max: 50)

    Returns:
        List of recall campaigns with NHTSA campaign number, component,
        summary, consequence, and remedy information.
    """
    limit = validate_limit(limit, max_val=50, default=10)

    if not make and not model and not year:
        return "Please provide at least one filter: make, model, or year."

    params: dict[str, str] = {}
    if make:
        params["make"] = make
    if model:
        params["model"] = model
    if year:
        params["modelYear"] = year

    url = f"{NHTSA_BASE_URL}/recalls/recallsByVehicle"

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching recall data: {e}"

    results_list = data.get("results", [])

    if not results_list:
        filters = []
        if make:
            filters.append(f"make '{make}'")
        if model:
            filters.append(f"model '{model}'")
        if year:
            filters.append(f"year '{year}'")
        filter_str = ", ".join(filters)
        return f"No recalls found for {filter_str}."

    total = len(results_list)
    results_list = results_list[:limit]

    lines = [f"NHTSA Vehicle Recalls ({len(results_list)} of {total} total):\n"]

    for r in results_list:
        campaign = r.get("NHTSACampaignNumber", "N/A")
        component = r.get("Component", "Unknown")
        summary = r.get("Summary", "No summary available")
        consequence = r.get("Consequence", "Not specified")
        remedy = r.get("Remedy", "Not specified")
        manufacturer = r.get("Manufacturer", "Unknown")
        report_date = r.get("ReportReceivedDate", "")

        lines.append(f"**Campaign {campaign}**")
        lines.append(f"  Manufacturer: {manufacturer}")
        lines.append(f"  Component: {component}")
        if report_date:
            lines.append(f"  Report Date: {report_date}")
        lines.append(f"  Summary: {summary}")
        lines.append(f"  Consequence: {consequence}")
        lines.append(f"  Remedy: {remedy}")
        lines.append("")

    lines.append(f"\n_Total recalls found: {total}_")
    lines.append("_Source: NHTSA Recalls API_")

    return "\n".join(lines)


@mcp.tool()
async def get_vehicle_complaints(
    make: str = "",
    model: str = "",
    year: str = "",
    limit: int = 10,
) -> str:
    """Get consumer complaints about vehicles from NHTSA.

    Queries the NHTSA Complaints API for consumer-submitted vehicle
    safety complaints, which may lead to investigations and recalls.

    Args:
        make: Vehicle manufacturer (e.g., 'Toyota', 'Ford', 'Honda')
        model: Vehicle model (e.g., 'Camry', 'F-150', 'Civic')
        year: Model year (e.g., '2020')
        limit: Maximum number of results to return (default: 10, max: 50)

    Returns:
        List of consumer complaints with component, description, crash
        and injury information, and investigation details.
    """
    limit = validate_limit(limit, max_val=50, default=10)

    if not make and not model and not year:
        return "Please provide at least one filter: make, model, or year."

    params: dict[str, str] = {}
    if make:
        params["make"] = make
    if model:
        params["model"] = model
    if year:
        params["modelYear"] = year

    url = f"{NHTSA_BASE_URL}/complaints/complaintsByVehicle"

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error fetching complaint data: {e}"

    results_list = data.get("results", [])

    if not results_list:
        filters = []
        if make:
            filters.append(f"make '{make}'")
        if model:
            filters.append(f"model '{model}'")
        if year:
            filters.append(f"year '{year}'")
        filter_str = ", ".join(filters)
        return f"No complaints found for {filter_str}."

    total = len(results_list)
    results_list = results_list[:limit]

    lines = [f"NHTSA Vehicle Complaints ({len(results_list)} of {total} total):\n"]

    for c in results_list:
        odi_number = c.get("odiNumber", "N/A")
        component = c.get("components", "Unknown")
        summary = c.get("summary", "No summary available")
        crash = c.get("crash", "Unknown")
        fire = c.get("fire", "Unknown")
        injuries = c.get("injuries", 0)
        deaths = c.get("deaths", 0)
        date_complaint = c.get("dateComplaintFiled", "")
        date_incident = c.get("dateOfIncident", "")

        lines.append(f"**Complaint {odi_number}**")
        lines.append(f"  Component: {component}")
        if date_complaint:
            lines.append(f"  Date Filed: {date_complaint}")
        if date_incident:
            lines.append(f"  Date of Incident: {date_incident}")
        lines.append(f"  Crash: {crash} | Fire: {fire} | Injuries: {injuries} | Deaths: {deaths}")
        lines.append(f"  Summary: {summary}")
        lines.append("")

    lines.append(f"\n_Total complaints found: {total}_")
    lines.append("_Source: NHTSA Complaints API_")

    return "\n".join(lines)


@mcp.tool()
async def decode_vin(vin: str) -> str:
    """Decode a Vehicle Identification Number (VIN) using the NHTSA vPIC API.

    Returns detailed vehicle specifications including make, model, year,
    body class, engine, drivetrain, and safety features decoded from
    the 17-character VIN.

    Args:
        vin: A 17-character Vehicle Identification Number

    Returns:
        Decoded vehicle information including make, model, year, body class,
        engine type, drivetrain, and other specifications.
    """
    if not vin or not vin.strip():
        return "Please provide a VIN to decode."

    vin = vin.strip().upper()

    if len(vin) != 17:
        return f"Invalid VIN length: expected 17 characters, got {len(vin)}."

    url = f"{VPIC_BASE_URL}/DecodeVinValues/{vin}"
    params = {"format": "json"}

    try:
        data = await fetch_json(url, params=params)
    except Exception as e:
        return f"Error decoding VIN: {e}"

    results = data.get("Results", [])
    if not results:
        return f"No results returned for VIN '{vin}'."

    vehicle = results[0]

    # Check for errors from the API
    error_code = vehicle.get("ErrorCode", "0")
    error_text = vehicle.get("ErrorText", "")
    if error_code and error_code != "0" and "0" not in error_code.split(","):
        return f"VIN decode error: {error_text}"

    # Extract key fields, filtering out empty values
    key_fields = [
        ("Make", "Make"),
        ("Model", "Model"),
        ("Model Year", "ModelYear"),
        ("Body Class", "BodyClass"),
        ("Vehicle Type", "VehicleType"),
        ("Drive Type", "DriveType"),
        ("Engine (Cylinders)", "EngineCylinders"),
        ("Engine (Displacement L)", "DisplacementL"),
        ("Fuel Type - Primary", "FuelTypePrimary"),
        ("Transmission Style", "TransmissionStyle"),
        ("Trim", "Trim"),
        ("Series", "Series"),
        ("Plant City", "PlantCity"),
        ("Plant State", "PlantState"),
        ("Plant Country", "PlantCountry"),
        ("Manufacturer", "Manufacturer"),
        ("GVWR", "GVWR"),
        ("Doors", "Doors"),
        ("Seat Belts Type", "SeatBeltsType"),
        ("Air Bag Locations - Front", "AirBagLocFront"),
        ("Air Bag Locations - Side", "AirBagLocSide"),
        ("TPMS", "TPMS"),
        ("Active Safety - ABS", "ABS"),
        ("Active Safety - ESC", "ESC"),
    ]

    lines = [f"VIN Decode: {vin}\n"]

    for label, field in key_fields:
        value = vehicle.get(field, "")
        if value and value.strip() and value.strip().lower() != "not applicable":
            lines.append(f"  {label}: {value}")

    lines.append("")
    lines.append("_Source: NHTSA vPIC (Vehicle Product Information Catalog)_")

    return "\n".join(lines)
