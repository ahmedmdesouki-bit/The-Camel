# CAMEL BROKER MATRIX — capability comparison & resolved direction (S6.6)

> **Canonical home for the broker decision.** Resolves the live-broker open question. The Phase-1
> go-live mechanics live in `CAMEL_LIVE_READINESS.md`; this doc is the *comparison* and the *why*.

## Resolved direction

- **Alpaca** — the **autonomous US paper→micro-live path**. API-first; key is **trade-only with
  withdrawals disabled**; limit orders only; no pre-/after-hours. This is the broker the operator
  actually drives.
- **Sahm** — the founder's **real Saudi/US-ETF account**, assumed **no automation API**. ⚠️ *Lead to verify
  (data research, 2026-06-06): `sahmk.sa/en/developers` suggests Sahm may expose a developer/API surface — if
  confirmed, the manual-entry assumption below may be revised to a real API integration. Verify before S13.*
  Until then, handled by
  a **`ManualBroker` (manual-entry) mode**: Camel proposes → founder executes in the Sahm app →
  logs the fill (price/shares/timestamp) back to the append-only ledger under the **same Constitution
  + reconciliation**. No automation, but full evidence + guardrail discipline.
- **IBKR** — **deferred to Phase 2**, only if position sizing grows or multi-market automation is
  needed.
- **EGX brokers (Thndr/Telda)** — **later** (markets order is US → Saudi → EGX). No retail API; would
  also be manual-entry. Not in scope until the US/Saudi core is solid.

## Comparison

| Broker | Markets | API | Sharia screening | Fractional | Min capital | PDT rule | Automation | Notes |
|---|---|---|---|---|---|---|---|---|
| **Alpaca** | US | ✅ REST | ❌ (Camel screens) | ✅ | $0 (paper); cash acct live | N/A for us* | ✅ full | Paper IEX free; trade-only key; withdrawals disabled |
| **Sahm** | US ETFs + Saudi | ❌ none | ❌ (Camel screens) | ❌ whole-shares | ~$0 | n/a | ✋ manual-entry | The founder's **real** account today (~$126 + $100/mo) |
| **IBKR** | Global | ✅ (complex) | ❌ | ✅ | higher | applies on margin | ✅ | Phase 2 candidate; not Sharia-screened |
| **Thndr / Telda (EGX)** | Egypt | ❌ retail | partial (Thndr badge) | varies | low | n/a | ✋ manual-entry | Later market only |

\* **PDT note:** Alpaca live's $25K Pattern-Day-Trader minimum applies to 4+ **day-trades** in 5 days on
a **margin** account. The Camel is **cash-account, long-only, positional** (not day-trading) — so PDT is
largely **N/A**. Documented here so it isn't mistaken for a blocker.

## Selection rules (carried by the Constitution / live-readiness gate)

- Live key must be **trade-only, withdrawals disabled, margin + options disabled**, scoped to minimum
  permissions; verified at startup.
- **Limit orders only**; no pre-/after-hours.
- Whole-share constraint honored for Sahm (no fractional).
- Every fill — automated (Alpaca) or manual (Sahm) — writes to the **append-only hash-chain ledger** and
  must **reconcile**; positions update on every fill (S6.6 position accounting).
