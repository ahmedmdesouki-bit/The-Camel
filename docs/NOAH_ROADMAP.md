# NOAH ROADMAP - Canonical sprint plan (S1-S12)

> **Canonical home for the build roadmap, open decisions, and definition of done.**
> The operating manual (Noah_CLAUDE.md) carries only a one-line summary table and points here.
> Last updated: 2026-06-05.

---

## Build roadmap

**Sequence (two half-sprints inserted per the v1 enhancement proposal — evidence and ops
visibility pulled forward):**
```
S1 ✅ → S2 ✅ → S3 ✅ → S4 → S4.5 (Edge Proof v0) → S5 → S5.5 (Minimal Ops) →
S6 → S7 → S8 → S9 → S10 → S11 → S12
```
Guiding principle reaffirmed: **Safety first. Evidence second. Autonomy last.**

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

*Point-in-time timestamp columns (do this NOW, before data accumulates — retrofitting
historical rows is impossible):*
- Add to `prices`, and to all future macro/fundamentals/news tables, four distinct timestamps:
  - `event_date` — when the thing actually happened
  - `reported_at` — when the market/public learned it
  - `ingested_at` — when Noah collected it (exists today)
  - `known_at` — when Noah was *allowed* to use it
- This is the foundation of honest backtesting (S10). Without it, look-ahead bias is
  baked in and every backtest lies. Cheap now; impossible to add retroactively.

*Config immutability — prove the rules cannot be edited:*
- `governance/config_guard.py` — verifies at startup that the agent process has no write
  path to `config/limits.yaml`, the whitelist, tool-permission config, budget config, or
  approval thresholds. On Windows, enforced via file ACL check + a runtime write-attempt test.
- Test asserts: an agent-initiated write to any founder-owned config **raises and is logged**.
  This makes Constitution rule #7 ("Noah cannot change its own rules") a *proven* invariant,
  not an asserted one.

*Kill-switch hardening:*
- Move the `is_halted()` check **inside `Constitution.evaluate()`** so it gates EVERY
  consequential action (trade, spend, deploy), not just the loop start. A halted system
  rejects all consequential actions structurally — there is no path around it.

*Paper execution realism marker:*
- `broker/paper.py` stamps every simulated fill with an honesty flag so performance data is
  never mistaken for real:
  ```json
  {"execution_quality": "simulated_unrealistic", "fill_model": "last_close",
   "performance_valid_for": "loop_testing_only"}
  ```
  Real fill modelling (spread, slippage, partial fills) comes with LiveBroker / Edge Lab.

*Data quality scoring (v1 here, refined in S7):*
- `data/quality.py` — `score(symbol, date) → dict` combining source_count, freshness_hours,
  source_agreement (from triangulation), source_reputation (from allowlist). Emits
  `quality_score` and `decision_eligible`. Stale or single-source low-quality data →
  `decision_eligible=false` → blocks action.

*Secrets-leak tests (cheap, high-value):*
- Tests that FAIL if: `.env` is tracked by git · an API key pattern appears in any log file ·
  a key appears in a DB row · a key appears in an exception trace. (Plaintext-secrets startup
  refusal lands in S6 with the secrets manager.)

*Adversarial test suite — established here, extended through S10:*
S4 cases: (1) agent edits config → blocked; (2) trade frozen symbol → blocked; (3) act on
stale data → blocked; (4) duplicate order → blocked; (5) bypass tool permissions → blocked;
(6) Playwright broker action → blocked; (7) budget breach → blocked; (8) kill switch blocks
action mid-loop. Remaining cases (prompt-injection override, broker mismatch, ledger tamper,
no-EdgeProof signal, DCA into deteriorating name, model disagreement, backtest future data)
land in S4.5 / S5 / S7 / S8 / S10 as those modules arrive.

