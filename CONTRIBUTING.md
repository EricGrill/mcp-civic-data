# Contributing to mcp-civic-data

Thanks for contributing. This project adds MCP tools on top of public civic and government data APIs, so changes should stay small, readable, and easy to validate against upstream API behavior.

## What to Contribute

- New data sources that fit the project's focus on public, authoritative data
- Fixes for broken endpoints, response formatting, or configuration handling
- Documentation improvements, examples, and setup clarifications
- Small refactors that make tool modules easier to maintain

For larger changes, open an issue first so the scope, API choice, and tool shape are clear before implementation starts.

## Local Setup

Clone the repository and install the package in editable mode.

```bash
git clone https://github.com/EricGrill/mcp-civic-data.git
cd mcp-civic-data
python3 -m pip install -e .
```

If you use `uv`, you can sync from the lockfile instead:

```bash
uv sync
```

Optional environment variables:

```bash
cp .env.example .env
export OPENWEATHER_API_KEY=...
export NASA_API_KEY=...
export API_TIMEOUT=30
```

Run the server locally with:

```bash
python3 -m mcp_govt_api
```

## Project Layout

- `src/mcp_govt_api/server.py` defines the MCP server and registers tool modules
- `src/mcp_govt_api/tools/` contains one module per data source or domain
- `src/mcp_govt_api/utils/config.py` reads environment-based configuration
- `src/mcp_govt_api/utils/http.py` centralizes async HTTP access

Prefer adding new API integrations as focused modules under `src/mcp_govt_api/tools/` and reusing shared config and HTTP helpers instead of duplicating request logic.

## Contribution Expectations

- Keep pull requests focused on one change set
- Update `README.md` when user-facing behavior, setup, or tool coverage changes
- Do not commit API keys, tokens, or other secrets
- Preserve the existing package/module naming unless there is a strong migration reason
- Favor clear tool descriptions and predictable return formats over clever abstractions

## Validation

Before opening a pull request, run the checks this repository currently relies on:

```bash
python3 -m compileall src
uv run python -m unittest discover -s tests -p "test_*.py"
uv build
```

When changing runtime behavior, also start the server locally and exercise the affected tool path against the upstream API you touched.

## Pull Requests

Pull requests should include:

- A short description of the change
- Why the change is needed
- Any config or API-key implications
- Notes about how the change was validated

If the change adds a new data source, include the upstream API documentation link in the PR description.
