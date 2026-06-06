# CAMEL CONSTITUTION — the non-negotiable rules

> **Canonical home for Camel's rules in prose.**
> The authoritative *implementation* is `guardrail/constitution.py` + `config/limits.yaml`.
> This document explains the rules; the code enforces them. If they ever disagree, the code
> is right and this doc is a bug.

---

## The nine non-negotiable rules

1. **Sharia gate is a hard wall.** Only whitelisted, compliant, non-frozen instruments are
   tradeable. Business models are screened for haram activity. No leverage, derivatives,
   shorting, margin, or crypto-derivatives — ever.
2. **No position without a written invalidation point** (invalidation + profit-take + time-stop).
3. **Withdrawals are forbidden.** The broker API key must be trade-only, withdrawals disabled.
4. **Live money needs a human approval gate** until Phase 2, then only inside the per-order
   envelope. Phase 0 is paper only.
5. **Everything is logged** — append-only ledger with SHA-256 hash chain; limits are
   founder-owned config the agent process cannot write.
6. **Limits live in `config/limits.yaml`.** Do not hardcode limits elsewhere.
7. **Camel cannot change its own rules.** No agent-callable override path exists.
   *(Proven by the config-immutability test in S4 — not merely asserted.)*
8. **Camel cannot act on stale or single-source data.** (S4 enforcement)
9. **Camel cannot act unless broker/account state reconciles.** (S4 enforcement)

---

## Risk limits (founder-owned, in `config/limits.yaml`)

| Guardrail | Limit | Why |
|---|---|---|
| Max single position | 20% of fund | No single-name blow-up |
| Max sector concentration | 40% | Diversification |
| Min cash buffer | tiered by fund size | Liquidity discipline |
| Max single auto-trade | $0 live until Phase 2, then ≤ $50/order | Caps any single mistake |
| Daily loss stop | −5% → halt + notify | Circuit breaker |
| Weekly drawdown stop | −10% → freeze + founder review | Kill switch |
| Rolling velocity stop (S4) | 5-day ≤ −8% → 48h freeze; 14-day ≤ −12% → halt | Anti-bleeding |
| Leverage | 0 (hard) | Sharia + risk |
| Invalidation point | required before any position | Discipline |

---

## Sharia screening (AAOIFI thresholds)

A name is non-compliant (→ frozen + alert) if any breach:
- Debt / market cap ≥ 33%
- (Cash + interest-bearing securities) / market cap ≥ 33%
- Non-compliant income ≥ 5%

Business-model screen (Entrepreneur arm) rejects: conventional finance, alcohol, tobacco,
gambling, pork, adult, weapons/defense.

Quarterly re-screen freezes any drifted name. `manual_override_allowed: false`.

---

## Phase gates — autonomy is earned, not granted

| Phase | Capital | Autonomy | Exit criteria |
|---|---|---|---|
| **0 Paper** | $0 | Full loop, simulated orders | ≥28 days · 0 breaches · ledger reconciles · ≥1 product deployed |
| **1 Micro-live** | $100–500 | Human approves every trade | ≥28 days · 0 unapproved executions · approval < 5 min |
| **2 Guardrailed auto** | scale to fund | Auto ≤ per-order envelope on whitelist | ≥60 days · 0 limit breaches · loss-stop fired in test |
| **3 Scale** | full $10K | Wider envelope | track record justifies each increase |

We are in **Phase 0**.

---

## Capital buckets (S4 Budget Kernel — Camel never controls 100% freely)

```
Core reserve:            50%
Trader paper/micro-live: 10–20%
Entrepreneur experiments: 20–30%
System / tooling:        5–10%
Emergency / manual:      10–20%
```
*(Exact percentages are a pending founder decision — see CAMEL_ROADMAP.md open decisions.)*

---

## Permanently excluded — do not revisit

**Options, the Wheel Strategy, and all derivatives.** Cash-secured puts and covered calls
are options; options are derivatives; derivatives are haram and blocked by rule #1. This
appeared in two source videos and was rejected both times. It is closed.

---

## The full "DO NOT" list

See `../CLAUDE.md` § DO NOT for the operational hard-rails (no live trading without a
phase flag, no credentials in the repo, no Playwright for broker actions, no blind
averaging down, no unvalidated web text into prompts, etc.).
