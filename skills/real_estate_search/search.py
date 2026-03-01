"""Skill entrypoint for buyer listing search (mock dataset)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, List

DATA_PATH = os.path.join(os.path.dirname(__file__), "sample-data.json")


@dataclass
class SearchInput:
    location: str
    min_price: int = 0
    max_price: int = 10**9
    beds: int = 0
    baths: int = 0
    must_haves: List[str] | None = None
    nice_to_haves: List[str] | None = None
    max_results: int = 5


def load_data() -> list[dict]:
    with open(DATA_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def matches_query(home: dict, payload: SearchInput) -> bool:
    if home["price"] < payload.min_price or home["price"] > payload.max_price:
        return False
    if home["beds"] < payload.beds:
        return False
    if home["baths"] < payload.baths:
        return False
    if payload.location:
        combined = " ".join([home["city"], home["state"], home["zip"]]).lower()
        if payload.location.lower() not in combined:
            return False
    if payload.must_haves:
        tags = set(tag.lower() for tag in home.get("style_tags", []) + home.get("features", []))
        for keyword in payload.must_haves:
            if keyword.lower() not in tags:
                return False
    return True


def compute_score(home: dict, payload: SearchInput) -> float:
    score = 0.5
    # Price proximity
    target = (payload.min_price + payload.max_price) / 2 if payload.max_price < 10**9 else payload.min_price
    if target:
        delta = abs(home["price"] - target)
        span = max(payload.max_price - payload.min_price, 1)
        score += max(0, 0.25 * (1 - delta / span))
    # DOM bonus
    dom = home.get("dom", 0)
    if dom and dom < 15:
        score += 0.1
    # Nice-to-have overlap
    if payload.nice_to_haves:
        tags = set(tag.lower() for tag in home.get("style_tags", []) + home.get("features", []))
        overlap = len(tags & set(t.lower() for t in payload.nice_to_haves))
        score += min(0.15, overlap * 0.05)
    return min(score, 1.0)


def format_output(home: dict, score: float) -> dict:
    return {
        "mls_id": home["mls_id"],
        "address": f"{home['address']}, {home['city']}, {home['state']} {home['zip']}",
        "price": home["price"],
        "beds": home["beds"],
        "baths": home["baths"],
        "sqft": home.get("sqft"),
        "lot_sqft": home.get("lot_sqft"),
        "hoa": home.get("hoa"),
        "dom": home.get("dom"),
        "style_tags": home.get("style_tags", []),
        "match_score": round(score, 2),
        "summary": home.get("notes"),
        "detail_url": home.get("url"),
        "notes": home.get("features", []),
    }


def run(payload: dict[str, Any]) -> list[dict]:
    data = load_data()
    search_input = SearchInput(
        location=payload.get("location", ""),
        min_price=payload.get("min_price", 0),
        max_price=payload.get("max_price", 10**9),
        beds=payload.get("beds", 0),
        baths=payload.get("baths", 0),
        must_haves=payload.get("must_haves") or [],
        nice_to_haves=payload.get("nice_to_haves") or [],
        max_results=min(payload.get("max_results", 5), 10),
    )

    matches: list[tuple[dict, float]] = []
    for home in data:
        if matches_query(home, search_input):
            score = compute_score(home, search_input)
            matches.append((home, score))

    matches.sort(key=lambda item: item[1], reverse=True)
    return [format_output(home, score) for home, score in matches[: search_input.max_results]]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--location", required=True)
    parser.add_argument("--min-price", type=int, default=0)
    parser.add_argument("--max-price", type=int, default=10**9)
    parser.add_argument("--beds", type=int, default=0)
    parser.add_argument("--baths", type=int, default=0)
    parser.add_argument("--must-haves", type=str, default="")
    parser.add_argument("--nice-to-haves", type=str, default="")
    args = parser.parse_args()

    payload = {
        "location": args.location,
        "min_price": args.min_price,
        "max_price": args.max_price,
        "beds": args.beds,
        "baths": args.baths,
        "must_haves": [x.strip() for x in args.must_haves.split(",") if x.strip()],
        "nice_to_haves": [x.strip() for x in args.nice_to_haves.split(",") if x.strip()],
    }
    print(json.dumps(run(payload), indent=2))
