"""
S17.3 — the scheduler/DAG: dependency-ordered desk runs + skip-on-upstream-failure.
"""
import pytest

from research.workforce import Workforce, Desk, DeskResult
from research.scheduler import topological_order, run_dag, DEFAULT_DAG


class _Ok(Desk):
    def __init__(self, did):
        self.desk_id = did
        self.kind = "operator"

    def run(self, dbs, ctx=None):
        return DeskResult(self.desk_id, "ok")


class _Fail(Desk):
    def __init__(self, did):
        self.desk_id = did
        self.kind = "operator"

    def run(self, dbs, ctx=None):
        raise RuntimeError("boom")


def test_topological_order_linear():
    assert topological_order({"a": [], "b": ["a"], "c": ["b"]}) == ["a", "b", "c"]


def test_topological_order_detects_cycle():
    with pytest.raises(ValueError):
        topological_order({"a": ["b"], "b": ["a"]})


def test_default_dag_scout_first_conductor_last():
    order = topological_order(DEFAULT_DAG)
    assert order[0] == "scout" and order[-1] == "conductor"
    assert order.index("scout") < order.index("quant") < order.index("conductor")


def test_run_dag_happy_path(dbs):
    wf = Workforce()
    for d in ("a", "b", "c"):
        wf.register(_Ok(d))
    out = run_dag(wf, dbs, {"a": [], "b": ["a"], "c": ["b"]})
    assert [r.desk_id for r in out] == ["a", "b", "c"]
    assert all(r.status == "ok" for r in out)


def test_run_dag_skips_downstream_on_upstream_failure(dbs):
    wf = Workforce()
    wf.register(_Fail("a"))
    wf.register(_Ok("b"))
    wf.register(_Ok("c"))
    out = run_dag(wf, dbs, {"a": [], "b": ["a"], "c": ["b"]})
    byid = {r.desk_id: r.status for r in out}
    assert byid["a"] == "error" and byid["b"] == "skipped" and byid["c"] == "skipped"
