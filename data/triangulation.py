"""
Multi-source price triangulation.

Stores one record per source per (symbol, date).
Flags disagreement when two sources' close prices differ by > threshold (0.5%).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple

from data.store import get_prices, store_price

DISAGREEMENT_THRESHOLD = 0.005   # 0.5%


@dataclass
class PriceDisagreement:
    symbol: str
    date: str
    source_a: str
    price_a: float
    source_b: str
    price_b: float
    diff_pct: float


def check_disagreement(
    db_path: str,
    symbol: str,
    date: str,
    threshold: float = DISAGREEMENT_THRESHOLD,
) -> List[PriceDisagreement]:
    """
    Return a PriceDisagreement for every pair of sources that disagree by
    more than `threshold` on close price.
    Empty list = all sources agree (or only one source available).
    """
    records = get_prices(db_path, symbol, date)
    disagreements: List[PriceDisagreement] = []

    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            a, b = records[i], records[j]
            ca, cb = a.get("close"), b.get("close")
            if ca is None or cb is None:
                continue
            ref = (ca + cb) / 2 or 1.0
            diff = abs(ca - cb) / ref
            if diff > threshold:
                disagreements.append(PriceDisagreement(
                    symbol=symbol,
                    date=date,
                    source_a=a["source"],
                    price_a=ca,
                    source_b=b["source"],
                    price_b=cb,
                    diff_pct=diff,
                ))

    return disagreements


def get_consensus_price(
    db_path: str,
    symbol: str,
    date: str,
) -> Tuple[Optional[float], List[PriceDisagreement]]:
    """
    Return (median_close, disagreements).
    Median across all sources is the consensus price.
    """
    records = get_prices(db_path, symbol, date)
    closes = sorted(r["close"] for r in records if r.get("close") is not None)

    if not closes:
        return None, []

    n = len(closes)
    median = (
        closes[n // 2] if n % 2
        else (closes[n // 2 - 1] + closes[n // 2]) / 2
    )
    return median, check_disagreement(db_path, symbol, date)