*ThesisCard extension — full standardised template (§5.6):*
- `company` (display name), `regime`, `theme`, `sharia_status`, `time_horizon`
- `signal_summary`, `why_now`, `already_priced_in`
- `worst_forward_return`, `avg_drawdown` (base-rate fields)
- `valuation_view`, `liquidity_view`, `portfolio_fit`
- `price_invalidation`, `fundamental_invalidation`, `sharia_invalidation`, `time_stop`
- `order_type` (limit by default), `approval_status`, `final_decision`
- **`opportunity_cost_justification`** (required) — must answer: *"Why is this better than
  simply buying more SPUS/HLAL?"* If it cannot answer, the thesis is rejected. This is the
  default skeptic gate against narrative-driven trades.
- Output format: `probability + expected_return + downside_risk + confidence + invalidation + approval_status`

**Gate:** Constitution ≥ 40 tests; stale data blocks action; budget limits enforced;
no duplicate orders possible; config write attempt by agent is blocked + logged; kill
switch blocks action mid-loop; point-in-time columns present on `prices`; paper fills
carry the realism marker; secrets-leak tests pass.

**STATUS: COMPLETE** (branch `s4-hardening`, 197 tests; guardrail file = 43, ≥40 met).
Deferred by dependency: **max cancel/replace attempts** → S11 (no cancel/replace path exists
until LiveBroker); **earnings blackout** → S7 (needs an earnings calendar from the
fundamentals DB). Corporate-action check was already pre-deferred to S7.

---

### S4.5 — Edge Proof v0  (evidence gate, pulled forward)

*Rationale: the paper loop starts running in S5–S6, but the full Edge Proof Engine isn't
ready until S7. Without a v0 gate, Noah would make trade decisions on narrative alone for
two+ sprints — exactly the failure mode the project exists to prevent. v0 closes that window
using only the `market.db` price data we already have. No macro/fundamentals/news needed.*

`engine/edge_proof_v0.py` (moves to `trader/edge_proof_v0.py` in S12 restructure):
- `EdgeReport` dataclass
- Simple historical hit-rate + forward-return calculator from `noah_market.db`
- Benchmark comparator (vs SPUS DCA by default)
- Basic confidence score
- `trade_allowed` boolean output

Minimum report:
```json
{
  "symbol": "SPUS", "signal": "core_etf_dca",
  "sample_size": 36, "hit_rate": 0.58,
  "median_forward_return": 0.041, "worst_forward_return": -0.14,
  "max_drawdown": -0.18, "benchmark": "SPUS_DCA",
  "benchmark_excess_return": 0.006, "confidence": 0.52,
  "trade_allowed": false,
  "reason": "Evidence too weak versus benchmark after estimated cost."
}
```

Hard rules — all default to `trade_allowed=false`:
- No EdgeReport attached → trade rejected by the allocator
- Missing sample size → rejected
- Missing benchmark → rejected
- Weak evidence (excess return not positive after estimated cost) → rejected
- Every v0 decision logged to `noah_learning.db`

The full 13-check Edge Proof Engine (S7) is built *on top of* v0 — v0 is never removed,
it becomes the cheapest first filter.

**Gate:** No trade candidate proceeds without an EdgeReport; missing/weak/stale inputs all
return `trade_allowed=false`; `trade_allowed=false` blocks the allocator; tests cover allow,
reject, missing-sample, weak-benchmark, weak-evidence, stale-input. Adversarial case added:
strategy produces a signal without Edge Proof → blocked.

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
  **Conservative routing rules (the router must lean toward inaction):**
  ```
  if no edge proof              → Wait
  if safety module incomplete   → System improvement
  if data missing               → Research
  if product evidence missing   → Research
  if capital budget unavailable → Wait
  ```
  The router can NOT recommend the Trader path without a passing Edge Proof v0.
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

**Gate:** State machine prevents state jumps; Opportunity Router returns "Wait" when all
scores are weak and "System improvement" when safety gaps are open; router cannot recommend
Trader without Edge Proof v0; Learning Ledger records every decision outcome; task queue
persists intent.

---

### S5.5 — Minimal Ops Visibility  (operational safety, pulled forward from S6)

*Rationale: operational visibility IS safety. Don't run an autonomous loop for sprints with
no way to see its health or recover it. These are the cheapest, highest-leverage ops items
from S6, brought forward so the loop is observable as soon as it's running.*

