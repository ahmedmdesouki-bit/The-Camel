# CAMEL CHANGELOG — sprint & decision history

> **Canonical home for what happened when.** Derived from git history; one entry per
> meaningful change. Newest first.

---

## 2026-06-07 — Data-sourcing second pass (historical + news emphasis) + live capability confirmed

**Confirmed live data-pull capability** (direct test): Fed RSS press releases ✅ and Yahoo SPY series ✅ pulled
clean; SEC 403'd a generic user-agent and GDELT 429'd under load — the friction that justifies the
`SourceConnector` framework (descriptive UA, retry/backoff, recorded fixtures, sanitization). "Real-time charts"
= we pull the underlying real-time *series* (Alpaca IEX + Finnhub websockets) and render our own (Dashboard v2);
we never scrape rendered charts (guardrail: no raw web text to the LLM).

**Ran a 4-category data-source search** (parallel verified research: historical · news · geopolitical ·
trends/reactions) and **expanded `CAMEL_DATA_SOURCES.md`** with an **operating plan**: a decision→data map, a
**tiered ingestion plan (T0 decision-critical core / T1 quorum cross-check / T2 paid phase-in / T3 reference-
only)** that honors the founder directive *"don't exhaust the system — ingest a lean core + one cross-check, not
everything,"* expanded rosters for the **historical** and **news** pillars, quorum pairs per category, and
operational flags. Roughly **doubled the free options per category.**

**Two roadmap gaps now have FREE answers:** (1) the **USD/SAR peg monitor** activates via **FRED `DEXSAUS`** —
the FRED connector already exists, so $0 → wired into the S9 slice-4 plan; (2) the **`event_reactions` substrate**
(S9 slice 3) is buildable free from FRED/ALFRED + Finnhub surprises + CFTC COT + Kenneth French factors.

**New free anchors added to the S8 backlog (prioritized):** SEC RSS, Finnhub (EPS surprise + WS), CFTC COT,
Kenneth French, CBOE/FRED stress, **IMF PortWatch** (chokepoint shipping — high value for a Gulf book), GPR/EPU,
OFAC + **UK Sanctions List**, Marketaux, OpenSanctions, **SAHMK** (free Tadawul-licensed). **Operational flags:**
🔴 OFSI list closed 28-Jan-2026 → use UKSL; UCDP API now needs a free token; OpenSanctions free non-commercial
only; **MENA has no native clean gov/exchange news API (Egypt weakest) — route via licensed APIs + sanitize.**
Also queued: **connector-base hardening** (retry/backoff + UA discipline). Docs-only; suite stays 440 green.

---

## 2026-06-07 — S10.5 promoted to a dedicated sprint (founder-agreed)

Following the sanity-check finding, the founder agreed to treat the **operator-loop assembly** as its own
focused effort rather than letting the wiring ride implicitly inside other sprints. **Workstreams A + B are now
a numbered sprint, `S10.5 — Operator-Loop Assembly + Runtime Automation`**, inserted at the S10→S11 boundary
(sequence + summary table updated in `CAMEL_ROADMAP.md` and `CLAUDE.md`). It assembles the §4 loop around the
real S10 Edge-Proof gate **before** S11 strategies start flowing trades through it. Headline deliverable / gate:
an end-to-end paper tick runs through the *assembled* loop and **a buy with no passing EdgeReport is rejected by
the assembled loop (not just the Allocator unit) — closing the Phase-1 blocker (A1)**; plus real Task-Scheduler
entrypoints for the daily ops/brief + weekly safety jobs. Still paper, no live capital. No code yet (planning).

---

## 2026-06-07 — Full project sanity check (docs + code sweep)

**Ran a comprehensive project audit** (three parallel review passes over the whole tree: deferred/backlog
markers, doc consistency, and built-but-not-wired code). **Conclusion: the sprint plan had not silently dropped
anything major** — but the sweep surfaced one structural gap and a layer of doc drift, all now corrected/tracked.

**Added to the roadmap — new "Workstreams & Backlog" section** (top of `CAMEL_ROADMAP.md`):
- **Workstream A — Operator-loop assembly (the structural finding).** The components (Router, Edge-Proof
  `Allocator`, Budget Kernel, Operator-OS state machine, regime engine, peg, dashboard, brief, ops jobs) are
  all built + unit-tested, but `loop/scheduler.py` runs with no-op callbacks, so the §4 loop is never assembled
  at runtime. **A1 (wire the Edge-Proof gate into the assembled loop) is a Phase-1 BLOCKER** — harmless today
  only because nothing trades in Phase 0. Now a hard gate in S13 live-readiness.
- **Workstream B — scheduled entrypoints** for weekly checks / heartbeat / dead-man / dashboard render /
  founder brief (only the daily loop + kill-switch currently have `__main__`).
- **Workstream C — founder tools** (Dashboard v2 done; `camel-coach` read-only skill still to build).
- **Workstream D — connector ingestion orchestration** + the parked S8 connector backlog + a **new USD/SAR FX
  feed** to activate the peg monitor.
- **Backlog**: Alaa items mapped into S11/S13 sprint bodies; health-monitor cpu/mem/broker/telegram checks
  (add `psutil`); `data/quality.py` refinement (→ S8 cont.); plus the already-owned S12 write-atomicity, S8
  earnings blackout, S13 cancel/replace, Phase-2 IBKR.

