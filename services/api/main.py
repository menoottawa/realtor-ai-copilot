"""FastAPI backend for buyer search + lead capture."""
from __future__ import annotations

import uuid
from typing import List

from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, Field

from skills.real_estate_search import search as search_skill

app = FastAPI(title="Realtor AI Copilot API", version="0.1.0")


class SearchRequest(BaseModel):
    location: str = Field(..., example="Lakeway, TX")
    min_price: int | None = Field(default=0, ge=0)
    max_price: int | None = Field(default=1000000, ge=0)
    beds: int | None = Field(default=0, ge=0)
    baths: int | None = Field(default=0, ge=0)
    must_haves: List[str] = Field(default_factory=list)
    nice_to_haves: List[str] = Field(default_factory=list)
    max_results: int = Field(default=5, ge=1, le=10)


class ListingResult(BaseModel):
    mls_id: str
    address: str
    price: int
    beds: float
    baths: float
    sqft: int | None
    lot_sqft: int | None
    hoa: float | None
    dom: int | None
    style_tags: List[str] = Field(default_factory=list)
    match_score: float
    summary: str | None
    detail_url: str | None
    notes: List[str] | str | None


class LeadPayload(BaseModel):
    name: str
    email: str
    phone: str | None = None
    interested_listing_ids: List[str] = Field(default_factory=list)
    timeline: str | None = None
    financing_status: str | None = None


class TourRequest(BaseModel):
    name: str
    email: str
    phone: str
    listing_id: str
    preferred_date: str
    notes: str | None = None


LEAD_STORE: list[dict] = []
TOUR_STORE: list[dict] = []


@app.post("/search", response_model=list[ListingResult])
def search_listings(payload: SearchRequest):
    results = search_skill.run(payload.dict())
    if not results:
        raise HTTPException(status_code=404, detail="No listings matched. Try adjusting criteria.")
    return results


@app.post("/leads")
def create_lead(payload: LeadPayload):
    lead = payload.dict() | {"id": str(uuid.uuid4())}
    LEAD_STORE.append(lead)
    # TODO: persist to DB / CRM and send notification via OpenClaw messaging
    return {"status": "ok", "lead_id": lead["id"]}


@app.post("/tours")
def request_tour(payload: TourRequest):
    tour = payload.dict() | {"id": str(uuid.uuid4())}
    TOUR_STORE.append(tour)
    # TODO: send calendar invite / Telegram alert
    return {"status": "ok", "tour_id": tour["id"]}


@app.get("/health")
def healthcheck():
    return {"status": "ready"}
