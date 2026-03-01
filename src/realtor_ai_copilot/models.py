"""Pydantic data models for listings, buyer profiles, and match results."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Listing(BaseModel):
    """Represents a single MLS property listing."""

    mls_id: str = Field(..., description="Unique MLS identifier")
    address: str = Field(..., description="Full street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State / province")
    zip_code: str = Field(..., description="Postal / ZIP code")
    price: float = Field(..., gt=0, description="Listing price in dollars")
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms")
    bathrooms: float = Field(..., ge=0, description="Number of bathrooms")
    sqft: Optional[float] = Field(None, ge=0, description="Interior square footage")
    lot_sqft: Optional[float] = Field(None, ge=0, description="Lot size in square feet")
    year_built: Optional[int] = Field(None, description="Year the property was built")
    property_type: str = Field("Single Family", description="Property type (e.g. Condo, Townhouse)")
    description: Optional[str] = Field(None, description="Agent remarks / property description")
    listing_url: Optional[str] = Field(None, description="Public URL for the listing")

    @field_validator("price", mode="before")
    @classmethod
    def parse_price(cls, v: object) -> float:
        """Strip currency symbols / commas before coercing to float."""
        if isinstance(v, str):
            v = v.replace("$", "").replace(",", "").strip()
        return float(v)  # type: ignore[arg-type]

    @property
    def price_per_sqft(self) -> Optional[float]:
        """Return price-per-square-foot or None if sqft is unknown."""
        if self.sqft and self.sqft > 0:
            return round(self.price / self.sqft, 2)
        return None

    @property
    def full_address(self) -> str:
        return f"{self.address}, {self.city}, {self.state} {self.zip_code}"


class BuyerProfile(BaseModel):
    """Represents a buyer's search preferences."""

    name: str = Field(..., description="Buyer's full name")
    email: Optional[str] = Field(None, description="Buyer contact email")
    max_price: float = Field(..., gt=0, description="Maximum purchase price")
    min_price: float = Field(0.0, ge=0, description="Minimum purchase price")
    min_bedrooms: int = Field(0, ge=0, description="Minimum number of bedrooms")
    min_bathrooms: float = Field(0.0, ge=0, description="Minimum number of bathrooms")
    min_sqft: Optional[float] = Field(None, ge=0, description="Minimum interior square footage")
    preferred_cities: list[str] = Field(default_factory=list, description="Preferred city names")
    preferred_property_types: list[str] = Field(
        default_factory=list, description="Preferred property types"
    )
    must_have_garage: bool = Field(False, description="Requires a garage")
    notes: Optional[str] = Field(None, description="Free-text notes from agent intake")


class MatchResult(BaseModel):
    """A scored listing-to-profile match."""

    listing: Listing
    score: float = Field(..., ge=0.0, le=100.0, description="Match score 0-100")
    highlights: list[str] = Field(default_factory=list, description="Key match reasons")
    concerns: list[str] = Field(default_factory=list, description="Potential issues / mismatches")
    analysis: Optional[str] = Field(None, description="AI-generated narrative analysis")
