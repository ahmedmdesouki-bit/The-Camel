# The Camel — Project Handoff

**Prepared:** 2026-06-05 · **Updated:** 2026-06-06
**Status:** Sprints **S1 → S5.5 complete** · **263 tests green** · 7-database architecture live
**Founder:** Chiko (Riyadh) · **Runtime:** Windows 11 PC
**Repo state:** 30 commits on `master`, clean working tree · **Next: S6** (Dashboard + Telegram + Tailscale)

> For the live sprint-by-sprint detail and module list see `docs/CAMEL_ROADMAP.md` and the
> `## Current status` section of `CLAUDE.md` — both are kept current. This file's
> sprint table below shows the S1–S3 core; S4–S5.5 detail lives in the roadmap.

> Companion docs: [`CLAUDE.md`](CLAUDE.md) is the source of truth for how to work
> in this repo and the full sprint roadmap. This file is the orientation handoff —
> read it first, then `CLAUDE.md`, then the code.

---

## 1. What Camel Is

Camel is a **guardrailed autonomous AI operator** that runs a continuous
Observe→Thesis→Choose→Act→Measure→Learn loop across two arms:

- **Trader Camel** — Sharia-compliant market trading (paper first, live only when earned).
- **Entrepreneur Camel** — Sharia-compliant AI products (build/deploy/sell).

The defining idea: **every consequential action passes through a deterministic constraint
engine (the Constitution) that the LLM cannot edit.** The agent proposes; the Constitution
disposes. Autonomy is aggressive *inside* the rails and mechanically impossible *outside*
them.

### North Star
> Camel is a Sharia-compliant autonomous operator with a deterministic constitution,
> an edge-proof engine, a budget kernel, and a learning ledger.
> **LLM proposes. Math tests. Guardrails decide. Human approves high-risk actions.**

### Priority hierarchy (never inverted)
```
1. Sharia compliance   2. Capital preservation   3. System integrity
4. Evidence quality    5. Learning speed          6. Return generation
7. Autonomy expansion
```

### Phase gates (autonomy is earned, not granted)
| Phase | Capital | Autonomy | Exit criteria |
|---|---|---|---|
| **0 Paper** | $0 | Full loop, simulated orders | ≥28 days · 0 guardrail breaches · ledger reconciles · ≥1 product deployed |
| **1 Micro-live** | $100–500 | Human approves every trade | ≥28 days · 0 unapproved executions · approval round-trip < 5 min |
| **2 Guardrailed auto** | scale to fund | Auto ≤ per-order envelope on whitelist | ≥60 days · 0 limit breaches · loss-stop fired in test |
| **3 Scale** | full $10K | Wider envelope | track record justifies each increase |

We are in **Phase 0**.

---

## 2. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Language | **Python 3.12** | `guardrail/` and `engine/` kept pure (no I/O) for unit-testing |
| Database | **SQLite × 7** | One file per data domain. Migrate to Supabase when remote/dashboard/multi-device is needed |
| Broker / data | **Alpaca paper** (free IEX feed) | `alpaca-py`. yfinance ok for quick prototypes |
| Test framework | **pytest** | 110 tests, run via the `N:\` virtual drive (see §6) |
| Config | **YAML** (`config/limits.yaml`) | Founder-owned; agent process has no write path |
| Scheduler | **Windows Task Scheduler** | `python loop/scheduler.py` post-close (EOD); intraday monitor every 5 min (S8) |
| Secrets | **`.env`** now → **Windows Credential Manager** (S6) | Never in code, logs, or commits |
| Remote access / kill switch | **Tailscale** (S6) | ACLs locked to founder devices |
| Notifications / approvals | **Telegram bot** (S6) | One-tap approve/veto |
| Migration target | **Supabase / Postgres** | `db/schema.sql` is the Phase-1+ schema with RLS sketch |

### Dependencies (`requirements.txt`)
```
pyyaml>=6.0
pytest>=8.0
alpaca-py>=0.20      # Sprint 2
python-dotenv>=1.0   # Sprint 2
# supabase / requests — Sprint 3+ (stubbed)
```

---

## 3. Repository Structure

```
guardrail/        constitution.py  — evaluate(action, state) -> Decision. THE GATE.
                  __init__.py

