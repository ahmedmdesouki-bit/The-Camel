"""
ManualBroker (S13) — the Sahm manual-entry execution path.

Sahm has a data API but NO order-placement API (verified, `CAMEL_BROKER_MATRIX.md`), so the real
Phase-1 path is: Camel **proposes** an order ticket → the founder executes it by hand in the Sahm app →
the founder **records the fill** back here, which writes it to the append-only ledger + positions under
the same Constitution + reconciliation as any other fill. No automation, full evidence discipline. The
propose step moves no money; only `record_fill` (a human-entered, real-world fill) touches the book.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from db.paths import CamelDbs
from guardrail.constitution import Action
from ledger.writer import append_entry
from broker.positions import apply_fill


@dataclass
class OrderTicket:
    ticket_id: str
    symbol: str
    side: str
    qty: float
    limit_price: float
    instructions: str          # what the founder should do in the Sahm app


def propose(action: Action, limit_price: float, qty: float) -> OrderTicket:
    """Produce a manual order ticket for the founder. Moves no money."""
    tid = uuid.uuid4().hex[:12]
    return OrderTicket(
        ticket_id=tid, symbol=action.symbol, side=action.side, qty=qty, limit_price=limit_price,
        instructions=(f"In Sahm: place a LIMIT {action.side.upper()} of {int(qty)} {action.symbol} "
                      f"@ ${limit_price:.2f} (whole shares). Then record the fill with ticket {tid}."))


def record_fill(dbs: CamelDbs, *, symbol: str, side: str, qty: float, price: float,
                ticket_id: str = "") -> dict:
    """Record a founder-entered real-world fill: ledger entry + position update (reconciles to the book).
    BUY → negative cash; SELL → positive cash (matches ledger convention)."""
    amount = -(qty * price) if side.lower() == "buy" else (qty * price)
    append_entry(dbs.portfolio, side.upper(), symbol, amount, ref=f"manual:{ticket_id or 'na'}")
    pos = apply_fill(dbs.portfolio, symbol, side, qty, price)
    return {"symbol": symbol, "side": side, "qty": qty, "price": price,
            "cash_amount": amount, "position_qty": pos.qty, "ticket_id": ticket_id}
