# CAMEL CHANGELOG — sprint & decision history

> **Canonical home for what happened when.** Derived from git history; one entry per
> meaningful change. Newest first.

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
Deferred by dependency: max cancel/replace → S11 (LiveBroker); earnings blackout → S7.
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
