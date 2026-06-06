"""
WhatsApp notifier via CallMeBot (S6 — harvested from Alaa's parallel build).

A zero-cost second alert channel alongside Telegram. Same credential-safe contract as
`TelegramNotifier`: with no phone/api-key it operates in STUB mode (formats and returns the
message, no network call), and a real send is only attempted when both creds are present AND
`requests` is installed — so the test suite never hits the network and the loop never crashes
on a delivery failure.

CallMeBot is a one-way relay (you message their number once to get a key); it is NOT an
approval channel. Interactive approve/veto stays on Telegram (S11).
"""
from __future__ import annotations

import os
import urllib.parse
from typing import Optional

from alerts.telegram import SendResult

API = "https://api.callmebot.com/whatsapp.php"


class WhatsAppNotifier:
    def __init__(self, phone: Optional[str] = None, api_key: Optional[str] = None):
        self.phone = phone or os.environ.get("WHATSAPP_PHONE")
        self.api_key = api_key or os.environ.get("CALLMEBOT_API_KEY")

    @property
    def configured(self) -> bool:
        return bool(self.phone and self.api_key)

    def send(self, text: str) -> SendResult:
        if not self.configured:
            # STUB: no creds → never touch the network; surface the message for logs/tests.
            return SendResult(sent=False, preview=text, reason="no whatsapp credentials (stub)")
        try:
            import requests  # optional dependency
        except ImportError:
            return SendResult(sent=False, preview=text, reason="requests not installed")
        try:
            params = {"phone": self.phone, "text": text, "apikey": self.api_key}
            resp = requests.get(f"{API}?{urllib.parse.urlencode(params)}", timeout=15)
            ok = resp.status_code == 200
            return SendResult(sent=ok, preview=text,
                              reason="" if ok else f"HTTP {resp.status_code}")
        except Exception as exc:                      # network/other failure must not crash the loop
            return SendResult(sent=False, preview=text, reason=f"send error: {exc}")
