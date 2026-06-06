# CLAUDE.md — Camel operator (context for Claude Code)

> You are working on **The Camel**, a Python-based, guardrailed autonomous operator that runs a
> continuous Observe→Thesis→Choose→Act→Measure→Learn loop across two arms:
> **Trader Camel** (Sharia-compliant markets) and **Entrepreneur Camel** (Sharia-compliant
> AI products). Defining principle — an **inversion of trust**: the LLM only *proposes*; a
> deterministic Constitution it cannot edit, an Edge Proof gate, a Budget Kernel, audit logs, a
> kill switch, and human approval gates *decide*. Founder: Chiko (Riyadh). Runtime: Windows PC.
> This file is the **operating manual** — how to work in the repo. The full sprint plan,
> rules-in-prose, data contracts, testing, and go-live checklist live in `docs/` (see the
> Documentation set section at the bottom). Read this file fully before acting.

---

## North Star

> The Camel is a Sharia-compliant autonomous operator with a deterministic constitution,
> an edge-proof engine, a budget kernel, and a learning ledger.
> The Camel is not a stock-picking chatbot.
> LLM proposes. Math tests. Guardrails decide. Humans approve what's risky. Autonomy is earned, not granted.

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
7. **Camel cannot change its own rules.** No agent-callable override path exists.
8. **Camel cannot act on stale or single-source data.** (Sprint 4 enforcement)
9. **Camel cannot act unless broker/account state reconciles.** (Sprint 4 enforcement)

> Full rules in prose (phase gates, AAOIFI thresholds, capital buckets): `docs/CAMEL_CONSTITUTION.md`.
> Authoritative implementation: `guardrail/constitution.py` + `config/limits.yaml`.

---

## Current status

- **Sprint 1 COMPLETE.** Guardrail Service; `pytest -q` → 28 passed.
- **Sprint 2 COMPLETE.** Sharia gate (whitelist, re-screen, classifier) + Alpaca data
  ingestion + triangulation; → 62 passed.
- **Sprint 3 COMPLETE.** Loop runner, PaperBroker, append-only ledger, capital allocator;
  → 110 passed.
- **Sprint 4 COMPLETE** *(branch `s4-hardening`)*. Constitution hardening (rolling stops,
  illiquidity gate, kill-switch in `evaluate`), Budget Kernel, Tool Permission Matrix, config
  immutability, data freshness/quality/sanitiser, source allowlist, Playwright stub, broker
  idempotency, point-in-time columns, ThesisCard template, secrets + adversarial suites;
  → **197 passed**. Two items deferred by dependency: max cancel/replace (→ S13 LiveBroker),
  earnings blackout (→ S8 earnings data from the fundamentals connectors).
- **Sprint 4.5 COMPLETE.** Edge Proof v0 (`engine/edge_proof_v0.py`): historical hit-rate +
  forward-return vs benchmark from `camel_market.db`; `gate()` wired into the allocator — no
  trade proceeds without a passing `EdgeReport`; missing/weak/stale → `trade_allowed=false`.
  → **217 passed**.
- **Sprint 5 COMPLETE.** Operator OS in `operator_os/` (named to avoid the stdlib `operator`
  module): 11-state machine (can't jump FORMING_THESIS→ACTING; ACTING only from
  AWAITING_APPROVAL; PAUSED needs founder approval; KILLED terminal), Opportunity Router
  (5 paths, leans to Wait, no Trader without Edge Proof), persistent task queue, Learning
  Ledger, append-only op log, and a health monitor with the GREEN/YELLOW/RED/BLACK classifier.
  → **253 passed**.
- **Sprint 5.5 COMPLETE.** Minimal Ops Visibility: `ops/daily_report.py` (status + counts),
  `ops/kill_switch_test.py` (halt stops the tick, resume restores), `ops/secrets_check.py`
  (plaintext-secret startup scan), `ops/backup.py` (verified backup + restore of all 7 DBs).
  → **263 passed**.
- **Sprint 6 COMPLETE (code).** Dashboard + Monitoring: read-only HTML `dashboard/`,
  credential-safe `alerts/` Telegram adapter + daily report delivery, `ops/heartbeat.py`,
  `ops/log_rotation.py`, `ops/secrets_manager.py` (hard plaintext refusal), `ops/archive.py`
  (off-box zip), `ops/reconciliation_report.py`, `ops/scheduled_checks.py` (weekly kill-switch
  test + backup + reconcile). → **289 passed**. *Machine-setup half (Tailscale, BitLocker,
  dedicated user, UPS, MFA, secrets migration) is the founder checklist in
  `docs/CAMEL_MACHINE_HARDENING.md`.*
