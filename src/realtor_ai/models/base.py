"""SQLAlchemy declarative base and ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Agent(TimestampMixin, Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str | None]
    brokerage: Mapped[str | None]
    plan_tier: Mapped[str | None]

    buyers: Mapped[list["BuyerProfile"]] = relationship(back_populates="agent")
    packets: Mapped[list["Packet"]] = relationship(back_populates="agent")


class BuyerProfile(TimestampMixin, Base):
    __tablename__ = "buyer_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        Enum("active", "paused", "archived", name="buyer_status"),
        default="active",
    )
    budget_min: Mapped[int | None]
    budget_max: Mapped[int | None]
    location_polygon: Mapped[dict | None] = mapped_column(JSON)
    commute_center: Mapped[dict | None] = mapped_column(JSON)
    commute_minutes: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(Text)

    agent: Mapped[Agent] = relationship(back_populates="buyers")
    criteria: Mapped[list["BuyerCriterion"]] = relationship(
        back_populates="buyer", cascade="all, delete-orphan"
    )
    preference_tags: Mapped[list["BuyerPreferenceTag"]] = relationship(
        back_populates="buyer", cascade="all, delete-orphan"
    )
    matches: Mapped[list["MatchResult"]] = relationship(back_populates="buyer")
    packets: Mapped[list["Packet"]] = relationship(back_populates="buyer")


class BuyerCriterion(TimestampMixin, Base):
    __tablename__ = "buyer_criteria"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("buyer_profiles.id", ondelete="CASCADE")
    )
    requirement_type: Mapped[str] = mapped_column(
        Enum("must", "nice", name="criterion_requirement")
    )
    field: Mapped[str] = mapped_column(String(100))
    operator: Mapped[str] = mapped_column(String(50), default="=")
    value: Mapped[dict | None] = mapped_column(JSON)
    weight: Mapped[float] = mapped_column(Numeric(5, 2), default=1.0)

    buyer: Mapped[BuyerProfile] = relationship(back_populates="criteria")
    criterion_scores: Mapped[list["MatchCriterionScore"]] = relationship(
        back_populates="criterion"
    )


class BuyerPreferenceTag(TimestampMixin, Base):
    __tablename__ = "buyer_preference_tags"

    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("buyer_profiles.id", ondelete="CASCADE"), primary_key=True
    )
    tag: Mapped[str] = mapped_column(String(100), primary_key=True)

    buyer: Mapped[BuyerProfile] = relationship(back_populates="preference_tags")


class Listing(TimestampMixin, Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mls_source: Mapped[str | None] = mapped_column(String(100))
    mls_id: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None]
    city: Mapped[str | None]
    state: Mapped[str | None]
    zip: Mapped[str | None]
    lat: Mapped[float | None]
    lng: Mapped[float | None]
    price: Mapped[int | None]
    beds: Mapped[float | None]
    baths: Mapped[float | None]
    sqft: Mapped[int | None]
    year_built: Mapped[int | None]
    lot_sqft: Mapped[int | None]
    hoa_monthly: Mapped[float | None]
    status: Mapped[str | None]
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    style_tags: Mapped[list[str]] = mapped_column(ARRAY(String(50)), default=list)
    dom: Mapped[int | None]
    price_drop_percent: Mapped[float | None]

    versions: Mapped[list["ListingVersion"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )
    enrichments: Mapped[list["ListingEnrichment"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )
    feature_vector: Mapped["ListingFeatureVector" | None] = relationship(
        back_populates="listing", uselist=False, cascade="all, delete-orphan"
    )
    matches: Mapped[list["MatchResult"]] = relationship(back_populates="listing")


class ListingVersion(TimestampMixin, Base):
    __tablename__ = "listing_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE")
    )
    raw_payload: Mapped[dict] = mapped_column(JSON)

    listing: Mapped[Listing] = relationship(back_populates="versions")


class ListingEnrichment(TimestampMixin, Base):
    __tablename__ = "listing_enrichment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE")
    )
    data_type: Mapped[str] = mapped_column(String(50))
    payload: Mapped[dict] = mapped_column(JSON)
    source: Mapped[str | None] = mapped_column(String(100))

    listing: Mapped[Listing] = relationship(back_populates="enrichments")


class ListingFeatureVector(TimestampMixin, Base):
    __tablename__ = "listing_feature_vectors"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True
    )
    embedding: Mapped[list[float] | None] = mapped_column(ARRAY(Float))
    model_version: Mapped[str | None]

    listing: Mapped[Listing] = relationship(back_populates="feature_vector")


class MatchResult(TimestampMixin, Base):
    __tablename__ = "match_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("buyer_profiles.id", ondelete="CASCADE")
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE")
    )
    score: Mapped[float] = mapped_column(Numeric(5, 2))
    status: Mapped[str] = mapped_column(
        Enum("new", "in_review", "sent", "dismissed", name="match_status"),
        default="new",
    )

    buyer: Mapped[BuyerProfile] = relationship(back_populates="matches")
    listing: Mapped[Listing] = relationship(back_populates="matches")
    criterion_scores: Mapped[list["MatchCriterionScore"]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )
    analysis: Mapped["AIAnalysis" | None] = relationship(
        back_populates="match", uselist=False, cascade="all, delete-orphan"
    )
    feedback: Mapped[list["AgentFeedback"]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )
    packets: Mapped[list["Packet"]] = relationship(
        secondary="packet_properties", back_populates="matches"
    )


class MatchCriterionScore(TimestampMixin, Base):
    __tablename__ = "match_criterion_scores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_results.id", ondelete="CASCADE")
    )
    criterion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("buyer_criteria.id", ondelete="CASCADE")
    )
    score_component: Mapped[float] = mapped_column(Numeric(5, 2))
    explanation: Mapped[str | None] = mapped_column(Text)

    match: Mapped[MatchResult] = relationship(back_populates="criterion_scores")
    criterion: Mapped[BuyerCriterion] = relationship(back_populates="criterion_scores")


class AIAnalysis(TimestampMixin, Base):
    __tablename__ = "ai_analyses"

    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_results.id", ondelete="CASCADE"), primary_key=True
    )
    model_version: Mapped[str | None]
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 2))

    match: Mapped[MatchResult] = relationship(back_populates="analysis")
    sections: Mapped[list["AISection"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )


class AISection(TimestampMixin, Base):
    __tablename__ = "ai_sections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_results.id", ondelete="CASCADE")
    )
    section_type: Mapped[str] = mapped_column(
        Enum("summary", "pros", "cons", "risks", "neighborhood", name="ai_section_type")
    )
    content: Mapped[str] = mapped_column(Text)
    citations: Mapped[dict | None] = mapped_column(JSON)

    analysis: Mapped[AIAnalysis] = relationship(back_populates="sections")
    match: Mapped[MatchResult] = relationship(back_populates="analysis")


class Packet(TimestampMixin, Base):
    __tablename__ = "packets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("buyer_profiles.id", ondelete="CASCADE")
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        Enum("draft", "approved", "sent", name="packet_status"), default="draft"
    )
    template: Mapped[str | None]
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    buyer: Mapped[BuyerProfile] = relationship(back_populates="packets")
    agent: Mapped[Agent] = relationship(back_populates="packets")
    properties: Mapped[list["PacketProperty"]] = relationship(
        back_populates="packet", cascade="all, delete-orphan"
    )
    exports: Mapped[list["PacketExport"]] = relationship(
        back_populates="packet", cascade="all, delete-orphan"
    )
    matches: Mapped[list[MatchResult]] = relationship(
        secondary="packet_properties", back_populates="packets"
    )


class PacketProperty(TimestampMixin, Base):
    __tablename__ = "packet_properties"

    packet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("packets.id", ondelete="CASCADE"), primary_key=True
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_results.id", ondelete="CASCADE"), primary_key=True
    )
    sort_order: Mapped[int | None]

    packet: Mapped[Packet] = relationship(back_populates="properties")
    match: Mapped[MatchResult] = relationship(back_populates="packets")


class PacketExport(TimestampMixin, Base):
    __tablename__ = "packet_exports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    packet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("packets.id", ondelete="CASCADE")
    )
    format: Mapped[str] = mapped_column(
        Enum("pdf", "slides", "doc", name="packet_export_format")
    )
    storage_url: Mapped[str] = mapped_column(String(512))

    packet: Mapped[Packet] = relationship(back_populates="exports")


class AgentFeedback(TimestampMixin, Base):
    __tablename__ = "agent_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_results.id", ondelete="CASCADE")
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE")
    )
    feedback_type: Mapped[str] = mapped_column(
        Enum("approve", "reject", "edit", name="feedback_type")
    )
    notes: Mapped[str | None] = mapped_column(Text)

    match: Mapped[MatchResult] = relationship(back_populates="feedback")
    agent: Mapped[Agent] = relationship()
    corrections: Mapped[list["CorrectionItem"]] = relationship(
        back_populates="feedback", cascade="all, delete-orphan"
    )


class CorrectionItem(TimestampMixin, Base):
    __tablename__ = "correction_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    feedback_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_feedback.id", ondelete="CASCADE")
    )
    field: Mapped[str] = mapped_column(String(100))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)

    feedback: Mapped[AgentFeedback] = relationship(back_populates="corrections")
