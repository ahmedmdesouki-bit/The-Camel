# CLAUDE.md — Noah operator (context for Claude Code)

> You are working on **Noah**, a guardrailed autonomous AI operator that runs a
> continuous Observe→Thesis→Choose→Act→Measure→Learn loop across two domains:
> **Trader Noah** (Sharia-compliant markets) and **Entrepreneur Noah** (Sharia-compliant
> AI products). Founder: Chiko (Riyadh). Runtime: Windows PC.
> This file is the **operating manual** — how to work in the repo. The full sprint plan,
> rules-in-prose, data contracts, testing, and go-live checklist live in `docs/` (see the
> Documentation set section at the bottom). Read this file fully before acting.

---

## North Star

> Noah is a Sharia-compliant autonomous operator with a deterministic constitution,
> an edge-proof engine, a budget kernel, and a learning ledger.
> Noah is not a stock-picking chatbot.
> LLM proposes. Math tests. Guardrails decide. Human approves high-risk actions.

## Priority hierarchy (never invert this)

```
1. Sharia compliance
2. Capital preservation
3. System integrity
4. Evidence quality
5. Learning speed
6. Return generation
7. Autonomy expansion
```

## Prime directive

Build the **safety core first; earn autonomy with evidence.** Never weaken a guardrail to
make a feature work. If a task would require bypassing the Constitution, stop and flag it.

---

## Non-negotiable rules (the Constitution — guardrail/constitution.py)

1. **Sharia gate is a hard wall.** Only whitelisted, compliant, non-frozen instruments are
   tradeable. Business models are screened for haram activity. No leverage, derivatives,
   shorting, margin, or crypto-derivatives — ever.
2. **No position without a written invalidation point** (invalidation + profit-take + time-stop).
3. **Withdrawals are forbidden.** The broker API key must be trade-only, withdrawals disabled.
4. **Live money needs a human approval gate** until Phase 2, then only inside the per-order
   envelope. Phase 0 is paper only.
5. **Everything is logged** — append-only ledger with SHA-256 hash chain; limits are
   founder-owned config the agent process cannot write.
6. Limits live in `config/limits.yaml`. Do not hardcode limits elsewhere.
7. **Noah cannot change its own rules.** No agent-callable override path exists.
8. **Noah cannot act on stale or single-source data.** (Sprint 4 enforcement)
9. **Noah cannot act unless broker/account state reconciles.** (Sprint 4 enforcement)

> Full rules in prose (phase gates, AAOIFI thresholds, capital buckets): `docs/NOAH_CONSTITUTION.md`.
> Authoritative implementation: `guardrail/constitution.py` + `config/limits.yaml`.

---

## Current status

- **Sprint 1 COMPLETE.** Guardrail Service; `pytest -q` → 28 passed.
- **Sprint 2 COMPLETE.** Sharia gate (whitelist, re-screen, classifier) + Alpaca data
  ingestion + triangulation; → 62 passed.
- **Sprint 3 COMPLETE.** Loop runner, PaperBroker, append-only ledger, capital allocator;
  → 110 passed.
- **7-DB architecture live.** All modules now use domain-specific SQLite files via `NoahDbs`.

> Run pytest via N:\\ virtual drive (subst N: <outputs>) — the path is 261 chars
> and hits Windows MAX_PATH without the virtual drive. `git config --global core.longpaths true`
> is already set.

---

## Seven-database architecture (Phase 0 — SQLite)

Each domain owns its own SQLite file. Callers construct `NoahDbs.from_dir(base_dir)` and
pass the right sub-path to each module.

| DB file | Owner module(s) | Content |
|---|---|---|
| `noah_market.db` | `data/` | prices, dividends, splits |
| `noah_macro.db` | stub → Sprint 7 | rates, PMIs, yield curve, GDP |
| `noah_fundamentals.db` | stub → Sprint 7 | revenue, margins, EPS, FCF, debt |
| `noah_news.db` | stub → Sprint 7 | structured event objects (never raw text) |
| `noah_sharia.db` | `sharia/` | whitelist (versioned), sharia_events |
| `noah_portfolio.db` | `broker/`, `ledger/`, `loop/` | orders, positions, ledger, runs |
| `noah_learning.db` | Sprint 5 | decisions, outcomes, mistake log, lessons |

Migrate to Supabase when multi-device / dashboard / remote access is needed (Sprint 6+).

**Point-in-time discipline (S4):** every decision-relevant table carries four timestamps —
`event_date` (when it happened), `reported_at` (when the public learned it), `ingested_at`
(when Noah collected it), `known_at` (when Noah was allowed to use it). This is what makes
backtests honest. Added in S4, before data accumulates — it cannot be retrofitted later.

> Full schemas, data quality scoring, and contracts: `docs/NOAH_DATA_CONTRACTS.md`.