config/           limits.yaml      — founder-owned limits (phase, caps, envelope, cash tiers)

db/               paths.py         — CamelDbs dataclass + init_all()  ← entry point for all DBs
                  market.py        — camel_market.db DDL (prices, dividends, splits)
                  sharia.py        — camel_sharia.db DDL (whitelist, sharia_events)
                  portfolio.py     — camel_portfolio.db DDL (orders, positions, ledger, runs)
                  learning.py      — camel_learning.db DDL (decisions, outcomes, lessons)
                  macro.py         — camel_macro.db DDL (stub → S7)
                  fundamentals.py  — camel_fundamentals.db DDL (stub → S7)
                  news.py          — camel_news.db DDL (stub → S7)
                  sqlite.py        — connect() helper
                  schema.sql       — Postgres/Supabase migration target

sharia/           whitelist.py     — load/add/freeze/unfreeze  (→ camel_sharia.db)
                  screener.py      — quarterly AAOIFI re-screen job
                  classifier.py    — business-model haram classifier (7 categories)

data/             store.py         — store_price / get_prices  (→ camel_market.db)
                  triangulation.py — cross-source disagreement (>0.5% close flags)
                  alpaca.py        — Alpaca paper EOD ingestion adapter

engine/           thesis.py        — ThesisCard + BaseRateCard (pure, no I/O)

loop/             runner.py        — LoopRunner (Observe→…→Learn, Constitution gate at Act)
                  state.py         — RunState persistence (→ camel_portfolio.db)
                  scheduler.py     — Windows Task Scheduler entrypoint (EOD)

broker/           paper.py         — PaperBroker(portfolio_db, market_db)
                  live.py          — LiveBroker stub (NotImplementedError, Phase 1+)

ledger/           writer.py        — append_entry + SHA-256 hash chain
                  reconcile.py     — verify_hash_chain + balance diff

capital/          allocator.py     — Allocator.request() routes through Constitution

ops/              kill_switch.py   — halt / resume / is_halted (file flag)

tests/            test_guardrail.py (28)  test_sharia.py (23)   test_data.py (11)
                  test_engine.py (12)     test_loop.py (11)     test_broker.py (7)
                  test_ledger.py (11)     test_capital.py (7)   = 110 total

