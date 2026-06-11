"""
S17 — the strategy-fit panel: the registry/matrix surfaced read-only in the snapshot, the dashboard, and
the coach.
"""
from dashboard.snapshot import build_snapshot
from dashboard.generate import build_dashboard_html
from founder_tools.coach import coach


def test_snapshot_includes_strategy_roster(dbs):
    ids = {x["id"] for x in build_snapshot(dbs)["strategies"]}
    assert {"core_dca", "ts_momentum", "mean_reversion", "dca_ladder"} <= ids


def test_dashboard_has_strategies_tab(dbs):
    html = build_dashboard_html(dbs)
    assert "Strategies" in html and "Strategy roster" in html and "core_dca" in html
    assert "data-view='strategies'" in html


def test_coach_strategies_route(dbs):
    out = coach(dbs, "what strategies are there?")
    assert "core_dca" in out and "rung" in out
