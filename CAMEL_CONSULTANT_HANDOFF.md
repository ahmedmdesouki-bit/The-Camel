# The Camel — Consultant Review Handoff

> **Self-contained snapshot for an external reviewer.** You should be able to understand the
> project, what's built, what's planned, and where your feedback is most valuable — without
> reading anything else. Repo links are provided if you want to go deeper.
>
> **Snapshot date:** 2026-06-06 · **Repo:** https://github.com/ahmedmdesouki-bit/The-Camel
> (branch `main`) · **Status:** Sprints S1–S7 complete, S8 in progress (slice 1) · 366 tests green ·
> paper-mode only · on Roadmap v3 (S1–S14).

> ⚠️ **What this is:** a personal, educational, decision-support / engineering project for the
> founder's **own** capital. It is **not** financial, legal, or Sharia advice, and **not** a
> product offered to others. Live money is not moving — everything runs in paper/simulation
> behind a human approval gate.

---

## 0. How to give feedback (read this first)

This is the **fourth** external review of the project; the prior three were high-quality and were
folded into the roadmap. The most useful feedback engages with the **architecture and the honest
open questions** (§11), not feature wishlists. Specifically, we'd value your read on:

1. **Is there a real trading edge** under these constraints, or is the honest expectation "market
   beta minus costs"? (See §11 Q1 — this is the big one.)
2. **Is the guardrail model actually sound** — what ruinous or prohibited action can still slip
   through? (§5, §11 Q3–Q4)
3. **Is the sequencing right** — we just reordered to "data backbone before the proof engine,
   Entrepreneur arm earlier." Agree/disagree? (§10)
4. **Is this worth doing at all** given ~$126 real capital + $100/mo? Argue both sides. (§11 Q6)

Brutal honesty is welcome and expected.

---

## 1. What it is (one paragraph)

**The Camel** is a Python-based, guardrailed autonomous operator running a continuous
**Observe → Thesis → Choose → Act → Measure → Learn** loop across two arms: **Trader Camel** for
Sharia-compliant markets and **Entrepreneur Camel** for Sharia-compliant AI products. Its defining
principle is an **inversion of trust** — the LLM only *proposes*; every consequential action
(anything touching Sharia compliance, real money, or the live internet) is *decided* by deterministic
machinery the model cannot edit: a **Constitution**, an **Edge Proof** evidence gate, a **Budget
Kernel**, append-only **audit logs**, a **kill switch**, and **human approval gates** before any
live-money autonomy. Aggressive inside the rails, powerless outside them — autonomy is earned through
a paper-trading track record, never granted.

**Tagline:** *LLM proposes · Math tests · Guardrails decide · Humans approve what's risky · Autonomy
is earned, not granted.*

---

## 2. The core thesis (why this is different)

Most "AI trading bot" or "autonomous agent" projects let the LLM make decisions. **The Camel's bet is
the opposite: the LLM is the *least*-trusted component in the system.** It is good at proposing ideas
and bad at being trusted with consequences. So:

- It can **propose** trades, theses, and product ideas.
- It **cannot** decide. Deterministic code (the Constitution), math (Edge Proof), and a human gate decide.
- It **cannot** edit its own rules, limits, whitelist, or permissions — there is no agent-callable
  override path anywhere in the codebase. That's tested, not just asserted.

The two arms aren't the point — they're two **proving grounds** for one underlying artifact: *a
containment architecture for autonomous AI.* Trading has **ruin risk** (markets can wipe you out);
software has **bounded downside** (a bad product just fails). If the containment holds across both,
it generalizes.

This is why the priority hierarchy (§4) puts **return generation second-to-last**. This is a
safety-and-evidence system that happens to trade — not a trading system with guardrails bolted on.

---

## 3. Founder context & hard constraints

- **Founder:** "Chiko" (Ahmed), Riyadh, Saudi Arabia. Beginner-to-intermediate investor.
- **Day job:** full-time at a **travel-tech startup** — real domain knowledge behind the
  Entrepreneur arm's lead product (an Arabic complaint/SLA-response assistant for Saudi
  travel/hospitality operators).
- **Compliance:** **Sharia-compliant only — a hard wall.** Excludes conventional finance, alcohol,
  tobacco, gambling, pork, adult content, **and weapons/defense.** No riba, leverage, shorting,
  options, or derivatives — ever.
- **Risk profile:** moderate; holds through dips, does not panic-sell.
- **Real brokerage today:** the **Sahm** app — **whole shares only** (no fractional), US ETFs/equities.
- **Real capital today:** ~**$126** deployed + **$100/month** contributions (deliberately small — a
  learning-stage account). A separate **$10K "Camel Fund"** is the target working capital for the
  autonomous operator.
