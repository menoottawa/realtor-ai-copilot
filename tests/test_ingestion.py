"""Tests for MLS data ingestion."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from realtor_ai_copilot.ingestion.loader import load_listings
from realtor_ai_copilot.models import Listing


class TestLoadCSV:
    def test_load_csv(self, csv_file: Path) -> None:
        listings = load_listings(csv_file)
        assert len(listings) == 3
        assert all(isinstance(lst, Listing) for lst in listings)

    def test_csv_field_values(self, csv_file: Path) -> None:
        listings = load_listings(csv_file)
        mls_a = next(lst for lst in listings if lst.mls_id == "MLS-A")
        assert mls_a.city == "Ottawa"
        assert mls_a.price == 500000.0
        assert mls_a.bedrooms == 3
        assert mls_a.bathrooms == 2.0

    def test_csv_with_aliases(self, tmp_path: Path) -> None:
        """CSV using alternate column names should still load correctly."""
        content = (
            "listing_id,street_address,city,state,zip,list_price,beds,baths,square_feet,type\n"
            "M1,1 St,Ottawa,ON,K1A,400000,3,2,1500,Single Family\n"
        )
        p = tmp_path / "alias.csv"
        p.write_text(content)
        listings = load_listings(p)
        assert listings[0].mls_id == "M1"
        assert listings[0].price == 400000.0
        assert listings[0].sqft == 1500.0

    def test_csv_missing_required_column(self, tmp_path: Path) -> None:
        content = "mls_id,address,city,state\nX1,1 St,Ottawa,ON\n"
        p = tmp_path / "bad.csv"
        p.write_text(content)
        with pytest.raises(ValueError, match="missing required columns"):
            load_listings(p)


class TestLoadJSON:
    def test_load_json_array(self, json_file: Path) -> None:
        listings = load_listings(json_file)
        assert len(listings) == 1
        assert listings[0].mls_id == "MLS-X"

    def test_load_json_envelope(self, tmp_path: Path) -> None:
        """JSON with a 'listings' key envelope should be unwrapped."""
        data = {
            "listings": [
                {
                    "mls_id": "E1",
                    "address": "1 Env St",
                    "city": "Ottawa",
                    "state": "ON",
                    "zip_code": "K1A",
                    "price": 500000,
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "property_type": "Single Family",
                }
            ]
        }
        p = tmp_path / "envelope.json"
        p.write_text(json.dumps(data))
        listings = load_listings(p)
        assert listings[0].mls_id == "E1"

    def test_price_string_in_json(self, tmp_path: Path) -> None:
        data = [
            {
                "mls_id": "P1",
                "address": "1 Price St",
                "city": "Ottawa",
                "state": "ON",
                "zip_code": "K1A",
                "price": "$550,000",
                "bedrooms": 3,
                "bathrooms": 2,
            }
        ]
        p = tmp_path / "price.json"
        p.write_text(json.dumps(data))
        listings = load_listings(p)
        assert listings[0].price == 550000.0


class TestLoadErrors:
    def test_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_listings("/nonexistent/path/listings.csv")

    def test_unsupported_format(self, tmp_path: Path) -> None:
        p = tmp_path / "listings.xlsx"
        p.touch()
        with pytest.raises(ValueError, match="Unsupported file format"):
            load_listings(p)
