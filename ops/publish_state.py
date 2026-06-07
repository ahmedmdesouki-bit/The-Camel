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


def _post(url: str, service_key: str, payload: dict,
          opener: Optional[Callable[[urllib.request.Request], object]] = None) -> int:
    """Upsert one row into system_state via the Supabase REST API. Returns the HTTP status."""
    endpoint = f"{url.rstrip('/')}/rest/v1/system_state?on_conflict=id"
    body = json.dumps([payload]).encode("utf-8")
    req = urllib.request.Request(endpoint, data=body, method="POST", headers={
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    })
    do = opener or urllib.request.urlopen
    with do(req) as resp:                                # noqa: S310 (trusted Supabase endpoint)
        return getattr(resp, "status", 200)


def publish(dbs: CamelDbs, *, url: Optional[str] = None, service_key: Optional[str] = None,
            mode: str = "paper", opener=None) -> int:
    url = url or os.environ.get("SUPABASE_URL", "")
    service_key = service_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not service_key:
        raise RuntimeError("set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (brain-side env) to publish.")
    return _post(url, service_key, build_payload(dbs, mode), opener=opener)


def main(argv=None) -> int:                              # pragma: no cover - CLI entrypoint
    db_dir = os.environ.get("CAMEL_DB_DIR", ".")
    dbs = CamelDbs.from_dir(db_dir)
    status = publish(dbs)
    print(f"published system_state -> HTTP {status}")
    return 0


if __name__ == "__main__":                               # pragma: no cover
    raise SystemExit(main())
