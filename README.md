# The Camel

A Python-based, guardrailed autonomous operator running an Observe → Thesis → Choose → Act →
Measure → Learn loop across two Sharia-compliant arms — **Trader Camel** (markets) and
**Entrepreneur Camel** (AI products). Its defining principle is an **inversion of trust**: the
LLM only *proposes*; a deterministic **Constitution** it cannot edit, an **Edge Proof** evidence
gate, a **Budget Kernel**, append-only **audit logs**, a **kill switch**, and **human approval
gates** *decide* what actually happens. Aggressive inside the rails, powerless outside them —
autonomy is earned through a paper track record, never granted.

> **Safety first. Evidence second. Autonomy last.**
> LLM proposes · Math tests · Guardrails decide · Humans approve what's risky · Autonomy is earned, not granted.

**Status:** Phase 0 (paper) · Sprints **S1–S7 complete** · **S8 core** (10 connectors) · **S9 COMPLETE (slices 1–4)** · Dashboard v2 + founder alerts · **478 tests green** ·
7-DB architecture live · on **Roadmap v3** (S1–S14).

---

## What's built (Phase 0 — paper, 478 tests green)

The **safety and evidence core** is done. Everything runs in paper mode behind a human gate.

| | Sprint | What shipped |
|---|---|---|
| ✅ | **S1** Guardrail Service | The deterministic **Constitution** — `evaluate(action, state) → Decision`; rogue-action suite 100% rejected |
| ✅ | **S2** Sharia gate + data | Whitelist / re-screen / haram classifier; Alpaca market-data ingestion + cross-source triangulation |
| ✅ | **S3** Loop + broker + ledger | LoopRunner, PaperBroker, append-only **SHA-256 hash-chain ledger**, capital allocator |
| ✅ | **S4** Hardening + Budget Kernel | Rolling velocity stops, illiquidity gate, kill-switch in `evaluate`, **Budget Kernel**, Tool Permission Matrix, config immutability, data freshness/quality/sanitiser, point-in-time columns |
| ✅ | **S4.5** Edge Proof v0 | Evidence gate wired into the allocator — **no trade without a passing EdgeReport** |
| ✅ | **S5** Operator OS | 11-state machine, Opportunity Router (leans to *Wait*), persistent task queue, **Learning Ledger**, op log, health monitor |
| ✅ | **S5.5** Minimal Ops | Daily report, kill-switch self-test, plaintext-secret scan, verified backup/restore |
| ✅ | **S6** Dashboard + Monitoring | Read-only HTML dashboard, credential-safe Telegram alerts, heartbeat, log rotation, hard secrets refusal, off-box archive, weekly scheduled checks + machine-hardening checklist |
| ✅ | **S6.5** Safety & accounting hotfix | Phantom-sell guard, close-only exits for frozen/non-compliant holdings, Edge Proof mandatory for buys, no $1 fallback price in production |
| ✅ | **S6.6** Position accounting + ops hardening | Positions table on every fill (avg cost, realized P&L, exact phantom guard, ledger reconcile); illiquidity fail-closed in live; dead-man's-switch; SQLite WAL; beginner mode; broker matrix |
| ✅ | **S7** Entrepreneur Product Engine | 17-field Product Gate + separate Entrepreneur Constitution (code-gen-only autonomy; privacy/rights/budget/approval gates; banned claim wording) + 10-stage build pipeline (no launch without founder approval) |
| ◑ | **S8** Data backbone (core) | `SourceConnector` framework + provenance + `source_documents`; **10 connectors** (FRED, SEC EDGAR, Treasury, World Bank, BLS, BEA, EIA, GDELT, ACLED, ETF-holdings) filling all 3 stub DBs + ETF look-through; news injection-redaction; scraping policy. Injectable transport (no live web in tests, zero new deps). *Remaining connectors deferred.* |
| ◑ | **S9** Knowledge graph + regime (slices 1–2) | Entity resolver: `resolve(ticker)` → full identity (CIK, sector, Sharia status, ETF look-through, latest filing). **Regime Engine**: 10-state classifier over real macro (rates/curve/CPI/HY/VIX/USD/oil) → regime + confidence + themes |

Plus the **7-database SQLite architecture** (market / macro / fundamentals / news / sharia / portfolio / learning)
with **point-in-time discipline** (`event_date · reported_at · ingested_at · known_at`) so backtests can't cheat.

## What's planned (Roadmap v3 — S7 → S14)

**Guiding insight:** build the **data supply chain before the proof engine**, and move the cash-flow
(Entrepreneur) arm earlier. Optimize for *evidence density, not feature count*. Full detail in
[`docs/CAMEL_ROADMAP.md`](docs/CAMEL_ROADMAP.md).

| Sprint | Theme | One-line goal |
|---|---|---|
| **S8** ◑ core done | Data Intelligence Backbone | framework + provenance + 10 connectors (incl. ETF look-through) + news pipeline (injection-hardened); all 3 stub DBs real. *Remaining ~10 connectors + market-data + paid vendors deferred to a backlog* |
| **S9** ◑ in progress | Knowledge Graph + Regime Engine | **slices 1–2 done**: entity resolver + 10-state Regime Engine. **Next:** event intelligence, Sharia cross-check (multi-state) |
| **S9** | Knowledge Graph + Regime Engine | Entity resolution, event intelligence, 10-state regime classifier, Sharia cross-check |
| **S10** | Full Edge Proof Engine | **17-check signal-conditioned** proof (multiple-testing penalty, signal decay, regime-filtered sample) + decision-quality dashboard |
| **S11** | Strategy Registry + Learning | Trio: `core_dca` / `quality_momentum` / `etf_regime_rotation`; 4-tier learning engine |
| **S12** | Edge Lab + ⭐ Sandbox Mode | **`sandbox`**: full system on live data + virtual money (the dress rehearsal that earns micro-live); two-engine cross-check; Sharia-drag quantified; **No-Edge protocol → DCA** |
| **S13** | Micro-Live Readiness | Telegram approval channel, LiveBroker, limit-orders-only, $100–500 human-approved |
| **S14** | Module Restructure | Flat layout → clean domain hierarchy (tests stay green) |

## Where to start

| You want to… | Read |
|---|---|
| Understand the project (why, who, context) | [`docs/CAMEL_BRIEF.md`](docs/CAMEL_BRIEF.md) |
| Get current status + run it | [`HANDOFF.md`](HANDOFF.md) |
| Work in the repo (build a sprint) | [`CLAUDE.md`](CLAUDE.md) — the operating manual |
| See the full plan | [`docs/CAMEL_ROADMAP.md`](docs/CAMEL_ROADMAP.md) |
| Everything else | [`docs/README.md`](docs/README.md) — the documentation index |

## Source of truth

- **Docs:** `CLAUDE.md` (operating manual) + `docs/` (one canonical doc per topic).
  A fact has exactly one home — change a sprint in `docs/CAMEL_ROADMAP.md`, not elsewhere.
- **Code beats docs:** `guardrail/constitution.py` + `config/limits.yaml` are authoritative.
- **History/origin:** the original PRDs, specs, and the StockSense playbook are archived in
  [`docs/source-materials/`](docs/source-materials/).

## Run the tests

The repo path is 261 chars (over Windows MAX_PATH). Map a virtual drive first:

```powershell
subst N: "<path-to-this-folder>"
cd N:\
python -m pytest -q          # 478 passed
```

*(For future work, cloning to a short path like `C:\camel` removes this friction.)*
