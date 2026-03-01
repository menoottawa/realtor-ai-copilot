"""Shared test fixtures."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from realtor_ai_copilot.models import BuyerProfile, Listing


@pytest.fixture()
def sample_listing() -> Listing:
    return Listing(
        mls_id="TEST-001",
        address="100 Test Street",
        city="Ottawa",
        state="ON",
        zip_code="K1A 0A1",
        price=525000,
        bedrooms=3,
        bathrooms=2,
        sqft=1800,
        year_built=2005,
        property_type="Single Family",
        description="A nice home in a quiet neighbourhood.",
    )


@pytest.fixture()
def sample_profile() -> BuyerProfile:
    return BuyerProfile(
        name="Test Buyer",
        max_price=600000,
        min_price=400000,
        min_bedrooms=3,
        min_bathrooms=2,
        min_sqft=1600,
        preferred_cities=["Ottawa", "Kanata"],
        preferred_property_types=["Single Family"],
        notes="Looking for a family home near schools.",
    )


@pytest.fixture()
def csv_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        mls_id,address,city,state,zip_code,price,bedrooms,bathrooms,sqft,property_type
        MLS-A,10 Alpha St,Ottawa,ON,K1A 1A1,500000,3,2,1800,Single Family
        MLS-B,20 Beta Ave,Kanata,ON,K2K 2B2,450000,4,3,2100,Single Family
        MLS-C,30 Gamma Rd,Barrhaven,ON,K2J 0P2,350000,2,1,1000,Condo
    """)
    p = tmp_path / "listings.csv"
    p.write_text(content)
    return p


@pytest.fixture()
def json_file(tmp_path: Path) -> Path:
    data = [
        {
            "mls_id": "MLS-X",
            "address": "10 X Street",
            "city": "Ottawa",
            "state": "ON",
            "zip_code": "K1B 1B1",
            "price": 580000,
            "bedrooms": 4,
            "bathrooms": 3,
            "sqft": 2200,
            "property_type": "Single Family",
        }
    ]
    p = tmp_path / "listings.json"
    p.write_text(json.dumps(data))
    return p
