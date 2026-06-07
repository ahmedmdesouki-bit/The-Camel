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
from typing import Callable, List

from sharia.whitelist import freeze_instrument, load_whitelist
from sharia.aaoifi import (
    AAOIFIFinancials, screen as aaoifi_screen,
    DEBT_LIMIT, LIQUID_ASSETS_LIMIT, HARAM_INCOME_LIMIT,
)

# Re-export the verified limits so any legacy importer sees the unified AAOIFI values (not the old 33%).
DEBT_RATIO_LIMIT = DEBT_LIMIT                       # 0.30
INTEREST_ASSETS_RATIO_LIMIT = LIQUID_ASSETS_LIMIT   # 0.30
# HARAM_INCOME_LIMIT re-exported from aaoifi (0.05)


@dataclass
class Financials:
    """Compact snapshot used by the quarterly path. Mapped onto the full AAOIFI model on screen."""
    symbol: str
    market_cap: float
    total_debt: float
    cash_and_interest_securities: float
    non_compliant_income_pct: float   # 0.03 = 3%


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


def _to_aaoifi(f: Financials) -> AAOIFIFinancials:
    """Map the compact snapshot onto the verified AAOIFI model.

    The compact form carries 4 numbers, so we project them onto the AAOIFI denominators conservatively:
    market_cap stands in for the 12-month-average market cap; interest-bearing assets go to the liquid
    bucket; the income fraction becomes the haram-income ratio (total_revenue normalised to 1.0). Assets
    that the compact form doesn't track (receivables) are zero, and total_assets uses market_cap as a
    benign proxy so the ≤67% receivables ratio is computable and trivially passes rather than erroring.
    """
    return AAOIFIFinancials(
        symbol=f.symbol,
        avg_market_cap_12mo=f.market_cap,
        total_debt=f.total_debt,
        cash_and_deposits=0.0,
        interest_bearing_investments=f.cash_and_interest_securities,
        receivables=0.0,
        total_assets=f.market_cap or 1.0,
        non_compliant_revenue=f.non_compliant_income_pct,
        interest_income=0.0,
        total_revenue=1.0,
        sector="unknown",
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
    """Drift screen on one instrument via the verified AAOIFI ratios. Hard fail → not passed; doubtful →
    passed+note. **NOT a full compliance certification** — the compact `Financials` snapshot only carries
    debt/liquid/haram-income, so the receivables (≤67%) and prohibited-sector screens are *not* evaluated
    here (see `ScreenResult.unscreened`). Use `sharia/cross_check.py` (full `AAOIFIFinancials`) to certify
    a name as buyable; this path is for quarterly drift detection on already-whitelisted names only."""
    res = aaoifi_screen(_to_aaoifi(f))
    reasons = list(res.breaches)
    if res.status == "doubtful":
        reasons += res.near_misses
    return ScreenResult(symbol=f.symbol, passed=(res.status != "fail"), reasons=reasons, full_screen=False)


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

    return results
