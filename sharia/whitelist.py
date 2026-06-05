"""
Sharia whitelist — persistence layer (SQLite for Phase 0).

Caller is responsible for routing ADD_WHITELIST through Constitution.evaluate()
first; this module handles the DB write after the gate passes.
"""
from __future__ import annotations
import datetime
from datetime import timezone
from typing import Dict, Optional

from db.sqlite import connect
from guardrail.constitution import Instrument


def load_whitelist(db_path: str) -> Dict[str, Instrument]:
    """
    Load all non-frozen and frozen whitelist entries as {symbol: Instrument}.
    This is the dict that PortfolioState.whitelist expects.
    """
    with connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM whitelist").fetchall()
    result: Dict[str, Instrument] = {}
    for r in rows:
        result[r["symbol"]] = Instrument(
            symbol=r["symbol"],
            sector=r["asset_type"] or "Unknown",
            sharia_status=r["sharia_status"] or "unknown",
            frozen=bool(r["frozen"]),
            on_whitelist=True,
        )
    return result


def add_instrument(
    db_path: str,
    symbol: str,
    asset_type: str,
    approved_by: str,
    scan_id: str,
    source: str = "",
    sharia_status: str = "compliant",
) -> None:
    """
    Persist a whitelist entry.  Constitution gate must pass before calling this.
    Upserts on conflict so re-adding a cleared name refreshes metadata.
    """
    now = datetime.datetime.now(timezone.utc).isoformat()
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO whitelist
                (symbol, asset_type, sharia_status, frozen,
                 approved_by, scanned_at, scan_id, source)
            VALUES (?, ?, ?, 0, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                sharia_status = excluded.sharia_status,
                frozen        = 0,
                approved_by   = excluded.approved_by,
                scanned_at    = excluded.scanned_at,
                scan_id       = excluded.scan_id,
                source        = excluded.source
            """,
            (symbol, asset_type, sharia_status, approved_by, now, scan_id, source),
        )
        conn.execute(
            "INSERT INTO sharia_events (event_type, symbol, reason) VALUES (?,?,?)",
            ("SHARIA_SCAN", symbol, f"Added by {approved_by}, scan_id={scan_id}"),
        )


def freeze_instrument(db_path: str, symbol: str, reason: str) -> bool:
    """
    Mark an instrument frozen (compliance drift detected by re-screen).
    Returns True if the symbol existed.
    """
    with connect(db_path) as conn:
        c = conn.execute(
            "UPDATE whitelist SET frozen=1 WHERE symbol=?", (symbol,)
        )
        if c.rowcount == 0:
            return False
        conn.execute(
            "INSERT INTO sharia_events (event_type, symbol, reason) VALUES (?,?,?)",
            ("FROZEN", symbol, reason),
        )
    return True


def unfreeze_instrument(db_path: str, symbol: str) -> bool:
    """
    Unfreeze after a re-screen clears the instrument.
    Returns True if the symbol existed.
    """
    with connect(db_path) as conn:
        c = conn.execute(
            "UPDATE whitelist SET frozen=0, sharia_status='compliant' WHERE symbol=?",
            (symbol,),
        )
        if c.rowcount == 0:
            return False
        conn.execute(
            "INSERT INTO sharia_events (event_type, symbol, reason) VALUES (?,?,?)",
            ("UNFROZEN", symbol, "Manual re-screen clearance"),
        )
    return True


def get_instrument(db_path: str, symbol: str) -> Optional[Dict]:
    """Return the raw row dict for a symbol, or None if not found."""
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM whitelist WHERE symbol=?", (symbol,)
        ).fetchone()
    return dict(row) if row else None
