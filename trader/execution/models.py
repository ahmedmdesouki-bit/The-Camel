"""
Execution-realism models (S12) — the shared shapes for the realistic-paper engine.

Camel's `realistic_paper` is decision-validation, NOT a broker-API smoke test. It must do what broker
paper does not: model the spread you actually cross, partial fills against displayed size, fees, and —
critically — **reject stale data** rather than invent a price. There is no $1 fallback here (that lives
only in `loop_test`); a non-marketable or stale order produces an honest non-fill / rejection.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FillStatus(str, Enum):
    FILLED = "filled"
    PARTIAL = "partial"
    NO_FILL = "no_fill"        # marketable test failed (limit not crossed) — honest, not an error
    REJECTED = "rejected"      # stale data / invalid snapshot / non-limit order — refused on purpose


@dataclass
class MarketSnapshot:
    symbol: str
    bid: Optional[float]
    ask: Optional[float]
    last: Optional[float] = None
    displayed_size: Optional[float] = None   # shares available at the touch (None = assume full)
    as_of: Optional[str] = None              # ISO timestamp of the quote (for stale-data rejection)

    @property
    def mid(self) -> Optional[float]:
        if self.bid is not None and self.ask is not None and self.ask > 0:
            return (self.bid + self.ask) / 2.0
        return None

    @property
    def spread_pct(self) -> Optional[float]:
        m = self.mid
        if m and self.bid is not None and self.ask is not None:
            return (self.ask - self.bid) / m
        return None


@dataclass
class Order:
    symbol: str
    side: str                  # "buy" | "sell"
    qty: float
    limit_price: float
    order_type: str = "limit"  # limit-orders only in realistic paper (no market orders, no pre/after-hours)


@dataclass
class Fill:
    symbol: str
    side: str
    requested_qty: float
    filled_qty: float
    fill_price: float
    fees: float
    slippage_bps: float
    status: FillStatus
    reason: str = ""
