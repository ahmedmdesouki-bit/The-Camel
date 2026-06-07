"""
S9 slice 3 — event intelligence + the event_reactions substrate.

Covers the deterministic synthesis (dedupe/quorum, entity-linking, severity/direction/theme),
the reaction math (forward returns, drawdown, excess-vs-benchmark, regime-at-event), the
injection-safety rule (safe=0 rows are never enriched/used), and idempotency.
"""
import json
from datetime import date, timedelta

from db.sqlite import connection
from data.entity_resolver import register_asset
from data.store import store_price
from sharia.whitelist import add_instrument
from trader.events.intelligence import (
    build_entity_dictionary, link_entities, score_severity, event_direction,
    map_theme, enrich_event, dedupe, run_event_intelligence,
)
from trader.events.reactions import (
    forward_returns_from, max_drawdown_window, regime_at,
    record_event_reactions, HORIZONS,
)


# ---------------- helpers ----------------

def _seed_prices(dbs, symbol, closes, start="2024-01-01"):
    d0 = date.fromisoformat(start)
    for k, c in enumerate(closes):
        store_price(dbs.market, {"symbol": symbol, "date": (d0 + timedelta(days=k)).isoformat(),
                                 "close": c, "adj_close": c}, source="test")


def _insert_event(dbs, *, event_id, title, source_id="gdelt", tone=3.0,
                  event_type="news_article", region=None, event_date="2024-01-01",
                  known_at="2024-01-01T00:00:00Z", safe=1, affected=None):
    with connection(dbs.news) as conn:
        conn.execute(
            "INSERT INTO news_events (event_id, event_type, title, tone, region, safe, affected_assets, "
            "event_date, reported_at, ingested_at, known_at, source_id, data_quality_score) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (event_id, event_type, title, tone, region, safe,
             json.dumps(affected) if affected is not None else None,
             event_date, known_at, known_at, known_at, source_id, 0.85))


# ---------------- deterministic synthesis ----------------

def test_link_entities_dictionary_match(dbs):
    register_asset(dbs, "AAPL", name="Apple Inc.", sector="Technology")
    add_instrument(dbs.sharia, "AAPL", "stock", approved_by="chiko", scan_id="s1")
    ed = build_entity_dictionary(dbs)
    assert link_entities("AAPL beats estimates; Apple raises guidance", ed) == ["AAPL"]
    assert link_entities("Some unrelated ZZZZ headline", ed) == []   # unknown ticker not matched


def test_severity_direction_theme():
    assert score_severity(9.0) == 5 and score_severity(0.0) == 1
    assert score_severity(0.0, "sanction") == 4           # event-type floor
    assert event_direction(3.0) == "positive" and event_direction(-3.0) == "negative"
    assert event_direction(0.0) == "neutral"
    assert map_theme("OPEC cuts crude output") == "energy"
    assert map_theme("Fed signals another rate hike") == "rates"
    assert map_theme("Missile strike near Hormuz") == "geopolitical_risk_off"
    assert map_theme("Local festival opens") == "general"


def test_dedupe_collapses_and_counts_quorum():
    evs = [
        {"event_id": "a", "title": "Apple beats earnings", "event_date": "2024-01-01",
         "known_at": "2024-01-01T09:00:00Z", "source_id": "gdelt"},
        {"event_id": "b", "title": "Apple  beats   earnings!", "event_date": "2024-01-01",
         "known_at": "2024-01-01T10:00:00Z", "source_id": "benzinga"},
    ]
    out = dedupe(evs)
    assert len(out) == 1
    canonical, quorum, dups = out[0]
    assert quorum == 2 and canonical["event_id"] == "a" and dups == ["b"]   # earliest known = canonical


def test_enrich_confidence_discounts_single_source(dbs):
    ed = build_entity_dictionary(dbs)
    ev = {"title": "x", "tone": 1.0, "data_quality_score": 0.8}
    assert enrich_event(ev, ed, quorum=1)["confidence"] == 0.4    # 0.8 * 0.5
    assert enrich_event(ev, ed, quorum=2)["confidence"] == 0.8    # 0.8 * 1.0


