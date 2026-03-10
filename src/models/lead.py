from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OwnerProfile(BaseModel):
    """Aggregated profile of a property owner across their portfolio."""

    name: str
    entity_type: Optional[str] = None
    mailing_address: Optional[str] = None
    total_properties: int = 0
    total_assessed_value: float = 0.0
    total_square_feet: int = 0
    avg_occupancy: Optional[float] = None
    avg_years_held: Optional[float] = None
    property_types: list[str] = Field(default_factory=list)
    markets: list[str] = Field(default_factory=list)


class LeadScore(BaseModel):
    """Scored breakdown for a prospective seller lead."""

    overall: float = Field(ge=0.0, le=100.0, description="Composite score 0-100")
    motivation: float = Field(ge=0.0, le=100.0, description="Likelihood to sell")
    timing: float = Field(ge=0.0, le=100.0, description="Market timing score")
    portfolio_fit: float = Field(
        ge=0.0, le=100.0, description="Fit with buyer criteria"
    )
    deal_size: float = Field(ge=0.0, le=100.0, description="Deal size attractiveness")
    reasons: list[str] = Field(
        default_factory=list,
        description="Human-readable reasons for the score",
    )


class LeadPriority(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class Lead(BaseModel):
    """A scored, actionable seller lead."""

    owner: OwnerProfile
    properties: list[str] = Field(
        description="Parcel IDs of properties associated with this lead"
    )
    score: LeadScore
    priority: LeadPriority = LeadPriority.COLD
    recommended_approach: Optional[str] = None
    ai_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def estimated_portfolio_value(self) -> float:
        return self.owner.total_assessed_value
