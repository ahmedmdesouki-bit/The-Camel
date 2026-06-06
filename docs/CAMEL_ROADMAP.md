# CAMEL ROADMAP - Canonical sprint plan (S1-S14, Roadmap v3)

> **Canonical home for the build roadmap, open decisions, and definition of done.**
> The operating manual (CLAUDE.md) carries only a one-line summary table and points here.
> Last updated: 2026-06-06. **Roadmap v3** (research-driven restructure) replaces the old
> S7-S12 block — see `## Roadmap v3` below for the rationale and the new sequence.

---

## Build roadmap

**Sequence (Roadmap v3 — data backbone before the proof engine; Entrepreneur moved earlier):**
```
S1 ✅ → S2 ✅ → S3 ✅ → S4 ✅ → S4.5 ✅ (Edge Proof v0) → S5 ✅ → S5.5 ✅ (Minimal Ops) → S6 ✅ →
S6.5 (Safety/Accounting hotfix) → S7 (Entrepreneur) → S8 (Data Backbone) → S9 (Knowledge Graph + Regime) →
S10 (Full Edge Proof, 17-check) → S11 (Strategy Registry) → S12 (Edge Lab + realistic paper) →
S13 (Micro-Live) → S14 (Restructure)
```
Guiding principle reaffirmed: **Safety first. Evidence second. Autonomy last.**
Optimize for **evidence density, not feature count.**

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
- `whitelist`: +`historical_drift_count`, +`purification_ratio` ✅ (live in camel_sharia.db)
- `sharia_events`: +`trigger_period`, +`reasoning_summary` ✅
- `orders`: +`client_order_id` (UUID, idempotency) ✅
- `broker/paper.py`: `pre_flight_execution_check()` — raises `DuplicateOrderException`.

*Point-in-time timestamp columns (do this NOW, before data accumulates — retrofitting
historical rows is impossible):*
- Add to `prices`, and to all future macro/fundamentals/news tables, four distinct timestamps:
  - `event_date` — when the thing actually happened
  - `reported_at` — when the market/public learned it
  - `ingested_at` — when Camel collected it (exists today)
  - `known_at` — when Camel was *allowed* to use it
- This is the foundation of honest backtesting (S10). Without it, look-ahead bias is
  baked in and every backtest lies. Cheap now; impossible to add retroactively.

*Config immutability — prove the rules cannot be edited:*
- `governance/config_guard.py` — verifies at startup that the agent process has no write
  path to `config/limits.yaml`, the whitelist, tool-permission config, budget config, or
  approval thresholds. On Windows, enforced via file ACL check + a runtime write-attempt test.
- Test asserts: an agent-initiated write to any founder-owned config **raises and is logged**.
  This makes Constitution rule #7 ("Camel cannot change its own rules") a *proven* invariant,
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
Deferred by dependency: **max cancel/replace attempts** → S13 (no cancel/replace path exists
until LiveBroker); **earnings blackout** → S8 (needs an earnings calendar from the
fundamentals connectors). Corporate-action check was already pre-deferred to the S8/S12 data work.

---

### S4.5 — Edge Proof v0  (evidence gate, pulled forward)

*Rationale: the paper loop starts running in S5–S6, but the full Edge Proof Engine isn't
ready until S7. Without a v0 gate, Camel would make trade decisions on narrative alone for
two+ sprints — exactly the failure mode the project exists to prevent. v0 closes that window
using only the `market.db` price data we already have. No macro/fundamentals/news needed.*

`engine/edge_proof_v0.py` (moves to `trader/edge_proof_v0.py` in S12 restructure):
- `EdgeReport` dataclass
- Simple historical hit-rate + forward-return calculator from `camel_market.db`
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
- Every v0 decision logged to `camel_learning.db`

The full 13-check Edge Proof Engine (S7) is built *on top of* v0 — v0 is never removed,
it becomes the cheapest first filter.

**Gate:** No trade candidate proceeds without an EdgeReport; missing/weak/stale inputs all
return `trade_allowed=false`; `trade_allowed=false` blocks the allocator; tests cover allow,
reject, missing-sample, weak-benchmark, weak-evidence, stale-input. Adversarial case added:
strategy produces a signal without Edge Proof → blocked.

