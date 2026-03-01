"""Run deterministic scoring for buyers vs listings."""
from __future__ import annotations

from realtor_ai.services.scoring import ScoringEngine


def load_active_buyers() -> list[dict]:
    # Placeholder for DB call
    return [
        {
            "id": "buyer-1",
            "budget_min": 650000,
            "budget_max": 800000,
            "min_beds": 3,
            "min_baths": 3,
            "commute_minutes": 35,
        }
    ]


def candidate_listings() -> list[dict]:
    return [
        {
            "id": "listing-1",
            "price": 720000,
            "beds": 3,
            "baths": 3,
            "distance_minutes": 28,
            "style_tags": ["modern", "open-floorplan"],
            "dom": 5,
            "price_drop_percent": 0,
        }
    ]


def load_criteria(buyer_id: str) -> list[dict]:
    return [
        {
            "id": "crit-1",
            "requirement_type": "must",
            "field": "beds",
            "operator": ">=",
            "value": 3,
            "weight": 1.0,
        }
    ]


def store_match(match) -> None:
    print(f"[match] {match.buyer_id} vs {match.listing_id} => {match.score}")


def main() -> None:
    engine = ScoringEngine()
    for buyer in load_active_buyers():
        criteria = load_criteria(buyer["id"])
        for listing in candidate_listings():
            match = engine.score(buyer, listing, criteria)
            if not match.rejected:
                store_match(match)


if __name__ == "__main__":
    main()
