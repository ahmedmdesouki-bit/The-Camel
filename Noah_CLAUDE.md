# CLAUDE.md — Noah operator (context for Claude Code)

> You are working on **Noah**, a guardrailed autonomous AI operator that runs a
> continuous Observe→Thesis→Choose→Act→Measure→Learn loop across two domains:
> **Trader Noah** (Sharia-compliant markets) and **Entrepreneur Noah** (Sharia-compliant
> AI products). Founder: Chiko (Riyadh). Runtime: the founder's **Windows PC**.
> This file is the source of truth for how to work here. Read it fully before acting.

## Prime directive
Build the **safety core first; earn autonomy with evidence.** Never weaken a guardrail to
make a feature work. If a task would require bypassing the Constitution, stop and flag it.

## Non-negotiable rules (the Constitution — see guardrail/constitution.py)
1. **Sharia gate is a hard wall.** Only whitelisted, compliant, non-frozen instruments are
   tradeable. Business models are screened for haram activity. No leverage, derivatives,
   shorting, margin, or crypto-derivatives — ever.
2. **No position without a written invalidation point** (invalidation + profit-take + time-stop).
3. **Withdrawals are forbidden.** The broker API key must be trade-only, withdrawals disabled.
4. **Live money needs a human approval gate** until Phase 2, then only inside the per-order
   envelope. Phase 0 is paper only.
5. **Everything is logged** — append-only ledger; limits are founder-owned config the agent
   process cannot write.
6. Limits live in `config/limits.yaml`. Do not hardcode limits elsewhere; read them from config.

## Current status
- **Sprint 1 COMPLETE.** Guardrail Service implemented; `pytest -q` → **28 passed**, including
  the full rogue-action suite. Do not regress these tests.

## Repo map
- `guardrail/constitution.py` — `Constitution.evaluate(action, state) -> Decision`. The gate.
- `guardrail/__init__.py` — public exports.
- `config/limits.yaml` — founder-owned limits (phase, caps, envelope, cash tiers).
- `db/schema.sql` — Postgres/Supabase schema. **Phase 0 may use local SQLite instead.**
- `tests/test_guardrail.py` — boundary + rogue-action suites. Keep green.
- `ops/kill_switch.py` — halt/resume (never auto-liquidates).
- `.env.example` — copy to `.env` (never commit). Phase 0 needs only Alpaca PAPER keys.

## Conventions
- Python 3.12. Keep `guardrail/` pure (no I/O) so it stays unit-testable.
- Every new consequential action type must route through `Constitution.evaluate`.
- New modules get tests in `tests/`. Run `pytest -q` before declaring a task done.
- Adapter pattern for broker/data: `PaperBroker` (Alpaca paper) first; `LiveBroker` behind a flag.
- Secrets only in `.env` / Windows Credential Manager. Never in code, logs, or commits.

## Phase 0 simplified stack (single Windows machine — don't over-build)
- DB: **SQLite** locally (migrate to Supabase when you need remote/dashboard/multi-device).
- Harness: a **plain Python loop** (adopt Claude Agent SDK only when real tool-use autonomy is needed).
- Data/broker: **Alpaca paper** (free). yfinance ok for quick prototypes.
- Notifications/approvals: **Telegram bot** (Phase 1).
- Scheduler: **Windows Task Scheduler** to run the loop post-close.
- Remote access + kill switch: **Tailscale**.

## Build roadmap (sprints)
- S1 ✅ Guardrail Service + schema + tests.
- S2 → Sharia gate module (whitelist, quarterly re-screen job, business-model classifier)
  + Alpaca paper data ingestion + triangulation. Gate: off-list + haram both rejected; prices land.
- S3 → Thesis/base-rate engine + loop runner + PaperBroker + ledger + reconciliation + allocator.
  Gate: full unattended paper loop runs, ledger reconciles.
- S4 → Dashboard on live DB + monitoring/alerts + kill switch over Tailscale.
- S5 → Entrepreneur pipeline; ship one compliant product (Stripe test).
- Run Phase 0 ≥28 days, 0 guardrail breaches → unlock Phase 1 (Approval channel + LiveBroker).

## Open decisions (ask the founder before assuming)
1. Live broker for Phase 1: Alpaca vs IBKR (paper = Alpaca regardless).
2. Notification channel: Telegram (default) vs Pushover.
3. First Entrepreneur product to ship.
4. Canonical Sharia screener for the whitelist: Musaffa vs Zoya.
5. Starting limit values in `config/limits.yaml`.

## Definition of done (v1)
Guardrail suite green; Noah runs the full loop unattended on paper nightly; dashboard + ledger
reflect it; kill switch + alerts work; one compliant product deployed; 28 days clean paper ops.
