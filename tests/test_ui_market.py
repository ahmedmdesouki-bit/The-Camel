"""
S-UI — the interface enhancement: the watchlist store, real price changes, and the snapshot/dashboard
Market / Watchlist / Hotlist tabs (Camel Design System, real ingested numbers).
"""
from datetime import datetime, timedelta

from data.store import store_price
from data.watchlist import seed_watchlist, add_to_watchlist, list_watchlist, price_change
from dashboard.snapshot import build_snapshot
from dashboard.generate import build_dashboard_html


def _series(dbs, symbol, closes):
    base = datetime(2026, 5, 1)
    for i, c in enumerate(closes):
        d = (base + timedelta(days=i)).date().isoformat()
        store_price(dbs.market, {"symbol": symbol, "date": d, "open": c, "high": c, "low": c,
                                 "close": c, "volume": 100000, "adj_close": c}, source="alpaca")


def test_watchlist_store(dbs):
    assert seed_watchlist(dbs) == 5
    assert {"SPUS", "HLAL", "SPSK"} <= {w["symbol"] for w in list_watchlist(dbs, kind="watch")}
    add_to_watchlist(dbs, "qqq", kind="hot", note="megacaps")
    assert any(w["symbol"] == "QQQ" for w in list_watchlist(dbs, kind="hot"))


def test_price_change_real_numbers(dbs):
    _series(dbs, "SPUS", [100.0, 102.0])               # prev 100 -> last 102 = +2%
    pc = price_change(dbs, "SPUS")
    assert pc["last"] == 102.0 and pc["change_1d_pct"] == 2.0
    assert price_change(dbs, "NONE")["last"] is None    # no data -> empty, never fabricated


def test_snapshot_market_watchlist_hotlist(dbs):
    from sharia.whitelist import add_instrument
    add_instrument(dbs.sharia, "SPUS", "etf", approved_by="founder", scan_id="t")
    _series(dbs, "SPUS", [100.0, 101.0, 104.0])
    seed_watchlist(dbs)
    snap = build_snapshot(dbs)
    assert {"market", "watchlist", "hotlist"} <= set(snap)
    assert any(x["label"] == "VIX (volatility)" for x in snap["market"]["macro"])   # macro labels present
    assert any(u["symbol"] == "SPUS" and u["last"] == 104.0 for u in snap["market"]["universe"])
    assert any(w["symbol"] == "SPUS" for w in snap["watchlist"])
    assert any(m["symbol"] == "SPUS" for m in snap["hotlist"]["movers"])             # it moved -> a mover


def test_dashboard_renders_new_tabs(dbs):
    from sharia.whitelist import add_instrument
    add_instrument(dbs.sharia, "SPUS", "etf", approved_by="founder", scan_id="t")
    _series(dbs, "SPUS", [100.0, 102.0])
    seed_watchlist(dbs)
    html = build_dashboard_html(dbs)
    for label in ("Market", "Watchlist", "Hotlist"):
        assert label in html
    for vid in ("data-view='market'", "data-view='watchlist'", "data-view='hotlist'"):
        assert vid in html
    assert "Macro — the real market state" in html and "SPUS" in html