conftest.py       sys.path fix + shared `dbs` fixture (fresh CamelDbs per test)
pyproject.toml    pytest pythonpath = ["."]
```

---

## 4. The Seven Databases

Each domain owns its own SQLite file. Callers build `CamelDbs.from_dir(base_dir)` and pass
the relevant path to each module. `init_all(dbs)` creates all seven.

| File | Owner | Content | Status |
|---|---|---|---|
| `camel_market.db` | `data/` | prices, dividends, splits | **Live** |
| `camel_sharia.db` | `sharia/` | whitelist (+`historical_drift_count`, +`purification_ratio`), sharia_events (+`trigger_period`, +`reasoning_summary`) | **Live** |
| `camel_portfolio.db` | `broker/`, `ledger/`, `loop/` | orders (+`client_order_id`), positions, ledger, runs, guardrail_events, approvals | **Live** |
| `camel_learning.db` | S8 learning engine | decisions, outcomes, mistake log, lessons | Schema live, unused |
| `camel_macro.db` | S7 | rates, PMIs, yield curve, GDP | Stub |
| `camel_fundamentals.db` | S7 | revenue, margins, EPS, FCF, debt | Stub |
| `camel_news.db` | S7 | structured event objects (never raw text) | Stub |

---

## 5. What Is Built (Sprints 1–3)

### Sprint 1 — Guardrail Service `[28 tests]`
`guardrail/constitution.py` — the deterministic gate. `Constitution.evaluate(action, state)
-> Decision`. Enforces, with **no agent-callable override**:
- Sharia whitelist gate (off-list / frozen / non-compliant → rejected)
- No leverage, derivatives, shorting, margin (hard block)
- No position without invalidation + profit-take + time-stop
- Withdrawals permanently forbidden
- Position cap 20% · sector cap 40% · tiered cash buffer
- Daily loss stop −5% · weekly drawdown stop −10%
- Phase-gated live-approval requirement
- Limits loaded from `config/limits.yaml` (founder-owned)

Includes the full **rogue-action suite** — every prohibited action is provably rejected.

### Sprint 2 — Sharia Gate + Data `[+34 → 62 tests]`
- `sharia/whitelist.py` — versioned whitelist persistence
- `sharia/screener.py` — quarterly AAOIFI re-screen (debt <33%, interest assets <33%,
  haram income <5%); breaches freeze the instrument and log it
- `sharia/classifier.py` — business-model haram classifier (7 categories)
- `data/store.py` — OHLCV upsert
- `data/triangulation.py` — multi-source disagreement flag (>0.5% on close)
- `data/alpaca.py` — Alpaca paper EOD adapter (lazy import; tests run without keys)

### Sprint 3 — Loop + Broker + Ledger + Allocator `[+48 → 110 tests]`
- `loop/runner.py` — full Observe→Thesis→Choose→Act→Measure→Learn; Constitution gate at
  Act; kill switch checked before start; every step persisted for crash recovery
- `loop/state.py` — `RunState` → `runs` table
- `loop/scheduler.py` — Task Scheduler entrypoint
- `broker/paper.py` — `PaperBroker` fills at last close (fallback $1), writes orders + ledger
- `broker/live.py` — `LiveBroker` stub behind phase flag
- `ledger/writer.py` — append-only entries with SHA-256 hash chain
- `ledger/reconcile.py` — chain verification + balance diff vs broker statement
- `capital/allocator.py` — routes through Constitution; rejects (never clamps) with `notional=0`

### Post-S3 — Architecture + Roadmap
- **7-database split** — domain isolation (replaced the original single SQLite file)
- **Schema extensions** — `client_order_id`, `historical_drift_count`, `purification_ratio`,
  `trigger_period`, `reasoning_summary`
- **Consolidated roadmap** — all items from 3 external feedback sources mapped into S4–S12

---

## 6. How To Run

> **Critical Windows gotcha:** the repo's absolute path is **261 characters** — one over the
> Windows MAX_PATH limit. Python's file finder returns "not found" for files this deep.
> Work around it with a virtual drive (no admin needed):

```powershell
# One-time per session — map N: to the repo
subst N: "C:\Users\...\outputs"