**Doc drift corrected in place:**
- **AAOIFI thresholds** in `CAMEL_CONSTITUTION.md` updated from the loose 33% (Dow-Jones-style) to the verified
  AAOIFI spec (≤30% / ≤30% / ≤67% / ≤5% + 11 sectors; 12-mo-avg-mktcap denominator), with enforcement noted at
  S9 slice 4. (Sharia is #1 in the hierarchy — the canonical rules doc must be right.)
- **`CLAUDE.md` repo map** marked `strategies/`, `learning/`, `loop/intraday_monitor.py`,
  `data/congress_filings.py` as ⏳ PLANNED (S11) — they were listed as if on disk but don't exist yet.
- **Stale test counts → 440** (README run-example, CONSULTANT_HANDOFF ×3, TESTING "current suite", roadmap S9
  status). **Sprint statuses** fixed: "S9 slice 1" → "slices 1–2", "S8 slice 1" → core (slices 1–5).
- **DB stub status** corrected (macro/fundamentals/news now Live/real, learning no longer "unused") across
  DATA_CONTRACTS, HANDOFF, CONSULTANT_HANDOFF, and `db/paths.py` comments.
- **Cross-refs**: full Edge-Proof engine "S7 / 13-check" → **S10 / 17-check** (roadmap ×2 + LIVE_READINESS);
  live-readiness sprint "S11" → **S13**; added MACHINE_HARDENING + ALAA_REVIEW + CONSULTANT_HANDOFF to the
  `docs/README.md` index; CONSULTANT_HANDOFF "see §13" → §15.

No code changed in this pass (docs only); suite stays **440 green**.

---

## 2026-06-07 — More Alaa harvest shipped (founder alerting + peg monitor)

**Built the next batch of self-contained Alaa-harvested items as real, tested code** (the rest stay scheduled
at their sprints): (1) `alerts/whatsapp.py` — **WhatsApp/CallMeBot** 2nd alert channel, same credential-safe
stub contract as Telegram (no network in tests); (2) `alerts/redalert.py` — the **RED ALERT founder-panic
protocol** (breathe→assess→act; informational only — never places/blocks/proposes a trade); (3) `alerts/brief.py`
— a **founder daily brief** built from the dashboard snapshot (single source of truth), deliverable over
Telegram *or* WhatsApp, appending RED ALERT on a >3% drop; (4) `trader/regime/peg.py` — the **SAR/USD peg
monitor** (pure `peg_status` + dormant-safe `latest_peg_status`, for the S9 regime layer). Plus the cash-drag
ratio already shipped inside Dashboard v2. `tests/test_alerts_founder.py` (9) + `tests/test_peg_monitor.py` (5).
**426 → 440 tests green.** **Deferred (on purpose):** the sector-cap ≤40% guardrail → S11 (needs the portfolio
engine + per-holding sector aggregation to be meaningful; won't half-wire a guardrail). Remaining Alaa items
(strategy-fit selector/mix UX, OCR manual entry, eval harness, camel-coach skill, yield-on-cost, moat matrix)
stay scheduled at S11/S12.5/S13.

---

## 2026-06-06 — Feedback session wrap

**Dashboard v2 SHIPPED (first code out of the feedback session).** Rebuilt the S6 operator dashboard taking
Alaa's interactive single-file dashboard as the *visual ground*, then enhanced it heavily and re-pointed it at
**our governed state**. New `dashboard/snapshot.py` (pure, JSON-serializable snapshot from the 7 SQLite DBs)
+ rewritten `dashboard/generate.py` (rich, tabbed, **CSS-only / zero-JS**, fully offline & read-only HTML:
Overview · Portfolio · **Decisions** · Regime · Sharia · Ops). Unlike a portfolio tracker (or Alaa's), it
surfaces **Edge-Proof verdicts + Constitution rejections-with-reasons**, the macro regime, and an *honest*
live-money safety posture (real booleans, not a self-scored X/10). Server-side render = no CORS proxy, no
localStorage-as-truth, no live fetch, every value HTML-escaped (XSS-safe), CSS-only tabs (no `<script>` to
inject through). Early delivery of the **S10 decision-quality dashboard**. `tests/test_dashboard_snapshot.py`
(7 tests). **419 → 426 tests green.** Decisions logged: kept SQLite + server-render spine (declined Alaa's
CORS-proxy/localStorage approach); kept full-AAOIFI (declined his debt÷assets<33%).

**Feedback session closed.** Inputs folded this session: consultant round #7 (portfolio/strategy/data/research
expansion) → roadmap S9–S12.5; deep-research report second-pass (Edge-Proof bundle, promotion ladder,
event-driven scheduling, dividend 4-stage) → roadmap + `docs/CAMEL_DATA_SOURCES.md`; Alaa cross-build review
→ `docs/CAMEL_ALAA_REVIEW.md` + roadmap harvest + Dashboard v2. All docs/memory synced; pushed to `main`.
**Next:** resume the build queue — S9 slice 3 (event intelligence over `news_events`) → S9 slice 4 (Sharia
cross-check, multi-state + AAOIFI ratios) to close S9; then S10.

---

## 2026-06-06

**Cross-build review — Alaa's parallel Camel (founder-facing layer) reviewed file-by-file + harvested
(docs-only).** A friend's Camel that built the *cockpit + coach* (interactive dashboard, packaged
`camel-coach` Claude skill, daily-brief script, OCR manual entry) to our *engine + rails*. Same vocabulary,
no enforcement layer — independent validation of the framing. Full review → `docs/CAMEL_ALAA_REVIEW.md`.
**Adopted/folded:** RED-ALERT founder-panic protocol (→ Constitution human-factors + S13 gate + daily brief);
screenshot-OCR manual entry (→ S13 ManualBroker + broker matrix); strategy-fit selector + fit-metadata (→ S11
registry); strategy "mix" coherence UX (→ S11 matrix rendering); his interactive dashboard as the S10/S11 UI
starting point (re-wired to our DBs, must surface rejections-with-reasons); WhatsApp/CallMeBot 2nd alert
channel + brief format (→ S6); LLM-output eval harness (→ S12.5 + coach skill); a founder-tools `camel-coach`
skill (read-only, proposes-never-executes); frameworks: cash-drag ratio, yield-on-cost, moat matrix, sector
cap ≤40% incl. ETF look-through, SAR/USD-peg monitor. **Declined:** his looser debt÷assets<33% Sharia screen
(keep full AAOIFI), hardcoded analysis data, no-enforcement posture, localStorage, Yahoo/stooq as
decision-grade. No code; 419 tests unchanged.

---

## 2026-06-06

**Consultant review round #7 (portfolio/strategy/data/research-agent expansion) folded (docs-only).** Two
consultant docs that *independently validated* the architecture we'd already built/planned (~70% already
done or folded). **Adopted (5 additive items):**
- **Event-reaction engine** (`event_reactions` table: return_1d/5d/21d/63d, excess-vs-benchmark, regime-at-event)
  → S9, the point-in-time substrate for S10 signal-conditioned event studies.
