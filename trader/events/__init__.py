"""Event intelligence + market-reaction substrate (S9 slice 3)."""
from trader.events.intelligence import (
    build_entity_dictionary, link_entities, score_severity, event_direction,
    map_theme, enrich_event, dedupe, run_event_intelligence,
)
from trader.events.reactions import (
    forward_returns_from, max_drawdown_window, regime_at,
    compute_event_reaction, record_event_reactions, HORIZONS,
)

__all__ = [
    "build_entity_dictionary", "link_entities", "score_severity", "event_direction",
    "map_theme", "enrich_event", "dedupe", "run_event_intelligence",
    "forward_returns_from", "max_drawdown_window", "regime_at",
    "compute_event_reaction", "record_event_reactions", "HORIZONS",
]