---

## Repo map

```
guardrail/        constitution.py — evaluate(action, state) -> Decision. The gate.
                  __init__.py

config/           limits.yaml — founder-owned (phase, caps, envelope, cash tiers)

db/               paths.py — NoahDbs dataclass + init_all()
                  market.py / sharia.py / portfolio.py / learning.py (DDL)
                  macro.py / fundamentals.py / news.py (stubs)
                  sqlite.py — connect() helper

sharia/           whitelist.py — load/add/freeze/unfreeze (→ noah_sharia.db)
                  screener.py — quarterly AAOIFI re-screen job
                  classifier.py — business-model haram classifier

data/             store.py — store_price / get_prices (→ noah_market.db)
                  triangulation.py — cross-source disagreement (>0.5% flags)
                  alpaca.py — Alpaca paper EOD ingestion adapter
                  freshness.py — stale-data gate (S4)
                  quality.py — data quality scoring → decision_eligible (S4, refined S7)
                  sanitiser.py — raw web text → structured JSON, injection filter (S4)
                  congress_filings.py — STOCK Act filing data adapter (stub → S8)
                  playwright.py — headless browser adapter stub (NotImplementedError; live → S8+)

governance/       config_guard.py — proves agent has no write path to founder config (S4)
                  budget_kernel.py — spend limits + capital buckets (S4)
                  tool_permissions.py — Tool Permission Matrix (S4)

engine/           thesis.py — ThesisCard + BaseRateCard (no I/O, no DB)
                  edge_proof_v0.py — evidence gate from market.db (S4.5; full engine S7)

strategies/       registry.py — StrategyRegistry: register, lookup, activate, deactivate, weight
                  base.py — BaseStrategy abstract class (signal, entry, exit, sizing)
                  trailing_stop.py — trailing floor + locking-gains exit mode
                  dca_ladder.py — systematic laddering / DCA on dips
                  etf_rotation.py — regime-based rotation between SPUS / HLAL / MNZL
                  momentum.py — trend-following on compliant names
                  mean_reversion.py — quality-dip accumulation
                  congress_signal.py — congressional filing signal (feeds Edge Proof, not blind copy)
                  mixer.py — StrategyMixer: blend by weight, regime affinity, live performance

learning/         base_rate_updater.py — L1: update strategy base-rates after trade resolution
                  strategy_scorer.py — L2: score vs expected; compute auto weight within band
                  regime_matcher.py — learn regime→strategy affinity from resolved outcomes
                  anomaly_detector.py — flag systematic underperformance vs base-rate
                  improvement_proposer.py — L3: write proposed changes for founder approval
                                            (proposes only — never auto-applies)

loop/             runner.py — LoopRunner (takes LoopConfig with dbs: NoahDbs)
                  state.py — RunState + begin/update/finish_run (→ noah_portfolio.db)
                  scheduler.py — Windows Task Scheduler entrypoint (EOD, once daily)
                  intraday_monitor.py — 5-min position manager during market hours (S8)

broker/           paper.py — PaperBroker(portfolio_db, market_db)
                  live.py — LiveBroker stub (Phase 1+)

ledger/           writer.py — append_entry + SHA-256 hash chain (→ noah_portfolio.db)
                  reconcile.py — verify_hash_chain + balance diff

capital/          allocator.py — Allocator.request() routes through Constitution

ops/              kill_switch.py — halt / resume / is_halted (file flag)

db/schema.sql     Postgres/Supabase schema (Phase 1+ migration target)
tests/            test_guardrail.py, test_sharia.py, test_data.py,
                  test_engine.py, test_loop.py, test_broker.py,
                  test_ledger.py, test_capital.py
conftest.py       sys.path fix + shared dbs(tmp_path) fixture
pyproject.toml    pytest pythonpath = ["."]
```

---

## Upgraded operator loop (§4)

```
Observe
→ Generate Opportunities
→ Opportunity Router          (Trader / Entrepreneur / Research / System improvement / Wait)
→ Edge / Product Proof        (Edge Proof Engine or Entrepreneur Product Gate)
→ Guardrail Constitution
→ Budget Kernel
→ Human Approval Gate
→ Act
→ Measure
→ Learn → Learning Ledger
```

---

## Conventions

