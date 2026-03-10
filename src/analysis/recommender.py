from __future__ import annotations

import logging
from collections import defaultdict

from src.analysis.scorer import BuyerCriteria, LeadScorer, ScoringWeights
from src.models.lead import Lead, LeadPriority, OwnerProfile
from src.models.property import Property

logger = logging.getLogger(__name__)

# Priority thresholds
HOT_THRESHOLD = 70.0
WARM_THRESHOLD = 45.0


class Recommender:
    """Aggregates properties by owner, scores them, and produces ranked leads."""

    def __init__(
        self,
        weights: ScoringWeights | None = None,
        criteria: BuyerCriteria | None = None,
    ) -> None:
        self.scorer = LeadScorer(weights=weights, criteria=criteria)

    def generate_leads(self, properties: list[Property]) -> list[Lead]:
        """Group properties by owner, score, and return ranked leads."""
        owner_groups = self._group_by_owner(properties)
        leads: list[Lead] = []

        for owner_name, props in owner_groups.items():
            profile = self._build_owner_profile(owner_name, props)
            score = self.scorer.score(profile, props)

            if score.overall >= HOT_THRESHOLD:
                priority = LeadPriority.HOT
            elif score.overall >= WARM_THRESHOLD:
                priority = LeadPriority.WARM
            else:
                priority = LeadPriority.COLD

            approach = self._suggest_approach(priority, profile, props)

            leads.append(
                Lead(
                    owner=profile,
                    properties=[p.parcel_id for p in props],
                    score=score,
                    priority=priority,
                    recommended_approach=approach,
                )
            )

        leads.sort(key=lambda l: l.score.overall, reverse=True)
        logger.info(
            "Generated %d leads: %d hot, %d warm, %d cold",
            len(leads),
            sum(1 for l in leads if l.priority == LeadPriority.HOT),
            sum(1 for l in leads if l.priority == LeadPriority.WARM),
            sum(1 for l in leads if l.priority == LeadPriority.COLD),
        )
        return leads

    def _group_by_owner(self, properties: list[Property]) -> dict[str, list[Property]]:
        groups: dict[str, list[Property]] = defaultdict(list)
        for prop in properties:
            groups[prop.owner_name].append(prop)
        return dict(groups)

    def _build_owner_profile(self, name: str, props: list[Property]) -> OwnerProfile:
        total_assessed = sum(p.assessed_value or 0 for p in props)
        total_sqft = sum(p.square_feet or 0 for p in props)
        occupancies = [p.occupancy_rate for p in props if p.occupancy_rate is not None]
        hold_years = [p.years_since_last_sale for p in props if p.years_since_last_sale is not None]
        prop_types = list({p.property_type.value for p in props})
        markets = list({f"{p.city}, {p.state}" for p in props})

        entity_type = None
        mailing_address = None
        for p in props:
            if p.owner_entity_type:
                entity_type = p.owner_entity_type
            if p.owner_mailing_address:
                mailing_address = p.owner_mailing_address

        return OwnerProfile(
            name=name,
            entity_type=entity_type,
            mailing_address=mailing_address,
            total_properties=len(props),
            total_assessed_value=total_assessed,
            total_square_feet=total_sqft,
            avg_occupancy=sum(occupancies) / len(occupancies) if occupancies else None,
            avg_years_held=sum(hold_years) / len(hold_years) if hold_years else None,
            property_types=prop_types,
            markets=markets,
        )

    def _suggest_approach(
        self, priority: LeadPriority, owner: OwnerProfile, props: list[Property]
    ) -> str:
        listed = [p for p in props if p.is_listed]

        if priority == LeadPriority.HOT:
            if listed:
                return (
                    "Direct outreach — property already listed. Contact listing broker "
                    "or reach out to owner directly with a competitive offer based on "
                    "comparable sales analysis."
                )
            return (
                "High-priority off-market approach. Send personalized letter highlighting "
                "market conditions and your track record with similar properties. "
                "Follow up with a phone call within 7 days."
            )

        if priority == LeadPriority.WARM:
            return (
                "Relationship-building outreach. Introduce yourself and express interest "
                "in the market area. Provide a free property valuation as a conversation "
                "starter. Nurture over 2-4 weeks before making an offer."
            )

        return (
            "Add to long-term nurture list. Monitor for changes in occupancy, "
            "listing status, or ownership. Re-evaluate quarterly."
        )
