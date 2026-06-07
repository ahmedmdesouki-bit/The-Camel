"""
Dividend mechanics (S11) — model the cash, not a single opaque event.

Pure helpers for the gross → withholding → net split and the purification amount. **Tax frame = NRA
withholding** (the founder is KSA-resident): a US dividend to a non-resident alien is taxed by treaty
withholding (Form 1042-S / DIVNRA), reported gross/withheld/net separately — the US qualified-dividend
60-day rule is largely N/A. Lot-level accounting and the 4-stage corporate-action pipeline land with the
realistic-paper engine (S12); these are the primitives the `dividend_growth` strategy and S12 share.
"""
from __future__ import annotations

from dataclasses import dataclass

# default US→KSA treaty-style withholding (verify the exact treaty rate at procurement; 0.30 is the
# statutory NRA default when no treaty rate applies)
DEFAULT_NRA_WITHHOLDING = 0.30


@dataclass
class DividendCash:
    gross: float
    withheld: float
    net: float
    withholding_rate: float


def net_dividend(gross: float, withholding_rate: float = DEFAULT_NRA_WITHHOLDING) -> DividendCash:
    """Split a gross dividend into withheld + net (NRA frame). Stored as three separate amounts."""
    rate = max(0.0, min(1.0, withholding_rate))
    withheld = round(gross * rate, 6)
    return DividendCash(gross=round(gross, 6), withheld=withheld,
                        net=round(gross - withheld, 6), withholding_rate=rate)


def purification_amount(dividend_received: float, impure_fraction: float) -> float:
    """The impure portion of a dividend to give away (purification). `impure_fraction` comes from the
    AAOIFI screen's purification_ratio (S9)."""
    return round(max(0.0, dividend_received) * max(0.0, min(1.0, impure_fraction)), 6)
