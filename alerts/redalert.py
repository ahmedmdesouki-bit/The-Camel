"""
RED ALERT — founder-panic protocol (S6 — harvested from Alaa's parallel build).

The Camel's hard guardrails protect against the *machine* misbehaving. This protects against
the *human operator's* emotions — a real risk vector in a manual-execution (Sahm) loop where
the founder can panic-sell on a red day. It is informational only: it never places, blocks, or
proposes a trade. It de-escalates and points back at the data.

Pure functions, no I/O. The daily brief calls `check_red_alert` on the day's price moves and,
if triggered, appends `red_alert_message`. The 3-step shape mirrors the SKILL.md protocol:
breathe → assess → act-or-hold.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

DEFAULT_DROP_THRESHOLD_PCT = -3.0      # a single-day drop at/below this fires the protocol


@dataclass
class RedAlert:
    triggered: bool
    threshold_pct: float
    breaches: List[Dict] = field(default_factory=list)   # [{symbol, pct}]


def check_red_alert(price_moves: Dict[str, float],
                    threshold_pct: float = DEFAULT_DROP_THRESHOLD_PCT) -> RedAlert:
    """`price_moves` is {symbol: daily_pct_change}. Fires if any holding fell at/below threshold."""
    breaches = sorted(
        ({"symbol": s, "pct": round(float(p), 2)} for s, p in (price_moves or {}).items()
         if p is not None and float(p) <= threshold_pct),
        key=lambda b: b["pct"],
    )
    return RedAlert(triggered=bool(breaches), threshold_pct=threshold_pct, breaches=breaches)


def red_alert_message(alert: RedAlert) -> str:
    """The breathe → assess → act protocol. Never recommends a panic sell."""
    if not alert.triggered:
        return ""
    worst = ", ".join(f"{b['symbol']} {b['pct']:+.1f}%" for b in alert.breaches)
    return (
        "🚨 RED ALERT\n"
        f"Daily drop ≥ {abs(alert.threshold_pct):.0f}% detected: {worst}\n"
        "1) Breathe — this is noise, not news. DCA is *designed* to buy through volatility.\n"
        "2) Assess — has the thesis actually changed, or only the price? Check the Constitution: "
        "no panic sells, no leverage, no thesis change on a red candle.\n"
        "3) Act or hold — default is HOLD. A lower price is a future buy signal, not a sell signal. "
        "Do not place any order today out of fear."
    )
