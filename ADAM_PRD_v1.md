# 📐 ADAM × StockSense v11 — Product Requirements Document
### The buildable blueprint for a guardrailed autonomous operator
*PRD v1.0 · June 2026 · Companion to the Build Spec v0.2 · Target runtime: Mac mini (KSA), founder-operated*

---

> ⚠️ **Stance.** This PRD describes software you will build and run on your own machine to manage **your own** capital. It is engineering/decision-support documentation — not financial, legal, or Sharia advice. The system is designed so that **live money movement is impossible without a human approval step** until you explicitly graduate it through measured phases. Withdrawals are disabled at the broker key level. Nothing here should run with real capital before Phase 0 acceptance criteria are met.

---

## 1. Summary

**What we're building:** an always-on AI operator ("ADAM") that runs a continuous Observe → Thesis → Choose → Act → Measure → Learn loop across two domains — **Trader ADAM** (Sharia-compliant markets) and **Entrepreneur ADAM** (Sharia-compliant AI products) — where every consequential action is filtered through a deterministic **Guardrail Constitution** the agent cannot modify.

**Why:** to convert StockSense v11 (a manual decision-support doc) into a self-operating system that compounds knowledge and, once proven, capital — without exposing you to ruin, Sharia violations, or unattended money movement.

**Definition of success (north star):** ADAM completes ≥ 4 weeks of fully autonomous **paper** operation with **zero guardrail breaches**, a reconciling ledger, and an invalidation point on every position — earning the right to a tightly-capped live phase.

---

## 2. Goals & non-goals

**Goals**
- G1 — A constraint engine that makes prohibited actions *impossible*, not just discouraged.
- G2 — Autonomous EOD trading loop on a **paper** account (Phase 0), graduating to capped live (Phase 2+).
- G3 — Sharia compliance enforced **as code** (whitelist + ratio re-screen + business-model screen).
- G4 — One Entrepreneur product shipped end-to-end (build → deploy → can accept payment).
- G5 — Full auditability: every decision and transaction logged and reconcilable.
- G6 — Founder control: approval channel + kill switch reachable from your phone/laptop.

**Non-goals (explicitly out of scope for v1)**
- N1 — Unattended live trading on day one. (Earned, not granted.)
- N2 — Leverage, margin, options, shorting, crypto derivatives. (Sharia + risk.)
- N3 — Managing anyone else's money. (Triggers KSA CMA licensing — §11 of Spec.)
- N4 — High-frequency / intraday trading. (Positional EOD only.)
- N5 — Auto-withdrawals or fund transfers of any kind.

---

## 3. Measurable phase exit criteria

| Phase | Capital | Autonomy | **Exit criteria (all must pass)** |
|---|---|---|---|
| **0 Paper** | $0 | Full loop, simulated orders | ≥28 days continuous run · 0 guardrail breaches · 100% positions had invalidation point · ledger reconciles to broker paper statement · ≥1 Entrepreneur product deployed |
| **1 Micro-live** | $100–500 | Human approves every trade | ≥28 days · 0 unapproved executions · approval round-trip < 5 min · weekly broker-vs-ledger reconciliation clean |
| **2 Guardrailed auto** | scale to fund | Auto ≤ per-order envelope on whitelist | ≥60 days · 0 limit breaches · daily-loss-stop fired correctly in ≥1 test · Sharia re-screen ran on schedule |
| **3 Scale** | full $10K | Wider envelope | track record (Sharpe/hit-rate vs base rates) justifies each envelope increase |

---

## 4. Personas

- **Founder (you):** sets limits, approves live actions, holds the kill switch and secrets. Not in the loop for research/build.
- **Trader ADAM:** sub-agent — forms market theses, sizes to invalidation, prepares orders.
- **Entrepreneur ADAM:** sub-agent — chooses/builds/deploys compliant AI products.
- **Sharia Auditor:** sub-agent with **veto** wired to the Constitution; no action ships if it objects.
- **Risk/Compliance sub-agent:** runs the §2 checks pre-execution.

---

## 5. System components & functional requirements

Each component lists an ID, requirement, and acceptance criterion (AC). Build order is in §9.

