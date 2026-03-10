from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PropertyType(str, Enum):
    OFFICE = "office"
    RETAIL = "retail"
    INDUSTRIAL = "industrial"
    MULTIFAMILY = "multifamily"
    MIXED_USE = "mixed_use"
    LAND = "land"
    HOSPITALITY = "hospitality"
    SPECIAL_PURPOSE = "special_purpose"


class Property(BaseModel):
    """A commercial real estate property record."""

    parcel_id: str = Field(description="Unique parcel or tax ID")
    address: str
    city: str
    state: str
    zip_code: str
    property_type: PropertyType
    square_feet: Optional[int] = None
    lot_size_acres: Optional[float] = None
    year_built: Optional[int] = None
    num_units: Optional[int] = None
    zoning: Optional[str] = None

    # Ownership
    owner_name: str
    owner_mailing_address: Optional[str] = None
    owner_entity_type: Optional[str] = Field(
        default=None,
        description="LLC, Trust, Individual, Corporation, etc.",
    )

    # Valuation & financials
    assessed_value: Optional[float] = None
    market_value: Optional[float] = None
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[date] = None
    annual_tax: Optional[float] = None

    # Occupancy & income
    occupancy_rate: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="0.0 to 1.0"
    )
    annual_noi: Optional[float] = Field(
        default=None, description="Net operating income"
    )
    cap_rate: Optional[float] = Field(
        default=None, description="Capitalization rate"
    )

    # Listing status
    is_listed: bool = False
    list_price: Optional[float] = None
    days_on_market: Optional[int] = None

    @property
    def price_per_sqft(self) -> Optional[float]:
        if self.market_value and self.square_feet and self.square_feet > 0:
            return self.market_value / self.square_feet
        return None

    @property
    def years_since_last_sale(self) -> Optional[float]:
        if self.last_sale_date:
            delta = date.today() - self.last_sale_date
            return delta.days / 365.25
        return None