- **Base currency:** SAR, pegged ~3.75/USD (USD holdings carry ~no FX risk for the founder).
- **Runtime:** a dedicated Windows 11 PC; remote access + kill switch over Tailscale.
- **Real-world action item (founder's timing):** the founder's currently-deployed holdings
  **SCHD + SCHX both fail the Sharia screen**; compliant whole-share swaps identified (SPUS
  recommended; HLAL, MNZL).

---

## 4. North Star & priority hierarchy

> The Camel is a Sharia-compliant autonomous operator with a deterministic constitution, an
> edge-proof engine, a budget kernel, and a learning ledger. **Not a stock-picking chatbot.**
> LLM proposes. Math tests. Guardrails decide. Humans approve what's risky. Autonomy is earned, not granted.

**Priority hierarchy (never inverted):**

```
1. Sharia compliance      ← a hard wall, not a preference
2. Capital preservation
3. System integrity
4. Evidence quality
5. Learning speed
6. Return generation      ← note how low this sits
7. Autonomy expansion     ← earned last, with evidence
```

---

## 5. The guardrail Constitution (the heart of the system)

`guardrail/constitution.py` — a pure, deterministic `evaluate(action, state) → Decision`. No I/O,
fully unit-tested. Every consequential action routes through it. The non-negotiable rules:

1. **Sharia gate is a hard wall.** Only whitelisted, compliant, non-frozen instruments are tradeable.
   Business models screened for haram activity. No leverage/derivatives/shorting/margin/crypto-derivatives.
2. **No position without a written invalidation point** (invalidation + profit-take + time-stop).
3. **Withdrawals are forbidden.** The broker API key must be trade-only, withdrawals disabled.
4. **Live money needs a human approval gate** until a later phase, then only inside a per-order envelope.
   Phase 0 is paper only.
5. **Everything is logged** — append-only ledger with SHA-256 hash chain; limits are founder-owned
   config the agent process cannot write.
6. **Limits live in `config/limits.yaml`** — not hardcoded elsewhere.
7. **The Camel cannot change its own rules.** No agent-callable override path exists (proven by a test).
8. **Cannot act on stale or single-source data.**
9. **Cannot act unless broker/account state reconciles.**

Additional enforced rails: rolling velocity stops (5-day ≤ −8%, 14-day ≤ −12%), daily-loss circuit
breaker, illiquidity/slippage gate, kill-switch checked inside `evaluate()`, Budget Kernel spend
caps, a Tool Permission Matrix, and a prompt-injection sanitiser so scraped web text never reaches
the reasoning engine as instructions.

---

## 6. Architecture overview

**The loop:**
```
Observe → Generate Opportunities → Opportunity Router (Trader / Entrepreneur / Research /
System-improvement / Wait) → Edge Proof or Product Gate → Constitution → Budget Kernel →
Human Approval Gate → Act → Measure → Learn → Learning Ledger
```
The router is biased toward **Wait**; there is no Trader path without a passing Edge Proof.

**Seven-database SQLite architecture** (Phase 0; migrates to Postgres/Supabase when remote/dashboard
needs it). Each domain owns its file:

| DB | Owner | Content | State |
|---|---|---|---|
| `camel_market.db` | `data/` | prices, dividends, splits | **live** |
| `camel_macro.db` | (S8) | rates, yield curve, GDP, CPI | **stub → S8** |
| `camel_fundamentals.db` | (S8) | revenue, margins, EPS, FCF, debt | **stub → S8** |
| `camel_news.db` | (S8) | structured event objects (never raw text) | **stub → S8** |
| `camel_sharia.db` | `sharia/` | whitelist (versioned), sharia_events | **live** |
| `camel_portfolio.db` | `broker/ ledger/ loop/` | orders, positions, ledger, runs | **live** |
| `camel_learning.db` | learning | decisions, outcomes, mistakes, lessons | **live** |

> **The stubs are deliberate.** The macro/fundamentals/news DBs exist with full schemas but no data
> yet. Filling them with real, provenanced data (S8) is the next big build — and the reason the
> roadmap was reordered (§10).

**Point-in-time discipline** — every decision-relevant table carries four timestamps:
`event_date` (when it happened) · `reported_at` (when the public learned it) · `ingested_at`
(when the Camel collected it) · `known_at` (when the Camel was *allowed* to use it). This is what
makes backtests honest, and it was added early (S4) — before data accumulates — because it cannot be
retrofitted.

**Edge Proof** (`engine/edge_proof_v0.py`, today) — the evidence gate: historical hit-rate +
forward-return vs benchmark from real market data. `gate()` is wired into the capital allocator so
**no trade proceeds without a passing EdgeReport** (missing/weak/stale → `trade_allowed=false`). The
full 17-check signal-conditioned engine is S10.

**Operator OS** (`operator_os/`) — an 11-state machine (illegal transitions blocked; `ACTING` only
from `AWAITING_APPROVAL`; `KILLED` terminal), the Opportunity Router, a persistent task queue, the
Learning Ledger, an append-only op log, and a GREEN/YELLOW/RED/BLACK health monitor.

---

## 7. What's built — Phase 0, 366 tests green

The **safety and evidence core is done.** Everything below runs in paper/simulation behind a human gate.

| Sprint | Theme | What shipped | Tests |
|---|---|---|---|
| **S1** | Guardrail Service | The deterministic Constitution; rogue-action suite 100% rejected | 28 |
| **S2** | Sharia gate + data | Whitelist / quarterly re-screen / haram classifier; Alpaca market-data ingestion + cross-source triangulation | 62 |
| **S3** | Loop + broker + ledger | LoopRunner, PaperBroker, append-only SHA-256 hash-chain ledger, capital allocator | 110 |
| **S4** | Hardening + Budget Kernel | Rolling velocity stops, illiquidity gate, kill-switch in `evaluate`, Budget Kernel, Tool Permission Matrix, config immutability, data freshness/quality/sanitiser, broker idempotency, point-in-time columns | 197 |
| **S4.5** | Edge Proof v0 | Evidence gate wired into the allocator — no trade without an EdgeReport | 217 |
| **S5** | Operator OS | 11-state machine, Opportunity Router (leans to *Wait*), task queue, Learning Ledger, op log, health monitor | 253 |
| **S5.5** | Minimal Ops | Daily report, kill-switch self-test, plaintext-secret scan, verified backup/restore | 263 |
| **S6** | Dashboard + Monitoring | Read-only HTML dashboard, credential-safe Telegram alerts, heartbeat, log rotation, hard secrets refusal, off-box archive, weekly scheduled checks + a founder machine-hardening checklist | 289 |
| **S6.5** | Safety & accounting hotfix | Phantom-sell + oversell guard, close-only/reduce-only exits for frozen/non-compliant holdings, Edge Proof mandatory for buys (sells exempt), no $1 fallback fill in production | 309 |
| **S6.6** | Position accounting + ops hardening | Positions table on every fill (weighted-avg cost, realized P&L, exact qty-based phantom guard, ledger reconcile); illiquidity fail-closed in live; dead-man's-switch; SQLite WAL; beginner mode; broker matrix | 331 |
| **S7** | Entrepreneur Product Engine *(engine)* | 17-field Product Gate + separate Entrepreneur Constitution (code-gen-only autonomy; privacy/rights/budget/approval gates; banned claim wording; haram screen) + 10-stage build pipeline (no launch without founder approval) | 352 |

**Notable engineering choices already proven by tests:** the agent has no write path to founder
config (`config_guard`); the ledger is a cash-account convention with a hash chain that detects
tampering; a malicious symbol is HTML-escaped in the dashboard, not injected; a test fixture that
*looked* like a secret was caught by the project's own secret scanner (working as intended).

> **Not yet built / not yet true:** no live trading, no real data in macro/fundamentals/news, no
> backtesting engine yet, no Entrepreneur product shipped yet, no real track record. All of that is
> the plan below.

---

## 8. Tech stack

- **Language:** Python 3.12. `guardrail/` and `engine/` are kept pure (no I/O) for unit-testability.
- **Tests:** pytest — 289 passing. Adversarial + integration suites included.
- **Data layer:** SQLite × 7 (Phase 0). Postgres/Supabase schema staged for later migration.
- **Market data / broker:** Alpaca paper (free IEX feed); yfinance for quick prototypes.
- **Harness:** a plain Python loop today (Claude Agent SDK adoption deferred until real tool-use
  autonomy is needed).
- **Notifications / approvals:** Telegram bot (credential-safe; stubs out when no token present).
- **Scheduler:** Windows Task Scheduler → post-close daily run.
- **Remote access + kill switch:** Tailscale.
- **Secrets:** Windows Credential Manager (keyring); hard refusal on plaintext secrets at startup.
- **Planned additions (scoped per sprint, kept out of the pure core):** S8 — `requests`/`httpx`,
  `pydantic`, `feedparser`, `vcrpy`/`pytest-recording` (recorded fixtures, no live web in tests).
  S12 — the heavy quant libs (pandas, numpy, scipy, statsmodels, scikit-learn, vectorbt, quantstats).

---

## 9. Repo map (high level)

```
guardrail/     constitution.py — evaluate(action, state) -> Decision. The gate. (pure)
config/        limits.yaml — founder-owned (phase, caps, envelope, cash tiers)
sharia/        whitelist / quarterly screener / haram classifier
data/          store / triangulation / alpaca / freshness / quality / sanitiser
governance/    config_guard / budget_kernel / tool_permissions
engine/        thesis (ThesisCard) / edge_proof_v0 (evidence gate)
operator_os/   state machine / opportunity router / task queue / learning ledger / op log / health
loop/          runner / state / scheduler
broker/        paper (live = stub, behind a phase flag)
ledger/        writer (SHA-256 hash chain) / reconcile
capital/       allocator — routes every request through the Constitution
ops/           kill_switch / heartbeat / backup / secrets_manager / scheduled_checks / reconciliation
dashboard/     read-only HTML view
alerts/        telegram / daily report
db/            CamelDbs (7-DB paths) + per-domain DDL
tests/         21 test files, 289 tests
docs/          the documentation set (see §13)
```

---

## 10. What's planned — Roadmap v3 (S6.5 → S14)

**The reordering insight (this is the most recent strategic change, and worth your scrutiny):** the
safety/governance/evidence scaffolding is strong, but the macro/fundamentals/news DBs are *stubs*. A
real Edge Proof Engine is meaningless without real, point-in-time, provenanced data — you can't do
regime-filtered sampling without macro data, event studies without news, or valuation checks without
fundamentals. **So: build the data supply chain *before* the full proof engine, and move the
cash-flow (Entrepreneur) arm earlier.** Optimize for *evidence density, not feature count*.

| Sprint | Theme | One-line goal |
|---|---|---|
| **S8** *(in progress — slice 1 done)* | Data Intelligence Backbone | `SourceConnector` framework + **top-20 connectors** (SEC EDGAR/XBRL, FRED + ALFRED vintage, World Bank, GDELT, BLS, BEA, Treasury, EIA, ACLED, OFAC, ETF holdings, …), full provenance + point-in-time, recorded-fixture tests; paid vendors phased in (EODHD/Polygon/Norgate/Sharadar/Quiver/Zoya/CRSP); fills the stub DBs |
| **S9** | Knowledge Graph + Regime Engine | Entity resolution (ticker↔CIK↔ISIN↔CUSIP), ETF look-through, event intelligence, 10-state regime classifier from real macro, Sharia cross-check (multi-state status; disagreement → freeze new buys) |
| **S10** | Full Edge Proof Engine | **17-check signal-conditioned** proof (adds survivorship control, similar-regime filter, multiple-testing penalty, signal-decay) + a decision-quality dashboard (shows *why*: rejected signals + reason, regime, beating-benchmark, edge decay) |
| **S11** | Strategy Registry + Learning | Trio: `core_dca` / `quality_momentum` / `etf_regime_rotation`; StrategyMixer; DCA guardrails; 4-tier learning engine (auto base-rates → auto-weight-in-band → propose-only → founder-only) |
| **S12** | Edge Lab + realistic paper + ⭐ **Sandbox Mode** | Three run modes incl. **`sandbox`** (full system on live data + virtual money — the dress rehearsal that produces the micro-live track record); walk-forward; crisis tests; **two-engine cross-check**; Sharia-drag quantified; **No-Edge protocol → DCA**; delisted handling; must beat simple DCA after costs |
| **S13** | Micro-Live Readiness (Phase 1) | Telegram approval channel (timeout = veto), LiveBroker, limit-orders-only, $100–500 human-approved per trade; ≥28-day paper track record + zero guardrail breaches as prerequisites |
| **S14** | Module Restructure | Flat layout → clean domain hierarchy (`governance/ operator_os/ trader/ entrepreneur/ data/ security/ alerts/ dashboard/`); tests stay green |

---

## 11. Key design decisions & rationale

- **Guardrails as code, not prompts** — autonomy is only safe if prohibitions are deterministic and
  un-promptable.
- **Lead with the Entrepreneur arm, leash the Trader arm** — software has bounded downside;
  autonomous trading has ruin risk, so it stays human-gated longer.
- **Paper-first** — prove the guardrails before any real dollar moves.
- **Personal-use only** — managing others' money would trigger Saudi CMA robo-advisory licensing.
- **Point-in-time discipline added before data accumulates** — honest backtesting is impossible to
  bolt on later.
- **Data backbone before the proof engine** (Roadmap v3) — the proof engine is only as honest as its
  inputs.
- **Free/official data first, paid vendors phased in** — SEC, FRED/ALFRED, World Bank, GDELT cover
  most of the need at $0; paid (EODHD delisted data, etc.) only when there's a concrete reason.

---

## 12. Honest limitations & risks (please pressure-test these)

- **Tiny real capital.** ~$126 + $100/mo. The autonomous-operator effort is arguably disproportionate
  to the capital — see Q6.
- **No edge proven yet.** Edge Proof v0 exists, but the macro/fundamentals/news data needed to prove a
  *real* signal-conditioned edge isn't ingested yet (S8).
- **No live track record.** Everything is paper/simulation. The whole "earn autonomy with evidence"
  premise is untested in production.
- **Single operator, single machine.** Windows PC + Tailscale. Hardware/availability is a real risk
  (mitigated by the machine-hardening checklist, but it's a checklist, not redundancy).
- **LLM-in-the-loop failure modes** still exist at the *proposal* layer: hallucinated thesis cards,
  prompt injection from web data, data poisoning. The architecture contains the *consequences*, but
  the reviewer should probe whether containment is truly complete.

---

## 13. Open questions for the reviewer 🔎

These are genuinely open and are the highest-value places for your feedback:

1. **Edge in trading.** A $10K positional, long-only, Sharia-screened book — is there a credible,
   defensible asymmetric edge, or is the honest expectation "market beta minus costs"? Where could a
   real edge come from under these constraints? *(The whole S8→S10 data-and-proof investment is the
   project's attempt to answer this honestly before risking capital.)*
2. **Entrepreneur arm realism.** What's a realistic first compliant AI product an autonomous agent
   could actually ship and monetize, and what's the true success rate?
3. **Guardrail completeness.** What prohibited or ruinous action do the rules still miss?
4. **Autonomy danger.** Where does "auto within guardrails" still bite — data poisoning, broker API
   edge cases, prompt injection, hallucinated theses?
5. **Broker choice.** Alpaca vs IBKR for live, given KSA residency + a self-imposed Sharia whitelist.
6. **Is this worth it?** Brutally: given $126 + $100/mo, is the effort better spent on contributions
   and skill-building than on building an autonomous operator? Argue both sides.
7. **Sequencing.** Is "data backbone before proof engine, Entrepreneur earlier" the right call?

---

## 14. How to run / verify

```bash
git clone https://github.com/ahmedmdesouki-bit/The-Camel.git
cd The-Camel
python -m pytest -q          # expect: 289 passed
```

- No credentials are required to run the test suite (Alpaca/Telegram stub out without keys).
- Authoritative artifacts: **`guardrail/constitution.py`** + **`config/limits.yaml`** (code beats docs).
- The kill switch: `python ops/kill_switch.py halt | resume`.

> **Windows note (founder's machine only):** the working path is 261 chars (one over MAX_PATH);
> the founder maps a `subst N:` virtual drive to run tests. On a normal clone to a short path this
> is irrelevant.

---

## 15. The documentation set (if you want to go deeper)

Each doc is the single canonical home for its topic (the project enforces "one fact, one home"):

| Doc | Canonical for |
|---|---|
| `README.md` | Repo entry point — building / built / planned at a glance |
| `CLAUDE.md` | Operating manual: conventions, rails, repo map, current status |
| `docs/CAMEL_BRIEF.md` | Project context: why/who, real capital, open questions |
| `docs/CAMEL_ROADMAP.md` | Full sprint plan S1–S14 (Roadmap v3) + open decisions + definition of done |
| `docs/CAMEL_CONSTITUTION.md` | The rules in prose (Sharia, risk, phase gates) |
| `docs/CAMEL_DATA_CONTRACTS.md` | 7-DB schemas, point-in-time discipline, data quality |
| `docs/CAMEL_TESTING.md` | Test strategy, adversarial + integration suites |
| `docs/CAMEL_LIVE_READINESS.md` | Phase 1 go-live checklist |
| `docs/CAMEL_MACHINE_HARDENING.md` | Founder machine-setup checklist (Tailscale, BitLocker, backups) |
| `docs/CAMEL_CHANGELOG.md` | Sprint & decision history |
| `HANDOFF.md` | Internal contributor onboarding |

---

*Thank you for reviewing. The prior three external reviews materially improved this project — candid,
specific, architecture-level critique is exactly what's wanted.*
