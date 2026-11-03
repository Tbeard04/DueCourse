-- DueCourse embedded audit/state database (SQLite).
-- Single source of truth for the schema; applied idempotently by store.py.

CREATE TABLE IF NOT EXISTS clients (
    company_number TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    contact_name   TEXT NOT NULL,
    contact_email  TEXT NOT NULL,   -- fictional; never a real address
    notes          TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS runs (
    id          TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,       -- sync | triage | draft | digest | weekly
    as_of_date  TEXT NOT NULL,       -- ISO date the run computed against
    started_at  TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS triage (
    run_id         TEXT NOT NULL REFERENCES runs(id),
    company_number TEXT NOT NULL,
    filing_kind    TEXT NOT NULL,
    due_date       TEXT NOT NULL,
    status         TEXT NOT NULL,
    days_until_due INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS drafts (
    id             TEXT PRIMARY KEY,
    run_id         TEXT REFERENCES runs(id),
    company_number TEXT NOT NULL,
    subject        TEXT NOT NULL,
    body           TEXT NOT NULL,
    citations_json TEXT NOT NULL DEFAULT '[]',
    triage_json    TEXT NOT NULL,   -- TriageItem snapshot the draft was written against
    model_used     TEXT NOT NULL,   -- provenance: model id or "template"
    created_at     TEXT NOT NULL,
    state          TEXT NOT NULL DEFAULT 'pending'  -- pending | decided
);

-- Append-only: decisions are never updated or deleted. This is the audit trail.
CREATE TABLE IF NOT EXISTS decisions (
    draft_id    TEXT NOT NULL REFERENCES drafts(id),
    action      TEXT NOT NULL,       -- approved | edited | rejected
    edited_body TEXT,
    reason      TEXT,                -- required when action = rejected (enforced in code)
    decided_at  TEXT NOT NULL
);
