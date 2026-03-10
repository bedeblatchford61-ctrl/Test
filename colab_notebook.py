########################################################################
# COMMERCIAL REAL ESTATE AI AGENT — Google Colab Version
#
# INSTRUCTIONS:
# 1. Go to https://colab.research.google.com on your iPad
# 2. Sign in with your Google account
# 3. Click "New Notebook"
# 4. Delete any code already in the first cell
# 5. Copy-paste this ENTIRE file into that cell
# 6. Tap the Play ▶ button on the left side of the cell
# 7. Scroll down to see your results!
#
# To use YOUR OWN data: scroll down to the SAMPLE DATA section
# and replace the fake properties with real ones from your market.
########################################################################

# --- Install dependencies ---
!pip install -q pydantic rich

from datetime import date, datetime
from enum import Enum
from typing import Optional
from collections import defaultdict
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table

console = Console()

# =====================================================================
# CONFIGURATION — CHANGE THESE TO MATCH YOUR TARGET MARKET
# =====================================================================

TARGET_CITY = "Austin"
TARGET_STATE = "TX"
MIN_DEAL_SIZE = 500_000       # Minimum property value you're interested in
MAX_DEAL_SIZE = 50_000_000    # Maximum property value you're interested in
TARGET_PROPERTY_TYPES = ["office", "retail", "industrial", "multifamily"]
TARGET_CAP_RATE = 0.05        # Minimum cap rate you want
PREFER_VALUE_ADD = True       # Prefer properties with upside potential?

# =====================================================================
# SAMPLE DATA — REPLACE THIS WITH YOUR REAL PROPERTIES
# =====================================================================
# Each property is a dictionary. Copy this format for your own data.
# At minimum you need: address, city, state, zip_code, property_type,
# owner_name. Everything else is optional but improves scoring.
#
# property_type must be one of:
#   "office", "retail", "industrial", "multifamily",
#   "mixed_use", "land", "hospitality", "special_purpose"
# =====================================================================

