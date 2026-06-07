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
- **Sprint 6.5 COMPLETE (Roadmap v3 — first code sprint).** Safety & accounting hotfix:
  phantom-sell guard + close-only/reduce-only exits for frozen/non-compliant holdings (in
  `guardrail/constitution.py`), Edge Proof now mandatory for buys by default while sells are
  exempt (`capital/allocator.py`, `require_edge=None` → resolves to True for buy/increase), and
  the PaperBroker refuses the $1 fallback price outside opted-in unit tests
  (`broker/paper.py`, `NoMarketPriceError`; fallback fills stamped `fill_model="fallback_dollar"`).
  → **309 passed**.
- **Sprint 6.6 COMPLETE.** Position accounting + ops hardening (review rounds #5–6):
  `broker/positions.py` maintains the `positions` table on every fill (weighted-avg cost, realized P&L,
  exact qty-based phantom guard, ledger reconcile); SQLite WAL mode; illiquidity gate **fail-closed in
  live**; health-monitor disk-test mocked + unknown→YELLOW; `ops/deadman.py` external dead-man's-switch;
  `config/beginner_mode.yaml` + `governance/beginner_mode.py` (only-tightens); prompt-injection adversarial
  tests; `docs/CAMEL_BROKER_MATRIX.md`. → **331 passed**.
- **Sprint 7 COMPLETE (Entrepreneur engine).** New `entrepreneur/` package, all deterministic:
  `product_gate.py` (17-field `ProductThesis` + gate; travel/hospitality SLA assistant as the worked
  example), `constitution.py` (separate `EntrepreneurConstitution` — code-gen-only autonomy; privacy/rights/
  budget/approval gates; banned claim wording; haram screen), `build_pipeline.py` (10-stage state machine;
  no skip; PRODUCTION needs founder approval + passing tests). → **352 passed**. *Engine only — real
  Stripe/GitHub/deploy integration lands when a real product ships behind these gates.*
- **Sprint 8 — CORE COMPLETE (slices 1–5; remaining connectors deferred).** Data Intelligence Backbone framework: `data/provenance.py`
  (point-in-time provenance + `source_documents` table + `assert_provenanced`), `data/source_registry.py`
  (`SourceSpec` registry), `data/connectors/base.py` (`SourceConnector` with an injectable transport —
  stdlib fetch in prod, stubbed in tests; **no live web in tests, zero new deps**), `data/connectors/fred.py`
  (→ real `macro_observations`, ALFRED vintage), `data/connectors/sec_edgar.py` (→ real `company_facts`),
  `security/scraping_policy.py` (API > … > browser-QA-only). Slice 2 added `MacroConnector` shared base +
  Treasury / World Bank / BLS connectors (→ macro_observations). Slice 3 added the news pipeline:
  `news_base.py` (`NewsConnector` — sanitise every title; redact + mark-unsafe injection-flagged content;
  structured events only) + `gdelt.py` + news adversarial tests. Slice 4 added BEA + EIA (macro) + ACLED
  (conflict → news). Slice 5 added the ETF issuer-holdings connector (CSV; `etf_holdings.py` → sharia DB
  look-through). **10 connectors live; all 3 stub DBs hold real data.** → **389 passed**. Remaining:
  ~10 more connectors (OFAC/USGS/disclosures/French/SEC-RSS) + market-data + paid vendors.
- **Sprint 9 ✅ COMPLETE — slices 1–4.** (1) Entity resolution: `assets` table + `data/entity_resolver.py`
  (`resolve(ticker)` joins assets + company_facts + etf_holdings look-through + whitelist Sharia status).
  (2) Regime Engine: `trader/regime/` — feature builder over `macro_observations`, deterministic 10-state
  classifier (regime + confidence + signals; `regime_to_themes`), `regime_history` audit table.
  (3) **Event intelligence: `trader/events/`** — `intelligence.py` (deterministic dedupe + reporting quorum,
  dictionary entity-linker over *sanitised* titles, severity/direction/theme rule tables; enriches
  `news_events`; **only `safe=1` rows**) + `reactions.py` (the **`event_reactions`** substrate: forward returns
  1/5/21/63/126d, 63d drawdown, 21d excess-vs-SPUS, `regime_at_event` — a hindsight study table for S10, not a
  live signal).
  (4) **Sharia cross-check: `sharia/aaoifi.py`** (verified AAOIFI screen — ≤30/≤30/≤67/≤5% on **12-mo-avg
  market cap** + 11 sectors; doubtful band; purification ratio) + **`sharia/cross_check.py`** (multi-state
  status pass/fail/doubtful/frozen/pending_review; **disagreement→freeze**; **fail-safe quorum** — a single
  source can fail but not clear a name; authority stack local-board>AAOIFI>founder-tighten-only>agent-never;
  drift; fail-safe writer → `sharia_status` table). **Peg wired:** `features.py` reads FRED `DEXSAUS` →
  `peg_deviation_pct`; classifier raises `GEOPOLITICAL_RISK_OFF` on peg stress. **→ 465 tests. S9 COMPLETE
  (slices 1–4).** *(Legacy `sharia/screener.py` keeps its 33% boundary tests — migration to `aaoifi.py` is backlog.)*
- **QA/QC hardening pass** (independent line-by-line review of S6.5→S9): fixed YoY-vs-MoM in the regime
  feature builder, vintage look-ahead, connector date-fabrication, BLS month-13, unguarded floats,
  register_asset un-delist, beginner-mode rail coverage, sanitiser whitespace bypass — each with a
  regression test (`tests/test_qa_hardening.py`). → **419 passed**. (Broker write-atomicity deferred to S12.)
- **Dashboard v2** (post-Alaa cross-build review): rebuilt `dashboard/` as `snapshot.py` (pure JSON snapshot
  from the 7 DBs) + `generate.py` (rich, tabbed, **CSS-only / zero-JS**, fully offline & read-only HTML).
  Adds the panels a portfolio tracker lacks — **Edge-Proof verdicts + Constitution rejections-with-reasons**,
  macro regime, and an honest live-money safety posture. Early slice of the S10 decision-quality dashboard,
  on Alaa's visual ground but re-pointed at our governed state. `tests/test_dashboard_snapshot.py`. → **426 passed**.
- **Founder alerting + peg monitor** (more harvested from Alaa, now real code): `alerts/whatsapp.py`
  (CallMeBot 2nd channel, same credential-safe stub contract as Telegram), `alerts/redalert.py` (the
  **RED ALERT** founder-panic protocol — breathe→assess→act, informational only, never proposes a trade),
  `alerts/brief.py` (founder daily brief built from the dashboard snapshot; Telegram **or** WhatsApp; appends
  RED ALERT on a >3% drop), and `trader/regime/peg.py` (**SAR/USD peg monitor** — pure + dormant-safe DB
  reader, for the S9 regime layer). `tests/test_alerts_founder.py` + `tests/test_peg_monitor.py`. → **440 passed**.
  *(Sector-cap ≤40% guardrail deliberately deferred to S11 — needs the portfolio engine to be meaningful.)*
- **Integration status (S10.5 — Phase-1 blocker CLOSED).** The §4 loop is now **assembled** in
  `loop/assembled.py` (`AssembledLoop.run_tick`): Observe(regime) → Opportunity Router → **Allocator (Edge Proof +
  Constitution)** → Budget Kernel → phase-gated Human-Approval → Act(paper). Every action routes through
  `Allocator.request(...)`, never `Constitution.evaluate` directly, so **a buy with no passing EdgeReport is
  rejected by the assembled loop** (invariant test). Scheduled ops have real entrypoints (`loop/jobs.py` —
  `python -m loop.jobs daily|weekly`). *The legacy `loop/runner.py` is unchanged (its tests still pass); the
  assembled loop is the real harness — S11 strategies feed it candidates.*
- **S10 ✅ Full Edge Proof** (`engine/edge_proof.py`, 17 checks + shadow/enforcing) · **S10.5 ✅ loop assembled**
  (`loop/assembled.py`, Phase-1 blocker closed) · **S11 ✅ Strategy Registry + Portfolio Engine + Learning**
  (`strategies/` trio + dividend_growth + mixer + promotion ladder; `portfolios/` 6 seed portfolios + lifecycle
  + tolerance-band rebalancing; `learning/` 4-tier L1–L4) · **S11.5 ✅ integration keystone** (`loop/driver.py`:
  registry→full Edge Proof→assembled loop; `portfolios/holdings.py` reconciles to fund) · **S12 ✅ Edge Lab +
  Realistic Paper + ⭐ Sandbox** (`execution/` realistic fills + 4-stage dividends; `edgelab/` two-engine
  backtest + No-Edge→DCA; `sandbox/` full system on a live feed + virtual money — the micro-live track record).
  **→ 543 tests** · **S12.5 ✅ Research Desk framework** (`research/` evidence-object contract + desks + master
  switch DORMANT by default; evidence-only, no execute path) · **S13 ◑ Micro-Live readiness** (`governance/
  approval.py` human gate withholds by default; `broker/manual.py` Sahm path; `broker/live.py` gated LiveBroker
  refuses by default; `ops/live_readiness.py` not-ready by default). **→ 557 tests** · **S14 ✅ architecture
  documented** (`docs/CAMEL_ARCHITECTURE.md`; physical reorg deferred) · **Backlog sweep ✅** (`demo.py` one-command
  governed-tick + dashboard demo; `sharia/screener.py` now delegates to verified `sharia/aaoifi.py` — one 30% screen;
  `data/connectors/base.py` retry/backoff + descriptive UA; real health checks cpu/mem/creds; `strategies/analytics.py`
  yield-on-cost + moat matrix). **→ 571 tests. The whole BUILD (S1–S14) is done; going LIVE is the founder's explicit
  act (machine hardening + ≥28-day track record + phase-flip).**
- **7-DB architecture live.** All modules now use domain-specific SQLite files via `CamelDbs`.
- **First look:** `python demo.py` → seeds the 7 DBs, runs one fully-governed tick, writes the read-only dashboard
  (offline, paper-only, no creds). Smoke-tested by `tests/test_demo.py`.

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
                  aaoifi.py — ⭐ verified in-house AAOIFI screen (S9 — ≤30/≤30/≤67/≤5%, 12-mo-avg mktcap, 11 sectors)
                  cross_check.py — multi-state status + disagreement→freeze + authority stack + drift (S9)
                  screener.py — LEGACY quarterly re-screen (33%; superseded by aaoifi.py)
                  classifier.py — business-model haram classifier

data/             provenance.py — point-in-time provenance fields + source_documents (S8)
                  entity_resolver.py — resolve(ticker) → full identity + ETF look-through (S9)
                  source_registry.py — SourceSpec registry (FRED, SEC EDGAR, …) (S8)
                  connectors/ — base.py (SourceConnector + injectable transport), macro_base.py,
                                fred.py, treasury.py, world_bank.py, bls.py, sec_edgar.py,
                                bea.py, eia.py, etf_holdings.py (CSV look-through),
                                news_base.py (sanitise/redact), gdelt.py, acled.py (S8)
                  store.py — store_price / get_prices (→ camel_market.db)
                  triangulation.py — cross-source disagreement (>0.5% flags)
                  alpaca.py — Alpaca paper EOD ingestion adapter
                  freshness.py — stale-data gate (S4)
                  quality.py — data quality scoring → decision_eligible (S4, refined S8)
                  sanitiser.py — raw web text → structured JSON, injection filter (S4)
                  congress_filings.py — ⏳ PLANNED (S11) STOCK Act filing adapter (signal-only, never blind copy)
                  playwright.py — headless browser adapter stub (NotImplementedError; live → S8 scraping policy, QA-only)

governance/       config_guard.py — proves agent has no write path to founder config (S4)
                  tool_permissions.py — Tool Permission Matrix (S4)
                  beginner_mode.py — only-tightens rail (S6.6)
                  (note: BudgetKernel lives in capital/budget_kernel.py, not here)

engine/           thesis.py — ThesisCard + BaseRateCard (no I/O, no DB)
                  edge_proof_v0.py — evidence gate v0 from market.db (S4.5; cheapest first filter)
                  edge_proof.py — ⭐ full 17-check Edge Proof engine (S10): run_full_edge_proof (pure),
                  evaluate_signal_full (DB wrapper), gate (shadow/enforcing), edge_reports audit log

strategies/       ✅ S11 — base.py (BaseStrategy + Signal/Context/Meta + promotion ladder + tradeable guard)
                  registry.py — StrategyRegistry: register, lookup, activate/pause/kill, weight (band),
                  promote/demote, strategy-portfolio matrix + regime filter (signals_for)
                  core_dca.py · quality_momentum.py · etf_rotation.py · dividend_growth.py · dividends.py · mixer.py
                  (⏳ backlog after the Edge Lab: trailing_stop · dca_ladder · momentum · mean_reversion · congress_signal — NOT on disk)

execution/        ✅ S12 — realistic-paper engine: fill.py + slippage (cross the spread, partial fills,
                  fees, STALE-DATA REJECTION, no $1 fallback), realistic_paper.py (whole-share),
                  corporate_actions.py (4-stage dividend NRA pipeline + split replay)
edgelab/          ✅ S12 — backtest.py (cost-aware, two-engine cross-check, beats-DCA), honest.py
                  (walk-forward + overfit guard + crisis windows), no_edge.py (No-Edge → DCA protocol)
sandbox/          ✅ S12 — runner.py: ⭐ full assembled system on an injected live feed + virtual money
                  (regime→strategy→full Edge Proof→Constitution→realistic fill); the micro-live track record

portfolios/       ✅ S11 — engine.py: Portfolio + lifecycle + 6 seed portfolios + allocation +
                  tolerance-band rebalancing (suggestions, not auto-trades) + 4-level risk budgets +
                  persistence (portfolios table)
                  holdings.py — per-portfolio weighted-avg holdings + reconcile_to_fund (S11.5)

learning/         ✅ S11 — 4-tier learning engine:
                  base_rate_updater.py — L1: update strategy base-rates after trade resolution
                  strategy_scorer.py — L2: score vs expected; compute auto weight within band
                  regime_matcher.py — learn regime→strategy affinity from resolved outcomes
                  anomaly_detector.py — flag systematic underperformance vs base-rate
                  improvement_proposer.py — L3: write proposed changes for founder approval
                                            (proposes only — never auto-applies)

loop/             runner.py — LoopRunner (legacy LoopConfig harness; tests still pass)
                  assembled.py — ⭐ AssembledLoop (S10.5): the real §4 tick — Observe(regime)→Router→
                  Allocator(Edge+Constitution)→Budget→Approval→Act; closes the Phase-1 blocker
                  jobs.py — scheduled entrypoints (S10.5): run_daily_ops / run_weekly_safety (python -m loop.jobs)
                  driver.py — ⭐ S11.5 keystone: registry→context→mixer→FULL Edge Proof→assembled loop (run_strategy_tick)
                  state.py — RunState + begin/update/finish_run (→ camel_portfolio.db)
                  scheduler.py — Windows Task Scheduler entrypoint (EOD, once daily)
                  intraday_monitor.py — ⏳ PLANNED (S11) 5-min position manager during market hours

broker/           paper.py — PaperBroker(portfolio_db, market_db)
                  positions.py — position accounting: apply_fill (avg cost, realized P&L), held_qty (S6.6)
                  live.py — LiveBroker stub (Phase 1+)

ledger/           writer.py — append_entry + SHA-256 hash chain (→ camel_portfolio.db)
                  reconcile.py — verify_hash_chain + balance diff

entrepreneur/     product_gate.py — 17-field ProductThesis + evaluate_gate (S7)
                  constitution.py — EntrepreneurConstitution (separate rails; code-gen-only autonomy)
                  build_pipeline.py — 10-stage state machine (no skip; PRODUCTION needs founder approval)

trader/regime/    features.py (macro features from macro_observations), classifier.py (10-state
                  regime + confidence + themes), history.py + regime_history table (S9),
                  peg.py — SAR/USD peg monitor (pure peg_status + dormant-safe latest_peg_status)

trader/events/    intelligence.py — dedupe + quorum + dictionary entity-linker + severity/direction/
                  theme over news_events (safe=1 only) (S9 slice 3)
                  reactions.py — event_reactions substrate (forward returns/drawdown/excess/regime;
                  hindsight study table for S10 event studies, not a live signal)

alerts/           telegram.py — credential-safe one-way notifier (+approve/veto S11)
                  whatsapp.py — CallMeBot 2nd channel (same stub contract)
                  redalert.py — RED ALERT founder-panic protocol (informational; never trades)
                  brief.py — founder daily brief from the dashboard snapshot (any notifier)
                  daily.py — ops/health daily report delivery

capital/          allocator.py — Allocator.request() routes through Edge Proof + Constitution
                  budget_kernel.py — BudgetKernel: per-action + rolling spend limits + capital buckets (S4)

ops/              kill_switch.py — halt / resume / is_halted (file flag)

dashboard/        snapshot.py — pure JSON snapshot from the 7 DBs (positions, edge decisions,
                  guardrail rejections-with-reasons, regime, safety posture) — read-only, offline
                  generate.py — rich tabbed CSS-only HTML renderer, **re-skinned to the Camel Design
                  System** (malachite/gold/parchment tokens, serif/sans/mono voices; offline, no JS).
                  Design reference: docs/source-materials/camel-design-system/

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
Do not let an Entrepreneur product launch, spend, collect data, use third-party assets, or make
  legal/financial/medical claims without passing the Entrepreneur Constitution + founder approval (S7).
Do not let the agent do more than code-generation autonomously on the Entrepreneur arm.
Do not publish copy with overstated compliance wording ("100% Sharia certified", "guaranteed", etc.).
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
| `docs/CAMEL_ARCHITECTURE.md` | Layered module map (S14) — how every package composes into the trust-inverted system |
| `docs/CAMEL_CONSTITUTION.md` | The rules in prose (Sharia, risk, phase gates) |
| `docs/CAMEL_DATA_CONTRACTS.md` | 7-DB schemas, point-in-time discipline, data quality |
| `docs/CAMEL_TESTING.md` | Test strategy, adversarial + integration suites |
| `docs/CAMEL_LIVE_READINESS.md` | Phase 1 go-live checklist + definition of done |
| `docs/CAMEL_MACHINE_HARDENING.md` | S6 founder machine-setup checklist (Tailscale, BitLocker, secrets, backups, NTFS config lock, dead-man's-switch) |
| `docs/CAMEL_BROKER_MATRIX.md` | Broker capability comparison + resolved direction (Alpaca + Sahm manual + IBKR Phase 2) |
| `docs/CAMEL_DATA_SOURCES.md` | Verified data-feed catalogue + connector build-list (deep-research output; drives S8/S8.5/S9 Sharia ratios) |
| `docs/CAMEL_ALAA_REVIEW.md` | Review of Alaa's parallel Camel (founder-facing dashboard + coach skill); adopt/adapt/decline + sprint mapping |
| `docs/CAMEL_CHANGELOG.md` | Sprint & decision history |
| `docs/source-materials/` | Archived original PRDs/specs/playbook (provenance only) |
| `HANDOFF.md` | Current status + tech stack + how to run |

**Rule:** a fact has ONE home. Changing a sprint? Edit `docs/CAMEL_ROADMAP.md`, not here.
Code beats docs: `guardrail/constitution.py` + `config/limits.yaml` are authoritative.

---

## Build roadmap - summary  (full detail: `docs/CAMEL_ROADMAP.md` — Roadmap v3)

Sequence (**Roadmap v3** — data backbone before the proof engine; Entrepreneur moved earlier):
```
S1 OK -> S2 OK -> S3 OK -> S4 OK -> S4.5 OK -> S5 OK -> S5.5 OK -> S6 OK -> S6.5 OK -> S6.6 OK -> S7 OK ->
S8 ~CORE (10 connectors; rest deferred) -> S8.5 (Real-Time Data Tier) -> S9 ✅ (Knowledge Graph + Regime + Sharia cross-check)
-> S10 ✅ (Full Edge Proof) -> S10.5 ✅ (Operator-Loop Assembly) -> S11 ✅ (Strategy Registry + Portfolio + Learning)
-> S12 ✅ (Edge Lab + realistic paper + Sandbox Mode + No-Edge protocol) -> S12.5 (Research Desk; design, dormant)
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
| S6.5 OK | Safety & Accounting hotfix | phantom sell blocked; frozen-name close-only; buy needs edge; no $1 fallback in non-test paths (309 tests) |
| S6.6 OK | Position accounting + Ops hardening + Beginner Mode | positions table on every fill (avg cost, realized P&L, exact phantom guard, reconcile); illiquidity fail-closed in live; disk-test mocked + unknown→YELLOW; dead-man's-switch; SQLite WAL; beginner-mode; broker matrix (331 tests) |
| S7 OK | Entrepreneur Product Engine (engine; agent scope = code-gen only) | 17-field gate + separate Entrepreneur Constitution + 10-stage pipeline; no launch without founder approval (352 tests) |
| S8 ~ | Data Intelligence Backbone (top-20 connectors) | **slices 1–5 done** (framework + provenance + 10 connectors incl. ETF look-through + news injection-hardening + scraping policy, 389 tests; all 3 stub DBs real); ~10 connectors + market-data + paid remain |
| S8.5 | Real-Time Data Tier *(founder)* | streaming quotes + live-news + real-time monitor/alerts; separate realtime store (EOD bars untouched); monitoring-only unless quorum; **execution stays EOD** |
| S9 ✅ | Knowledge Graph + Regime + Sharia cross-check | **slices 1–4 done** (entity resolver + 10-state Regime Engine + event intelligence/`event_reactions` + multi-state AAOIFI Sharia cross-check w/ disagreement→freeze + peg wiring), **465 tests** |
| ✅ S10 | Full Edge Proof Engine (17 checks) | `engine/edge_proof.py` — 17 checks, pre-registered thresholds, multiple-testing penalty, signal-decay, Sharia fail-safe, model-disagreement→human, shadow/enforcing, `edge_reports` log. **Now fed real strategy signals via the S11.5 driver.** *(Regime-conditioned sample + dashboard panels: backlog)* |
| ✅ S10.5 | Operator-Loop Assembly + Runtime (Workstream A/B) | **DONE (486 tests):** `loop/assembled.py` assembles Observe→Router→Allocator(Edge+Constitution)→Budget→Approval→Act; invariant test proves **a buy with no EdgeReport is rejected by the assembled loop** (Phase-1 blocker CLOSED); `loop/jobs.py` scheduled daily/weekly entrypoints; still paper |
| ✅ S11 (513 tests) | Strategy Registry + Portfolio Engine + Learning | >=3 strategies (trio incl. dividend_growth w/ **lot-level + gross→NRA-withholding→net** mechanics) pass Edge Proof; **multi-portfolio (lifecycle incubate→retire, tolerance-band rebalance, multi-benchmark, 6 seed portfolios, portfolio-scoped positions/ledger reconciling to fund)**; meets the 15-item acceptance checklist; never auto-edits the Constitution |
| ✅ S12 (543 tests) | Edge Lab + realistic paper + Sandbox Mode | two-engine cross-check; delisted handled; beats simple DCA after costs; ⭐ sandbox (live data + virtual money) runs the full system; No-Edge protocol → DCA |
| S12.5 | Research Desk / Analyst Agents *(founder; design now, dormant)* | per-vertical research agents (Agent SDK — full roster incl. market-microstructure + execution/TCA) write evidence only via the **evidence-object contract**, never act; narrow/safe learning (no retrain, no Constitution edits); token budget; master switch defaults OFF |
| S13 | Micro-Live Readiness (Phase 1) | all live-readiness boxes pass |
| S14 | Module Restructure | full suite green after restructure |

**Open decisions, full sprint detail, and Definition of Done:**
`docs/CAMEL_ROADMAP.md` + `docs/CAMEL_LIVE_READINESS.md`.