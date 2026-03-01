"""Deterministic scoring engine for buyer/listing matches."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class CriterionResult:
    criterion_id: str
    passed: bool
    score_component: float
    explanation: str


@dataclass
class MatchScore:
    listing_id: str
    buyer_id: str
    score: float
    criterion_results: List[CriterionResult]
    rejected: bool = False
    rejection_reason: str | None = None


class ScoringEngine:
    def __init__(self, weights: Dict[str, float] | None = None):
        self.weights = weights or {
            "price": 0.25,
            "space": 0.20,
            "location": 0.20,
            "lifestyle": 0.20,
            "market": 0.10,
            "override": 0.05,
        }

    def score(self, buyer: Dict[str, Any], listing: Dict[str, Any], criteria: List[Dict[str, Any]]) -> MatchScore:
        criterion_results: List[CriterionResult] = []
        for criterion in criteria:
            result = self._evaluate_criterion(criterion, listing)
            criterion_results.append(result)
            if criterion["requirement_type"] == "must" and not result.passed:
                return MatchScore(
                    listing_id=listing["id"],
                    buyer_id=buyer["id"],
                    score=0.0,
                    criterion_results=criterion_results,
                    rejected=True,
                    rejection_reason=result.explanation,
                )

        components = {
            "price": self._price_score(buyer, listing),
            "space": self._space_score(buyer, listing),
            "location": self._location_score(buyer, listing),
            "lifestyle": self._lifestyle_score(buyer, listing, criteria),
            "market": self._market_signal_score(listing),
            "override": 0.0,
        }

        final_score = sum(components[name] * weight for name, weight in self.weights.items())
        return MatchScore(
            listing_id=listing["id"],
            buyer_id=buyer["id"],
            score=round(final_score * 100, 2),
            criterion_results=criterion_results,
        )

    def _evaluate_criterion(self, criterion: Dict[str, Any], listing: Dict[str, Any]) -> CriterionResult:
        field = criterion["field"]
        operator = criterion.get("operator", "=")
        value = criterion.get("value")
        listing_value = listing.get(field)

        passed = True
        explanation = ""
        if operator == ">=" and listing_value is not None:
            passed = listing_value >= value
        elif operator == "<=" and listing_value is not None:
            passed = listing_value <= value
        elif operator == "IN" and listing_value is not None:
            passed = listing_value in value
        elif operator == "CONTAINS_ANY" and listing_value:
            passed = bool(set(value) & set(listing_value))
        elif operator == "WITHIN_DISTANCE":
            # Expect listing_value to already include a computed distance
            passed = listing.get("distance_minutes") <= value
        else:
            passed = listing_value == value

        explanation = (
            f"{field} requirement ({operator} {value}) => {'PASS' if passed else 'FAIL'}"
        )
        score_component = criterion.get("weight", 1.0) if passed else 0.0
        return CriterionResult(
            criterion_id=criterion["id"],
            passed=passed,
            score_component=score_component,
            explanation=explanation,
        )

    def _price_score(self, buyer: Dict[str, Any], listing: Dict[str, Any]) -> float:
        price = listing.get("price")
        min_budget = buyer.get("budget_min")
        max_budget = buyer.get("budget_max")
        if not price or not min_budget or not max_budget:
            return 0.5
        target = (min_budget + max_budget) / 2
        span = max_budget - min_budget or 1
        delta = abs(price - target)
        normalized = max(0.0, 1 - (delta / span))
        return normalized

    def _space_score(self, buyer: Dict[str, Any], listing: Dict[str, Any]) -> float:
        desired_beds = buyer.get("min_beds", 0)
        desired_baths = buyer.get("min_baths", 0)
        bed_score = min(1.0, (listing.get("beds", 0) - desired_beds + 1) / 2)
        bath_score = min(1.0, (listing.get("baths", 0) - desired_baths + 1) / 2)
        return max(0.0, (bed_score + bath_score) / 2)

    def _location_score(self, buyer: Dict[str, Any], listing: Dict[str, Any]) -> float:
        commute_minutes = buyer.get("commute_minutes")
        distance = listing.get("distance_minutes")
        if not commute_minutes or distance is None:
            return 0.5
        if distance <= commute_minutes:
            return 1 - (distance / (commute_minutes * 1.5))
        return max(0.0, 1 - ((distance - commute_minutes) / commute_minutes))

    def _lifestyle_score(self, buyer: Dict[str, Any], listing: Dict[str, Any], criteria: List[Dict[str, Any]]) -> float:
        tags = {c["value"] for c in criteria if c["field"] == "style"}
        listing_tags = set(listing.get("style_tags", []))
        if not tags:
            return 0.5
        overlap = len(tags & listing_tags)
        return min(1.0, overlap / max(len(tags), 1))

    def _market_signal_score(self, listing: Dict[str, Any]) -> float:
        days_on_market = listing.get("dom") or 0
        price_drop = listing.get("price_drop_percent") or 0
        score = 0.5
        if days_on_market < 10:
            score += 0.2
        elif days_on_market > 45:
            score -= 0.2
        if price_drop >= 5:
            score += 0.2
        return min(max(score, 0.0), 1.0)
