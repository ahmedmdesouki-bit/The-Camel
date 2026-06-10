"""
S16-A3 (Alpaca price wiring) + S16-A4 (Sharia universe seeding + re-screen schedule).

Hermetic: the Alpaca fetcher is injected (no live web, no alpaca-py needed); the universe seeding is
proven Constitution-gated and fail-closed.
"""
from datetime import datetime, timedelta, timezone

import pytest

from db.sqlite import connection
from data.ingest import alpaca_backfill, have_alpaca_keys
from sharia.universe import DEFAULT_UNIVERSE, seed_universe, rescreen_due
from sharia.whitelist import load_whitelist


# ================= A3 — Alpaca backfill =================

def _bars(symbols, start, end):
    return [{"symbol": s, "date": "2026-01-02", "open": 10.0, "high": 11.0, "low": 9.5,
             "close": 10.5, "volume": 1000, "adj_close": 10.5} for s in symbols]


def test_alpaca_backfill_stores_bars(dbs):
    out = alpaca_backfill(dbs.market, ["SPUS", "HLAL"], days=5, fetcher=_bars)
    assert out == {"stored": 2, "symbols": ["HLAL", "SPUS"]}
    with connection(dbs.market) as conn:
        rows = conn.execute("SELECT symbol, close, source FROM prices ORDER BY symbol").fetchall()
    assert [(r["symbol"], r["close"], r["source"]) for r in rows] == [
        ("HLAL", 10.5, "alpaca"), ("SPUS", 10.5, "alpaca")]


def test_alpaca_backfill_reports_errors_never_raises(dbs):
    def boom(symbols, start, end):
        raise RuntimeError("network down")
    out = alpaca_backfill(dbs.market, ["SPUS"], fetcher=boom)
    assert "error" in out and "network down" in out["error"]


def test_have_alpaca_keys_reads_env(monkeypatch):
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)
    assert not have_alpaca_keys()
    monkeypatch.setenv("ALPACA_API_KEY", "k")
    monkeypatch.setenv("ALPACA_API_SECRET", "s")
    assert have_alpaca_keys()


# ================= A4 — universe seeding =================

def test_seed_universe_is_founder_gated_fail_closed(dbs):
    with pytest.raises(ValueError):
        seed_universe(dbs, "")                              # no founder identity → refuse
    with pytest.raises(ValueError):
        seed_universe(dbs, "   ")


def test_seed_universe_adds_default_etfs_via_constitution(dbs):
    res = seed_universe(dbs, "Chiko")
    assert set(res) == set(DEFAULT_UNIVERSE) and all(v == "added (compliant)" for v in res.values())
    wl = load_whitelist(dbs.sharia)
    assert wl["SPUS"].on_whitelist and not wl["SPUS"].frozen
    with connection(dbs.sharia) as conn:                    # the audit event was written
        n = conn.execute("SELECT COUNT(*) FROM sharia_events WHERE event_type='SHARIA_SCAN'").fetchone()[0]
    assert n == len(DEFAULT_UNIVERSE)


def test_seed_universe_never_stamps_unvetted_symbols_compliant(dbs):
    """QA Sharia-rail regression: a seed is NOT a screen. Only the named default ETFs land
    'compliant'; any other symbol seeds 'pending_review' — on the list but NOT tradeable (the
    strategy guard requires pass/compliant; the Constitution blocks non-compliant buys) until a
    real quorum screen clears it."""
    res = seed_universe(dbs, "Chiko", symbols={"TSLA": "equity", "SPUS": "etf"})
    assert res["TSLA"] == "added (pending_review)" and res["SPUS"] == "added (compliant)"
    wl = load_whitelist(dbs.sharia)
    assert wl["TSLA"].sharia_status == "pending_review"
    # and the buy path is actually blocked for it
    from guardrail.constitution import Constitution, Action, ActionType, PortfolioState, Thesis
    d = Constitution().evaluate(
        Action(ActionType.TRADE, symbol="TSLA", side="buy", notional_usd=10,
               thesis=Thesis("i", "p", "t"), mode="paper"),
        PortfolioState(fund_usd=100, cash_usd=100, whitelist=wl))
    assert not d.allow and "not Sharia-compliant" in d.reason


def test_persisted_source_urls_never_carry_keys(dbs):
    """QA secret-at-rest regression: a keyed vendor URL (FRED-style) must be redacted in every
    persisted row and source_document — backups ship these files off-box."""
    from data.connectors.base import redact_url
    keyed = "https://api.stlouisfed.org/fred/series?series_id=DGS10&api_key=SuPerSecret123&file_type=json"
    safe = redact_url(keyed)
    assert "SuPerSecret123" not in safe and "api_key=REDACTED" in safe and "series_id=DGS10" in safe
    assert redact_url("https://x.test/data?token=abc&q=1") == "https://x.test/data?token=REDACTED&q=1"
    assert redact_url("") == ""


def test_seed_universe_respects_kill_switch(dbs):
    from ops.kill_switch import halt
    halt()                                                  # Constitution refuses ALL actions when halted
    res = seed_universe(dbs, "Chiko")
    assert all("kill switch" in v.lower() for v in res.values())
    assert load_whitelist(dbs.sharia) == {}                 # nothing was added


# ================= A4 — re-screen schedule =================

def test_rescreen_due_flags_seed_only_names(dbs):
    seed_universe(dbs, "Chiko")
    due = rescreen_due(dbs)
    assert {d["symbol"] for d in due} == set(DEFAULT_UNIVERSE)
    assert all("never re-screened" in d["reason"] for d in due)


def test_rescreen_respects_next_review_at(dbs):
    seed_universe(dbs, "Chiko", symbols={"SPUS": "etf"})
    now = datetime.now(timezone.utc)
    fresh = (now + timedelta(days=80)).isoformat()
    with connection(dbs.sharia) as conn:                    # a recent cross-check screen exists
        conn.execute("CREATE TABLE IF NOT EXISTS sharia_status (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     " symbol TEXT, screened_at TEXT, next_review_at TEXT)")
        conn.execute("INSERT INTO sharia_status (symbol, screened_at, next_review_at) VALUES (?,?,?)",
                     ("SPUS", now.isoformat(), fresh))
    assert rescreen_due(dbs) == []                          # screened and not yet due
    stale = (now - timedelta(days=1)).isoformat()
    with connection(dbs.sharia) as conn:
        conn.execute("INSERT INTO sharia_status (symbol, screened_at, next_review_at) VALUES (?,?,?)",
                     ("SPUS", (now - timedelta(days=91)).isoformat(), stale))
    due = rescreen_due(dbs)
    assert [d["symbol"] for d in due] == ["SPUS"] and "due since" in due[0]["reason"]


def test_daily_ops_surfaces_rescreen_due(dbs, tmp_path):
    from loop.jobs import run_daily_ops
    from alerts.telegram import TelegramNotifier
    seed_universe(dbs, "Chiko", symbols={"SPUS": "etf"})
    summary = run_daily_ops(dbs, notifier=TelegramNotifier(None, None),
                            dashboard_path=str(tmp_path / "d.html"))
    assert [d["symbol"] for d in summary["sharia_rescreen_due"]] == ["SPUS"]
