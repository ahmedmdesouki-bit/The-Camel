"""
Beginner Mode (S6.6) — a tighter limits profile for the real small account.

Loads config/beginner_mode.yaml and ASSERTS it only tightens the base limits — it can never
widen a risk rail (raise RailWidenedError otherwise). Returns a limits dict to pass to
Constitution(limits=...). This is the safe "live-fire training wheels" profile for ~$126 + $100/mo.
"""
from __future__ import annotations
import os
import yaml

from guardrail.constitution import DEFAULT_LIMITS

_ROOT = os.path.dirname(os.path.dirname(__file__))
_BASE = os.path.join(_ROOT, "config", "limits.yaml")
_BEGINNER = os.path.join(_ROOT, "config", "beginner_mode.yaml")

# keys where a SMALLER value is tighter
_TIGHTER_IF_SMALLER = ("max_position_pct", "max_sector_pct", "per_order_envelope_usd",
                       "max_orders_per_day", "max_bid_ask_spread_pct", "max_adv_participation")
# loss stops are negative; tighter = greater (closer to zero): -0.03 > -0.05
_TIGHTER_IF_GREATER = ("daily_loss_stop_pct", "weekly_drawdown_stop_pct",
                       "rolling_5d_stop_pct", "rolling_14d_stop_pct")


class RailWidenedError(RuntimeError):
    """Raised if the beginner profile would widen (loosen) a risk rail."""


def _load(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def beginner_limits(base_path: str = _BASE, beginner_path: str = _BEGINNER) -> dict:
    """Return base limits overlaid with the beginner profile, after proving it only TIGHTENS every
    risk rail. Validates against the effective base (DEFAULT_LIMITS + limits.yaml) so rails that live
    only in code (rolling stops, illiquidity caps) are still checked, plus the cash-buffer tiers."""
    base = {**DEFAULT_LIMITS, **_load(base_path)}
    beg = _load(beginner_path)

    for k in _TIGHTER_IF_SMALLER:
        if k in beg and k in base and beg[k] > base[k]:
            raise RailWidenedError(f"beginner '{k}'={beg[k]} widens base {base[k]}")
    for k in _TIGHTER_IF_GREATER:
        if k in beg and k in base and beg[k] < base[k]:
            raise RailWidenedError(f"beginner '{k}'={beg[k]} widens base {base[k]}")
    if beg.get("allow_leverage"):
        raise RailWidenedError("beginner mode cannot enable leverage")

    # cash buffer: beginner min_cash_pct must be >= base at each matching fund tier
    if "cash_tiers" in beg:
        base_tiers = {t["max_fund"]: t["min_cash_pct"] for t in base.get("cash_tiers", [])}
        for t in beg["cash_tiers"]:
            base_pct = base_tiers.get(t["max_fund"])
            if base_pct is not None and t["min_cash_pct"] < base_pct:
                raise RailWidenedError(
                    f"beginner cash buffer {t['min_cash_pct']} < base {base_pct} "
                    f"at fund tier {t['max_fund']}")

    return {**base, **beg}
