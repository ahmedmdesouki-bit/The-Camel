"""
State publisher (web bridge) — push the Camel's current snapshot to Supabase for the web window.

The web app is a READ-ONLY MIRROR: this is the only thing that writes the system state it shows. It builds
the same snapshot the offline dashboard uses (`dashboard/snapshot.build_snapshot`) and upserts it as a single
row (id=1) into the Supabase `system_state` table, using the **service-role key** — which lives ONLY here on
the brain side (never in Vercel). Stdlib HTTP only (no new deps). Run it from the daily loop or on a timer:

    python -m ops.publish_state                 # uses CAMEL_DB_DIR + SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY

Nothing here moves money or makes a decision — it only mirrors state outward.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Callable, Optional

from db.paths import CamelDbs
from dashboard.snapshot import build_snapshot


def build_payload(dbs: CamelDbs, mode: str = "paper") -> dict:
    """The single upsert row for `system_state` (id is fixed so we keep exactly one current snapshot)."""
    return {"id": 1, "state": build_snapshot(dbs, mode=mode)}


def equity_point(snapshot: dict) -> dict:
    """One row for the equity-curve table, derived from the snapshot KPIs (the paper track record)."""
    k = snapshot.get("kpis", {})
    return {"total_value": k.get("total_value"), "cash": k.get("cash"),
            "positions_value": k.get("positions_value")}


def _post(url: str, service_key: str, path: str, rows: list, prefer: str,
          opener: Optional[Callable[[urllib.request.Request], object]] = None) -> int:
    """POST rows to a Supabase REST table. Returns the HTTP status."""
    endpoint = f"{url.rstrip('/')}/rest/v1/{path}"
    body = json.dumps(rows).encode("utf-8")
    req = urllib.request.Request(endpoint, data=body, method="POST", headers={
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": prefer,
    })
    do = opener or urllib.request.urlopen
    with do(req) as resp:                                # noqa: S310 (trusted Supabase endpoint)
        return getattr(resp, "status", 200)


def publish(dbs: CamelDbs, *, url: Optional[str] = None, service_key: Optional[str] = None,
            mode: str = "paper", opener=None, append_equity: bool = True) -> int:
    """Upsert the current state and (best-effort) append an equity point. Returns the state HTTP status."""
    url = url or os.environ.get("SUPABASE_URL", "")
    service_key = service_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not service_key:
        raise RuntimeError("set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (brain-side env) to publish.")
    snapshot = build_snapshot(dbs, mode=mode)
    status = _post(url, service_key, "system_state?on_conflict=id", [{"id": 1, "state": snapshot}],
                   "resolution=merge-duplicates,return=minimal", opener=opener)
    if append_equity:
        try:                                             # the equity point is nice-to-have, never fatal
            _post(url, service_key, "equity_points", [equity_point(snapshot)], "return=minimal", opener=opener)
        except Exception:
            pass
    return status


def main(argv=None) -> int:                              # pragma: no cover - CLI entrypoint
    db_dir = os.environ.get("CAMEL_DB_DIR", ".")
    dbs = CamelDbs.from_dir(db_dir)
    status = publish(dbs)
    print(f"published system_state -> HTTP {status}")
    return 0


if __name__ == "__main__":                               # pragma: no cover
    raise SystemExit(main())
