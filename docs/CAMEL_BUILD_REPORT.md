# The Camel — Build Report & Architecture Document

**Audience:** External engineering team (review & integration)
**Author:** Lead Systems Architect (handoff)
**System:** *The Camel* — a guardrailed, Sharia-compliant autonomous operator
**Status as of this report:** Phase 0 (paper-only). S1–S14 built, fail-safe, and physically organized; S15 (paid feeds + founder go-live) is the only remaining tier. **787 automated tests passing (pytest).** Web operator window live at `the-camel-five.vercel.app`.
**Capital at risk:** $0. No code path can place real capital at risk; going live is an explicit, manual founder act (see §5.6).

> **Reading order.** This document pairs with three in-repo references: `CLAUDE.md` (file-level repo map), `docs/CAMEL_ARCHITECTURE.md` (layered module map), and `docs/CAMEL_DATA_CONTRACTS.md` (the 7-database schemas). This report is the **integration-oriented synthesis** of all three.

---

## 1. Executive Summary

The Camel is an autonomous operator built around a single, deliberately inverted premise: **the AI is the least-privileged component in the system.** It may *propose* — theses, trades, products, code — but it can *enact* nothing on its own. Every consequential action descends through a cascade of **deterministic gates the AI cannot read around, write to, or disable.** The gates are plain Python with no LLM in the loop; their limits live in a founder-owned file the agent process has no write access to.

The system has two arms:

- **The Trader Camel** — a long-only, no-leverage, no-derivatives, Sharia-screened equity/ETF operator. Mature and fully built.
- **The Entrepreneur Camel** — a product-builder that may autonomously generate code, but cannot launch, spend, collect user data, use third-party assets, or publish claims without passing its own deterministic gate and a founder approval. Built as pure logic; external integrations (Stripe/GitHub/deploy) are wired only when a real product ships.

