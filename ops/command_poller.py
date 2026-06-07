"""
Command poller (web bridge, phase 2) — the brain dequeues + executes commands the web enqueued.

The web window can only *request*; this is the only thing that *acts* on those requests, and it runs on the
brain side (where the DBs + guardrails live), so every command still flows through the full stack:
  - `run_tick`  → `loop.jobs.run_trading_tick` (Constitution + Edge Proof + Budget + approval gate; paper),
  - `approve` / `veto` → `governance.approval.decide` — **founder-only** (a friend can watch, only the founder
    can approve a live action), enforced here by CAMEL_FOUNDER_EMAIL.

Marks each command done/error with a result. Stdlib HTTP, service-role key (brain-side env only). Single-shot:

    python -m ops.command_poller            # process all pending, then exit (run on a short timer)
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Callable, List, Optional

from db.paths import CamelDbs


def _req(url: str, key: str, method: str, path: str, body: Optional[dict], opener) -> object:
    endpoint = f"{url.rstrip('/')}/rest/v1/{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(endpoint, data=data, method=method, headers={
        "apikey": key, "Authorization": f"Bearer {key}",
        "Content-Type": "application/json", "Prefer": "return=representation",
    })
    do = opener or urllib.request.urlopen
    return do(req)                                       # noqa: S310 (trusted Supabase endpoint)


def fetch_pending(url: str, key: str, opener=None) -> List[dict]:
    with _req(url, key, "GET", "commands?status=eq.pending&order=created_at.asc", None, opener) as resp:
        return json.loads(resp.read().decode("utf-8"))


def mark(url: str, key: str, cmd_id: int, status: str, result: dict, opener=None) -> None:
    body = {"status": status, "result": result, "processed_at": "now()"}
    with _req(url, key, "PATCH", f"commands?id=eq.{int(cmd_id)}", body, opener):
        pass


def process_command(dbs: CamelDbs, cmd: dict, *, founder_email: str = "",
                    symbols: Optional[List[str]] = None) -> dict:
    """Execute ONE command on the brain. Pure-ish (no HTTP) so it is unit-testable. Returns a result dict."""
    ctype = cmd.get("type")
    payload = cmd.get("payload") or {}
    requested_by = (cmd.get("requested_by") or "").lower()

    if ctype == "run_tick":
        from loop.jobs import run_trading_tick
        syms = payload.get("symbols") or symbols or [s for s in os.environ.get("CAMEL_SYMBOLS", "").split(",") if s]
        return {"ok": True, **run_trading_tick(dbs, symbols=syms)}

    if ctype in ("approve", "veto"):
        # founder-only: a friend may queue it, but only the founder's request is honored for a live decision.
        if founder_email and requested_by != founder_email.lower():
            return {"ok": False, "error": "approve/veto is founder-only"}
        ref = str(payload.get("ref") or "")
        if not ref:
            return {"ok": False, "error": "missing approval ref"}
        from governance.approval import decide, is_approved
        decide(dbs, ref, approve=(ctype == "approve"), decided_by=requested_by or "web")
        return {"ok": True, "ref": ref, "approved": is_approved(dbs, ref)}

    return {"ok": False, "error": f"unknown command type {ctype!r}"}


def poll_once(dbs: CamelDbs, *, url: Optional[str] = None, key: Optional[str] = None,
              founder_email: Optional[str] = None, opener=None) -> List[dict]:
    url = url or os.environ.get("SUPABASE_URL", "")
    key = key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    founder_email = founder_email if founder_email is not None else os.environ.get("CAMEL_FOUNDER_EMAIL", "")
    if not url or not key:
        raise RuntimeError("set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (brain-side env) to poll.")
    out: List[dict] = []
    for cmd in fetch_pending(url, key, opener=opener):
        try:
            result = process_command(dbs, cmd, founder_email=founder_email)
            mark(url, key, cmd["id"], "done" if result.get("ok") else "error", result, opener=opener)
        except Exception as exc:                          # one bad command must not stop the rest
            result = {"ok": False, "error": str(exc)}
            mark(url, key, cmd["id"], "error", result, opener=opener)
        out.append({"id": cmd.get("id"), "type": cmd.get("type"), "result": result})
    return out


def main(argv=None) -> int:                              # pragma: no cover - CLI entrypoint
    dbs = CamelDbs.from_dir(os.environ.get("CAMEL_DB_DIR", "."))
    done = poll_once(dbs)
    print(f"processed {len(done)} command(s): {done}")
    return 0


if __name__ == "__main__":                               # pragma: no cover
    raise SystemExit(main())
