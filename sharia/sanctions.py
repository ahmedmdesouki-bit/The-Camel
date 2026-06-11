"""
OFAC SDN sanctions screen (S17 backlog, built S17).

Scope decision: the US Treasury OFAC SDN list (`sdn.csv`) is a HEADERLESS, positional CSV (col0 ent_num,
col1 SDN_Name, col2 SDN_Type, col3 Program, …) and is a *current snapshot*, not point-in-time observations —
so it does NOT fit the `SourceConnector` pipeline (which drops anything without an `event_date`). This is a
standalone compliance primitive instead: fetch (injected transport — no live web in tests) → parse
positionally → snapshot into a `sanctions` table → `is_sanctioned(name)`.

A sanctioned entity must never enter the tradeable universe — capital preservation + an ethical/legal hard
line. The screen is wired into `sharia.universe.seed_universe` as a name guard: it fires for any seeded
name on the SDN list. For the current ETF-only universe (no single sanctionable issuer) it is inert-but-
enforced; it becomes load-bearing the moment the founder seeds individual equities by name.
"""
from __future__ import annotations

import csv
import io
import re
from typing import Callable, List, Optional

from db.paths import CamelDbs
from db.sqlite import connection
from data.source_registry import OFAC

_NULL = {"", "-0-", "-0- "}


def normalize(name: str) -> str:
    """Uppercase + collapse to alnum/space, so 'Acme, Inc.' and 'ACME INC' match the same key."""
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", (name or "").upper())).strip()


def parse_sdn(raw: str) -> List[dict]:
    """Parse the headerless OFAC sdn.csv positionally. Drops the '-0-' null rows and blank names."""
    out: List[dict] = []
    for row in csv.reader(io.StringIO(raw or "")):
        if len(row) < 2:
            continue
        name = (row[1] or "").strip()
        if name in _NULL or not name:
            continue
        out.append({
            "ent_num": (row[0] or "").strip(),
            "name": name,
            "sdn_type": (row[2].strip() if len(row) > 2 else ""),
            "program": (row[3].strip() if len(row) > 3 else ""),
        })
    return out


def _ensure_table(sharia_db: str) -> None:
    # Single source of truth is db/sharia.py.
    from db.sharia import init_sharia_db
    init_sharia_db(sharia_db)


def refresh_sanctions(dbs: CamelDbs, transport: Optional[Callable[[str], str]] = None,
                      *, now: Optional[str] = None) -> int:
    """Fetch + SNAPSHOT the SDN list into `sanctions` (replaces the prior OFAC snapshot). Returns the
    count stored. `transport` is injected (stdlib fetch in prod, a stub in tests)."""
    from datetime import datetime, timezone
    if transport is None:
        from data.connectors.base import http_get, with_retries
        transport = with_retries(lambda u: http_get(u))
    now = now or datetime.now(timezone.utc).isoformat()
    records = parse_sdn(transport(f"{OFAC.base_url}/sdn.csv"))
    _ensure_table(dbs.sharia)
    with connection(dbs.sharia) as conn:
        conn.execute("DELETE FROM sanctions WHERE source='ofac'")        # snapshot, not append
        for r in records:
            conn.execute("INSERT INTO sanctions (ent_num, name, normalized, sdn_type, program, ingested_at)"
                         " VALUES (?,?,?,?,?,?)",
                         (r["ent_num"], r["name"], normalize(r["name"]), r["sdn_type"], r["program"], now))
    return len(records)


def is_sanctioned(dbs: CamelDbs, name: str) -> bool:
    """True if `name` (normalized) matches an OFAC SDN entry. An empty/unknown name is False — the screen
    never invents a positive (fail-open on *absence of a name*, fail-closed on a *match*)."""
    norm = normalize(name)
    if not norm:
        return False
    _ensure_table(dbs.sharia)
    with connection(dbs.sharia) as conn:
        row = conn.execute("SELECT 1 FROM sanctions WHERE normalized=? LIMIT 1", (norm,)).fetchone()
    return row is not None
