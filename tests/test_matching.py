"""Tests for the listing scoring / matching engine."""

from __future__ import annotations

from realtor_ai_copilot.matching.scorer import score_listings
from realtor_ai_copilot.models import BuyerProfile, Listing, MatchResult


def make_listing(**kwargs) -> Listing:
    defaults = dict(
        mls_id="TST-001",
        address="1 Main St",
        city="Ottawa",
        state="ON",
        zip_code="K1A",
        price=500000,
        bedrooms=3,
        bathrooms=2,
        sqft=1800,
        property_type="Single Family",
    )
    defaults.update(kwargs)
    return Listing(**defaults)


def make_profile(**kwargs) -> BuyerProfile:
    defaults = dict(
        name="Test Buyer",
        max_price=600000,
        min_bedrooms=3,
        min_bathrooms=2,
        min_sqft=1600,
        preferred_cities=["Ottawa"],
        preferred_property_types=["Single Family"],
    )
    defaults.update(kwargs)
    return BuyerProfile(**defaults)


class TestScoreListing:
    def test_perfect_match_scores_high(self) -> None:
        listing = make_listing()
        profile = make_profile()
        results = score_listings([listing], profile)
        assert len(results) == 1
        assert results[0].score >= 80.0

    def test_over_budget_scores_zero(self) -> None:
        listing = make_listing(price=700000)
        profile = make_profile(max_price=600000)
        results = score_listings([listing], profile)
        assert results[0].score < 70  # price component zeroed

    def test_too_few_bedrooms_penalised(self) -> None:
        listing = make_listing(bedrooms=2)
        profile = make_profile(min_bedrooms=3)
        results = score_listings([listing], profile)
        # Bedroom concern should be present
        assert any("bed" in c.lower() for c in results[0].concerns)

    def test_wrong_city_penalised(self) -> None:
        listing = make_listing(city="Barrhaven")
        profile = make_profile(preferred_cities=["Ottawa", "Kanata"])
        results = score_listings([listing], profile)
        assert any("preferred cities" in c.lower() for c in results[0].concerns)

    def test_wrong_property_type_penalised(self) -> None:
        listing = make_listing(property_type="Condo")
        profile = make_profile(preferred_property_types=["Single Family"])
        results = score_listings([listing], profile)
        assert any("preferred" in c.lower() for c in results[0].concerns)

    def test_sqft_below_minimum_penalised(self) -> None:
        listing = make_listing(sqft=1200)
        profile = make_profile(min_sqft=1600)
        results = score_listings([listing], profile)
        assert any("sqft" in c.lower() for c in results[0].concerns)

    def test_no_sqft_preference_gives_full_sqft_points(self) -> None:
        listing = make_listing(sqft=None)
        profile = make_profile(min_sqft=None)
        results = score_listings([listing], profile)
        # Should not penalise for sqft when no preference set
        assert not any("sqft" in c.lower() for c in results[0].concerns)

    def test_highlights_populated(self) -> None:
        listing = make_listing()
        profile = make_profile()
        results = score_listings([listing], profile)
        assert len(results[0].highlights) > 0

    def test_score_range(self) -> None:
        listing = make_listing()
        profile = make_profile()
        results = score_listings([listing], profile)
        assert 0.0 <= results[0].score <= 100.0


class TestScoreListings:
    def test_sorted_descending(self) -> None:
        listings = [
            make_listing(mls_id="A", city="Barrhaven"),  # wrong city → lower score
            make_listing(mls_id="B", city="Ottawa"),  # preferred city → higher score
        ]
        profile = make_profile(preferred_cities=["Ottawa"])
        results = score_listings(listings, profile)
        assert results[0].listing.mls_id == "B"
        assert results[1].listing.mls_id == "A"

    def test_top_n(self) -> None:
        listings = [make_listing(mls_id=f"L{i}") for i in range(10)]
        profile = make_profile()
        results = score_listings(listings, profile, top_n=3)
        assert len(results) == 3

    def test_min_score_filter(self) -> None:
        over_budget = make_listing(price=900000)  # will score near 0
        good = make_listing()
        profile = make_profile()
        results = score_listings([over_budget, good], profile, min_score=50.0)
        assert all(r.score >= 50.0 for r in results)

    def test_empty_listings(self) -> None:
        profile = make_profile()
        results = score_listings([], profile)
        assert results == []

    def test_returns_match_result_objects(self) -> None:
        listing = make_listing()
        profile = make_profile()
        results = score_listings([listing], profile)
        assert all(isinstance(r, MatchResult) for r in results)
