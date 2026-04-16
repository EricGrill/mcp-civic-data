"""SEC EDGAR API tools for company filings and disclosures."""

import time

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import http_client

SEC_BASE = "https://data.sec.gov"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# In-memory cache for ticker-to-CIK mapping
_ticker_cache: dict[str, dict] = {}  # ticker -> {"cik": str, "name": str}
_ticker_cache_time: float = 0.0
_CACHE_TTL = 3600  # Refresh cache every hour


def _pad_cik(cik: str) -> str:
    """Pad CIK to 10 digits with leading zeros."""
    return cik.zfill(10)


async def _load_ticker_cache() -> None:
    """Fetch the SEC company tickers JSON and populate the cache.

    The SEC endpoint returns a JSON object keyed by index, each entry
    containing ``cik_str``, ``ticker``, and ``title``.  We build a
    dictionary keyed by upper-case ticker for O(1) lookups.
    """
    global _ticker_cache, _ticker_cache_time

    now = time.monotonic()
    if _ticker_cache and (now - _ticker_cache_time) < _CACHE_TTL:
        return  # Cache is still fresh

    headers = {"User-Agent": "mcp-civic-data/0.1.0"}
    response = await http_client.get(TICKERS_URL, headers=headers)
    response.raise_for_status()
    data = response.json()

    new_cache: dict[str, dict] = {}
    for entry in data.values():
        ticker_key = str(entry.get("ticker", "")).upper()
        if ticker_key:
            new_cache[ticker_key] = {
                "cik": str(entry.get("cik_str", "")),
                "name": entry.get("title", ""),
            }

    _ticker_cache = new_cache
    _ticker_cache_time = now


async def _resolve_ticker(ticker: str) -> dict | None:
    """Resolve a ticker symbol to its CIK and company name.

    Returns a dict with ``cik`` and ``name`` keys, or ``None`` if the
    ticker is not found.  The lookup is case-insensitive.
    """
    await _load_ticker_cache()
    return _ticker_cache.get(ticker.upper())


