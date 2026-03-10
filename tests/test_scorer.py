from datetime import date

from src.analysis.scorer import BuyerCriteria, LeadScorer, ScoringWeights
from src.models.lead import OwnerProfile
from src.models.property import Property, PropertyType


def _make_property(**overrides) -> Property:
    defaults = dict(
        parcel_id="TEST-001",
        address="100 Main St",
        city="Austin",
        state="TX",
        zip_code="78701",
        property_type=PropertyType.OFFICE,
        square_feet=20000,
        owner_name="Test Owner",
        owner_entity_type="LLC",
        assessed_value=5000000,
        market_value=6000000,
        last_sale_price=3000000,
        last_sale_date=date(2008, 1, 1),
        occupancy_rate=0.55,
        cap_rate=0.07,
    )
    defaults.update(overrides)
    return Property(**defaults)


def _make_profile(**overrides) -> OwnerProfile:
    defaults = dict(
        name="Test Owner",
        entity_type="Individual",
        total_properties=2,
        total_assessed_value=8000000,
        total_square_feet=40000,
        avg_occupancy=0.55,
        avg_years_held=16.0,
        property_types=["office"],
        markets=["Austin, TX"],
    )
    defaults.update(overrides)
    return OwnerProfile(**defaults)


def test_scorer_produces_score():
    scorer = LeadScorer()
    profile = _make_profile()
    props = [_make_property()]
    score = scorer.score(profile, props)
    assert 0 <= score.overall <= 100
    assert len(score.reasons) > 0


def test_high_motivation_for_long_hold_low_occupancy():
    scorer = LeadScorer()
    profile = _make_profile(avg_years_held=20, avg_occupancy=0.5, entity_type="Individual")
    props = [_make_property()]
    score = scorer.score(profile, props)
    assert score.motivation >= 60


def test_listed_property_boosts_motivation():
    scorer = LeadScorer()
    profile = _make_profile(avg_years_held=5, avg_occupancy=0.9)
    props = [_make_property(is_listed=True, days_on_market=200)]
    score = scorer.score(profile, props)
    assert score.motivation >= 50


def test_deal_size_within_range_scores_high():
    criteria = BuyerCriteria(min_deal_size=1_000_000, max_deal_size=10_000_000)
    scorer = LeadScorer(criteria=criteria)
    profile = _make_profile(total_assessed_value=5_000_000)
    props = [_make_property()]
    score = scorer.score(profile, props)
    assert score.deal_size >= 60


def test_portfolio_fit_matching_types():
    criteria = BuyerCriteria(target_property_types=["office", "retail"])
    scorer = LeadScorer(criteria=criteria)
    profile = _make_profile(property_types=["office"])
    props = [_make_property()]
    score = scorer.score(profile, props)
    assert score.portfolio_fit >= 40
