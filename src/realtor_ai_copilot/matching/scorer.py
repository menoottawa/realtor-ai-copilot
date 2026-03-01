"""Score and rank MLS listings against a buyer profile."""

from __future__ import annotations

from realtor_ai_copilot.models import BuyerProfile, Listing, MatchResult

# Weights must sum to 100
_WEIGHT_PRICE = 35
_WEIGHT_BEDROOMS = 20
_WEIGHT_BATHROOMS = 10
_WEIGHT_SQFT = 15
_WEIGHT_CITY = 10
_WEIGHT_PROPERTY_TYPE = 10


def _score_price(listing: Listing, profile: BuyerProfile) -> tuple[float, list[str], list[str]]:
    """Return (score_contribution, highlights, concerns) for price."""
    highlights: list[str] = []
    concerns: list[str] = []

    if listing.price > profile.max_price:
        over_pct = (listing.price - profile.max_price) / profile.max_price * 100
        concerns.append(f"${listing.price:,.0f} is {over_pct:.1f}% over max budget")
        return 0.0, highlights, concerns

    if profile.min_price > 0 and listing.price < profile.min_price:
        concerns.append(f"${listing.price:,.0f} is below minimum price ${profile.min_price:,.0f}")
        return 0.0, highlights, concerns

    budget_used = listing.price / profile.max_price
    # Award full marks for listings using 60-100% of the budget (well-matched)
    if budget_used >= 0.60:
        score = _WEIGHT_PRICE * 1.0
        highlights.append(f"Price ${listing.price:,.0f} fits within budget")
    else:
        # Partial credit — listing is affordable but potentially under-specified
        score = _WEIGHT_PRICE * (budget_used / 0.60)
        highlights.append(f"Price ${listing.price:,.0f} is within budget")

    return score, highlights, concerns


def _score_bedrooms(listing: Listing, profile: BuyerProfile) -> tuple[float, list[str], list[str]]:
    highlights: list[str] = []
    concerns: list[str] = []

    if listing.bedrooms < profile.min_bedrooms:
        concerns.append(
            f"Only {listing.bedrooms} bed(s); buyer needs at least {profile.min_bedrooms}"
        )
        return 0.0, highlights, concerns

    highlights.append(f"{listing.bedrooms} bedroom(s) meets requirement")
    # Bonus for extras (up to 1 extra bedroom = full marks)
    extra = min(listing.bedrooms - profile.min_bedrooms, 1)
    score = _WEIGHT_BEDROOMS * (0.85 + 0.15 * extra)
    return score, highlights, concerns


def _score_bathrooms(
    listing: Listing, profile: BuyerProfile
) -> tuple[float, list[str], list[str]]:
    highlights: list[str] = []
    concerns: list[str] = []

    if listing.bathrooms < profile.min_bathrooms:
        concerns.append(
            f"Only {listing.bathrooms} bath(s); buyer needs at least {profile.min_bathrooms}"
        )
        return 0.0, highlights, concerns

    highlights.append(f"{listing.bathrooms} bathroom(s) meets requirement")
    return _WEIGHT_BATHROOMS * 1.0, highlights, concerns


def _score_sqft(listing: Listing, profile: BuyerProfile) -> tuple[float, list[str], list[str]]:
    highlights: list[str] = []
    concerns: list[str] = []

    if profile.min_sqft is None:
        return _WEIGHT_SQFT * 1.0, highlights, concerns  # no preference → full marks

    if listing.sqft is None:
        concerns.append("Square footage not provided")
        return _WEIGHT_SQFT * 0.5, highlights, concerns

    if listing.sqft < profile.min_sqft:
        concerns.append(
            f"Only {listing.sqft:,.0f} sqft; buyer wants at least {profile.min_sqft:,.0f}"
        )
        return 0.0, highlights, concerns

    highlights.append(f"{listing.sqft:,.0f} sqft meets requirement")
    return _WEIGHT_SQFT * 1.0, highlights, concerns


def _score_city(listing: Listing, profile: BuyerProfile) -> tuple[float, list[str], list[str]]:
    highlights: list[str] = []
    concerns: list[str] = []

    if not profile.preferred_cities:
        return _WEIGHT_CITY * 1.0, highlights, concerns  # no preference → full marks

    preferred = [c.lower() for c in profile.preferred_cities]
    if listing.city.lower() in preferred:
        highlights.append(f"Located in preferred city: {listing.city}")
        return _WEIGHT_CITY * 1.0, highlights, concerns

    concerns.append(f"{listing.city} is not in preferred cities")
    return 0.0, highlights, concerns


def _score_property_type(
    listing: Listing, profile: BuyerProfile
) -> tuple[float, list[str], list[str]]:
    highlights: list[str] = []
    concerns: list[str] = []

    if not profile.preferred_property_types:
        return _WEIGHT_PROPERTY_TYPE * 1.0, highlights, concerns

    preferred = [pt.lower() for pt in profile.preferred_property_types]
    if listing.property_type.lower() in preferred:
        highlights.append(f"Property type '{listing.property_type}' matches preference")
        return _WEIGHT_PROPERTY_TYPE * 1.0, highlights, concerns

    concerns.append(f"Property type '{listing.property_type}' is not preferred")
    return 0.0, highlights, concerns


def _score_listing(listing: Listing, profile: BuyerProfile) -> MatchResult:
    """Compute a MatchResult for a single listing/profile pair."""
    all_highlights: list[str] = []
    all_concerns: list[str] = []
    total = 0.0

    for scorer in (
        _score_price,
        _score_bedrooms,
        _score_bathrooms,
        _score_sqft,
        _score_city,
        _score_property_type,
    ):
        pts, h, c = scorer(listing, profile)
        total += pts
        all_highlights.extend(h)
        all_concerns.extend(c)

    return MatchResult(
        listing=listing,
        score=round(min(total, 100.0), 1),
        highlights=all_highlights,
        concerns=all_concerns,
    )


def score_listings(
    listings: list[Listing],
    profile: BuyerProfile,
    *,
    top_n: int | None = None,
    min_score: float = 0.0,
) -> list[MatchResult]:
    """Score and rank a list of listings against a buyer profile.

    Parameters
    ----------
    listings:
        MLS listings to evaluate.
    profile:
        The buyer's search criteria.
    top_n:
        If given, return only the top N matches by score.
    min_score:
        Exclude results below this score (0–100).

    Returns
    -------
    list[MatchResult]
        Results sorted descending by score.
    """
    results = [_score_listing(listing, profile) for listing in listings]
    results = [r for r in results if r.score >= min_score]
    results.sort(key=lambda r: r.score, reverse=True)
    if top_n is not None:
        results = results[:top_n]
    return results
