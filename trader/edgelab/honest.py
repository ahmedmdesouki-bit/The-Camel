"""
Honest-backtesting guards (S12) — keep the Edge Lab from lying to itself.

Walk-forward out-of-sample split, an overfit/decay guard (the out-of-sample edge must survive a fraction
of the in-sample edge), and the named crisis windows every candidate is stress-tested through. These pair
with the two-engine cross-check (`backtest.py`), point-in-time data (S4 known_at), and survivorship-free
prices (Sharadar, S12 backlog) — together that's the difference between a real edge and a curve fit.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# crisis windows for stress tests (a candidate must not blow up through these)
CRISIS_WINDOWS: Dict[str, Tuple[str, str]] = {
    "dotcom_2000": ("2000-03-01", "2002-10-31"),
    "gfc_2008": ("2007-10-01", "2009-03-31"),
    "covid_2020": ("2020-02-19", "2020-04-30"),
    "rate_shock_2022": ("2022-01-01", "2022-10-31"),
}


def walk_forward_split(n: int, train_frac: float = 0.7) -> Tuple[List[int], List[int]]:
    """Split a series of length n into an in-sample (train) and out-of-sample (test) index range.
    Parameters are fit on train; the edge is JUDGED on test (data the fit never saw)."""
    cut = max(1, min(n - 1, int(round(n * train_frac))))
    return list(range(cut)), list(range(cut, n))


def survives_out_of_sample(train_return: float, test_return: float, min_fraction: float = 0.5) -> bool:
    """The out-of-sample edge must survive at least `min_fraction` of the in-sample edge AND stay positive.
    A strong in-sample return that collapses out-of-sample is overfit — reject it."""
    if train_return <= 0:
        return test_return > 0
    return test_return > 0 and (test_return / train_return) >= min_fraction


def passes_crisis(crisis_drawdowns: Dict[str, float], max_drawdown: float = -0.35) -> bool:
    """All crisis-window drawdowns must be no worse than the floor (e.g. −35%)."""
    return all(dd >= max_drawdown for dd in crisis_drawdowns.values())
