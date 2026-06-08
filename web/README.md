# The Camel — web window (Next.js + Supabase, Vercel)

A **private** operator window for The Camel: a read-only mirror of the paper system + a phase-2 control bar
that *queues* commands the Python brain executes. Friends-only (email allowlist), English, **paper only —
no real money can move from here.**

## The shape (brain ↔ bridge ↔ window)

```
  Python brain (your PC)                Supabase (the bridge)            Vercel (this app)
  -------------------------             ----------------------           ------------------
  ops/publish_state.py  ── upsert ───►  system_state (jsonb)  ── read ──► dashboard (read-only)
  ops/command_poller.py ◄── poll ─────  commands (queue)      ◄─ insert ─ control bar (you + friends)
        (service-role key, here only)                              (anon key, RLS-enforced)
```

The brain keeps running where it belongs (it owns the SQLite DBs, the guardrails, the loop). This app never
runs the engine — it only shows what the brain published and queues requests the brain chooses to act on.

---

## 1. Supabase (5 min)
1. Create a project at https://supabase.com.
2. **SQL Editor → run** [`supabase/schema.sql`](supabase/schema.sql) (creates `allowed_emails`, `system_state`,
   `equity_points`, `commands` + the `is_allowlisted()` function and **friends-only RLS**).
3. **Seed the allowlist** (this is the real gate — RLS denies everyone not in it):
   ```sql
   insert into public.allowed_emails (email) values ('you@example.com'), ('friend@example.com');
   ```
4. **Project Settings → API**: copy the **Project URL**, the **anon public** key, and the **service_role** key.
5. **Authentication → Providers → Email**: enable it, and **turn OFF "Allow new users to sign up"** so strangers
   can't self-provision an account — invite friends under **Authentication → Users**. (Load-bearing: with
   signups on, anyone could create an account; RLS still blocks them unless they're in `allowed_emails`, but
   disabling signups is the clean belt-and-suspenders.)
6. **Authentication → URL Configuration**: add your site URL + `…/auth/callback` to the redirect allow-list
   (add both `http://localhost:3000` for local dev and your Vercel URL once you have it).

## 2. Deploy the web app to Vercel (5 min)
1. Push this repo to GitHub (already done) and **New Project** on Vercel from it.
2. **Root Directory → `web`** (this app lives in a subfolder of the Python repo).
3. **Environment Variables** (Settings → Environment Variables) — set **before** the first deploy:
   - `NEXT_PUBLIC_SUPABASE_URL` = your Project URL
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` = the anon public key
   - `NEXT_PUBLIC_ALLOWED_EMAILS` = `you@example.com,friend@example.com` (leave blank to allow any signed-in user)
   - ⚠️ **Do NOT** put the service-role key in Vercel — it bypasses RLS and must live only on the brain.
4. Deploy. Open the URL → sign in with a magic link → you're in.

Local dev: `cd web && cp .env.example .env.local && npm install && npm run dev` (use a short path on Windows
to avoid MAX_PATH — e.g. clone to `C:\camel`).

## 3. The brain side (publish state + run commands)
**Prereq:** run these from the **repo root** with the Python project installed (`pip install -r requirements.txt`).
They are part of the Python repo, not the `web/` app. On the machine that runs The Camel, set these env vars
(the service-role key lives **only** here):
```
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
CAMEL_DB_DIR=.                       # where the 7 camel_*.db files live
CAMEL_FOUNDER_EMAIL=you@example.com  # only this email can approve/veto via the web
CAMEL_SYMBOLS=SPUS,HLAL              # default symbols for a web-triggered tick
```
Then:
```
python -m ops.publish_state          # push the current snapshot to the web (run from the daily loop or a timer)
python -m ops.command_poller         # execute any queued web commands (run on a short timer)
```
Schedule both with Windows Task Scheduler (e.g. publish every few minutes, poll every minute) so the window
stays fresh and the control bar feels live.

**Or one command** — [`scripts/run-brain.ps1`](../scripts/run-brain.ps1) does a full cycle (ingest → paper
tick → publish → poll):
```
./scripts/run-brain.ps1 -Loop -Interval 300     # repeat every 5 min; Ctrl+C to stop
```
It reads a local `.env` for the env vars above, so you don't have to export them each time. (If `SUPABASE_*`
aren't set it just runs the local paper tick and skips publish/poll.)

### Live refresh + equity curve
- `schema.sql` also creates **`equity_points`** — the publisher appends one row per run, and the dashboard
  renders the **paper equity curve** (pure SVG, no chart library).
- For instant updates, enable **Realtime** on `system_state`: Supabase → **Database → Replication** (or
  Table editor → the table → enable Realtime). The app subscribes and refreshes on change; if you skip this,
  it still auto-refreshes every 30s as a fallback.

## What's safe by construction
- The web uses **only the anon key** → RLS lets it **read** state and **insert** a command, nothing else.
- **Friends-only is enforced in the DATABASE** (RLS gates every table on the `allowed_emails` table via
  `is_allowlisted()`), not just in the app — so nobody outside the allowlist can read state or enqueue a
  command even if they hit PostgREST directly with the anon key.
- It can never write the system state or execute a command — only the brain (service-role) does.
- `run_tick` runs the full **Constitution + Edge Proof + Budget + approval** path (paper); `approve`/`veto`
  is **founder-only** (`CAMEL_FOUNDER_EMAIL`). **No path moves real money** — that still needs the founder's
  deliberate `config/limits.yaml` phase-flip on the brain.
- The app is `noindex` (kept out of search engines) and gated behind sign-in + the email allowlist.

## Roadmap for this app
- **v1 (done):** read-only dashboard (status, KPIs, regime, positions, Edge verdicts, rejections, ledger,
  Sharia whitelist) · the queued control bar · the **paper equity curve** · **live refresh** (Realtime + 30s
  fallback) · the one-command `run-brain.ps1`.
- **Next:** a per-friend read-only vs founder-control role split · per-strategy/portfolio drill-down ·
  a downloadable track-record export.