def test_run_event_intelligence_safe_only(dbs):
    register_asset(dbs, "AAPL", name="Apple Inc.", sector="Technology")
    _insert_event(dbs, event_id="ok", title="AAPL surges on strong guidance", tone=5.0)
    _insert_event(dbs, event_id="bad", title="[redacted: injection-flagged content]",
                  source_id="x", safe=0)
    n = run_event_intelligence(dbs)
    assert n == 1
    with connection(dbs.news) as conn:
        ok = conn.execute("SELECT affected_assets, severity FROM news_events WHERE event_id='ok'").fetchone()
        bad = conn.execute("SELECT affected_assets FROM news_events WHERE event_id='bad'").fetchone()
    assert json.loads(ok["affected_assets"]) == ["AAPL"] and ok["severity"] == 3   # |tone|=5 → ≥4 band
    assert bad["affected_assets"] is None                 # injection-flagged row never touched


# ---------------- reaction math (pure) ----------------

def test_forward_returns_from():
    series = [(f"2024-01-{d:02d}", 100.0 + i) for i, d in enumerate(range(1, 31))]
    r = forward_returns_from(series, "2024-01-01", [1, 5])
    assert r[1] == round(101 / 100 - 1, 6) and r[5] == round(105 / 100 - 1, 6)
    # a horizon beyond the series is None, not fabricated
    assert forward_returns_from(series, "2024-01-01", [999])[999] is None


def test_max_drawdown_window():
    # up to 110, dip to 90, recover — drawdown from the 110 peak to 90 = -18.18%
    closes = [100, 110, 90, 105]
    series = [(f"2024-01-{i+1:02d}", c) for i, c in enumerate(closes)]
    dd = max_drawdown_window(series, "2024-01-01", window=3)
    assert dd is not None and abs(dd - (90 / 110 - 1)) < 1e-6 and dd < 0


def test_regime_at_picks_latest_before_date(dbs):
    with connection(dbs.macro) as conn:
        conn.execute("INSERT INTO regime_history (classified_at, regime, confidence) VALUES (?,?,?)",
                     ("2023-12-01T00:00:00Z", "INFLATION_SHOCK", 0.7))
        conn.execute("INSERT INTO regime_history (classified_at, regime, confidence) VALUES (?,?,?)",
                     ("2024-02-01T00:00:00Z", "RECESSION_RISK", 0.6))
    assert regime_at(dbs, "2024-01-01") == "INFLATION_SHOCK"   # latest at/before the event
    assert regime_at(dbs, "2023-01-01") is None                # nothing recorded before


# ---------------- end-to-end reactions ----------------

def test_record_event_reactions_writes_excess_and_regime(dbs):
    _seed_prices(dbs, "AAPL", [100.0 + k for k in range(130)])     # linear up
    _seed_prices(dbs, "SPUS", [200.0 + 0.5 * k for k in range(130)])
    with connection(dbs.macro) as conn:
        conn.execute("INSERT INTO regime_history (classified_at, regime, confidence) VALUES (?,?,?)",
                     ("2023-12-15T00:00:00Z", "INFLATION_SHOCK", 0.7))
    register_asset(dbs, "AAPL", name="Apple Inc.", sector="Technology")
    # AAPL has prices, ZZZZ does not → ZZZZ must be skipped (no fabricated reaction)
    _insert_event(dbs, event_id="e1", title="AAPL event", affected=["AAPL", "ZZZZ"])

    n = record_event_reactions(dbs, benchmark="SPUS")
    assert n == 1
    with connection(dbs.news) as conn:
        row = dict(conn.execute("SELECT * FROM event_reactions WHERE event_id='e1'").fetchone())
    assert row["symbol"] == "AAPL" and row["sector"] == "Technology"
    assert row["return_1d"] is not None and row["return_21d"] > 0
    assert row["benchmark"] == "SPUS" and row["excess_return_21d"] is not None
    assert row["excess_return_21d"] > 0                         # AAPL rose faster than SPUS
    assert row["regime_at_event"] == "INFLATION_SHOCK"

    # idempotent: a second run writes nothing new
    assert record_event_reactions(dbs, benchmark="SPUS") == 0
