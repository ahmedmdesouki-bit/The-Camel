# CAMEL LIVE READINESS — Phase 1 go-live checklist

> **Canonical home for the pre-live gate.** This is the operational checklist you tick
> before any real money moves. The sprint that builds it is S11 (see `CAMEL_ROADMAP.md`);
> the rules behind it are in `CAMEL_CONSTITUTION.md`. Nothing here is automatic — going
> live is a deliberate founder act.

---

## Phase 0 → Phase 1 prerequisites (ALL must pass)

- [ ] ≥ 28 days continuous paper operation
- [ ] 0 guardrail breaches over the run
- [ ] Ledger reconciles with the broker paper statement
- [ ] Every position had a thesis + invalidation point
- [ ] Kill switch tested and confirmed working (over Tailscale)
- [ ] Broker API key scoped trade-only, withdrawals disabled
- [ ] Margin disabled · options disabled · key scoped to minimum permissions
- [ ] Edge Proof Engine has approved at least one signal
- [ ] Approval flow tested end-to-end
- [ ] Manual dry-run completed
- [ ] One **rejected** trade test completed in the live environment (no order placed)
- [ ] One **approved** micro trade completed manually before any automation
- [ ] Emergency broker login tested

---

## Definition of Done (v1) — unlocks Phase 1

- [ ] All tests green (target ≥ 200 by S8)
- [ ] Agent cannot modify its own constitution/config — **proven by config-immutability test**
- [ ] Tool permissions enforced before every tool action
- [ ] Budget limits enforced before every money/spend action
- [ ] Data freshness checked before every trade decision; stale/single-source = decision-ineligible
- [ ] Point-in-time timestamps present on all decision-relevant tables (no look-ahead bias)
- [ ] Broker/account reconciliation clean
- [ ] Kill switch checked inside `Constitution.evaluate()` — gates every consequential action
- [ ] State machine prevents skipped steps
- [ ] ThesisCard required before any paper trade, including opportunity-cost justification
- [ ] Invalidation required before any paper trade (fixed or trailing floor)
- [ ] Every action logged
- [ ] **No trade proceeds without an EdgeReport** (v0 from S4.5; full engine from S7)
- [ ] Edge Proof Engine approved at least one signal
- [ ] Adversarial test suite green (all 15 cases — see CAMEL_TESTING.md)
- [ ] Strategy Registry has ≥ 3 active strategies with live base-rates
- [ ] Learning Engine updating base-rates autonomously
- [ ] Improvement proposals landing in Learning Ledger (Level 3 — not auto-applied)
- [ ] Daily health report working
- [ ] Kill switch working over Tailscale
- [ ] No live trading possible unless explicitly enabled by founder-owned config
- [ ] 28 days clean paper operation meeting Phase 0 exit criteria

---

## Phase 1 operating rules (once live)

```
Human approval required for every live trade.
No autonomous live execution.
Limit orders only.
No pre-market / after-hours.
Max total live capital: $100–500.
Max single order: lower of $50 or founder-defined limit.
Whitelist only.
Edge Proof required.
Budget Kernel required.
Broker reconciliation required before every order.
```

---

## Status classifier (from S5.5 — drives the daily report)

```
GREEN  = safe to run paper loop
YELLOW = run research only (a safety/data gap is open)
RED    = halt all consequential actions (loss-stop, reconciliation diff, stale data)
BLACK  = kill switch / manual founder intervention required
```

Going live requires a sustained GREEN run meeting every box above.
