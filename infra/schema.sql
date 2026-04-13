-- ══════════════════════════════════════════════════════════════════
-- AlloyDB Schema Setup for FinOps Multi-Agent RAG
-- ══════════════════════════════════════════════════════════════════
-- Run this against your AlloyDB instance via psql:
--   PGPASSWORD="..." psql -h <ALLOYDB_IP> -U postgres -d postgres -f infra/schema.sql
-- ══════════════════════════════════════════════════════════════════

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ── Structured Data: Billing ────────────────────────────────────

CREATE TABLE IF NOT EXISTS billing_data (
    id SERIAL PRIMARY KEY,
    billing_account_id TEXT,
    invoice_month TEXT,
    usage_start_time TEXT,
    usage_end_time TEXT,
    service_id TEXT,
    service_description TEXT,
    sku_id TEXT,
    sku_description TEXT,
    project_id TEXT,
    project_name TEXT,
    cost_type TEXT,
    cost NUMERIC(12,2),
    credits_amount NUMERIC(12,2),
    net_cost NUMERIC(12,2),
    currency TEXT DEFAULT 'USD',
    usage_amount NUMERIC(12,4),
    usage_unit TEXT,
    resource_name TEXT,
    location_region TEXT,
    label_team TEXT,
    label_environment TEXT,
    label_cost_center TEXT,
    label_project_id TEXT,
    label_owner_email TEXT,
    label_created_date TEXT,
    tags_environment TEXT
);

-- ── Structured Data: Idle Resources ─────────────────────────────

CREATE TABLE IF NOT EXISTS idle_resources (
    id SERIAL PRIMARY KEY,
    resource_name TEXT,
    resource_type TEXT,
    project_id TEXT,
    team TEXT,
    environment TEXT,
    region TEXT,
    monthly_cost_usd NUMERIC(10,2),
    last_active_date DATE,
    days_idle INTEGER,
    cpu_avg_pct_14d NUMERIC(5,2),
    connection_count_14d INTEGER,
    invocation_count_21d INTEGER,
    label_owner_email TEXT,
    label_created_date DATE,
    label_team TEXT,
    label_environment TEXT,
    idle_status TEXT,
    flagged_date DATE,
    notes TEXT
);

-- ── Structured Data: Budget Allocation ──────────────────────────

CREATE TABLE IF NOT EXISTS budget_allocation (
    id SERIAL PRIMARY KEY,
    team TEXT UNIQUE NOT NULL,
    cost_center TEXT,
    monthly_budget_usd NUMERIC(10,2),
    q1_2026_budget_usd NUMERIC(10,2),
    alert_threshold_pct NUMERIC(5,2),
    hard_cap_usd NUMERIC(10,2),
    environment_split_prod_pct NUMERIC(5,2),
    environment_split_staging_pct NUMERIC(5,2),
    environment_split_dev_pct NUMERIC(5,2),
    primary_services TEXT,
    budget_owner_email TEXT,
    approved_date DATE,
    chargeback_model TEXT
);

-- ── Vector Store (pgvector) ─────────────────────────────────────

CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    source_file TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_file, chunk_index)
);

-- IVFFlat index for approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

-- ── ADK Session Storage ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS adk_sessions (
    id TEXT PRIMARY KEY,
    app_name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    state JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_app_user
    ON adk_sessions(app_name, user_id);

-- ── Agent Memory ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agent_memory (
    id SERIAL PRIMARY KEY,
    session_id TEXT REFERENCES adk_sessions(id),
    agent_name TEXT NOT NULL,
    memory_key TEXT NOT NULL,
    memory_value JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
