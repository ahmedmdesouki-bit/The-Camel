# CAMEL PRE-LIVE HARDENING — the must-close-before-real-money checklist

> **Origin:** the full 5-dimension line-by-line QA/QC audit on **2026-06-08** (safety core · Sharia ·
> data integrity · decision/execution/loop · docs/coverage). **Result: 0 BLOCKERS, 0 active HIGH bugs.**
> The build (S1–S14, 603 tests green) is **sound and fail-safe for paper/Phase-0 use today.** Every item
> below is a *latent* gap — safe right now because the system is paper-only, Phase-0, single-caller, and
> timestamps collapse to `now` — that should be closed **before any real money** flows. This is the
> canonical home for those items; pair it with `CAMEL_LIVE_READINESS.md` (the go-live gate) and
> `CAMEL_MACHINE_HARDENING.md` (the machine checklist).

**Why "safe today" is true, in one line:** real capital is triple-gated off (`broker/live.py` raises;
approval withholds; phase=0), the production executor is a no-op, virtual money is isolated in the sandbox,
and the live tables only hold knowable bars — so none of these gaps can move a real cent in the current state.

> ### ✅ UPDATE 2026-06-08 — P1 and P2 are now CLOSED (603 tests green)
> The post-S14 hardening push implemented **all P1** (A broker write-atomicity · B Edge-Proof `as_of` · C
> Budget-Kernel injection + D single phase source + E scheduler→assembled, via the new
> `loop.jobs.run_trading_tick` / `python -m loop.jobs tick`) and **all P2** (A `known_at` filter · B
> `etf_holdings` UNIQUE+reported_at · C *documented* — `quality.decision_eligible` left as the richer gate
> pending quorum-metadata plumbing, freshness + sample-size are the active gates · D compact screener
> completed · E doubtful persisted · F shadow-phase guard · G manual-fill guard) and **P3-E** (peg `as_of`).
> The sections below are kept as the record of what each item was. **Remaining: only P2-C (documented,
> deferred), the lower-stakes P3 polish, and P4 (the founder/paid go-live gates → now `CAMEL_S15_...md`).**

---

## ✅ Fixed in the QA pass (2026-06-08)

| # | Area | What was fixed | File |
|---|---|---|---|
| F1 | Decision | **Edge-mandate fail-open closed.** `_opens_or_increases` now requires an Edge Proof for *any* non-reducing TRADE side ("increase"/"add"/unrecognised), not only the literal `"buy"`. | `capital/allocator.py` |
| F2 | Safety | **Legacy scheduler can't become the live path.** `loop/scheduler.py` (which does NOT run the Edge Proof gate) now **refuses `phase ≥ 1`** and documents that live must use `loop/driver.py` / `loop/jobs.py`. | `loop/scheduler.py` |
| F3 | Sharia | **False-compliant "loaded gun" defused.** The legacy compact `screen_instrument` now marks `full_screen=False` + `unscreened=[receivables_ratio, prohibited_sector]` so a `passed=True` from that path can never be mistaken for full certification. (Authoritative screen remains `sharia/cross_check.py`.) | `sharia/screener.py` |
| F4 | Exec | Removed a confusing `* 0` no-op in the dividend attribution math (cosmetic; result unchanged). | `execution/corporate_actions.py` |
| F5 | Docs | Test-count drift corrected (557 → **572**) across README, HANDOFF, docs/README, CAMEL_TESTING, roadmap footers, architecture; HANDOFF status refreshed to "S1–S14 complete"; consultant handoff banner-marked as a frozen snapshot. | (docs) |

---

## P1 — MUST close before micro-live (S13 gate)

These are the items an auditor flagged as "paper-only today, **must** be closed before the same code path
touches real money."

- **P1-A · Broker write-atomicity.** `broker/paper.py::submit()` writes `orders`, the ledger, and `positions`
  in **three separate transactions**. A mid-sequence failure (or the `apply_fill` phantom-sell re-check
  raising) leaves the order + cash entry committed but positions un-updated → the books diverge.
  *Fix:* wrap orders-INSERT + `append_entry` + `apply_fill` in a single SQLite transaction, **or** run the
  phantom-sell check before any write so a rejection leaves nothing committed. *(This is the long-standing
  "broker write-atomicity deferred to S12" backlog item — the live broker reuses this contract.)*

- **P1-B · Edge Proof price loader is not point-in-time.** `engine/edge_proof_v0.py::_load_closes` reads
  `prices` with **no `as_of`/`known_at` cutoff**. Safe today (EOD tables hold only knowable bars), but a
  backfill, sandbox replay, or restated/adjusted bar would leak look-ahead straight into the trade verdict.
  *Fix:* thread an optional `as_of` through `evaluate_signal_full → _load_closes` and filter
  `WHERE symbol=? AND date <= ? AND (known_at IS NULL OR known_at <= ?)`; default `as_of=now` in live.

- **P1-C · Production driver must inject the Budget Kernel.** `AssembledLoop` enforces the budget **only if**
  a `budget_kernel` is injected (it's `None` by default). *Fix:* the live wiring (`loop/jobs.py` / the
  go-live driver) must construct `AssembledLoop` with a real `BudgetKernel`, and a test should assert that
  the live path fails closed if it's absent.

- **P1-D · Phase: single founder-owned source of truth.** Phase is read from `CAMEL_PHASE` (env) in
  `loop/scheduler.py` and from `config/limits.yaml` in the Constitution; the scheduler builds the
  Constitution with `limits=None` (so it never loads the yaml). *Fix:* derive phase **only** from
  `config/limits.yaml` (founder-owned, OS-read-only) everywhere; drop `CAMEL_PHASE` or assert it equals the
  yaml value. (Mitigated by F2, which refuses the scheduler at phase ≥ 1, but the dual source should still go.)

