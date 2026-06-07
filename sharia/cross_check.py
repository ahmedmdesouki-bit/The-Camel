"""
Sharia cross-check + multi-state status (S9 slice 4) — the compliance decision layer.

Sharia is #1 in the priority hierarchy, so this layer is deliberately **fail-safe and quorum-bound**:

  * MULTI-STATE status: pass / fail / doubtful / frozen / pending_review (not a bare boolean).
  * DISAGREEMENT RULE: the in-house AAOIFI screen is cross-checked against a canonical screener
    (Zoya/IdealRatings, injected). If they disagree → **doubtful → freeze for new buys, allow
    reduce-only exits, route to human review.** Never silently trust one over the other.
  * FAIL-SAFE QUORUM: a single source can FAIL a name but cannot CLEAR it. With no cross-check, a
    pass becomes **pending_review** (hold/observe, not a confident buy) — honoring "critical signals
    need ≥2 sources." A single-source fail is still a fail.
  * AUTHORITY STACK: local Sharia board > AAOIFI > founder (tighten-only) > agent (never). Some MENA
    markets' boards differ from AAOIFI; the local board, when present, overrides.
  * DRIFT: a held name whose debt/liquidity ratios crept toward the limit since the last screen is
    flagged early — a warning before an outright freeze.

The cross-check source and financials are injected (adapter pattern), so this is fully testable with
no network. The writer persists each screen to the append-only `sharia_status` table and freezes the
whitelist on any non-clear outcome.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional

from db.paths import CamelDbs
from db.sqlite import connection
from sharia.aaoifi import AAOIFIFinancials, AAOIFIResult, screen, DEBT_LIMIT, LIQUID_ASSETS_LIMIT
from sharia.whitelist import freeze_instrument, load_whitelist

# multi-state vocabulary
PASS, FAIL, DOUBTFUL, FROZEN, PENDING = "pass", "fail", "doubtful", "frozen", "pending_review"
_NON_CLEAR = {FAIL, DOUBTFUL, FROZEN}            # outcomes that block new buys (freeze the whitelist)

AUTHORITY_STACK = ["local_board", "AAOIFI", "founder", "agent"]
_REVIEW_DAYS = 90                                # quarterly re-screen
_DRIFT_MOVE = 0.01                               # ratio crept ≥ 1pp toward the limit → drift


@dataclass
class MultiStateStatus:
    symbol: str
    in_house_status: str
    cross_check_status: Optional[str]
    final_status: str
    methodology: str = "AAOIFI"
    authority: str = "AAOIFI"
    confidence: float = 0.0
    ratios: Dict = field(default_factory=dict)
    purification_ratio: float = 0.0
    sector: str = "unknown"
    drift: bool = False
    note: str = ""
    screened_at: str = ""
    known_at: str = ""
    next_review_at: str = ""
    source_hash: str = ""


def combine(in_house: str, cross_check: Optional[str]) -> tuple:
    """Combine the two screens into (final_status, confidence, note). Fail-safe + quorum-bound."""
    if in_house == FAIL or cross_check == FAIL:
        return FAIL, 0.95, "a screen failed → non-compliant"          # one failure is decisive
    if cross_check is None:
        # single source can't CLEAR a name → needs a second opinion before a confident buy
        return PENDING, 0.40, "no cross-check available → pending second source"
    if in_house == PASS and cross_check == PASS:
        return PASS, 0.90, "both screens pass"
    # one says pass, the other doubtful (or vice-versa) → disagreement
    return DOUBTFUL, 0.50, f"screens disagree (in-house={in_house}, cross-check={cross_check}) → freeze for new buys, reduce-only, human review"


def apply_authority(aaoifi_final: str, *, local_board_status: Optional[str] = None,
                    founder_action: Optional[str] = None) -> tuple:
    """Resolve the authority stack → (status, authority). Local board overrides; founder may only
    TIGHTEN (freeze a pass), never loosen; the agent has no say."""
    if local_board_status is not None:
        return local_board_status, "local_board"
    status, authority = aaoifi_final, "AAOIFI"
    if founder_action == "freeze" and status == PASS:        # tighten-only
        status, authority = FROZEN, "founder"
    return status, authority


def detect_drift(prev_ratios: Optional[Dict], curr_ratios: Dict) -> bool:
    """True if a debt/liquidity ratio crept ≥ _DRIFT_MOVE toward its limit since the last screen
    AND now sits in the doubtful band (early warning before a freeze)."""
    if not prev_ratios:
        return False
    for key, limit in (("debt_ratio", DEBT_LIMIT), ("liquid_assets_ratio", LIQUID_ASSETS_LIMIT)):
        prev, curr = prev_ratios.get(key), curr_ratios.get(key)
        if prev is None or curr is None:
            continue
        if (curr - prev) >= _DRIFT_MOVE and curr >= (limit - 0.05):
            return True
    return False


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _source_hash(f: AAOIFIFinancials) -> str:
    payload = json.dumps([f.symbol, f.avg_market_cap_12mo, f.total_debt, f.cash_and_deposits,
                          f.interest_bearing_investments, f.receivables, f.total_assets,
                          f.non_compliant_revenue, f.interest_income, f.total_revenue, f.sector],
                         sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def _prev_ratios(dbs: CamelDbs, symbol: str) -> Optional[Dict]:
    with connection(dbs.sharia) as conn:
        row = conn.execute("SELECT ratios FROM sharia_status WHERE symbol=? ORDER BY id DESC LIMIT 1",
                           (symbol,)).fetchone()
    if not row or not row["ratios"]:
        return None
    try:
        return json.loads(row["ratios"])
    except (ValueError, TypeError):
        return None


# whitelist sharia_status string per final state
_WHITELIST_STATUS = {PASS: "compliant", FAIL: "non_compliant", DOUBTFUL: "doubtful",
                     FROZEN: "frozen", PENDING: "pending_review"}


def evaluate_symbol(dbs: CamelDbs, symbol: str, fin: AAOIFIFinancials,
                    cross_check_status: Optional[str], *,
                    local_board_status: Optional[str] = None,
                    founder_action: Optional[str] = None, now: Optional[str] = None) -> MultiStateStatus:
    """Screen one symbol end-to-end and return its multi-state status (pure except the prev-ratios read)."""
    now = now or _utcnow()
    res: AAOIFIResult = screen(fin)
    final, conf, note = combine(res.status, cross_check_status)
    final, authority = apply_authority(final, local_board_status=local_board_status,
                                       founder_action=founder_action)
    drift = detect_drift(_prev_ratios(dbs, symbol), res.ratios)
    return MultiStateStatus(
        symbol=symbol, in_house_status=res.status, cross_check_status=cross_check_status,
        final_status=final, methodology=res.methodology, authority=authority, confidence=conf,
        ratios=res.ratios, purification_ratio=res.purification_ratio, sector=fin.sector,
        drift=drift, note=note, screened_at=now, known_at=now,
        next_review_at=(datetime.fromisoformat(now.replace("Z", "+00:00")) + timedelta(days=_REVIEW_DAYS)).isoformat(),
        source_hash=_source_hash(fin),
    )


def _persist(dbs: CamelDbs, st: MultiStateStatus) -> None:
    with connection(dbs.sharia) as conn:
        conn.execute(
            "INSERT INTO sharia_status (symbol, in_house_status, cross_check_status, final_status, "
            " methodology, authority, confidence, ratios, purification_ratio, sector, drift, "
            " screened_at, known_at, next_review_at, source_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (st.symbol, st.in_house_status, st.cross_check_status, st.final_status, st.methodology,
             st.authority, st.confidence, json.dumps(st.ratios), st.purification_ratio, st.sector,
             1 if st.drift else 0, st.screened_at, st.known_at, st.next_review_at, st.source_hash),
        )
        conn.execute(
            "UPDATE whitelist SET sharia_status=?, purification_ratio=? WHERE symbol=?",
            (_WHITELIST_STATUS.get(st.final_status, "unknown"), st.purification_ratio, st.symbol),
        )


def run_sharia_cross_check(dbs: CamelDbs,
                           get_financials: Callable[[str], AAOIFIFinancials],
                           get_cross_check_status: Callable[[str], Optional[str]],
                           *, local_board: Optional[Dict[str, str]] = None,
                           now: Optional[str] = None) -> List[MultiStateStatus]:
    """Re-screen every whitelist name through the in-house AAOIFI screen + the injected canonical
    cross-check, persist the multi-state status, and **freeze any non-clear outcome** (fail / doubtful
    / disagreement) for new buys (reduce-only exits stay allowed). Returns all statuses."""
    local_board = local_board or {}
    out: List[MultiStateStatus] = []
    for symbol in load_whitelist(dbs.sharia):
        try:
            fin = get_financials(symbol)
            cc = get_cross_check_status(symbol)
        except Exception as exc:
            # fail-safe: any error screening a name freezes it (never trade through uncertainty)
            freeze_instrument(dbs.sharia, symbol, reason=f"sharia cross-check error: {exc}")
            out.append(MultiStateStatus(symbol=symbol, in_house_status="error", cross_check_status=None,
                                        final_status=FROZEN, authority="AAOIFI", note=str(exc)))
            continue
        st = evaluate_symbol(dbs, symbol, fin, cc, local_board_status=local_board.get(symbol), now=now)
        _persist(dbs, st)
        if st.final_status in _NON_CLEAR:
            reason = f"AAOIFI cross-check → {st.final_status}: {st.note}"
            if st.drift:
                reason += " (ratio drift since last screen)"
            freeze_instrument(dbs.sharia, symbol, reason=reason)
        out.append(st)
    return out
