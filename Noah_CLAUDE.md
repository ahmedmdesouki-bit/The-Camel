# CLAUDE.md — Noah operator (context for Claude Code)

> You are working on **Noah**, a guardrailed autonomous AI operator that runs a
> continuous Observe→Thesis→Choose→Act→Measure→Learn loop across two domains:
> **Trader Noah** (Sharia-compliant markets) and **Entrepreneur Noah** (Sharia-compliant
> AI products). Founder: Chiko (Riyadh). Runtime: Windows PC.
> This file is the source of truth for how to work here. Read it fully before acting.

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
                  congress_filings.py — STOCK Act filing data adapter (stub → S8)
                  playwright.py — headless browser adapter stub (NotImplementedError; live → S8+)

engine/           thesis.py — ThesisCard + BaseRateCard (no I/O, no DB)

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
                  scheduler.py — Windows Task Scheduler entrypoint

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

## Phase 0 simplified stack

- DB: **SQLite** × 7 (migrate to Supabase when remote/dashboard needed).
- Harness: **plain Python loop** (adopt Claude Agent SDK when real tool-use autonomy needed).
- Data/broker: **Alpaca paper** (free IEX feed). yfinance ok for quick prototypes.
- Notifications/approvals: **Telegram bot** (Sprint 6).
- Scheduler: **Windows Task Scheduler** → `python loop/scheduler.py` post-close.
- Remote access + kill switch: **Tailscale**.

---

## Build roadmap

### Completed
- **S1 ✅** Guardrail Service + schema + tests. Gate: 28 rogue-action tests green.
- **S2 ✅** Sharia gate + data ingestion. Gate: off-list + haram rejected; prices land.
- **S3 ✅** Loop runner + PaperBroker + ledger + allocator. Gate: full paper loop runs; ledger reconciles.

---

### S4 — Hardening: Guardrail extensions + Budget Kernel + Data Freshness
*Constitution additions (Feedback 1 + 2):*
- Rolling Velocity Stop: 5-day rolling P&L ≤ −8% → 48h cooldown freeze; 14-day ≤ −12% → halt.
- Illiquidity / Slippage Gate: bid-ask spread > 0.5% → reject; order > 1% of 30-day ADV → reject.
  (Skips gracefully when spread data unavailable — IEX free tier limitation.)
- Additional hard rules: max orders/day, **max cancel/replace attempts** (prevent broker API
  loops), stale-data rejection, earnings blackout, source quorum, corporate action check
  (splits/mergers/delistings/ticker changes — defer to S7 enforcement).

*New modules:*
- `capital/budget_kernel.py` — daily/weekly/monthly spend limits; capital buckets
  (Core 50%, Trader 10–20%, Entrepreneur 20–30%, System 5–10%, Emergency 10–20%).
- `governance/tool_permissions.py` — Tool Permission Matrix. Full table:

  | Tool | Allowed | Requires approval | Forbidden |
  |---|---|---|---|
  | GitHub | Create branch, commit, open PR | Merge to main | Delete repo |
  | Supabase | Read/write app DB | Schema migration | Delete tables |
  | Netlify/Cloudflare | Deploy preview | Production deploy | Delete domain/DNS |
  | Playwright | Browse, scrape, QA | Submit non-financial forms | Live broker actions, move money, change account/margin/whitelist/approval settings |
  | Broker API | Paper trade | Live order | Withdrawals, margin, options |
  | Telegram | Send alerts | Approval confirmation | Change rules |

  Every tool action evaluated by `evaluate_tool_action(tool, action, state)`.
- `data/freshness.py` — `check_freshness(symbol, max_age_hours)` blocks action on stale data.
- `data/sanitiser.py` — `sanitise(raw_text) → dict` prompt-injection filter.
- `security/source_allowlist.py` — allowlist of approved data sources for critical signals;
  reject data from unlisted sources. `log_retrieved_source(url, content_hash)` appends an
  audit trail entry for every external fetch.
- `data/playwright.py` — stub adapter with `NotImplementedError` on every public function.
  Enforces the Tool Permission Matrix constraint in code: Playwright may never be used for
  live broker actions, money movement, or whitelist/approval changes. Real implementation
  wired in a later sprint for scraping/QA only.

