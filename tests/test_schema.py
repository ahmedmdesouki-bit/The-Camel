"""
Data-layer architecture guards (from the 2026-06-11 review):
  * `init_all` is the SINGLE, COMPLETE source of truth — every table a feature module relies on has a
    canonical home (no orphans).
  * the hot-path indexes exist.
  * a feature module's defensive `_ensure_*` delegates to the canonical init and changes nothing.
"""
from db.paths import init_all
from db.sqlite import connection


def _objs(db: str, kind: str) -> set:
    with connection(db) as conn:
        return {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type=? AND name NOT LIKE 'sqlite_%'", (kind,))}


def test_init_all_creates_the_complete_schema(dbs):
    init_all(dbs)
    assert {"orders", "positions", "ledger", "runs", "guardrail_events", "approvals", "tasks",
            "op_log", "heartbeat", "portfolios", "portfolio_holdings"} <= _objs(dbs.portfolio, "table")
    assert {"prices", "dividends", "splits", "source_documents"} <= _objs(dbs.market, "table")
    assert {"macro_snapshots", "macro_observations", "regime_history"} <= _objs(dbs.macro, "table")
    assert {"whitelist", "sharia_events", "sharia_status", "etf_holdings", "sanctions"} \
        <= _objs(dbs.sharia, "table")
    # the two tables that used to live ONLY in feature modules now have a canonical home:
    assert {"learning_ledger", "edge_reports", "strategy_base_rates", "learning_proposals",
            "opportunity_proposals", "desk_control", "desk_runs", "research_evidence",
            "memory_consolidation"} <= _objs(dbs.learning, "table")


def test_hot_path_indexes_exist(dbs):
    init_all(dbs)
    assert "idx_macro_obs_series" in _objs(dbs.macro, "index")
    assert {"idx_sanctions_norm", "idx_sharia_status_symbol"} <= _objs(dbs.sharia, "index")
    assert {"idx_learning_ledger_type", "idx_opportunity_proposals_status", "idx_desk_runs_desk",
            "idx_edge_reports_symbol"} <= _objs(dbs.learning, "index")


def test_feature_ensure_is_a_noop_against_canonical(dbs):
    """A defensive `_ensure_*` must delegate to the canonical init and add nothing — proving there is one
    source of truth, not two that can drift."""
    init_all(dbs)
    before = _objs(dbs.learning, "table") | _objs(dbs.learning, "index")
    from research.workforce import _ensure_desk_runs
    from loop.opportunity_board import _ensure_table
    from sharia.sanctions import _ensure_table as _ensure_sanctions
    _ensure_desk_runs(dbs.learning)
    _ensure_table(dbs.learning)
    _ensure_sanctions(dbs.sharia)
    assert (_objs(dbs.learning, "table") | _objs(dbs.learning, "index")) == before


def test_timestamp_helpers():
    from db.sqlite import utcnow_iso, parse_ts
    now = parse_ts(utcnow_iso())
    assert now is not None and now.tzinfo is not None                 # the app 'now' is tz-aware
    assert parse_ts("2026-06-11T16:30:45.123Z").tzinfo is not None    # new-default 'Z' shape
    assert parse_ts("2026-06-11T16:30:45+00:00").tzinfo is not None   # app isoformat shape
    assert parse_ts("2026-06-11 16:30:45").tzinfo is not None         # legacy SQLite naive -> assumed UTC
    assert parse_ts("") is None and parse_ts("garbage") is None


def test_default_timestamp_is_tz_aware(dbs):
    """A row the app doesn't stamp now gets the standardized tz-aware default (not the legacy naive shape)."""
    from db.sqlite import connection, parse_ts
    init_all(dbs)
    with connection(dbs.learning) as conn:
        conn.execute("INSERT INTO memory_consolidation (summary) VALUES ('x')")
        ts = conn.execute("SELECT ts FROM memory_consolidation ORDER BY id DESC LIMIT 1").fetchone()[0]
    assert "T" in ts and ts.endswith("Z")                            # standardized shape
    assert parse_ts(ts).tzinfo is not None


def test_dump_schema_is_authoritative_and_complete():
    """The generator dumps the live schema for all 7 DBs incl. the formerly-orphan tables + indexes —
    so the Phase-1 Postgres migration is driven by reality, not the (now-quarantined) schema.sql."""
    from db.dump_schema import dump_schema, render, DB_ORDER
    s = dump_schema()
    assert set(s.keys()) == set(DB_ORDER)
    text = render(s)
    for obj in ("prices", "macro_observations", "orders", "ledger", "positions", "whitelist",
                "sanctions", "desk_runs", "memory_consolidation", "idx_macro_obs_series"):
        assert obj in text
