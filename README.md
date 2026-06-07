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

**Status:** Phase 0 (paper) · **Roadmap v3 build S1–S14 complete** (full stack: data → Edge Proof → Constitution → Budget → assembled loop → Edge Lab + Sandbox; research desk + micro-live readiness fail-safe by default) · Dashboard (Design-System skin) + founder alerts · **603 tests green** ·
7-DB architecture live. Remaining steps are deliberately **founder-gated** (machine hardening · ≥28-day paper/sandbox track record · the live phase-flip with real money).

> **New here? Run `python demo.py`** — one command seeds sample data, drives one fully-governed tick through the whole stack, and writes the read-only dashboard. Fully offline, paper-only, no credentials. See **[Try it](#try-it-one-command)** below.

---

## What's built (Phase 0 — paper, 603 tests green)

**The entire Roadmap v3 build (S1–S14) is done.** The full trust-inverted stack — data → knowledge → Edge
Proof → Constitution → Budget → assembled loop → Edge Lab + Sandbox → micro-live readiness — runs in paper
mode behind a human gate, fail-safe by default. Everything below is implemented, tested, and on `main`.

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
| ✅ | **S8** Data Intelligence Backbone | `SourceConnector` framework + provenance + point-in-time + `source_documents`; **12 connectors** incl. the free **Stooq daily-price feed** (FRED, SEC EDGAR + SEC-RSS 8-K, Treasury, World Bank, BLS, BEA, EIA, GDELT, ACLED, ETF look-through, Stooq); injection-hardened news; the **ingestion orchestrator** (`data/ingest.py`) populates the DBs in production. Injectable transport (no live web in tests) |
| ✅ | **S9** Knowledge graph + regime + Sharia cross-check | entity resolver (`resolve(ticker)` → full identity); **10-state Regime Engine** over real macro + SAR/USD peg; event intelligence + `event_reactions`; **verified AAOIFI** screen + multi-state cross-check (disagreement → freeze) |
| ✅ | **S10** Full Edge Proof Engine | **17-check signal-conditioned** proof — multiple-testing penalty, signal decay, Sharia fail-safe, model-disagreement → human, shadow/enforcing, point-in-time `as_of` |
| ✅ | **S10.5** Operator-loop assembly | the §4 loop assembled (`loop/assembled.py` + `loop/driver.py`) — the **no-edge-no-trade** invariant holds end-to-end; scheduled entrypoints (`python -m loop.jobs tick`) |
| ✅ | **S11 (+S11.5)** Strategy registry + portfolios + learning | the trio + dividend_growth + mixer + promotion ladder; 6 seed portfolios + risk budgets; 4-tier learning; the S11.5 driver wires it all end-to-end |
| ✅ | **S12** Edge Lab + ⭐ Sandbox | realistic-paper fills + 4-stage NRA dividends; **two-engine backtest cross-check**; **No-Edge → DCA**; **Sandbox** runs the full system on a live feed with virtual money — the track record that earns micro-live |
| ✅ | **S12.5** Research Desk | evidence-object contract + analyst desks — **dormant by design** (master switch off, no execute path) |
| ◑ | **S13** Micro-Live readiness | approval gate (withholds by default) + inbound approve/veto channel; Sahm **ManualBroker** + paste-a-confirmation parser; **gated LiveBroker** (refuses without phase ≥ 1 + creds); readiness checklist (NOT-READY by default). All fail-safe — **go-live is the founder's explicit act** |
| ✅ | **S14** Architecture + module reorg | the layered module map (`docs/CAMEL_ARCHITECTURE.md`) + the **physical reorg** — the whole Trader Camel under `trader/` (engine · edgelab · execution · strategies · portfolios · sandbox · regime · events) |
| ✅ | **QA + pre-live hardening** | full 5-dimension line-by-line QA/QC (**0 blockers**); broker **write-atomicity**, point-in-time `known_at`, vintage-aware schemas, the production Edge-gated tick with a single founder-owned phase source + injected Budget Kernel |

Plus the **7-database SQLite architecture** (market / macro / fundamentals / news / sharia / portfolio / learning)
with **point-in-time discipline** (`event_date · reported_at · ingested_at · known_at`) so backtests can't cheat.

## What's left — S15 (paid tools + founder actions)

**S1–S14 are built, hardened, organized, and fail-safe (603 tests green).** The *only* remaining work is
crossing "above the line" into real, scheduled, live operation — which by definition is **not free code**: it
is **paid vendors** and **founder actions**. Each item is mapped to the code already built and waiting for it in
[`docs/CAMEL_S15_PAID_AND_FOUNDER.md`](docs/CAMEL_S15_PAID_AND_FOUNDER.md).

| Category | Items |
|---|---|
| 💳 **Paid vendors** | EODHD (dividends + 2nd fundamentals) · Sharadar (survivorship-free backtests) · Benzinga (news) · Finnhub (earnings calendar) · Alpaca (live + IEX websocket) · IBKR (Phase 2) |
| 🔑 **Founder credentials** (free to provision) | FRED / BEA / EIA keys · Telegram bot token + chat id · Alpaca trade-only key · real SEC contact UA · OCR for Sahm screenshots |
| 🖥️ **Founder machine + go-live** | machine hardening · Windows Task-Scheduler wiring (`data.ingest`, `loop.jobs tick`) · a **≥28-day paper/sandbox track record** · the `config/limits.yaml` **phase-flip** with real (tiny) capital |

*Below the line is done. Above it is yours — no code crosses that line on its own.* Full sprint history +
open decisions live in [`docs/CAMEL_ROADMAP.md`](docs/CAMEL_ROADMAP.md).

## Try it (one command)

For a first look — no setup, no credentials, nothing touches the network or real money:

```bash
git clone https://github.com/ahmedmdesouki-bit/The-Camel.git
cd The-Camel
python demo.py
```

`demo.py` seeds a fresh set of the 7 SQLite DBs under `./demo_run/`, drives **one fully-governed tick**
through the entire stack — regime classification → strategy proposal → the **17-check Edge Proof** →
Constitution (Sharia #1) → Budget Kernel → a **realistic-paper fill** (whole shares, fees, slippage) — and
writes the read-only operator dashboard to `./demo_run/camel-dashboard.html`. Open that file in any browser.

What you'll see it prove:
- A name with a **proven edge** passes every gate and fills with realistic costs.
- A **frozen / non-compliant** name (`SCHD`) is held out by the Sharia gate — the dashboard shows the
  rejection, because *the rejections are the point*.
- Flip the seeded macro to an inverted curve and the Opportunity Router goes to **Wait** — no edge, no trade.

```bash
pytest -q          # then run the suite — expect 603 passed
```

## Where to start

| You want to… | Read |
|---|---|
| Understand the project (why, who, context) | [`docs/CAMEL_BRIEF.md`](docs/CAMEL_BRIEF.md) |
| Get current status + run it | [`HANDOFF.md`](HANDOFF.md) |
| Work in the repo (build a sprint) | [`CLAUDE.md`](CLAUDE.md) — the operating manual |
| Stand up the **private web window** (Vercel + Supabase) | [`web/README.md`](web/README.md) — read-only mirror + control bar, friends-only, paper-safe |
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
python -m pytest -q          # 603 passed
```

*(For future work, cloning to a short path like `C:\camel` removes this friction.)*