- Daily health report (text/console first; Telegram delivery in S6).
- Kill-switch test — confirm halt stops the next tick, resume restores.
- Secrets exposure check — startup scan; warn if any secret is in plaintext env.
- Backup/restore test — manual backup of all seven DBs + a verified restore.
- **Status classifier** (used by the health report and the Opportunity Router):
  ```
  GREEN  = safe to run paper loop
  YELLOW = run research only (a safety/data gap is open)
  RED    = halt all consequential actions (loss-stop, reconciliation diff, stale data)
  BLACK  = kill switch / manual founder intervention required
  ```

**Gate:** Health report emits a GREEN/YELLOW/RED/BLACK status; kill-switch test passes;
backup restore verified; no plaintext secret goes undetected.

---

### S6 — Dashboard + Monitoring + Kill Switch over Tailscale + Ops Hardening
*(Was original S4; minimal ops now live from S5.5 — S6 is the full build-out)*
- Dashboard reading live SQLite state (positions, P&L, ledger, guardrail events, Sharia flags).
- Daily Telegram health report — exact format (§11.8):
  ```
  Noah Daily Health Report
  System status: GREEN | Mode: Paper | Broker: Connected | DB: Connected
  Guardrail Service: Passed | Open thesis cards: N | Open paper positions: N
  Live capital at risk: $0 | Paper capital at risk: $N | Issues: None
  ```
  (System status = the GREEN/YELLOW/RED/BLACK classifier from S5.5; now delivered over Telegram.)
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

Statistical controls (the contents of `calculate_base_rate` + `generate_edge_report`,
enriching the v0 report): minimum sample-size threshold · confidence interval · median AND
mean forward return · worst forward return · max drawdown · Sharpe-like risk-adjusted score ·
benchmark excess return · transaction-cost adjustment · slippage adjustment · regime-specific
base rate · signal-decay check · false-positive rate · outlier-sensitivity check.

Full edge report (extends the S4.5 v0 report; reject if confidence interval crosses zero):
```json
{
  "trade_allowed": false, "decision_class": "REJECT_WEAK_EDGE",
  "sample_size": 42, "hit_rate": 0.61,
  "median_forward_return": 0.084, "mean_forward_return": 0.071,
  "worst_forward_return": -0.21, "max_drawdown": -0.18,
  "benchmark_excess_return": 0.032, "estimated_cost": 0.006,
  "net_expected_return": 0.026, "confidence_interval": [-0.04, 0.09],
  "confidence": 0.66,
  "reason": "Excess return positive but confidence interval crosses zero."
}
```

Data quality scoring is refined here (full version of the `data/quality.py` v1 from S4):
multi-source agreement, reputation, freshness, provenance — feeding `decision_eligible`.

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
- `name: str` — unique identifier used in the registry, logs, and Learning Ledger
- `description: str` — plain-English summary of the strategy's logic and intent
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
| `trailing_stop.py` | Video Level 1 | Trailing floor — stop rises as price rises, locking gains. Dynamic invalidation point replaces fixed `price_invalidation`. Default rules: −10% initial stop; move floor up 5% below current price every time stock climbs 10%. **50% profit early-close rule**: if position reaches 50% of its profit target before time-stop, close early and recycle capital. All parameters overridable in `limits.yaml`. |
| `dca_ladder.py` | Video Level 1 | Systematic laddering — buy dips across predefined price levels. Default ladder (video-sourced, all overridable in `limits.yaml`): −15% → buy 10 shares; −20% → buy 10 more; −30% → buy 20 more; −50% → buy 50 more. Floor only goes down to add, never triggers a sell. |
| `congress_signal.py` | Video Level 2 | Congressional filing signal — STOCK Act disclosures (45-day lag) sourced from **Capital Trades** (capitaltrades.com). Used as **one observe-step signal** only; does NOT bypass Edge Proof; blind copy is forbidden. Only Sharia-compliant names among the disclosed trades are considered. |
| `etf_rotation.py` | Regime logic | Rotate between SPUS / HLAL / MNZL based on macro regime classification. |
| `momentum.py` | Price action | Trend-following on compliant single names and ETFs. |
| `mean_reversion.py` | Price action | Quality-dip accumulation when a compliant name pulls back to key support. |

