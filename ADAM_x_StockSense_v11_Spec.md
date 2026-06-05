# 🜂 ADAM × StockSense v11 — Autonomous Operator Build Spec
### A guardrailed AI operator that picks Sharia-compliant opportunities and acts within hard limits
*Version 0.1 · June 2026 · Merges the ADAM 6-layer stack with the StockSense v11 investment brain*

---

> ⚠️ **Disclaimer & operating stance.** This is an engineering/decision-support spec, not financial or legal advice. The design deliberately keeps **live money movement behind a human-approval gate** and routes all autonomy through hard-coded constraints. An agent that places trades or moves funds entirely unattended is a liability, not a feature — this spec is built so ADAM can be aggressive *inside the rails* and powerless *outside them*.

---

## 0. The one-sentence design

**ADAM is free to think, research, build, and propose autonomously — but every action that touches the Sharia gate, real capital, or the outside world passes through a constraint engine ADAM cannot edit.** Hermes powers it, Paperclip orchestrates it, the Guardrail Constitution contains it, StockSense v11 is its investing conscience.

---

## 1. What we already have vs. what ADAM adds

| Capability | StockSense v11 (built) | ADAM adds |
|---|---|---|
| Investing brain (Observe→Thesis→Act→Measure→Learn) | ✅ base-rate engine, invalidation discipline, research log | Runs the loop **autonomously** on a schedule |
| Sharia gate | ✅ documented hard wall + scan | Turns it into **code that blocks actions** |
| Tracker + dashboard | ✅ Excel + HTML | Becomes a **live service** ADAM reads/writes |
| Two operators | ⚠️ implicit (markets only) | **Trader ADAM + AI Entrepreneur ADAM** |
| Capital | ⚠️ manual | **$10K fund** with a guardrailed allocator |
| Memory / persistence | ⚠️ a doc you reload | **Always-on machine + database** |
| Execution surface | ❌ none | GitHub / Supabase / Netlify / Playwright |

**The honest gap:** v11 assumes *you* are in the loop. ADAM removes you from the loop for everything *except* the three things that can actually hurt you — Sharia violations, losing money, and acting on the live internet. Those stay gated.

---

## 2. The Guardrail Constitution (Layer 0 — the part that makes autonomy safe)

These are not prompts. They are **deterministic checks in code** that sit between ADAM's intent and any real action. ADAM proposes; the Constitution disposes. If a proposed action fails any check, it is **rejected and logged** — no override path exists in the agent.

### 2.1 The Sharia Gate, as code
- **Universe whitelist.** ADAM may only act on instruments/businesses on a pre-screened compliant list (seed: SPUS, HLAL, MNZL + any name that has passed a logged `SHARIA SCAN`). Anything off-list is auto-rejected at the *planning* stage, before capital is ever considered.
- **Business-activity filter.** For *AI Entrepreneur ADAM*, the business model itself is screened — no haram lines (conventional finance, alcohol, tobacco, gambling, pork, adult, weapons/defense). A coded keyword+classifier gate on the PRD.
- **Ratio re-screen.** Quarterly job re-runs AAOIFI ratios (debt/mktcap <33%, cash+interest-sec/mktcap <33%, non-compliant income <5%); any name that drifts non-compliant is frozen and flagged.
- **No interest, no leverage, no derivatives, no margin, no short-selling** — both a Sharia requirement and a risk control. Hard-blocked.

### 2.2 Capital & risk limits (the numbers ADAM cannot exceed)