**STATUS: COMPLETE** (217 tests). `engine/edge_proof_v0.py` + `Allocator.request(...,
edge_report=, require_edge=)`; `require_edge=True` rejects a trade with no/weak/stale report
(`limit_hit="no_edge_proof"`) before the Constitution is consulted. Backward compatible:
existing S3 allocator calls (no edge_report) are unchanged. Logs to `camel_learning.db`.

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
- `operator/learning_ledger.py` — writes to `camel_learning.db`:
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

**STATUS: COMPLETE** (253 tests). Package is **`operator_os/`** — *not* `operator/` as the
§14.5 target names it, because `operator` is a Python stdlib module and would shadow it.
S12 restructure should use `operator_os/`. The GREEN/YELLOW/RED/BLACK status classifier and
daily-report text (an S5.5 item) landed early in `ops/health_monitor.py`.

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

**STATUS: COMPLETE** (263 tests). `ops/daily_report.py`, `ops/kill_switch_test.py`,
`ops/secrets_check.py`, `ops/backup.py`. The status classifier itself shipped early in S5
(`ops/health_monitor.py`). Remaining for S6: Telegram delivery, scheduled weekly kill-switch
test, secrets-manager hard refusal, off-box encrypted backup, dashboard, Tailscale.

---

### S6 — Dashboard + Monitoring + Kill Switch over Tailscale + Ops Hardening
*(Was original S4; minimal ops now live from S5.5 — S6 is the full build-out)*
- Dashboard reading live SQLite state (positions, P&L, ledger, guardrail events, Sharia flags).
- Daily Telegram health report — exact format (§11.8):
  ```
  Camel Daily Health Report
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
  BitLocker enabled · dedicated OS user for Camel · UPS/power backup · 5G/hotspot
  fallback internet · Tailscale ACLs locked to founder devices · MFA on all accounts.

**Gate:** Kill switch stops next loop tick; daily-loss-stop simulation halts; dashboard
reflects paper trade within one refresh; weekly kill-switch test passes; backup restore
verified; secrets not in plaintext.

**STATUS: COMPLETE (code, 289 tests).** `dashboard/` (read-only HTML), `alerts/` (Telegram,
credential-safe stub), `ops/`: heartbeat, log_rotation, secrets_manager (hard refusal),
reconciliation_report, archive (off-box zip), scheduled_checks (weekly kill-switch + backup +
reconcile). The **machine-setup half** — Tailscale kill-switch path, BitLocker, dedicated OS
user, UPS, 5G fallback, MFA, secrets migration to Credential Manager, encrypted off-box
transfer — is the founder checklist in `docs/CAMEL_MACHINE_HARDENING.md` (do before Phase 1).

---

## Roadmap v3 — research-driven restructure (adopted from Power Maximization Proposal v2 + data-source deep research)

**Why v3:** the system is strong on safety/governance/evidence-gating but the macro / fundamentals /
news databases are still *stubs*. A real Edge Proof Engine is meaningless without real, point-in-time,
provenanced data. So: **build the data supply chain before the proof engine, move the Entrepreneur
(cash-flow) arm earlier, and upgrade Edge Proof to signal-conditioned.** North star unchanged:
*excellent at rejecting weak ideas, proving rare strong ones, compounding capital, and building
cash-flow products.* Optimize for **evidence density, not feature count.**

**Revised sequence (S6 done):**
```
S6 OK -> S6.5 (Safety/Accounting hotfix) -> S7 (Entrepreneur, moved earlier)
-> S8 (Data Intelligence Backbone) -> S9 (Knowledge Graph + Regime Engine)
-> S10 (Full Edge Proof, 17-check) -> S11 (Strategy Registry) -> S12 (Edge Lab + realistic paper)
-> S13 (Micro-Live) -> S14 (Module Restructure)
```

---

### S6.5 — Safety & Accounting Hotfix  (small, do before the data work)
Cheap, real tightening surfaced by the stress-test:
- **No phantom sells** — block any sell whose qty exceeds current holdings.
- **Close-only / reduce-only exits for frozen or non-compliant holdings** — a frozen name may be
  SOLD to de-risk, never bought/increased.
- **Edge Proof mandatory for buy/increase by default** — `Allocator.request(..., require_edge=True)`
  is the default for opening/increasing; `reduce_only` / `close_only` actions are exempt.
- **Remove the $1 fallback price outside unit tests** — paper fills use a validated close; the
  `simulated_unrealistic` marker stays; **no performance number may come from a fallback fill.**

**Gate:** phantom sell blocked; frozen-name buy blocked but close-only allowed; buy without an
EdgeReport rejected; no $1 fallback in any non-test path.

---

### S7 — Entrepreneur Product Engine  (MOVED EARLIER — cash flow first)
*Moved ahead of the trading-data build (founder decision): for year one the Entrepreneur arm has
higher expected cash-flow + learning than trading a small account. Trader compounds; Entrepreneur
creates income.*

**Founder context:** the founder works full-time in a **travel-tech startup** — so the lead product
is a real domain fit.

- **Product Gate — 17 fields** before any code: problem statement · target customer · evidence of
  pain · competitor check · monetization hypothesis · MVP scope · build cost · launch risk ·
  Sharia/compliance check · data/privacy check · success metric · distribution channel · first 10
  target customers · willingness-to-pay evidence · compliance risk rating · data retention policy ·
  human-review requirement for generated outputs.
- **Lead product candidate:** Arabic complaint / SLA-response assistant for Saudi travel/hospitality
  operators (founder's domain). Alternatives: partnership-proposal generator (fintech/travel/
  e-commerce); Saudi loyalty-campaign planner; Sharia-compliant personal-investing research assistant.
- Build pipeline: product_thesis → PRD → build plan → GitHub issues → MVP → tests → staging →
  human approval → production → outcome measurement. No production deploy without tests + approval.
- **Entrepreneur Constitution** (separate from Trader): no legal/financial/medical claims without
  human approval; no sensitive-data collection without privacy review; no copyrighted assets without
  a rights check; no production launch without founder approval; no paid ads without Budget Kernel
  approval; no "official compliance guarantee" wording.
- Ship one compliant product (Stripe test mode for Phase 0).

**Gate:** no build without all 17 gate fields + Sharia check + approval; no paid spend without budget
approval; no customer data without privacy check; live URL; payment-capable.

---

### S8 — Data Intelligence Backbone  (the long pole — fills the stub DBs)
*The supply chain. The full Edge Proof Engine is impossible until macro/fundamentals/news hold real,
point-in-time, provenanced data.*

**`SourceConnector` base class** — every connector implements `fetch_raw / parse / normalize /
validate / store`, with `source_name, source_type, requires_api_key, allowed_use,
rate_limit_per_minute`. **Recorded-fixture tests (vcrpy / pytest-recording) — no live web in unit tests.**

**Provenance enforcement** — no decision-relevant record stored without: source · source_url/endpoint ·
source_document_id · event_date · reported_at · ingested_at · known_at · content_hash ·
parser_version · confidence · data_quality_score · license_status. New `source_documents` table.

**Top-20 source connectors (free/official first; paid phased in as budget allows):**

*Free / official (1–20):*
1. SEC EDGAR submissions API → fundamentals (10-K/10-Q/8-K metadata, filing history)
2. SEC XBRL CompanyFacts API → fundamentals (revenue, margins, debt, cash, shares)
3. SEC RSS feeds → news (filing alerts) + 8-K event triggers
4. FRED → macro (rates, inflation, credit spreads, money supply, yield curve)
5. **ALFRED (vintage)** → macro — *point-in-time* values, the key to honest macro backtests
6. BLS API → macro (CPI/PPI/unemployment/wages)
7. BEA API → macro (GDP/income/consumption/trade)
8. US Treasury Fiscal Data API → macro (yields/debt/fiscal)
9. World Bank Pink Sheet → macro (commodities: energy/metals/agriculture)
10. EIA → macro (oil/gas/inventories)
11. USGS minerals → macro (metals supply/demand)
12. GDELT → news (global events, tone, entities, themes, geography)
13. ACLED → news (political violence/protests/conflict)
14. Caldara & Iacoviello Geopolitical Risk Index → macro
15. Economic Policy Uncertainty Index → macro
16. OFAC + EU/UN sanctions lists → compliance exclusion + event detection
17. House financial disclosures → alt-data (signal only, never blind copy)
18. Senate financial disclosures → alt-data
19. ETF issuer holdings pages (SPUS/HLAL/MNZL) → sharia (constituents + methodology)
20. Kenneth French Data Library → factor data (momentum/value) for `quality_momentum`

*Paid (phased in, same references the research recommends):* **EODHD** (live-ish US quotes; 150k+
tickers; raw + adjusted history; **delisted dataset for survivorship control**; corporate actions;
~$20–100/mo) · **Polygon/Massive** (clean prices + corporate actions) · **Norgate** (survivorship-
resistant US/AU + delisted) · **Nasdaq Data Link / Sharadar** (fundamentals) · **Quiver Quantitative**
(congress/insider/lobbying/contracts/patents) · **Zoya / Musaffa** (Sharia API) · **CRSP** (research-
grade, 1926, survivor-bias-free — the aspirational historical-truth layer).

**Connector deps:** `requests`/`httpx`, `pydantic`, `feedparser`, `beautifulsoup4`/`trafilatura`,
`python-dateutil`, `vcrpy`/`pytest-recording`. (Heavy quant libs deferred to S12.)

**Scraping policy (`security/scraping_policy.py`):** API > vendor API > official file > RSS > static
scrape > browser (QA only). Check robots.txt + terms; respect rate limits; clear User-Agent with
contact email for SEC; store URL/time/hash/parser version; never execute scripts from pages; **never
let scraped text instruct the LLM.**

**Critical rules:** raw text → sanitiser → structured event → source quorum (≥2) → LLM summary (no raw
article text reaches the reasoning engine). **No backtest is valid unless adjusted/unadjusted prices,
splits, dividends, delistings, and ticker changes are handled.**

**Dashboard extension (data-pipeline health):** connector status · last successful ingestion ·
failed-source count · stale-source warnings · data-quality panel.

**Gate:** no ingested record without full provenance + point-in-time fields; ≥16 free connectors live
with recorded-fixture tests; macro/fundamentals/news DBs hold real data; raw text never reaches the LLM.

---

### S9 — Research Knowledge Graph + Regime Engine
*Turn raw data into linked, queryable intelligence, and classify the environment before choosing strategy.*

- **Entity resolution / `assets` table** — ticker ↔ CIK ↔ ISIN ↔ CUSIP ↔ company name ↔ sector ↔
  ETF holding ↔ Sharia screen; `active_from/active_to`, `delisted_flag`. Resolver maps a ticker to
  its full identity.
- **ETF holdings resolver** — SPUS/HLAL/MNZL constituents (look-through to single-name exposure).
- **Event intelligence** — structured events (`event_type`, region, affected_assets/sectors, severity,
  direction, confidence, source_count, point-in-time stamps) + dedup + severity scorer + entity linker
  + event→theme mapper.
- **Regime Engine** (`trader/regime/`: `regime_classifier_v0`, `regime_feature_builder`,
  `regime_history_store`). Regimes: LIQUIDITY_EXPANSION, LIQUIDITY_TIGHTENING, INFLATION_SHOCK,
  DISINFLATION_GROWTH, RECESSION_RISK, RECOVERY, COMMODITY_SUPPLY_SHOCK, GEOPOLITICAL_RISK_OFF,
  AI_CAPEX_BOOM, USD_STRENGTH_EM_PRESSURE. Features: fed_funds, 2y/10y yields, curve, real yield,
  CPI/core/PPI YoY, unemployment, payrolls, HY credit spread, DXY, oil/copper/gold, commodity index,
  VIX, SPUS/Nasdaq trend.
- **Regime → Theme mapper** — regime/event → sectors/assets/companies.
- **Sharia cross-check + multi-state status** — independent SEC/XBRL ratio sanity-check vs the
  canonical screener (Musaffa/Zoya). Status = `pass / fail / doubtful / frozen / pending_review` +
  methodology (AAOIFI/MSCI/S&P/FTSE/DowJones/custom) + confidence + business/financial screen results
  + purification_ratio + screened_at/known_at/next_review_at + source_hash. **Rule: canonical vs
  cross-check disagree → freeze for new buys, allow reduce-only exits, route to human review.**

**Gate:** given a ticker, Camel returns company identity, CIK, sector, Sharia status (multi-state),
latest filings, latest events, ETF exposure, and benchmark; the regime classifier labels the current
environment from real macro data; a Sharia disagreement freezes new buys.

---

### S10 — Full Edge Proof Engine  (signal-conditioned, 17 checks)
*Was S7. Upgraded to test THE SIGNAL on real data, not just general forward returns. Built on top of the
S4.5 v0 gate — v0 is never removed, it's the cheapest first filter.*

**17 checks:** 1 signal definition · 2 source provenance · 3 point-in-time availability · 4 historical
sample construction · 5 survivorship-bias control · 6 similar-regime filter · 7 forward returns at
1M/3M/6M/12M · 8 benchmark comparison (SPUS/HLAL/cash/DCA) · 9 transaction-cost + spread adjustment ·
10 worst-case drawdown · 11 volatility-adjusted return · 12 **multiple-testing penalty** ·
13 **signal-decay test** · 14 counter-signal inventory · 15 Sharia status at the historical decision
date · 16 liquidity + whole-share feasibility · 17 final trade decision.

**Model-disagreement rule** — BOARDROOM (Bull/Bear/Sharia Auditor) conflict → `trade_allowed=false` →
Human Approval Gate.

Edge report (extends v0): signal_id, candidate, sample_size, **regime_filtered_sample_size**,
hit_rate_3m, median_excess_return_3m, worst_forward_return_3m, max_drawdown, benchmark, after_costs,
turnover_estimate, data_quality_score, **multiple_testing_penalty_applied**, **signal_decay_detected**,
trade_allowed, reason. New `edge_reports` table. Observe structure: Regime → Theme → Asset → Sector →
Company → Candidate.

**Minimum thresholds:** sample ≥ 50 · regime-filtered sample ≥ 20 · median excess ≥ +2.5% over
benchmark for the horizon · worst forward return no worse than −25% unless position ≤ 2% · data
quality ≥ 0.80 · source quorum ≥ 2 for non-price events · fail if last-24-month edge materially
underperforms the full sample (decay).

**Decision-quality dashboard (extends the S6 state dashboard — shows *why*, not just *what*):**
current regime + confidence (from S9) · active strategy + weight · **signals rejected this cycle and
the exact reason** (failed check #, threshold missed) · are we beating SPUS / DCA / cash · **is the
edge decaying** (rolling 24-month vs full-sample) · data freshness + source-quorum status. Panels
come online as their inputs do: regime at S9, rejected-signals + edge-decay here at S10,
beating-benchmark at S12. This is the more valuable operator view — it surfaces the rejections that
are the whole point of the system.

**Gate:** every signal passes all 17 checks; regime-filtered sample enforced; multiple-testing penalty
+ signal decay applied; `trade_allowed=false` blocks the allocator; no edge proof = no trade; the
decision-quality dashboard renders the current regime, the active strategy, and at least one
rejected-signal-with-reason.

---

### S11 — Strategy Registry + Learning Engine
*Was S8. Starter trio updated (now feasible because the data backbone exists).*

**Starter trio (build first):** `core_dca` (monthly DCA into approved core ETF/basket; benchmark SPUS;
no timing unless regime risk is extreme — likely beats most overactive systems after costs) ·
`quality_momentum` (factor-driven, low turnover: 12-1 momentum, 6m momentum, positive earnings
revisions, revenue growth, FCF margin, low leverage, liquidity, valuation-not-extreme) ·
`etf_regime_rotation` (SPUS/HLAL/MNZL/cash by regime — **only if it beats simple DCA after costs**).

Then `earnings_guidance_drift` (after the earnings calendar + fundamentals are clean).
**Delay (revisit after Edge Lab):** `congress_signal`, complex `mean_reversion`, intraday active
management beyond monitoring, single-name `dca_ladder`, ML / LLM strategy discovery.
**Reject permanently:** day trading, options/Wheel, crypto derivatives, shorting, leverage,
weapons/defense themes, blind congress/social copy.

`BaseStrategy` (name, description, signal, entry/exit/sizing, applicable_regimes, base_rate); **all
signals still pass the 17-check Edge Proof.** `StrategyMixer` (blend by regime/weight/performance).
**DCA-ladder safety guardrails:** no DCA into frozen/deteriorating/litigated names; final stop
condition (no infinite averaging down); inside position + sector caps. **Intraday Position Monitor**
(5-min; manages open positions only; every action through `Constitution.evaluate()`; trailing-stop
50%-profit early-close).

**4-tier Learning Engine:** L1 auto base-rate updates · L2 auto weight within founder-set ±band ·
L3 propose-only (founder approves activate/deactivate + regime affinity) · L4 founder-only
(Constitution / new strategies / the band itself). Regime→strategy affinity learned at N≥20 per regime.

**Gate:** ≥3 strategies (the trio) all passing Edge Proof; learning updating base-rates; improvement
proposals land in the Learning Ledger; DCA guardrails enforced; never auto-edits the Constitution.

---

### S12 — Edge Lab (Backtesting) + Realistic Paper Execution
*Was S10. Adds the realistic-paper engine + survivorship + two-engine cross-check. Mandatory before any
live automation. Run after ≥28 days of paper data.*

**Realistic paper execution (two modes):** `loop_test` (last-close fills; $1 fallback only in unit
tests) vs `realistic_paper` (no fallback; limit orders only; spread model; slippage model; non-fill +
partial-fill logic; market hours; corporate-action awareness). Modules: `execution_simulator`,
`fill_model`, `slippage_model`, `order_book_snapshot`, `partial_fill`. **No performance report may use
loop_test fills.**

**Honest backtesting:** look-ahead / survivorship / data-leakage / overfitting prevention; walk-forward
(out-of-sample); transaction-cost + slippage + spread; whole-share constraints (Sahm); point-in-time
Sharia status; **delisted-company handling (EODHD delisted dataset; CRSP later)**; crisis tests
(2000 dot-com, 2008 GFC, 2020 COVID, 2022 rate shock).

**Benchmark hierarchy:** Cash · monthly DCA into SPUS · SPUS B&H · HLAL B&H · MNZL · equal-weight
Sharia basket · Camel active. If Camel doesn't beat simple DCA on risk-adjusted terms after costs, it
does not trade actively.

**Strategy kill criteria** (disable / research-only if ANY): out-of-sample < benchmark · drawdown >
threshold · hit rate below base rate · depends on one outlier · costs erase edge · works only in one
cherry-picked regime · sample too small.

**Two-engine cross-check** — a vectorized engine (vectorbt-style) AND an event-driven engine
(custom / Zipline/LEAN-style); compare results — never trust one engine. Heavy quant libs land here:
pandas, numpy, scipy, statsmodels, scikit-learn, vectorbt, quantstats.

**Gate:** every strategy tested out-of-sample on two engines; delisted handled; full benchmark
hierarchy compared; weak signals killed; all performance from realistic_paper fills; Camel beats
simple DCA before any live execution; backtest using future/restated data blocked by `known_at`.

---

### S13 — Micro-Live Readiness (Phase 1)
*(Was S11; prerequisites + deliverables unchanged.)*

**Prerequisites (all must pass):** ≥28 days continuous paper operation · 0 guardrail breaches · ledger
reconciles with the broker paper statement · every position had thesis + invalidation · kill switch
tested over Tailscale · broker key trade-only/withdrawals-disabled · margin + options disabled · key
scoped to minimum permissions · Edge Proof has approved ≥1 signal · approval flow tested · manual
dry-run · one **rejected** trade test live (no order placed) · one **approved** micro trade done
manually before automation · emergency broker login tested.

**Deliverables:** Approval Channel (Telegram one-tap approve/veto, timeout = veto) · LiveBroker
(Alpaca paper → live, behind the phase flag) · limit orders only · no pre-market/after-hours · live
key-scope verification at startup.

**Initial live permissions:** human approval on every live trade · no autonomous execution · max
$100–500 · limit orders only · whitelist only · no pre-market/after-hours.

---

### S14 — Module Restructure (last sprint)
Restructure the flat layout into a clean domain hierarchy (all tests stay green). Target tree extends
the original §14.5 plan with the v3 additions:

```
governance/  constitution, sharia_registry, risk_rules, budget_kernel, tool_permissions, approvals, config_guard
operator_os/ state_machine, task_queue, opportunity_router, learning_ledger, op_log, health_monitor, kill_switch
trader/      thesis_card, edge_proof_engine, regime/, event_study, forward_returns, portfolio_engine
broker/      paper_broker, live_broker, execution_simulator, fill_model, slippage_model, partial_fill, reconciliation
entrepreneur/ product_thesis, prd_generator, build_workflow, compliance_gate, qa_checklist
data/        market, macro, fundamentals, news, freshness, quality, sanitiser,
             connectors/ (sec, macro, events, market_data), provenance, entity_resolver
security/    prompt_injection_filter, secrets, source_validation, scraping_policy, source_allowlist
alerts/      telegram, daily_report
dashboard/   generate
```

**Gate:** full test suite green after restructure; all imports updated; CLAUDE.md updated.

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