PROPERTIES_DATA = [
    {
        "parcel_id": "TC-001",
        "address": "1200 Congress Ave",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "property_type": "office",
        "square_feet": 45000,
        "year_built": 1985,
        "owner_name": "Lone Star Office Holdings LLC",
        "owner_mailing_address": "PO Box 4521, Austin, TX 78765",
        "owner_entity_type": "LLC",
        "assessed_value": 8500000,
        "market_value": 9200000,
        "last_sale_price": 4200000,
        "last_sale_date": "2008-06-15",
        "occupancy_rate": 0.62,
        "cap_rate": 0.046,
        "is_listed": False,
    },
    {
        "parcel_id": "TC-002",
        "address": "3400 S Lamar Blvd",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78704",
        "property_type": "retail",
        "square_feet": 18000,
        "year_built": 1992,
        "owner_name": "Margaret Chen",
        "owner_mailing_address": "5600 Balcones Dr, Austin, TX 78731",
        "owner_entity_type": "Individual",
        "assessed_value": 3200000,
        "market_value": 3800000,
        "last_sale_price": 1100000,
        "last_sale_date": "2003-09-22",
        "occupancy_rate": 0.55,
        "cap_rate": 0.038,
        "is_listed": False,
    },
    {
        "parcel_id": "TC-003",
        "address": "7800 Shoal Creek Blvd",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78757",
        "property_type": "industrial",
        "square_feet": 72000,
        "year_built": 1978,
        "owner_name": "Barton Creek Industrial Trust",
        "owner_mailing_address": "Suite 200, 1100 Guadalupe St, Austin, TX 78701",
        "owner_entity_type": "Trust",
        "assessed_value": 5800000,
        "market_value": 6500000,
        "last_sale_price": 2800000,
        "last_sale_date": "2005-03-10",
        "occupancy_rate": 0.78,
        "cap_rate": 0.058,
        "is_listed": False,
    },
    {
        "parcel_id": "TC-004",
        "address": "500 E Riverside Dr",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78704",
        "property_type": "multifamily",
        "square_feet": 95000,
        "num_units": 120,
        "year_built": 1995,
        "owner_name": "Riverside Apartments LP",
        "owner_mailing_address": "2200 Colorado St, Austin, TX 78701",
        "owner_entity_type": "LLC",
        "assessed_value": 18500000,
        "market_value": 22000000,
        "last_sale_price": 12500000,
        "last_sale_date": "2015-11-01",
        "occupancy_rate": 0.91,
        "cap_rate": 0.057,
        "is_listed": False,
    },
    {
        "parcel_id": "TC-005",
        "address": "2100 E 6th St",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78702",
        "property_type": "retail",
        "square_feet": 28000,
        "num_units": 12,
        "year_built": 1960,
        "owner_name": "Margaret Chen",
        "owner_mailing_address": "5600 Balcones Dr, Austin, TX 78731",
        "owner_entity_type": "Individual",
        "assessed_value": 4100000,
        "market_value": 5200000,
        "last_sale_price": 850000,
        "last_sale_date": "1999-04-18",
        "occupancy_rate": 0.72,
        "cap_rate": 0.04,
        "is_listed": True,
        "list_price": 5500000,
        "days_on_market": 280,
    },
    {
        "parcel_id": "TC-006",
        "address": "800 Brazos St",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "property_type": "office",
        "square_feet": 55000,
        "year_built": 1990,
        "owner_name": "Downtown Realty Ventures Inc",
        "owner_mailing_address": "800 Brazos St #100, Austin, TX 78701",
        "owner_entity_type": "Corporation",
        "assessed_value": 11200000,
        "market_value": 12800000,
        "last_sale_price": 7500000,
        "last_sale_date": "2012-04-15",
        "occupancy_rate": 0.58,
        "cap_rate": 0.038,
        "is_listed": True,
        "list_price": 13500000,
        "days_on_market": 245,
    },
    {
        "parcel_id": "TC-007",
        "address": "6700 Burnet Rd",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78757",
        "property_type": "retail",
        "square_feet": 24000,
        "year_built": 1983,
        "owner_name": "James & Patricia Dawson",
        "owner_mailing_address": "1200 Westlake Dr, Austin, TX 78746",
        "owner_entity_type": "Individual",
        "assessed_value": 4800000,
        "market_value": 5600000,
        "last_sale_price": 1200000,
        "last_sale_date": "1998-11-30",
        "occupancy_rate": 0.67,
        "cap_rate": 0.044,
        "is_listed": True,
        "list_price": 5900000,
        "days_on_market": 312,
    },
    {
        "parcel_id": "TC-008",
        "address": "4200 S Congress Ave",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78745",
        "property_type": "office",
        "square_feet": 22000,
        "year_built": 1988,
        "owner_name": "Hill Country Office Group",
        "owner_mailing_address": "600 W 28th St, Austin, TX 78705",
        "owner_entity_type": "LLC",
        "assessed_value": 3900000,
        "market_value": 4300000,
        "last_sale_price": 2100000,
        "last_sale_date": "2010-02-14",
        "occupancy_rate": 0.45,
        "cap_rate": 0.029,
        "is_listed": False,
    },
    {
        "parcel_id": "TC-009",
        "address": "11200 Ranch Road 2222",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78730",
        "property_type": "office",
        "square_feet": 15000,
        "year_built": 2005,
        "owner_name": "Hill Country Office Group",
        "owner_mailing_address": "600 W 28th St, Austin, TX 78705",
        "owner_entity_type": "LLC",
        "assessed_value": 4500000,
        "market_value": 5100000,
        "last_sale_price": 3200000,
        "last_sale_date": "2012-07-30",
        "occupancy_rate": 0.52,
        "cap_rate": 0.032,
        "is_listed": False,
    },
    {
        "parcel_id": "TC-010",
        "address": "1500 S Pleasant Valley Rd",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78741",
        "property_type": "industrial",
        "square_feet": 48000,
        "year_built": 1975,
        "owner_name": "Barton Creek Industrial Trust",
        "owner_mailing_address": "Suite 200, 1100 Guadalupe St, Austin, TX 78701",
        "owner_entity_type": "Trust",
        "assessed_value": 6100000,
        "market_value": 7200000,
        "last_sale_price": 2200000,
        "last_sale_date": "2002-05-20",
        "occupancy_rate": 0.71,
        "cap_rate": 0.047,
        "is_listed": True,
        "list_price": 7500000,
        "days_on_market": 198,
    },
]


