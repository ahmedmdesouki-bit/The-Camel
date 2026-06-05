-- ADAM × StockSense v11 — Supabase / Postgres schema (Sprint 1)
-- Second wall after the Guardrail Service: DB permissions make the ledger
-- append-only and limits read-only to the agent role.

create table if not exists whitelist (
  id uuid primary key default gen_random_uuid(),
  symbol text unique not null,
  asset_type text default 'etf',
  sharia_status text default 'unknown',   -- compliant | non_compliant | unknown
  frozen boolean default false,
  approved_by text,
  scanned_at timestamptz,
  source text
);

create table if not exists instruments (
  symbol text primary key,
  name text, sector text, market text default 'US', currency text default 'USD'
);

create table if not exists prices (
  symbol text, date date, open numeric, high numeric, low numeric,
  close numeric, volume bigint, adj_close numeric, source text,
  ingested_at timestamptz default now(),
  primary key (symbol, date, source)
);

create table if not exists theses (
  id uuid primary key default gen_random_uuid(),
  symbol text, side text, thesis text,
  invalidation text, profit_take text, time_stop text,
  base_rate_json jsonb, created_by text, created_at timestamptz default now(),
  status text default 'open'
);

create table if not exists orders (
  id uuid primary key default gen_random_uuid(),
  symbol text, side text, qty numeric, type text, limit_price numeric,
  status text, broker text, mode text,             -- paper | live
  approval_id uuid, thesis_id uuid references theses(id),
  created_at timestamptz default now(), filled_at timestamptz, fill_price numeric
);

create table if not exists positions (
  symbol text primary key, qty numeric, avg_cost numeric,
  market_value numeric, unrealized_pnl numeric, updated_at timestamptz default now()
);

-- append-only
create table if not exists ledger (
  id uuid primary key default gen_random_uuid(),
  ts timestamptz default now(), type text, symbol text,
  amount numeric, balance_after numeric, ref text, hash text
);

create table if not exists guardrail_events (
  id uuid primary key default gen_random_uuid(),
  ts timestamptz default now(), action_json jsonb,
  decision boolean, reason text, limit_hit text
);

create table if not exists approvals (
  id uuid primary key default gen_random_uuid(),
  action_ref text, status text default 'pending',     -- pending|approved|vetoed|timeout
  requested_at timestamptz default now(), decided_at timestamptz,
  decided_by text, channel text
);

create table if not exists products (
  id uuid primary key default gen_random_uuid(),
  name text, url text, business_model text, sharia_status text,
  status text, mrr numeric default 0, created_at timestamptz default now()
);

create table if not exists runs (
  id uuid primary key default gen_random_uuid(),
  started_at timestamptz default now(), ended_at timestamptz,
  phase int, steps_json jsonb, outcome text
);

create table if not exists config (key text primary key, value jsonb);

-- ============ RLS sketch (enforce with the 'adam' role) ============
-- alter table ledger enable row level security;
-- create policy adam_ledger_insert on ledger for insert to adam with check (true);
-- revoke update, delete on ledger from adam;            -- append-only
-- revoke insert, update, delete on config from adam;    -- founder-owned limits
-- grant select on config to adam;
