# ADAM × StockSense v11 — Sprint 1: the safety core

This is the **Guardrail Constitution** + schema. Nothing here trades. Its job is to
prove that prohibited actions are *impossible* before any later sprint can move money.

## Run the tests (Sprint 1 gate)
```bash
cd adam
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q            # the rogue-action suite must be 100% green
```

## What's here
- `guardrail/constitution.py` — `Constitution.evaluate(action, state) -> Decision`. Every
  trade/spend/deploy/withdraw routes through this. No agent-callable override.
- `config/limits.yaml` — **founder-owned** limits. Changing autonomy = editing these on purpose.
- `db/schema.sql` — Supabase tables; ledger append-only, config read-only to the agent role (RLS).
- `ops/kill_switch.py` — `python ops/kill_switch.py halt|resume`.

## The rule that keeps you safe
- Withdrawals: always rejected.
- Live orders: rejected without founder approval until Phase 2, then only inside the per-order envelope.
- Off-whitelist / non-compliant / frozen names: rejected.
- No position without an invalidation point. No leverage, derivatives, or shorting.
- Set your Alpaca key **trade-only, withdrawals disabled** (see `.env.example`).

## Next (Sprint 2)
Whitelist + quarterly Sharia re-screen, business-model classifier, Alpaca paper data ingestion.