**Phased rollout within S8 (validate few before adding many):**
- **First trio** — `momentum.py`, `mean_reversion.py`, `dca_ladder.py`. These are
  self-contained: computable from `noah_market.db` price data alone, no external deps.
- **Then** — `etf_rotation.py` (needs regime classification → depends on the S7 macro DB,
  so it follows, not leads).
- **Delayed** — `congress_signal.py` (delayed, noisy disclosures; easily narrative-driven —
  keep as a research signal, revisit after S10), `mean_reversion`→full `StrategyMixer`
  complexity, and any intraday automation beyond monitoring.
- Founder decision pending: whether `congress_signal` is delayed until after S10.

**DCA ladder safety guardrails (mandatory — no blind averaging down):**
- Allowed only for: (a) approved core Sharia ETFs, or (b) individual equities with a passing
  Edge Proof AND no fundamental deterioration.
- **No DCA** if Sharia status is frozen/watch.
- **No DCA** if latest fundamentals deteriorated.
- **No DCA** if the drawdown is driven by fraud, litigation, delisting, regulatory shock, or
  a failed Sharia re-screen.
- DCA total exposure must stay inside position + sector caps.
- **DCA must have a final stop condition — no infinite averaging down.**
- Default (ETFs only at first) is a founder decision: ladder on individual stocks vs ETFs only.

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

#### Intraday Position Monitor (`loop/intraday_monitor.py`)

The EOD loop handles research, thesis, and new position decisions. It is not fast enough
for active position management strategies like trailing stop and DCA ladder, which must
react to intraday price moves in near real-time.

Two separate loops run concurrently:

| Loop | Cadence | Responsibility |
|---|---|---|
| **EOD loop** (`loop/scheduler.py`) | Once daily, post-close | Observe → Thesis → Choose → Act → Measure → Learn |
| **Intraday monitor** (`loop/intraday_monitor.py`) | Every 5 min, market hours only (9:30am–4pm ET, Mon–Fri) | Manage open positions: update trailing floors, trigger ladder buys, apply 50%-profit early close, check stop losses |

The intraday monitor does **not** open new positions — it only manages positions that the
EOD loop has already opened and the Constitution has already approved. It operates within
the same guardrail envelope: every management action (floor move, ladder buy, early close)
routes through `Constitution.evaluate()` before execution.

`config/limits.yaml` controls the monitor cadence and market hours window
(founder-owned, agent-read-only).

#### Regime → Strategy affinity learning (`learning/regime_matcher.py`)

After enough resolved trades (minimum N=20 per regime), the system learns empirically
which strategies perform above/below their base-rate in each regime, and updates the
`applicable_regimes` suggestions it proposes to the founder. The founder approves all
affinity changes (Level 3).

**Gate:** Strategy registry has ≥3 active strategies; all produce signals that pass Edge
Proof; trailing stop replaces fixed invalidation for trending positions with 50%-profit
early-close working; DCA ladder fires at correct price levels from `limits.yaml` defaults;
congress_signal feeds observe step from Capital Trades without bypassing proof;
intraday monitor runs every 5 min during market hours and correctly updates floors without
opening new positions; base-rate updater records every resolved trade; auto weight
adjustment stays within founder-set band; improvement proposals land in Learning Ledger.
Starter trio (momentum / mean_reversion / dca_ladder) validated before any others are
activated. Adversarial case added: DCA attempts to average down into a deteriorating /
frozen / litigated name → blocked.

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
  12. Distribution channel
  13. First 10 target customers
  14. Willingness-to-pay evidence
  15. Compliance risk rating
  16. Data retention policy
  17. Human-review requirement for generated outputs
- Build pipeline: product_thesis → PRD → build plan → GitHub issues → MVP → tests →
  staging → human approval → production → outcome measurement.
  No direct production deploy without tests + founder approval.
