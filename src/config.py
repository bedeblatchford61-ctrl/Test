from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """Top-level configuration for the CRE agent."""

    # Target market
    city: str = "Austin"
    state: str = "TX"

    # Property filters
    property_types: list[str] = field(
        default_factory=lambda: ["office", "retail", "industrial", "multifamily"]
    )
    min_value: float = 500_000
    max_value: float = 50_000_000

    # Data source paths (set to None to skip a source)
    public_records_path: str | None = "data/sample_properties.json"
    listings_path: str | None = "data/sample_listings.json"

    # Scoring weights (must sum to ~1.0)
    weight_motivation: float = 0.35
    weight_timing: float = 0.20
    weight_portfolio_fit: float = 0.25
    weight_deal_size: float = 0.20

    # Buyer criteria
    target_cap_rate: float = 0.05
    prefer_value_add: bool = True

    # AI enrichment
    anthropic_api_key: str | None = None
    ai_model: str = "claude-sonnet-4-6"
    enrich_with_ai: bool = True

    # Output
    max_leads: int = 25
    output_format: str = "table"  # "table" or "json"
