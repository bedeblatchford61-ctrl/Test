from __future__ import annotations

import json
import logging
import os

from src.analysis.recommender import Recommender
from src.analysis.scorer import BuyerCriteria, ScoringWeights
from src.config import AgentConfig
from src.models.lead import Lead
from src.models.property import Property
from src.scrapers.listings import ListingsScraper
from src.scrapers.public_records import PublicRecordsScraper

logger = logging.getLogger(__name__)


class CREAgent:
    """Commercial Real Estate AI Agent.

    Orchestrates the full pipeline:
    1. Scrape / load property data from multiple sources
    2. De-duplicate and merge records
    3. Score and rank property owners as potential seller leads
    4. (Optional) Enrich lead summaries via Claude API
    5. Return prioritized, actionable recommendations
    """

    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or AgentConfig()
        self._scrapers = self._init_scrapers()
        self._recommender = self._init_recommender()

    def _init_scrapers(self) -> list:
        scrapers = []
        if self.config.public_records_path:
            scrapers.append(PublicRecordsScraper(data_path=self.config.public_records_path))
        if self.config.listings_path:
            scrapers.append(ListingsScraper(data_path=self.config.listings_path))
        return scrapers

    def _init_recommender(self) -> Recommender:
        weights = ScoringWeights(
            motivation=self.config.weight_motivation,
            timing=self.config.weight_timing,
            portfolio_fit=self.config.weight_portfolio_fit,
            deal_size=self.config.weight_deal_size,
        )
        criteria = BuyerCriteria(
            target_property_types=self.config.property_types,
            min_deal_size=self.config.min_value,
            max_deal_size=self.config.max_value,
            min_cap_rate=self.config.target_cap_rate,
            prefer_value_add=self.config.prefer_value_add,
        )
        return Recommender(weights=weights, criteria=criteria)

    def run(self) -> list[Lead]:
        """Execute the full agent pipeline and return scored leads."""
        logger.info("Starting CRE Agent for %s, %s", self.config.city, self.config.state)

        # 1. Collect data
        all_properties = self._collect_properties()
        if not all_properties:
            logger.warning("No properties found. Check data sources and filters.")
            return []

        # 2. De-duplicate by parcel ID
        properties = self._deduplicate(all_properties)
        logger.info("Collected %d unique properties", len(properties))

        # 3. Score & rank
        leads = self._recommender.generate_leads(properties)

        # 4. AI enrichment
        if self.config.enrich_with_ai:
            leads = self._enrich_leads(leads)

        # 5. Trim to max
        leads = leads[: self.config.max_leads]

        logger.info("Pipeline complete — %d leads generated", len(leads))
        return leads

    def _collect_properties(self) -> list[Property]:
        all_props: list[Property] = []
        for scraper in self._scrapers:
            logger.info("Running scraper: %s", scraper.name)
            try:
                props = scraper.scrape(
                    city=self.config.city,
                    state=self.config.state,
                    property_types=self.config.property_types,
                    min_value=self.config.min_value,
                    max_value=self.config.max_value,
                )
                all_props.extend(props)
                logger.info("  -> %d records from %s", len(props), scraper.name)
            except Exception:
                logger.exception("Scraper %s failed", scraper.name)
        return all_props

    def _deduplicate(self, properties: list[Property]) -> list[Property]:
        seen: dict[str, Property] = {}
        for p in properties:
            existing = seen.get(p.parcel_id)
            if existing is None:
                seen[p.parcel_id] = p
            else:
                # Prefer the record that is listed (has more recent data)
                if p.is_listed and not existing.is_listed:
                    seen[p.parcel_id] = p
        return list(seen.values())

    def _enrich_leads(self, leads: list[Lead]) -> list[Lead]:
        """Use Claude to generate a brief AI summary for each lead."""
        api_key = self.config.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.info("No Anthropic API key found — skipping AI enrichment")
            return leads

        try:
            import anthropic
        except ImportError:
            logger.info("anthropic package not installed — skipping AI enrichment")
            return leads

        client = anthropic.Anthropic(api_key=api_key)

        for lead in leads:
            prompt = self._build_enrichment_prompt(lead)
            try:
                message = client.messages.create(
                    model=self.config.ai_model,
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}],
                )
                lead.ai_summary = message.content[0].text
            except Exception:
                logger.debug("AI enrichment failed for %s", lead.owner.name)

        return leads

    def _build_enrichment_prompt(self, lead: Lead) -> str:
        owner = lead.owner
        return (
            "You are a commercial real estate acquisitions analyst. "
            "Write a 2-3 sentence summary of this seller lead and why they may be a "
            "good target for outreach. Be specific and actionable.\n\n"
            f"Owner: {owner.name}\n"
            f"Entity type: {owner.entity_type or 'Unknown'}\n"
            f"Properties: {owner.total_properties}\n"
            f"Portfolio value: ${owner.total_assessed_value:,.0f}\n"
            f"Property types: {', '.join(owner.property_types)}\n"
            f"Markets: {', '.join(owner.markets)}\n"
            f"Avg occupancy: {owner.avg_occupancy:.0%}" if owner.avg_occupancy else ""
            f"\nAvg years held: {owner.avg_years_held:.1f}" if owner.avg_years_held else ""
            f"\nScore: {lead.score.overall}/100 ({lead.priority.value})\n"
            f"Key signals: {'; '.join(lead.score.reasons[:5])}"
        )

    def leads_to_json(self, leads: list[Lead]) -> str:
        return json.dumps(
            [lead.model_dump(mode="json") for lead in leads],
            indent=2,
            default=str,
        )
