# NOAH CHANGELOG — sprint & decision history

> **Canonical home for what happened when.** Derived from git history; one entry per
> meaningful change. Newest first.

---

## 2026-06-06

**Consolidation: one source of truth, clean repo.**
Folded `Noah_Project_Brief.md` → `docs/NOAH_BRIEF.md` (canonical "why/who" doc: founder
constraints, real capital ~$126 + $100/mo, $10K target, origin, open questions). Added a
top-level `README.md` entry point. Archived all legacy source docs (ADAM/Noah PRDs & specs,
StockSense playbook/dashboard/tracker generator) to `docs/source-materials/` via git-tracked
renames (history preserved, nothing deleted). Removed junk (pytest cache `adam/`, stale
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
domain databases via `NoahDbs`. Schema extensions added. 110 tests stay green.

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
