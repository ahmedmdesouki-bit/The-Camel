"""
Prompt-injection sanitiser (S4).

Raw external text (news, filings, scraped pages) is HOSTILE by default. It is never passed
to the reasoning engine directly. `sanitise()` strips markdown/UI noise, scans for injection
patterns, and returns a flat structured record. Content extraction is separated from
instruction execution — flagged content is surfaced, never obeyed.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List

INJECTION_PATTERNS = (
    "ignore previous", "ignore all previous", "disregard previous",
    "system prompt", "developer message", "tool call", "function call",
    "api key", "secret key", "download this", "execute this", "run this",
    "change your rules", "override guardrail", "override the guardrail",
    "bypass", "you are now", "new instructions",
)

# crude markdown / UI strippers
_MD = re.compile(r"[*_`#>\[\]]|!\[|\]\(")
_WS = re.compile(r"\s+")


@dataclass
class Sanitised:
    clean_text: str
    injection_flags: List[str] = field(default_factory=list)
    safe: bool = True


def sanitise(raw_text: str) -> Sanitised:
    """
    Strip markdown/UI characters, collapse whitespace, and flag injection patterns.
    `safe` is False if any injection pattern is present.
    """
    text = raw_text or ""
    # match against a whitespace- and markdown-collapsed lowercase string so spacing tricks
    # ("ignore   previous", line breaks, markdown noise) can't slip an injection pattern past us
    match_str = _WS.sub(" ", _MD.sub(" ", text.lower())).strip()
    flags = [p for p in INJECTION_PATTERNS if p in match_str]

    clean = _MD.sub(" ", text)
    clean = _WS.sub(" ", clean).strip()

    return Sanitised(clean_text=clean, injection_flags=flags, safe=len(flags) == 0)
