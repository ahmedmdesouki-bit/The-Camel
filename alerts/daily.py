"""
Daily report delivery (S6) — build the S5.5 daily report and push it to Telegram.

Credential-safe: with no Telegram creds it returns a stub SendResult carrying the report
text (so the loop/scheduler can still log it). The report content itself is built by
ops.daily_report (S5.5).
"""
from __future__ import annotations
from typing import Optional

from db.paths import CamelDbs
from ops.daily_report import build_daily_report
from alerts.telegram import TelegramNotifier, SendResult


def send_daily_report(dbs: CamelDbs, mode: str = "paper",
                      notifier: Optional[TelegramNotifier] = None,
                      open_cards: int = 0) -> SendResult:
    text = build_daily_report(dbs, mode=mode, open_cards=open_cards)
    notifier = notifier or TelegramNotifier()
    return notifier.send(text)
