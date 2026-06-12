-- ECHO Phase 1 — Initial schema
-- Idempotent: aman dijalankan berulang kali.
-- Jalankan di psql atau lewat scripts/run_migrations.py

BEGIN;

-- Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ── users ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT        NOT NULL,
    password_hash TEXT        NOT NULL,
    org_name      TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT users_email_unique UNIQUE (email)
);

-- ── postmortems ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS postmortems (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title            TEXT        NOT NULL,
    incident_date    TEXT        NOT NULL,   -- ISO-8601 "YYYY-MM-DD"
    raw_content      TEXT        NOT NULL,
    summary          TEXT,
    root_causes      JSONB,                  -- list[str]
    action_items     JSONB,                  -- list[{description, owner, status, ticket_ref}]
    severity         TEXT        CHECK (severity IN ('P0','P1','P2','P3')),
    systems_affected JSONB,                  -- list[str]
    embedding        vector(1024),           -- Voyage-3-large dims (Phase 3)
    has_recurrence   BOOLEAN     NOT NULL DEFAULT false,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── indexes ───────────────────────────────────────────────────────────────────

-- Filter per user (list + pattern score)
CREATE INDEX IF NOT EXISTS idx_postmortems_user_created
    ON postmortems (user_id, created_at DESC);

-- Cosine similarity search (Phase 3 — ivfflat)
-- lists=10: efektif mulai dari ~10 baris, cocok untuk dataset hackathon
CREATE INDEX IF NOT EXISTS idx_postmortems_embedding_cosine
    ON postmortems
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

COMMIT;
