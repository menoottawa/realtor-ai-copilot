"""Call enrichment providers (schools, comps, crime, flood)."""
from __future__ import annotations

import random
from typing import Iterable

MOCK_LISTINGS = ["listing-1", "listing-2"]


def select_listings(limit: int = 100) -> Iterable[str]:
    # Placeholder for DB query
    return random.sample(MOCK_LISTINGS, k=min(limit, len(MOCK_LISTINGS)))


def enrich_listing(listing_id: str) -> None:
    # TODO: integrate with GreatSchools, HouseCanary, etc.
    print(f"[enrich] Would enrich listing {listing_id}")


def main() -> None:
    for listing_id in select_listings():
        enrich_listing(listing_id)


if __name__ == "__main__":
    main()
