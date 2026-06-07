"""Realistic-paper execution engine (S12) — fills, slippage, fees, stale-rejection, corporate actions."""
from execution.models import Order, MarketSnapshot, Fill, FillStatus
from execution.fill import simulate_fill, slippage_bps, DEFAULT_FEE_BPS, DEFAULT_MAX_AGE_S
from execution.realistic_paper import RealisticPaperExecutor
from execution.corporate_actions import (
    announce, entitled_qty, settle, attribute, replay_split,
    DividendAnnouncement, DividendSettlement,
)

__all__ = [
    "Order", "MarketSnapshot", "Fill", "FillStatus",
    "simulate_fill", "slippage_bps", "DEFAULT_FEE_BPS", "DEFAULT_MAX_AGE_S",
    "RealisticPaperExecutor",
    "announce", "entitled_qty", "settle", "attribute", "replay_split",
    "DividendAnnouncement", "DividendSettlement",
]