### 5.1 Guardrail Service (the Constitution) — *highest priority*
- **FR-G1** Expose a pure function `evaluate(action) → {allow:bool, reason}`. Every action (trade, spend, deploy, data-write) routes through it.
- **FR-G2** Enforce: Sharia whitelist, position ≤20% fund, sector ≤40%, per-order ≤ envelope, daily-loss-stop −5%, weekly −10%, no leverage/derivatives, invalidation-point-required.
- **FR-G3** No override path callable by the agent. Limits live in config the agent process cannot write.
- **FR-G4** Every evaluation (allow *and* reject) is logged to `guardrail_events`.
- **AC:** unit tests cover each limit at boundary (e.g., 19.9% allow / 20.1% reject); a scripted "rogue action" suite is 100% rejected.

### 5.2 Sharia Gate module
- **FR-S1** Maintain a `whitelist` table; only listed instruments/businesses are actionable.
- **FR-S2** Adding a name requires a logged `SHARIA SCAN` record + founder approval flag.
- **FR-S3** Quarterly job re-runs AAOIFI ratios; non-compliant drift → set instrument `frozen=true` + alert.
- **FR-S4** Business-model classifier screens Entrepreneur PRDs for haram lines; reject + reason.
- **AC:** an off-whitelist ticker and a haram business idea are both auto-rejected with a logged reason.

### 5.3 Data Ingestion
- **FR-D1** Scheduled EOD pull per market (US after 4pm ET; Saudi/Egypt scaffolded) into `prices`.
- **FR-D2** Triangulate: store source per datapoint; flag if two sources disagree >0.5%.
- **FR-D3** Provider abstraction: Alpaca data (US) now; EODHD adapter stub for 3-market later.
- **AC:** a daily run populates OHLCV for all whitelist tickers; disagreement flag fires on injected bad data.

### 5.4 Thesis / Base-Rate Engine
- **FR-T1** For any signal, produce a base-rate card: sample N, horizon, hit rate, median magnitude, priced-in note, counter-signals, overfitting check.
- **FR-T2** A position cannot be proposed without a populated invalidation trigger, profit-take, and time stop.
- **AC:** attempting to open a position with empty invalidation is rejected by the Guardrail Service.

### 5.5 Loop Runner (Hermes harness)
- **FR-L1** Scheduled run executes Observe→Thesis→Choose→Act→Measure→Learn; step 4 calls Guardrail Service first.
- **FR-L2** Persist loop state/run history; resume cleanly after restart (persistence).
- **FR-L3** Configurable cadence (default: once daily post-close).
- **AC:** a full loop runs unattended, writes a research-log entry, and survives a process kill/restart mid-run.

### 5.6 Capital Allocator
- **FR-C1** Allocate fund across Trader/Entrepreneur within §2.2 limits; never exceed cash/concentration rules.
- **FR-C2** Respect tiered cash rule by current book size.
- **AC:** allocation requests that would breach a cap are rejected, not clamped silently (logged).

### 5.7 Order Manager
- **FR-O1** Adapter pattern: `PaperBroker` (Alpaca paper) for Phase 0; `LiveBroker` (Alpaca/IBKR) behind a feature flag for Phase 1+.
- **FR-O2** Live orders require an `approval_id` from the Approval Channel; reject if absent (Phase 1) or over-envelope (Phase 2).
- **FR-O3** Broker API keys must be **trade-only, withdrawals disabled**; startup check refuses to run a live broker key that has withdrawal scope (where detectable) and logs a warning.
- **AC:** in Phase 1 mode, an order without `approval_id` is refused; paper orders fill and write to `orders`+`ledger`.

### 5.8 Approval Channel
- **FR-A1** Push a proposed action (with base-rate card) to founder; capture approve/veto with timestamp + identity.
- **FR-A2** Timeout default = veto (fail-safe). Configurable window.
- **AC:** approve → executes; veto/timeout → logged, no execution.

### 5.9 Ledger & Audit
- **FR-X1** Append-only `ledger`; no updates/deletes by the agent role (DB permissions).
- **FR-X2** Daily encrypted off-box backup; weekly reconcile job vs broker statement → diff report.
- **AC:** reconciliation report is clean on paper account; tampering attempt by agent role is denied by RLS.

