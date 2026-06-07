"""
Quarterly Sharia re-screen job — now a thin adapter over the verified AAOIFI screen.

**Migration (backlog sweep):** this module no longer carries its own looser 33% two-ratio model. It now
**delegates to `sharia/aaoifi.py`** — the canonical, verified AAOIFI / FTSE-IdealRatings spec (≤30% debt,
≤30% liquid assets, ≤67% receivables, ≤5% haram income, + the 11 prohibited sectors). That makes
`sharia/aaoifi.py` the *single* source of truth for compliance thresholds; the old 33% vs 30%
inconsistency is gone. This module keeps the small, convenient `Financials` snapshot + the quarterly
"freeze on drift" workflow that the rest of the system already calls.

A name that lands just **inside** a 30% limit is reported by AAOIFI as *doubtful* (a watch band) — here it
is treated as **passed-with-a-note** (we don't auto-freeze a doubtful name; that's the cross-check's job),
and only a hard AAOIFI **fail** freezes the instrument.

The financials getter is injected (adapter pattern) so the job is fully testable without network I/O.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from db.sqlite import connection
from sharia.whitelist import freeze_instrument, load_whitelist
from sharia.aaoifi import (
    AAOIFIFinancials, screen as aaoifi_screen,
    DEBT_LIMIT, LIQUID_ASSETS_LIMIT, HARAM_INCOME_LIMIT,
)


def _mark_doubtful(db_path: str, symbol: str) -> None:
    """P2-E: a doubtful (watch-band) name must not stay `compliant` on the whitelist. Mark it doubtful
    so the Constitution treats it as non-buyable (close-only), matching cross_check's behaviour."""
    try:
        with connection(db_path) as conn:
            conn.execute("UPDATE whitelist SET sharia_status='doubtful' WHERE symbol=?", (symbol,))
    except Exception:                              # best-effort; never break the rescreen loop
        pass

# Re-export the verified limits so any legacy importer sees the unified AAOIFI values (not the old 33%).
DEBT_RATIO_LIMIT = DEBT_LIMIT                       # 0.30
INTEREST_ASSETS_RATIO_LIMIT = LIQUID_ASSETS_LIMIT   # 0.30
# HARAM_INCOME_LIMIT re-exported from aaoifi (0.05)


@dataclass
class Financials:
    """Compact snapshot used by the quarterly path. Mapped onto the full AAOIFI model on screen.

    The first four fields are the drift-screen core (debt / liquid / haram-income). Supply the three
    OPTIONAL fields (P2-D) and the screen becomes a *full* AAOIFI screen — receivables ≤67% and the
    11 prohibited sectors are then evaluated too, and `ScreenResult.full_screen` is True."""
    symbol: str
    market_cap: float
    total_debt: float
    cash_and_interest_securities: float
    non_compliant_income_pct: float   # 0.03 = 3%
    receivables: Optional[float] = None     # supply to run the ≤67% receivables screen
    total_assets: Optional[float] = None    # denominator for the receivables screen
    sector: Optional[str] = None            # supply to run the 11-prohibited-sector exclusion


@dataclass
class ScreenResult:
    symbol: str
    passed: bool
    reasons: List[str] = field(default_factory=list)
    # ⚠️ The compact path screens ONLY debt/liquid/haram-income (drift detection). The two AAOIFI screens
    # the compact `Financials` snapshot cannot express are listed here so a `passed=True` from this path can
    # NEVER be mistaken for a full compliance certification. Authoritative compliance = `sharia/cross_check.py`.
    full_screen: bool = False
    unscreened: List[str] = field(default_factory=lambda: ["receivables_ratio", "prohibited_sector"])


def _is_full(f: Financials) -> bool:
    """True when the optional fields are all supplied → all 5 AAOIFI screens can run."""
    return f.receivables is not None and f.total_assets is not None and f.sector is not None


