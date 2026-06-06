"""
Business-model Sharia classifier for Entrepreneur Camel.

Returns categorised flags with reasons — richer than the substring check in
constitution.py. The Constitution's _has_haram is the hard gate; this module
gives the BOARDROOM the detail it needs to explain a rejection.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

HARAM_CATEGORIES: Dict[str, List[str]] = {
    "conventional_finance": [
        "bank", "conventional finance", "interest", "lending", "loan",
        "mortgage", "payday", "credit card", "savings account", "bond",
        "fixed income", "riba",
    ],
    "alcohol": [
        "alcohol", "beer", "wine", "liquor", "brewery", "spirits", "distill",
        "winery", "pub", "bar ",
    ],
    "tobacco": [
        "tobacco", "cigarette", "vape", "nicotine", "e-cigarette", "hookah",
    ],
    "gambling": [
        "gambling", "casino", "betting", "lottery", "poker", "slot",
        "sportsbook", "wager",
    ],
    "pork": [
        "pork", "swine", "pig", "bacon", "ham", "lard",
    ],
    "adult": [
        "adult", "porn", "pornography", "escort", "onlyfans", "explicit",
        "erotic",
    ],
    "weapons": [
        "weapon", "defense", "defence", "firearm", "ammunition", "military",
        "explosive", "grenade", "missile", "arms dealer", "gun ",
    ],
}


@dataclass
class ClassifierResult:
    approved: bool
    flags: List[str] = field(default_factory=list)         # haram category names
    matched_terms: List[str] = field(default_factory=list) # exact strings that matched
    details: List[str] = field(default_factory=list)       # human-readable per-category


def classify_business_model(description: str) -> ClassifierResult:
    """
    Screen a business-model description for haram activity.
    approved=True only when no haram categories are found.
    """
    text = (description or "").lower()
    flags: List[str] = []
    matched_terms: List[str] = []
    details: List[str] = []

    for category, terms in HARAM_CATEGORIES.items():
        hits = [t for t in terms if t in text]
        if hits:
            flags.append(category)
            matched_terms.extend(hits)
            details.append(f"{category}: matched {hits}")

    return ClassifierResult(
        approved=len(flags) == 0,
        flags=flags,
        matched_terms=matched_terms,
        details=details,
    )