### 5.10 Dashboard
- **FR-V1** Port the v11 HTML dashboard to read live Supabase state (positions, P&L, ledger, guardrail events, Sharia flags, milestone).
- **FR-V2** Read-only for the operator view; no order entry from the dashboard.
- **AC:** dashboard reflects a paper trade within one refresh; shows guardrail-event feed.

### 5.11 Entrepreneur Pipeline
- **FR-E1** PRD → `/goal` → Codex build → deploy (Netlify) → register product in `products` table.
- **FR-E2** Business-model passes Sharia screen (FR-S4) before any build starts.
- **FR-E3** Spend (hosting, API) routes through Guardrail Service against an Entrepreneur budget.
- **AC:** one compliant product builds, deploys to a live URL, and is capable of accepting payment (Stripe test mode acceptable for Phase 0).

### 5.12 Monitoring, Alerting, Kill Switch
- **FR-K1** Founder kill command (over Tailscale) halts new actions immediately; does **not** auto-liquidate (no panic selling).
- **FR-K2** Health checks + alerts on: loop failure, data staleness, guardrail near-miss, reconciliation diff, daily-loss-stop.
- **AC:** kill command stops the next loop tick; a simulated daily −5% halts trading and alerts.

---

## 6. Data model (Supabase / Postgres)

```
whitelist        (id, symbol, asset_type, sharia_status, frozen, approved_by, scanned_at, source)
instruments      (symbol, name, sector, market, currency)
prices           (symbol, date, open, high, low, close, volume, adj_close, source, ingested_at)
theses           (id, symbol, side, thesis, invalidation, profit_take, time_stop,
                  base_rate_json, created_by, created_at, status)
orders           (id, symbol, side, qty, type, limit_price, status, broker, mode,
                  approval_id, thesis_id, created_at, filled_at, fill_price)
positions        (symbol, qty, avg_cost, market_value, unrealized_pnl, updated_at)
ledger           (id, ts, type, symbol, amount, balance_after, ref, hash)        -- append-only
guardrail_events (id, ts, action_json, decision, reason, limit_hit)
approvals        (id, action_ref, status, requested_at, decided_at, decided_by, channel)
products         (id, name, url, business_model, sharia_status, status, mrr, created_at)
runs             (id, started_at, ended_at, phase, steps_json, outcome)
config           (key, value)                                                    -- limits, envelopes, cadence
```
**Rules:** the `adam` DB role has INSERT on `ledger` only (no UPDATE/DELETE — RLS); `config` is read-only to `adam`, writable only by `founder`.

---

## 7. External integrations

| Service | Use | Phase | Notes |
|---|---|---|---|
| **Alpaca** | Paper + live trading API, US data | 0+ | Free paper; IEX data free; trade-only keys |
| **IBKR** | Alt/expanded live venue | 2+ | Broader markets incl. Saudi via SNB |
| **OpenAI / Claude API** | Reasoning, base-rate cards, Codex builds | 0+ | Usage-metered |
| **Supabase** | DB, auth, RLS, storage | 0+ | Free → Pro |
| **Netlify** | Deploy dashboard + products | 0+ | — |
| **Cloudflare** | DNS/edge/security | 1+ | — |
| **Tailscale** | Private remote access + kill switch path | 0+ | ACLs to your devices |
| **Notification** (Pushover/Telegram bot) | Approval channel + alerts | 1+ | One-tap approve/veto |
| **Stripe** | Entrepreneur payments | 0 test / 1 live | test mode for Phase 0 |
| **EODHD** | 3-market EOD data | later | when EGX/Tadawul go live |

---

## 8. Tech stack & repo structure

**Stack:** Python 3.12 (agent + guardrail + loop) · Supabase (Postgres) · TypeScript/HTML (dashboard) · GitHub Actions or launchd/cron for scheduling · pytest for the guardrail suite.

```
adam/
├─ guardrail/        # the Constitution — pure functions + config loader + tests
├─ sharia/           # whitelist, ratio re-screen job, business classifier
├─ data/             # ingestion adapters (alpaca, eodhd stub), triangulation
├─ engine/           # thesis / base-rate engine
├─ loop/             # Hermes loop runner, state, scheduler entrypoint
├─ capital/          # allocator
├─ broker/           # PaperBroker, LiveBroker adapters, money gate
├─ approval/         # notification + approve/veto handler
├─ ledger/           # append-only writer + reconciliation
├─ entrepreneur/     # PRD→build→deploy pipeline
├─ subagents/        # bull / bear / sharia-auditor / compliance (BOARDROOM)
├─ dashboard/        # v11 HTML reading Supabase
├─ ops/              # kill switch, health checks, backups
├─ config/           # limits.yaml (founder-owned), .env.example
└─ tests/            # guardrail boundary + rogue-action suites
```

