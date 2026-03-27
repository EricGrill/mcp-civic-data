# Contributing to MCP Civic Data

Thank you for your interest in contributing to MCP Civic Data! This MCP server provides access to free government and open data APIs.

## Overview

MCP Civic Data is a Model Context Protocol (MCP) server that enables AI assistants to access various civic data sources including NOAA, Census, World Bank, and more.

## Quick Start

### Prerequisites

- Python 3.11+
- uv (recommended) or pip

### Setup

```bash
# Clone the repository
git clone https://github.com/EricGrill/mcp-civic-data.git
cd mcp-civic-data

# Install dependencies with uv
uv sync

# Or with pip
pip install -e .

# Copy environment file
cp .env.example .env
```

### Running the Server

```bash
# With uv
uv run python -m mcp_govt_api

# Or after pip install
python -m mcp_govt_api
```

## How to Contribute

### Reporting Issues

- Check existing issues first
- Include Python version and OS
- Provide steps to reproduce
- Include error messages and logs

### Adding New Data Sources

1. Create an adapter in `src/mcp_govt_api/adapters/`
2. Follow the existing adapter pattern
3. Add tests
4. Update documentation
5. Submit a PR

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to public functions
- Keep functions focused and testable

## Development Workflow

1. Fork the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```
3. Make your changes
4. Run tests:
   ```bash
   uv run pytest
   ```
5. Submit a pull request

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_specific.py
```

## Adding a New Data Source

### 1. Create Adapter

```python
# src/mcp_govt_api/adapters/my_source.py
from typing import Any
import httpx

class MySourceAdapter:
    """Adapter for My Source API."""
    
    BASE_URL = "https://api.mysource.gov"
    
    async def fetch_data(self, endpoint: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}/{endpoint}")
            response.raise_for_status()
            return response.json()
```

### 2. Add Tools

Register your adapter's methods as MCP tools in the server module.

### 3. Document

- Add to README.md
- Include example usage
- Document required API keys

## Documentation

- Keep README.md updated
- Add inline code comments
- Update this file for process changes

## Pull Request Guidelines

- Clear description of changes
- Link related issues
- Ensure tests pass
- Update documentation
- Follow existing code patterns

## Code of Conduct

Be respectful, welcoming, and helpful to all contributors.

## Questions?

Open an issue or start a discussion.

Thank you for improving MCP Civic Data!
