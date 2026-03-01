"""Tests for data models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from realtor_ai_copilot.models import BuyerProfile, Listing, MatchResult


class TestListing:
    def test_basic_creation(self) -> None:
        listing = Listing(
            mls_id="X1",
            address="1 Main St",
            city="Ottawa",
            state="ON",
            zip_code="K1A",
            price=500000,
            bedrooms=3,
            bathrooms=2.0,
        )
        assert listing.mls_id == "X1"
        assert listing.price == 500000.0

    def test_price_with_currency_string(self) -> None:
        listing = Listing(
            mls_id="X2",
            address="2 Main St",
            city="Ottawa",
            state="ON",
            zip_code="K1A",
            price="$1,250,000",
            bedrooms=4,
            bathrooms=3,
        )
        assert listing.price == 1250000.0

    def test_price_per_sqft(self) -> None:
        listing = Listing(
            mls_id="X3",
            address="3 Main St",
            city="Ottawa",
            state="ON",
            zip_code="K1A",
            price=400000,
            bedrooms=3,
            bathrooms=2,
            sqft=2000,
        )
        assert listing.price_per_sqft == 200.0

    def test_price_per_sqft_none_when_no_sqft(self, sample_listing: Listing) -> None:
        sample_listing = sample_listing.model_copy(update={"sqft": None})
        assert sample_listing.price_per_sqft is None

    def test_full_address(self, sample_listing: Listing) -> None:
        assert sample_listing.full_address == "100 Test Street, Ottawa, ON K1A 0A1"

    def test_invalid_price(self) -> None:
        with pytest.raises(ValidationError):
            Listing(
                mls_id="X4",
                address="4 Main St",
                city="Ottawa",
                state="ON",
                zip_code="K1A",
                price=-100,
                bedrooms=3,
                bathrooms=2,
            )

    def test_invalid_bedrooms(self) -> None:
        with pytest.raises(ValidationError):
            Listing(
                mls_id="X5",
                address="5 Main St",
                city="Ottawa",
                state="ON",
                zip_code="K1A",
                price=500000,
                bedrooms=-1,
                bathrooms=2,
            )


class TestBuyerProfile:
    def test_basic_creation(self, sample_profile: BuyerProfile) -> None:
        assert sample_profile.name == "Test Buyer"
        assert sample_profile.max_price == 600000

    def test_default_empty_lists(self) -> None:
        bp = BuyerProfile(name="A", max_price=500000)
        assert bp.preferred_cities == []
        assert bp.preferred_property_types == []

    def test_invalid_max_price(self) -> None:
        with pytest.raises(ValidationError):
            BuyerProfile(name="A", max_price=-1)


class TestMatchResult:
    def test_creation(self, sample_listing: Listing) -> None:
        mr = MatchResult(listing=sample_listing, score=80.0)
        assert mr.score == 80.0
        assert mr.highlights == []
        assert mr.concerns == []
        assert mr.analysis is None

    def test_score_bounds(self, sample_listing: Listing) -> None:
        with pytest.raises(ValidationError):
            MatchResult(listing=sample_listing, score=101.0)
        with pytest.raises(ValidationError):
            MatchResult(listing=sample_listing, score=-1.0)