- **P1-E · Scheduler → assembled path.** Beyond F2's refusal guard, the actual post-close production job
  should run the **assembled** path (`loop/driver.py::run_strategy_tick` via `loop/jobs.py::run_daily_ops`),
  not the legacy `LoopRunner`, so the Edge Proof gate is in the live loop by construction.

---

## P2 — SHOULD close before live (defense that activates as the system grows up)

- **P2-A · `known_at` in the regime point-in-time filter.** `trader/regime/features.py::_points` filters
  `event_date`/`reported_at` but not `known_at`. Correct today (timestamps collapse to `now`), but the day an
  embargo/licence lag makes `known_at > reported_at`, an as-of query leaks future-knowledge.
  *Fix:* add `AND (known_at IS NULL OR known_at <= ?)` to the cutoff.

- **P2-B · `etf_holdings` UNIQUE drops a restated vintage.** `db/sharia.py` uses
  `UNIQUE(source_id, etf, holding_ticker, event_date)` + `INSERT OR IGNORE` — a corrected holdings file with
  the same `event_date` but a later `reported_at` is silently ignored. *Fix:* add `reported_at` (and
  optionally `content_hash`) to the UNIQUE, matching `macro_observations`.

- **P2-C · Wire or retire `data/quality.py`.** `QualityScore.decision_eligible` (the stale/single-source/
  unapproved hard gate, Constitution rule #8) is **dead code** — no non-test module imports it; the live gate
  is `data/freshness.py` + the Edge Proof sample-size + a scalar `data_quality_score`. *Fix:* either wire
  `quality.score(...).decision_eligible` into the allocator/Edge-Proof input assembly, or delete it and
  document that freshness + sample-size are the real gates.

- **P2-D · Legacy compact Sharia screener — retire or complete.** F3 defused the misread risk; the structural
  fix is to either extend the compact `Financials` to carry receivables/total_assets/sector (so all 5 AAOIFI
  screens run), or **delete the compact path** now that `cross_check.py` is the real gate and point
  `test_sharia.py` at the full screen.

- **P2-E · Quarterly rescreen should persist "doubtful".** `run_quarterly_rescreen` neither freezes nor
  records a doubtful name; its whitelist `sharia_status` stays `compliant`. *Fix:* write
  `sharia_status='doubtful'` (+ a sharia_event), or route the quarterly job through `cross_check`.

- **P2-F · Shadow-mode phase guard.** `engine/edge_proof.py` returns `trade_allowed=True` in shadow mode (by
  design, for calibration). *Fix:* refuse `mode="shadow"` when `phase ≥ 1` so a live caller can't silently
  disable the edge block. (`loop/driver.py` already defaults to `enforcing` — good.)

- **P2-G · `broker/manual.py::record_fill` guard.** Records a real-world Sahm fill (money already moved), so it
  has no Constitution/kill-switch check. *Fix:* add a whitelist/kill-switch **warning** (not a hard block) and
  tag manual fills so reconciliation flags a manual entry with no matching proposed ticket.

---

## P3 — Polish / lower-stakes (track, fix opportunistically)

- **P3-A** · Unify the two haram-sector lists (`guardrail/constitution.py::HARAM_TERMS` vs
  `sharia/aaoifi.py::PROHIBITED_SECTORS`) or document that they serve different layers.
- **P3-B** · `DOUBTFUL × None → PENDING` in `cross_check.combine` — consider freezing (`DOUBTFUL`) instead, so
  a genuinely doubtful in-house screen with no second source is frozen, not merely observed. (Capital is safe
  either way — the Constitution blocks any `!= compliant`.)
- **P3-C** · Ledger cash uses raw `notional`; positions use `qty*fill_price` → ~1e-13 float divergence (well
  inside the 0.01 reconcile tolerance). Derive ledger cash from `qty*fill_price` for penny-identical books.
- **P3-D** · `source_document_id` falls back to `source_id:url`; prefer a `content_hash`-based id for endpoints
  without a native document identifier.
- **P3-E** · `trader/regime/peg.py::latest_peg_status` orders by `known_at DESC` with no `as_of` — fine as a
  live reader; add an optional `as_of` before reusing it in any backtest/as-of context.
- **P3-F** · Real SEC/User-Agent contact email before any live SEC pull (`founder@example.com` /
  `founder@thecamel.local` are placeholders that can be rate-limited/403'd).
- **P3-G** · `data/sanitiser.py` injection list is English-substring, allow-by-default — acceptable given
  defense-in-depth (structured-fields-only, redaction, dictionary linking), but a known coverage limit.
- **P3-H** · Sandbox stale-quote path is not exercised when `now` is unset (`now or snap.as_of` → age 0);
  inject `now` to test the staleness rejection.

---

## P4 — Founder / paid / external gates (not code we can close; the go-live prerequisites)

Unchanged from the roadmap backlog — none of these block a tester:
machine hardening (`CAMEL_MACHINE_HARDENING.md`) · a **≥28-day paper/sandbox track record** with 0 breaches and
a clean reconcile · the **phase-flip with real money** (founder's explicit act) · live broker credentials ·
paid vendors (EODHD/Sharadar/Benzinga) · the live websocket feed · IBKR (Phase 2) · Windows Task-Scheduler
wiring · the connector-ingestion orchestrator + parked connector backlog · the optional physical module reorg.

---

### Bottom line
0 blockers. The system is **ready for paper/sandbox testing now**. Close **P1 (A–E)** before flipping any
real-money phase; **P2** as the data pipeline starts carrying vintage lag and restatements; **P3/P4** as
convenient. None of these are reachable in the current paper, Phase-0, single-caller state.
