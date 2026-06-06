"""
Regime history store (S9) — append-only record of the regime engine's classifications.

Lets the system see how the environment has shifted over time (and, later, learn regime→strategy
affinity). Writes to camel_macro.db.regime_history.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Optional

from db.sqlite import connection
from db.paths import CamelDbs
from trader.regime.classifier import RegimeResult


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_regime(dbs: CamelDbs, result: RegimeResult, now: Optional[str] = None) -> None:
    now = now or _utcnow()
    with connection(dbs.macro) as conn:
        conn.execute(
            "INSERT INTO regime_history (classified_at, regime, confidence, signals, features) "
            "VALUES (?,?,?,?,?)",
            (now, result.regime.value, result.confidence,
             json.dumps(result.signals), json.dumps(result.features)),
        )


def latest_regime(dbs: CamelDbs) -> Optional[dict]:
    with connection(dbs.macro) as conn:
        row = conn.execute(
            "SELECT classified_at, regime, confidence, signals, features "
            "FROM regime_history ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if row is None:
        return None
    return {
        "classified_at": row["classified_at"],
        "regime": row["regime"],
        "confidence": row["confidence"],
        "signals": json.loads(row["signals"] or "[]"),
        "features": json.loads(row["features"] or "{}"),
    }
