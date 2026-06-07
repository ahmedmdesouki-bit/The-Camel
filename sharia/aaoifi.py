"""
In-house AAOIFI Sharia screen (S9 slice 4) — the verified ratio spec.

This is the canonical financial screen. It supersedes the older/looser 33% screen in
`sharia/screener.py` (Dow-Jones-style) with the verified **AAOIFI / FTSE-Russell-IdealRatings**
methodology (see `docs/CAMEL_DATA_SOURCES.md` and `docs/CAMEL_CONSTITUTION.md`):

  1. interest-bearing debt ÷ 12-month-average market cap                       ≤ 30%
  2. (cash + deposits + interest-bearing investments) ÷ 12-mo-avg market cap   ≤ 30%
  3. (cash + deposits + receivables) ÷ total assets                            ≤ 67%
  4. non-compliant revenue + non-operating interest income ÷ total income      ≤ 5%
  5. 11 prohibited business sectors → outright exclusion regardless of ratios

Two AAOIFI-specific details we get right: the 30% screens use the **12-month-average** market cap
(not a spot snapshot — a documented difference vs. Zoya's plain-market-cap default), and a name that
sits just under a limit is flagged **doubtful** (a watch band), not silently passed.

Pure and side-effect-free — fully unit-tested. Computed from SEC/XBRL fundamentals (free); the result
is cross-checked against a canonical screener in `sharia/cross_check.py` (the multi-state status +
disagreement→freeze rule). Purification ratio (the impure fraction of income to give away) is reported
so `dividend_growth` (S11) can purify.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ---- thresholds (verified AAOIFI spec; founder-owned, deliberately explicit) ----
DEBT_LIMIT = 0.30                 # debt ÷ 12-mo-avg market cap
LIQUID_ASSETS_LIMIT = 0.30        # (cash + deposits + interest investments) ÷ 12-mo-avg market cap
RECEIVABLES_LIMIT = 0.67          # (cash + deposits + receivables) ÷ total assets
HARAM_INCOME_LIMIT = 0.05         # non-compliant revenue + interest income ÷ total income
DOUBTFUL_MARGIN = 0.02            # within 2pp below a 30% limit → "doubtful" watch band

# the 11 AAOIFI-prohibited business sectors (normalised keys)
PROHIBITED_SECTORS = {
    "alcohol", "gambling", "pork", "tobacco", "conventional_finance",
    "conventional_insurance", "defense", "adult", "hotels", "music", "cinema_broadcasting",
}


@dataclass
class AAOIFIFinancials:
    """One point-in-time fundamentals snapshot (from SEC/XBRL). All currency amounts same units."""
    symbol: str
    avg_market_cap_12mo: float        # the AAOIFI denominator (12-month average, NOT spot)
    total_debt: float = 0.0
    cash_and_deposits: float = 0.0
    interest_bearing_investments: float = 0.0
    receivables: float = 0.0
    total_assets: float = 0.0
    non_compliant_revenue: float = 0.0
    interest_income: float = 0.0
    total_revenue: float = 0.0
    sector: str = "unknown"           # normalised; matched against PROHIBITED_SECTORS


@dataclass
class AAOIFIResult:
    symbol: str
    status: str                       # "pass" | "doubtful" | "fail"
    ratios: Dict[str, Optional[float]] = field(default_factory=dict)
    purification_ratio: float = 0.0   # impure income fraction to purify
    sector_excluded: bool = False
    breaches: List[str] = field(default_factory=list)     # hard fails
    near_misses: List[str] = field(default_factory=list)  # doubtful-band warnings
    methodology: str = "AAOIFI"


def _ratio(numer: float, denom: float) -> Optional[float]:
    if denom is None or denom <= 0:
        return None                   # cannot compute → unknown (handled conservatively upstream)
    return numer / denom


def compute_ratios(f: AAOIFIFinancials) -> Dict[str, Optional[float]]:
    return {
        "debt_ratio": _ratio(f.total_debt, f.avg_market_cap_12mo),
        "liquid_assets_ratio": _ratio(
            (f.cash_and_deposits or 0) + (f.interest_bearing_investments or 0), f.avg_market_cap_12mo),
        "receivables_ratio": _ratio(
            (f.cash_and_deposits or 0) + (f.receivables or 0), f.total_assets),
        "haram_income_pct": _ratio(
            (f.non_compliant_revenue or 0) + (f.interest_income or 0), f.total_revenue),
    }


def purification_ratio(f: AAOIFIFinancials) -> float:
    r = _ratio((f.non_compliant_revenue or 0) + (f.interest_income or 0), f.total_revenue)
    return round(r, 6) if r is not None else 0.0


def screen(f: AAOIFIFinancials) -> AAOIFIResult:
    """Run the full AAOIFI screen on one snapshot. Conservative: a missing ratio (no denominator)
    is treated as a near-miss (doubtful), never a silent pass."""
    ratios = compute_ratios(f)
    breaches: List[str] = []
    near_misses: List[str] = []

    sector_excluded = (f.sector or "").strip().lower().replace(" ", "_").replace("/", "_") in PROHIBITED_SECTORS
    if sector_excluded:
        breaches.append(f"prohibited sector: {f.sector}")

    limits = {
        "debt_ratio": DEBT_LIMIT,
        "liquid_assets_ratio": LIQUID_ASSETS_LIMIT,
        "receivables_ratio": RECEIVABLES_LIMIT,
        "haram_income_pct": HARAM_INCOME_LIMIT,
    }
    for key, limit in limits.items():
        val = ratios.get(key)
        if val is None:
            near_misses.append(f"{key}: no data → cannot confirm ≤ {limit:.0%}")
            continue
        if val > limit:
            breaches.append(f"{key}={val:.2%} > {limit:.0%} limit")
        elif key in ("debt_ratio", "liquid_assets_ratio") and val >= (limit - DOUBTFUL_MARGIN):
            near_misses.append(f"{key}={val:.2%} within {DOUBTFUL_MARGIN:.0%} of the {limit:.0%} limit")

    if breaches:
        status = "fail"
    elif near_misses:
        status = "doubtful"
    else:
        status = "pass"

    return AAOIFIResult(
        symbol=f.symbol, status=status, ratios={k: (round(v, 6) if v is not None else None)
                                                for k, v in ratios.items()},
        purification_ratio=purification_ratio(f), sector_excluded=sector_excluded,
        breaches=breaches, near_misses=near_misses,
    )
