"""
Quarterly Sharia re-screen job.

AAOIFI limits (from spec §2.1):
  - debt / market_cap            < 33%
  - (cash + interest_securities) / market_cap < 33%
  - non_compliant_income_pct     < 5%

The financials getter is injected (adapter pattern) so the job is
fully testable without network I/O.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List

from sharia.whitelist import freeze_instrument, load_whitelist

DEBT_RATIO_LIMIT = 0.33
INTEREST_ASSETS_RATIO_LIMIT = 0.33
HARAM_INCOME_LIMIT = 0.05


@dataclass
class Financials:
    """Snapshot used for AAOIFI ratio checks."""
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


def compute_aaoifi_ratios(f: Financials) -> dict:
    """Return the three AAOIFI ratios.  Guards against zero market_cap."""
    mc = f.market_cap if f.market_cap > 0 else 1.0
    return {
        "debt_ratio": f.total_debt / mc,
        "interest_assets_ratio": f.cash_and_interest_securities / mc,
        "haram_income_pct": f.non_compliant_income_pct,
    }


def screen_instrument(f: Financials) -> ScreenResult:
    """Run AAOIFI checks on one instrument's financials."""
    ratios = compute_aaoifi_ratios(f)
    reasons: List[str] = []

    if ratios["debt_ratio"] >= DEBT_RATIO_LIMIT:
        reasons.append(
            f"debt_ratio={ratios['debt_ratio']:.1%} >= {DEBT_RATIO_LIMIT:.0%} limit"
        )
    if ratios["interest_assets_ratio"] >= INTEREST_ASSETS_RATIO_LIMIT:
        reasons.append(
            f"interest_assets_ratio={ratios['interest_assets_ratio']:.1%}"
            f" >= {INTEREST_ASSETS_RATIO_LIMIT:.0%} limit"
        )
    if ratios["haram_income_pct"] >= HARAM_INCOME_LIMIT:
        reasons.append(
            f"haram_income_pct={ratios['haram_income_pct']:.1%}"
            f" >= {HARAM_INCOME_LIMIT:.0%} limit"
        )

    return ScreenResult(symbol=f.symbol, passed=len(reasons) == 0, reasons=reasons)


def run_quarterly_rescreen(
    db_path: str,
    get_financials: Callable[[str], Financials],
) -> List[ScreenResult]:
    """
    Re-screen every non-frozen whitelist instrument.
    Non-compliant drift → freeze + log.
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