| Guardrail | Limit (tunable) | Why |
|---|---|---|
| Max single position | 20% of fund | No single-name blow-up |
| Max sector concentration | 40% | v11 sector guardrail |
| Min cash buffer | per v11 tiered rule (deploy-don't-hoard < $1k; 10–15% to $10k) | Liquidity + discipline |
| Max single auto-trade | **$0 live until Phase 2; then ≤ $50/order** | Caps any single mistake |
| Daily loss stop | −5% of fund → **halt + notify** | Circuit breaker |
| Weekly drawdown stop | −10% → **freeze all trading, founder review** | Kill switch |
| Leverage | 0 (hard) | Sharia + risk |
| Invalidation point | **required** before any position opens | v11 rule #4, enforced |

### 2.3 The money-movement gate (the most important rule)
- **Live trades and any fund withdrawal require human approval** until ADAM has a logged track record (Phase 2+), and even then only **auto-execute inside the ≤$50/order envelope on whitelist names**. Everything larger queues for your one-tap approval via the remote channel.
- ADAM **prepares** the order (ticker, size, entry, invalidation, base-rate card) → you **approve/execute**. This is the defensible posture and the one I can support.
- **Brokerage reality check:** Sahm (your current app) is whole-share retail with **no trading API** → ADAM can't place orders there programmatically without fragile UI automation (Playwright), which you should *never* point at live orders unattended. For real Trader-ADAM autonomy you'd need an **API broker that is also Sharia-workable** (e.g., Interactive Brokers / Alpaca with a self-imposed compliant whitelist). Treat this as a prerequisite decision, not a detail.

### 2.4 Kill switch & audit
- **Founder kill switch** over Tailscale: one command halts the loop and flattens nothing automatically (no panic selling — v11 RED ALERT ethos) but stops new actions.
- **Immutable ledger.** Every decision, every order, every $ in/out written to an append-only log (Supabase + daily export). "Every transaction is logged" is the floor, not the ceiling.
- **Anomaly halt.** Unexpected price gap, data-source disagreement (v11 triangulation rule), or guardrail near-miss → auto-pause for review.

---

## 3. Mapping the 6 ADAM layers to our build

### Layer 1 — Intelligence (the brains)
- **Codex** = builder (turns goals/PRDs into working code for Entrepreneur ADAM).
- **OpenAI/Claude API** = reasoning, the StockSense v11 *investment cortex* (base-rate engine, BOARDROOM debate, EARNINGS CHECK).
- **PRD → /goal → build** is the spine for the Entrepreneur side. For the Trader side, the "PRD" is a **thesis card** (v11 §5) that must include sample size, hit rate, what's priced in, and an invalidation point.

### Layer 2 — Harness (intelligence → operator)
- **Hermes Agent** = the always-on harness: **Memory** (the research log + knowledge files), **Autonomy** (the loop runner), **Persistence** (the machine + DB), **Planning** (PRD/thesis generation).
- **Paperclip** = orchestration: **Budgets** (capital allocator under §2.2), **Goals**, **Sub-agents**, **Coordination**, **Company OS**.
- **Sub-agents map directly to v11's BOARDROOM:** `Tech-Growth Bull` · `Risk-Aware Bear` · **`Sharia Auditor`** (with veto power wired to the Constitution). Add a `Compliance/Guardrail` sub-agent that runs §2 checks before anything ships.

### Layer 3 — Execution (where it ships)
- **GitHub** (build/version), **Supabase** (state: positions, ledger, research log, whitelist), **Netlify** (deploy the v11 dashboard + any Entrepreneur products), **Cloudflare** (security/edge), **Tailscale** (private remote access), **Playwright** (web automation: data scraping, *not* live orders).
- The v11 **HTML dashboard becomes the live UI**; the **Excel tracker logic moves into Supabase** so ADAM reads/writes positions programmatically.

### Layer 4 — Capital ($10K fund)
- One **$10K working-capital pool** ADAM allocates between Trader and Entrepreneur — **but only within §2.2 limits**, and live trades gated per §2.3.
- **No fixed buckets** (per the slide) is fine *only because* the Constitution caps concentration and per-order size. "ADAM decides allocation" is safe when the decision space is pre-bounded.
- **Differentiated read:** the **Entrepreneur side is the better place to let ADAM run hot.** Building/deploying/selling AI tools has bounded downside (you lose build time + hosting $) and uncapped upside, with far less regulatory and ruin risk than autonomous trading. **Lead autonomy with Entrepreneur ADAM; keep Trader ADAM on a tight leash longer.**

### Layer 5 — Physical
- **Mac mini (KSA) + 5G + Tailscale + founder laptop.** Good. The real work here is **security hardening**, because a remotely-accessible machine that controls money is a target: dedicated user, full-disk encryption, Tailscale ACLs + MFA, no inbound ports, secrets in a manager (never in code/chat — mirrors your EODHD-key rule), automatic patching, and a daily encrypted backup of the ledger off-box.

### Layer 6 — The ADAM Loop (with guardrail checkpoints)
```
1 Observe Signals      → data pulled per v11 §12 sources (EOD, triangulated)
2 Form Thesis          → base-rate card REQUIRED (v11 §5)  ──┐
3 Choose Path          → Trader or Entrepreneur               │ Guardrail
4 Act with Capital     → ✋ Sharia gate + risk limits + money │ checkpoints
                         gate (§2) BEFORE any execution     ──┘
5 Measure Outcome      → P&L / product metrics → ledger
6 Learn + Reallocate   → update base rates, re-screen, resize
```
Each arrow into step 4 passes through the Constitution. That is the whole safety model.

---

## 4. Trader ADAM vs AI Entrepreneur ADAM

| | Trader ADAM | AI Entrepreneur ADAM |
|---|---|---|
| Job | Trade compliant markets, seek asymmetric setups | Build/launch/sell scalable AI products |
| Sharia screen | Instrument whitelist (§2.1) | Business-model screen (§2.1) |
| Downside profile | **Ruin risk** — capped hard (§2.2/2.3) | Bounded (build time + hosting) |
| Autonomy level | Lowest — human-gated trades | Highest — auto-build within budget |
| Maps to v11 | base-rate engine, invalidation, tracker | `Analyze`, PRD→build, moat matrix |
| First milestone | Paper-trade the compliant ETF rotation | Ship one small AI tool end-to-end |

---

## 5. Phased rollout — the safe path to "auto within guardrails"

**Phase 0 — Paper / dry run (4–8 weeks).** Full loop, **zero live money.** ADAM observes, forms thesis cards, chooses paths, *simulates* trades, builds one real Entrepreneur product. Goal: prove the Constitution rejects every bad action. Exit criteria: 0 guardrail breaches, every position had an invalidation point, ledger reconciles.

**Phase 1 — Micro-live, human-approved (4+ weeks).** Real but tiny ($100–500). **Every trade you approve.** Entrepreneur side may auto-deploy within a small hosting budget. Build the approval channel (push notification → one-tap approve/veto).

**Phase 2 — Guardrailed auto (gated).** Auto-execute trades **only**: on the whitelist, ≤ per-order envelope, within all §2.2 limits, with daily loss stop live. You get notified and can veto within a window. Entrepreneur ADAM runs largely autonomously.

**Phase 3 — Scale the envelope.** Raise per-order/position limits *only* as the logged base-rate track record justifies it. Autonomy is **earned by evidence**, never granted by default.

---

## 6. Prerequisites & open decisions (yours to make)

1. **Broker with an API + your Sharia stance** — Sahm has no API. Pick the execution venue before Trader ADAM can be more than paper. *(decision)*
2. **Sharia authority for the coded gate** — which standard/screener is canonical (AAOIFI via Musaffa/Zoya), and who signs off on the whitelist. *(decision)*
3. **Legal/regulatory** — automated trading and running a revenue business from KSA have compliance implications; worth a professional check before live capital. *(flag — not advice)*
4. **Secrets & security owner** — who holds the keys, where they live, MFA on everything. *(decision)*
5. **Definition of "done" per phase** — the exit criteria above, made measurable. *(decision)*

---

## 7. Build backlog (what Codex/Hermes actually builds first)

1. **Supabase schema** — `positions`, `orders`, `ledger`, `whitelist`, `research_log`, `theses`, `guardrail_events`.
2. **Guardrail service** — pure function `evaluate(action) → allow | reject(reason)` implementing §2; unit-tested against edge cases.
3. **Loop runner (Hermes)** — scheduled Observe→…→Learn with a Constitution checkpoint before step 4.
4. **Sharia gate module** — whitelist + ratio re-screen job + business-model classifier.
5. **Approval channel** — notify → one-tap approve/veto; nothing live executes without it (Phase 1).
6. **Dashboard port** — v11 HTML reading live Supabase state; ledger view.
7. **First Entrepreneur build** — one small, compliant AI tool, end-to-end, as the autonomy proving ground.

---

## 8. Naming & identity
The post calls it ADAM ("two operators, one learning system"). Your instance can keep ADAM as the operator and **StockSense v11 as its investing conscience / Sharia auditor**. Hermes = the body, Paperclip = the manager, the Constitution = the law, ADAM = the will.

---

## 9. Broker decision — the Trader-ADAM execution venue *(refined with June 2026 facts)*

The Sahm blocker is real, but the path around it is clearer than expected. Two API brokers are reachable from KSA, and one of them solves Phase 0 for free.

| | **Sahm** (current) | **Alpaca** | **Interactive Brokers (IBKR)** |
|---|---|---|---|
| Trading API | ❌ none | ✅ API-first (built for this) | ✅ TWS API · Web API · FIX |
| **Paper-trading API** | ❌ | ✅ **free** — ideal for Phase 0 | ✅ paper account |
| KSA access | ✅ (your account) | ✅ supported; partnered w/ Saudi's **Derayah** | ✅ KSA residents; even Saudi Exchange via **SNB Capital** |
| Fractional shares | ❌ whole only | ✅ | ✅ |
| Sharia screening | manual | none native → **you self-screen via whitelist** | none native → **you self-screen via whitelist** |
| Best for | manual whole-share buys | **automation + Phase 0 paper** | breadth, global markets, serious scale |

**Refined recommendation:**
- **Phase 0 runs on Alpaca's free paper-trading API** — full programmatic loop, zero real money, zero new risk. This removes the last excuse to skip the dry run.
- **For live (Phase 1+), Alpaca is the cleaner developer experience; IBKR is the heavier, broader institution-grade venue.** Pick on temperament: Alpaca if you want clean REST and fractional micro-orders; IBKR if you want one account spanning US + Saudi + global.
- **Neither screens for Sharia** — compliance stays *your* coded whitelist (Constitution §2.1). That's fine; it's actually cleaner than trusting a broker's label.
- **Keep Sahm** for manual, conviction whole-share buys. It doesn't have to be the automation venue.

⚠️ *Confirm live-account eligibility and documentation directly with the broker for your residency before funding — not advice.*

## 10. Security hardening — the part that protects a money-controlling machine

A remotely-accessible box that touches capital is a target. Minimum bar before any live phase:

- **Identity & access:** dedicated non-admin OS user for ADAM; Tailscale ACLs locked to your devices only; **MFA on every account** (broker, OpenAI, Supabase, GitHub, email); no inbound ports open to the public internet.
- **Secrets:** broker keys + API keys in a secrets manager (or at minimum an encrypted `.env` outside the repo) — **never in code, never in chat, never in the knowledge doc** (mirrors your EODHD-key rule). Rotate quarterly.
- **Machine:** full-disk encryption (FileVault), automatic security updates, firewall on, screen-lock.
- **Broker-side blast radius:** use API keys scoped to **trading only — withdrawals disabled at the broker.** Even a fully compromised key then cannot move money *out*, only trade within the Constitution.
- **Ledger safety:** append-only ledger + **daily encrypted off-box backup**; reconcile broker statement vs ledger weekly.
- **Recovery:** written runbook for "key leaked / machine compromised" → revoke keys, kill Tailscale, halt loop.

> The single highest-leverage control: **disable withdrawals on the API key.** It converts the worst case from "fund drained" to "some bad trades inside caps."

## 11. KSA legal & regulatory flags *(flag, not advice — verify with a professional)*

- **Personal vs. service is the key line.** Automating *your own* account is materially different from *offering* automated/robo-advisory to others. In **March 2026 the Saudi CMA approved a robo-advisory framework** — but it governs **licensed Capital Market Institutions offering the service to clients** (algorithm testing ≥10 days pre-launch, risk disclosures, diversification rules). If ADAM ever manages money for anyone but you, that framework — and licensing — is in scope.
- **Foreign-securities rule worth noting:** the CMA framework expects securities listed outside KSA to be supervised by a regulator of *equivalent* standard (US SEC qualifies) — relevant if you scale.
- **Diversification echo:** the CMA's own eligibility rule excludes portfolios *concentrated in a single asset* — which independently validates the Constitution's position/sector caps (§2.2).
- **The Entrepreneur side** (running a revenue-generating online business from KSA) has its own commercial-registration/tax considerations separate from securities law.
- **Action:** a one-hour consult with a KSA capital-markets lawyer before live trading is cheap insurance. The Hammad & Al-Mehdar commentary on algorithmic-trading legal challenges is a reasonable starting read.

## 12. Run-cost estimate *(separate from the $10K fund)*

**One-time**
- Mac mini (M4 base) ~$599 — or use hardware you already own · domain ~$12/yr

**Monthly (small scale)**

| Item | Est. / mo | Note |
|---|---|---|
| LLM API (reasoning + builds) | $20–100 | usage-driven; EOD positional is light |
| Market data | $0–22 | Alpaca IEX data free · EODHD ~€20 for 3-market reach |
| Supabase | $0–25 | free tier early; Pro at scale |
| Netlify | $0–19 | free tier covers early deploys |
| Cloudflare / Tailscale | $0 | free tiers sufficient |
| 5G internet | existing | — |
| **Total** | **~$25–170 / mo** | starts near the low end |

**Read:** the operator costs roughly **a streaming-subscription-to-a-cheap-gym-membership per month** to run at your scale — trivial next to a $10K fund. The real budget item is your *attention* during Phases 0–1, not dollars.

---

## 8'. Updated prerequisites status
1. ✅ **Broker** — resolved: Alpaca (paper → live) and/or IBKR; both reach KSA. Sahm stays for manual.
2. ⏳ **Sharia authority** — still yours to set (AAOIFI via Musaffa/Zoya as canonical).
3. ⏳ **Legal** — book the KSA capital-markets consult before live capital.
4. ⏳ **Secrets/security owner** — implement §10 before Phase 1.
5. ⏳ **Phase exit criteria** — make §5 measurable.

---

*ADAM × StockSense v11 · Build Spec v0.2 · Educational/engineering decision support — not financial, legal, or Sharia advice. Live money stays behind a human gate until evidence says otherwise.*