*Schema extensions (existing tables only):*
- `whitelist`: +`historical_drift_count`, +`purification_ratio` ✅ (live in noah_sharia.db)
- `sharia_events`: +`trigger_period`, +`reasoning_summary` ✅
- `orders`: +`client_order_id` (UUID, idempotency) ✅
- `broker/paper.py`: `pre_flight_execution_check()` — raises `DuplicateOrderException`.

*ThesisCard extension — full standardised template (§5.6):*
- `company` (display name), `regime`, `theme`, `sharia_status`, `time_horizon`
- `signal_summary`, `why_now`, `already_priced_in`
- `worst_forward_return`, `avg_drawdown` (base-rate fields)
- `valuation_view`, `liquidity_view`, `portfolio_fit`
- `price_invalidation`, `fundamental_invalidation`, `sharia_invalidation`, `time_stop`
- `order_type` (limit by default), `approval_status`, `final_decision`
- Output format: `probability + expected_return + downside_risk + confidence + invalidation + approval_status`

**Gate:** Constitution ≥ 40 tests; stale data blocks action; budget limits enforced;
no duplicate orders possible.

---

### S5 — Operator State Machine + Opportunity Router + Learning Ledger
- `operator/state_machine.py` — 11 formal states:
  `IDLE → OBSERVING → RESEARCHING → FORMING_THESIS → TESTING_EDGE →
   AWAITING_APPROVAL → ACTING → MONITORING → LEARNING → PAUSED → KILLED`
  Transition rules: cannot jump from FORMING_THESIS to ACTING; cannot ACT without guardrail
  approval; cannot leave PAUSED without founder approval.
- `operator/opportunity_router.py` — scores five valid paths:
  **Trader / Entrepreneur / Research / System improvement / Wait**.
  "Wait" and "System improvement" are first-class outputs, not the absence of a decision.
  Scoring weights (§11.5): Expected upside 20% · Evidence quality 20% · Downside risk 20% ·
  Sharia/compliance clarity 15% · Capital required 10% · Time required 10% ·
  Strategic learning value 5%.
  Output: `{recommended_path, reason, confidence, capital_required, approval_required}`.
- `operator/task_queue.py` — persistent task queue; every planned action is enqueued before
  execution, enabling pause/resume and auditing of intent vs outcome.
- `operator/learning_ledger.py` — writes to `noah_learning.db`:
  decision_type, thesis_summary, expected/actual outcome, mistake_type, lesson, pattern.
  Combines outcomes from Trader AND Entrepreneur arms (shared learning system).
- `operator/append_op_log.py` — append-only operator action log (separate from the trade
  ledger); every state transition and tool invocation is recorded.
- `ops/health_monitor.py` — full check list:
  machine uptime · internet status · **disk status** · **CPU/memory usage** ·
  DB connections · broker connection · **Telegram connection** ·
  **secrets availability (without exposing secrets)** · last heartbeat ·
  guardrail service status · current mode (paper/micro-live/paused/killed).

**Gate:** State machine prevents state jumps; Opportunity Router returns "Wait" when no
edge proven; Learning Ledger records every decision outcome; task queue persists intent.

---

### S6 — Dashboard + Monitoring + Kill Switch over Tailscale + Ops Hardening
*(Was original S4)*
- Dashboard reading live SQLite state (positions, P&L, ledger, guardrail events, Sharia flags).
- Daily Telegram health report — exact format (§11.8):
  ```
  Noah Daily Health Report
  Status: Running | Mode: Paper | Broker: Connected | DB: Connected
  Guardrail Service: Passed | Open thesis cards: N | Open paper positions: N
  Live capital at risk: $0 | Paper capital at risk: $N | Issues: None
  ```
- Kill switch reachable over Tailscale.
- Machine heartbeat + uptime monitor.
- Full reconciliation report (ledger vs broker paper statement).
- **Weekly kill-switch test** — automated test fires kill, verifies loop halts, resumes; result logged.
- **Secrets manager** — move all secrets from `.env` into Windows Credential Manager or
  equivalent; startup check refuses to run if secrets are in plaintext env vars.
- **Log rotation** — bound log file growth; retain last 30 days of operator logs.
- **Off-box encrypted backup** — daily encrypted backup of all seven DB files to an
  external location; documented restore procedure tested at least once.
