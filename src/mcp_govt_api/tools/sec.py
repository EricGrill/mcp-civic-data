"""SEC EDGAR API tools for company filings and disclosures."""

from mcp_govt_api.server import mcp
from mcp_govt_api.utils.http import http_client


SEC_BASE = "https://data.sec.gov"
CIK_LOOKUP_URL = "https://www.sec.gov/cgi-bin/browse-edgar"


def _pad_cik(cik: str) -> str:
    """Pad CIK to 10 digits with leading zeros."""
    return cik.zfill(10)


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
        # Get company data using ticker or CIK
        if ticker:
            # First, lookup CIK from ticker
            ticker_upper = ticker.upper()
            lookup_url = f"{SEC_BASE}/submissions/CIK0000000000.json"
            headers = {"User-Agent": "mcp-civic-data/0.1.0"}
            
            # Try to get from ticker-CIK mapping via submissions endpoint
            # First we need to find the CIK from the ticker
            submissions_data = None
            
            # Use a public ticker-to-CIK lookup approach via SEC submissions
            sub_url = f"{SEC_BASE}/submissions/CIK0000000000.json"
            response = await http_client.get(sub_url, headers=headers)
            
            # If that doesn't work, try company facts with a search approach
            # For now, we'll need user to provide CIK for reliable lookup
            return (
                f"To look up {ticker}, please use the CIK number.\n"
                f"You can find CIK numbers at: https://www.sec.gov/edgar/searchedgar/cik"
            )
        
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
                
                # Build EDGAR link
                accession_clean = accession.replace("-", "")
                edgar_link = f"https://www.sec.gov/Archives/edgar/data/{cik_number}/{accession_clean}"
                
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
        # Note: SEC doesn't have a direct search API for company names
        # We'll provide guidance on how to find CIK numbers
        
        if ticker:
            ticker_upper = ticker.upper()
            return (
                f"**Company Search for Ticker: {ticker_upper}**\n\n"
                f"To find the CIK for {ticker_upper}:\n"
                f"1. Visit: https://www.sec.gov/edgar/searchedgar/cik\n"
                f"2. Enter ticker: {ticker_upper}\n"
                f"3. Use the CIK number with `get_company_filings` or `get_latest_submissions`\n\n"
                f"Alternatively, visit:\n"
                f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker_upper}&type=&dateb=&owner=include&count=40"
            )
        
        if name:
            return (
                f"**Company Search for: {name}**\n\n"
                f"To find the CIK for '{name}':\n"
                f"1. Visit: https://www.sec.gov/edgar/searchedgar/cik\n"
                f"2. Search for: {name}\n"
                f"3. Use the CIK number with `get_company_filings` or `get_latest_submissions`\n\n"
                f"Alternatively, use the SEC company search:\n"
                f"https://www.sec.gov/edgar/searchedgar/companysearch"
            )
            
    except Exception as e:
        return f"Error searching for company: {str(e)}"


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
                    edgar_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_clean}/{accession}-index.htm"
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
        
        result.append(f"\nFor detailed financials, visit:\n")
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