# Run the tests
cd N:\
python -m pytest -q
```

`git config --global core.longpaths true` is already set (needed for `git init` to succeed).
**For future sprints, clone to a short path like `C:\camel` to avoid this entirely.**

### Running the loop manually
```powershell
cd N:\
python loop\scheduler.py        # env: CAMEL_DB_DIR (default repo root), CAMEL_PHASE (default 0)
```

### Kill switch
```powershell
python ops\kill_switch.py halt      # creates config/HALT flag — loop skips next tick
python ops\kill_switch.py resume    # removes flag
```

---

## 7. What Is Planned (Sprints 4–12)

> Full detail with module names and gate criteria is in [`CLAUDE.md`](CLAUDE.md).

| Sprint | Theme | Key deliverables |
|---|---|---|
| **S4** | Hardening | Rolling velocity stop (5d −8% / 14d −12%); illiquidity/slippage gate; Budget Kernel (capital buckets); Tool Permission Matrix; Data Freshness Checker; sanitiser; Playwright stub; `pre_flight_execution_check` (idempotency); ThesisCard full template |
| **S5** | Operator OS | 11-state machine; Opportunity Router (Trader/Entrepreneur/Research/System-improvement/Wait); task queue; Learning Ledger; append-only op log; health monitor |
| **S6** | Visibility + Control | Dashboard; daily Telegram health report; kill switch over Tailscale; weekly kill-switch test; secrets manager; log rotation; off-box backup; machine hardening checklist |
| **S7** | Edge Proof Engine | 13-check proof (regime → analogues → event study → forward returns → base rate → counter-signals → valuation → momentum → liquidity → sharia → portfolio fit → corporate action → report); model-disagreement rule. **No edge proof = no trade.** Macro/fundamentals/news DBs activated |
| **S8** | Strategy Models + Learning | Strategy Registry (trailing_stop, dca_ladder, congress_signal, etf_rotation, momentum, mean_reversion); StrategyMixer; intraday monitor (5-min); 4-tier learning engine; regime→strategy affinity learning |
| **S9** | Entrepreneur Track | Product Gate (11 fields); build pipeline; Entrepreneur Constitution; ship one compliant product |
| **S10** | Edge Lab (Backtesting) | Bias prevention; walk-forward; crisis tests (2000/2008/2020/2022); benchmarks (SPUS/HLAL/Cash/DCA); per-strategy + mixer backtest |
| **S11** | Micro-Live Readiness | Approval Channel; LiveBroker; limit-orders-only; Phase 1 entry ($100–500, human-approved) |
| **S12** | Module Restructure | Flat → `governance/ operator/ trader/ entrepreneur/ data/ security/ alerts/` (tests stay green) |

### Permanently excluded
**Options / the Wheel Strategy.** Derivatives are haram and blocked by Constitution rule #1.
Appeared in two source videos; rejected both times. Do not revisit.

---

## 8. Key Decisions & Conventions

- **Branch workflow (going forward):** feature branch → one module at a time → add tests →
  run full suite → no merge to main without approval. (S1–S3 + roadmap edits were committed
  directly to master during setup; switch to branches from S4.)
- **Every new consequential action type must route through `Constitution.evaluate`.**
- **New modules get tests.** Run the suite via `N:\` before declaring done.
- **Secrets** only in `.env` / Credential Manager — never in code, logs, commits, or the
  Claude workspace.
- **Raw external text is sanitised to structured JSON before reaching the LLM.** Never pass
  scraped content directly to the reasoning engine (prompt-injection defense).
- **Learning never edits rules.** The 4-tier learning engine (S8) proposes; the founder
  approves Level 3+ changes. Camel cannot change the Constitution, risk limits, or the
  ±weight band.

---

## 9. Open Decisions (founder input needed)

1. Live broker for Phase 1: **Alpaca** vs IBKR (paper = Alpaca regardless).
2. Notification channel: **Telegram** (default) vs Pushover.
3. First Entrepreneur product to ship.
4. Canonical Sharia screener: **Musaffa** vs Zoya.
5. Starting limit values in `config/limits.yaml`.
6. Capital bucket percentages (S4 Budget Kernel defaults).

---

## 10. External Feedback Sources Incorporated

1. **Feedback 1** — Architectural critique (rolling velocity stop, illiquidity gate,
   idempotency, schema extensions). → S4.
2. **Feedback 2** — Unified 19-section spec (Edge Proof Engine, 7-DB architecture, State
   Machine, Opportunity Router, Learning Ledger, Budget Kernel, Tool Permission Matrix,
   philosophy hierarchy). → S4–S12.
3. **Video: "Claude Stock Trading" (Samin Yasar)** — trailing stop, DCA ladder, congress
   copy-trading via Capital Trades, intraday monitor, 50%-profit early close. → S8.
   (Wheel strategy from this source rejected.)

All three were gap-analyzed line-by-line against the roadmap; every actionable item is
mapped to a sprint. Memory files: `feedback_camel_arch_1.md`, `feedback_camel_arch_2.md`.

---

## 11. Definition of Done (v1 — unlocks Phase 1)

- All tests green (target ≥200 by S8)
- Agent cannot modify its own constitution / config
- Tool permissions enforced before every tool action
- Budget limits enforced before every money/spend action
- Data freshness checked before every trade decision
- Broker/account reconciliation clean
- State machine prevents skipped steps
- ThesisCard + invalidation required before any paper trade (fixed or trailing floor)
- Edge Proof Engine approved at least one signal
- Strategy Registry has ≥3 active strategies with live base-rates
- Learning Engine updating base-rates; proposals landing in Learning Ledger (not auto-applied)
- Daily health report + kill switch (over Tailscale) working
- No live trading possible unless explicitly enabled by founder-owned config
- 28 days clean paper operation meeting Phase 0 exit criteria
```

---

*Build the safety core first; earn autonomy with evidence. Not financial, legal, or
Sharia advice.*
