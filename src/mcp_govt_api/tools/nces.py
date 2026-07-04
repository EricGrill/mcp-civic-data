from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import fetch_json

NCES_BASE = "https://educationdata.urban.org/api/v1"


@mcp.tool()
async def search_school_districts(
    state: str = "",
    name: str = "",
    year: str = "2022",
    limit: int = 10,
) -> str:
    """Search for school districts by state or name using NCES data.

    Args:
        state: State name to filter by (e.g., 'California', 'Texas')
        name: District name to search for (e.g., 'Los Angeles')
        year: School year (default: '2022')
        limit: Maximum number of results (default: 10)

    Returns:
        List of matching school districts with location and enrollment info
    """
    try:
        params: dict[str, str | int] = {"limit": limit}
        if state:
            params["state_name"] = state
        if name:
            params["lea_name"] = name

        url = f"{NCES_BASE}/schools/ccd/directory/{year}/"
        data = await fetch_json(url, params=params)

        results = data.get("results", [])
        if not results:
            return "No school districts found matching your search criteria."

        output = [f"**School District Search Results** ({len(results)} results)\n"]

        for district in results:
            lea_name = district.get("lea_name", "Unknown")
            state_name = district.get("state_name", "N/A")
            city = district.get("city_location", "N/A")
            enrollment = district.get("enrollment", "N/A")
            phone = district.get("phone", "N/A")
            zip_code = district.get("zip_location", "N/A")
            leaid = district.get("leaid", "N/A")

            output.append(
                f"**{lea_name}**\n"
                f"State: {state_name}\n"
                f"City: {city}, {zip_code}\n"
                f"Enrollment: {enrollment}\n"
                f"Phone: {phone}\n"
                f"LEA ID: {leaid}"
            )

        return "\n\n---\n\n".join(output)
    except Exception as e:
        return f"Error searching school districts: {e}"


@mcp.tool()
async def get_school_enrollment(
    state: str = "",
    district: str = "",
    year: str = "2022",
    limit: int = 10,
) -> str:
    """Get school enrollment data by state or district using NCES data.

    Args:
        state: State name to filter by (e.g., 'California', 'Texas')
        district: District name to filter by (e.g., 'Los Angeles Unified')
        year: School year (default: '2022')
        limit: Maximum number of results (default: 10)

    Returns:
        School enrollment data including grade-level breakdowns
    """
    try:
        params: dict[str, str | int] = {"limit": limit}
        if state:
            params["state_name"] = state
        if district:
            params["lea_name"] = district

        url = f"{NCES_BASE}/schools/ccd/enrollment/{year}/"
        data = await fetch_json(url, params=params)

        results = data.get("results", [])
        if not results:
            return "No enrollment data found matching your search criteria."

        output = [f"**School Enrollment Data** ({len(results)} results)\n"]

        for school in results:
            school_name = school.get("school_name", "Unknown")
            state_name = school.get("state_name", "N/A")
            enrollment = school.get("enrollment", "N/A")
            grade = school.get("grade", "N/A")
            lea_name = school.get("lea_name", "N/A")
            race = school.get("race", "N/A")
            sex = school.get("sex", "N/A")

            output.append(
                f"**{school_name}**\n"
                f"District: {lea_name}\n"
                f"State: {state_name}\n"
                f"Grade: {grade}\n"
                f"Enrollment: {enrollment}\n"
                f"Race: {race} | Sex: {sex}"
            )

        return "\n\n---\n\n".join(output)
    except Exception as e:
        return f"Error fetching school enrollment: {e}"


@mcp.tool()
async def search_colleges(
    state: str = "",
    name: str = "",
    limit: int = 10,
) -> str:
    """Search for colleges and universities using NCES IPEDS data.

    Args:
        state: State name to filter by (e.g., 'California', 'New York')
        name: Institution name to search for (e.g., 'Stanford', 'MIT')
        limit: Maximum number of results (default: 10)

    Returns:
        List of matching colleges/universities with location and type info
    """
    try:
        params: dict[str, str | int] = {"limit": limit}
        if state:
            params["state_name"] = state
        if name:
            params["inst_name"] = name

        url = f"{NCES_BASE}/college-university/ipeds/directory/2022/"
        data = await fetch_json(url, params=params)

        results = data.get("results", [])
        if not results:
            return "No colleges found matching your search criteria."

        output = [f"**College/University Search Results** ({len(results)} results)\n"]

        for college in results:
            inst_name = college.get("inst_name", "Unknown")
            state_name = college.get("state_name", "N/A")
            city = college.get("city", "N/A")
            zip_code = college.get("zip", "N/A")
            inst_level = college.get("inst_level", "N/A")
            inst_control = college.get("inst_control", "N/A")
            hbcu = college.get("hbcu", 0)
            unitid = college.get("unitid", "N/A")

            hbcu_label = "Yes" if hbcu == 1 else "No"

            output.append(
                f"**{inst_name}**\n"
                f"Location: {city}, {state_name} {zip_code}\n"
                f"Level: {inst_level}\n"
                f"Control: {inst_control}\n"
                f"HBCU: {hbcu_label}\n"
                f"Unit ID: {unitid}"
            )

        return "\n\n---\n\n".join(output)
    except Exception as e:
        return f"Error searching colleges: {e}"
