"""
The Camel — one-command demo (for testers / a first look).

    python demo.py

Seeds a fresh set of the 7 SQLite DBs under ./demo_run/ with realistic sample data, drives ONE full
governed tick through the entire stack (regime → strategy → 17-check Edge Proof → Constitution → Budget
→ realistic-paper fill), and writes the read-only operator dashboard to ./demo_run/camel-dashboard.html.

Everything is PAPER and offline — no network, no real money, no credentials. It is a faithful, safe
demonstration of how the Camel decides: it shows the rejections (the whole point), not just the holdings.
"""
from __future__ import annotations

import os
from datetime import date, timedelta


def main(out_dir: str | None = None, quiet: bool = False) -> int:
    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_run")
    os.makedirs(out_dir, exist_ok=True)

    from db.paths import CamelDbs, init_all
    from db.sqlite import connection
    from data.store import store_price
    from ledger.writer import append_entry
    from broker.positions import apply_fill
    from sharia.whitelist import add_instrument, freeze_instrument
    from engine.edge_proof_v0 import EdgeReport, log_edge_report
    from guardrail.constitution import PortfolioState, Instrument
    from strategies.registry import StrategyRegistry
    from strategies.quality_momentum import QualityMomentum
    from strategies.core_dca import CoreDCA
    from execution.models import MarketSnapshot
    from sandbox.runner import SandboxRunner
    from dashboard.generate import write_dashboard

    dbs = CamelDbs.from_dir(out_dir)
    init_all(dbs)

    # ---- seed a small paper book + Sharia whitelist (incl. a frozen, non-compliant name) ----
    append_entry(dbs.portfolio, "DEPOSIT", "", 10_000.0)
    for sym, qty, px in (("SPUS", 26, 41.20), ("HLAL", 31, 48.90)):
        append_entry(dbs.portfolio, "BUY", sym, -(qty * px), ref="seed")
        apply_fill(dbs.portfolio, sym, "buy", qty, px)
        add_instrument(dbs.sharia, sym, "etf", approved_by="chiko", scan_id="seed")
    add_instrument(dbs.sharia, "AAPL", "stock", approved_by="chiko", scan_id="seed")
    add_instrument(dbs.sharia, "SCHD", "etf", approved_by="chiko", scan_id="seed")
    freeze_instrument(dbs.sharia, "SCHD", reason="AAOIFI debt ratio > 30%")
    with connection(dbs.sharia) as conn:
        conn.execute("INSERT INTO sharia_status (symbol, final_status) VALUES ('AAPL','pass')")

    # ---- seed prices (AAPL in an uptrend that beats the flat benchmark) + a regime + Edge decisions ----
    d0 = date.fromisoformat("2025-06-01")
    for k in range(320):
        d = (d0 + timedelta(days=k)).isoformat()
        store_price(dbs.market, {"symbol": "AAPL", "date": d, "close": 40.0 + 0.1 * k, "adj_close": 40.0 + 0.1 * k})
        store_price(dbs.market, {"symbol": "SPUS", "date": d, "close": 50.0, "adj_close": 50.0})
    # seed enough FRED-style macro for the regime engine to classify a real state (restrictive, low-vol)
    for series_id, value in (("FEDFUNDS", 3.50), ("DGS2", 3.60), ("DGS10", 4.35), ("UNRATE", 3.9),
                             ("BAMLH0A0HYM2", 2.9), ("VIXCLS", 13.8), ("DTWEXBGS", 119.0),
                             ("CPIAUCSL", 318.0), ("DCOILWTICO", 71.0), ("DEXSAUS", 3.7505)):
        with connection(dbs.macro) as conn:
            conn.execute("INSERT INTO macro_observations (series_id, value, event_date, known_at, source_id) "
                         "VALUES (?,?,?,?,?)", (series_id, value, "2026-06-05", "2026-06-05", "demo"))
    log_edge_report(dbs.learning, EdgeReport("AAPL", "quality_momentum", 148, 0.61, 0.04, -0.06, -0.1,
                                             "SPUS", 0.02, 0.71, True, "edge survives multiple-testing penalty"))
    log_edge_report(dbs.learning, EdgeReport("SCHD", "core_dca", 92, 0.51, -0.01, -0.2, -0.2,
                                             "SPUS", -0.02, 0.34, False, "non-compliant — Sharia gate"))

    # ---- drive ONE full governed tick through the whole stack (sandbox = virtual money, stub live feed) ----
    reg = StrategyRegistry(); reg.register(QualityMomentum()); reg.register(CoreDCA())
    state = PortfolioState(fund_usd=10_000, cash_usd=8_000,
                           whitelist={"AAPL": Instrument("AAPL", "tech", "compliant", False, True)})

    def feed(_sym):
        return MarketSnapshot(symbol="AAPL", bid=71.5, ask=72.0, last=71.8, displayed_size=100,
                              as_of="2026-06-07T15:00:00+00:00")

    out = SandboxRunner(dbs, reg, feed=feed).run_tick(["AAPL"], state, notional_per_trade=500.0)

    dash = write_dashboard(dbs, os.path.join(out_dir, "camel-dashboard.html"), mode="paper")

    if quiet:
        return 0
    print("\n  THE CAMEL -- demo run\n  " + "-" * 48)
    print(f"  Regime classified : {out.tick.regime}")
    print(f"  Router path       : {out.tick.router_path}")
    print(f"  Executed (virtual): {out.filled or '-- (no proven edge -> No-Edge: ' + (out.no_edge or 'wait') + ')'}")
    if out.fills:
        f = out.fills[0]
        print(f"  Realistic fill    : {f.status.value} {f.filled_qty} {f.symbol} @ ${f.fill_price} (fees ${f.fees})")
    print(f"\n  Dashboard written : {dash}")
    print("  Open it in any browser -- fully offline, read-only, no order entry.\n")
    print("  Run the test suite:  pytest -q   (expect 572 passed)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
