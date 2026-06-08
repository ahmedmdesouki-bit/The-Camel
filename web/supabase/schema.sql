-- The Camel — web bridge schema. Run this once in your Supabase project (SQL Editor).
-- Tables: an email allowlist, the published system state (read by the web), an equity track record, and a
-- command queue (written by the web, executed by the Python brain). RLS enforces FRIENDS-ONLY at the
-- DATABASE — not just in the app — so nobody outside the allowlist can read state or enqueue a command even
-- if they hit PostgREST directly with the anon key. The web is read-only on state; only the brain (service
-- role, which bypasses RLS) writes state and executes commands.

-- ============================================================================
-- allowed_emails : the friends-only allowlist. THE source of truth — RLS gates everything on it.
--   >>> After running this file, add your + your friends' emails (lowercase):
--       insert into public.allowed_emails (email) values ('you@example.com'), ('friend@example.com');
--   Leave it empty and NO ONE can read or write (fail-closed). Also, in Supabase Auth -> Providers -> Email:
--   DISABLE self-signup (strangers can't provision accounts) and ENABLE "Confirm email" (so the JWT `email`
--   claim is always a verified address — the gate trusts that claim).
-- ============================================================================
create table if not exists public.allowed_emails (email text primary key);
alter table public.allowed_emails enable row level security;   -- locked: no policy => only the brain/SQL editor can read/write it

-- SECURITY DEFINER so the predicate can read allowed_emails regardless of the caller's RLS. Checks the
-- caller's verified JWT email against the allowlist.
create or replace function public.is_allowlisted()
returns boolean language sql security definer stable
set search_path = public as $$
  select exists (
    select 1 from public.allowed_emails
    where email = lower(coalesce(auth.jwt() ->> 'email', ''))
  );
$$;

-- ============================================================================
-- system_state : the latest snapshot the Python brain publishes (single row, id = 1, upserted).
-- ============================================================================
create table if not exists public.system_state (
  id          bigint primary key,
  state       jsonb not null,
  updated_at  timestamptz not null default now()
);
alter table public.system_state enable row level security;

-- Allowlisted users may READ the state. Nobody writes via the anon/auth key — only the brain (service role).
drop policy if exists "state readable by authenticated" on public.system_state;
drop policy if exists "state readable by allowlisted" on public.system_state;
create policy "state readable by allowlisted"
  on public.system_state for select
  to authenticated using (public.is_allowlisted());

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
drop policy if exists "equity readable by allowlisted" on public.equity_points;
create policy "equity readable by allowlisted"
  on public.equity_points for select
  to authenticated using (public.is_allowlisted());

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

-- Only ALLOWLISTED users may enqueue a command or see the queue (the DB enforces it — not just the app).
-- They may NOT update/execute it; the brain (service role) is the only thing that flips status + writes results.
drop policy if exists "commands insertable by authenticated" on public.commands;
drop policy if exists "commands insertable by allowlisted" on public.commands;
create policy "commands insertable by allowlisted"
  on public.commands for insert
  to authenticated with check (public.is_allowlisted());

drop policy if exists "commands readable by authenticated" on public.commands;
drop policy if exists "commands readable by allowlisted" on public.commands;
create policy "commands readable by allowlisted"
  on public.commands for select
  to authenticated using (public.is_allowlisted());