@mcp.tool()
async def get_company_filings(ticker: str = "", cik: str = "") -> str:
    """Get company filings from SEC EDGAR.

    Args:
        ticker: Company ticker symbol (e.g., 'AAPL', 'MSFT')
        cik: Company CIK number (alternative to ticker)

    Returns:
        Recent SEC filings for the company including 10-K, 10-Q, 8-K forms
    """
    if not ticker and not cik:
        return "Error: Please provide either a ticker symbol or CIK number."

    try:
        # Resolve ticker to CIK if needed
        if ticker and not cik:
            resolved = await _resolve_ticker(ticker)
            if resolved is None:
                return (
                    f"Error: Ticker '{ticker.upper()}' not found in SEC database.\n"
                    f"Please verify the ticker symbol or provide a CIK number directly.\n"
                    f"You can search for CIK numbers at: "
                    f"https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK={ticker.upper()}&type=&dateb=&owner=include&count=40&search_text=&action=getcompany"
                )
            cik = resolved["cik"]

        # Use provided CIK
        cik_padded = _pad_cik(cik)
        submissions_url = f"{SEC_BASE}/submissions/CIK{cik_padded}.json"
        headers = {"User-Agent": "mcp-civic-data/0.1.0"}

        response = await http_client.get(submissions_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Extract company info
        company_name = data.get("name", "Unknown Company")
        cik_number = data.get("cik", cik)

        # Get recent filings
        recent_filings = data.get("filings", {}).get("recent", {})
        forms = recent_filings.get("form", [])
        dates = recent_filings.get("filingDate", [])
        descriptions = recent_filings.get("primaryDocDescription", [])
        accessions = recent_filings.get("accessionNumber", [])

        # Build response
        result = [f"**SEC Filings for {company_name}**\n"]
        result.append(f"CIK: {cik_number}\n")

        # Show up to 15 most recent filings
        count = min(len(forms), 15)
        if count == 0:
            result.append("No recent filings found.")
        else:
            result.append(f"**Recent Filings (showing {count}):**\n")
            for i in range(count):
                form = forms[i] if i < len(forms) else "N/A"
                date = dates[i] if i < len(dates) else "N/A"
                desc = descriptions[i] if i < len(descriptions) else ""
                accession = accessions[i] if i < len(accessions) else ""

                result.append(f"- **{form}** ({date})")
                if desc:
                    result.append(f"  {desc}")
                if accession:
                    result.append(f"  Accession: {accession}")
                result.append("")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching SEC filings: {str(e)}"


@mcp.tool()
async def search_company(name: str = "", ticker: str = "") -> str:
    """Search for a company by name or ticker symbol.

    Args:
        name: Company name (e.g., 'Apple Inc')
        ticker: Ticker symbol (e.g., 'AAPL')

    Returns:
        Company information including CIK number
    """
    if not name and not ticker:
        return "Error: Please provide either a company name or ticker symbol."

    try:
        if ticker:
            resolved = await _resolve_ticker(ticker)
            if resolved is not None:
                cik_str = resolved["cik"]
                company_name = resolved["name"]
                cik_padded = _pad_cik(cik_str)
                return (
                    f"**Company Found: {company_name}**\n\n"
                    f"Ticker: {ticker.upper()}\n"
                    f"CIK: {cik_str}\n\n"
                    f"Use this CIK with:\n"
                    f"- `get_company_filings(cik=\"{cik_str}\")` for recent filings\n"
                    f"- `get_latest_submissions(cik=\"{cik_str}\")` for submissions\n"
                    f"- `get_company_facts(cik=\"{cik_str}\")` for financial data\n\n"
                    f"EDGAR page: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_padded}&type=&dateb=&owner=include&count=40"
                )
            else:
                return (
                    f"Error: Ticker '{ticker.upper()}' not found in SEC database.\n"
                    f"Please verify the ticker symbol or try searching by company name."
                )

        if name:
            # Search the ticker cache for matching company names
            await _load_ticker_cache()
            name_lower = name.lower()
            matches: list[dict] = []
            for tick, info in _ticker_cache.items():
                if name_lower in info["name"].lower():
                    matches.append({"ticker": tick, **info})
                if len(matches) >= 10:
                    break

            if matches:
                result = [f"**Company Search Results for: {name}**\n"]
                for m in matches:
                    result.append(
                        f"- **{m['name']}** | Ticker: {m['ticker']} | CIK: {m['cik']}"
                    )
                result.append(
                    f"\nUse the CIK number with `get_company_filings` or `get_latest_submissions`."
                )
                return "\n".join(result)
            else:
                return (
                    f"**No results found for: {name}**\n\n"
                    f"Try a different search term, or search directly:\n"
                    f"https://www.sec.gov/cgi-bin/browse-edgar?company={name}&CIK=&type=&dateb=&owner=include&count=40&search_text=&action=getcompany"
                )

    except Exception as e:
        return f"Error searching for company: {str(e)}"

    return "Error: Please provide either a company name or ticker symbol."


@mcp.tool()
async def get_latest_submissions(cik: str, form_type: str = "") -> str:
    """Get latest submissions/filings for a company by CIK.

    Args:
        cik: Company CIK number (required)
        form_type: Filter by form type (e.g., '10-K', '10-Q', '8-K', 'DEF 14A')

    Returns:
        Recent SEC submissions with links to documents
    """
    if not cik:
        return "Error: CIK number is required."

    try:
        cik_padded = _pad_cik(cik)
        submissions_url = f"{SEC_BASE}/submissions/CIK{cik_padded}.json"
        headers = {"User-Agent": "mcp-civic-data/0.1.0"}

        response = await http_client.get(submissions_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        company_name = data.get("name", "Unknown Company")
        cik_number = data.get("cik", cik)

        # Get all filings
        recent_filings = data.get("filings", {}).get("recent", {})
        forms = recent_filings.get("form", [])
        dates = recent_filings.get("filingDate", [])
        descriptions = recent_filings.get("primaryDocDescription", [])
        accessions = recent_filings.get("accessionNumber", [])

        # Filter by form type if specified
        filtered_indices = []
        form_filter = form_type.upper() if form_type else ""

        for i, form in enumerate(forms):
            if not form_filter or form == form_filter:
                filtered_indices.append(i)

        # Build response
        result = [f"**Latest SEC Submissions for {company_name}**\n"]
        result.append(f"CIK: {cik_number}\n")

        if form_type:
            result.append(f"**Filtered by Form Type: {form_type.upper()}**\n")

        # Show up to 20 filings
        count = min(len(filtered_indices), 20)
        if count == 0:
            if form_type:
                result.append(f"No {form_type.upper()} filings found for this company.")
            else:
                result.append("No recent filings found.")
        else:
            result.append(f"**Showing {count} submission(s):**\n")
            for idx in filtered_indices[:20]:
                form = forms[idx] if idx < len(forms) else "N/A"
                date = dates[idx] if idx < len(dates) else "N/A"
                desc = descriptions[idx] if idx < len(descriptions) else ""
                accession = accessions[idx] if idx < len(accessions) else ""

                # Build EDGAR filing URL
                if accession:
                    accession_clean = accession.replace("-", "")
                    cik_int = int(cik_number) if cik_number.isdigit() else cik_number
                    edgar_url = (
                        f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_clean}/{accession}-index.htm"
                    )
                else:
                    edgar_url = ""

                result.append(f"**{form}** - {date}")
                if desc:
                    result.append(f"  Description: {desc}")
                if edgar_url:
                    result.append(f"  Filing: {edgar_url}")
                result.append("")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching submissions: {str(e)}"


@mcp.tool()
async def get_company_facts(cik: str) -> str:
    """Get company facts and financial data from SEC.

    Args:
        cik: Company CIK number (required)

    Returns:
        Company facts including financial metrics
    """
    if not cik:
        return "Error: CIK number is required."

    try:
        cik_padded = _pad_cik(cik)
        facts_url = f"{SEC_BASE}/api/xbrl/companyfacts/CIK{cik_padded}.json"
        headers = {"User-Agent": "mcp-civic-data/0.1.0"}

        response = await http_client.get(facts_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        entity_name = data.get("entityName", "Unknown Company")
        cik_number = data.get("cik", cik)

        facts = data.get("facts", {})

        result = [f"**Company Facts for {entity_name}**\n"]
        result.append(f"CIK: {cik_number}\n")

        # Show available fact categories
        result.append("**Available Financial Data Categories:**\n")
        for taxonomy, concepts in facts.items():
            concept_count = len(concepts)
            result.append(f"- {taxonomy}: {concept_count} concepts")

        result.append("\n**Common Financial Metrics Available:**")
        result.append("- Assets, Liabilities, Stockholders' Equity")
        result.append("- Net Income, Revenue, Operating Income")
        result.append("- Cash and Cash Equivalents")
        result.append("- Earnings Per Share (EPS)")
        result.append("- Current Assets, Current Liabilities")

        result.append("\nFor detailed financials, visit:\n")
        result.append(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json")

        return "\n".join(result)

    except Exception as e:
        return f"Error fetching company facts: {str(e)}"


@mcp.tool()
async def query_sec_edgar(endpoint: str, params: dict | None = None) -> dict:
    """Make a raw query to the SEC EDGAR API.

    Args:
        endpoint: API endpoint path (e.g., 'submissions/CIK0000320193.json')
        params: Optional query parameters

    Returns:
        Raw JSON response from SEC EDGAR API
    """
    url = f"{SEC_BASE}/{endpoint}"
    headers = {"User-Agent": "mcp-civic-data/0.1.0"}

    response = await http_client.get(url, params=params or {}, headers=headers)
    response.raise_for_status()
    return response.json()