- **7-DB architecture live.** All modules now use domain-specific SQLite files via `CamelDbs`.

> Run pytest via N:\\ virtual drive (subst N: <outputs>) — the path is 261 chars
> and hits Windows MAX_PATH without the virtual drive. `git config --global core.longpaths true`
> is already set.

---

## Seven-database architecture (Phase 0 — SQLite)

Each domain owns its own SQLite file. Callers construct `CamelDbs.from_dir(base_dir)` and
pass the right sub-path to each module.

| DB file | Owner module(s) | Content |
|---|---|---|
| `camel_market.db` | `data/` | prices, dividends, splits |
| `camel_macro.db` | stub → Sprint 8 | rates, PMIs, yield curve, GDP |
| `camel_fundamentals.db` | stub → Sprint 8 | revenue, margins, EPS, FCF, debt |
| `camel_news.db` | stub → Sprint 8 | structured event objects (never raw text) |
| `camel_sharia.db` | `sharia/` | whitelist (versioned), sharia_events |
| `camel_portfolio.db` | `broker/`, `ledger/`, `loop/` | orders, positions, ledger, runs |
| `camel_learning.db` | Sprint 5 | decisions, outcomes, mistake log, lessons |

Migrate to Supabase when multi-device / dashboard / remote access is needed (Sprint 6+).

**Point-in-time discipline (S4):** every decision-relevant table carries four timestamps —
`event_date` (when it happened), `reported_at` (when the public learned it), `ingested_at`
(when Camel collected it), `known_at` (when Camel was allowed to use it). This is what makes
backtests honest. Added in S4, before data accumulates — it cannot be retrofitted later.

> Full schemas, data quality scoring, and contracts: `docs/CAMEL_DATA_CONTRACTS.md`.

---

## Repo map