- **Machine hardening ops checklist** (non-code, founder action):
  BitLocker enabled · dedicated OS user for Noah · UPS/power backup · 5G/hotspot
  fallback internet · Tailscale ACLs locked to founder devices · MFA on all accounts.

**Gate:** Kill switch stops next loop tick; daily-loss-stop simulation halts; dashboard
reflects paper trade within one refresh; weekly kill-switch test passes; backup restore
verified; secrets not in plaintext.

---

### S7 — Edge Proof Engine
*The most important missing module — no live money until this exists.*

Every trade candidate passes 13 checks before a position is proposed (§5.2):

```
classify_regime()           → macro regime (expansion / contraction / crisis / recovery)
find_historical_analogues() → prior cases matching this setup
run_event_study()           → forward-return distribution around the trigger
calculate_forward_returns() → median, worst, distribution
calculate_base_rate()       → sample N, hit rate, magnitude
check_counter_signals()     → what would invalidate the thesis
check_valuation()           → is the setup priced in?
check_momentum()            → technical / momentum confirmation (step 8 §5.2)
check_liquidity()           → spread, ADV, whole-share constraints
check_sharia()              → re-confirm whitelist + frozen status at trade time (step 10 §5.2)
check_portfolio_fit()       → position + sector concentration within current portfolio (step 11 §5.2)
corporate_action_check()    → splits, mergers, delistings, ticker changes since last screen
generate_edge_report()      → structured JSON output (below)
```

Additional guardrail wired here: **model disagreement rule** — when BOARDROOM sub-agents
(Bull, Bear, Sharia Auditor) conflict materially, `generate_edge_report()` sets
`trade_allowed=false` and routes to Human Approval Gate instead of auto-proceeding.

Minimum edge report:
```json
{
  "signal": "...", "sample_size": 42, "hit_rate": 0.61,
  "median_forward_return": 0.084, "worst_forward_return": -0.21,
  "max_drawdown": -0.18, "benchmark_excess_return": 0.032,
  "confidence": 0.66, "trade_allowed": false,
  "reason": "Sample size acceptable but excess return not strong after costs."
}
```

Observe-step structure follows: Regime → Theme → Asset Class → Sector → Company → Candidate.

**Gate:** Every signal passes all 13 checks; `trade_allowed=false` blocks the allocator;
no edge proof = no trade; model disagreement routes to human approval.

---

### S8 — Strategy Models + Learning Engine

Noah should not be locked into one approach. This sprint builds a **Strategy Registry** —
a library of named, backtested, switchable strategy modules — plus a tiered learning engine
that makes the system progressively smarter from real outcomes without violating the
Constitution's "Noah cannot change its own rules" constraint.

#### Strategy Registry (`strategies/`)

Every strategy is a module that implements `BaseStrategy`:
- `signal(observations) → List[SignalCandidate]` — what to look at
- `entry_logic(signal) → EntryPlan` — how to enter (single, ladder, scaled)
- `exit_logic(position) → ExitPlan` — fixed, trailing floor, or time-based
- `sizing_logic(signal, state) → float` — notional amount, respecting Constitution caps
- `applicable_regimes: List[str]` — which macro regimes favour this strategy
- `base_rate: BaseRateCard` — live-updated hit rate, median return, worst return, drawdown

Signals from every strategy **still pass through the full 13-check Edge Proof Engine**
before a position is proposed. Strategies generate candidates; Edge Proof validates them.

**Initial strategy library (Sharia-compliant, no options/derivatives ever):**

| Strategy | Source | Description |
|---|---|---|
| `trailing_stop.py` | Video Level 1 | Trailing floor — stop rises as price rises, locking gains. Replaces fixed `price_invalidation` with a dynamic trailing invalidation point on trending positions. |
| `dca_ladder.py` | Video Level 1 | Systematic laddering — buy on dips in compliant ETFs across predefined price levels. Position-building mode alongside single-entry. |
| `congress_signal.py` | Video Level 2 | Congressional filing signal — STOCK Act disclosures (45-day lag) aggregated from Capital Trades or similar. Used as **one observe-step signal** only; does NOT bypass Edge Proof. Only Sharia-compliant names acted on. |
| `etf_rotation.py` | Regime logic | Rotate between SPUS / HLAL / MNZL based on macro regime classification. |
| `momentum.py` | Price action | Trend-following on compliant single names and ETFs. |
| `mean_reversion.py` | Price action | Quality-dip accumulation when a compliant name pulls back to key support. |

