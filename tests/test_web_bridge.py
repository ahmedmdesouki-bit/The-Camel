"""Web bridge — state publisher payload + command poller logic (hermetic; HTTP is injected)."""
import json

from ops.publish_state import build_payload, publish
from ops import command_poller
from governance.approval import request_approval, is_approved


class _Resp:
    def __init__(self, status=200, body=b"[]"):
        self.status = status
        self._body = body
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self): return self._body


# ---- publisher ----

def test_build_payload_shape(dbs):
    p = build_payload(dbs)
    assert p["id"] == 1
    assert "state" in p and "governance" in p["state"] and "kpis" in p["state"]
    assert p["state"]["governance"]["live_at_risk"] == 0.0     # always $0 in paper


def test_publish_posts_to_supabase(dbs):
    calls = []
    def opener(req):
        calls.append({"url": req.full_url, "method": req.get_method(),
                      "auth": req.headers.get("Authorization")})
        return _Resp(status=201)
    status = publish(dbs, url="https://x.supabase.co", service_key="svc-key", opener=opener)
    assert status == 201                                          # the state-upsert status
    urls = [c["url"] for c in calls]
    assert any(u.endswith("/rest/v1/system_state?on_conflict=id") for u in urls)
    assert any(u.endswith("/rest/v1/equity_points") for u in urls)   # the equity point is appended too
    assert all(c["method"] == "POST" and c["auth"] == "Bearer svc-key" for c in calls)


def test_publish_without_equity(dbs):
    calls = []
    publish(dbs, url="https://x.supabase.co", service_key="svc", opener=lambda r: calls.append(r.full_url) or _Resp(),
            append_equity=False)
    assert all("equity_points" not in u for u in calls)           # opt-out works


# ---- poller ----

def test_process_run_tick_is_paper(dbs):
    res = command_poller.process_command(dbs, {"type": "run_tick", "payload": {"symbols": []}})
    assert res["ok"] and res["phase"] == 0                     # paper, no real money


def test_process_approve_is_founder_only(dbs):
    request_approval(dbs, "ref1")
    # a non-founder request is refused
    res = command_poller.process_command(
        dbs, {"type": "approve", "payload": {"ref": "ref1"}, "requested_by": "friend@x.com"},
        founder_email="chiko@x.com")
    assert not res["ok"] and "founder-only" in res["error"]
    assert not is_approved(dbs, "ref1")
    # the founder's request is honored
    res2 = command_poller.process_command(
        dbs, {"type": "approve", "payload": {"ref": "ref1"}, "requested_by": "chiko@x.com"},
        founder_email="chiko@x.com")
    assert res2["ok"] and is_approved(dbs, "ref1")


def test_process_unknown_command(dbs):
    res = command_poller.process_command(dbs, {"type": "nuke", "payload": {}})
    assert not res["ok"] and "unknown" in res["error"]


def test_poll_once_processes_and_marks(dbs):
    pending = [{"id": 7, "type": "run_tick", "payload": {"symbols": []}, "requested_by": "chiko@x.com"}]
    calls = {"patched": []}
    def opener(req):
        if req.get_method() == "GET":
            return _Resp(body=json.dumps(pending).encode())
        calls["patched"].append(req.full_url)               # PATCH mark
        return _Resp(status=204)
    out = command_poller.poll_once(dbs, url="https://x.supabase.co", key="svc",
                                   founder_email="chiko@x.com", opener=opener)
    assert len(out) == 1 and out[0]["result"]["ok"]
    assert any("id=eq.7" in u for u in calls["patched"])     # the command was marked done
