from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.models.lead import LeadScore, OwnerProfile
from src.models.property import Property

logger = logging.getLogger(__name__)


@dataclass
class ScoringWeights:
    """Configurable weights for each scoring dimension."""

    motivation: float = 0.35
    timing: float = 0.20
    portfolio_fit: float = 0.25
    deal_size: float = 0.20


@dataclass
class BuyerCriteria:
    """What the buyer (you) is looking for."""

    target_property_types: list[str] = field(default_factory=lambda: ["office", "retail", "industrial"])
    min_deal_size: float = 500_000
    max_deal_size: float = 50_000_000
    target_markets: list[str] = field(default_factory=lambda: [])
    min_cap_rate: float = 0.05
    prefer_value_add: bool = True


class LeadScorer:
    """Scores property owners on their likelihood and attractiveness as sellers."""

    def __init__(
        self,
        weights: ScoringWeights | None = None,
        criteria: BuyerCriteria | None = None,
    ) -> None:
        self.weights = weights or ScoringWeights()
        self.criteria = criteria or BuyerCriteria()

    def score(self, owner: OwnerProfile, properties: list[Property]) -> LeadScore:
        motivation = self._score_motivation(owner, properties)
        timing = self._score_timing(properties)
        portfolio_fit = self._score_portfolio_fit(owner, properties)
        deal_size = self._score_deal_size(owner, properties)

        reasons: list[str] = []
        reasons.extend(motivation[1])
        reasons.extend(timing[1])
        reasons.extend(portfolio_fit[1])
        reasons.extend(deal_size[1])

        w = self.weights
        overall = (
            w.motivation * motivation[0]
            + w.timing * timing[0]
            + w.portfolio_fit * portfolio_fit[0]
            + w.deal_size * deal_size[0]
        )

        return LeadScore(
            overall=round(min(overall, 100.0), 1),
            motivation=round(motivation[0], 1),
            timing=round(timing[0], 1),
            portfolio_fit=round(portfolio_fit[0], 1),
            deal_size=round(deal_size[0], 1),
            reasons=reasons,
        )

    def _score_motivation(
        self, owner: OwnerProfile, properties: list[Property]
    ) -> tuple[float, list[str]]:
        """Estimate seller motivation based on ownership signals."""
        score = 30.0  # baseline
        reasons = []

        # Long hold period suggests potential motivation to exit
        if owner.avg_years_held is not None:
            if owner.avg_years_held > 15:
                score += 30
                reasons.append(f"Long hold period ({owner.avg_years_held:.0f}+ years) — may be ready to exit")
            elif owner.avg_years_held > 8:
                score += 15
                reasons.append(f"Moderate hold period ({owner.avg_years_held:.0f} years)")

        # Low occupancy signals distress
        if owner.avg_occupancy is not None:
            if owner.avg_occupancy < 0.6:
                score += 25
                reasons.append(f"Low occupancy ({owner.avg_occupancy:.0%}) — potential distress")
            elif owner.avg_occupancy < 0.8:
                score += 10
                reasons.append(f"Below-market occupancy ({owner.avg_occupancy:.0%})")

        # Individual owners more likely to sell than institutions
        if owner.entity_type and owner.entity_type.lower() in ("individual", "trust"):
            score += 10
            reasons.append(f"Owner type ({owner.entity_type}) — often more motivated")

        # Properties already listed
        listed = [p for p in properties if p.is_listed]
        if listed:
            score += 20
            reasons.append(f"{len(listed)} property(ies) currently listed")

        return min(score, 100.0), reasons

    def _score_timing(self, properties: list[Property]) -> tuple[float, list[str]]:
        """Score market timing signals."""
        score = 40.0
        reasons = []

        # Stale listings
        stale = [p for p in properties if p.days_on_market and p.days_on_market > 180]
        if stale:
            score += 25
            reasons.append(f"{len(stale)} listing(s) on market 180+ days — seller may be flexible")

        # High cap rates relative to target
        high_cap = [
            p
            for p in properties
            if p.cap_rate and p.cap_rate > self.criteria.min_cap_rate + 0.02
        ]
        if high_cap:
            score += 15
            reasons.append("Above-target cap rate — attractive entry point")

        # Recent tax increases (assessed value much higher than last sale)
        for p in properties:
            if (
                p.assessed_value
                and p.last_sale_price
                and p.assessed_value > p.last_sale_price * 1.5
            ):
                score += 15
                reasons.append("Assessed value significantly above last sale — rising tax burden")
                break

        return min(score, 100.0), reasons

    def _score_portfolio_fit(
        self, owner: OwnerProfile, properties: list[Property]
    ) -> tuple[float, list[str]]:
        """How well does this opportunity match buyer criteria?"""
        score = 20.0
        reasons = []

        # Property type match
        matching_types = set(owner.property_types) & set(self.criteria.target_property_types)
        if matching_types:
            score += 30
            reasons.append(f"Property types match target: {', '.join(matching_types)}")

        # Market match
        if self.criteria.target_markets:
            matching_markets = set(owner.markets) & set(self.criteria.target_markets)
            if matching_markets:
                score += 20
                reasons.append(f"Located in target market(s): {', '.join(matching_markets)}")

        # Value-add opportunity
        if self.criteria.prefer_value_add and owner.avg_occupancy is not None:
            if owner.avg_occupancy < 0.85:
                score += 20
                reasons.append("Value-add opportunity — below-stabilized occupancy")

        return min(score, 100.0), reasons

    def _score_deal_size(
        self, owner: OwnerProfile, properties: list[Property]
    ) -> tuple[float, list[str]]:
        """Score based on deal size alignment with buyer range."""
        score = 20.0
        reasons = []

        total_value = owner.total_assessed_value
        if total_value == 0:
            return score, ["Insufficient valuation data"]

        min_d, max_d = self.criteria.min_deal_size, self.criteria.max_deal_size
        if min_d <= total_value <= max_d:
            score += 60
            reasons.append(f"Portfolio value (${total_value:,.0f}) within target range")
        elif total_value < min_d:
            score += 20
            reasons.append(f"Portfolio value (${total_value:,.0f}) below target minimum")
        else:
            score += 30
            reasons.append(f"Portfolio value (${total_value:,.0f}) above target max — partial acquisition possible")

        return min(score, 100.0), reasons