**Wheel Strategy (Video Level 3) — permanently excluded.**
Cash Secured Puts and Covered Calls are options (derivatives). Haram + Constitution rule #1.
No exceptions. Do not revisit.

#### StrategyMixer (`strategies/mixer.py`)

Blends active strategies into a combined signal set:
- **By regime** — activate strategies with matching `applicable_regimes` for today's regime
- **By weight** — configurable weight per strategy (founder-set defaults in `limits.yaml`)
- **By performance** — within the auto-weight band, shift weight toward outperformers
- **Mixed signals** — multiple strategies can agree on the same ticker, increasing conviction

#### Ongoing Learning Engine (`learning/`) — four permission tiers

```
Level 1 — Fully autonomous (no approval):
  After every resolved trade, update the strategy's base-rate record:
  hit/miss, actual return, actual drawdown, regime at entry.
  Pure bookkeeping. No rule changes.

Level 2 — Auto within founder-set band (default ±10%):
  Adjust strategy weights based on 30-day rolling performance vs expected base-rate.
  If trailing_stop hits 68% when base-rate says 60% → weight increases.
  Band limits live in config/limits.yaml (founder-owned, agent-read-only).

Level 3 — Propose only, founder approves:
  Activate or deactivate a strategy.
  Change a strategy's regime affinity mapping.
  improvement_proposer.py writes a structured proposal to the Learning Ledger.
  Founder reviews and approves/rejects. Nothing changes without explicit approval.

Level 4 — Founder-only, system never touches:
  Add a new strategy to the registry.
  Modify the Constitution or risk rules.
  Change the ±band limits themselves.
```

#### Regime → Strategy affinity learning (`learning/regime_matcher.py`)

After enough resolved trades (minimum N=20 per regime), the system learns empirically
which strategies perform above/below their base-rate in each regime, and updates the
`applicable_regimes` suggestions it proposes to the founder. The founder approves all
affinity changes (Level 3).

**Gate:** Strategy registry has ≥3 active strategies; all produce signals that pass Edge
Proof; trailing stop replaces fixed invalidation for trending positions; DCA ladder
operates correctly on SPUS/HLAL; congress_signal feeds observe step without bypassing
proof; base-rate updater records every resolved trade; auto weight adjustment stays within
founder-set band; improvement proposals land in Learning Ledger for review.

---

### S9 — Entrepreneur Track
*(Was S8)*
- Entrepreneur Product Gate — every product must answer all 11 fields before a line of code
  is written (§11.7):
  1. Problem statement
  2. Target customer
  3. Evidence of pain
  4. Competitor check
  5. Monetization hypothesis
  6. MVP scope
  7. Build cost
  8. Launch risk
  9. Sharia / compliance check
  10. Data / privacy check
  11. Success metric
- Build pipeline: product_thesis → PRD → build plan → GitHub issues → MVP → tests →
  staging → human approval → production → outcome measurement.
  No direct production deploy without tests + founder approval.
- Entrepreneur Constitution (separate from Trader constitution).
  Risk areas: wasted money, legally risky claims, customer data mishandling, copyrighted
  assets, non-compliant products, reputational damage — all gated.
- Ship one compliant AI product (Stripe test mode acceptable for Phase 0).

**Gate:** No build without all 11 product gate fields + Sharia check + approval;
no paid spend without budget approval; no customer data collection without privacy check;
live URL; payment-capable.

---

### S10 — Edge Lab (Backtesting)
*Run after ≥ 28 days of paper data has accumulated.*

- Historical return testing: look-ahead bias prevention, survivorship bias prevention,
  data leakage checks, overfitting check.
- Walk-forward testing (out-of-sample validation).
- Transaction costs + slippage + spread modeling.
- Whole-share constraints (Sahm compatibility).
- Sharia whitelist availability at the historical point (point-in-time compliance status).
- **Delisted companies** — exclude or account for names that were delisted in the test window.
- Crisis tests: 2000 dot-com, 2008 GFC, 2020 COVID, 2022 inflation/rate shock.
- Benchmark comparison vs **SPUS / HLAL / Cash / simple DCA**.
  If Noah cannot beat simple DCA on risk-adjusted terms after costs, it should not trade actively.
