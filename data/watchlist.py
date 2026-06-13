"""
data/watchlist.py (S-UI) — the founder-curated watch / hot lists + a price-change helper for the interface.

watchlist(kind='watch') = names being tracked; watchlist(kind='hot') = high-conviction pins. Being on a list
here is purely tracking — it is NOT the tradeable whitelist (that lives in camel_sharia and is founder-gated
through the Constitution). `price_change` reads camel_market for the latest close + daily / ~1-month % change,
so the Market / Watchlist / Hotlist tabs show REAL ingested numbers (as of the last data pull), not mock data.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from db.paths import CamelDbs
from db.sqlite import connection

# Default watch set: the compliant ETF family (SP Funds + Wahed). Tracking only — not tradeable until a name
# is founder-vetted into the whitelist.
DEFAULT_WATCH = {
    "SPUS": "SP Funds S&P 500 Sharia",
    "HLAL": "Wahed FTSE USA Shariah",
    "SPSK": "SP Funds Dow Jones Global Sukuk",
    "SPRE": "SP Funds S&P Global REIT Sharia",
    "UMMA": "Wahed Dow Jones Islamic World",
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_to_watchlist(dbs: CamelDbs, symbol: str, *, kind: str = "watch", note: str = "",
                     by: str = "founder") -> None:
    from db.market import init_market_db
    init_market_db(dbs.market)
    with connection(dbs.market) as conn:
        conn.execute(
            "INSERT INTO watchlist (symbol, kind, note, added_at, added_by) VALUES (?,?,?,?,?) "
            "ON CONFLICT(symbol, kind) DO UPDATE SET note=excluded.note, added_at=excluded.added_at",
            (symbol.upper(), kind, note, _utcnow(), by))


def remove_from_watchlist(dbs: CamelDbs, symbol: str, *, kind: str = "watch") -> None:
    with connection(dbs.market) as conn:
        conn.execute("DELETE FROM watchlist WHERE symbol=? AND kind=?", (symbol.upper(), kind))


def list_watchlist(dbs: CamelDbs, *, kind: Optional[str] = None) -> List[dict]:
    from db.market import init_market_db
    init_market_db(dbs.market)
    sql, args = "SELECT symbol, kind, note, added_at FROM watchlist", []
    if kind:
        sql += " WHERE kind=?"
        args.append(kind)
    sql += " ORDER BY symbol"
    with connection(dbs.market) as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def seed_watchlist(dbs: CamelDbs, by: str = "founder") -> int:
    """Seed the default compliant ETF family into the 'watch' list (idempotent)."""
    for sym, note in DEFAULT_WATCH.items():
        add_to_watchlist(dbs, sym, kind="watch", note=note, by=by)
    return len(DEFAULT_WATCH)


def priced_symbols(dbs: CamelDbs) -> List[str]:
    from db.market import init_market_db
    init_market_db(dbs.market)
    with connection(dbs.market) as conn:
        return [r[0] for r in conn.execute("SELECT DISTINCT symbol FROM prices ORDER BY symbol").fetchall()]


def price_change(dbs: CamelDbs, symbol: str) -> dict:
    """Latest close + daily and ~1-month % change for `symbol` from camel_market (None where no data)."""
    with connection(dbs.market) as conn:
        rows = conn.execute(
            "SELECT date, close FROM prices WHERE symbol=? AND close IS NOT NULL "
            "ORDER BY date DESC LIMIT 30", (symbol,)).fetchall()
    closes = [(r[0], float(r[1])) for r in rows]                 # newest first
    if not closes:
        return {"symbol": symbol, "last": None, "date": None,
                "change_1d_pct": None, "change_21d_pct": None}
    date, last = closes[0]
    prev = closes[1][1] if len(closes) > 1 else None
    mo = closes[21][1] if len(closes) > 21 else (closes[-1][1] if len(closes) > 1 else None)
    return {
        "symbol": symbol, "last": round(last, 4), "date": date,
        "change_1d_pct": round((last / prev - 1.0) * 100, 2) if prev else None,
        "change_21d_pct": round((last / mo - 1.0) * 100, 2) if mo else None,
    }


def main(argv=None) -> int:                                       # pragma: no cover - CLI entrypoint
    import argparse
    import os
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    p = argparse.ArgumentParser(description="The Camel — watch / hot lists")
    p.add_argument("cmd", choices=["seed", "watch", "hot", "unwatch", "list"])
    p.add_argument("symbol", nargs="?", default="")
    p.add_argument("--note", default="")
    p.add_argument("--db-dir", default=os.environ.get("CAMEL_DB_DIR", "."))
    args = p.parse_args(argv)
    from db.paths import init_all
    dbs = CamelDbs.from_dir(args.db_dir)
    init_all(dbs)
    if args.cmd == "seed":
        print(f"seeded {seed_watchlist(dbs)} names into the watch list")
    elif args.cmd in ("watch", "hot") and args.symbol:
        add_to_watchlist(dbs, args.symbol, kind=("hot" if args.cmd == "hot" else "watch"), note=args.note)
        print(f"added {args.symbol.upper()} to the {args.cmd} list")
    elif args.cmd == "unwatch" and args.symbol:
        remove_from_watchlist(dbs, args.symbol)
        print(f"removed {args.symbol.upper()} from the watch list")
    else:
        for w in list_watchlist(dbs):
            print(f"  {w['symbol']:<6} [{w['kind']}] {w.get('note') or ''}")
    return 0


if __name__ == "__main__":                                        # pragma: no cover
    raise SystemExit(main())
