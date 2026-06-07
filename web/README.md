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
2. **SQL Editor → run** [`supabase/schema.sql`](supabase/schema.sql) (creates `system_state` + `commands` with RLS).
3. **Project Settings → API**: copy the **Project URL**, the **anon public** key, and the **service_role** key.
4. **Authentication → Providers → Email**: enable it. (Optional: turn **off** "Allow new users to sign up" so
   only people you invite can log in — invite friends under **Authentication → Users**.)
5. **Authentication → URL Configuration**: add your site URL + `…/auth/callback` to the redirect allow-list
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
On the machine that runs The Camel, set these env vars (the service-role key lives **only** here):
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

## What's safe by construction
- The web uses **only the anon key** → RLS lets it **read** state and **insert** a command, nothing else.
- It can never write the system state or execute a command — only the brain (service-role) does.
- `run_tick` runs the full **Constitution + Edge Proof + Budget + approval** path (paper); `approve`/`veto`
  is **founder-only** (`CAMEL_FOUNDER_EMAIL`). **No path moves real money** — that still needs the founder's
  deliberate `config/limits.yaml` phase-flip on the brain.
- The app is `noindex` (kept out of search engines) and gated behind sign-in + the email allowlist.

## Roadmap for this app
- **v1 (now):** read-only dashboard (status, KPIs, regime, positions, Edge verdicts, rejections, ledger,
  Sharia whitelist) + the queued control bar.
- **Next:** an equity-curve chart for the paper track record · live-refresh (Supabase Realtime) · a per-friend
  read-only vs founder-control role split.