# =====================================================================
# ENGINE — You don't need to change anything below this line
# =====================================================================

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
    parcel_id: str
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
    owner_name: str
    owner_mailing_address: Optional[str] = None
    owner_entity_type: Optional[str] = None
    assessed_value: Optional[float] = None
    market_value: Optional[float] = None
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[date] = None
    annual_tax: Optional[float] = None
    occupancy_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    annual_noi: Optional[float] = None
    cap_rate: Optional[float] = None
    is_listed: bool = False
    list_price: Optional[float] = None
    days_on_market: Optional[int] = None

    @property
    def years_since_last_sale(self) -> Optional[float]:
        if self.last_sale_date:
            return (date.today() - self.last_sale_date).days / 365.25
        return None


class OwnerProfile(BaseModel):
    name: str
    entity_type: Optional[str] = None
    mailing_address: Optional[str] = None
    total_properties: int = 0
    total_assessed_value: float = 0.0
    total_square_feet: int = 0
    avg_occupancy: Optional[float] = None
    avg_years_held: Optional[float] = None
    property_types: list = Field(default_factory=list)
    markets: list = Field(default_factory=list)


class LeadScore(BaseModel):
    overall: float = Field(ge=0.0, le=100.0)
    motivation: float = Field(ge=0.0, le=100.0)
    timing: float = Field(ge=0.0, le=100.0)
    portfolio_fit: float = Field(ge=0.0, le=100.0)
    deal_size: float = Field(ge=0.0, le=100.0)
    reasons: list = Field(default_factory=list)


def score_motivation(owner, properties):
    score = 30.0
    reasons = []
    if owner.avg_years_held is not None:
        if owner.avg_years_held > 15:
            score += 30
            reasons.append(f"Long hold period ({owner.avg_years_held:.0f}+ yrs) — may be ready to exit")
        elif owner.avg_years_held > 8:
            score += 15
            reasons.append(f"Moderate hold period ({owner.avg_years_held:.0f} yrs)")
    if owner.avg_occupancy is not None:
        if owner.avg_occupancy < 0.6:
            score += 25
            reasons.append(f"Low occupancy ({owner.avg_occupancy:.0%}) — potential distress")
        elif owner.avg_occupancy < 0.8:
            score += 10
            reasons.append(f"Below-market occupancy ({owner.avg_occupancy:.0%})")
    if owner.entity_type and owner.entity_type.lower() in ("individual", "trust"):
        score += 10
        reasons.append(f"Owner type ({owner.entity_type}) — often more motivated")
    listed = [p for p in properties if p.is_listed]
    if listed:
        score += 20
        reasons.append(f"{len(listed)} property(ies) currently listed for sale")
    return min(score, 100.0), reasons


def score_timing(properties):
    score = 40.0
    reasons = []
    stale = [p for p in properties if p.days_on_market and p.days_on_market > 180]
    if stale:
        score += 25
        reasons.append(f"{len(stale)} listing(s) on market 180+ days — seller may be flexible on price")
    high_cap = [p for p in properties if p.cap_rate and p.cap_rate > TARGET_CAP_RATE + 0.02]
    if high_cap:
        score += 15
        reasons.append("Above-target cap rate — attractive entry point")
    for p in properties:
        if p.assessed_value and p.last_sale_price and p.assessed_value > p.last_sale_price * 1.5:
            score += 15
            reasons.append("Assessed value way above last sale — rising tax burden on owner")
            break
    return min(score, 100.0), reasons


def score_portfolio_fit(owner, properties):
    score = 20.0
    reasons = []
    matching = set(owner.property_types) & set(TARGET_PROPERTY_TYPES)
    if matching:
        score += 30
        reasons.append(f"Property types match your target: {', '.join(matching)}")
    if PREFER_VALUE_ADD and owner.avg_occupancy is not None and owner.avg_occupancy < 0.85:
        score += 20
        reasons.append("Value-add opportunity — occupancy below stabilized level")
    return min(score, 100.0), reasons


