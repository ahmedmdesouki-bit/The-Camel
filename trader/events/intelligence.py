"""
Event intelligence (S9 slice 3) — synthesis over the structured `news_events` rows that the S8
connectors (GDELT/ACLED/SEC-RSS) produced.

Four deterministic, side-effect-free steps, then a writer:
  1. dedupe        — collapse the same story reported by multiple sources into one, and count the
                     reporting **quorum** (independent sources) — our "≥2 sources" discipline made visible.
  2. link_entities — a DICTIONARY matcher (tickers + company names from `assets`/whitelist) over the
                     already-SANITISED title. This is matching, not LLM inference — no raw text reasoning.
  3. score_severity / event_direction / map_theme — explicit rule tables, auditable.
  4. confidence    — data_quality_score × quorum factor (single-source events are discounted).

Nothing here trusts injection-flagged rows: `run_event_intelligence` only processes `safe=1` events,
so a redacted/hostile title is never linked, scored, or acted on. Agents may later widen the entity
dictionary / theme map (the consultant's "narrow, safe learning loop") — they never edit the Constitution.
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple

from db.paths import CamelDbs
from db.sqlite import connection

# ---- rule tables (explicit + founder-tunable; deliberately not learned at runtime) ----

# keyword -> theme (matched against the sanitised, lower-cased title + region)
_THEME_KEYWORDS = [
    (("opec", "crude", " oil", "oil ", "barrel", "refinery", "energy"), "energy"),
    (("war", "conflict", "attack", "strike", "missile", "sanction", "invasion", "coup",
      "hormuz", "red sea", "blockade"), "geopolitical_risk_off"),
    (("fed", "fomc", "interest rate", "rate hike", "rate cut", "cpi", "inflation",
      "central bank", "sama", "monetary"), "rates"),
    (("earnings", "revenue", "profit", "guidance", "dividend", "buyback"), "earnings"),
    (("chip", "semiconductor", "ai ", "data center", "datacenter", "nvidia"), "technology"),
]

# event_type -> minimum severity floor (1..5)
_TYPE_SEVERITY_FLOOR = {
    "conflict": 3, "acled": 3, "filing_8k": 3, "sanction": 4, "news_article": 1,
}

_WORD = re.compile(r"[A-Za-z0-9]+")
_TICKER = re.compile(r"\b[A-Z]{2,5}\b")          # candidate ticker tokens in the raw title


# ---------------------------------------------------------------- entity dictionary

def build_entity_dictionary(dbs: CamelDbs) -> Dict[str, List[str]]:
    """Return {'tickers': [...], 'names': [(name_lower, ticker), ...]} from assets + whitelist.

    Conservative: only tickers length ≥ 2 and names length ≥ 4 are matchable (avoids 'A'/'IT' noise)."""
    tickers: Dict[str, str] = {}
    names: List[Tuple[str, str]] = []
    with connection(dbs.fundamentals) as conn:
        for r in conn.execute("SELECT symbol, name FROM assets"):
            sym = (r["symbol"] or "").upper()
            if len(sym) >= 2:
                tickers[sym] = sym
            nm = (r["name"] or "").strip().lower()
            if len(nm) >= 4:
                names.append((nm, sym))
    with connection(dbs.sharia) as conn:
        for r in conn.execute("SELECT symbol FROM whitelist"):
            sym = (r["symbol"] or "").upper()
            if len(sym) >= 2:
                tickers.setdefault(sym, sym)
    return {"tickers": sorted(tickers), "names": names}


def link_entities(title: str, entity_dict: Dict) -> List[str]:
    """Match known tickers/company-names in a (sanitised) title. Deterministic; returns sorted tickers."""
    if not title:
        return []
    found = set()
    upper_tokens = set(_TICKER.findall(title))
    tickset = set(entity_dict.get("tickers", []))
    found |= (upper_tokens & tickset)
    low = title.lower()
    for nm, sym in entity_dict.get("names", []):
        if nm in low:
            found.add(sym)
    return sorted(found)


# ---------------------------------------------------------------- scoring

def score_severity(tone: Optional[float], event_type: str = "news_article") -> int:
    """1..5 from |tone| with an event-type floor. Deterministic."""
    mag = abs(tone) if tone is not None else 0.0
    base = 1
    for thr, lvl in ((8, 5), (6, 4), (4, 3), (2, 2)):
        if mag >= thr:
            base = lvl
            break
    floor = _TYPE_SEVERITY_FLOOR.get((event_type or "").lower(), 1)
    return max(base, floor)


def event_direction(tone: Optional[float]) -> str:
    if tone is None:
        return "neutral"
    if tone > 0.5:
        return "positive"
    if tone < -0.5:
        return "negative"
    return "neutral"


def map_theme(title: str, region: Optional[str] = None) -> str:
    hay = f"{title or ''} {region or ''}".lower()
    for keywords, theme in _THEME_KEYWORDS:
        if any(k in hay for k in keywords):
            return theme
    return "general"


def enrich_event(event: Dict, entity_dict: Dict, quorum: int = 1) -> Dict:
    """Pure: compute the synthesis fields for one event row. Does not touch the DB."""
    tone = event.get("tone")
    etype = event.get("event_type", "news_article")
    assets = link_entities(event.get("title", ""), entity_dict)
    dq = event.get("data_quality_score")
    dq = 0.85 if dq is None else float(dq)
    quorum_factor = min(1.0, max(1, quorum) / 2.0)     # 1 source → 0.5, ≥2 → 1.0
    confidence = round(dq * quorum_factor, 3)
    return {
        "affected_assets": assets,
        "severity": score_severity(tone, etype),
        "direction": event_direction(tone),
        "theme": map_theme(event.get("title", ""), event.get("region")),
        "confidence": confidence,
        "quorum": quorum,
    }


# ---------------------------------------------------------------- dedupe / quorum

def _norm_title(title: str) -> str:
    return " ".join(_WORD.findall((title or "").lower()))


def dedupe(events: List[Dict]) -> List[Tuple[Dict, int, List[str]]]:
    """Collapse the same story (same normalised title + same event_date day) reported by multiple
    sources. Returns [(canonical_event, quorum, duplicate_event_ids)]. Quorum = # distinct sources.
    The canonical row is the earliest-known one (lowest known_at)."""
    groups: Dict[Tuple[str, str], List[Dict]] = {}
    for e in events:
        key = (_norm_title(e.get("title", "")), (e.get("event_date") or "")[:10])
        groups.setdefault(key, []).append(e)
    out: List[Tuple[Dict, int, List[str]]] = []
    for _, rows in groups.items():
        rows_sorted = sorted(rows, key=lambda r: (r.get("known_at") or "", r.get("event_id") or ""))
        canonical = rows_sorted[0]
        sources = {r.get("source_id") for r in rows if r.get("source_id")}
        quorum = max(len(sources), 1)
        dup_ids = [r.get("event_id") for r in rows_sorted[1:]]
        out.append((canonical, quorum, dup_ids))
    return out


# ---------------------------------------------------------------- writer (side effect)

def run_event_intelligence(dbs: CamelDbs, limit: int = 1000) -> int:
    """Enrich `safe=1` news_events that lack synthesis: dedupe → entity-link → score → write back
    affected_assets / severity / direction / confidence. Returns the number of rows enriched.
    Injection-flagged (safe=0) rows are never touched."""
    entity_dict = build_entity_dictionary(dbs)
    with connection(dbs.news) as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM news_events WHERE safe=1 AND affected_assets IS NULL "
            "ORDER BY id LIMIT ?", (limit,)).fetchall()]
    if not rows:
        return 0

    n = 0
    with connection(dbs.news) as conn:
        for canonical, quorum, _dups in dedupe(rows):
            syn = enrich_event(canonical, entity_dict, quorum=quorum)
            conn.execute(
                "UPDATE news_events SET affected_assets=?, severity=?, direction=?, confidence=? "
                "WHERE event_id=? AND source_id=?",
                (json.dumps(syn["affected_assets"]), syn["severity"], syn["direction"],
                 syn["confidence"], canonical.get("event_id"), canonical.get("source_id")),
            )
            n += 1
    return n
