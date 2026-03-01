-- Core schema for realtor-ai-copilot
-- Generated: 2026-03-01

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE agents (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    brokerage TEXT,
    plan_tier TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE buyer_profiles (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    name TEXT NOT NULL,
    status TEXT CHECK (status IN ('active','paused','archived')),
    budget_min INT,
    budget_max INT,
    location_polygon GEOGRAPHY,
    commute_center GEOGRAPHY,
    commute_minutes INT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE buyer_criteria (
    id UUID PRIMARY KEY,
    buyer_id UUID REFERENCES buyer_profiles(id),
    requirement_type TEXT CHECK (requirement_type IN ('must','nice')),
    field TEXT,
    operator TEXT,
    value JSONB,
    weight NUMERIC DEFAULT 1.0
);

CREATE TABLE buyer_preference_tags (
    buyer_id UUID REFERENCES buyer_profiles(id),
    tag TEXT,
    PRIMARY KEY (buyer_id, tag)
);

CREATE TABLE listings (
    id UUID PRIMARY KEY,
    mls_source TEXT,
    mls_id TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    price INT,
    beds NUMERIC,
    baths NUMERIC,
    sqft INT,
    year_built INT,
    lot_sqft INT,
    hoa_monthly NUMERIC,
    status TEXT,
    last_seen TIMESTAMPTZ
);

CREATE TABLE listing_versions (
    id BIGSERIAL PRIMARY KEY,
    listing_id UUID REFERENCES listings(id),
    raw_payload JSONB,
    fetched_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE listing_enrichment (
    id BIGSERIAL PRIMARY KEY,
    listing_id UUID REFERENCES listings(id),
    data_type TEXT,
    payload JSONB,
    source TEXT,
    scored_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE listing_feature_vectors (
    listing_id UUID PRIMARY KEY REFERENCES listings(id),
    embedding VECTOR(1536),
    model_version TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE match_results (
    id UUID PRIMARY KEY,
    buyer_id UUID REFERENCES buyer_profiles(id),
    listing_id UUID REFERENCES listings(id),
    score NUMERIC,
    status TEXT CHECK (status IN ('new','in_review','sent','dismissed')),
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE match_criterion_scores (
    id BIGSERIAL PRIMARY KEY,
    match_id UUID REFERENCES match_results(id),
    criterion_id UUID REFERENCES buyer_criteria(id),
    score_component NUMERIC,
    explanation TEXT
);

CREATE TABLE ai_analyses (
    match_id UUID PRIMARY KEY REFERENCES match_results(id),
    model_version TEXT,
    confidence NUMERIC,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ai_sections (
    id BIGSERIAL PRIMARY KEY,
    match_id UUID REFERENCES match_results(id),
    section_type TEXT CHECK (section_type IN ('summary','pros','cons','risks','neighborhood')),
    content TEXT,
    citations JSONB
);

CREATE TABLE packets (
    id UUID PRIMARY KEY,
    buyer_id UUID REFERENCES buyer_profiles(id),
    agent_id UUID REFERENCES agents(id),
    title TEXT,
    status TEXT CHECK (status IN ('draft','approved','sent')),
    template TEXT,
    approved_at TIMESTAMPTZ
);

CREATE TABLE packet_properties (
    packet_id UUID REFERENCES packets(id),
    match_id UUID REFERENCES match_results(id),
    sort_order INT,
    PRIMARY KEY (packet_id, match_id)
);

CREATE TABLE packet_exports (
    id UUID PRIMARY KEY,
    packet_id UUID REFERENCES packets(id),
    format TEXT CHECK (format IN ('pdf','slides','doc')),
    storage_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agent_feedback (
    id UUID PRIMARY KEY,
    match_id UUID REFERENCES match_results(id),
    agent_id UUID REFERENCES agents(id),
    feedback_type TEXT CHECK (feedback_type IN ('approve','reject','edit')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE correction_items (
    id BIGSERIAL PRIMARY KEY,
    feedback_id UUID REFERENCES agent_feedback(id),
    field TEXT,
    old_value TEXT,
    new_value TEXT
);
