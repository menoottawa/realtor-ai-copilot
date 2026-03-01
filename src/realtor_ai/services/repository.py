"""Database helper queries used by pipelines."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Iterable, Sequence

from sqlalchemy import Select, and_, exists, func, select
from sqlalchemy.orm import Session

from realtor_ai.models import (
    AIAnalysis,
    Agent,
    BuyerCriterion,
    BuyerProfile,
    Listing,
    ListingEnrichment,
    ListingVersion,
    MatchCriterionScore,
    MatchResult,
    Packet,
    PacketExport,
)


def get_active_buyers(session: Session) -> Sequence[BuyerProfile]:
    stmt = select(BuyerProfile).where(BuyerProfile.status == "active")
    return session.scalars(stmt).all()


def get_buyer_criteria(session: Session, buyer_id: uuid.UUID) -> Sequence[BuyerCriterion]:
    stmt = select(BuyerCriterion).where(BuyerCriterion.buyer_id == buyer_id)
    return session.scalars(stmt).all()


def get_recent_listings(
    session: Session,
    buyer: BuyerProfile,
    hours_back: int = 48,
    limit: int = 50,
) -> Sequence[Listing]:
    filters = []
    if buyer.budget_max:
        filters.append(Listing.price <= buyer.budget_max * 1.1)
    if buyer.budget_min:
        filters.append(Listing.price >= buyer.budget_min * 0.8)
    stmt: Select = (
        select(Listing)
        .where(*filters)
        .where(Listing.last_seen >= datetime.utcnow() - timedelta(hours=hours_back))
        .order_by(Listing.last_seen.desc())
        .limit(limit)
    )
    return session.scalars(stmt).all()


def upsert_listing(session: Session, payload: dict) -> Listing:
    listing = session.scalar(
        select(Listing).where(
            Listing.mls_source == payload.get("mls_source"),
            Listing.mls_id == payload.get("mls_id"),
        )
    )
    if not listing:
        listing = Listing(
            id=uuid.uuid4(),
            mls_source=payload.get("mls_source"),
            mls_id=payload.get("mls_id"),
        )
        session.add(listing)

    listing.address = payload.get("address")
    listing.city = payload.get("city")
    listing.state = payload.get("state")
    listing.zip = payload.get("zip")
    listing.lat = payload.get("lat")
    listing.lng = payload.get("lng")
    listing.price = payload.get("price")
    listing.beds = payload.get("beds")
    listing.baths = payload.get("baths")
    listing.sqft = payload.get("sqft")
    listing.year_built = payload.get("year_built")
    listing.lot_sqft = payload.get("lot_sqft")
    listing.hoa_monthly = payload.get("hoa")
    listing.status = payload.get("status")
    listing.last_seen = payload.get("last_seen", datetime.utcnow())
    listing.style_tags = payload.get("style_tags", [])
    listing.dom = payload.get("dom")
    listing.price_drop_percent = payload.get("price_drop_percent")

    session.add(
        ListingVersion(listing=listing, raw_payload=payload)
    )
    return listing


def listings_needing_enrichment(session: Session, limit: int = 50) -> Sequence[Listing]:
    subq = (
        select(ListingEnrichment.listing_id)
        .where(ListingEnrichment.data_type == "schools")
        .subquery()
    )
    stmt = select(Listing).where(~Listing.id.in_(select(subq.c.listing_id))).limit(limit)
    return session.scalars(stmt).all()


def record_enrichment(
    session: Session, listing: Listing, data_type: str, payload: dict, source: str
) -> None:
    session.add(
        ListingEnrichment(
            listing_id=listing.id,
            data_type=data_type,
            payload=payload,
            source=source,
        )
    )


def upsert_match(
    session: Session, buyer: BuyerProfile, listing: Listing, score: float
) -> MatchResult:
    match = session.scalar(
        select(MatchResult).where(
            MatchResult.buyer_id == buyer.id, MatchResult.listing_id == listing.id
        )
    )
    if not match:
        match = MatchResult(buyer=buyer, listing=listing)
    match.score = score
    match.status = "new"
    session.add(match)
    return match


def attach_criterion_scores(
    session: Session,
    match: MatchResult,
    details: Iterable[dict],
) -> None:
    session.query(MatchCriterionScore).filter_by(match_id=match.id).delete()
    for detail in details:
        session.add(
            MatchCriterionScore(
                match_id=match.id,
                criterion_id=detail["criterion_id"],
                score_component=detail["score_component"],
                explanation=detail["explanation"],
            )
        )


def matches_missing_analysis(session: Session, limit: int = 10) -> Sequence[MatchResult]:
    stmt = (
        select(MatchResult)
        .where(MatchResult.status == "new")
        .where(~exists(select(AIAnalysis.match_id).where(AIAnalysis.match_id == MatchResult.id)))
        .limit(limit)
    )
    return session.scalars(stmt).all()


def packets_pending_render(session: Session, limit: int = 20) -> Sequence[Packet]:
    stmt = (
        select(Packet)
        .where(Packet.status == "approved")
        .where(
            ~exists(
                select(PacketExport.id).where(PacketExport.packet_id == Packet.id)
            )
        )
        .limit(limit)
    )
    return session.scalars(stmt).all()


def recent_matches_for_notification(
    session: Session, minutes: int = 10
) -> Sequence[MatchResult]:
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    stmt = (
        select(MatchResult)
        .where(MatchResult.created_at >= cutoff)
        .where(MatchResult.status == "new")
    )
    return session.scalars(stmt).all()
