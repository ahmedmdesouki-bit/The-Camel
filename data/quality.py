"""
Data quality scoring (S4 v1; refined in S7).

Combines source count, freshness, cross-source agreement, and source reputation into a
single `quality_score` and a hard `decision_eligible` flag. Data that is stale, single-source
when a quorum is required, or from an unapproved source is NOT eligible to drive a decision.
"""
from __future__ import annotations
from dataclasses import dataclass

MIN_AGREEMENT = 0.99       # multi-source close prices must agree within 1%
QUORUM_SOURCES = 2         # important signals want >= 2 sources


@dataclass
class QualityScore:
    quality_score: float
    decision_eligible: bool
    reason: str


def score(
    source_count: int,
    freshness_hours: float,
    source_agreement: float,
    source_reputation: str,
    max_age_hours: float = 24.0,
    require_quorum: bool = False,
) -> QualityScore:
    """
    source_agreement: 1.0 = identical across sources (use 1.0 for a single source).
    source_reputation: 'approved' | 'unknown' | 'rejected'.
    """
    reasons = []
    eligible = True

    if source_count < 1:
        return QualityScore(0.0, False, "no sources")
    if source_reputation == "rejected":
        return QualityScore(0.0, False, "source reputation rejected")
    if freshness_hours > max_age_hours:
        eligible = False
        reasons.append(f"stale ({freshness_hours:.1f}h)")
    if require_quorum and source_count < QUORUM_SOURCES:
        eligible = False
        reasons.append("below source quorum")
    if source_count >= 2 and source_agreement < MIN_AGREEMENT:
        eligible = False
        reasons.append(f"sources disagree ({source_agreement:.3f})")
    if source_reputation != "approved":
        reasons.append("source not on approved allowlist")

    # Simple 0..1 score: penalise staleness, disagreement, thin sourcing, low reputation.
    freshness_factor = max(0.0, 1.0 - freshness_hours / max_age_hours) if max_age_hours else 0.0
    source_factor = min(1.0, source_count / QUORUM_SOURCES)
    rep_factor = {"approved": 1.0, "unknown": 0.6, "rejected": 0.0}.get(source_reputation, 0.5)
    agree_factor = source_agreement if source_count >= 2 else 1.0
    quality = round(0.30 * freshness_factor + 0.25 * source_factor
                    + 0.20 * rep_factor + 0.25 * agree_factor, 3)

    return QualityScore(quality, eligible, "; ".join(reasons) or "ok")


# ---- wiring (P2-C): turn the previously-dead `decision_eligible` flag into a LIVE rule-#8 gate ----

# Price-feed source NAMES trusted to drive a decision (the `source` column in `prices`). The name-level
# companion to security/source_allowlist.py (which works on URLs/hosts). A source proven unreliable is moved
# to REJECTED and hard-blocked. An UNKNOWN source is NOT blocked (fail-open) — a missing label is neither
# "stale" nor "single-source"; freshness + Edge-Proof sample-size stay the dominant gates.
APPROVED_PRICE_SOURCES = {"alpaca", "stooq", "sec_edgar", "fred", "treasury", "world_bank", "bls", "bea", "eia"}
REJECTED_PRICE_SOURCES: set = set()


def data_eligible(dbs, symbol: str, *, now: str = None, max_age_hours: float = 24.0,
                  require_quorum: bool = False) -> QualityScore:
    """Constitution rule #8 at decision time: is `symbol`'s price data fit to drive a BUY?

    Wires the previously-dead `QualityScore.decision_eligible` into the live path. A name is INELIGIBLE
    (dropped from the buy set, logged) when its latest price is STALE or from a REJECTED source.
    `require_quorum` stays False by default: a single APPROVED end-of-day source is acceptable for the
    whitelisted ETF core — multi-source quorum is enforced only once more than one price feed exists.
    Fail-safe: no price data at all -> ineligible. (Freshness is a LIVE concept — callers in a point-in-time
    backtest skip this gate, where the `known_at` discipline governs instead.)
    """
    from datetime import datetime, timezone
    from db.sqlite import connection
    from data.freshness import check_symbol_freshness
    now = now or datetime.now(timezone.utc).isoformat()
    fr = check_symbol_freshness(dbs.market, symbol, now, max_age_hours)
    if not fr.fresh:
        return QualityScore(0.0, False, fr.reason)
    with connection(dbs.market) as conn:
        latest = conn.execute("SELECT MAX(date) FROM prices WHERE symbol=?", (symbol,)).fetchone()[0]
        srcs = [r[0] for r in conn.execute(
            "SELECT DISTINCT source FROM prices WHERE symbol=? AND date=?", (symbol, latest)).fetchall() if r[0]]
    low = {(s or "").lower() for s in srcs}
    reputation = ("rejected" if low & REJECTED_PRICE_SOURCES
                  else "approved" if low & APPROVED_PRICE_SOURCES
                  else "unknown")
    return score(source_count=max(1, len(srcs)), freshness_hours=fr.age_hours or 0.0,
                 source_agreement=1.0, source_reputation=reputation,
                 max_age_hours=max_age_hours, require_quorum=require_quorum)
