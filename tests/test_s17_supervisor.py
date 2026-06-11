"""
S17.2 — the Supervisor: the cost cap (runaway-bill guardrail) + retry/quarantine resilience.

Deterministic: desk cost is injected via metrics, so no real API call is ever made.
"""
from research.workforce import Workforce, Desk, DeskResult
from research.supervisor import Supervisor, CostMeter


class _OkDesk(Desk):
    def __init__(self, did, cost=0.0):
        self.desk_id = did
        self.kind = "operator"
        self._cost = cost

    def run(self, dbs, ctx=None):
        return DeskResult(self.desk_id, "ok", summary="ok", metrics={"cost_usd": self._cost})


class _FailDesk(Desk):
    def __init__(self, did):
        self.desk_id = did
        self.kind = "operator"
        self.calls = 0

    def run(self, dbs, ctx=None):
        self.calls += 1
        raise RuntimeError("boom")


# ---------------- the cost cap ----------------

def test_cost_meter_basics():
    m = CostMeter(2.0)
    assert m.remaining() == 2.0 and not m.at_cap()
    m.charge(1.5)
    assert m.remaining() == 0.5
    m.charge(1.0)
    assert m.at_cap() and m.remaining() == 0.0


def test_cost_cap_stops_the_cycle(dbs):
    wf = Workforce()
    for i in range(5):
        wf.register(_OkDesk(f"d{i}", cost=0.5))
    rep = Supervisor(wf, cost_cap_usd=1.0).run_cycle(dbs)
    assert rep.ran == ["d0", "d1"]              # d0->0.5, d1->1.0, then at_cap -> STOP
    assert rep.stopped_on_cost and rep.spent_usd == 1.0


def test_all_desks_run_when_under_cap(dbs):
    wf = Workforce()
    for i in range(3):
        wf.register(_OkDesk(f"d{i}", cost=0.1))
    rep = Supervisor(wf, cost_cap_usd=100.0).run_cycle(dbs)
    assert rep.ran == ["d0", "d1", "d2"] and not rep.stopped_on_cost
    assert abs(rep.spent_usd - 0.3) < 1e-9


# ---------------- resilience: retry + quarantine ----------------

def test_failing_desk_is_retried_then_quarantined(dbs):
    wf = Workforce()
    fail = _FailDesk("bad")
    wf.register(fail)
    wf.register(_OkDesk("good"))
    rep = Supervisor(wf, cost_cap_usd=100.0, max_retries=2).run_cycle(dbs)
    assert fail.calls == 3                       # 1 initial + 2 retries
    assert "bad" in rep.quarantined
    assert "good" in rep.ran                     # one bad desk never stops the rest


def test_quarantine_persists_to_next_cycle(dbs):
    wf = Workforce()
    fail = _FailDesk("bad")
    wf.register(fail)
    wf.register(_OkDesk("good"))
    sup = Supervisor(wf, cost_cap_usd=100.0, max_retries=0)
    sup.run_cycle(dbs)                            # bad fails once -> quarantined
    fail.calls = 0
    rep2 = sup.run_cycle(dbs)
    assert fail.calls == 0                        # quarantined -> not run again
    assert rep2.ran == ["good"]