Human oversight is structural, not optional: the operator runs as a **brain (Python, on the founder's machine) / window (Next.js, read-only) / bridge (Supabase)** split. The window mirrors *every* decision — including the ones where the system chose **not** to act and why — and can only *queue* commands that the brain executes under the same gates.

---

## 2. System Overview — The One Idea: Inversion of Trust

![The Camel — inversion of trust: the AI proposes at the top as the least-privileged component, and every action descends through Edge Proof, the Constitution, the Budget Kernel, and a Human Approval gate before any act, recorded in a hash-chained audit; a founder-owned panel (limits.yaml, kill switch, config guard) feeds the gates from the side.](architecture-cascade.svg)

***Figure 1 — the trust-inversion cascade.*** *The text fallback below renders the same flow for plain-text viewers.*

```
Observe (regime)  ─►  Opportunity Router  ─►  Strategies / Agents PROPOSE
        │
        ▼
   Edge Proof Engine        (trader/engine/edge_proof.py — 17 checks)     ← EVIDENCE gate
        ▼
   Constitution             (guardrail/constitution.py)                   ← SHARIA #1, risk, phase rails
        ▼
   Budget Kernel            (capital/budget_kernel.py)                    ← spend limits / capital buckets
        ▼
   Human-Approval gate      (governance/approval.py)                      ← phase-gated; WITHHOLDS by default
        ▼
   Act — paper · realistic-paper · manual (Sahm) · live (gated OFF)
        ▼
   Measure → Learn (propose-only) → Audit (hash-chained ledger + op_log)
```

The runtime keystone that strings these together is **`loop/driver.py` (`run_strategy_tick`) → `loop/assembled.py` (`AssembledLoop`)**. A buy with no passing Edge Report is rejected *by the assembled loop itself*, not merely in a unit test. The same action object is re-checked at each layer; there is no "trusted" fast path.

**Design invariant:** *Camel proposes; the gates dispose.* Each gate is pure (`evaluate(...) -> Decision`), side-effect-free, and unit-tested in isolation. The single exception is the kill-switch file read inside the Constitution — deliberate, so the gate itself sees the halt and there is no path around it.

---

## 3. Agent Framework — The Multi-Agent Hierarchy

The Camel is not a single prompt. It is a hierarchy of **proposers** beneath a shared spine of **deterministic disposers**. Proposers are replaceable and untrusted; the spine is fixed and founder-owned.

### 3.1 The Trader Camel (built, mature)

The entire Trader arm lives under one package tree, `trader/`, cleanly separated from the cross-cutting gate layers.

| Sub-system | Package | Responsibility |
|---|---|---|
| **Regime engine** | `trader/regime/` | 10-state macro classifier (e.g. RECOVERY, RISK-OFF, GEOPOLITICAL_RISK_OFF) + SAR/USD peg monitor. Sets the context every proposal is conditioned on. |
| **Event intelligence** | `trader/events/` | News/8-K/earnings event reactions; earnings-blackout rule. |
| **Edge Proof Engine** | `trader/engine/` | The 17-check evidence gate (§5.5). The Trader's core discipline: *no trade without proven, regime-conditioned, cost-net, Sharia-clear edge.* |
| **Strategies (proposers)** | `trader/strategies/` | Momentum, mean-reversion, DCA-ladder, dividend-growth + a mixer and an evidence-gated **promotion ladder**. Strategies only **propose**; promotion to "live-eligible" requires a passing Edge Proof. |
| **Portfolios** | `trader/portfolios/` | 6 portfolios / sleeves with per-portfolio risk budgets; per-portfolio accounting reconciles to the fund. |
| **Edge Lab** | `trader/edgelab/` | Two-engine backtester; the **No-Edge → DCA** protocol (when there is capital but no alpha edge, DCA into the compliant core is *edge-exempt*; alpha still requires an edge). |
| **Realistic execution** | `trader/execution/` | Realistic-paper fills (modeled spread, whole-share, fees), 4-stage NRA dividend handling, corporate actions. |
| **Sandbox** | `trader/sandbox/` | The full assembled system on an injected live feed + virtual money → a micro-live track record without capital risk. |

**Trader flow (one tick):** Regime → Opportunity Router ranks candidates → a strategy proposes an action with a written thesis (invalidation / profit-take / time-stop) → Edge Proof → Constitution → Budget Kernel → (phase-gated) approval → fill → ledger + learning.

### 3.2 The Entrepreneur Camel (built as pure logic; external I/O gated)

The product arm mirrors the Trader's discipline with its own deterministic gates. Code: `entrepreneur/` (`constitution.py`, `product_gate.py`, `build_pipeline.py`).

- **Autonomous scope = code-generation only.** Writing code and opening issues is permitted once the activity screen passes. **Everything that touches customers, money, data, third-party assets, or public claims is gated.**
- **Entrepreneur Constitution** (`EntrepreneurConstitution.evaluate`) — separate from the Trader Constitution, same philosophy, **no agent-callable override.** Action types and their gates:
  - `BUILD` (code-gen) — allowed once the Sharia activity screen passes.
  - `DATA_COLLECT` — requires a recorded privacy review.
  - `ASSET_USE` — requires a rights-cleared check.
  - `SPEND` — must be within the entrepreneur budget bucket.
  - `LAUNCH` (deploy to production) — requires a **founder approval id**.
  - `PUBLISH_COPY` — scanned for prohibited compliance wording (e.g. "guaranteed halal", "100% Sharia certified", "guaranteed returns") which is **banned with or without approval**; regulated (legal/financial/medical) claims always need human approval.
  - The Trader's `HARAM_TERMS` screen is reused, so a haram business model can never be built.
- **Product Gate** (`evaluate_gate`) — the Entrepreneur analog of the Edge Proof: a **17-field `ProductThesis`** must be fully answered and valid (every field present, a Sharia **pass**, a valid risk rating, a real first-10-customers list, a stated human-review requirement for generated outputs) before any build proceeds.
- **Build pipeline** (`build_pipeline.py`) — staged build behind the gates. Pure logic; Stripe / GitHub / customer-data / real deploy integrations are wired only when a real product ships, always behind the approval gates.
- **Worked example (a thesis, not a launch):** an Arabic complaint / SLA-response assistant for Saudi travel/hospitality operators — used to prove the gate + pipeline end-to-end, with *every AI-drafted reply requiring human approval before sending*.

> **Maturity note for the receiving team:** the Trader arm is production-shaped (data feeds live, paper track record accruing). The Entrepreneur arm is a complete, tested *gate-and-pipeline skeleton* — its discipline is real and enforced, but it has not yet built or launched a live product. Treat it as "ready to wire to real services behind the existing gates," not "shipping."

### 3.3 Shared spine (cross-cutting, founder-owned)

`guardrail/` (Constitution) · `governance/` (approval, config-guard, tool-permissions, desk-control) · `capital/` (Allocator + Budget Kernel) · `operator_os/` (state machine + Opportunity Router) · `broker/` · `loop/` · `ledger/` · `ops/` (kill-switch, health, backup, live-readiness) · `data/` · `db/` · `sharia/` · `dashboard/` · `alerts/`.

---

## 4. Security & Execution Guardrails — The Inversion of Trust

This is the heart of the system. The guarantees below are not policy or prompt text — they are **deterministic code paths with no AI in them**, each independently unit-tested.

### 4.1 The deterministic Trader Constitution

`Constitution.evaluate(action, portfolio_state) -> Decision`. A single function, no DB, no network (except the kill-switch read), fully pure. It enforces, in order:

0. **Kill switch** — if the halt file is present, **every** action is refused. Checked *inside* the gate, not at the loop entry, so there is no path around it.
1. **Withdrawals are forbidden** — `WITHDRAW` is unconditionally denied. The system can never move money out.
2. **No derivatives / leverage / shorting** — options, futures, swaps, CFDs, margin, forwards, and crypto-derivatives are prohibited instruments; `short` / `sell_short` sides are prohibited; leverage > 1.0 is refused.
3. **Whitelist-only** — a symbol must be on the founder-approved compliant whitelist even to be sold.
4. **Close-only for drift** — a frozen or no-longer-compliant holding may be **sold to de-risk** but never bought or increased.
5. **Phantom-sell guard** — cannot sell what is not held; cannot oversell.
6. **Thesis required** — no open/increase without a written invalidation, profit-take, and time-stop.
7. **Circuit breakers** — daily loss stop (−5%), weekly drawdown stop (−10%), rolling 5-day (−8%) and 14-day (−12%) velocity stops, post-breach cooldown freeze.
8. **Runaway-loop backstop** — max orders per day (default 10).
9. **Illiquidity / slippage gate** — rejects wide spreads (>0.5%) and orders exceeding 1% of 30-day ADV. **Fail-closed in live:** missing the data needed to clear the gate is a *block* in live mode (it skips gracefully only in paper).
10. **Concentration limits** — max 20% of fund per position, max 40% per sector.
11. **Tiered cash buffer** — a minimum cash reserve scaled by fund size; orders exceeding deployable cash after the buffer are refused.
12. **Money-movement gate** — in live mode, an order needs a founder approval id unless it is both within an auto-execute phase (≥2) and under the per-order envelope.

Whitelist additions are themselves gated: `ADD_WHITELIST` requires both a founder approver and a logged Sharia scan id — a whitespace-only "approval" is treated as no approval.

### 4.2 The Budget Kernel

`capital/budget_kernel.py` — checked **before** the Constitution's sizing logic. Deterministic and founder-owned:

- **Rolling spend limits:** per-action, daily, weekly, monthly. A request that breaches any limit is **rejected explicitly, never silently clamped.**
- **Capital buckets** (fractions of total fund, founder-owned): `core 0.50 · trader 0.15 · entrepreneur 0.20 · system 0.05 · emergency 0.10`. The Trader and Entrepreneur arms draw from separate buckets, so neither can starve the other or the core.
- Negative spend is rejected as a non-action.

### 4.3 The Edge Proof Engine (17 checks)

`trader/engine/edge_proof.py` — the evidence gate. Pure; runs 17 signal-conditioned checks and returns a gated `FullEdgeReport`. The blocking checks (a non-blocking check *records* but does not veto):

| # | Check | What it proves |
|---|---|---|
| 1 | `signal_definition` | A precise, hashed signal definition exists. |
| 2 | `source_provenance` | ≥2 independent sources for non-price events (quorum). |
| 3 | `point_in_time` | Returns computed from point-in-time prices (no look-ahead). |
| 4 | `sample_size` | Historical sample ≥ minimum. |
| 5 | `survivorship_control` | Survivorship-free source (warns until curated data wired). |
| 6 | `regime_filter` | Enough same-regime observations. |
| 7 | `forward_returns` | A forward-return distribution was built. |
| 8 | `benchmark_comparison` | Median **excess** return vs benchmark clears the bar. |
| 9 | `after_costs` | Net **positive after** estimated transaction cost + spread. |
| 10 | `worst_case` | Worst-case drawdown acceptable (or position small enough). |
| 11 | `vol_adjusted` | Volatility-adjusted return floor (soft). |
| 12 | `multiple_testing` | Excess clears a **penalized** bar scaled by # signals tested. |
| 13 | `signal_decay` | Recent edge not materially below the full sample. |
| 14 | `counter_signal_inventory` | Counter-signals enumerated (record). |
| 15 | `sharia_status` | A **clear Sharia pass at the decision date** (fail-safe — Sharia is #1). |
| 16 | `whole_share_feasible` | Price ≤ budget for a whole share. |
| 17 | `final_decision` | The recorded verdict, plus `data_quality` and `model_agreement` (model disagreement routes to the human-approval gate). |

The engine runs **enforcing** (blocks) or **shadow** (logs but does not block) — shadow mode is refused at phase ≥ 1, so a live system can never silently run un-gated.

### 4.4 The human-approval gate & phase model

`governance/approval.py` — **fail-safe by construction.** `is_approved(...)` returns true only for an explicit, recorded approval; missing, pending, or vetoed all resolve to **False**. The default approval callback **withholds** approval. Founder decisions (approve/veto, via Telegram) are recorded with `decided_by` for the audit trail.

**Phase model** (`config/limits.yaml`): `0 paper | 1 micro-live | 2 auto | 3 scale`. The system ships at **phase 0**. The live broker (`broker/live.py`) refuses to act unless phase ≥ 1 **and** live is explicitly enabled **and** credentials are present — all three, fail-safe.

### 4.5 Why the AI cannot edit, bypass, or overwrite the rules

This is the property the receiving team must be able to trust. It is enforced five independent ways:

1. **Config ownership.** All limits live in `config/limits.yaml`, whose header states the contract: *"The agent process must NOT have write access to this file. Changing autonomy = changing these numbers, deliberately, by you."* The Constitution loads these via `from_yaml`; defaults in code are equal-or-stricter. The single source of phase truth is this one file.
2. **Config guard.** `governance/config_guard.py` enforces that the agent cannot mutate the guardrail configuration at runtime.
3. **Tool-permission matrix.** `governance/tool_permissions.py` constrains which tools the agent may invoke at all — the proposer simply has no capability to reach the disposer's controls.
4. **Kill switch inside the gate.** The halt is read *within* `Constitution.evaluate`, so a halted system blocks every action regardless of which proposer or loop initiated it.
5. **Append-only audit.** The hash-chained ledger (`ledger/`) and `op_log` record every decision and fill; the published web state is a read-only mirror. There is no agent-callable path to rewrite history or move money out.

> **The rules are data, owned by a human, read by a deterministic function the AI cannot rewrite — and the AI is never handed the pen.**

---

## 5. User Interface & Oversight

Oversight is a first-class architectural component, not a reporting afterthought. The system is split so the human *always* sees, and *always* gates, what the operator does.

### 5.1 Brain / window / bridge

- **Brain** (Python) runs on the founder's machine — it holds the strategies, the gates, the 7 databases, and the secrets. It can never run on the public cloud.
- **Window** (Next.js 14 App Router, on Vercel) is a **read-only mirror.** It renders the published state and can only *queue* commands.
- **Bridge** (Supabase: Postgres + RLS + magic-link auth) carries the published snapshot one way and queued commands the other. Access is **friends-only, double-gated** (DB row-level security **and** an app-layer allowlist, both fail-closed). The Supabase service-role key is **brain-side only**, never in Vercel or the repo.

### 5.2 The analytics & decision-tracking surface (primary oversight mechanism)

The operator window's **decision-analytics panels are the mandatory oversight mechanism** — the place a human watches, in near-real-time, *every* call the operator makes:

- **Edge Proof verdicts** — for each candidate: signal, verdict (● EDGE / ○ NO EDGE), sample size, hit rate, benchmark excess, and the reason. *This is the analytics core: it shows why the system traded **or refused to**, which is the whole point.*
- **Safety posture** — the live guardrail gate as a set of boolean facts (N/total confirmed), each a real check, not a score.
- **Markets** (tabbed: Market / Watchlist / Hotlist) — real ingested numbers: FRED macro (Fed funds, 2Y/10Y, VIX, HY spread) + yield curve, the classified regime, the compliant universe with live price and 1-day/~1-month change, the curated watchlist, and computed movers.
- **The Kitchen** — each desk's status and the ranked, reasoned **Opportunity Board** the founder approves.
- **Paper equity curve**, **Portfolio KPIs**, **Positions**, **Guardrail decisions** (Constitution rejections with reasons), the **append-only Ledger**, and the **Sharia whitelist** with compliance status.

The same analytics render on the **local read-only dashboard** (`dashboard/`, the Camel Design System skin, offline / no-JS) so oversight does not depend on the cloud.

### 5.3 Read-only by design

The window cannot execute anything. Controls **queue** a command; the brain dequeues it on its next poll and runs it **through the full gate cascade** (approve/veto is founder-only, fail-closed, timestamped). The interface is itself a guardrail: there is no browser-side path to money or to the rules.

### 5.4 Alerts

`alerts/` delivers a founder brief and RED-ALERT events over Telegram / WhatsApp — including kill-switch trips and approval requests, so oversight reaches the founder rather than waiting to be polled.

---

## 6. Data Architecture

Seven purpose-scoped SQLite databases (WAL mode), accessed through one `CamelDbs` handle:

`camel_market` (prices, dividends, splits, watchlist) · `camel_macro` (observations, regime_history, event_reactions) · `camel_fundamentals` (company_facts, assets) · `camel_news` (news_events) · `camel_sharia` (whitelist, sharia_status, etf_holdings, sanctions) · `camel_portfolio` (orders, positions, ledger, runs, approvals, portfolios, portfolio_holdings, op_log) · `camel_learning` (learning_ledger, edge_reports, learning_proposals, research_evidence).

**Point-in-time discipline** on every decision-relevant table — `event_date · reported_at · ingested_at · known_at` — so backtests and the Edge Proof see only what was knowable at the decision time (no look-ahead bias). This was designed in before data accumulated; it cannot be retrofitted.

*(A Postgres / managed-DB migration is on the roadmap, not yet done; `db/dump_schema.py` already emits the authoritative schema as the migration reference.)*

---

## 7. Technical Stack

| Layer | Technology |
|---|---|
| **Brain language** | Python 3.12 (pure-stdlib gates; `yaml` for config; `pytest` for tests) |
| **Storage** | SQLite × 7 (WAL, point-in-time columns); Postgres migration roadmapped |
| **Market data** | **Alpaca** (paper account, IEX feed) for prices — via stdlib `urllib` to avoid a TLS-proxy cert issue |
| **Macro data** | **FRED** (Fed funds, DGS2/DGS10, VIX, HY credit spread) |
| **Other connectors** | SEC EDGAR RSS (8-K), Geopolitical Risk (GPR) CSV, OFAC SDN (sanctions), Stooq (fallback). 10 connectors total via the ingest orchestrator. |
| **Sharia screen** | AAOIFI methodology (`sharia/aaoifi.py`), single 30% threshold + cross-check |
| **Brokers** | Paper, Realistic-paper, Manual (Sahm path), Live (`broker/live.py` — gated OFF, refuses unless phase ≥ 1 + live-enabled + creds) |
| **Web window** | TypeScript + **Next.js 14** (App Router), React server + client components; deployed on **Vercel** |
| **Bridge / auth** | **Supabase** (Postgres, row-level security, magic-link auth); brain publishes via `ops/publish_state.py`, polls commands via `ops/command_poller.py` |
| **Scheduling** | Windows Task Scheduler (daily governed tick + weekly safety task) |
| **Messaging** | Telegram / WhatsApp (`alerts/`) |
| **Source control / CI** | Git → GitHub (`The-Camel`); Vercel auto-deploys `main` for the window |

---

## 8. Operational Logic — One Governed Tick

1. **Ingest** — `data/ingest.py` pulls prices (Alpaca) + macro (FRED) + events, stamping point-in-time columns.
2. **Classify** — the regime engine sets the macro context.
3. **Propose** — the Opportunity Router ranks candidates; a strategy emits an action with a written thesis.
4. **Prove** — Edge Proof runs its 17 checks (enforcing). No passing report → no buy. *No edge but capital → the edge-exempt DCA path into the compliant core.*
5. **Dispose** — Budget Kernel (spend/buckets) → Constitution (Sharia, risk, phase) → human-approval gate (phase-gated, withholds by default).
6. **Act** — paper / realistic-paper / manual / (gated) live broker writes orders + ledger + positions in **one atomic transaction** (rollback proven).
7. **Record** — append to the hash-chained ledger + `op_log`.
8. **Learn** — the learning layer mines outcomes and emits **propose-only** improvements (never self-applied).
9. **Publish** — `ops/publish_state.py` upserts the full snapshot to Supabase; the window mirrors it.

Entry point: `python -m loop.jobs tick [--realistic --notional N]`. Only **realistic** runs advance the ≥28-run "investment-valid" track-record clock that gates any future go-live readiness.

---

## 9. Build Status — What's Live vs. Roadmap

| Area | Status |
|---|---|
| Trust spine (Constitution, Budget Kernel, Edge Proof, approval, kill switch) | **Built, tested, enforced** |
| Trader arm (regime, strategies, portfolios, execution, sandbox, edge lab) | **Built** |
| Entrepreneur arm (constitution, product gate, build pipeline) | **Built as pure logic;** external integrations gated, not yet shipped |
| Data feeds (Alpaca prices, FRED macro) | **Live** |
| 7-DB architecture + point-in-time | **Built** |
| Web operator window + bridge | **Live** (`the-camel-five.vercel.app`), friends-only |
| Paper track record | **Accruing** (realistic-paper, ≥28-run clock running) |
| **S15 — paid feeds + go-live** | **Pending founder:** paid data vendors, live credentials, machine hardening, the phase-flip. *Going live is an explicit human act.* |
| Multi-source quorum enforcement, attribution, research-desk activation | **Roadmapped** (research desk ships **dormant** by default) |

**Tests:** 787 automated tests (pytest), last full green run in the current session.

---

## 10. Integration Notes & Handoff Checklist

For the receiving team, the load-bearing invariants to preserve in any review or integration:

1. **Never give the agent process write access to `config/limits.yaml`** or a runtime path to mutate guardrail config. This is the whole security model.
2. **The gates are pure and ordered.** Do not add a "trusted" path that skips Edge Proof → Constitution → Budget Kernel → approval. The assembled loop re-checks the same action object; keep it that way.
3. **Fail-safe defaults.** Approval withholds by default; the live broker refuses by default; shadow mode is refused at phase ≥ 1; missing liquidity data blocks in live. Preserve every default-to-no.
4. **Sharia is check #1 and a hard wall** in both arms (`HARAM_TERMS`, AAOIFI screen, decision-date status). It is non-negotiable, not a tunable.
5. **Secrets are brain-side only.** The Supabase service-role key, broker creds, and FRED key live in a git-ignored brain-side `.env`. Nothing sensitive belongs in Vercel or the repo.
6. **Phase is the single autonomy dial.** It lives in one file; ≥2 enables auto-execution under the envelope; live requires explicit enablement + creds. Treat any change as a deliberate, reviewed act.
7. **Point-in-time columns cannot be retrofitted.** Any new decision-relevant table must carry `event_date / reported_at / ingested_at / known_at` from day one.

---

## Appendix A — Package Map (top level)

```
guardrail/        the Trader Constitution (the first wall)
governance/       approval · config_guard · tool_permissions · desk_control · beginner_mode
capital/          Allocator + Budget Kernel
operator_os/      state machine + Opportunity Router
trader/           regime · events · engine(EdgeProof) · edgelab · execution · strategies · portfolios · sandbox
entrepreneur/     constitution · product_gate · build_pipeline (the other arm)
broker/           paper · realistic · manual · live(gated)
loop/             runner · assembled · driver · jobs · scheduler  (the runtime keystone)
data/             ingest + 10 connectors + provenance + watchlist + quality
sharia/           AAOIFI screen · whitelist · sanctions · universe
db/               7 SQLite DBs + CamelDbs + schema tooling
ledger/           hash-chained audit
ops/              kill_switch · health · backup · live_readiness · publish_state · command_poller
dashboard/        local read-only operator dashboard (Camel Design System)
alerts/           Telegram / WhatsApp brief + RED-ALERT
research/          analyst-desk framework (dormant by default, evidence-only)
learning/         4-tier learning (propose-only)
web/              Next.js 14 operator window (Vercel) + Supabase bridge
config/           limits.yaml (FOUNDER-OWNED — the autonomy dial)
```

## Appendix B — Glossary

- **Inversion of trust** — the AI is the least-privileged component; it proposes, deterministic gates dispose.
- **Edge Proof** — the 17-check evidence gate; no alpha trade without a passing report.
- **No-Edge → DCA** — when there's capital but no proven edge, dollar-cost-average into the compliant core (edge-exempt).
- **Phase** — the autonomy level (0 paper → 3 scale), set only by the founder in `limits.yaml`.
- **Realistic-paper / investment-valid run** — a paper fill modeling spread/fees/whole-shares; only these advance the go-live readiness clock.
- **Brain / window / bridge** — Python brain (private), Next.js window (read-only mirror), Supabase bridge.

---

*End of report. This document reflects the codebase as built; where a capability is designed but not yet shipped (paid feeds, Entrepreneur external integrations, Postgres migration, research-desk activation), it is labeled as such. No statement here should be read as a claim that the system trades real capital — it does not, and cannot, without an explicit founder go-live act.*
