"""
Corporate-action + dividend replay (S12) — the part broker paper does NOT simulate.

Implements the consultant-adopted **4-stage dividend pipeline** + split replay, on the **NRA-withholding**
tax frame (founder is KSA-resident):

  1. announcement — record dates/amount; NO cash or P&L change.
  2. entitlement  — freeze the entitled quantity at the ex/record rule (incl. the 25%+ special-dividend
                    deferral: ex-date = one business day AFTER payment; and due-bills on stock dividends).
  3. settlement   — post gross + withholding + net as SEPARATE ledger amounts (settle-date accounting).
  4. attribution  — split the event into income · tax · price effects (so a sleeve that looks strong on
                    cash-received isn't actually losing after the ex-date gap + withholding).

Pure helpers; the realistic-paper engine / sandbox call these to replay events through the book.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from strategies.dividends import net_dividend, purification_amount, DEFAULT_NRA_WITHHOLDING


# ---- stage 1: announcement ----
@dataclass
class DividendAnnouncement:
    symbol: str
    gross_per_share: float
    ex_date: str
    record_date: str = ""
    pay_date: str = ""
    is_special: bool = False        # ≥25% of price → special handling
    cash_change: float = 0.0        # always 0 at announcement


def announce(symbol: str, gross_per_share: float, ex_date: str, *, record_date: str = "",
             pay_date: str = "", price: Optional[float] = None) -> DividendAnnouncement:
    """Stage 1. A dividend ≥ 25% of the share price is flagged special (ex-date deferral applies)."""
    is_special = bool(price and price > 0 and gross_per_share / price >= 0.25)
    return DividendAnnouncement(symbol, gross_per_share, ex_date, record_date, pay_date, is_special)


# ---- stage 2: entitlement ----
def entitled_qty(held_qty: float, buy_date: str, ann: DividendAnnouncement) -> float:
    """Stage 2. You are entitled only if you held BEFORE the ex-date. Buy on/after the ex-date → 0.
    For a special dividend the effective ex-date is deferred to one business day after payment, so a
    holder through the pay date stays entitled (modelled by comparing against pay_date when special)."""
    cutoff = ann.pay_date if (ann.is_special and ann.pay_date) else ann.ex_date
    if not cutoff:
        return held_qty
    return held_qty if (buy_date or "") < cutoff else 0.0


# ---- stage 3: settlement ----
@dataclass
class DividendSettlement:
    symbol: str
    entitled_qty: float
    gross: float
    withheld: float
    net: float
    purification: float
    withholding_rate: float


def settle(ann: DividendAnnouncement, entitled: float, *,
           withholding_rate: float = DEFAULT_NRA_WITHHOLDING, impure_fraction: float = 0.0) -> DividendSettlement:
    """Stage 3. Gross → withholding (NRA) → net, as three separate amounts; plus the purification owed."""
    gross_cash = ann.gross_per_share * max(0.0, entitled)
    cash = net_dividend(gross_cash, withholding_rate)
    return DividendSettlement(ann.symbol, entitled, cash.gross, cash.withheld, cash.net,
                              purification_amount(cash.net, impure_fraction), cash.withholding_rate)


# ---- stage 4: attribution ----
def attribute(settlement: DividendSettlement, ex_date_price_drop: float, position_qty: float) -> Dict[str, float]:
    """Stage 4. Decompose the event: income (net cash) · tax (withheld) · price (the ex-date drop)."""
    price_effect = round(-abs(ex_date_price_drop) * max(0.0, position_qty), 6)
    return {
        "income_effect": settlement.net,
        "tax_effect": -settlement.withheld,
        "price_effect": price_effect,
        "net_total": round(settlement.net - settlement.withheld * 0 + price_effect, 6),  # withheld already out of net
        "purification_owed": settlement.purification,
    }


# ---- splits ----
def replay_split(qty: float, avg_cost: float, ratio: float) -> Dict[str, float]:
    """A `ratio`-for-1 split: qty × ratio, avg cost ÷ ratio (market value and basis unchanged)."""
    if ratio <= 0:
        return {"qty": qty, "avg_cost": avg_cost}
    return {"qty": round(qty * ratio, 6), "avg_cost": round(avg_cost / ratio, 6)}
