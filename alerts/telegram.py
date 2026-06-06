"""
Telegram notifier (S6) — one-way alerts + (S11) one-tap approve/veto later.

Credential-safe by design: with no bot token/chat_id it operates in STUB mode — it formats
and returns the message but does NOT attempt any network call. Real sending is only attempted
when both creds are present AND `requests` is installed, so the test suite never hits the
network. The Approval Channel (interactive approve/veto) is wired in S11.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional

API = "https://api.telegram.org/bot{token}/sendMessage"


@dataclass
class SendResult:
    sent: bool
    preview: str
    reason: str = ""


class TelegramNotifier:
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    @property
    def configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, text: str) -> SendResult:
        if not self.configured:
            # STUB: no creds → never touch the network; surface the message for logs/tests.
            return SendResult(sent=False, preview=text, reason="no telegram credentials (stub)")
        try:
            import requests  # optional dependency
        except ImportError:
            return SendResult(sent=False, preview=text, reason="requests not installed")
        try:
            resp = requests.post(
                API.format(token=self.token),
                json={"chat_id": self.chat_id, "text": text},
                timeout=10,
            )
            ok = resp.status_code == 200
            return SendResult(sent=ok, preview=text,
                              reason="" if ok else f"HTTP {resp.status_code}")
        except Exception as exc:                      # network/other failure must not crash the loop
            return SendResult(sent=False, preview=text, reason=f"send error: {exc}")