- Signal leaderboard.

- Per-strategy backtesting: every registered strategy in the registry is tested independently
  and as a mixed portfolio. StrategyMixer blends are tested across regimes.
- Strategy leaderboard: rank all strategies by risk-adjusted return after costs.

**Gate:** Every strategy tested out-of-sample; delisted companies handled; all four
benchmarks compared; weak signals rejected; each strategy has a published base-rate record;
StrategyMixer blend tested; Noah beats simple DCA before any live execution.

---

### S11 — Micro-Live Readiness (Phase 1)

**Prerequisites (all must pass):**
- ≥ 28 days continuous paper operation.
- 0 guardrail breaches.
- Ledger reconciles with broker paper statement.
- Every position had thesis + invalidation point.
- Kill switch tested and confirmed working.
- Broker API key scoped trade-only, withdrawals disabled.
- Edge Proof Engine has approved at least one signal.
- Approval flow end-to-end tested.

*Deliverables:*
- Approval Channel (Telegram one-tap approve / veto with timeout = veto).
- LiveBroker (Alpaca paper → live, behind phase flag).
- Limit orders only (no market orders in live mode).
- No pre-market / after-hours trading.
- Live broker key scope verification at startup.

Initial live permissions:
```
Human approval required for every live trade.
No autonomous live execution.
Max total live capital: $100–500.
Limit orders only.
Whitelist only.
No pre-market / after-hours.
```

---

### S12 — Module Restructure (last sprint)
*(Section 14.5 of Feedback 2)*

Restructure the flat layout into a clean domain hierarchy. All 200+ tests must stay green.

```
governance/
  constitution.py       (moved from guardrail/)
  sharia_registry.py    (from sharia/)
  risk_rules.py
  budget_kernel.py      (from capital/)
  tool_permissions.py
  approvals.py

operator/
  state_machine.py
  task_queue.py
  opportunity_router.py
  learning_ledger.py
  health_monitor.py
  kill_switch.py        (from ops/)

trader/
  thesis_card.py        (from engine/)
  edge_proof_engine.py
  regime_classifier.py
  event_study.py
  forward_returns.py
  portfolio_engine.py
  paper_broker.py       (from broker/)
  broker_reconciliation.py

entrepreneur/
  product_thesis.py
  prd_generator.py
  build_workflow.py
  compliance_gate.py
  qa_checklist.py

data/
  market_data.py
  macro_data.py
  company_fundamentals.py
  news_events.py
  data_freshness.py
  sanitiser.py

security/
  prompt_injection_filter.py
  secrets_check.py
  source_validation.py

alerts/
  telegram_bot.py
  daily_report.py
```

**Gate:** Full test suite green after restructure; all imports updated; CLAUDE.md updated.

---

## Open decisions (ask the founder before assuming)

1. Live broker for Phase 1: Alpaca vs IBKR.
2. Notification channel: Telegram (default) vs Pushover.
3. First Entrepreneur product to ship.
4. Canonical Sharia screener: Musaffa vs Zoya.
5. Starting limit values in `config/limits.yaml`.
6. Capital bucket percentages (defaults in S4 Budget Kernel).

---

## Definition of done (v1)

All of the following must be true before Phase 1 (live money) is unlocked:

- All tests green (target ≥ 200 tests by S8).
- Agent cannot modify its own constitution / config.
- Tool permissions enforced before every tool action.
- Budget limits enforced before every money/spend action.
- Data freshness checked before every trade decision.
- Broker/account reconciliation clean.
- State machine prevents skipped steps.
- ThesisCard required before any paper trade.
- Invalidation required before any paper trade (fixed or trailing floor).
- Every action logged.
- Edge Proof Engine approved at least one signal.
- Strategy Registry has ≥ 3 active strategies with live base-rates.
- Learning Engine updating base-rates autonomously after resolved trades.
- Improvement proposals landing in Learning Ledger (Level 3 — not auto-applied).
- Daily health report working.
- Kill switch working over Tailscale.
- No live trading possible unless explicitly enabled by founder-owned config.
- 28 days clean paper operation meeting Phase 0 exit criteria.
