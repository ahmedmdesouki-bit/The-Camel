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
S6.5 ✅ (Safety/Accounting hotfix) → S6.6 ✅ (Position accounting + Ops hardening + Beginner Mode) → S7 ✅ (Entrepreneur engine) →
S8 (Data Backbone ~core) → S8.5 (Real-Time Data Tier) → S9 ✅ (Knowledge Graph + Regime + Sharia cross-check) →
S10 ✅ (Full Edge Proof, 17-check; shadow/enforcing) → ⭐ S10.5 ✅ (Operator-Loop Assembly + Runtime — Workstream A/B) →
S11 ✅ (Strategy Registry + Portfolio Engine + Learning) →
S12 ✅ (Edge Lab + realistic paper + ⭐ Sandbox Mode + No-Edge protocol) → S12.5 ✅ (Research Desk — framework built, DORMANT) →
S13 ◑ (Micro-Live — readiness infra built, go-live FOUNDER-GATED) → S14 ✅ (architecture documented + physical reorg DONE — Trader Camel under `trader/`) →
S16 ✅ (Operational Activation — CODE-COMPLETE: A1 durable Act + A2 Measure→Learn + A7 governed exits + A3 Alpaca feed + A4 Sharia universe + A5 evidence-gated promotion + Edge Lab harness + scheduler; 671 tests; the full wave-catching pipeline wired end-to-end) →
S15 ◑ (Paid tools & founder actions to cross "above the line"; all paid or founder-gated — now the ONLY remaining work)
```

> **Post-S14 hardening push (2026-06-08):** all *free, non-founder* deferred work is now done — pre-live
> hardening P1/P2/P3 (broker write-atomicity, Edge-Proof `as_of`, production Edge-gated tick, vintage/known_at
> discipline, full screener, doubtful persistence, shadow-phase guard, manual-fill guard), **S8 completed**
> (free Stooq price connector + ingestion orchestrator + SEC-RSS 8-K connector + earnings-blackout rule), and
> **S12/S13 code** (per-portfolio book threading + inbound approve/veto channel + manual-entry parser).
> **613 tests green.** ⚠️ **Correction (2026-06-09 verified audit):** "S15 only" was too optimistic. It holds for
> *code-built-and-tested*, but an adversarial 6-dimension audit (independent agents, verified against source +
> the live DBs) found the **operator does not yet run end-to-end on real data**: **Measure→Learn is wired
> nowhere** and the production tick (`loop/jobs.run_trading_tick`) **doesn't fill or persist a `runs` row**, so
> the ≥28-run track record S13 needs literally cannot be produced yet. The honest distances are: software
> built+tested **~78%**, operationally-wired-and-proven **~12%**, autonomy *earned* **0%**. No core *safety*
> claim was overstated (every guardrail is a tested hard wall) — the drift is all in *progress* claims. The
> **free CODE to close this is now `### S16 — Operational Activation` (below)**; only after S16 lands do the
> S15 paid/founder go-live steps apply. See `docs/CAMEL_S15_PAID_AND_FOUNDER.md` for the paid/founder catalogue.
*(⭐ **Sandbox Mode** = the full system on live real-time data with virtual money — the founder-requested
live dress rehearsal that produces the track record gating micro-live.)*

> **Founder direction (2026-06-06) — four additions folded in:** (1) **multi-portfolio + strategy-per-portfolio**
> → Portfolio Engine in S11; (2) **real-time / streaming data tier** → new S8.5 (ingestion + monitoring;
> execution stays EOD); (3) **dedicated per-vertical research agents** → new S12.5 Research Desk, *designed now
> but dormant until capital/edge justify the spend*; (4) **dividends** → a dividends connector (S8 backlog) +
> a `dividend_growth` strategy (S11). Plus: *many independent sources per data category, cross-checked* — an
> explicit S8 goal. A cited data-resource research pass is the agreed next task after this fold.
> **Cross-build harvest — Alaa's Camel (2026-06-06), founder-facing layer folded in** (full review:
> `docs/CAMEL_ALAA_REVIEW.md`). A friend's parallel Camel built the *cockpit + coach* to our *engine + rails*.
> Independent validation of the framing; net gift is a mature founder-facing surface we'd deprioritized.
> **BUILT (2026-06-07): (e) Dashboard v2 · (f) WhatsApp/CallMeBot + founder brief · (a) RED ALERT panic
> protocol · SAR/USD peg monitor · cash-drag ratio.** Remaining items stay scheduled below. Folded:
> (a) **founder-panic "RED ALERT" protocol** (breathe→assess→act; human-factors guardrail) → Constitution
> human-factors + S13 approval gate + daily-brief auto-fire on drop >3%; (b) **screenshot-OCR manual entry**
> (paste a Sahm screenshot → prices/positions; still writes the append-only ledger + must reconcile) → S13
> ManualBroker + broker matrix; (c) **strategy-fit selector + fit-metadata** (risk/horizon/research/capital/
> priority scores; sharia flag+note) → S11 Strategy Registry; (d) **strategy "mix" coherence UX** (explain
> *why* a pick is off-strategy) → S11 strategy-portfolio matrix rendering; (e) **interactive dashboard** (his
> single-file HTML as the visual starting point) → S10 decision-quality dashboard + S11 portfolio views,
> re-wired to our real DBs and to surface *rejections-with-reasons*; (f) **daily brief + WhatsApp/CallMeBot**
> 2nd alert channel (always show Live-Money-Gate X/10) → S6 alerts; (g) **LLM-output eval harness** → S12.5
> agents + the coach skill; (h) a **founder-tools `camel-coach` skill** (read-only Q&A over our governed
> state; proposes, never executes) → new founder-tools workstream. Harvested frameworks: **cash-drag ratio**
> (S11), **yield-on-cost** (S11 dividend_growth), **moat matrix** (Edge-Proof #14 / fundamentals agent),
> **sector-concentration cap ≤40% incl. ETF look-through** (S11 risk budgets), **SAR/USD-peg monitor** (S9
> macro). **Declined:** his looser "debt÷assets <33%" Sharia screen (keep full AAOIFI), hardcoded analysis
> data, no-enforcement posture, localStorage persistence, Yahoo/stooq as a decision-grade source.

Guiding principle reaffirmed: **Safety first. Evidence second. Autonomy last.**
Optimize for **evidence density, not feature count.**

---

## Workstreams & Backlog (sanity check — 2026-06-07)

> A full project sweep (code + all docs) confirmed **the sprint plan hasn't silently dropped anything major** —
> but it surfaced one structural gap, plus parallel workstreams and backlog items that need an explicit home so
> they aren't lost between sprints. Everything below is now tracked here.

### ⭐ WORKSTREAM A — Operator-loop assembly / integration — ◑ DECISION-HALF CLOSED (S10.5+S11.5); LEARNING-HALF + DURABLE ACT RE-OPENED → S16
**DECISION-HALF RESOLVED.** A1–A4 are done: the §4 loop is assembled in `loop/assembled.py` (every action routes through
`Allocator.request()` → Edge Proof + Constitution; the invariant test proves a no-edge buy is rejected by the
*assembled* loop — Phase-1 blocker closed), A2/A3 driven by the loop, A4 peg wired in S9 slice 4.
> ⚠️ **Re-opened by the 2026-06-09 audit (→ S16):** the *decision half* of the loop (Observe→Router→Edge→
> Constitution→Budget→Approval→Act-decision) is genuinely assembled and tested. But **(1) the Act has no durable
> effect in the production tick** — `loop/jobs.run_trading_tick` injects no broker, so Act is a `'simulated_fill'`
> string (no ledger/positions write, no `runs` row; only `trader/sandbox/runner.py` wires a real executor); and
> **(2) Measure→Learn is wired NOWHERE** — the whole `learning/` package is imported only by its own tests. So the
> full North Star loop (…→Act→Measure→Learn→Learning Ledger) is **not** strung together at runtime. Closing both
> is **S16 — Operational Activation**.

**The S11.5 keystone `loop/driver.py` then connected S9–S11 end-to-end:** registry → context → mixer → the **full** 17-check
Edge Proof → assembled loop (proven by `tests/test_integration.py`). The original finding is kept below for the
record.
*(Original finding:)* the Camel was *a complete set of well-tested components with the integration layer largely
unbuilt*. Each station — Opportunity Router, Edge-Proof gate (`capital/allocator.py`), Budget Kernel,
Operator-OS state machine, Regime engine, Constitution, Approval gate — is built and unit-tested, but
`loop/scheduler.py` assembles a `LoopConfig` with **no-op observe/choose/execute/measure/learn callbacks**, so
the upgraded §4 loop (Observe→Router→Edge/Product-Proof→Constitution→Budget→Approval→Act→Learn) is **never
strung together at runtime**. Consequences to close before any live trading:
- **A1 — Wire the Edge-Proof gate into the loop.** `loop/runner.py` currently calls `Constitution.evaluate`
  *directly*, bypassing `Allocator.request()` (where "no buy without a passing EdgeReport" actually lives).
  Harmless today only because nothing trades (no-op callbacks) — **but a Phase-1 BLOCKER.** The CLAUDE.md rail
  "no trade without an EdgeReport" must hold in the *assembled* loop, not just in the Allocator unit.
- **A2 — Drive the Operator-OS state machine + Opportunity Router from the loop** (built in S5, uncalled).
- **A3 — Consume the Regime engine in a decision** (today it feeds only `regime_history` + the dashboard).
- **A4 — Wire `trader/regime/peg.py` into `features.py`** (peg monitor built, not yet read). *(→ S9 slice 4.)*
- **Home (founder-agreed 2026-06-07): a dedicated sprint — `S10.5 — Operator-Loop Assembly` — at the S10→S11
  boundary** (see its body below), rather than letting the wiring ride implicitly inside other sprints. A1 is
  also a hard gate in the **S13 live-readiness** checklist and `CAMEL_LIVE_READINESS.md`. Tracked, not dropped.

### WORKSTREAM B — Scheduled entrypoints / ops automation — ✅ CLOSED (S10.5)
**RESOLVED.** `loop/jobs.py` provides the entrypoints (`python -m loop.jobs daily|weekly`): `run_daily_ops`
(heartbeat + dashboard render + founder brief) and `run_weekly_safety` (kill-switch self-test + backup +
reconcile). *(The connector-ingestion entrypoint remains under Workstream D; founder still wires these into
Windows Task Scheduler per the S6 machine-setup checklist.)*

### WORKSTREAM C — Founder tools (parallel, read-only, outside the trust boundary)
- **Dashboard v2** ✅ done (`dashboard/snapshot.py` + `generate.py`).
- **`camel-coach` skill** (harvested from Alaa) — a read-only conversational Q&A over our *real* governed state
  (positions, edge decisions, regime, gate). Proposes, never executes. **Not yet built**; design alongside the
  S12.5 Research Desk (shares the evidence-object + eval-harness ideas) but ships independently.

### WORKSTREAM D — Connector ingestion orchestration & data backlog
- **Ingestion orchestrator:** the 10 S8 connectors only `.run()` in tests — no scheduled production ingestion,
  so `regime/features.py` would read empty tables at runtime. Add an ingestion job (part of Workstream B). *(S8 cont.)*
- **Parked S8 connectors** (founder-deferred): OFAC, USGS, congress/senate disclosures, Kenneth-French factors,
  SEC-RSS/8-K, GPR/EPU, market-data adapter, dividends/corporate-actions, paid vendors. *(S8 continuation.)*
- **New free connectors (2026-06-07 data research, prioritized — see `CAMEL_DATA_SOURCES.md`):** **SEC RSS** (8-K
  events) · **Finnhub** (EPS/revenue surprise + free websocket) · **CFTC COT** (positioning API) · **Kenneth
  French** factor library · **CBOE / FRED stress** (VIX, NFCI, STLFSI) · **IMF PortWatch** (chokepoint shipping —
  high value for a Gulf book) · **GPR + EPU** indices · **OFAC + UK Sanctions List** (⚠️ OFSI list closed 28-Jan-
  2026 → use UKSL) · **Marketaux** (entity-tagged news, tags Tadawul+EGX) · **OpenSanctions** · **SAHMK** (free
  Tadawul-licensed Saudi). *Ingest a lean decision-critical core + one quorum cross-check per category — NOT all
  of them (founder directive: "don't exhaust the system"). The full tiered plan (T0 core / T1 quorum / T2 paid /
  T3 reference) lives in `CAMEL_DATA_SOURCES.md`.*
- **USD/SAR FX feed → ✅ DONE (S9 slice 4):** `features.py` reads **FRED `DEXSAUS`** → `peg_deviation_pct`; the
  classifier raises `GEOPOLITICAL_RISK_OFF` on peg stress. Free (the FRED connector already existed).
- **Connector base hardening → ✅ DONE (backlog sweep 2026-06-07):** `with_retries()` in `data/connectors/base.py`
  wraps any transport with bounded retry + exponential backoff on *transient* failures only (429/5xx/URLError);
  permanent errors (403/404) fail fast. Injectable `sleeper` → zero real wait in tests. Descriptive, contact-bearing
  default User-Agent (fixes the SEC 403 / GDELT 429 generic-agent blocks). `default_transport` is now retry-wrapped.

### BACKLOG — smaller items with a home
- **Per-portfolio positions/ledger (A2): PARTIAL.** `portfolios/holdings.py` (S11.5) gives a per-portfolio
  weighted-avg holdings view + `reconcile_to_fund` (the S11 acceptance criterion at a basic level). The fund-level
  `positions`/`ledger` remain the book of record; folding `portfolio_id` through them so every fill writes both
  books in one transaction is the **remaining S12 item** (pairs with broker write-atomicity below).
- **System-integration polish (S11.5 done; remainder):** `loop/driver.py` connects registry→full-Edge-Proof→loop;
  remaining = drive it from a scheduled entrypoint (Workstream B) + per-portfolio context (pass `portfolio_id`).
- **Alaa harvested items:** screenshot-OCR manual entry → S13; strategy-fit *selector* + "mix" coherence UX → S11
  backlog (the *registry/matrix* shipped; the founder-facing selector UI did not — still open); **yield-on-cost +
  moat matrix → ✅ DONE (backlog sweep 2026-06-07)** in `strategies/analytics.py` (`yield_on_cost`, `moat_score` →
  none/narrow/wide; pure, evidence-only); sector-cap ≤40% → landed in `portfolios/check_risk_budget` (S11).
- **Health-monitor checks → ✅ DONE (backlog sweep 2026-06-07):** `cpu/memory` via psutil *if present* (honest
  `n/a` otherwise — never a hard dep); `broker/telegram/secrets` are now **credential-presence** checks (env-based,
  value never echoed; absent is fine in paper → never degrades status). No more `"skipped"` placeholders.
- **`data/quality.py`** "refine" was mis-tagged to S7 — refinement belongs with the data backbone (S8 cont.). *(open)*
- **Migrate `sharia/screener.py` → `sharia/aaoifi.py` → ✅ DONE (backlog sweep 2026-06-07):** the legacy quarterly
  job now **delegates** to the verified AAOIFI screen. The looser 33% model is gone — one screen, ≤30%/≤30%/≤67%/≤5%
  + 11 sectors, doubtful = passed-with-a-note (not auto-frozen). `test_sharia.py` boundary tests updated to 30%.
- **Broker write-atomicity** (positions↔ledger transaction) → **S12** (already owned). **Earnings blackout** →
  **S8** (needs earnings calendar). **Max cancel/replace order handling** → **S13** (LiveBroker). **IBKR** → Phase 2.
- ⭐ **Cross-tick transaction atomicity (data-layer review 2026-06-11) → pre-Phase-1.** The broker fill is
  atomic (orders + ledger + positions in one txn), but a full governed tick spans MULTIPLE transactions
  (begin-run → exits → act → measure→learn → finish-run), so a mid-tick crash can leave a run half-graded or
  learning partially applied. Phase 0 tolerates it — the fill (the only money-moving write) is atomic and
  `finish_run` grades fail-safe — but before Phase 1, wrap the consequential legs of a tick into a single unit
  (or a saga + compensation) so a crash can't leave the books and the run record inconsistent.
- ⭐ **Postgres / Supabase migration (data-layer review 2026-06-11) → Phase 1.** The SQLite per-domain DDL is
  now the single source of truth and `python -m db.dump_schema` emits the authoritative live schema;
  `db/schema.sql` holds the regenerate-process + the RLS/permissions "second wall" design. Remaining = the
  actual translation (SQLite types → Postgres, JSON → jsonb, INTEGER flags → boolean; keep every UNIQUE + the
  point-in-time columns) and enforcing the RLS grants — done when multi-device / remote-dashboard / real
  capital justifies the operational cost.

*(Doc-drift items found in the same sweep — phantom repo-map modules, stale test counts/sprint statuses, the
AAOIFI threshold mismatch, and stale cross-references — were corrected in place; see the 2026-06-07 changelog entry.)*

---

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

The full 17-check Edge Proof Engine (S10) is built *on top of* v0 — v0 is never removed,
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
reconcile). **Dashboard v2 (post-Alaa review, 2026-06-06):** rebuilt as `dashboard/snapshot.py`
(pure JSON snapshot from the 7 DBs) + `dashboard/generate.py` (rich tabbed, CSS-only, fully
offline/read-only HTML — Overview · Portfolio · **Decisions** · Regime · Sharia · Ops). It now
surfaces the things a portfolio tracker can't: **Edge-Proof verdicts and Constitution
rejections-with-reasons**, the macro regime, and an honest live-money safety posture — the early
delivery of the S10 *decision-quality dashboard* on Alaa's visual ground. The **machine-setup
half** — Tailscale kill-switch path, BitLocker, dedicated OS
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