- **Dividend mechanics** (gross/withheld/net; ex-date 25%-special deferral + due-bills; settle-date; corporate
  actions as ledger events; **lot-level** accounting) → S11/S12. **Tax frame corrected to NRA-withholding**
  (founder is KSA-resident; the US qualified-dividend 60-day rule is N/A — model gross→withholding→net).
- **Portfolio lifecycle** (incubate→…→retire), tolerance-band rebalancing, 4-level risk budgets, multi-benchmark
  (policy/opportunity/cash), the **6 seed portfolios** + strategy-portfolio matrix + the consultant SQL schemas → S11.
- **Acceptance checklist** (15 items) → S11 definition-of-done.
- **Fuller research-agent roster** (adds market-microstructure + execution/TCA) + the **evidence-object contract** → S12.5.
**Declined / corrected (founder-agreed push-backs):**
- **Vendor cost:** declined the Polygon/Massive-Advanced-as-primary ($199/mo) and $400–$2,000/mo stack — the
  free-first path (Alpaca/Finnhub free + SEC EDGAR + EODHD ~$20) in `CAMEL_DATA_SOURCES.md` holds for a personal book.
- **Infra:** declined the near-term Postgres + Parquet/Iceberg lakehouse + feature-store migration — SQLite stays;
  migrate only when multi-device/scale genuinely demands it (we ingest *structured events*, not GDELT's raw firehose).
- **Tax:** corrected the US-person qualified-dividend assumption to NRA withholding (see above).
*Their stale sprint numbering (S5.6–S7) mapped onto our v3; "S5.6 hotfix" = our shipped S6.5. No code; 419 tests unchanged.*

**Second-pass re-read of the deep-research report (`docs/source-materials/CONSULTANT_DEEP_RESEARCH_2026-06-06.md`,
now archived).** Caught 3 additive items round #7 had missed, folded docs-only: (1) **composable per-decision
Edge-Proof bundle** + the worked **dividend-sleeve example (9 checks)** → S10; (2) **per-strategy promotion
ladder** (backtest→realistic_paper→shadow→live_small→live_scale, one rung at a time, failure demotes not
deletes — distinct from the portfolio lifecycle) → S11 registry `mode`; (3) **event-driven scheduling** by
`(portfolio_id, strategy_id, event_window)` tuples for N-portfolio scale → S11. Plus named the **dividend
4-stage pipeline** (announcement→entitlement→settlement→attribution). Report saved as memory
(`camel_consultant_deep_research.md`). No code; 419 tests unchanged.

---

## 2026-06-06

**Follow-up data research — two gaps RESOLVED (direct web verification).** The follow-up deep-research
*workflow failed* on a harness/schema error, so the two gaps were closed by direct web search + primary-source
fetches:
- **Streaming (S8.5) resolved → Alpaca IEX websocket (primary) + Finnhub free websocket (cross-check, ≤50
  symbols)** — both true real-time, both **free**, monitoring-only fit, no new paid spend. Polygon real-time is
  $199/mo (skip); Twelve Data/Tiingo not suited to free streaming.
- **Sahm-API verdict (the key question): Sahm has a usable DATA API but NO execution API.** The SAHMK Developers
  API is market-data only (REST + realtime websocket on Pro+ + historical + financials; `X-API-Key`); no order
  endpoints → **manual execution for Sahm stands** (broker matrix updated). Bonus: it's a genuine **Tadawul
  (Saudi) data source** (free 100 req/day; $149/mo). **Egypt (EGX) data → EODHD** (279 tickers, EOD + fundamentals,
  $19.99+). Execution for Saudi *and* Egypt remains manual (no retail execution API found).
- Folded into S8.5 (streaming pick), the broker matrix (Sahm verdict + Saudi data path), and `CAMEL_DATA_SOURCES.md`.

---

**Data-resource deep research → `docs/CAMEL_DATA_SOURCES.md` (cited catalogue).** Deep-research pass
(5 angles, 25 sources fetched, 96 claims, **25 adversarially verified 3-0 / 0 killed**). Outcome:
- **Validated the free/official picks already built** — SEC EDGAR XBRL (no key; UA + ~10 req/s required),
  FRED/ALFRED + Treasury/World Bank/BLS/BEA/EIA, GDELT, ACLED — these were the right anchors.
- **⭐ Got the exact AAOIFI ratio spec** (from the FTSE/IdealRatings Islamic-index methodology) to implement
  in the **S9 Sharia cross-check**: debt ÷ 12-mo-avg mkt-cap ≤30%; (cash+deposits+interest-investments) ÷
  12-mo-avg mkt-cap ≤30%; (cash+deposits+receivables) ÷ total assets ≤67%; non-compliant rev + interest income
  ≤5%; 11 prohibited sectors. **Zoya** = configurable cross-check (note: Zoya uses plain mkt-cap, AAOIFI uses 12-mo avg).
- **Paid, phased:** EODHD (fundamentals cross-check + dividends/splits → powers `dividend_growth`); Sharadar/
  Nasdaq Data Link (survivorship-free point-in-time → for the S12 Edge Lab); Benzinga (affordable structured
  news); RavenPack deferred (enterprise). yfinance/Stooq flagged prototyping-only.
- **Two gaps → follow-up searches:** (a) real-time/**streaming** vendors for S8.5 (Alpaca/Polygon/Tiingo/Twelve
  Data — none confirmed yet); (b) **Tadawul/EGX** coverage — **lead: `sahmk.sa/en/developers` suggests Sahm may
  expose an API**, which would revise the "Sahm = manual-only" broker assumption. Both need a dedicated pass.
- Caveats: only a subset verified in depth; pricing volatile; licensing/storage terms for paid vendors NOT confirmed.

---

## 2026-06-06

**Founder direction folded into the roadmap (docs-only; no code).** Four additions + a data goal:
- **Portfolio Engine** (multi-portfolio, strategy-per-portfolio) → folded into **S11**: `portfolios` table,
  `PortfolioManager`, portfolio-scoped positions/ledger reconciling to the fund, fund-level caps above
  per-portfolio caps. Trust inversion unchanged (gates run per portfolio).
- **Real-Time Data Tier** → new **S8.5**: streaming quotes (Alpaca IEX websocket), live-news polling through
  the sanitiser, a real-time monitor/charts + alerts. Scope is **ingestion + monitoring**; a live feed is
  monitoring-only unless corroborated (quorum ≥2); **execution stays EOD** (Sahm/positional) — real-time
  execution is a separate Phase-2+ call. (Founder chose to add the streaming tier now.)
- **Research Desk / Analyst Agents** → new **S12.5**: per-vertical agents (macro/sector/single-name/
  geopolitics/Sharia/strategy) that study→analyze→store evidence via the Claude Agent SDK. **Designed now,
  kept dormant** (master switch OFF, token budget) until capital/edge justify the spend — founder decision.
  Agents propose/analyze, never decide.
- **Dividends** → a dividends/corporate-actions connector (S8 backlog) + a `dividend_growth` strategy (S11,
  Sharia-screened quality income; *not* dividend-capture, which the Edge Proof will likely reject).
- **Many independent sources per data category, cross-checked** (source quorum ≥2) — reaffirmed S8 goal.
- **Agreed next task:** a cited data-resource research pass (best historical/news/geopolitical/market-reaction
  feeds, free + paid) to choose the specific connectors.

---

## 2026-06-06

**QA/QC hardening pass (independent line-by-line review of S6.5→S9) — 409 → 419 tests green.** An
independent review audited every new module; the real findings were fixed, each with a regression test
(`tests/test_qa_hardening.py`):
- **Regime `_yoy` was month-over-month, not year-over-year** (HIGH) — now matches the observation closest to
  exactly 1 year back (±60d) or returns None; wrong inflation/commodity inputs no longer misclassify regime.
- **Regime feature builder ignored data vintages → look-ahead** (HIGH) — `_points` now filters
  `reported_at <= as_of` and keeps the latest vintage per `event_date` (point-in-time honest).
- **Connector base `_stamp` fabricated `event_date` for dateless records** (HIGH) — it no longer invents a
  date; a record the parser couldn't date is dropped as unprovenanced (also fixes a UNIQUE-key collapse).
- **BLS `M13` (annual average) produced month-13 dates** → mapped to year-end; month validated 1–12.
- **Unguarded `float()` in fred/treasury/world_bank/bls** — one bad value aborted a whole run; now skips
  the bad row. World Bank `None-12-31` date guarded. EIA quarterly periods mapped to quarter-end.
- **`register_asset` silently un-delisted assets** on a partial update (survivorship) — `delisted` is now
  tri-state (None = leave untouched) with COALESCE.
- **Beginner-mode "only-tightens" guarantee** now validates against the full `DEFAULT_LIMITS` (rolling +
  illiquidity rails) and the cash-buffer tiers, not just the YAML.
- **Sanitiser injection match** now runs on whitespace/markdown-collapsed text ("ignore   previous" no
  longer slips through). *(Homoglyph/zero-width evasion noted for a future hardening.)*
- **ETF `netassets` weight-alias** dropped (could capture a dollar-AUM column).
- **Regime classifier tie-break** is now an explicit risk-first priority, not insertion order.
- **Deferred (documented backlog):** `broker/paper.py` writes orders + ledger + positions in three
  separate transactions with no positions↔ledger reconcile — acceptable for Phase-0 single-process, but
  a single-transaction submit + a positions reconcile is added to the **S12** backlog (realistic execution).

---

## 2026-06-06

**Sprint 9 (Knowledge Graph + Regime Engine) — slice 2 (Regime Engine) — 395 → 409 tests green.** New
`trader/regime/` package: `features.py` builds point-in-time macro features from `macro_observations`
(fed funds, 10y−2y curve, CPI YoY, unemployment, HY spread, VIX, USD, oil YoY); `classifier.py` is a
deterministic signal-scored 10-state classifier (LIQUIDITY_EXPANSION/TIGHTENING, INFLATION_SHOCK,
DISINFLATION_GROWTH, RECESSION_RISK, RECOVERY, COMMODITY_SUPPLY_SHOCK, GEOPOLITICAL_RISK_OFF,
AI_CAPEX_BOOM, USD_STRENGTH_EM_PRESSURE) → regime + confidence + the signals that fired, plus a
`regime_to_themes` mapper; `history.py` + a `regime_history` audit table persist each call. v0 covers the
macro-derivable regimes; AI_CAPEX_BOOM and a confident RECOVERY need equity-sector signals (later). The
LLM never decides the regime. `tests/test_regime.py`.

---

**Sprint 9 (Knowledge Graph + Regime Engine) — slice 1 (entity resolution) — 389 → 395 tests green.**
New `assets` table (ticker ↔ CIK ↔ ISIN ↔ CUSIP ↔ name ↔ sector, `active_from/to`, `delisted_flag` for
survivorship control) in the fundamentals DB, and `data/entity_resolver.py`: `resolve(ticker)` returns a
`ResolvedAsset` by joining `assets` (identity) + `company_facts` (latest SEC filing) + `etf_holdings` (which
compliant ETFs hold the name — single-name look-through) + the Sharia whitelist (status/frozen). `register_asset`
upserts identity (COALESCE so partial updates don't wipe fields). Delivers the gate's identity half. Remaining
S9: Regime Engine (classifier over macro_observations), event intelligence (over news_events), Sharia
cross-check + multi-state status. Also: S8 connector remainder formally deferred to a backlog (founder decision).

---

## 2026-06-06

**Sprint 8 (Data Intelligence Backbone) — slices 1–5 — 352 → 389 tests green.** The long pole begins.
*Slice 5:* `data/connectors/etf_holdings.py` — Sharia-ETF issuer holdings (SPUS/HLAL/MNZL) from CSV →
`camel_sharia.db.etf_holdings`, so the portfolio can look *through* an ETF to its single-name exposure
(feeds S9). Header-tolerant (case/space-insensitive alias matching across issuer layouts); `parse_csv`
added to the connector base (stdlib `csv`, no pandas). **10 connectors live.**
*Slice 4:* `bea.py` (BEA GDP/income) + `eia.py` (EIA energy) → macro_observations; `acled.py` (armed
conflict / protests) → news_events as structured events built only from `event_type`+`country` (free-text
`notes` never stored). **9 connectors live** (FRED, SEC, Treasury, World Bank, BLS, GDELT, BEA, EIA, ACLED).
*Slice 3 (news/events pipeline):* `data/connectors/news_base.py` (`NewsConnector` — every title runs through
the sanitiser; **injection-flagged titles are redacted, marked `safe=0`, and quality-downgraded** so the raw
hostile string never persists; only structured events land, no raw-body column) + `data/connectors/gdelt.py`
(GDELT DOC 2.0 → structured events). `db/news.py` rebuilt as a provenanced structured-event table. The
reviewers' **news-pipeline adversarial tests** in `tests/test_connectors_news.py` prove injection text is
redacted, no hostile string is persisted, and there is no raw-body column. **6 connectors live; all three
stub DBs (macro/fundamentals/news) now hold real data.**
*Slice 2:* `data/connectors/macro_base.py` (shared `MacroConnector.store` → `macro_observations`) + three
more macro connectors — `treasury.py` (Treasury Fiscal Data), `world_bank.py` (World Bank Indicators),
`bls.py` (BLS CPI/employment, with period→date mapping). FRED refactored onto the shared base.
**5 connectors live now** (FRED, SEC EDGAR, Treasury, World Bank, BLS). `tests/test_connectors_macro.py`.
- `data/provenance.py` — point-in-time provenance fields + the `source_documents` audit table +
  `assert_provenanced` (a record without full lineage is not decision-grade and is dropped).
- `data/source_registry.py` — `SourceSpec` registry (FRED + SEC EDGAR registered, free/official, tier 1).
- `data/connectors/base.py` — `SourceConnector` pipeline (fetch→parse→normalize→validate→store) with an
  **injectable transport**: stdlib `urllib` in production, a stub returning canned payloads in tests — so
  **no test hits the live web, with zero new dependencies** (the same guarantee as recorded cassettes).
- `data/connectors/fred.py` → real `macro_observations` (ALFRED vintage → honest `reported_at`);
  `data/connectors/sec_edgar.py` → real `company_facts` (filing date vs period end). Ingestion idempotent.
- `security/scraping_policy.py` — acquisition ladder (API > vendor > file > RSS > scrape > browser-QA-only);
  SEC contact-header rule.
- **PM call:** stayed **dependency-light** — deferred requests/httpx/pydantic/feedparser/vcrpy until a
  connector genuinely needs them (honors the reviewers' anti-bloat warning). **Remaining S8 slices:** the
  other ~18 free connectors, GDELT/news pipeline + adversarial tests, market-data adapter, paid vendors.

---

## 2026-06-06

**Sprint 7 (Entrepreneur Product Engine) COMPLETE — engine, 331 → 352 tests green.** The cash-flow arm,
moved earlier in v3 and tightly scoped per the reviewers. New `entrepreneur/` package, all deterministic:
- `product_gate.py` — the 17-field `ProductThesis` + `evaluate_gate` (the Entrepreneur analog of the Edge
  Proof gate). The validated lead candidate (Arabic complaint/SLA-response assistant for Saudi travel/
  hospitality) is encoded as `lead_product_thesis()` and proven through the gate end-to-end.
- `constitution.py` — a **separate** `EntrepreneurConstitution.evaluate(action)`: BUILD is **code-gen-only**
  (autonomous); DATA_COLLECT needs a privacy review; ASSET_USE needs a rights check; SPEND needs budget;
  LAUNCH needs founder approval; PUBLISH_COPY blocks unapproved legal/financial/medical claims and banned
  compliance-guarantee wording. Reuses the Trader haram-activity screen so a haram product can't be built.
- `build_pipeline.py` — a 10-stage state machine (thesis→PRD→build plan→issues→MVP→tests→staging→approval→
  production→measure). No skipping; STAGING needs passing tests; **PRODUCTION needs founder approval + a
  Constitution-allowed LAUNCH** — no autonomous production deploy, ever.
- `tests/test_entrepreneur.py`; CLAUDE.md gains Entrepreneur DO-NOT rails + repo-map entry.
- **Scope:** this is the **engine** (deterministic, in-repo, fully tested), mirroring how the Trader arm is
  a paper engine. Real Stripe/GitHub/customer-data/deploy integration is wired only when a real product
  actually ships behind these gates — a founder real-world action, not Phase 0.

---

## 2026-06-06

**Sprint 6.6 (Position Accounting + Ops Hardening + Beginner Mode) COMPLETE — 309 → 331 tests green.**
Led by review round #6's foundational item.
- `broker/positions.py` — **position accounting**: the single writer of the `positions` table, updated
  on every paper fill. BUY → create/increase + weighted-average cost; SELL → validate `qty ≤ held`,
  reduce, realize P&L `(price − avg_cost)·qty`, close at zero. `InsufficientPositionError` is the exact
  qty-based phantom guard (the broker's precise second wall behind the Constitution's value-based one).
  Wired into `PaperBroker.submit`; extended `positions` schema (market_price, realized_pnl, opened_at,
  status); positions reconcile with ledger cash.
- `db/sqlite.py` — **SQLite WAL mode** on every connection (reduce locking under concurrent r/w).
- `guardrail/constitution.py` — illiquidity gate **fails closed in live** when the data needed to clear
  it is missing (`illiquidity_data_missing`); paper still skips gracefully. *(Verified silent-skip gap.)*
- `ops/health_monitor.py` + `tests/test_health.py` — disk check is now **mocked** in tests (portability —
  a verified env-sensitive failure) and an **unknown/errored disk check degrades to YELLOW**, not GREEN.
- `ops/deadman.py` — external **dead-man's-switch** ping (network-safe stub; never raises). Pairs with the
  machine-hardening checklist (`CAMEL_DEADMAN_URL`).
- `config/beginner_mode.yaml` + `governance/beginner_mode.py` — **Beginner Mode** profile for the real
  small account; `beginner_limits()` proves it **only tightens** (raises `RailWidenedError` otherwise).
- `tests/test_adversarial.py` — **prompt-injection** tests: a "founder said ignore the Constitution"
  narrative, an "emergency" claim, and a forged `approval_id` all fail to bypass the gate.
- Docs: `docs/CAMEL_BROKER_MATRIX.md` (broker direction resolved); machine-hardening gains the NTFS
  config-lock + dead-man's-switch items.
- *Note:* review #6 was stale (S5.5/263) and its "critical S5.6 hotfix" was largely our already-shipped
  S6.5 — strong independent validation. The net-new item (position accounting) is this sprint.

---

## 2026-06-06

**External review round #5 folded into the roadmap (docs-only; no code change).** Two independent
technical reviews (one current at S6.5/309, one stale at S5.5/263). Founder decisions + adopted items:
- **New S6.6 — Ops & Safety Hardening + Beginner Mode:** illiquidity-gate fail-loud (the spread/ADV gate
  *silently skips* when data is absent — verified gap; now logs + blocks in live), prompt-injection
  adversarial tests (founder-override / emergency / data-poisoning claims), dead-man's-switch external
  ping, SQLite WAL mode, OS-level (NTFS) config immutability, beginner-mode profile (can only tighten
  rails), broker capability matrix.
- **⭐ Sandbox Mode (founder request) added to S12:** the full system on **live real-time data with
  virtual money** — the live dress rehearsal that produces the ≥28-day (90-day shadow) track record
  gating micro-live. Plus **shadow vs enforcing** Edge Proof modes (S10) for calibration.
- **"No-Edge Found" protocol (both reviews):** if the Edge Lab finds no defensible edge, the
  pre-registered fallback is scheduled DCA into SPUS/HLAL and Phase 1 does not proceed — a success state,
  not a failure. Thresholds pre-registered before the lab runs; Sharia-drag quantified (S12).
- **Markets US → Saudi → EGX (founder):** EGX is a *later* S8 connector, **not** a P0. Declined the
  reviewer's EGX-first restructure of S7 (it's the reviewer's home market, not the founder's primary one)
  and the SaaS-for-the-masses items (beginner-for-millions, multi-founder, open-source/enterprise) — they
  collide with the locked personal-use-only constraint.
- **Entrepreneur stays at S7 (founder)** but with the reviewers' concern adopted: **agent autonomous scope
  = code-generation only**; customer discovery, pricing, payments, launch, and spend need founder approval.
- **Broker resolved:** Alpaca (autonomous US path) + `ManualBroker` (Sahm, manual-entry for the real
  no-API account) + IBKR deferred to Phase 2; documented in a broker matrix. Sharia drift detection +
  local-board override (AAOIFI default) added to S9. News-pipeline adversarial tests added to S8.

---

## 2026-06-06

**Sprint 6.5 (Safety & Accounting Hotfix) COMPLETE — 289 → 309 tests green.** First code sprint
of Roadmap v3.
- `guardrail/constitution.py` — **phantom-sell guard** (reject a sell with no holdings →
  `no_holdings`, or a sell exceeding held value → `oversell`) and **close-only/reduce-only exits**:
  a frozen or non-compliant holding may now be SOLD to de-risk but never bought/increased (frozen/
  non-compliant *buys* still reject). Off-whitelist names are rejected on both sides.
- `capital/allocator.py` — `require_edge` now defaults to `None`, resolving to **True for a market
  buy/increase and False for a reduce-only/close (sell) or non-trade action**. Opening a position
  needs proven edge; de-risking does not.
- `broker/paper.py` — the legacy **$1 fallback price is refused by default**: `submit` raises
  `NoMarketPriceError` when no validated close exists. Unit tests opt in via
  `allow_fallback_price=True`, and such fills are stamped `fill_model="fallback_dollar"` so no
  performance number can come from a fabricated fill.
- New gate suite `tests/test_s6_5_safety.py`; existing allocator/broker/guardrail tests updated for
  the tightened defaults (Constitution-isolation calls pass `require_edge=False`).
- Deferred to S12 by dependency: a precise *share-level* phantom check at the broker (arrives with
  realistic execution). S6.5 uses the deterministic value-based guard in the Constitution, which
  covers both the allocator path and the direct-`evaluate` loop path.

---

## 2026-06-06

**Roadmap v3 — research-driven restructure (docs-only; no code change).**
Folded two approved feedback documents (Power Maximization Proposal v2 + a data-source deep-research
report) into the canonical roadmap. Founder decisions adopted in full:
- **Entrepreneur arm moved earlier** (was S9 → now **S7**) — cash flow + learning before the
  trading-data build. Validated by the founder's full-time travel-tech day job, making the lead
  product (Arabic complaint/SLA-response assistant for Saudi travel/hospitality) a real domain fit
  rather than a guess. Recorded in `CAMEL_BRIEF.md §2`.
- **New S6.5 Safety & Accounting hotfix** — no phantom sells, close-only/reduce-only for
  frozen/non-compliant holdings, Edge Proof mandatory for buy/increase, no $1 fallback price
  outside unit tests.
- **New S8 Data Intelligence Backbone** — `SourceConnector` framework + **top-20 source connectors**
  (free/official first: SEC EDGAR/XBRL/RSS, FRED + **ALFRED vintage**, BLS, BEA, Treasury, World
  Bank Pink Sheet, EIA, USGS, GDELT, ACLED, GPR, EPU, OFAC, congress/senate disclosures, ETF
  issuer holdings, Kenneth French) with full provenance + point-in-time enforcement and
  recorded-fixture (vcrpy) tests; **paid vendors phased into the plan** (EODHD, Polygon, Norgate,
  Nasdaq/Sharadar, Quiver, Zoya/Musaffa, CRSP). Adds a scraping policy (API > vendor > file > RSS >
  scrape > browser-QA-only) and fills the stub macro/fundamentals/news DBs.
- **New S9 Knowledge Graph + Regime Engine** — entity resolution (ticker↔CIK↔ISIN↔CUSIP),
  ETF look-through, structured event intelligence, a 10-state regime classifier from real macro,
  and a Sharia cross-check with multi-state status (pass/fail/doubtful/frozen/pending_review;
  disagreement → freeze new buys, allow reduce-only).
- **Edge Proof upgraded to 17 checks, signal-conditioned** (was S7 → now **S10**) — adds
  survivorship control, similar-regime filtering, multiple-testing penalty, and signal-decay
  testing; minimum thresholds + model-disagreement → human gate.
- **Strategy Registry trio refreshed** (was S8 → now **S11**): `core_dca`, `quality_momentum`,
  `etf_regime_rotation` (rotation only if it beats DCA after costs); congress/mean-reversion/
  intraday/ML deferred to post-Edge-Lab.
- **Edge Lab gains realistic paper execution** (was S10 → now **S12**) — `loop_test` vs
  `realistic_paper` (limit-only, spread/slippage/partial-fill, market hours, corporate actions;
  no perf number from a fallback fill), delisted handling, and a two-engine (vectorized +
  event-driven) cross-check.
- **Decision-quality dashboard** added to S10 (extends the S6 state dashboard): current regime,
  active strategy, **signals rejected this cycle + the exact reason**, beating SPUS/DCA/cash, edge
  decay, data freshness + quorum. Surfaces *why*, not just *what* — the rejections are the point.
- Micro-Live → **S13**, Module Restructure → **S14**. Sequence is now S1–S14.
- Net principle reaffirmed: **build the data supply chain before the proof engine; optimize for
  evidence density, not feature count.** No code written this entry — roadmap + CLAUDE.md +
  BRIEF cross-references renumbered to match.

---

## 2026-06-06

**Sprint 6 (Dashboard + Monitoring) COMPLETE — code, 263 → 289 tests green.**
- `dashboard/generate.py` — read-only HTML view (status, positions, ledger, runs, guardrail
  events, Sharia flags); HTML-escaped; no order entry.
- `alerts/` — credential-safe Telegram adapter (STUB mode with no token, never hits the
  network in tests) + daily-report delivery.
- `ops/` — heartbeat (single-row), log_rotation, secrets_manager (`enforce_startup(strict)`
  RAISES on plaintext secrets), reconciliation_report, archive (off-box zip), scheduled_checks
  (weekly kill-switch self-test + verified backup + reconcile, logged to op_log). New
  `heartbeat` table in db/portfolio.py.
- `docs/CAMEL_MACHINE_HARDENING.md` — the founder-only machine checklist (Tailscale, BitLocker,
  dedicated user, UPS, MFA, secrets migration, encrypted off-box backup).
- A test fixture initially matched the secrets-leak scanner's own pattern — the scanner caught
  it (working as intended); fixture de-shaped.

---

## 2026-06-06

**Sprint 5.5 (Minimal Ops Visibility) COMPLETE — 253 → 263 tests green.**
- `ops/daily_report.py` — assembles the GREEN/YELLOW/RED/BLACK status + live counts into the
  founder daily report (console/text; Telegram delivery in S6).
- `ops/kill_switch_test.py` — runnable self-test: halted → loop tick does not run (no run row),
  resumed → loop completes. (S6 schedules it weekly.)
- `ops/secrets_check.py` — startup scan; warns when a sensitive key is a real plaintext env
  var (hard refusal arrives with the secrets manager in S6).
- `ops/backup.py` — verified (SHA-256) local backup + restore of all seven DBs; a silent
  partial copy fails verification. (Off-box encrypted backup is S6.)

---

## 2026-06-06

**Sprint 5 (Operator OS) COMPLETE — 217 → 253 tests green.**
New `operator_os/` package — **named `operator_os` not `operator` to avoid shadowing the
Python stdlib `operator` module** (a real collision that would break dependencies). Contents:
- `state_machine.py` — 11 states with enforced transitions (can't jump FORMING_THESIS→ACTING;
  ACTING only from AWAITING_APPROVAL; leaving PAUSED needs founder approval; KILLED terminal).
- `opportunity_router.py` — 5 paths; conservative gates (safety→System improvement, missing
  data→Research, no capital→Wait); cannot recommend Trader without a passing Edge Proof.
- `task_queue.py`, `learning_ledger.py`, `op_log.py` — persistent intent, shared learning
  memory (both arms), append-only operator log. New `tasks` + `op_log` tables in db/portfolio.py.
- `ops/health_monitor.py` — real DB/disk/kill-switch checks + GREEN/YELLOW/RED/BLACK status
  classifier and the daily-report text (the classifier is an S5.5 item, landed early here).

---

## 2026-06-06

**Sprint 4.5 (Edge Proof v0) COMPLETE — 197 → 217 tests green.**
`engine/edge_proof_v0.py`: forward-return distribution + hit rate + benchmark excess from
`camel_market.db`; every missing/weak/stale input defaults to `trade_allowed=false`. `gate()`
wired into `Allocator.request(..., edge_report=, require_edge=)` — with `require_edge=True`, a
trade with no/failing EdgeReport is rejected (`no_edge_proof`) before the Constitution.
Backward compatible with S3 allocator calls; decisions log to the learning ledger.
*Process note:* the S4 merge first failed for lack of a git identity (now set repo-local);
the unmerged branch's safe-delete was refused, so nothing was lost — recovered and merged cleanly.

---

## 2026-06-06

**Sprint 4 (Hardening) COMPLETE — 110 → 197 tests green.**
Three increments:
- *S4a* — Constitution hardening: kill-switch now checked inside `evaluate()` (no bypass),
  rolling velocity stops (5d/14d) + cooldown, orders-per-day cap, illiquidity/slippage gate
  (skips when data absent). Guardrail file → 43 tests (≥40 gate met).
- *S4b* — new modules: config_guard (proves rule #7), Tool Permission Matrix, Budget Kernel,
  data freshness / quality / sanitiser, source allowlist, Playwright stub.
- *S4c* — point-in-time columns (event/reported/ingested/known), broker idempotency
  (client_order_id + DuplicateOrderException), full ThesisCard template + is_trade_ready,
  secrets-leak tests, consolidated 8-case adversarial suite.
Deferred by dependency: max cancel/replace → S11 (LiveBroker); earnings blackout → S7. *(Superseded under
Roadmap v3 — these now map to **S13** (cancel/replace, with LiveBroker) and **S8** (earnings blackout, needs
the earnings calendar). The canonical owners are in `CAMEL_ROADMAP.md`.)*
*Awaiting founder approval to merge `s4-hardening` → master (branch-workflow convention).*

---

## 2026-06-06

**QA/QC pass — fixed 4 findings + the minors. 110 tests green.**
- **Ledger sign convention (real bug):** PaperBroker recorded BUY as positive (deployed)
  while the ledger is a cash account (DEPOSIT positive). Fixed to BUY = cash out (negative),
  SELL = cash in (positive) so the ledger reconciles against a broker cash statement. Updated
  the two test_broker assertions to match.
- **Dead/divergent schema:** removed the unused `init_db` + stale DDL from `db/sqlite.py`
  (it lacked the extended columns). Schema now has one home: the per-domain `db/*.py` modules.
- **append_entry docstring** corrected (it claimed a RuntimeError it never raised).
- **Duplicated DDL:** added "canonical: db/portfolio.py" comments to the defensive
  `_ensure_table` helpers in writer/state/broker.
- **Minors:** unified all DB access on a single closing, Row-factory `connection()` context
  manager (was a mix of a non-closing helper and raw `sqlite3.connect` — fixes both the
  connection leak and the helper inconsistency). Added a `simulated_unrealistic` execution
  marker to paper fills.

---

## 2026-06-06

**Consolidation: one source of truth, clean repo.**
Folded `Camel_Project_Brief.md` → `docs/CAMEL_BRIEF.md` (canonical "why/who" doc: founder
constraints, real capital ~$126 + $100/mo, $10K target, origin, open questions). Added a
top-level `README.md` entry point. Archived all legacy source docs (the original PRDs & specs,
StockSense playbook/dashboard/tracker generator) to `docs/source-materials/` via git-tracked
renames (history preserved, nothing deleted). Removed junk (a pytest cache dir, stale
placeholder, stray zip) and gitignored transients. Root now holds only code + the canonical
entry docs. 110 tests green.

---

## 2026-06-05

**Docs: 9-document split with canonical-source discipline.**
Split the monolithic spec into purpose-built docs (README index, CONSTITUTION, ROADMAP,
DATA_CONTRACTS, TESTING, LIVE_READINESS, CHANGELOG + existing HANDOFF + CLAUDE). Each topic
has exactly one canonical home; CLAUDE.md trimmed to operating manual + index. Regenerated
the Downloads dossier with clean UTF-8 (fixed a PowerShell encoding bug).

**Roadmap v2 — folded in 16 items from Enhancement Proposal v1.0.**
- New half-sprints: **S4.5 Edge Proof v0** (evidence gate pulled forward), **S5.5 Minimal
  Ops Visibility**.
- S4: config-immutability test, point-in-time timestamp columns, kill-switch inside
  `Constitution.evaluate()`, paper realism marker, data quality scoring, secrets-leak tests,
  adversarial suite, opportunity-cost ThesisCard field.
- S8: starter trio reordered to momentum/mean_reversion/dca_ladder; DCA ladder safety
  guardrails (no infinite averaging down).
- S10: strategy kill criteria + 7-level benchmark hierarchy.
- S9/S11: expanded entrepreneur gate + live-readiness gates.
- Added the "DO NOT" hard-rails section.

**Roadmap: Strategy Models + Learning Engine (S8) + video transcript items.**
Strategy Registry (6 strategies), StrategyMixer, 4-tier learning engine, intraday monitor,
trailing-stop 50%-profit early close, DCA defaults, Capital Trades source. Wheel Strategy
permanently excluded.

**Roadmap: 25 + Playwright items from external feedback docs 1 & 2** mapped into S4–S12.

**Architecture: seven-database split.** Replaced the single SQLite file with seven
domain databases via `CamelDbs`. Schema extensions added. 110 tests stay green.

---

## Completed sprints (code)

| Sprint | Commit | Result |
|---|---|---|
| **S3** — Loop + PaperBroker + ledger + allocator | `a47d8cb` | 110 tests green; full paper loop runs, ledger reconciles |
| **S2** — Sharia gate + data ingestion | `d7e7ee3` | 62 tests; off-list + haram rejected, prices land |
| **S1** — Guardrail Service + schema + tests | `f97632a` | 28 tests; full rogue-action suite rejected |

---

## Commit log

```
Roadmap v2: fold in 16 items from enhancement proposal v1.0
Add full project handoff document (HANDOFF.md)
S8: add 4 items from video transcript
BaseStrategy: add name and description as explicit fields
S8: Strategy Models + Learning Engine — new sprint inserted
S4: add Playwright stub to roadmap
CLAUDE.md: add 25 missing feedback items to sprints
Seven-DB architecture + consolidated roadmap (110 tests pass)
Sprint 3: loop runner + PaperBroker + ledger + allocator (110 tests pass)
Sprint 2: Sharia gate + data ingestion (62 tests pass)
Sprint 1: Guardrail Service + schema + tests
```