def score_deal_size(owner):
    score = 20.0
    reasons = []
    val = owner.total_assessed_value
    if val == 0:
        return score, ["Insufficient valuation data"]
    if MIN_DEAL_SIZE <= val <= MAX_DEAL_SIZE:
        score += 60
        reasons.append(f"Portfolio value (${val:,.0f}) within your target range")
    elif val < MIN_DEAL_SIZE:
        score += 20
        reasons.append(f"Portfolio value (${val:,.0f}) below your minimum")
    else:
        score += 30
        reasons.append(f"Portfolio value (${val:,.0f}) above max — partial acquisition possible")
    return min(score, 100.0), reasons


def build_owner_profile(name, props):
    total_assessed = sum(p.assessed_value or 0 for p in props)
    total_sqft = sum(p.square_feet or 0 for p in props)
    occs = [p.occupancy_rate for p in props if p.occupancy_rate is not None]
    holds = [p.years_since_last_sale for p in props if p.years_since_last_sale is not None]
    ptypes = list({p.property_type.value for p in props})
    markets = list({f"{p.city}, {p.state}" for p in props})
    entity = None
    mailing = None
    for p in props:
        if p.owner_entity_type: entity = p.owner_entity_type
        if p.owner_mailing_address: mailing = p.owner_mailing_address
    return OwnerProfile(
        name=name, entity_type=entity, mailing_address=mailing,
        total_properties=len(props), total_assessed_value=total_assessed,
        total_square_feet=total_sqft,
        avg_occupancy=sum(occs)/len(occs) if occs else None,
        avg_years_held=sum(holds)/len(holds) if holds else None,
        property_types=ptypes, markets=markets,
    )


def suggest_approach(priority, owner, props):
    listed = [p for p in props if p.is_listed]
    if priority == "HOT":
        if listed:
            return (
                "DIRECT OUTREACH — property already listed. Contact listing broker "
                "or reach out to owner directly with a competitive offer. Use comparable "
                "sales to justify your number."
            )
        return (
            "HIGH-PRIORITY OFF-MARKET — send personalized letter highlighting market "
            "conditions and your track record. Follow up with a phone call within 7 days."
        )
    if priority == "WARM":
        return (
            "RELATIONSHIP BUILDING — introduce yourself, express interest in the area. "
            "Offer a free property valuation as a conversation starter. Nurture 2-4 weeks "
            "before making an offer."
        )
    return "LONG-TERM NURTURE — monitor for changes. Re-evaluate quarterly."


