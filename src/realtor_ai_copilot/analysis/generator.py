"""Generate agent-facing narrative analyses using OpenAI (with fallback)."""

from __future__ import annotations

import os
import textwrap
from typing import Optional

from realtor_ai_copilot.models import BuyerProfile, MatchResult

_DEFAULT_MODEL = "gpt-4o-mini"


def _build_prompt(result: MatchResult, profile: BuyerProfile) -> str:
    listing = result.listing
    highlights_txt = "\n".join(f"  - {h}" for h in result.highlights) or "  None"
    concerns_txt = "\n".join(f"  - {c}" for c in result.concerns) or "  None"

    return textwrap.dedent(f"""
        You are a professional real estate buyer's agent assistant. Write a concise,
        informative analysis of the following listing for the buyer's agent. The tone
        should be professional and objective — highlighting genuine strengths, surfacing
        real concerns, and concluding with an overall recommendation.

        BUYER: {profile.name}
        BUYER NOTES: {profile.notes or "None provided"}

        LISTING: {listing.full_address}
        MLS ID: {listing.mls_id}
        Price: ${listing.price:,.0f}
        Bedrooms: {listing.bedrooms}  |  Bathrooms: {listing.bathrooms}
        Sqft: {listing.sqft or "N/A"}  |  Year Built: {listing.year_built or "N/A"}
        Property Type: {listing.property_type}
        Match Score: {result.score}/100

        KEY HIGHLIGHTS:
        {highlights_txt}

        KEY CONCERNS:
        {concerns_txt}

        Property Description:
        {listing.description or "No description provided."}

        Write 2-3 short paragraphs. End with a clear "Recommendation:" sentence.
    """).strip()


def _fallback_analysis(result: MatchResult, profile: BuyerProfile) -> str:
    """Rule-based fallback used when no OpenAI key is available."""
    listing = result.listing
    parts: list[str] = []

    # Opening
    parts.append(
        f"This {listing.property_type.lower()} at {listing.full_address} "
        f"is listed at ${listing.price:,.0f} and achieves a match score of "
        f"{result.score}/100 against {profile.name}'s stated criteria."
    )

    # Highlights
    if result.highlights:
        parts.append("Strengths include: " + "; ".join(result.highlights) + ".")

    # Concerns
    if result.concerns:
        parts.append("Areas of concern: " + "; ".join(result.concerns) + ".")

    # Price-per-sqft insight
    if listing.price_per_sqft:
        parts.append(
            f"At ${listing.price_per_sqft:,.0f}/sqft, this property offers "
            f"{'competitive' if listing.price_per_sqft < 300 else 'premium'} value."
        )

    # Recommendation
    if result.score >= 75:
        rec = "Recommendation: Strong match — recommend scheduling a showing promptly."
    elif result.score >= 50:
        rec = "Recommendation: Moderate match — worth a closer look if top picks fall through."
    else:
        rec = "Recommendation: Below threshold — suggest deprioritising unless criteria change."
    parts.append(rec)

    return " ".join(parts)


def generate_analysis(
    result: MatchResult,
    profile: BuyerProfile,
    *,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """Generate a narrative analysis for a MatchResult.

    Attempts to use OpenAI; falls back to a rule-based summary if no API key
    is available or if the API call fails.

    Parameters
    ----------
    result:
        The scored listing match to analyse.
    profile:
        The buyer's profile (for context).
    api_key:
        OpenAI API key.  If omitted, the ``OPENAI_API_KEY`` environment variable
        is used.  If neither is present the fallback analysis is returned.
    model:
        OpenAI model name.  Defaults to ``OPENAI_MODEL`` env var or ``gpt-4o-mini``.

    Returns
    -------
    str
        Narrative analysis text.
    """
    resolved_key = api_key or os.environ.get("OPENAI_API_KEY", "")
    if not resolved_key:
        return _fallback_analysis(result, profile)

    resolved_model = model or os.environ.get("OPENAI_MODEL", _DEFAULT_MODEL)
    prompt = _build_prompt(result, profile)

    try:
        from openai import OpenAI  # imported lazily to avoid hard requirement at import time

        client = OpenAI(api_key=resolved_key)
        response = client.chat.completions.create(
            model=resolved_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=400,
        )
        return response.choices[0].message.content or _fallback_analysis(result, profile)
    except Exception:
        return _fallback_analysis(result, profile)


def generate_analyses(
    results: list[MatchResult],
    profile: BuyerProfile,
    *,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> list[MatchResult]:
    """Add AI-generated analysis to each MatchResult and return the updated list.

    Parameters
    ----------
    results:
        Scored match results (will be mutated — analysis field populated).
    profile:
        The buyer profile.
    api_key:
        OpenAI API key (optional).
    model:
        OpenAI model name (optional).

    Returns
    -------
    list[MatchResult]
        Same list with ``analysis`` populated on every result.
    """
    for result in results:
        result.analysis = generate_analysis(result, profile, api_key=api_key, model=model)
    return results