**STATUS: COMPLETE (289 → 309 tests).** Phantom-sell + oversell guard and close-only/reduce-only
exits for frozen/non-compliant holdings in `guardrail/constitution.py`; `Allocator.request` now
defaults `require_edge` to True for buy/increase and False for sell/non-trade
(`capital/allocator.py`); `PaperBroker(allow_fallback_price=False)` is the default and raises
`NoMarketPriceError` rather than fabricating a $1 fill, with fallback fills stamped
`fill_model="fallback_dollar"`. New gate suite `tests/test_s6_5_safety.py`. *(Note: a precise
share-level phantom check at the broker arrives with realistic execution in S12; S6.5 uses the
deterministic value-based guard in the Constitution, which covers both the allocator and the
direct-`evaluate` loop path.)*

---

### S6.6 — Position Accounting + Ops & Safety Hardening + Beginner Mode  (review rounds #5–6)
Correctness + cheap hardening surfaced by three independent technical reviews. The lead item (position
accounting) is foundational; the rest each close a verified gap.
- **⭐ Position accounting on every fill (review #6 — the foundational one).** Today the PaperBroker
  writes orders + ledger but **never maintains a positions table** — so the S6.5 phantom-sell/oversell
  guards are only *value-based* and paper P&L can't be trusted or reconciled. Add a real `positions`
  table (symbol · qty · avg_cost · market_price · market_value · realized_pnl · opened_at · updated_at ·
  status) updated on every paper fill: BUY creates/increases + weighted-average cost; SELL validates
  `qty ≤ held`, reduces, realizes P&L, closes at zero. The broker gains an **exact qty-based phantom
  guard** (`sell_qty ≤ held_qty`), making the Constitution's value-based guard precise. Positions must
  reconcile with ledger cash.
- **Health-monitor test portability (review #6 — verified bug).** `test_yellow_when_low_disk` is
  environment-sensitive (it asserts YELLOW by demanding 10 PB free; a filesystem reporting huge capacity
  returns GREEN and the test fails). Mock `shutil.disk_usage()`; and make an **unknown/errored disk check
  → YELLOW** (fail-safe), not GREEN.
- **Illiquidity-gate fail-loud** — the spread/ADV gate in `constitution.py` currently **skips silently
  when its data is absent**, so an illiquid trade can pass unchecked. Log every skip + raise a
  dashboard/alert flag; **fail-closed (block) in live mode** when the data needed to clear the gate is
  missing. *(Verified against the code — real gap.)*
- **Prompt-injection adversarial tests** — add to the red-team suite: agent claims "the founder told me
  to ignore the Constitution" → REJECT; "an emergency justifies breaking a rule" → REJECT; agent
  supplies fabricated data to justify a trade → REJECT after triangulation.
- **Dead-man's-switch** — an external heartbeat (e.g. healthchecks.io ping) the EOD loop must hit inside
  a window; a missed ping alerts the founder. Fixes the bootstrapping gap: the internal health monitor
  can't catch a failure if it isn't running (power cycle, forced Windows Update restart, sleep, logout).
- **SQLite WAL mode** — `PRAGMA journal_mode=WAL` on all 7 DBs to reduce locking under concurrent
  read/write; document crash-during-write behaviour and confirm reconciliation handles it.
- **OS-level config immutability** — move `config/limits.yaml` to an NTFS path the agent process user can
  only read; immutability enforced by the OS, not merely by code. (Founder machine-hardening checklist.)
- **Beginner Mode** (`config/beginner_mode.yaml`) — a founder-selectable profile for the real small
  account: small fixed position cap, fewer positions, tighter daily-loss stop, DCA-first, manual approval
  on. Sits on top of the existing fund-size cash tiers; **never relaxes a Sharia or capital-preservation
  rail** (it can only tighten).
- **Broker capability matrix** (`docs/CAMEL_BROKER_MATRIX.md`) — Alpaca / IBKR / Sahm / (later EGX):
  markets, API availability, Sharia screening, fractional shares, minimum capital, fees, PDT rule,
  automation. Resolves the live-broker direction.

**Gate:** positions update on every fill (weighted-avg cost on buy, realized P&L on sell, close at zero)
and reconcile with ledger cash; the broker's exact qty-based phantom guard blocks over-selling; the
disk-test is deterministic (mocked) and unknown disk → YELLOW; illiquidity-gate skip is logged and blocks
in live; the three prompt-injection tests pass; the dead-man's-switch alerts on a missed ping; all DBs run
WAL mode; the beginner-mode profile loads and can never widen a rail; broker matrix documented.

**STATUS: COMPLETE (309 → 331 tests).** `broker/positions.py` (single writer of the `positions` table:
weighted-avg cost, realized P&L, exact qty-based `InsufficientPositionError` guard, reconcile helper),
wired into `PaperBroker.submit`; extended `positions` schema; SQLite WAL in `db/sqlite.connection`;
illiquidity **fail-closed in live** (`illiquidity_data_missing`) in `constitution.py`; health-monitor
disk-test mocked + unknown→YELLOW; `ops/deadman.py` (network-safe external ping); `config/beginner_mode.yaml`
+ `governance/beginner_mode.py` (only-tightens, `RailWidenedError`); prompt-injection adversarial tests;
`docs/CAMEL_BROKER_MATRIX.md` + machine-hardening NTFS/dead-man items. New tests: `test_positions.py`,
`test_s6_6_hardening.py`, plus additions to guardrail/adversarial/health/broker suites.

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
- **Autonomous scope is code-generation only (reviewer-validated).** The agent may draft PRDs, write
  code, open issues, and prepare assets — but **customer discovery, pricing, payment setup, support,
  and any launch or spend decision require founder approval.** Both external reviews flagged this as the
  highest-risk, least-proven arm; keeping it at S7 (founder's call, for cash flow) is paired with this
  hard scope limit so "move it earlier" doesn't mean "let the agent launch a product."
- Ship one compliant product (Stripe test mode for Phase 0).

**Gate:** no build without all 17 gate fields + Sharia check + approval; no paid spend without budget
approval; no customer data without privacy check; live URL; payment-capable.

**STATUS: COMPLETE — engine (331 → 352 tests).** New `entrepreneur/` package, all deterministic:
`product_gate.py` (17-field `ProductThesis` + `evaluate_gate`; the travel/hospitality SLA assistant
encoded as `lead_product_thesis()` and proven through the gate); `constitution.py` (separate
`EntrepreneurConstitution.evaluate` — BUILD is code-gen-only; DATA_COLLECT needs a privacy review;
ASSET_USE needs a rights check; SPEND needs budget; LAUNCH needs founder approval; PUBLISH_COPY blocks
regulated claims without approval + banned compliance-guarantee wording; reuses the Trader haram screen);
`build_pipeline.py` (10-stage state machine — no skipping, STAGING needs passing tests, PRODUCTION needs
founder approval + a Constitution-allowed LAUNCH). Tests in `tests/test_entrepreneur.py`. *Scope note: this
is the **engine**; real Stripe/GitHub/customer-data/deploy integration is wired only when a real product
ships behind these gates (a founder real-world action, like live trading) — not in Phase 0.*

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

**News-pipeline adversarial tests (reviewer-validated)** — before any news ingestion goes live: malformed
structured events; instruction text injected into an event's narrative field; events crafted to trip a
specific Constitution rule via their data content. The structured-event design (never raw text to the
LLM) is the mitigation; these tests prove it.

**Market expansion order (founder decision): US → Saudi → EGX.** The US connectors above are the focus.
**Saudi (Tadawul)** market-data + Sharia-list adapters come next as a sub-track. **EGX (Egypt)** is a
*later* adapter (Mubasher / EGX official / a manual-entry broker), **not a P0** — adopted only once the
US/Saudi core is solid. *(An external reviewer pushed EGX-first; declined — it's the reviewer's home
market, not the founder's primary one. The founder trades US ETFs via Sahm from Riyadh.)*

**Dashboard extension (data-pipeline health):** connector status · last successful ingestion ·
failed-source count · stale-source warnings · data-quality panel.

**Gate:** no ingested record without full provenance + point-in-time fields; ≥16 free connectors live
with recorded-fixture tests; macro/fundamentals/news DBs hold real data; raw text never reaches the LLM.

**STATUS: IN PROGRESS — slices 1–5 (352 → 389 tests); 10 connectors live (FRED, SEC EDGAR, Treasury, World
Bank, BLS, GDELT, BEA, EIA, ACLED, ETF-holdings) — all three stub DBs hold real data.** Slice 4 added BEA +
EIA (macro) + ACLED (conflict→news). Slice 5 added the **ETF issuer-holdings** connector (CSV; header-tolerant;
SPUS/HLAL/MNZL constituents → `camel_sharia.db.etf_holdings` for single-name look-through; feeds S9).

**S8 CORE DELIVERED — remaining connectors DEFERRED (founder decision).** The framework is proven across
JSON + CSV, macro/fundamentals/news/sharia domains; 10 connectors give enough breadth for S9 to proceed.
**Parked backlog (revisit as an S8 continuation):** OFAC sanctions, USGS minerals, congress/senate
disclosures, Kenneth French factors, SEC RSS/8-K, GPR/EPU indices, a market-data adapter, a **dividends /
corporate-actions connector** (ex-div date, yield, payout ratio, growth streak — feeds `dividend_growth` in
S11), and the paid vendors (EODHD/Polygon/Norgate/Sharadar/Quiver/Zoya/CRSP); markets US → Saudi → EGX.
**Founder goal: many independent sources per category, cross-checked** (the source-quorum ≥2 rule already in
the design) — so historical prices, news, geopolitics, and market-reaction data each have multiple feeds,
no single point of failure or bias. **Feeds now chosen — see `docs/CAMEL_DATA_SOURCES.md` (verified, cited):**
- *Next free connectors:* **SEC RSS** (8-K/filing events), **GPR** geopolitical-risk index (CC-BY file), **OFAC**
  sanctions list.
- *Dividends / corporate-actions connector* → **EODHD** Splits/Dividends API (ex-div, yield, payout ratio,
  splits) — powers `dividend_growth` (S11).
- *Paid, phased:* **EODHD** fundamentals (2nd source, cross-check SEC) → **Sharadar/Nasdaq Data Link**
  (survivorship-free point-in-time, for the S12 Edge Lab) → **Benzinga** (structured news). RavenPack deferred
  (enterprise); yfinance/Stooq prototyping-only.
These are new-connector work on an established pattern, not blockers for S9–S12. Slice 3 added the
**news/events pipeline**: `data/connectors/news_base.py` (`NewsConnector` — every title sanitised; injection-
flagged titles **redacted + marked unsafe + quality-downgraded**, raw string never persisted; structured
events only, no raw-body column) + `data/connectors/gdelt.py`, with the reviewers' **news adversarial tests**. Framework + provenance + first 2 connectors:
`data/provenance.py` (point-in-time provenance fields + `source_documents` table + `assert_provenanced`);
`data/source_registry.py` (`SourceSpec` registry; FRED + SEC EDGAR registered); `data/connectors/base.py`
(`SourceConnector`: fetch→parse→normalize→validate→store with an **injectable transport** — stdlib `urllib`
in prod, stubbed in tests, so **no live web in tests, zero new deps**); `data/connectors/fred.py` → real
`macro_observations` (ALFRED vintage → `reported_at`); `data/connectors/sec_edgar.py` → real `company_facts`
(filing date vs period end); `security/scraping_policy.py` (API > … > browser-QA-only ladder). Idempotent
ingestion; records missing provenance are dropped. *Dependency-light call: deferred requests/httpx/pydantic/
feedparser/vcrpy until a connector genuinely needs them (e.g. feedparser for RSS).* **Remaining slices:**
the other ~18 free connectors (BLS/BEA/Treasury/World Bank/EIA/GDELT/ACLED/OFAC/disclosures/ETF/French),
GDELT/news pipeline + adversarial tests, market-data adapter, then paid vendors; markets US → Saudi → EGX.

---

### S8.5 — Real-Time Data Tier  (founder direction — streaming ingestion + monitoring)
*Adds a streaming/real-time path alongside the EOD connectors. Scope is **ingestion + monitoring**, NOT
real-time execution: positional execution stays EOD (Sahm / whole-share) until at least Phase 1.*
- **Streaming vendor (resolved — see `CAMEL_DATA_SOURCES.md`): Alpaca IEX websocket (primary) + Finnhub free
  websocket (cross-check, ≤50 symbols)** — both true real-time, both **free**, both fit a monitoring-only tier
  on a small whitelist (no new paid spend). IEX is single-exchange → monitoring-only, never decision-grade tape
  alone. A websocket/streaming adapter for live
  quotes/trades on whitelisted names → a separate `realtime_quotes` store, point-in-time stamped. It
  **never overwrites the official EOD bars** that backtests depend on.
- **Live news/event stream:** short-interval polling of the news connectors (GDELT / RSS) through the same
  sanitiser → structured-events path (no raw text to the LLM).
- **Real-time monitor + charts:** extends the S6 dashboard with a live, read-only view (positions, intraday
  P&L, current regime, rejected signals, data freshness); refreshes on the stream.
- **Alerting:** Telegram pushes on material moves / guardrail-relevant events.
- **Many sources, cross-checked:** a single live feed is **monitoring-only**; a real-time signal is not
  decision-grade until corroborated by source quorum ≥2.

**Honest note:** this is real infrastructure (streaming, reconnects, backpressure) and delivers **latency for
monitoring**, not a mandate to trade intraday. Real-time *execution* is a separate Phase-2+ decision. Build it
so unreviewed live ticks can never contaminate the EOD/backtest data set.

**Gate:** the live stream lands in a separate real-time store with point-in-time stamps; the EOD bar set is
untouched; the real-time monitor renders live; no real-time feed is decision-grade without quorum; execution
remains EOD.

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
- **⭐ Event-reaction engine (consultant-adopted)** — an `event_reactions` table recording how markets
  *historically* reacted to each event type: `event_type · event_date · known_at · affected_symbols/sectors/
  commodities · return_1d/5d/21d/63d/126d · max_drawdown_63d · benchmark_return · excess_return · regime_at_event`.
  Answers "when this kind of event happened before, what moved, how far, how long, and did compliant names
  capture it?" — the **point-in-time substrate for the S10 signal-conditioned event studies** (built honestly
  off `known_at`, never look-ahead).
- **Regime Engine** (`trader/regime/`: `regime_classifier_v0`, `regime_feature_builder`,
  `regime_history_store`). Regimes: LIQUIDITY_EXPANSION, LIQUIDITY_TIGHTENING, INFLATION_SHOCK,
  DISINFLATION_GROWTH, RECESSION_RISK, RECOVERY, COMMODITY_SUPPLY_SHOCK, GEOPOLITICAL_RISK_OFF,
  AI_CAPEX_BOOM, USD_STRENGTH_EM_PRESSURE. Features: fed_funds, 2y/10y yields, curve, real yield,
  CPI/core/PPI YoY, unemployment, payrolls, HY credit spread, DXY, oil/copper/gold, commodity index,
  VIX, SPUS/Nasdaq trend.
- **Regime → Theme mapper** — regime/event → sectors/assets/companies.
- **Sharia cross-check + multi-state status** — an **in-house AAOIFI screen computed from SEC/XBRL data**
  (free), cross-checked against a **canonical screener (Zoya — AAOIFI default; or Musaffa)**. Status =
  `pass / fail / doubtful / frozen / pending_review` + methodology (AAOIFI/MSCI/S&P/FTSE/DowJones/custom) +
  confidence + business/financial screen results + purification_ratio + screened_at/known_at/next_review_at +
  source_hash. **Rule: in-house vs cross-check disagree → freeze for new buys, allow reduce-only exits, route
  to human review.**
  - **AAOIFI ratio thresholds (verified, from the FTSE Russell / IdealRatings Islamic-index methodology —
    see `CAMEL_DATA_SOURCES.md`):** interest-bearing **debt** ÷ trailing-12-mo-avg market cap **≤ 30%** ·
    (cash + deposits + interest-bearing investments) ÷ 12-mo-avg market cap **≤ 30%** · (cash + deposits +
    receivables) ÷ total assets **≤ 67%** · non-compliant-activity revenue + non-operating interest income
    **≤ 5%** of total income · **11 prohibited sectors** (alcohol, gambling, pork, tobacco, conventional
    finance, conventional insurance, defense, adult, hotels, music, cinema/broadcasting). *Use AAOIFI's
    **12-month-average** market cap (Zoya uses plain market cap — a documented difference; Zoya is the
    cross-check, not the primary).*
- **AAOIFI drift detection (reviewer-validated)** — ratios re-screen quarterly; flag when a *held*
  position's debt/interest ratios have moved toward the doubtful zone *since purchase* — an early
  warning before an outright freeze.
- **Local-board override (configurable; AAOIFI default).** Some markets' local Sharia boards differ
  from AAOIFI (Saudi/Egypt especially). Authority stack: **local board > AAOIFI > founder judgment >
  agent (never)**. Default AAOIFI; per-market overrides land with the Saudi/EGX adapters. Recorded in
  the multi-state status's `methodology`/authority field.

**Gate:** given a ticker, Camel returns company identity, CIK, sector, Sharia status (multi-state),
latest filings, latest events, ETF exposure, and benchmark; the regime classifier labels the current
environment from real macro data; a Sharia disagreement freezes new buys.

**STATUS: ✅ COMPLETE — slices 1–4 done (→ 465 tests green).** *(419 QA → 426 Dashboard v2 → 440 Alaa alerts/peg
→ 449 event intelligence → **465 Sharia cross-check**.)*
- *Slice 1 (entity resolution):* `assets` table (ticker/CIK/ISIN/CUSIP/name/sector/active_from-to/
  delisted_flag) + `data/entity_resolver.py` `resolve(ticker)` → full identity joining `assets` +
  `company_facts` + `etf_holdings` look-through + Sharia whitelist.
- *Slice 2 (Regime Engine):* `trader/regime/` — `features.py` (point-in-time macro features from
  `macro_observations`: fed funds, 10y−2y curve, CPI YoY, unemployment, HY spread, VIX, USD, oil YoY),
  `classifier.py` (deterministic signal-scored 10-state classifier → regime + confidence + which signals
  fired; `regime_to_themes` mapper), `history.py` + `regime_history` table (append-only audit). v0 covers
  the macro-derivable regimes; AI_CAPEX_BOOM / confident RECOVERY need equity-sector signals (later).
**S9 slices:**
- *Slice 3 (event intelligence) — ✅ DONE (449 tests):* `trader/events/` — `intelligence.py` (deterministic
  **dedupe + reporting quorum**, dictionary **entity-linker** over sanitised titles, severity/direction/theme
  rule tables, confidence = data-quality × quorum factor; enriches `news_events.affected_assets/severity/
  direction/confidence`; **only `safe=1` rows — injection-flagged events are never linked or scored**) +
  `reactions.py` (the **`event_reactions`** substrate table: forward returns 1/5/21/63/126d, 63d max-drawdown,
  21d benchmark + excess vs SPUS, `regime_at_event`; a **hindsight study/base-rate table for S10 event studies,
  not a live signal**; pure math helpers unit-tested). *Free data recipe (FRED/ALFRED dates + Finnhub surprise +
  CFTC COT + Kenneth French factors) feeds it once those connectors land — see `CAMEL_DATA_SOURCES.md`.*
- *Slice 4 (Sharia cross-check) — ✅ DONE (465 tests):* `sharia/aaoifi.py` — the **verified in-house AAOIFI
  screen** (≤30% debt / ≤30% liquid-assets / ≤67% receivables / ≤5% haram-income, **12-mo-avg market-cap
  denominator**, 11 prohibited sectors; near-limit → *doubtful* band; missing-data → doubtful, never a silent
  pass; reports `purification_ratio`). `sharia/cross_check.py` — **multi-state status** (pass/fail/doubtful/
  frozen/pending_review) + the **disagreement→freeze rule**, **fail-safe quorum** (a single source can fail but
  not *clear* a name → no cross-check = `pending_review`), the **authority stack** (local board > AAOIFI >
  founder tighten-only > agent-never), **drift detection**, and a fail-safe writer (any error or non-clear
  outcome freezes for new buys; reduce-only exits stay open) persisting to the new `sharia_status` table.
  **Peg wired in:** `features.py` now reads **FRED `DEXSAUS`** → `peg_deviation_pct`, and the classifier raises
  a `GEOPOLITICAL_RISK_OFF` signal on peg stress — free activation, no new vendor. *(Legacy `sharia/screener.py`
  keeps its looser 33% boundary tests; migrating it to delegate to `aaoifi.py` is a small backlog item.)*

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

Edge report (extends v0): signal_id, **signal_definition_hash** (review #6 — recompute evidence if the
signal definition changes; prevents hidden strategy drift), candidate, sample_size,
**regime_filtered_sample_size**, hit_rate_3m, median_excess_return_3m, worst_forward_return_3m,
max_drawdown, benchmark, after_costs, turnover_estimate, data_quality_score,
**multiple_testing_penalty_applied**, **signal_decay_detected**, trade_allowed, reason. New
`edge_reports` table. Observe structure: Regime → Theme → Asset → Sector →
Company → Candidate.

**Minimum thresholds:** sample ≥ 50 · regime-filtered sample ≥ 20 · median excess ≥ +2.5% over
benchmark for the horizon · worst forward return no worse than −25% unless position ≤ 2% · data
quality ≥ 0.80 · source quorum ≥ 2 for non-price events · fail if last-24-month edge materially
underperforms the full sample (decay). **Pre-registered:** these thresholds are written down *before*
the Edge Lab (S12) runs — never tuned after seeing results.

**Per-decision evidence bundle (consultant-adopted).** The 17 checks are the *full* battery; a given
decision type assembles the **subset** that applies, fed by the S12.5 evidence objects. Worked example —
an **open-long dividend-sleeve** bundle requires: (1) latest Sharia status · (2) dividend-event integrity
(gross/withheld/net + ex-date rule resolved) · (3) corporate-action conflict check · (4) market-data
freshness · (5) slippage estimate · (6) portfolio risk-budget fit · (7) benchmark interaction ·
(8) macro-regime conflict check · (9) research-agent dissent summary. The bundle is what flows into the
gate; `decision_type` (open/add/reduce/close/rebalance) selects which checks are mandatory — sells/closes
stay edge-exempt (S6.5).

**Shadow vs enforcing mode (reviewer-validated).** The Edge Proof gate runs in `shadow` (log the
decision it *would* make, don't block) or `enforcing` (block). A new strategy on a freshly-fed backbone
starts in **shadow** so thresholds calibrate against real outcomes before they can block live trades;
promote to **enforcing** only after the shadow window. *(S6.5 already enforces edge for buys by default —
correct while no live strategy runs; shadow mode is how real strategies calibrate before going live in S11.)*

**Decision-quality dashboard (extends the S6 state dashboard — shows *why*, not just *what*):**
current regime + confidence (from S9) · active strategy + weight · **signals rejected this cycle and
the exact reason** (failed check #, threshold missed) · are we beating SPUS / DCA / cash · **is the
edge decaying** (rolling 24-month vs full-sample) · data freshness + source-quorum status. Panels
come online as their inputs do: regime at S9, rejected-signals + edge-decay here at S10,
beating-benchmark at S12. This is the more valuable operator view — it surfaces the rejections that
are the whole point of the system.
*(**Scaffold already shipped at S6** — Dashboard v2 (`dashboard/snapshot.py` + `generate.py`) already
renders the Decisions tab (Edge-Proof verdicts + Constitution rejections-with-reasons), the Regime tab,
and the safety posture. S10 fills the remaining panels as their inputs arrive: failed-check-number +
threshold-missed detail (needs the 17-check engine), beating-SPUS/DCA (S12), and the edge-decay
rolling window.)*

**Gate:** every signal passes all 17 checks; regime-filtered sample enforced; multiple-testing penalty
+ signal decay applied; `trade_allowed=false` blocks the allocator; no edge proof = no trade; the
decision-quality dashboard renders the current regime, the active strategy, and at least one
rejected-signal-with-reason.

**STATUS: ✅ ENGINE BUILT (→ 478 tests).** `engine/edge_proof.py` — pure `run_full_edge_proof` (all 17 checks
as `CheckResult`s with blocking flags) + pre-registered thresholds (sample ≥50, regime-sample ≥20, median
excess ≥2.5%, worst ≥−25% unless ≤2% position, data-quality ≥0.80) + **multiple-testing penalty** + **signal-
decay** test + **Sharia-status-at-decision (fail-safe, #1)** + **model-disagreement→human** rule + **shadow/
enforcing** mode; `FullEdgeReport.trade_allowed` keeps the allocator gate drop-in. `evaluate_signal_full` DB
wrapper (reuses the v0 loaders + S9 Sharia status) + `edge_reports` audit table + `log_full_edge_report`.
`tests/test_edge_proof_full.py` (13). *Remaining for full S10: feed it real strategy signals (S11) + the
regime-conditioned historical sample from `event_reactions`/`regime_history`; render the new panels on the
decision-quality dashboard as those inputs arrive. The engine + gate are done.*

---

### ⭐ S10.5 — Operator-Loop Assembly + Runtime Automation
*New sprint (founder-agreed 2026-06-07), promoted from Workstreams A + B. The components are built and unit-
tested; this sprint **strings them into the live loop** and gives them a runnable harness. Deliberately its own
focused effort at the S10→S11 boundary — by S10.5 the full 17-check Edge Proof (S10) exists, so the loop is
assembled around the real gate **before** S11 strategies start flowing trades through it.*

**Why now (the finding this closes):** today `loop/runner.py` calls `Constitution.evaluate` directly and
`loop/scheduler.py` runs with no-op callbacks — so the upgraded §4 loop (Observe → Router → Edge/Product-Proof →
Constitution → Budget → Approval → Act → Learn) is **never assembled at runtime**, and the Edge-Proof gate (which
lives in `capital/allocator.py`) is **bypassed in the assembled path**. Harmless only because nothing trades in
Phase 0 — but a **Phase-1 blocker**. Nothing new is invented here; it is *wiring built parts together safely*.

**A — Assemble the decision loop (Workstream A):**
- **A1 (the blocker):** route every consequential action through `Allocator.request()` (Edge-Proof gate +
  Budget Kernel) instead of calling `Constitution.evaluate` directly. **Invariant test:** in the *assembled*
  loop, a buy with no passing `EdgeReport` is rejected — i.e. the CLAUDE.md rail holds end-to-end, not just in
  the unit. Sells stay edge-exempt (S6.5).
- **A2:** drive the **Operator-OS state machine + Opportunity Router** from the loop (built S5, currently
  uncalled) — Observe → Router picks a path (Trader/Entrepreneur/Research/System/Wait) → Proof → gates → Act.
- **A3:** have a decision actually **consume the Regime engine** (today it feeds only `regime_history` + the
  dashboard) — Router/strategy selection reads `regime_to_themes`.
- **A4:** wire `trader/regime/peg.py` into `features.py` (if not already done in S9 slice 4).
- **Order of operations preserved:** Sharia → Edge/Product Proof → Constitution → Budget → Approval → Act. No
  station may be skipped; the assembly is exercised by an end-to-end integration test, not just unit tests.

**B — Runtime automation / scheduled entrypoints (Workstream B):**
- Add Task-Scheduler entrypoints (mirroring `loop/scheduler.py`) for: the **weekly** safety job
  (`ops/scheduled_checks.run_weekly_checks` — kill-switch self-test + backup + reconcile), and a **daily ops job**
  that beats `ops/heartbeat` + pings `ops/deadman`, **renders the dashboard** (`dashboard.write_dashboard`), and
  **sends the founder brief** (`alerts/brief.send_founder_brief` over Telegram/WhatsApp, with RED ALERT on a
  >3% drop). These are built but currently have no `__main__`.
- A minimal **connector-ingestion entrypoint** (part of Workstream D) so `macro_observations` etc. are populated
  on a schedule, not just in tests — otherwise the assembled loop's regime features read empty tables.

**Out of scope (stays where it is):** new strategies (S11), the full portfolio engine (S11), live execution
(S13). S10.5 is wiring + automation only — still **paper, still no live capital**.

**Gate:** an **end-to-end integration test** drives a full simulated tick through the assembled loop
(Observe → Router → Edge Proof → Constitution → Budget → Approval → Act → Learn) on paper; a buy with no passing
EdgeReport is **rejected by the assembled loop** (not just by the Allocator unit); the Router returns Wait when
there is no edge; the scheduled daily job renders the dashboard + emits the brief; the weekly job runs the
kill-switch self-test + backup + reconcile from a real entrypoint. **A1 closes the Phase-1 blocker.**

**STATUS: ✅ DONE (→ 486 tests). The Phase-1 blocker (A1) is CLOSED.** `loop/assembled.py` — `AssembledLoop.run_tick`
assembles Observe(regime) → **Opportunity Router** → **Allocator (Edge Proof + Constitution)** → **Budget Kernel**
→ **phase-gated Human-Approval** → Act(paper) → op-log. Every action routes through `Allocator.request(...)`, never
`Constitution.evaluate` directly — so the invariant test proves **a buy with no passing EdgeReport is rejected by
the assembled loop.** `loop/jobs.py` (Workstream B) — `run_daily_ops` (heartbeat + dashboard render + founder
brief) and `run_weekly_safety` (kill-switch self-test + backup + reconcile) with a `python -m loop.jobs daily|weekly`
entrypoint. `tests/test_assembled_loop.py` (8): the invariant, router-waits-without-edge, budget block, phase-1
approval gate, kill switch, op-log, and both jobs. *(A4 peg→features already done in S9 slice 4. The legacy
`loop/runner.py` is unchanged; the assembled loop is the new real harness — S11 strategies feed it candidates.)*

---

### S11 — Strategy Registry + Portfolio Engine + Learning Engine
*Was S8. Starter trio updated (now feasible because the data backbone exists). Founder direction folds in a
multi-portfolio layer + a dividend-growth strategy.*

**Starter trio (build first):** `core_dca` (monthly DCA into approved core ETF/basket; benchmark SPUS;
no timing unless regime risk is extreme — likely beats most overactive systems after costs) ·
`quality_momentum` (factor-driven, low turnover: 12-1 momentum, 6m momentum, positive earnings
revisions, revenue growth, FCF margin, low leverage, liquidity, valuation-not-extreme) ·
`etf_regime_rotation` (SPUS/HLAL/MNZL/cash by regime — **only if it beats simple DCA after costs**).

Then `dividend_growth` (founder direction — Sharia-screened **quality income**: compliant business, low
debt, durable + growing payout, sane payout ratio; purification of any impure portion via `purification_ratio`.
This is dividend-*growth*, **not** dividend-*capture* — capture buy-before/sell-after-ex-div rarely survives
costs + whole-share constraints and the Edge Proof will likely reject it; build the dividend data, treat
capture as a hypothesis to test, not a strategy to trust) and `earnings_guidance_drift` (after the earnings
calendar + fundamentals are clean).
  - **Dividend mechanics (consultant-adopted) — model the cash, not a single opaque event:** store **gross /
    withheld / net separately** (`dividend_events` + `dividend_receipts` tables); handle ex-date rules incl.
    the **25%+ special-dividend deferral** (ex-date = one business day *after* payment) and due-bills;
    corporate actions (splits/spinoffs/mergers/name-changes) are **ledger events**, and splits can cancel/
    adjust standing orders — broker-order state must reconcile, not assume orders persist; use **settle-date**
    accounting where broker practice requires. **Lot-level position accounting** for dividend/tax-sensitive
    strategies (weighted-average is too lossy for income work; dashboards still aggregate by symbol).
    Process it as a **4-stage pipeline**: *announcement* (store dates/amount, no cash/P&L change) →
    *entitlement* (freeze entitled qty at the ex/record rule, handle due-bills + 25%+ specials) →
    *settlement* (post gross + withholding + net as separate ledger events, settle-date) → *attribution*
    (split the event into income · tax · price effects, so a sleeve that looks strong on cash-received
    isn't actually losing after the ex-date gap + withholding).
  - **Tax frame = NRA withholding, NOT US-person (founder is KSA-resident — corrected from the consultant
    docs):** model **gross → withholding (Form 1042-S / DIV vs DIVNRA split) → net**; the US **qualified-
    dividend 60-day-holding rule is largely N/A** for a non-US person, so do *not* build holding-period tax
    optimization — withholding (treaty rate) is what matters.
  *(Dividend data: the EODHD Splits/Dividends API — ex-div date, yield,
payout ratio, growth streak — per `CAMEL_DATA_SOURCES.md`.)*
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

**Strategy promotion ladder (consultant-adopted) — per-strategy `mode`, distinct from the portfolio
lifecycle:** `backtest` (proves idea viability / parameter sensitivity; does *not* prove latency, queue
position, market impact) → `realistic_paper` (proves clock integrity, event/corp-action handling, fill
logic; not true routing or broker outages) → `shadow` (proves signal quality vs the live market; not
operational position accounting) → `live_small` (proves real slippage, broker behavior, the approval
path; not full-capacity scale) → `live_scale` (production). A strategy moves **one rung at a time**;
failure **demotes** (→ cooldown in `realistic_paper`), it doesn't delete. This `mode` is the registry's
`mode` field and gates which portfolios/phases a strategy may run in.

**4-tier Learning Engine:** L1 auto base-rate updates · L2 auto weight within founder-set ±band ·
L3 propose-only (founder approves activate/deactivate + regime affinity) · L4 founder-only
(Constitution / new strategies / the band itself). Regime→strategy affinity learned at N≥20 per regime.

**Portfolio Engine (founder direction — multiple portfolios, strategy-per-portfolio).** Today the Camel runs
one implicit portfolio; this adds a first-class multi-portfolio layer under the single Camel Fund:
- `portfolios` table (id · name · mandate · capital_allocation · assigned_strategies · per-portfolio risk
  limits · benchmark). Positions + ledger become **portfolio-scoped** (`portfolio_id` everywhere; the S6.6
  position accounting extends to per-portfolio).
- `PortfolioManager`: allocates fund capital across portfolios, assigns each a strategy set, runs every
  action through Edge Proof + Constitution **per portfolio**, and aggregates risk/P&L up to the fund level.
- Each portfolio carries its own strategies (e.g. a Core-DCA portfolio, a Quality-Momentum portfolio, a
  Dividend-Growth portfolio). **Trust inversion unchanged** — every action in every portfolio passes the same
  deterministic gates; the engine just runs them N times.
- Built for **breadth at scale** (N portfolios/strategies handled concurrently and cleanly); **execution
  stays EOD-positional**. Fund-level caps (total exposure, sector, cash buffer) sit *above* per-portfolio caps,
  and per-portfolio positions/ledger must reconcile to the fund.
- **Event-driven scheduling at scale (consultant-adopted):** rather than one monolithic loop, schedule work by
  `(portfolio_id, strategy_id, event_window)` tuples — so one sleeve can pause without pausing all portfolios,
  failures isolate, and research depth concentrates on the names/events that actually matter. (A scaling
  refinement of the current single EOD loop; adopt when N portfolios make the monolithic tick wasteful.)
- **Portfolio lifecycle (consultant-adopted):** incubate → qualify → pilot → scale → defend → retire, with
  per-phase gates (schema/data validated → realistic-paper fills/corp-actions → low-cap live + approval →
  normal → close-only/low-risk on drawdown → flatten & archive). A strategy that fails can **demote to
  realistic-paper (cooldown)**, not just delete.
- **Rebalancing:** tolerance-band (default — cuts turnover) + calendar + event-triggered (benchmark/whitelist/
  corporate-action/risk-budget breach). 4-level risk budgets: portfolio · sleeve · strategy · position.
- **Multi-benchmark per portfolio:** policy benchmark (what it should resemble) · opportunity benchmark
  (cost of the Sharia constraint) · cash hurdle. **Attribution:** allocation · selection · dividend/carry ·
  trading/friction effects.
- **Seed portfolios (consultant-adopted):** `core_sharia_growth` (SPUS bench; DCA/rotation) · `income_dividend`
  (dividend-quality) · `thematic_satellite` (momentum/themes) · `cash_waiting_room` (idle cash/watchlist) ·
  `experimental_paper` (new strategies pre-promotion) · `entrepreneur_camel` (product budget, revenue KPIs).
- **Strategy-portfolio matrix:** each strategy declares `allowed_portfolios`, `forbidden_portfolios`,
  `max_portfolio_weight`, `max_single_position`, `min_signal_confidence`, `kill_rule`, `requires_edge_proof` —
  so a strategy runs only where it's permitted (the consultant SQL schemas for `portfolios` / `strategies` /
  `portfolio_strategy_allocations` / `positions` / `trades` / `dividends` / `edge_proof_reports` are the
  concrete starting point).

**Portfolio/strategy definition-of-done (consultant acceptance checklist, adopted):** every position belongs to
a portfolio + a `strategy_id` (or a manual reason); every strategy is allowed only in specific portfolios;
every buy/increase needs Edge Proof; every portfolio has a benchmark + attribution; every dividend is recorded
separately from price return; every datapoint carries `source_id/known_at/ingested_at/content_hash`; critical
signals need ≥2 sources or human approval; data-quality failure blocks trades; portfolio drift produces
*rebalance suggestions*, not automatic live trades.

**Gate:** ≥3 strategies (the trio) all passing Edge Proof; learning updating base-rates; improvement
proposals land in the Learning Ledger; DCA guardrails enforced; never auto-edits the Constitution;
**≥2 portfolios run independent strategy sets with portfolio-scoped positions/ledger that reconcile to the
fund, and every per-portfolio action passes Edge Proof + Constitution.**

**STATUS: ✅ DONE (→ 513 tests).** **(a) Strategy framework** `strategies/` — `base.py` (`BaseStrategy` +
`Signal`/`StrategyContext`/`StrategyMeta`, the **promotion ladder** backtest→…→live_scale one-rung-at-a-time,
defence-in-depth `_is_tradeable` so a strategy never *proposes* a haram name), `registry.py` (`StrategyRegistry`
+ the **strategy-portfolio matrix** + regime filter + bounded weighting), the **starter trio** `core_dca` /
`quality_momentum` (pure 12-1 momentum) / `etf_regime_rotation` (regime→ETF-or-cash) **+ `dividend_growth`**
(quality income, not capture) + `dividends.py` (gross→**NRA withholding**→net + purification), and
`mixer.py` (`StrategyMixer` blends overlapping convictions by weight). **(b) Portfolio Engine** `portfolios/`
— `Portfolio` + lifecycle (incubate→…→retire), the **6 seed portfolios** (weights sum to 1.0), allocation,
**tolerance-band rebalancing that emits *suggestions, not auto-trades***, 4-level risk budgets, multi-benchmark,
`portfolios`/`portfolio_holdings` tables + persistence. **(c) 4-tier Learning Engine** `learning/` — L1 auto
base-rate (`base_rate_updater`), L2 auto weight **within a founder band** (`strategy_scorer`), regime affinity
gated at **N≥20** (`regime_matcher`), anomaly detector, **L3 propose-only** (`improvement_proposer` →
`learning_proposals` table; **no agent-callable apply** — L4 founder approves). Tests: `test_strategies.py` (13)
+ `test_portfolios.py` (9) + `test_learning_engine.py` (5). **S11.5 keystone integration shipped** (`loop/driver.py` —
`run_strategy_tick` drives registry→context→mixer→**full** Edge Proof→assembled loop, proven by
`tests/test_integration.py`; `portfolios/holdings.py` per-portfolio accounting + `reconcile_to_fund`). → 517 tests.
*Remaining backlog: full portfolio-scoped positions/ledger rewrite (S12, with broker write-atomicity);
intraday_monitor + congress_signal + the rest of the strategy roster are post-Edge-Lab.*

---

### S12 — Edge Lab (Backtesting) + Realistic Paper Execution
*Was S10. Adds the realistic-paper engine + survivorship + two-engine cross-check. Mandatory before any
live automation. Run after ≥28 days of paper data.*

**Run modes (three):**
- `loop_test` — historical / last-close fills; $1 fallback unit-tests only.
- `realistic_paper` — no fallback; limit orders only; spread + slippage models; non-fill + partial-fill
  logic; market hours; corporate-action awareness. **(Consultant-adopted) Camel's own realistic paper must
  do what broker paper does NOT:** Alpaca paper explicitly does *not* simulate dividends, market impact,
  latency slippage, queue position, or fees — so `realistic_paper` adds **dividend entitlement + settlement
  replay, corporate-action replay, fees, and stale-data rejection**. Two distinct concepts: *broker paper*
  (API-integration smoke test) vs *Camel realistic_paper* (decision-validation). No performance number ever
  comes from broker paper or `loop_test`.
- **`sandbox` — the full system on LIVE real-time data with VIRTUAL money (founder request).** ⭐
  Sandbox runs the *entire* loop — Observe → strategies (S11) → Edge Proof (shadow or enforcing) →
  Constitution → **virtual fills via the realistic-paper engine** — against the **live market feed**,
  with the decision-quality dashboard showing every accept/reject in real time. It is the live dress
  rehearsal: full system power, no real money. **The ≥28-day (and the reviewers' 90-day shadow) track
  record that gates micro-live (S13) is produced in sandbox.** This is the truest test of "can the whole
  thing actually trade" short of risking a dollar.

Modules: `execution_simulator`, `fill_model`, `slippage_model`, `order_book_snapshot`, `partial_fill`,
`sandbox_runner` (live-feed driver). **No performance report may use loop_test fills.**
*(Dependency note: a minimal sandbox — live price feed + virtual money + Edge Proof v0, no strategies —
is possible once Alpaca live-data is wired; the **full** "full-system-power" sandbox needs the strategy
registry (S11) and the realistic-paper engine, hence its home here in S12.)*

**Honest backtesting:** look-ahead / survivorship / data-leakage / overfitting prevention; walk-forward
(out-of-sample); transaction-cost + slippage + spread; whole-share constraints (Sahm); point-in-time
Sharia status; **delisted-company handling (EODHD delisted dataset; CRSP later)**; crisis tests
(2000 dot-com, 2008 GFC, 2020 COVID, 2022 rate shock).

**Benchmark hierarchy:** Cash · monthly DCA into SPUS · SPUS B&H · HLAL B&H · MNZL · equal-weight
Sharia basket · Camel active. If Camel doesn't beat simple DCA on risk-adjusted terms after costs, it
does not trade actively.

**Sharia-drag quantification (reviewer-validated)** — explicitly measure the filtered (compliant)
universe vs the unfiltered universe over the test window, so we know exactly what the screen costs in
return. Combined with the pre-registered thresholds (S10), this makes the edge verdict honest.

**⭐ The "No-Edge Found" protocol (both reviews; founder-adopted).** If the Edge Lab does **not** find a
defensible, cost-and-Sharia-drag-survived, out-of-sample-robust signal, that is **the system working,
not failing.** The pre-registered fallback is **scheduled DCA into SPUS/HLAL** managed by a simplified
`core_dca` + DCA guardrails, and **Phase 1 active trading does not proceed.** This branch is defined in
advance — in `docs/CAMEL_LIVE_READINESS.md` — so a disappointing result can't be rationalised away.

**Strategy kill criteria** (disable / research-only if ANY): out-of-sample < benchmark · drawdown >
threshold · hit rate below base rate · depends on one outlier · costs erase edge · works only in one
cherry-picked regime · sample too small.

**Broker write atomicity + positions reconcile (QA-deferred from S9).** `broker/paper.py` currently writes
the order, the ledger entry, and the position update in three separate transactions; wrap them in a single
transaction and add a positions↔ledger reconcile to `ops/reconciliation_report.py` so a mid-submit failure
can't leave them inconsistent. (Low-probability in Phase-0 single-process, but must be solid before live.)

**Two-engine cross-check** — a vectorized engine (vectorbt-style) AND an event-driven engine
(custom / Zipline/LEAN-style); compare results — never trust one engine. Heavy quant libs land here:
pandas, numpy, scipy, statsmodels, scikit-learn, vectorbt, quantstats.

**Gate:** every strategy tested out-of-sample on two engines; delisted handled; full benchmark
hierarchy compared; weak signals killed; all performance from realistic_paper fills; Camel beats
simple DCA before any live execution; backtest using future/restated data blocked by `known_at`.

**STATUS: ✅ DONE (→ 543 tests).** **(a) Realistic-paper execution** `execution/` — `fill.py`/`slippage.py`
(crosses the real spread, partial-fills against displayed size, charges fees, **REJECTS stale data** — no
$1 fallback), `realistic_paper.py` (whole-share constraint), `corporate_actions.py` (the **4-stage dividend
pipeline** announcement→entitlement→settlement→attribution on the **NRA-withholding** frame + split replay).
**(b) Edge Lab** `edgelab/` — `backtest.py` (cost-aware, with a **two-engine cross-check**: an event-driven
and a vectorized engine must agree or the result is untrusted; beats-DCA benchmark), `honest.py` (walk-forward
out-of-sample split + overfit/decay guard + crisis windows), `no_edge.py` (**No-Edge protocol → DCA**: an
active strategy runs only if it proves an edge AND beats DCA after costs; otherwise systematic DCA, never idle
on capital). **(c) ⭐ Sandbox Mode** `sandbox/runner.py` — drives the **full assembled system** (regime →
strategy → full Edge Proof → Constitution → Budget → Approval) against an **injected live quote feed** with
**virtual money** via the realistic-paper executor; produces the track record that gates micro-live. Tests:
`test_execution.py` (12) + `test_edgelab.py` (9) + `test_sandbox.py` (3). *Remaining backlog: survivorship-free
PIT history (Sharadar) for the deepest honest backtests; the live websocket feed adapter (S8.5) replaces the
test stub — both already tracked. The engine, backtester, No-Edge protocol, and sandbox are done.*

---

### S12.5 — Research Desk / Analyst Agents  (founder direction — DESIGN NOW, run later)
*Dedicated agents that each own an information vertical and run study → analyze → store cycles, feeding the
knowledge graph + Learning Ledger for decision-making. **Architecture built now; kept dormant until capital
and a proven edge justify the token spend** — founder decision: "design it, defer running it.")*
- **Vertical analyst agents** (Claude Agent SDK — the planned "real tool-use autonomy" trigger). Full roster
  (consultant-adopted): **market-microstructure** (spreads/liquidity/execution conditions), **macro & vintage**,
  **fundamentals/XBRL**, **dividend & corporate-actions**, **news/geopolitical**, **Sharia auditor**,
  **portfolio & risk** (crowding/overlap/drift), and **execution/TCA** (predicted-vs-realized fills → feeds
  slippage models back to S12). Each: gather (via the S8 connectors) → analyze → write a **structured, sourced
  research note + confidence** into `camel_learning.db` / the knowledge graph. **Agents propose/analyze; they
  never decide** — Edge Proof + Constitution still gate every consequential action (trust inversion intact).
- **Evidence-object contract (consultant-adopted):** each note is a mini credit-memo, not a chat reply —
  `claim · scope · evidence_ids · source_count · freshness · disagreement_score · confidence · horizon ·
  direction · invalidation_conditions · recommended_action · portfolio_fit · compliance_status` — and that
  object is what flows into Edge Proof. The learning loop is **narrow & safe**: agents update retrieval
  indices / prompt templates / entity dictionaries / event taxonomies / slippage params / source-reliability
  priors — they **never** retrain or edit the Constitution.
- **Orchestration:** **on-demand by default** (an analyst spins up when an opportunity/decision needs its
  vertical); an always-on fleet is a later, explicit cost decision. A hard **research token budget**.
- **Guardrails:** research agents are read-only to config/limits/whitelist; their notes are *evidence, never
  instructions*; raw external text passes the sanitiser; every note carries provenance.
- **Dormancy:** ships with the wiring + tests but a **master switch defaulting OFF**; turning it on is a
  founder action gated on capital/edge (sits at "autonomy last" in the priority hierarchy).

**Gate:** the analyst-agent framework exists with ≥1 vertical desk + tests; agents can only write evidence
(never act); a budget/token cap is enforced; the master switch defaults OFF.

**STATUS: ✅ FRAMEWORK DONE — DORMANT by design (→ 557 at slice close; 603 current).** `research/` — `evidence.py` (the 13-field
**EvidenceObject contract** + strict validation), `desk.py` (`AnalystDesk` base — **no execute path exists on
it**; `ResearchDesk` orchestrator with the **master switch defaulting OFF** + a token budget; `write_evidence`
→ the new `research_evidence` table), and **two vertical desks** (`ShariaDesk`, `MacroDesk`) producing evidence
deterministically from the governed DBs (placeholders for the future Agent-SDK desks — when those land they
implement `analyze` and return the same contract). `tests/test_research_desk.py` (6) prove: master switch off
by default → nothing runs/writes; the contract rejects malformed notes; the budget caps the desks; and a desk
**literally has no `act`/`execute`/`trade` method**. Evidence-only, never decides — turning it on is a founder
action gated on capital/edge.

---

### S13 — Micro-Live Readiness (Phase 1)
*(Was S11; prerequisites + deliverables unchanged.)*

**Prerequisites (all must pass):** ≥28 days continuous paper operation · 0 guardrail breaches · ledger
reconciles with the broker paper statement · every position had thesis + invalidation · kill switch
tested over Tailscale · broker key trade-only/withdrawals-disabled · margin + options disabled · key
scoped to minimum permissions · Edge Proof has approved ≥1 signal · approval flow tested · manual
dry-run · one **rejected** trade test live (no order placed) · one **approved** micro trade done
manually before automation · emergency broker login tested · **the Edge Lab (S12) found a defensible
edge** — if it did not, the No-Edge protocol applies and Phase 1 active trading does **not** proceed
(DCA-only; this is a success state, not a failure).

**Broker direction (founder-resolved):** **Alpaca** for the autonomous US paper→micro-live path
(API-first; trade-only key, withdrawals disabled; limit-only). **`ManualBroker` (Sahm)** for the
founder's real Saudi/US-ETF account, which has **no API**: Camel proposes → founder executes in the Sahm
app → logs the fill (price/shares/timestamp) back to the append-only ledger under the same Constitution
checks + reconciliation. **IBKR deferred to Phase 2.** Full comparison in `docs/CAMEL_BROKER_MATRIX.md`.
*(PDT note: Alpaca live's $25K pattern-day-trader rule is largely N/A — Camel is cash-account, long-only,
positional, not day-trading; documented in the matrix.)*

**Approval payload hardening (review #6):** a Telegram approval must carry an **action hash** + the
structured fields (notional · symbol · side · Edge-Proof summary · invalidation) and be logged; **no
approval by free-text message alone**; timeout = veto.

**Deliverables:** Approval Channel (Telegram one-tap approve/veto, timeout = veto) · LiveBroker — Alpaca
(paper → live, behind the phase flag) · `ManualBroker` (Sahm) manual-entry mode · limit orders only · no
pre-market/after-hours · live key-scope verification at startup.

**Initial live permissions:** human approval on every live trade · no autonomous execution · max
$100–500 · limit orders only · whitelist only · no pre-market/after-hours.

**STATUS: ◑ READINESS INFRASTRUCTURE DONE — go-live is FOUNDER-GATED (→ 557 at slice close; 603 current).** The code that makes
micro-live *possible and safe* is built and fail-safe; the act of going live is deliberately NOT automatable:
- **`governance/approval.py`** — the human approve/veto gate (one-tap Telegram). **Withholds by default**:
  an action executes only on an explicit, recorded human approval; missing/pending/vetoed → not approved.
  `approval_fn(dbs)` plugs straight into the assembled loop's phase-gated Human-Approval hook.
- **`broker/manual.py`** — the **`ManualBroker` (Sahm)** path: `propose` emits an order ticket (moves NO money);
  `record_fill` writes a founder-entered real-world fill to the append-only ledger + positions under the same
  Constitution + reconciliation.
- **`broker/live.py`** — the gated **`LiveBroker`** (Alpaca, Phase-2): `submit` **refuses unless all three**
  founder-owned switches are set (phase ≥ 1 · `live_enabled` · trade-only credentials); and even fully enabled
  it raises rather than silently trading (the real Alpaca integration is intentionally unwired — no creds in repo).
  **There is no configuration in which it moves real money on its own.**
- **`ops/live_readiness.py`** — the live-readiness checklist as code (`check_live_readiness`): kill-switch off,
  guardrail imports, ledger hash-chain verifies, paper track record, and **the founder's explicit `live_enabled`
  switch** — which is itself a required box, so the **default result is NOT READY**.
- `tests/test_micro_live.py` (8) prove every default is fail-safe: the LiveBroker refuses, the readiness gate is
  not ready, approval is withheld, and the Sahm path only moves money on a human-entered fill.
**Remaining for an actual go-live (deliberately the founder's, not the code's):** the machine-hardening checklist
(`CAMEL_MACHINE_HARDENING.md`), a ≥28-day paper/sandbox track record, a defensible Edge-Lab edge, and the explicit
phase-flip with real (tiny) capital. *No code here crosses that line.*

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

**STATUS: ✅ DONE — architecture documented AND physically reorganized (2026-06-08).** The value of S14 (a
clean, discoverable domain hierarchy) is delivered both ways: **`docs/CAMEL_ARCHITECTURE.md`** is the canonical
layered map, AND the **physical reorg is complete** — the six strategy/evidence/execution packages now live
under **`trader/`** (`trader/engine`, `trader/edgelab`, `trader/execution`, `trader/strategies`,
`trader/portfolios`, `trader/sandbox`) beside `trader/regime` + `trader/events`, so the whole Trader Camel is
one package tree. Done as a scripted one-shot migration (move dirs + rewrite every `from <pkg>` import),
verified by a **full green run — 603 tests, zero behaviour change**. It was safe because the codebase uses only
absolute `from <pkg>…` imports (no bare `import <pkg>`, no string/`patch()` refs), so the rewrite rebinds
imported names without touching usage sites. *Code beats docs; the move broke nothing.*

---

### S15 — Paid tools & founder actions ("above the line")

**STATUS: ◑ THE ONLY REMAINING WORK — all paid or founder-gated.** After the 2026-06-08 hardening push, every
*free, non-founder* deferred item is done (603 tests green). What's left to cross from paper into real, live,
scheduled operation is, by definition, **not free code we can write**: it is paid vendors, founder
credentials, founder machine setup, and the explicit go-live decision. The full catalogue — with each item
mapped to the code already built and waiting for it — is **`docs/CAMEL_S15_PAID_AND_FOUNDER.md`**. Summary:
- **Paid:** EODHD (dividends/corporate-actions feed + 2nd fundamentals) · Sharadar (survivorship-free PIT
  backtests) · Benzinga (news) · Finnhub (earnings calendar) · Alpaca (live + IEX websocket) · IBKR (Phase 2).
- **Founder credentials (free to provision):** FRED/BEA/EIA keys · Telegram bot token + chat id · Alpaca
  trade-only key · real SEC contact UA · OCR for Sahm screenshots.
- **Founder machine + go-live:** machine hardening · Task-Scheduler wiring (`data.ingest`, `loop.jobs tick`)
  — ✅ **daily + weekly tasks registered (2026-06-11)**, currently **run-when-logged-on** · a ≥28-day track
  record · the `config/limits.yaml` phase-flip with real (tiny) capital.
- ⭐ **NEXT (founder-machine task): run the brain HEADLESS.** Convert the scheduled tasks to *run whether the
  founder is logged on or not* — Task Scheduler "Run whether user is logged on or not" + a stored credential
  (or a dedicated service account / a small always-on box). Needs **elevation + a saved password**, so it's a
  founder act; the daily/weekly tasks and the short-path `C:\camel` repo are already in place for it. Until
  then the PC must be awake + logged in at the trigger time for the cycle to fire.

*Not S15 (free code): all free connectors incl. **GPR + OFAC are now DONE**; the S14 physical reorg is DONE;
the local repo is relocated to the short path **`C:\camel`** (drops the MAX_PATH friction for tasks + tests).*

---

### S16 — Operational Activation & Loop-Closure  (close the loop; start the track-record clock)

**Why this sprint exists — the 2026-06-09 verified audit.** A 6-dimension adversarial code audit (independent
agents, verified against source + the live DBs) found that **"S1–S14 DONE" is true for code-built-and-tested but
overstates operational reality.** Three honest distances: software built+tested **~78%**, operationally-wired-
and-proven on real data **~12%**, autonomy actually *earned* **0%**. The safety core is real — **no core safety
claim was overstated; every guardrail is a tested hard wall** — but the **operator does not yet run end-to-end on
real data**, for two structural reasons this sprint closes:

1. **The loop is open after Act.** Measure→Learn exists nowhere in the runtime — the entire `learning/` package
   (base_rate_updater, strategy_scorer, regime_matcher, anomaly_detector, improvement_proposer) is imported only
   by its own tests; `assembled.py` advertises "→ Learn" but `run_tick` stops at Act. The North Star loop's back
   half is unbuilt at the integration level.
2. **The production tick can't earn autonomy.** `loop/jobs.run_trading_tick` injects no broker, so its "Act" is a
   `'simulated_fill'` string — no ledger entry, no `positions` write, **no `runs` row**. The ≥28-run track record
   S13 requires literally **cannot be produced** by the founder-scheduled entrypoint; only `trader/sandbox/runner.py`
   fills (and even it resolves no trades). Masked by a test asserting only `isinstance(out['executed'], list)`.

Plus: **data is hollow** (verified on the live DBs: `prices=0, macro=0, runs=0` — Stooq now serves a JS anti-bot
page, FRED needs a free key, `sharia/cross_check` has no caller so the whitelist is unpopulated), and the
**Entrepreneur arm is ~10% of the Trader arm and wired into nothing** (the router can emit "entrepreneur" but no
loop stage ever calls the gate/pipeline).

**This sprint is the CODE half of the critical-path-to-live.** It must complete before the S13 ≥28-day clock can
start and before the S15 go-live — those founder/paid/time steps depend on it.

**Deliverables (all free code; paper-only; no guardrail is weakened):**
- **A1 — Durable Act in the production tick (the keystone).** Inject a `PaperBroker`/realistic executor into
  `loop/jobs.run_trading_tick` so "Act" places an order, appends to the SHA-256 ledger, updates the `positions`
  table, **and** writes a `runs` row via `loop/state.py` (begin/finish_run). Without this the live-readiness
  run-count is stuck at zero forever, regardless of elapsed time.
- **A2 — Close Measure→Learn.** Add a trade-resolution / Measure step (resolve closed or marked positions → win/
  loss outcomes) and call the L1/L2 learning updaters + `improvement_proposer.propose` on a schedule, writing to
  `learning_ledger`. **Propose-only stays a hard wall** (no `apply()`/auto-apply; `decide()` needs a human).
- **A3 — A working free price feed.** Stooq now returns a JS anti-bot page — **do NOT bypass bot-detection**; swap
  to a working free source (or the keyed feed) and run `data/ingest` to populate `prices`.
- **A4 — Populate + schedule the Sharia universe.** Wire `sharia/cross_check` (currently has no caller) and load
  a real whitelist + a scheduled re-screen, so the fail-safe `_is_tradeable` guard has names it can clear.
- **A5 — Evidence-gated per-strategy promotion (optional).** Make `registry.promote()` consult the now-real track
  record instead of being a free state-setter (today it advances a rung with zero evidence check and no runtime
  caller) — so the "autonomy earned per strategy" ladder becomes a mechanism, not documentation.
- **A6 — Doc-drift correction.** Fix the optimistic drift the audit catalogued: test count 603→**613**; the
  "closed loop" / "runs the assembled loop → Act" framing (it simulates); the sandbox-as-"micro-live track record"
  claim (it records fills, resolves nothing, learns nothing); the weak `isinstance(...,list)` test; the stale
  CLAUDE.md repo-map paths (post-S14 reorg) and the "13-check"/v0 docstring; and re-scope "two co-equal arms" to
  "Trader wired; Entrepreneur engine-only" until a real product is in flight.
- **A7 — Exit / position manager (the generator of closes).** ⚠️ Surfaced by the S16 QA: the Measure→Learn
  machinery (A2) is correct and proven, but it only fires when a position **closes**, and the scheduled decision
  path is **buy-only** (the driver proposes `side='buy'`; nothing sells). So in steady-state production no
  round-trip ever completes and the Learn half stays dormant. A7 adds a **reduce-only, governed** exit step
  (profit-take / stop-loss / time-stop on founder-owned thresholds; sells routed through the Constitution —
  phantom-sell + frozen-close-only still apply — then the PaperBroker), so positions actually close, resolution
  fires, and base-rates update from real round-trips. **Until A7 lands, do NOT describe the loop as auto-closing
  in production** — A2 is "machinery wired + correct + unit-proven on driven closes", A7 makes it flow.

**Gate (one line):** the production `loop.jobs tick` runs the FULL governed forward half on real free data and is
**durable** — a passing-edge buy fills via the PaperBroker (orders + ledger + positions, one txn), the tick
**writes a terminal `runs` row** (`complete` only when the Act stage ran; `no_action`/`halted`/`error` otherwise,
so no-op ticks never advance the ≥28-run gate), and **Measure→Learn** records each executed trade and, on a
**closed round-trip**, resolves it into a per-strategy base-rate update (round-trip P&L, one outcome per close) —
each proven by a real-fill / runs-row / base-rate-delta test (NOT `isinstance`). **A7** then supplies the closes
that make the Learn half fire end-to-end in steady-state production.

**Explicitly NOT in S16 (stays founder/paid/time — S13/S15):** the free `FRED_API_KEY` signup, Windows
Task-Scheduler registration, the ≥28-day elapsed clock, machine hardening, and the `config/limits.yaml`
phase-flip with real capital. **No code in S16 crosses the live line** — it makes the *paper* operator actually
run and learn, which is the prerequisite the go-live gates were always waiting on.

**Sequencing within S16:** A1 + A2 first (highest leverage — they convert the engine into something that can
record its own track record), then **A7** (exits, so the Learn half actually fires), then A3 + A4 (so the record
is on real data), A6 alongside, A5 last.

**STATUS: ✅ S16 CODE-COMPLETE — A1–A7 + Edge Lab harness + scheduler DONE & QA-HARDENED (2026-06-09/10). → 671 tests green.**
The wave-catching pipeline is now wired end-to-end in code; the only remaining inputs are founder/paid/time (below).
- **A1 — durable Act + run persistence** ✅ `loop/jobs.run_trading_tick` fills via a real `PaperBroker` (orders+ledger+
  positions, one txn); persists a GRADED terminal `runs` row (`complete` only when the Act stage actually FILLED —
  no-op/halted/error ticks never advance the ≥28-run readiness gate); failure → `error`, never stuck `running`.
- **A2 — Measure→Learn** ✅ `learning/measure.py`: per-round-trip P&L (delta from an at-open baseline, not lifetime
  cumulative), ONE outcome per economic close, persistent per-strategy base-rate (L1), propose-only L3 on
  underperformance (stable-reference anomaly). Now actually FIRES because A7 generates the closes.
- **A7 — governed exits (the generator of closes)** ✅ `trader/execution/exits.py` + `AssembledLoop.run_exits`:
  reduce-only profit-take / stop-loss / time-stop / sharia-exit on founder-owned `limits.yaml` thresholds (sign-typo
  sanity-checked); every sell routed through Constitution (whitelist-required, close-only-for-frozen, phantom/oversell)
  → phase-gated approval → broker; sells Edge-exempt, consume no budget; kill-switch honored. Wired into the tick
  BEFORE buys, with a mark-to-market + fund resync so the marks can't skew the buy leg's concentration/cash rails.
  **The e2e test proves the full loop in ONE scheduled tick: held position hits +X% → governed exit fills → run
  grades `complete` → round-trip resolves → base-rate moves.** The Learn half now fires in production.
- **A3 — real free price feed** ✅ `data.ingest.alpaca_backfill` (+`have_alpaca_keys`, CLI): the instant the founder
  provisions free Alpaca keys, real EOD history flows (Stooq is bot-blocked); error-tolerant, injectable, never raises.
- **A4 — Sharia universe** ✅ `sharia/universe.py`: founder-gated `seed_universe` through the Constitution's
  ADD_WHITELIST gate (fail-closed on blank founder; kill-switch refuses); **only the vetted default ETFs land
  `compliant`, any other symbol seeds `pending_review` (buy-blocked) until a real screen**; quarterly `rescreen_due`
  schedule surfaced in daily ops + the brain cycle.
- **A5 — evidence-gated promotion** ✅ `registry.promote()` is allow-on-proof (≥20 resolved round-trips, finite
  base-rate ≥ 0.5) and the two LIVE rungs are **founder-only regardless of evidence** — the agent can earn paper
  autonomy, never live capital.
- **Edge Lab harness** ✅ `python -m trader.edgelab.run --symbols …` → real history → two-engine backtest →
  per-bar-normalized walk-forward → beats-DCA → **EDGE / NO_EDGE→DCA** verdict per symbol.
- **Scheduler** ✅ `scripts/register-tasks.ps1` (founder runs once, elevated): daily brain cycle + weekly safety.
- Connector URLs are now **secret-redacted at rest** (`data/connectors/base.redact_url`) — no API key persists in DB
  rows / source_documents / backups. Two adversarial QA fleets (FAIL→fixed) + an independent re-verify pass cleared it.
**Remaining = founder/paid/time only (S15 / S13):** the two free signups (Alpaca paper key, FRED key), running the
Task-Scheduler script, the ≥28-day track record the daily cycle now accrues, and the founder's deliberate phase-flip.

---

### S17 — The Workforce (Desks · Supervisor · Scheduler · Kitchen)  ·  PLANNING

**STATUS: ◑ FIRST SLICE BUILT (2026-06-10) — S17.1 desks + S17.6 Opportunity Board + S17.7 Kitchen DONE &
QA-reviewed (700 tests). Remaining: S17.2 supervisor+cost-cap · S17.3 scheduler/DAG · S17.4 proposal
self-check · S17.5 memory consolidate · S17.8 LLM desks.** Full plan + web-deploy note in `docs/CAMEL_S17_WORKFORCE.md`.
Decomposes the one governed loop into named single-job **desks** (SCOUT data · HERALD news · ORACLE regime · MUFTI
Sharia · QUANT edge · STEWARD portfolio · CONDUCTOR decision), a **supervisor** (auto-restart + a hard token/API-cost
cap — the "runaway bill" guardrail), a **scheduler/DAG** (desks feed each other), a live **Kitchen** cockpit (watch
desks work + founder-only watch-AND-control over an Opportunity Board via the existing command channel), plus Level-2
(proposal self-check) and Level-3 (memory consolidation + patterns) hardening. **Activates and grows the dormant
S12.5 Research-Desk framework** (`research/` — evidence-object contract + no-act guarantee, already built). Output =
a ranked, reasoned, governed **Opportunity Board** ("where to put the money") the founder approves — never blind
auto-trading, never advice. Sub-sprints S17.1–S17.8 are independently pickable; recommended first slice
**S17.1 → S17.6 → S17.7**. Everything is buildable+testable now; the parts that become *real* money-insight light up
when the founder adds the free Alpaca + FRED keys. No sub-sprint weakens the trust-inversion or moves real money.

---

### S18+ — Evidence-Deepening & Next-Wave track  (from the 2026-06-11 consultant review)

Two external consultant proposals (a full stress-test + a portfolio/data/agent expansion) were reviewed
line-by-line. **~65% of their recommendations were already built** — S8 (data backbone + source registry +
provenance + point-in-time), S9 (**Event Reaction DB** `trader/events/reactions.py` + regime engine), S10
(17-check Edge Proof incl. regime-conditioning/multiple-testing/decay/walk-forward), S11 (portfolio engine +
strategy-portfolio matrix + promotion ladder + `dividend_growth`), S12.5 (research-desk evidence contract),
S17.2 (token/API cost cap), S17.5 (memory consolidation). The genuine residue is folded in here, **CALIBRATED**:
Tier A (do now; cheap; makes the track record *trustworthy*) → Tier B (let the ≥28-day clock run) → Tier C
(alpha discovery — **research-only, gated on a proven edge + a funded decision; never a trading shortcut**).

> ⚠️ **Governing caveat (the golden rule):** the "find the next major wave / beat the market" idea is the
> highest-value AND highest-risk part of the review. The Camel is trustworthy *because* it DCAs honestly when
> there is no edge; a wave engine is a narrative generator and must stay evidence-gated, SKEPTIC-checked,
> paper-only, Sharia-walled. Build it as **proof**, never as a faster path to acting.

**Tier A — trustworthy track record (free, buildable now):**
- **S18 — Production-Paper Integrity.** Wire the existing `trader/execution/realistic_paper.py` (spread/
  slippage/partial-fills/fees/stale-reject/whole-share) into the PRODUCTION tick as an **investment-valid**
  mode, distinct from the **operational** last-close mode — and make the **≥28-run readiness clock count only
  investment-valid runs**. (The executor exists in the Sandbox; this is wiring + a mode flag + run-grading.) *Top gap.*
- **S19 — Multi-source quorum enforcement.** The logic exists (`security/source_allowlist.has_quorum`,
  `data/triangulation`, `data/quality.data_eligible`); add a `require_quorum` gate so a price/corporate-action
  with <2 agreeing approved sources is research-only, not risk-eligible. *No-op-but-wired until a healthy 2nd
  free feed (Stooq) exists, then it bites.*
- **S20 — Portfolio & strategy attribution.** Decompose return into price / dividend / allocation / selection
  per `portfolio_id`+`strategy_id`+`edge_report_id`; an attribution view + benchmark-relative report.
- **S21 — SKEPTIC desk + structured dissent.** A new evidence desk attaching a mandatory counterargument +
  invalidation list to every Opportunity-Board proposal (deterministic risk flags now; LLM later). *The single
  best new idea in the review — institutionalized dissent, fits the trust-inversion.*

**Tier B — accrue evidence (no new code):** let S18's investment-valid paper run the ≥28-day track record.

**Tier C — alpha discovery (research-only; gated on Tier B + a funded decision):**
- **S22 — Signal-Definition Registry + Edge-Proof front-door.** Explicit signal objects (definition, known_at
  rule, eligible universe, holding periods, benchmark/controls) feeding the existing 17-check engine — so alpha
  proposers are tested as *signals*, not just symbols. (The checks exist; this is the missing front-door.)
- **S23 — Next-Wave Radar (`trader/waves/`).** detector → theme/sector/company-exposure graph → Sharia wall →
  signal-conditioned Edge Proof → SKEPTIC dissent → Opportunity Board; stages Radar→Watchlist→Candidate→Paper→
  Satellite→Scale→Retire. **Research/paper-only; never an autonomous live path.** Premature until an edge is proven.
- **Data depth (paid; founder):** EODHD (dividends/fundamentals) is the first sensible paid step; Polygon/
  Sharadar/Norgate are *post-edge* expenses (stay in S15), not pre-edge.

**Founder / external (not code):**
- **S-Sharia — External Sharia review** before any individual-equity trading: document the in-house AAOIFI
  methodology, cross-check Musaffa/Zoya/issuer, validate denominators + purification, obtain a qualified review.
  *The most important non-engineering gate; schedule independent of the engineering tracks.*

## Open decisions

**Resolved (founder + review round #5):**
1. ✅ **Live broker:** Alpaca for the autonomous US paper→micro-live path; `ManualBroker` (Sahm) for the
   real Saudi/US-ETF account (no API); IBKR deferred to Phase 2. (S13 + `CAMEL_BROKER_MATRIX.md`.)
2. ✅ **Notification channel:** Telegram (bidirectional approve/veto, free).
3. ✅ **First Entrepreneur product:** Arabic complaint/SLA assistant for Saudi travel/hospitality —
   **validated** (the founder works full-time in travel-tech). Built behind the S7 gate, human approval
   on every launch/spend; agent scope = code-gen only.
4. ✅ **Canonical Sharia screener:** Musaffa primary, Zoya cross-check (S9 cross-check).
7. ✅ **DCA ladder:** ETFs only until Edge Proof passes for individual equities.
8. ✅ **`congress_signal`:** delayed to post-Edge-Lab (S11 "delay" list), signal-only, never blind copy.
9. ✅ **Default benchmark:** SPUS primary, HLAL secondary, Cash + DCA as controls.
10. ✅ **Markets:** US → Saudi → EGX (EGX a later S8 connector, not a P0).

**Still open (founder to set values):**
5. Starting limit values in `config/limits.yaml` — recommend **starting at ~50% of documented values**
   (paper passes don't prove live behaviour; scale up after ~60 clean live days). Beginner-mode profile
   (S6.6) is the conservative default for the real small account.
6. Capital bucket percentages (S4 Budget Kernel) — reviewer suggestion given the unproven edge:
   Core 60 / Trader 10 / Entrepreneur 15 / System 5 / Emergency 10. Founder to confirm.
11. Capital path to the $10K Camel Fund (savings / income / Entrepreneur revenue) — affects pace, not architecture.

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
- **No trade proceeds without an EdgeReport** (v0 from S4.5; full 17-check engine from S10). This gate must
  hold in the **assembled loop** (Workstream A1), not only in the `Allocator` unit.
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
