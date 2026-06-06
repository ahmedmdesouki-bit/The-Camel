"""
Founder daily brief (S6 — harvested from Alaa's parallel build).

A concise, founder-facing daily message — distinct from the ops/health daily_report. It reuses
the dashboard snapshot as the single source of truth (so the brief and the dashboard can never
disagree), formats Alaa's brief shape (value · P&L · cash drag · safety posture), always shows
the live-money safety counter, and appends the RED ALERT protocol when the day's price moves
trigger it. Delivery is channel-agnostic: pass a TelegramNotifier or a WhatsAppNotifier.
"""
from __future__ import annotations

from typing import Dict, Optional

from db.paths import CamelDbs
from dashboard.snapshot import build_snapshot
from alerts.telegram import TelegramNotifier, SendResult
from alerts.redalert import check_red_alert, red_alert_message


def build_founder_brief(dbs: CamelDbs, mode: str = "paper",
                        price_moves: Optional[Dict[str, float]] = None) -> str:
    s = build_snapshot(dbs, mode=mode)
    k, g = s["kpis"], s["governance"]
    drag = k["cash_drag_pct"]
    drag_flag = " ⚠" if isinstance(drag, (int, float)) and drag > 10 else ""

    lines = [
        "🐫 THE CAMEL — Daily Brief",
        f"Status: {s['health']['status']} · {g['phase_label']} · kill switch {g['kill_switch']}",
        "",
        f"Total value: ${k['total_value']:,.2f}  ({k['open_positions']} positions)",
        f"Unrealised P&L: {_signed(k['unrealized_pnl'])} · Realised: {_signed(k['realized_pnl'])}",
        f"Cash: ${k['cash']:,.2f} · Cash drag: {drag}%{drag_flag}",
        "",
        f"Live-money gate: {g['gate_passed']}/{g['gate_total']} clear · Live capital at risk: ${g['live_at_risk']:,.0f}",
    ]

    alert = check_red_alert(price_moves or {})
    if alert.triggered:
        lines += ["", red_alert_message(alert)]

    lines += ["", "Patient capital. Governed by evidence. Not financial/Sharia advice."]
    return "\n".join(lines)


def send_founder_brief(dbs: CamelDbs, mode: str = "paper", notifier=None,
                       price_moves: Optional[Dict[str, float]] = None) -> SendResult:
    text = build_founder_brief(dbs, mode=mode, price_moves=price_moves)
    notifier = notifier or TelegramNotifier()
    return notifier.send(text)


def _signed(v) -> str:
    try:
        f = float(v)
        return f"{'+' if f >= 0 else '-'}${abs(f):,.2f}"
    except (TypeError, ValueError):
        return "—"
