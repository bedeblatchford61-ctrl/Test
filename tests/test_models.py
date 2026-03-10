from datetime import date

from src.models.lead import LeadScore, OwnerProfile
from src.models.property import Property, PropertyType


def test_property_creation():
    p = Property(
        parcel_id="TEST-001",
        address="100 Main St",
        city="Austin",
        state="TX",
        zip_code="78701",
        property_type=PropertyType.OFFICE,
        square_feet=10000,
        owner_name="Test Owner",
        assessed_value=1000000,
        market_value=1200000,
    )
    assert p.parcel_id == "TEST-001"
    assert p.price_per_sqft == 120.0
    assert p.property_type == PropertyType.OFFICE


def test_property_years_since_last_sale():
    p = Property(
        parcel_id="TEST-002",
        address="200 Main St",
        city="Austin",
        state="TX",
        zip_code="78701",
        property_type=PropertyType.RETAIL,
        owner_name="Test Owner",
        last_sale_date=date(2010, 1, 1),
    )
    years = p.years_since_last_sale
    assert years is not None
    assert years > 10


def test_owner_profile():
    profile = OwnerProfile(
        name="Test Owner",
        entity_type="LLC",
        total_properties=3,
        total_assessed_value=5000000,
        total_square_feet=50000,
        avg_occupancy=0.85,
        avg_years_held=12.0,
        property_types=["office", "retail"],
        markets=["Austin, TX"],
    )
    assert profile.total_properties == 3
    assert "office" in profile.property_types


def test_lead_score_bounds():
    score = LeadScore(
        overall=75.0,
        motivation=80.0,
        timing=60.0,
        portfolio_fit=85.0,
        deal_size=70.0,
        reasons=["Test reason"],
    )
    assert 0 <= score.overall <= 100
    assert len(score.reasons) == 1
