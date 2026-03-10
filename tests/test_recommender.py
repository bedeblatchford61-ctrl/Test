from datetime import date

from src.analysis.recommender import Recommender
from src.models.lead import LeadPriority
from src.models.property import Property, PropertyType


def _make_property(parcel_id, owner_name, **overrides) -> Property:
    defaults = dict(
        parcel_id=parcel_id,
        address="100 Main St",
        city="Austin",
        state="TX",
        zip_code="78701",
        property_type=PropertyType.OFFICE,
        square_feet=20000,
        owner_name=owner_name,
        owner_entity_type="LLC",
        assessed_value=5000000,
        market_value=6000000,
        last_sale_price=3000000,
        last_sale_date=date(2008, 1, 1),
        occupancy_rate=0.6,
        cap_rate=0.07,
    )
    defaults.update(overrides)
    return Property(**defaults)


def test_generate_leads_groups_by_owner():
    recommender = Recommender()
    properties = [
        _make_property("P1", "Owner A"),
        _make_property("P2", "Owner A"),
        _make_property("P3", "Owner B"),
    ]
    leads = recommender.generate_leads(properties)
    assert len(leads) == 2
    owner_names = {l.owner.name for l in leads}
    assert owner_names == {"Owner A", "Owner B"}


def test_leads_sorted_by_score_descending():
    recommender = Recommender()
    properties = [
        _make_property("P1", "High Score Owner", occupancy_rate=0.3, owner_entity_type="Individual",
                       last_sale_date=date(2000, 1, 1), is_listed=True, days_on_market=300),
        _make_property("P2", "Low Score Owner", occupancy_rate=0.95,
                       last_sale_date=date(2023, 1, 1)),
    ]
    leads = recommender.generate_leads(properties)
    assert leads[0].score.overall >= leads[1].score.overall


def test_hot_lead_has_approach():
    recommender = Recommender()
    properties = [
        _make_property("P1", "Motivated Seller", occupancy_rate=0.3,
                       owner_entity_type="Individual", last_sale_date=date(1998, 1, 1),
                       is_listed=True, days_on_market=400),
    ]
    leads = recommender.generate_leads(properties)
    assert leads[0].recommended_approach is not None
    assert len(leads[0].recommended_approach) > 0
