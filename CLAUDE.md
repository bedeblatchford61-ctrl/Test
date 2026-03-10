# CLAUDE.md

This file provides guidance for AI assistants (including Claude) working in this repository.

## Project Overview

**Commercial Real Estate AI Agent** — a Python application that collects commercial property data from multiple sources, scores property owners on their likelihood and attractiveness as sellers, and produces prioritized, actionable lead recommendations.

The agent pipeline:
1. Scrape/load property data (public records, listing platforms)
2. De-duplicate and merge records
3. Build owner profiles across their portfolio
4. Score leads on motivation, timing, portfolio fit, and deal size
5. (Optional) Enrich summaries via Claude API
6. Output ranked recommendations with suggested outreach approaches

## Repository Structure

```
/
├── CLAUDE.md                  # AI assistant guidance (this file)
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
├── src/
│   ├── agent.py               # Main CREAgent orchestrator
│   ├── config.py              # AgentConfig dataclass
│   ├── models/
│   │   ├── property.py        # Property and PropertyType models (Pydantic)
│   │   └── lead.py            # Lead, LeadScore, OwnerProfile models
│   ├── scrapers/
│   │   ├── base.py            # BaseScraper abstract class
│   │   ├── public_records.py  # County assessor / public records scraper
│   │   └── listings.py        # Commercial listing platform scraper
│   └── analysis/
│       ├── scorer.py          # LeadScorer with configurable weights
│       └── recommender.py     # Recommender — groups, scores, ranks leads
├── data/
│   ├── sample_properties.json # Sample public records (Austin, TX)
│   └── sample_listings.json   # Sample listings data (Austin, TX)
└── tests/
    ├── test_models.py
    ├── test_scorer.py
    ├── test_recommender.py
    └── test_scrapers.py
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with sample data (table output)
python main.py --city Austin --state TX

# Run without AI enrichment
python main.py --no-ai

# JSON output
python main.py --format json --no-ai

# Verbose logging
python main.py -v --no-ai
```

## Development Workflow

### Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

All tests must pass before pushing. The test suite covers models, scoring logic, the recommendation engine, and scrapers.

### Adding a New Data Source

1. Create a new scraper in `src/scrapers/` that extends `BaseScraper`
2. Implement the `scrape()` method returning `list[Property]`
3. Register it in `CREAgent._init_scrapers()` in `src/agent.py`
4. Add corresponding config fields to `src/config.py`

### Modifying Scoring Logic

Scoring weights and buyer criteria are configurable via `ScoringWeights` and `BuyerCriteria` in `src/analysis/scorer.py`. The four scoring dimensions are:
- **Motivation** (35%) — hold period, occupancy, entity type, listing status
- **Timing** (20%) — days on market, cap rate, tax burden signals
- **Portfolio fit** (25%) — property type match, market match, value-add potential
- **Deal size** (20%) — alignment with buyer's target acquisition range

### Branch Conventions

- **Main branch**: `main`
- **Feature branches**: Descriptive names prefixed by category (`feature/`, `fix/`, `docs/`)
- Keep commits atomic and well-described

### Commit Messages

Follow conventional commit style:

```
<type>: <short summary>

<optional body with more detail>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`, `ci`

## Key Technical Decisions

- **Pydantic** for data models — provides validation, serialization, and clear schemas
- **Rich** for CLI table output — readable terminal formatting
- **Anthropic SDK** (optional) for AI-powered lead summaries
- Scrapers use a local-JSON fallback pattern: production subclasses call external APIs, base implementations read from `data/` files
- All configuration flows through `AgentConfig` dataclass — no scattered env var reads

## Environment Variables

| Variable | Purpose | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API key for AI lead enrichment | No (agent works without it) |

## Code Conventions

1. **Keep changes minimal** — only modify what is necessary for the task
2. **Read before writing** — understand existing code before making changes
3. **No over-engineering** — solve the current problem, not hypothetical future ones
4. **Preserve existing patterns** — follow conventions already in the codebase
5. **Type hints everywhere** — use `from __future__ import annotations` at top of modules
6. **Pydantic for data** — all data structures that cross module boundaries should be Pydantic models
7. **Never commit secrets** — use environment variables for API keys and credentials

## Security

- Never commit API keys or credentials
- The `ANTHROPIC_API_KEY` must come from environment variables, never hardcoded
- Validate all external input at system boundaries
- Sample data files contain only fictional property records