def _unscreened(f: Financials) -> List[str]:
    missing: List[str] = []
    if f.receivables is None or f.total_assets is None:
        missing.append("receivables_ratio")
    if f.sector is None:
        missing.append("prohibited_sector")
    return missing


def _to_aaoifi(f: Financials) -> AAOIFIFinancials:
    """Map the compact snapshot onto the verified AAOIFI model.

    The four core fields drive debt/liquid/haram-income. When the OPTIONAL receivables/total_assets/
    sector are supplied (P2-D) they drive the ≤67% receivables screen and the prohibited-sector
    exclusion too. When absent, receivables defaults to 0 and total_assets to market_cap (so the
    ≤67% screen is computable and trivially passes) and the sector is "unknown" — those dimensions
    are then flagged in `ScreenResult.unscreened` so a pass is never read as full certification.
    """
    return AAOIFIFinancials(
        symbol=f.symbol,
        avg_market_cap_12mo=f.market_cap,
        total_debt=f.total_debt,
        cash_and_deposits=0.0,
        interest_bearing_investments=f.cash_and_interest_securities,
        receivables=f.receivables if f.receivables is not None else 0.0,
        total_assets=f.total_assets if f.total_assets is not None else (f.market_cap or 1.0),
        non_compliant_revenue=f.non_compliant_income_pct,
        interest_income=0.0,
        total_revenue=1.0,
        sector=f.sector if f.sector is not None else "unknown",
    )


def compute_aaoifi_ratios(f: Financials) -> dict:
    """Legacy 3-ratio view, now computed via the verified screen (guards zero market_cap)."""
    res = aaoifi_screen(_to_aaoifi(f))
    return {
        "debt_ratio": res.ratios.get("debt_ratio"),
        "interest_assets_ratio": res.ratios.get("liquid_assets_ratio"),
        "haram_income_pct": res.ratios.get("haram_income_pct"),
    }


def screen_instrument(f: Financials) -> ScreenResult:
    """Screen one instrument via the verified AAOIFI ratios. Hard fail → not passed; doubtful → passed+note.

    If the OPTIONAL receivables/total_assets/sector are supplied this is a **full** AAOIFI screen (all 5
    rules, `full_screen=True`). If not, it is a **drift screen** of debt/liquid/haram-income only — the
    receivables (≤67%) and prohibited-sector screens are skipped and listed in `unscreened`, so a
    `passed=True` is never mistaken for full certification. `sharia/cross_check.py` remains authoritative."""
    res = aaoifi_screen(_to_aaoifi(f))
    reasons = list(res.breaches)
    if res.status == "doubtful":
        reasons += res.near_misses
    return ScreenResult(symbol=f.symbol, passed=(res.status != "fail"), reasons=reasons,
                        full_screen=_is_full(f), unscreened=_unscreened(f))


def run_quarterly_rescreen(
    db_path: str,
    get_financials: Callable[[str], Financials],
) -> List[ScreenResult]:
    """
    Re-screen every non-frozen whitelist instrument.
    A hard AAOIFI fail → freeze + log. Doubtful names pass (the cross-check handles watch/disagreement).
    Returns all ScreenResults (both passed and failed).
    """
    whitelist = load_whitelist(db_path)
    results: List[ScreenResult] = []

    for symbol, inst in whitelist.items():
        if inst.frozen:
            continue  # already frozen — skip until manually unfrozen

        try:
            financials = get_financials(symbol)
        except Exception as exc:
            results.append(
                ScreenResult(symbol=symbol, passed=False,
                             reasons=[f"financials fetch error: {exc}"])
            )
            continue

        result = screen_instrument(financials)
        results.append(result)

        if not result.passed:
            freeze_instrument(
                db_path, symbol,
                reason="AAOIFI drift: " + "; ".join(result.reasons),
            )
        elif result.reasons:                       # passed but in the doubtful watch band (P2-E)
            _mark_doubtful(db_path, symbol)

    return results
