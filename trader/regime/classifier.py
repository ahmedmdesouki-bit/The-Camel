"""
Regime classifier v0 (S9) — deterministic, rule-based, signal-scored.

Takes a feature dict (from feature_builder) and scores each regime by how many macro signals
corroborate it; the highest-scoring regime wins, with a confidence = winning / total score.
Pure and side-effect-free. v0 covers the macro-derivable regimes; AI_CAPEX_BOOM and a confident
RECOVERY need equity/sector signals (a later refinement) — they remain defined but rarely assigned.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class Regime(str, Enum):
    LIQUIDITY_EXPANSION = "LIQUIDITY_EXPANSION"
    LIQUIDITY_TIGHTENING = "LIQUIDITY_TIGHTENING"
    INFLATION_SHOCK = "INFLATION_SHOCK"
    DISINFLATION_GROWTH = "DISINFLATION_GROWTH"
    RECESSION_RISK = "RECESSION_RISK"
    RECOVERY = "RECOVERY"
    COMMODITY_SUPPLY_SHOCK = "COMMODITY_SUPPLY_SHOCK"
    GEOPOLITICAL_RISK_OFF = "GEOPOLITICAL_RISK_OFF"
    AI_CAPEX_BOOM = "AI_CAPEX_BOOM"
    USD_STRENGTH_EM_PRESSURE = "USD_STRENGTH_EM_PRESSURE"
    UNKNOWN = "UNKNOWN"


# thresholds (founder-tunable later; deliberately explicit for auditability)
USD_STRONG = 120.0          # DTWEXBGS broad USD index level considered "strong"


@dataclass
class RegimeResult:
    regime: Regime
    confidence: float
    signals: List[str] = field(default_factory=list)
    features: Dict[str, Optional[float]] = field(default_factory=dict)


def classify(f: Dict[str, Optional[float]]) -> RegimeResult:
    """Score regimes from macro features; return the winner + confidence + the signals that fired."""
    s: Dict[Regime, float] = defaultdict(float)
    sig: List[str] = []

    cpi = f.get("cpi_yoy")
    curve = f.get("yield_curve")
    hy = f.get("hy_spread")
    vix = f.get("vix")
    ff = f.get("fed_funds")
    unemp = f.get("unemployment")
    oil = f.get("oil_change_pct")
    usd = f.get("usd")

    if cpi is not None and cpi >= 4.0:
        s[Regime.INFLATION_SHOCK] += 1.0; sig.append(f"cpi_yoy={cpi:.1f}>=4")
    if cpi is not None and cpi <= 2.5:
        s[Regime.DISINFLATION_GROWTH] += 0.7; sig.append(f"cpi_yoy={cpi:.1f}<=2.5")
    if curve is not None and curve < 0:
        s[Regime.RECESSION_RISK] += 1.0; sig.append(f"inverted_curve={curve:.2f}")
    if hy is not None and hy >= 5.0:
        s[Regime.RECESSION_RISK] += 1.0; sig.append(f"hy_spread={hy:.1f}>=5")
    if vix is not None and vix >= 30.0:
        s[Regime.GEOPOLITICAL_RISK_OFF] += 1.0; s[Regime.RECESSION_RISK] += 0.5
        sig.append(f"vix={vix:.0f}>=30")
    if ff is not None and ff >= 4.0:
        s[Regime.LIQUIDITY_TIGHTENING] += 1.0; sig.append(f"fed_funds={ff:.2f}>=4")
    if ff is not None and ff <= 1.0:
        s[Regime.LIQUIDITY_EXPANSION] += 1.0; sig.append(f"fed_funds={ff:.2f}<=1")
    if oil is not None and oil >= 20.0:
        s[Regime.COMMODITY_SUPPLY_SHOCK] += 1.0; sig.append(f"oil_yoy={oil:.0f}%>=20")
    if usd is not None and usd >= USD_STRONG:
        s[Regime.USD_STRENGTH_EM_PRESSURE] += 0.8; sig.append(f"usd={usd:.0f}>= {USD_STRONG:.0f}")
    if unemp is not None and unemp >= 5.0:
        s[Regime.RECESSION_RISK] += 0.5; sig.append(f"unemployment={unemp:.1f}>=5")
    # SAR/USD peg stress (from FRED DEXSAUS via the peg monitor) — a Gulf-book risk-off shock.
    # Normally 0 (peg intact since 1986); only fires on real drift, so it never perturbs benign regimes.
    peg_dev = f.get("peg_deviation_pct")
    if peg_dev is not None and abs(peg_dev) >= 0.5:
        s[Regime.GEOPOLITICAL_RISK_OFF] += 1.0; s[Regime.USD_STRENGTH_EM_PRESSURE] += 0.5
        sig.append(f"sar_peg_drift={peg_dev:+.2f}%")

    if not s:
        have_data = any(v is not None for v in (cpi, curve, hy, vix, ff, unemp, oil, usd))
        if have_data:
            return RegimeResult(Regime.RECOVERY, 0.4, ["benign: no stress signals"], dict(f))
        return RegimeResult(Regime.UNKNOWN, 0.0, ["no macro data"], dict(f))

    # winner = highest score; ties broken by an explicit risk-first priority (not insertion order)
    regime = max(s, key=lambda k: (s[k], -_TIE_PRIORITY.index(k)))
    total = sum(s.values())
    confidence = round(s[regime] / total, 2) if total else 0.0
    return RegimeResult(regime, confidence, sig, dict(f))


# tie-break order: most risk-relevant regimes win an equal-score tie
_TIE_PRIORITY = [
    Regime.RECESSION_RISK, Regime.GEOPOLITICAL_RISK_OFF, Regime.INFLATION_SHOCK,
    Regime.COMMODITY_SUPPLY_SHOCK, Regime.LIQUIDITY_TIGHTENING, Regime.USD_STRENGTH_EM_PRESSURE,
    Regime.LIQUIDITY_EXPANSION, Regime.DISINFLATION_GROWTH, Regime.RECOVERY,
]


# regime → favoured sectors/themes (consumed by the S9 regime→theme mapper / S11 strategy selection)
_THEMES = {
    Regime.INFLATION_SHOCK: ["energy", "commodities", "materials", "value"],
    Regime.RECESSION_RISK: ["defensives", "quality", "utilities", "healthcare", "cash"],
    Regime.LIQUIDITY_EXPANSION: ["growth", "technology", "small_cap"],
    Regime.LIQUIDITY_TIGHTENING: ["value", "quality", "short_duration"],
    Regime.DISINFLATION_GROWTH: ["technology", "growth", "consumer_discretionary"],
    Regime.RECOVERY: ["cyclicals", "industrials", "financials"],
    Regime.COMMODITY_SUPPLY_SHOCK: ["energy", "materials", "commodities"],
    Regime.GEOPOLITICAL_RISK_OFF: ["defensives", "gold", "energy", "cash"],
    Regime.AI_CAPEX_BOOM: ["technology", "semiconductors", "data_center"],
    Regime.USD_STRENGTH_EM_PRESSURE: ["us_large_cap", "domestic", "quality"],
    Regime.UNKNOWN: [],
}


def regime_to_themes(regime: Regime) -> List[str]:
    return list(_THEMES.get(regime, []))
