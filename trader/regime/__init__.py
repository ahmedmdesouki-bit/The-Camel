"""
Regime engine (S9) — classify the macro environment before choosing strategy.

feature_builder pulls point-in-time macro features from camel_macro.db; classifier_v0 applies
deterministic rules → a Regime + confidence; history_store persists the call; themes maps a regime
to favoured sectors. All deterministic; the LLM never decides the regime.
"""
from trader.regime.classifier import Regime, RegimeResult, classify, regime_to_themes
from trader.regime.features import build_features, DEFAULT_SERIES
from trader.regime.history import record_regime, latest_regime

__all__ = [
    "Regime", "RegimeResult", "classify", "regime_to_themes",
    "build_features", "DEFAULT_SERIES", "record_regime", "latest_regime",
]