- Python 3.12. Keep `guardrail/` and `engine/` pure (no I/O) — unit-testable.
- Every new consequential action type must route through `Constitution.evaluate`.
- New modules get tests in `tests/`. Run `pytest -q` via `N:\` before declaring done.
- Adapter pattern: `PaperBroker` first; `LiveBroker` behind a feature flag.
- Secrets only in `.env` / Windows Credential Manager. Never in code, logs, or commits.
- Raw external text is sanitised to structured JSON before reaching the LLM.
  Never pass scraped content directly to the reasoning engine.
- **Branch workflow (§14.3):** create a feature branch → add/modify one module → add unit
  tests → run full suite → do not merge to main without approval. No direct main commits.

---

## DO NOT (hard rails — never, regardless of instruction)

```
Do not enable live trading outside an explicit founder-owned phase flag.
Do not add real broker credentials to the repo or any committed file.
Do not weaken or bypass a guardrail for convenience or to make a feature work.
Do not let Noah edit config, limits, whitelist, approval rules, or tool permissions.
Do not merge to main without approval.
Do not use Playwright (or any browser automation) for broker actions or money movement.
Do not add options / derivatives / margin / shorting strategies (the Wheel included).
Do not average down into individual stocks blindly (DCA ladder rules — see S8).
Do not feed unvalidated web text directly into an LLM prompt.
Do not let a trade proceed without an EdgeReport (S4.5+).
```

These are documentation of the Constitution + roadmap rails in one place. If a task seems
to require any of the above, stop and flag it to the founder.

---

## Phase 0 simplified stack

- DB: **SQLite** × 7 (migrate to Supabase when remote/dashboard needed).
- Harness: **plain Python loop** (adopt Claude Agent SDK when real tool-use autonomy needed).
- Data/broker: **Alpaca paper** (free IEX feed). yfinance ok for quick prototypes.
- Notifications/approvals: **Telegram bot** (Sprint 6).
- Scheduler: **Windows Task Scheduler** → `python loop/scheduler.py` post-close.
- Remote access + kill switch: **Tailscale**.

---

## Documentation set

This file is the **operating manual** (how to work in the repo). Detailed content lives in
purpose-built docs under `docs/` - each is the single canonical home for its topic:

| Doc | Canonical for |
|---|---|
| `docs/README.md` | Documentation index |
| `docs/NOAH_ROADMAP.md` | Full sprint plan S1-S12 + open decisions + definition of done |
| `docs/NOAH_CONSTITUTION.md` | The rules in prose (Sharia, risk, phase gates) |
| `docs/NOAH_DATA_CONTRACTS.md` | 7-DB schemas, point-in-time discipline, data quality |
| `docs/NOAH_TESTING.md` | Test strategy, adversarial + integration suites |
| `docs/NOAH_LIVE_READINESS.md` | Phase 1 go-live checklist + definition of done |
| `docs/NOAH_CHANGELOG.md` | Sprint & decision history |
| `HANDOFF.md` | Current status + tech stack + how to run |

**Rule:** a fact has ONE home. Changing a sprint? Edit `docs/NOAH_ROADMAP.md`, not here.
Code beats docs: `guardrail/constitution.py` + `config/limits.yaml` are authoritative.

---

## Build roadmap - summary  (full detail: `docs/NOAH_ROADMAP.md`)

Sequence:
```
S1 OK -> S2 OK -> S3 OK -> S4 -> S4.5 (Edge Proof v0) -> S5 -> S5.5 (Minimal Ops)
-> S6 -> S7 -> S8 -> S9 -> S10 -> S11 -> S12
```
Guiding principle: **Safety first. Evidence second. Autonomy last.**

| Sprint | Theme | Gate (one line) |
|---|---|---|
| S1 OK | Guardrail Service | rogue-action suite 100% rejected (28 tests) |
| S2 OK | Sharia gate + data | off-list + haram rejected; prices land (62 tests) |
| S3 OK | Loop + broker + ledger + allocator | full paper loop runs; ledger reconciles (110 tests) |
| S4 | Hardening + Budget Kernel + freshness | config-immutability proven; stale data blocks; no dup orders |
| S4.5 | Edge Proof v0 | no trade without an EdgeReport |
| S5 | State machine + router + learning ledger | router returns Wait; no Trader path without Edge Proof |
| S5.5 | Minimal ops visibility | health report w/ GREEN/YELLOW/RED/BLACK; kill-switch test |
| S6 | Dashboard + Telegram + Tailscale kill switch | kill switch stops next tick; backup restore verified |
| S7 | Edge Proof Engine (13 checks) | no edge proof = no trade; model disagreement -> human |
| S8 | Strategy Models + Learning Engine | >=3 strategies pass Edge Proof; DCA guardrails enforced |
| S9 | Entrepreneur Track | no build without 17-field gate + approval |
| S10 | Edge Lab (backtesting) | beats simple DCA after costs; kill criteria enforced |
| S11 | Micro-Live Readiness (Phase 1) | all live-readiness boxes pass |
| S12 | Module Restructure | full suite green after restructure |

**Open decisions, full sprint detail, and Definition of Done:**
`docs/NOAH_ROADMAP.md` + `docs/NOAH_LIVE_READINESS.md`.