```
guardrail/        constitution.py — evaluate(action, state) -> Decision. The gate.
                  __init__.py

config/           limits.yaml — founder-owned (phase, caps, envelope, cash tiers)

db/               paths.py — CamelDbs dataclass + init_all()
                  market.py / sharia.py / portfolio.py / learning.py (DDL)
                  macro.py / fundamentals.py / news.py (stubs)
                  sqlite.py — connect() helper

sharia/           whitelist.py — load/add/freeze/unfreeze (→ camel_sharia.db)
                  screener.py — quarterly AAOIFI re-screen job
                  classifier.py — business-model haram classifier

data/             store.py — store_price / get_prices (→ camel_market.db)
                  triangulation.py — cross-source disagreement (>0.5% flags)
                  alpaca.py — Alpaca paper EOD ingestion adapter
                  freshness.py — stale-data gate (S4)
                  quality.py — data quality scoring → decision_eligible (S4, refined S8)
                  sanitiser.py — raw web text → structured JSON, injection filter (S4)
                  congress_filings.py — STOCK Act filing data adapter (stub → S11, signal-only, never blind copy)
                  playwright.py — headless browser adapter stub (NotImplementedError; live → S8 scraping policy, QA-only)

governance/       config_guard.py — proves agent has no write path to founder config (S4)
                  budget_kernel.py — spend limits + capital buckets (S4)
                  tool_permissions.py — Tool Permission Matrix (S4)

engine/           thesis.py — ThesisCard + BaseRateCard (no I/O, no DB)
                  edge_proof_v0.py — evidence gate from market.db (S4.5; full 17-check engine S10)

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

loop/             runner.py — LoopRunner (takes LoopConfig with dbs: CamelDbs)
                  state.py — RunState + begin/update/finish_run (→ camel_portfolio.db)
                  scheduler.py — Windows Task Scheduler entrypoint (EOD, once daily)
                  intraday_monitor.py — 5-min position manager during market hours (S11)

broker/           paper.py — PaperBroker(portfolio_db, market_db)
                  live.py — LiveBroker stub (Phase 1+)

ledger/           writer.py — append_entry + SHA-256 hash chain (→ camel_portfolio.db)
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
Do not let Camel edit config, limits, whitelist, approval rules, or tool permissions.
Do not merge to main without approval.
Do not use Playwright (or any browser automation) for broker actions or money movement.
Do not add options / derivatives / margin / shorting strategies (the Wheel included).
Do not average down into individual stocks blindly (DCA ladder rules — see S11).
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
| `README.md` | Repo entry point (top-level orientation) |
| `docs/README.md` | Documentation index |
| `docs/CAMEL_BRIEF.md` | Project context: why/who, real capital, open questions |
| `docs/CAMEL_ROADMAP.md` | Full sprint plan S1-S14 (Roadmap v3) + open decisions + definition of done |
| `docs/CAMEL_CONSTITUTION.md` | The rules in prose (Sharia, risk, phase gates) |
| `docs/CAMEL_DATA_CONTRACTS.md` | 7-DB schemas, point-in-time discipline, data quality |
| `docs/CAMEL_TESTING.md` | Test strategy, adversarial + integration suites |
| `docs/CAMEL_LIVE_READINESS.md` | Phase 1 go-live checklist + definition of done |
| `docs/CAMEL_MACHINE_HARDENING.md` | S6 founder machine-setup checklist (Tailscale, BitLocker, secrets, backups) |
| `docs/CAMEL_CHANGELOG.md` | Sprint & decision history |
| `docs/source-materials/` | Archived original PRDs/specs/playbook (provenance only) |
| `HANDOFF.md` | Current status + tech stack + how to run |

**Rule:** a fact has ONE home. Changing a sprint? Edit `docs/CAMEL_ROADMAP.md`, not here.
Code beats docs: `guardrail/constitution.py` + `config/limits.yaml` are authoritative.

---

## Build roadmap - summary  (full detail: `docs/CAMEL_ROADMAP.md` — Roadmap v3)

Sequence (**Roadmap v3** — data backbone before the proof engine; Entrepreneur moved earlier):
```
S1 OK -> S2 OK -> S3 OK -> S4 OK -> S4.5 OK -> S5 OK -> S5.5 OK -> S6 OK ->
S6.5 <- NEXT -> S7 (Entrepreneur) -> S8 (Data Backbone) -> S9 (Knowledge Graph + Regime)
-> S10 (Full Edge Proof) -> S11 (Strategy Registry) -> S12 (Edge Lab + realistic paper)
-> S13 (Micro-Live) -> S14 (Restructure)
```
Guiding principle: **Safety first. Evidence second. Autonomy last.**
Optimize for **evidence density, not feature count.**

| Sprint | Theme | Gate (one line) |
|---|---|---|
| S1 OK | Guardrail Service | rogue-action suite 100% rejected (28 tests) |
| S2 OK | Sharia gate + data | off-list + haram rejected; prices land (62 tests) |
| S3 OK | Loop + broker + ledger + allocator | full paper loop runs; ledger reconciles (110 tests) |
| S4 OK | Hardening + Budget Kernel + freshness | config-immutability proven; stale data blocks; no dup orders (197 tests) |
| S4.5 OK | Edge Proof v0 | no trade without an EdgeReport (217 tests) |
| S5 OK | State machine + router + learning ledger | router returns Wait; no Trader path without Edge Proof (253 tests) |
| S5.5 OK | Minimal ops visibility | daily report w/ status; kill-switch self-test; backup restore verified (263 tests) |
| S6 OK | Dashboard + Telegram + monitoring (code) | dashboard reflects paper trade; weekly checks pass; loss-stop sim halts (289 tests) + machine checklist |
| S6.5 | Safety & Accounting hotfix | phantom sell blocked; frozen-name close-only; no $1 fallback in non-test paths |
| S7 | Entrepreneur Product Engine (moved earlier) | no build without 17-field gate + Sharia check + approval; live payment-capable URL |
| S8 | Data Intelligence Backbone (top-20 connectors) | no record without full provenance + point-in-time; ≥16 free connectors live; raw text never reaches the LLM |
| S9 | Knowledge Graph + Regime Engine | ticker → identity/Sharia/filings/events/exposure; regime classified from real macro; Sharia disagreement freezes buys |
| S10 | Full Edge Proof Engine (17 checks) | no edge proof = no trade; regime-filtered sample + multiple-testing penalty + signal decay; model disagreement -> human |
| S11 | Strategy Registry + Learning Engine | >=3 strategies (trio) pass Edge Proof; DCA guardrails; never auto-edits the Constitution |
| S12 | Edge Lab + realistic paper execution | two-engine cross-check; delisted handled; beats simple DCA after costs; all perf from realistic_paper fills |
| S13 | Micro-Live Readiness (Phase 1) | all live-readiness boxes pass |
| S14 | Module Restructure | full suite green after restructure |

**Open decisions, full sprint detail, and Definition of Done:**
`docs/CAMEL_ROADMAP.md` + `docs/CAMEL_LIVE_READINESS.md`.