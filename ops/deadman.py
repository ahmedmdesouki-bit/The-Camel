"""
Dead-man's-switch (S6.6) — an EXTERNAL heartbeat so an outside service notices if the box dies.

The internal health monitor can only catch failures while it is itself running. A power cycle,
forced Windows Update restart, sleep, or logout kills the loop silently. This posts a ping to a
configured external endpoint (e.g. a free healthchecks.io check) that alerts the founder when an
expected ping is missed.

Network-safe by design:
  - returns a no-op 'stub' result when no URL is configured (CAMEL_DEADMAN_URL),
  - never raises if the network or endpoint fails (returns a result with the reason).
So it can run in tests and offline without touching the network.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class PingResult:
    sent: bool
    url_configured: bool
    reason: str = ""


def _deadman_url(explicit: Optional[str]) -> Optional[str]:
    return explicit or os.environ.get("CAMEL_DEADMAN_URL")


def ping(url: Optional[str] = None, timeout: float = 5.0) -> PingResult:
    """POST a heartbeat to the external dead-man's-switch.

    Stub (no network) when no URL is configured; never raises on a failed POST.
    """
    u = _deadman_url(url)
    if not u:
        return PingResult(sent=False, url_configured=False,
                          reason="no CAMEL_DEADMAN_URL configured (stub)")
    try:
        import urllib.request
        req = urllib.request.Request(u, method="POST")
        urllib.request.urlopen(req, timeout=timeout).close()
        return PingResult(sent=True, url_configured=True)
    except Exception as exc:                       # offline / bad endpoint — never fatal
        return PingResult(sent=False, url_configured=True, reason=f"ping failed: {exc}")
