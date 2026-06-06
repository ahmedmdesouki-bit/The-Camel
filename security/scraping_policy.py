"""
Scraping policy (S8) — how Camel is allowed to acquire external data.

Preference ladder (use the highest-ranked available method):
    API > vendor API > official file/bulk > RSS > static scrape > browser (QA only)

Hard rules:
  - the **browser** method is for QA/debugging only — never for decision-relevant ingestion,
  - some sources (SEC) require a descriptive User-Agent with a contact,
  - raw external text never instructs the LLM: connectors store STRUCTURED records, and any free
    text must pass the sanitiser first (data/sanitiser.py). Provenance is mandatory (data/provenance.py).
"""
from __future__ import annotations
from typing import Iterable

# lower rank = more preferred
_LADDER = {
    "api": 1,
    "vendor_api": 2,
    "official_file": 3,
    "rss": 4,
    "static_scrape": 5,
    "browser": 6,
}

# sources that must send a contactable User-Agent (fair-access policies)
_CONTACT_REQUIRED = {"sec_edgar"}


class ScrapingPolicyError(RuntimeError):
    """Raised when a disallowed acquisition method is attempted."""


def method_rank(method: str) -> int:
    if method not in _LADDER:
        raise ScrapingPolicyError(f"unknown acquisition method: {method!r}")
    return _LADDER[method]


def preferred_method(available: Iterable[str]) -> str:
    """Pick the highest-ranked (most trustworthy) method available."""
    avail = list(available)
    if not avail:
        raise ScrapingPolicyError("no acquisition method available")
    return min(avail, key=method_rank)


def is_allowed(method: str, purpose: str = "decisioning") -> bool:
    """Browser is allowed only for QA; everything else is allowed for decisioning."""
    rank = method_rank(method)        # validates the method name
    if method == "browser":
        return purpose == "qa"
    return True


def assert_allowed(method: str, purpose: str = "decisioning") -> None:
    if not is_allowed(method, purpose):
        raise ScrapingPolicyError(
            f"method '{method}' is not allowed for purpose '{purpose}' "
            f"(browser is QA-only; use an API/official source for decisioning)"
        )


def requires_contact_header(source_id: str) -> bool:
    return source_id in _CONTACT_REQUIRED