---

## 9. Build roadmap (sequenced sprints)

**Sprint 1 — Foundation (the safety core).** Supabase schema + RLS · Guardrail Service + full test suite · `limits.yaml`. *Gate: rogue-action suite 100% rejected.*

**Sprint 2 — Sharia + data.** Whitelist + ratio re-screen job · business-model classifier · Alpaca paper data ingestion + triangulation. *Gate: off-list + haram both rejected; daily prices land.*

**Sprint 3 — The loop (paper).** Thesis/base-rate engine · loop runner · PaperBroker · ledger + reconciliation · capital allocator. *Gate: full unattended loop runs nightly, ledger reconciles.*

**Sprint 4 — Visibility + control.** Dashboard on live Supabase · monitoring/alerts · kill switch over Tailscale. *Gate: kill works; daily-loss-stop simulation halts.*

**Sprint 5 — Entrepreneur track.** PRD→build→deploy pipeline · ship one compliant product (Stripe test). *Gate: live URL, payment-capable.*

**→ Run Phase 0 for 28+ days. Meet §3 exit criteria. Only then build the Approval Channel + LiveBroker (Sprint 6) for Phase 1.**

---

## 10. Machine setup (what you do on the Mac mini)

> You run it; I supply code + a README per sprint. High-level prerequisites:

1. **Accounts:** Alpaca (paper keys now), Supabase project, OpenAI/Claude API key, GitHub repo, Netlify, Tailscale, a Pushover/Telegram bot (Phase 1).
2. **Machine:** install Python 3.12, clone repo, `pip install -r requirements.txt`, copy `.env.example`→`.env` (keys go here, never in git).
3. **Secrets:** Alpaca key scoped **trade-only, withdrawals OFF**. Enable FileVault + firewall + auto-updates. Tailscale ACL locked to your devices, MFA everywhere.
4. **Schedule:** `launchd` (macOS) job runs the loop entrypoint post-close; a separate cron runs the quarterly Sharia re-screen.
5. **Verify:** run `pytest` (guardrail suite must pass) before first loop; confirm dashboard loads; test the kill command.

---

## 11. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Agent finds an override path | Limits in founder-only config; RLS; no agent-callable override; rogue-action test suite |
| API key leak | Trade-only keys (no withdrawals), secrets manager, quarterly rotation, kill switch |
| Bad data → bad trade | Triangulation + disagreement flag + anomaly halt |
| Sharia drift | Quarterly re-screen freezes drifted names + alerts |
| Overnight gap loss | Positional sizing, position/loss caps, daily-loss-stop |
| Scope creep into live too early | Hard phase gates with measurable exit criteria (§3) |
| KSA licensing if it ever manages others' money | Personal-use only; legal consult before any change (N3) |

---

## 12. Open decisions (need your input as we build)

1. **Live broker for Phase 1:** Alpaca (cleaner API) vs IBKR (broader). *(Paper = Alpaca regardless.)*
2. **Notification channel:** Pushover vs Telegram bot for approvals.
3. **First Entrepreneur product:** what compliant tool should ADAM ship as the proving build?
4. **Canonical Sharia screener:** Musaffa vs Zoya as the source of truth for the whitelist.
5. **Limit values:** confirm the starting numbers in `limits.yaml` (defaults in §2.2 of the Spec).

---

## 13. Definition of done (v1)
The system is "up and running" when: the guardrail suite is green; ADAM runs the full loop unattended on paper nightly; the dashboard and ledger reflect it; the kill switch and alerts work; one compliant product is deployed; and you have 28 days of clean paper operation meeting every §3 Phase-0 criterion — at which point Phase 1 (capped, human-approved live) is unlocked.

---

*ADAM × StockSense v11 · PRD v1.0 · Build the safety core first; earn autonomy with evidence. Not financial, legal, or Sharia advice.*
