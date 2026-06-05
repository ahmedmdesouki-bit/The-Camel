"""
Source allowlist + quorum (S4) — only approved sources may drive critical decisions,
and important signals need independent confirmation.

`is_allowed` checks a URL's host against the allowlist. `has_quorum` enforces a minimum
number of independent sources. `retrieved_record` builds an audit entry (caller persists)
so every external fetch is logged.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List
from urllib.parse import urlparse

DEFAULT_ALLOWLIST = {
    "alpaca.markets", "data.alpaca.markets",
    "capitaltrades.com",
    "sec.gov", "www.sec.gov",
    "finance.yahoo.com",
}

QUORUM_MIN = 2


def _host(url: str) -> str:
    netloc = urlparse(url if "://" in url else "https://" + url).netloc.lower()
    return netloc.split(":")[0]  # strip port


def is_allowed(url: str, allowlist: Iterable[str] = None) -> bool:
    """True if the URL's host is on the allowlist (exact host or registrable suffix)."""
    allow = set(allowlist) if allowlist is not None else DEFAULT_ALLOWLIST
    host = _host(url)
    if host in allow:
        return True
    # allow subdomains of allowlisted registrable domains
    return any(host == a or host.endswith("." + a) for a in allow)


def has_quorum(sources: List[str], minimum: int = QUORUM_MIN) -> bool:
    """True if there are at least `minimum` DISTINCT allowed sources."""
    distinct = {_host(s) for s in sources if is_allowed(s)}
    return len(distinct) >= minimum


def retrieved_record(url: str, content_hash: str) -> dict:
    """Audit record for an external fetch (caller persists to the log)."""
    return {
        "url": url,
        "host": _host(url),
        "content_hash": content_hash,
        "allowed": is_allowed(url),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }
