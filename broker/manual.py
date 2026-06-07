"""
ManualBroker (S13) — the Sahm manual-entry execution path.

Sahm has a data API but NO order-placement API (verified, `CAMEL_BROKER_MATRIX.md`), so the real
Phase-1 path is: Camel **proposes** an order ticket → the founder executes it by hand in the Sahm app →
the founder **records the fill** back here, which writes it to the append-only ledger + positions under
the same Constitution + reconciliation as any other fill. No automation, full evidence discipline. The
propose step moves no money; only `record_fill` (a human-entered, real-world fill) touches the book.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Optional

from db.paths import CamelDbs
from db.sqlite import connection
from guardrail.constitution import Action
from ledger.writer import append_entry, _ensure_table as _ensure_ledger_table
from broker.positions import apply_fill
from ops.kill_switch import is_halted
from sharia.whitelist import load_whitelist


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


def _compliance_warnings(dbs: CamelDbs, symbol: str, side: str) -> list:
    """P2-G: a manual fill records money that already moved in Sahm, so we WARN (never hard-block —
    we can't un-trade it) when the kill switch is on, or the name is off-whitelist / frozen / non-compliant
    on a BUY. Sells of a held name are always allowed (de-risking)."""
    warnings: list = []
    if is_halted():
        warnings.append("kill switch is HALTED — review this manual entry")
    try:
        inst = load_whitelist(dbs.sharia).get(symbol)
        if side.lower() == "buy":
            if inst is None or not inst.on_whitelist:
                warnings.append(f"{symbol} is not on the compliant whitelist")
            elif inst.frozen or getattr(inst, "sharia_status", "compliant") != "compliant":
                warnings.append(f"{symbol} is {('frozen' if inst.frozen else inst.sharia_status)} — buy is non-compliant")
    except Exception:                              # pragma: no cover - never break a real-money record
        pass
    return warnings


_SIDE_WORDS = {"BUY": "buy", "BOUGHT": "buy", "SELL": "sell", "SOLD": "sell"}
_NOT_A_TICKER = {"BUY", "SELL", "SOLD", "BOUGHT", "SAR", "USD", "AT", "QTY", "SHARES", "SHARE", "LIMIT", "MARKET"}


def parse_fill_text(text: str) -> Optional[dict]:
    """Parse a pasted Sahm/broker confirmation into {side, symbol, qty, price}. Tolerant of formats like
    'Buy 10 SPUS @ 41.20', 'Bought 10 shares of SPUS at $41.20', 'SELL SPUS 5 48.90'. Returns None if it
    cannot confidently extract all four (the founder then enters them manually rather than risk a bad book).

    NB: image→text OCR is the founder/paid dependency (S15); this is the text→structured step."""
    if not text:
        return None
    t = str(text).strip()
    up = t.upper()
    side = next((v for k, v in _SIDE_WORDS.items() if re.search(rf"\b{k}\b", up)), None)
    if side is None:
        return None
    # ticker: first 1–5 letter uppercase token that isn't a side/currency word
    symbol = next((tok for tok in re.findall(r"\b[A-Z]{1,5}\b", up) if tok not in _NOT_A_TICKER), None)
    # price: the number after @ / at / $ (else the first decimal number)
    pm = re.search(r"(?:@|\bAT\b|\$)\s*\$?\s*([0-9]+(?:\.[0-9]+)?)", up) or re.search(r"([0-9]+\.[0-9]+)", t)
    # qty: the first standalone integer that isn't the price
    price = float(pm.group(1)) if pm else None
    qty = None
    for m in re.findall(r"\b(\d+)\b", t):
        if price is None or float(m) != price:
            qty = int(m)
            break
    if not (symbol and price and qty):
        return None
    return {"side": side, "symbol": symbol, "qty": qty, "price": price}


def record_fill_from_text(dbs: CamelDbs, text: str, *, ticket_id: str = "") -> Optional[dict]:
    """Parse a pasted confirmation and record it. Returns None (records nothing) if parsing is not confident."""
    parsed = parse_fill_text(text)
    if parsed is None:
        return None
    return record_fill(dbs, ticket_id=ticket_id, **parsed)


def record_fill(dbs: CamelDbs, *, symbol: str, side: str, qty: float, price: float,
                ticket_id: str = "") -> dict:
    """Record a founder-entered real-world fill: ledger entry + position update (reconciles to the book).
    BUY → negative cash; SELL → positive cash (matches ledger convention).

    P2-G: surfaces compliance/kill-switch **warnings** (the money already moved, so these inform — they do
    not block), tags the entry as `manual`, and writes ledger + positions **atomically** (one transaction)
    so a phantom-sell/crash can't leave the books diverged."""
    warnings = _compliance_warnings(dbs, symbol, side)
    amount = -(qty * price) if side.lower() == "buy" else (qty * price)
    _ensure_ledger_table(dbs.portfolio)
    with connection(dbs.portfolio) as conn:
        append_entry(dbs.portfolio, side.upper(), symbol, amount,
                     ref=f"manual:{ticket_id or 'na'}", conn=conn)
        pos = apply_fill(dbs.portfolio, symbol, side, qty, price, conn=conn)
    return {"symbol": symbol, "side": side, "qty": qty, "price": price,
            "cash_amount": amount, "position_qty": pos.qty, "ticket_id": ticket_id,
            "manual": True, "warnings": warnings}
