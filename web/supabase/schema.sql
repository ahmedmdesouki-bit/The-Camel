-- The Camel — web bridge schema. Run this once in your Supabase project (SQL Editor).
-- Two tables: the published system state (read by the web) and a command queue (written by the web,
-- executed by the Python brain). RLS makes the web read-only on state and never able to self-execute.

-- ============================================================================
-- system_state : the latest snapshot the Python brain publishes (single row, id = 1, upserted).
-- ============================================================================
create table if not exists public.system_state (
  id          bigint primary key,
  state       jsonb not null,
  updated_at  timestamptz not null default now()
);

alter table public.system_state enable row level security;

-- Authenticated users may READ the state. Nobody may write via the anon/auth key — only the brain,
-- which uses the SERVICE-ROLE key (it bypasses RLS by design and never touches Vercel).
drop policy if exists "state readable by authenticated" on public.system_state;
create policy "state readable by authenticated"
  on public.system_state for select
  to authenticated using (true);

-- ============================================================================
-- equity_points : one row per publish — the paper track record (for the equity-curve chart).
-- ============================================================================
create table if not exists public.equity_points (
  id               bigserial primary key,
  ts               timestamptz not null default now(),
  total_value      double precision,
  cash             double precision,
  positions_value  double precision
);
create index if not exists equity_points_ts_idx on public.equity_points (ts desc);

alter table public.equity_points enable row level security;

drop policy if exists "equity readable by authenticated" on public.equity_points;
create policy "equity readable by authenticated"
  on public.equity_points for select
  to authenticated using (true);

-- ============================================================================
-- commands : the web enqueues; the brain dequeues + executes (paper, behind all the gates).
-- ============================================================================
create table if not exists public.commands (
  id            bigserial primary key,
  type          text not null check (type in ('run_tick','approve','veto')),
  payload       jsonb not null default '{}'::jsonb,
  status        text not null default 'pending' check (status in ('pending','done','error')),
  requested_by  text,
  result        jsonb,
  created_at    timestamptz not null default now(),
  processed_at  timestamptz
);

alter table public.commands enable row level security;

-- Authenticated users may INSERT a command and SEE the queue. They may NOT update/execute it —
-- the brain (service role) is the only thing that flips status + writes results.
drop policy if exists "commands insertable by authenticated" on public.commands;
create policy "commands insertable by authenticated"
  on public.commands for insert
  to authenticated with check (true);

drop policy if exists "commands readable by authenticated" on public.commands;
create policy "commands readable by authenticated"
  on public.commands for select
  to authenticated using (true);
