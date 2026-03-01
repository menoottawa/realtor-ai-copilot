# realtor-ai-copilot

AI-powered research and packet-generation assistant for buyer's agents — ingests MLS/IDX data,
scores listings against buyer profiles, produces explainable analyses, and auto-builds
client-ready presentations.

## Features

- **MLS Data Ingestion**: Load listing data from CSV or JSON files exported by any MLS/IDX feed
- **Buyer Profile Matching**: Score and rank listings against buyer criteria (price, beds, location, etc.)
- **AI Analysis**: Generate agent-facing narrative analyses using OpenAI GPT models
- **PDF Reports**: Auto-build polished, client-ready PDF presentation packets

## Quick Start

```bash
# Install
pip install -e .

# Set your OpenAI API key (optional — analysis degrades gracefully without it)
export OPENAI_API_KEY="sk-..."

# Run against sample data
realtor-ai --listings data/sample_listings.csv \
               --profile data/sample_profile.json \
               --output report.pdf
```

## Project Structure

```
src/realtor_ai_copilot/
├── models.py          # Pydantic data models (Listing, BuyerProfile, MatchResult)
├── ingestion/         # MLS data loaders (CSV, JSON)
├── matching/          # Scoring / ranking engine
├── analysis/          # OpenAI-powered narrative generator
├── reports/           # ReportLab PDF builder
└── main.py            # Typer CLI entry-point
```

## Configuration

Copy `.env.example` to `.env` and fill in your OpenAI API key:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

## Development

```bash
# Lint
ruff check src tests

# Format
ruff format src tests
```
