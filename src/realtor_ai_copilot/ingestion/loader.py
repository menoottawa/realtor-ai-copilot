"""Load MLS listing data from CSV or JSON files into Listing objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

import pandas as pd

from realtor_ai_copilot.models import Listing

# Column name aliases: maps common MLS export headers -> canonical field names
_COLUMN_ALIASES: dict[str, str] = {
    # MLS ID
    "mls_number": "mls_id",
    "listing_id": "mls_id",
    "id": "mls_id",
    # Price
    "list_price": "price",
    "listing_price": "price",
    # Bedrooms
    "beds": "bedrooms",
    "bed": "bedrooms",
    "br": "bedrooms",
    # Bathrooms
    "baths": "bathrooms",
    "bath": "bathrooms",
    "ba": "bathrooms",
    "full_baths": "bathrooms",
    # Square footage
    "square_feet": "sqft",
    "sq_ft": "sqft",
    "living_area": "sqft",
    "sq_feet": "sqft",
    # Lot size
    "lot_size": "lot_sqft",
    "lot_area": "lot_sqft",
    # Year built
    "built": "year_built",
    "year": "year_built",
    # Property type
    "type": "property_type",
    "prop_type": "property_type",
    "style": "property_type",
    # Address parts
    "street_address": "address",
    "street": "address",
    "postal_code": "zip_code",
    "zip": "zip_code",
    # Description
    "remarks": "description",
    "public_remarks": "description",
    "agent_remarks": "description",
    # URL
    "url": "listing_url",
    "listing_link": "listing_url",
}

_REQUIRED_FIELDS = {
    "mls_id", "address", "city", "state", "zip_code", "price", "bedrooms", "bathrooms"
}


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lower-case and alias column names to match Listing field names."""
    df = df.rename(columns=lambda c: c.strip().lower().replace(" ", "_"))
    df = df.rename(columns={k: v for k, v in _COLUMN_ALIASES.items() if k in df.columns})
    return df


def _df_to_listings(df: pd.DataFrame) -> list[Listing]:
    """Convert a normalised DataFrame to a list of Listing objects."""
    missing = _REQUIRED_FIELDS - set(df.columns)
    if missing:
        raise ValueError(f"MLS data is missing required columns: {sorted(missing)}")

    listings: list[Listing] = []
    for _, row in df.iterrows():
        data = {k: v for k, v in row.items() if pd.notna(v) and v != ""}
        # Coerce numeric-ish NaN / None for optional fields
        for opt_field in ("sqft", "lot_sqft", "year_built", "description", "listing_url"):
            data.setdefault(opt_field, None)
        listings.append(Listing(**data))
    return listings


def load_listings(path: Union[str, Path]) -> list[Listing]:
    """Load MLS listings from a CSV or JSON file.

    Parameters
    ----------
    path:
        Path to the MLS data file.  Supported formats:
        - ``.csv`` — comma-separated MLS export
        - ``.json`` — array of listing objects or a dict with a ``listings`` key

    Returns
    -------
    list[Listing]
        Validated Listing objects ready for scoring.

    Raises
    ------
    ValueError
        If the file format is unsupported or required columns are absent.
    FileNotFoundError
        If the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Listings file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path, dtype=str)
    elif suffix == ".json":
        with path.open() as fh:
            raw = json.load(fh)
        if isinstance(raw, dict):
            # Support {"listings": [...]} envelope
            raw = raw.get("listings", raw)
        df = pd.DataFrame(raw)
    else:
        raise ValueError(f"Unsupported file format '{suffix}'. Use .csv or .json")

    df = _normalise_columns(df)
    return _df_to_listings(df)
