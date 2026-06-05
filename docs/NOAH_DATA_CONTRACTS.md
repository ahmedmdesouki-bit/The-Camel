# NOAH DATA CONTRACTS — databases, schemas, point-in-time discipline

> **Canonical home for the data model.** The 7-database architecture, point-in-time
> timestamp discipline, and data quality scoring. Schema DDL lives in `db/*.py`.

---

## Seven-database architecture (Phase 0 — SQLite)

Each domain owns its own SQLite file. Callers construct `NoahDbs.from_dir(base_dir)` and
pass the right sub-path to each module. `init_all(dbs)` creates all seven.

| DB file | Owner module(s) | Content | Status |
|---|---|---|---|
| `noah_market.db` | `data/` | prices, dividends, splits | Live |
| `noah_macro.db` | S7 | rates, PMIs, yield curve, GDP, recession indicators | Stub |
| `noah_fundamentals.db` | S7 | revenue, margins, EPS, FCF, debt, valuation | Stub |
| `noah_news.db` | S7 | structured event objects (never raw text) | Stub |
| `noah_sharia.db` | `sharia/` | whitelist (versioned), sharia_events | Live |
| `noah_portfolio.db` | `broker/`, `ledger/`, `loop/` | orders, positions, ledger, runs, approvals | Live |
| `noah_learning.db` | S5/S8 | decisions, outcomes, mistake log, lessons | Schema live, unused |

Migrate to Supabase/Postgres when multi-device / dashboard / remote access is needed (S6+).
`db/schema.sql` is the Postgres migration target with the RLS sketch.

---

## Point-in-time discipline (S4 — do this BEFORE data accumulates)

Every decision-relevant table carries four distinct timestamps. This is the single most
important thing that makes backtests honest. It **cannot be retrofitted** — rows we never
captured with these stamps can never be corrected.

| Column | Meaning |
|---|---|
| `event_date` | when the thing actually happened |
| `reported_at` | when the market / public learned it |
| `ingested_at` | when Noah collected it |
| `known_at` | when Noah was *allowed* to use it |

Backtesting rule (S10): a strategy may only see rows where `known_at` ≤ the simulated
decision time. Using today's Sharia status, restated financials, or post-event news in a
pre-event decision is look-ahead bias and is blocked by this discipline.

---

## Schema extensions already live

- `whitelist`: `historical_drift_count`, `purification_ratio`
- `sharia_events`: `trigger_period`, `reasoning_summary`
- `orders`: `client_order_id` (UUID, idempotency)

---

## Data quality scoring (`data/quality.py` — v1 in S4, full in S7)

Any data used in a decision is scored before it is allowed to influence anything:

```json
{
  "source_count": 3,
  "freshness_hours": 4,
  "source_agreement": 0.997,
  "source_reputation": "approved",
  "quality_score": 0.92,
  "decision_eligible": true
}
```

Inputs: `source_count` + `freshness_hours` (from `data/freshness.py`),
`source_agreement` (from `data/triangulation.py`, >0.5% close disagreement flags),
`source_reputation` (from `security/source_allowlist.py`). Stale or single-source
low-quality data → `decision_eligible=false` → blocks action (Constitution rule #8).

---

## Per-table data contract (target for all decision tables)

Each table should carry: `owner` · `schema_version` · `data_source` · `as_of_date` ·
`created_at` · `updated_at` · `quality_score` · `provenance_hash`.

---

## News/event objects (never raw text)

Web text is sanitised to structured JSON (`data/sanitiser.py`) before landing in
`noah_news.db`. Example event object:

```json
{
  "date": "2022-02-24", "event_type": "war_escalation", "region": "Europe",
  "affected_assets": ["oil", "gas", "wheat", "defense"],
  "severity": 5, "expected_duration": "medium",
  "source_count": 6, "confidence": 0.82
}
```

Raw external text is **never** passed directly to the reasoning engine (prompt-injection
defense). See `../Noah_CLAUDE.md` conventions + NOAH_TESTING.md security tests.