def run_agent():
    print("=" * 60)
    print("  COMMERCIAL REAL ESTATE AI AGENT")
    print(f"  Target Market: {TARGET_CITY}, {TARGET_STATE}")
    print(f"  Deal Range: ${MIN_DEAL_SIZE:,.0f} - ${MAX_DEAL_SIZE:,.0f}")
    print("=" * 60)
    print()

    # Parse properties
    properties = []
    for record in PROPERTIES_DATA:
        try:
            properties.append(Property(**record))
        except Exception as e:
            print(f"  Skipping bad record {record.get('parcel_id')}: {e}")

    print(f"Loaded {len(properties)} properties")

    # Group by owner
    owner_groups = defaultdict(list)
    for p in properties:
        owner_groups[p.owner_name].append(p)

    print(f"Found {len(owner_groups)} unique owners")
    print()

    # Score each owner
    leads = []
    for name, props in owner_groups.items():
        profile = build_owner_profile(name, props)
        mot_score, mot_reasons = score_motivation(profile, props)
        tim_score, tim_reasons = score_timing(props)
        fit_score, fit_reasons = score_portfolio_fit(profile, props)
        deal_score, deal_reasons = score_deal_size(profile)

        overall = (0.35 * mot_score + 0.20 * tim_score +
                   0.25 * fit_score + 0.20 * deal_score)

        all_reasons = mot_reasons + tim_reasons + fit_reasons + deal_reasons

        if overall >= 70:
            priority = "HOT"
        elif overall >= 45:
            priority = "WARM"
        else:
            priority = "COLD"

        approach = suggest_approach(priority, profile, props)

        leads.append({
            "owner": profile,
            "properties": props,
            "overall": round(overall, 1),
            "motivation": round(mot_score, 1),
            "timing": round(tim_score, 1),
            "fit": round(fit_score, 1),
            "deal_size": round(deal_score, 1),
            "priority": priority,
            "reasons": all_reasons,
            "approach": approach,
        })

    leads.sort(key=lambda x: x["overall"], reverse=True)

    # Print results table
    table = Table(title="SELLER LEAD RANKINGS", show_lines=True)
    table.add_column("Rank", style="bold", width=4)
    table.add_column("Priority", width=8)
    table.add_column("Owner", min_width=22)
    table.add_column("Score", justify="right", width=6)
    table.add_column("Properties", justify="right", width=5)
    table.add_column("Portfolio Value", justify="right", min_width=14)
    table.add_column("Types", min_width=12)

    priority_styles = {
        "HOT": "[bold red]🔥 HOT[/bold red]",
        "WARM": "[bold yellow]⚡ WARM[/bold yellow]",
        "COLD": "[dim]❄️  COLD[/dim]",
    }

    for i, lead in enumerate(leads, 1):
        o = lead["owner"]
        table.add_row(
            str(i),
            priority_styles.get(lead["priority"], lead["priority"]),
            o.name,
            str(lead["overall"]),
            str(o.total_properties),
            f"${o.total_assessed_value:,.0f}",
            ", ".join(o.property_types),
        )

    console.print(table)

    # Print detailed breakdown for each lead
    print("\n")
    print("=" * 60)
    print("  DETAILED LEAD BREAKDOWN")
    print("=" * 60)

    for i, lead in enumerate(leads, 1):
        o = lead["owner"]
        print(f"\n{'─' * 60}")
        print(f"  #{i} — {o.name}")
        print(f"  Priority: {lead['priority']}  |  Score: {lead['overall']}/100")
        print(f"{'─' * 60}")
        print(f"  Entity Type:    {o.entity_type or 'Unknown'}")
        print(f"  Mailing Addr:   {o.mailing_address or 'Unknown'}")
        print(f"  Properties:     {o.total_properties}")
        print(f"  Portfolio Value: ${o.total_assessed_value:,.0f}")
        print(f"  Avg Occupancy:  {o.avg_occupancy:.0%}" if o.avg_occupancy else "  Avg Occupancy:  N/A")
        print(f"  Avg Years Held: {o.avg_years_held:.1f}" if o.avg_years_held else "  Avg Years Held: N/A")
        print()
        print(f"  SCORES:")
        print(f"    Motivation:    {lead['motivation']}/100")
        print(f"    Timing:        {lead['timing']}/100")
        print(f"    Portfolio Fit: {lead['fit']}/100")
        print(f"    Deal Size:     {lead['deal_size']}/100")
        print()
        print(f"  WHY THIS OWNER:")
        for reason in lead["reasons"]:
            print(f"    • {reason}")
        print()
        print(f"  RECOMMENDED ACTION:")
        print(f"    {lead['approach']}")
        print()
        print(f"  PROPERTIES:")
        for p in lead["properties"]:
            listed_tag = " [LISTED]" if p.is_listed else ""
            print(f"    • {p.address}, {p.city} {p.state} {p.zip_code}{listed_tag}")
            print(f"      {p.property_type.value} | {p.square_feet:,} sqft | Assessed: ${p.assessed_value:,.0f}" if p.square_feet and p.assessed_value else f"      {p.property_type.value}")

    print(f"\n{'=' * 60}")
    print(f"  SUMMARY: {len(leads)} leads total")
    print(f"    🔥 HOT:  {sum(1 for l in leads if l['priority'] == 'HOT')} — reach out this week")
    print(f"    ⚡ WARM: {sum(1 for l in leads if l['priority'] == 'WARM')} — nurture over 2-4 weeks")
    print(f"    ❄️  COLD: {sum(1 for l in leads if l['priority'] == 'COLD')} — monitor quarterly")
    print(f"{'=' * 60}")


# --- RUN IT ---
run_agent()