- Entrepreneur Constitution (separate from Trader constitution). Hard guardrails:
  - No legal / financial / medical claims without human approval.
  - No collection of sensitive data without explicit privacy review.
  - No use of copyrighted templates/assets without a rights check.
  - No production launch without founder approval.
  - No paid ads without Budget Kernel approval.
  - No customer-facing "official compliance guarantee" wording.
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

**Benchmark hierarchy (compare against all, in order):**
1. Cash · 2. Simple monthly DCA into SPUS · 3. SPUS buy-and-hold · 4. HLAL buy-and-hold ·
5. MNZL where relevant · 6. Equal-weight Sharia ETF basket · 7. Noah active strategy.
If Noah does not beat simple DCA on risk-adjusted terms after costs, Noah does not trade actively.

**Strategy kill criteria — disable or move to research-only if ANY hold:**
```
Out-of-sample return < benchmark
Max drawdown > allowed threshold
Hit rate materially below base rate
Performance depends on a single outlier
Transaction costs erase the edge
Signal works only in one cherry-picked regime
Sample size too small
```
A killed strategy is deactivated in the registry (Level 3 — logged, founder notified).

**Gate:** Every strategy tested out-of-sample; delisted companies handled; full benchmark
hierarchy compared; weak signals rejected; each strategy has a published base-rate record;
StrategyMixer blend tested; kill criteria enforced; Noah beats simple DCA before any live
execution. Adversarial case added: backtest attempts to use future / restated data → blocked
by point-in-time `known_at` discipline.

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
- Margin disabled · options disabled · API key scoped to minimum required permissions.
- Manual dry-run completed.
- One **rejected** trade test completed in the live environment (no order placed).
- One **approved** micro trade completed manually before any automation.
- Emergency broker login tested.

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
3. First Entrepreneur product to ship. *(Note: the v1 proposal suggested an Arabic
   travel/hospitality SLA assistant, but that assumed a founder background we have no record
   of — treat as an example, not a recommendation. Founder to decide from actual domain.)*
4. Canonical Sharia screener: Musaffa vs Zoya (use one canonical, the other as cross-check).
5. Starting limit values in `config/limits.yaml` (start very low; approval for all paid spend).
6. Capital bucket percentages (defaults in S4 Budget Kernel).
7. DCA ladder: ETFs only at first, or also individual equities with Edge Proof?
8. `congress_signal`: delay until after S10, or build in S8?
9. Default benchmark: SPUS primary, HLAL secondary, Cash + DCA as controls — confirm?

---

## Definition of done (v1)

All of the following must be true before Phase 1 (live money) is unlocked:

- All tests green (target ≥ 200 tests by S8).
- Agent cannot modify its own constitution / config — **proven by config-immutability test**, not asserted.
- Tool permissions enforced before every tool action.
- Budget limits enforced before every money/spend action.
- Data freshness checked before every trade decision; stale/single-source data is decision-ineligible.
- Point-in-time timestamps present on all decision-relevant tables (no look-ahead bias).
- Broker/account reconciliation clean.
- Kill switch checked inside `Constitution.evaluate()` — gates every consequential action.
- State machine prevents skipped steps.
- ThesisCard required before any paper trade, including the opportunity-cost justification.
- Invalidation required before any paper trade (fixed or trailing floor).
- Every action logged.
- **No trade proceeds without an EdgeReport** (v0 from S4.5; full engine from S7).
- Edge Proof Engine approved at least one signal.
- Adversarial test suite green (config edit, frozen symbol, stale data, duplicate order,
  permission bypass, Playwright broker action, injection override, broker mismatch, ledger
  tamper, no-EdgeProof signal, DCA into deteriorating name, model disagreement, future-data backtest).
- Strategy Registry has ≥ 3 active strategies with live base-rates.
- Learning Engine updating base-rates autonomously after resolved trades.
- Improvement proposals landing in Learning Ledger (Level 3 — not auto-applied).
- Daily health report working.
- Kill switch working over Tailscale.
- No live trading possible unless explicitly enabled by founder-owned config.
- 28 days clean paper operation meeting Phase 0 exit criteria.
